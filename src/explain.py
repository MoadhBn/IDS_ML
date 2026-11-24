"""Global explanations: three ways to measure how much each feature matters.

1. The forest's internal importance (mean decrease in impurity).
2. Permutation importance on the test set.
3. Mean absolute SHAP value on a sample of at most 2,000 test flows.

The models see 192 columns, because `proto`, `service` and `state` are
one-hot encoded. To compare like with like, every measure is brought back to
the 42 original features. For the internal importance and SHAP this is done
by adding up the values of the one-hot columns of each text feature, which is
valid because both measures are additive. Permutation importance shuffles the
original columns before the pipeline, so it is already per original feature.
"""

import numpy as np
import pandas as pd
import shap
from joblib import Parallel, delayed
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

from src import cache, config


# ---------------------------------------------------------------------------
# From encoded columns back to original features
# ---------------------------------------------------------------------------
def column_to_feature(pipeline):
    """Map each encoded column name to the original feature it comes from."""
    prep = pipeline.named_steps["prep"]
    names = prep.get_feature_names_out()
    encoder = prep.named_transformers_["cat"]
    mapping = {}
    for feature, categories in zip(config.CATEGORICAL, encoder.categories_):
        for cat in categories:
            mapping[f"{feature}_{cat}"] = feature
    return [mapping.get(n, n) for n in names]


def group_columns(values, pipeline):
    """Add up the columns (last axis) that belong to the same original feature."""
    features = column_to_feature(pipeline)
    df = pd.DataFrame(np.atleast_2d(values), columns=features)
    return df.T.groupby(level=0, sort=False).sum().T


# ---------------------------------------------------------------------------
# 1. Internal importance of the forest
# ---------------------------------------------------------------------------
def forest_importance(pipeline):
    """Mean decrease in impurity, per original feature, summing to 1."""
    raw = pipeline.named_steps["model"].feature_importances_
    return group_columns(raw, pipeline).iloc[0].sort_values(ascending=False)


# ---------------------------------------------------------------------------
# 2. Permutation importance
# ---------------------------------------------------------------------------
def permutation_importance_cached(name, pipeline, X, y, n_repeats=5, seed=config.SEED):
    """Drop in PR-AUC when each original feature is shuffled, averaged over repeats.

    Returns a DataFrame with the mean and standard deviation of the drop.
    """
    key = cache.fingerprint("permutation", name, cache.data_fingerprint(X, y), repr(pipeline),
                            n_repeats, seed)

    def compute():
        res = permutation_importance(pipeline, X, y, scoring="average_precision",
                                     n_repeats=n_repeats, random_state=seed, n_jobs=-1)
        return pd.DataFrame({"baisse moyenne": res.importances_mean, "écart-type": res.importances_std},
                            index=X.columns)

    result, _ = cache.load_or_compute(f"permutation_{name}.joblib", key, compute)
    return result.sort_values("baisse moyenne", ascending=False)


def group_permutation_drop(pipeline, X, y, columns, n_repeats=5, seed=config.SEED):
    """Drop in PR-AUC when several columns are shuffled together.

    The same row shuffle is applied to all the columns of the group, so their
    relation to one another is kept but their link to the label is broken.
    This answers a question single-feature permutation cannot: when features
    carry the same information, shuffling one leaves the others to compensate,
    so each looks less important than the group really is.
    """
    from sklearn.metrics import average_precision_score
    rng = np.random.default_rng(seed)
    reference = average_precision_score(y, pipeline.predict_proba(X)[:, 1])
    drops = []
    for _ in range(n_repeats):
        shuffled = X.copy()
        order = rng.permutation(len(X))
        shuffled[columns] = X[columns].to_numpy()[order]
        drops.append(reference - average_precision_score(y, pipeline.predict_proba(shuffled)[:, 1]))
    return float(np.mean(drops)), float(np.std(drops)), float(reference)


# ---------------------------------------------------------------------------
# 3. SHAP
# ---------------------------------------------------------------------------
def shap_sample(X, y, families, n=config.SHAP_MAX_SAMPLES, seed=config.SEED):
    """A random sample of n flows, stratified on the attack family."""
    idx, _ = train_test_split(np.arange(len(X)), train_size=n, stratify=families, random_state=seed)
    idx = np.sort(idx)
    return X.iloc[idx], y.iloc[idx], families.iloc[idx]


def _shap_chunk(model, Z):
    values = shap.TreeExplainer(model).shap_values(Z)
    values = np.asarray(values)
    # scikit-learn forests give one set of values per class: keep the "attack" class.
    return values[..., 1] if values.ndim == 3 else values


def shap_values_cached(name, pipeline, X_sample):
    """SHAP values of every encoded column for each flow of the sample.

    Returns (values, base_value, column_names). The computation is split into
    chunks run in parallel, then cached. For the forest, values are in
    probability of attack; for XGBoost, in log-odds.
    """
    key = cache.fingerprint("shap", name, cache.data_fingerprint(X_sample, X_sample.iloc[:, 0]),
                            repr(pipeline))

    def compute():
        model = pipeline.named_steps["model"]
        Z = pipeline.named_steps["prep"].transform(X_sample)
        chunks = np.array_split(Z, 12)
        parts = Parallel(n_jobs=-1)(delayed(_shap_chunk)(model, c) for c in chunks)
        base = np.atleast_1d(shap.TreeExplainer(model).expected_value)
        base = float(base[1] if len(base) == 2 else base[0])
        names = list(pipeline.named_steps["prep"].get_feature_names_out())
        return np.vstack(parts), base, names

    result, _ = cache.load_or_compute(f"shap_{name}.joblib", key, compute)
    return result


def mean_abs_shap(values, pipeline):
    """Mean absolute SHAP value per original feature.

    The one-hot columns of a text feature are summed flow by flow first (their
    total is the contribution of that feature), then the absolute value is
    averaged over flows.
    """
    grouped = group_columns(values, pipeline)
    return grouped.abs().mean().sort_values(ascending=False)


# ---------------------------------------------------------------------------
# Local explanations
# ---------------------------------------------------------------------------
def outcome(y_true, scores, threshold):
    """Label each flow as VP, FP, FN or VN (true/false positive/negative)."""
    pred = scores >= threshold
    y = np.asarray(y_true) == 1
    return np.select([pred & y, pred & ~y, ~pred & y], ["VP", "FP", "FN"], default="VN")


def pick_cases(X_sample, y_sample, families, scores, threshold, seed=config.SEED):
    """Choose the five flows to explain, with fixed, stated rules.

    - two true positives from two different attack families: the two most
      common families among the true positives of the sample;
    - two false positives: one with sttl = 254 and one with sttl = 62, the two
      groups that produce the false alerts (section 4.4);
    - one false negative.
    Within each group the flow is drawn at random with the project seed, so
    the choice is reproducible and not hand-picked.
    """
    rng = np.random.default_rng(seed)
    kinds = pd.Series(outcome(y_sample, scores, threshold), index=X_sample.index)
    fam = pd.Series(np.asarray(families), index=X_sample.index)

    def draw(mask):
        candidates = X_sample.index[mask]
        return candidates[rng.integers(len(candidates))]

    cases = {}
    tp = kinds == "VP"
    for i, family in enumerate(fam[tp].value_counts().index[:2], start=1):
        cases[f"VP {i} ({family})"] = draw(tp & (fam == family))
    fp = kinds == "FP"
    cases["FP 1 (sttl = 254)"] = draw(fp & (X_sample["sttl"] == 254))
    cases["FP 2 (sttl = 62)"] = draw(fp & (X_sample["sttl"] == 62))
    fn_idx = draw(kinds == "FN")
    cases[f"FN ({fam[fn_idx]})"] = fn_idx
    return cases, kinds


def explanation_for(row_position, values, base, pipeline, X_sample):
    """A SHAP Explanation for one flow, per original feature, with readable values."""
    grouped = group_columns(values[row_position], pipeline).iloc[0]
    raw = X_sample.iloc[row_position][grouped.index]
    # Round decimals so the figure stays readable (e.g. 38466.02734 -> 38466.03).
    def tidy(v):
        if isinstance(v, (int, float, np.integer, np.floating)):
            f = float(v)
            return int(f) if f.is_integer() else round(f, 3)
        return v
    readable = [tidy(v) for v in raw]
    return shap.Explanation(values=grouped.to_numpy(), base_values=base,
                            data=np.array(readable, dtype=object), feature_names=list(grouped.index))


def contribution_table(expl, top=8):
    """The largest contributions of one explanation, as a table."""
    df = pd.DataFrame({"valeur": expl.data, "contribution": expl.values}, index=expl.feature_names)
    return df.reindex(df["contribution"].abs().sort_values(ascending=False).index).head(top)


def plot_waterfall(expl, title, filename=None, max_display=10):
    import matplotlib.pyplot as plt
    shap.plots.waterfall(expl, max_display=max_display, show=False)
    plt.title(title)
    plt.tight_layout()
    if filename:
        plt.savefig(config.FIGURES / filename, dpi=150, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# Comparing the rankings
# ---------------------------------------------------------------------------
def ranking_table(measures, top=15):
    """Rank of each feature under each measure, for the features in anyone's top list."""
    ranks = pd.DataFrame({name: s.rank(ascending=False, method="min").astype(int)
                          for name, s in measures.items()})
    keep = set()
    for s in measures.values():
        keep |= set(s.sort_values(ascending=False).index[:top])
    order = sorted(keep, key=lambda f: ranks.loc[f].mean())
    return ranks.loc[order]


def rank_correlations(measures):
    """Spearman correlation between every pair of rankings, over all features."""
    return pd.DataFrame(measures).corr(method="spearman")


def plot_measures(measures, top=12, filename=None):
    """The three measures side by side, each scaled so that its top feature equals 1."""
    import matplotlib.pyplot as plt
    first = list(measures.values())[0]
    order = list(first.sort_values(ascending=False).index[:top])
    for s in measures.values():
        for f in s.sort_values(ascending=False).index[:top]:
            if f not in order:
                order.append(f)
    df = pd.DataFrame({name: s.clip(lower=0) / s.max() for name, s in measures.items()}).loc[order]
    ax = df.iloc[::-1].plot.barh(figsize=(8, 0.35 * len(order) + 1.5), width=0.8)
    ax.set_xlabel("importance relative (1 = variable la plus importante pour la mesure)")
    ax.set_title("Trois mesures d'importance, forêt aléatoire")
    plt.tight_layout()
    if filename:
        plt.savefig(config.FIGURES / filename, dpi=150)
    plt.show()
