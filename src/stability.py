"""Do the explanations change when the random seed or the split changes?

Two experiments, each compared with the reference run (seed 42, split 42):

- seed: same train/validation split, forest trained with another seed;
- split: another train/validation split, forest trained with seed 42.

Each run retrains the forest with the hyperparameters found in section 3,
then computes SHAP values on the same 2,000 test flows as section 5. Keeping
the explained flows fixed means any difference comes from the model, not
from the flows being explained. Results are cached run by run.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from src import cache, config
from src import data as D
from src import explain as X
from src import models as M
from src.preprocessing import numeric_columns

NAME = "Forêt aléatoire"


def run(train_clean, X_test, y_test, X_shap, best_params, split_seed, model_seed):
    """Train one variant and return its explanations and scores (cached)."""
    train, val = D.split_train_val(train_clean, seed=split_seed)
    X_tr, y_tr, _ = D.get_xy(train)
    X_va, y_va, _ = D.get_xy(val)
    pipeline = M.make_pipelines(numeric_columns(X_tr), seed=model_seed)[NAME]
    pipeline.set_params(**best_params)
    key = cache.fingerprint("stability", split_seed, model_seed, cache.data_fingerprint(X_tr, y_tr),
                            cache.data_fingerprint(X_shap, X_shap.iloc[:, 0]), repr(pipeline))

    def compute():
        pipeline.set_params(model__n_jobs=-1)  # speed only; results do not depend on it
        pipeline.fit(X_tr, y_tr)
        values, base, _ = X.shap_values_cached(f"stability_{split_seed}_{model_seed}", pipeline, X_shap)
        grouped = X.group_columns(values, pipeline)
        grouped.index = X_shap.index
        return {
            "shap": grouped,  # SHAP value of each original feature for each of the 2,000 flows
            "interne": X.forest_importance(pipeline),
            "PR-AUC validation": average_precision_score(y_va, pipeline.predict_proba(X_va)[:, 1]),
            "PR-AUC test": average_precision_score(y_test, pipeline.predict_proba(X_test)[:, 1]),
        }

    result, _ = cache.load_or_compute(f"stability_split{split_seed}_seed{model_seed}.joblib", key, compute)
    return result


def summarise(runs, reference, top=10):
    """One row per run: agreement of its global ranking with the reference."""
    ref_imp = reference["shap"].abs().mean()
    ref_top = set(ref_imp.sort_values(ascending=False).index[:top])
    rows = {}
    for name, r in runs.items():
        imp = r["shap"].abs().mean()
        ranks = imp.rank(ascending=False)
        rows[name] = {
            "PR-AUC validation": r["PR-AUC validation"],
            "PR-AUC test": r["PR-AUC test"],
            "rang de sttl": int(ranks["sttl"]),
            "rang de ct_state_ttl": int(ranks["ct_state_ttl"]),
            "part TTL dans SHAP": imp[["sttl", "dttl", "ct_state_ttl"]].sum() / imp.sum(),
            f"top {top} en commun": len(ref_top & set(imp.sort_values(ascending=False).index[:top])),
            "Spearman (SHAP)": imp.corr(ref_imp, method="spearman"),
            "Spearman (interne)": r["interne"].corr(reference["interne"], method="spearman"),
        }
    table = pd.DataFrame(rows).T
    counts = ["rang de sttl", "rang de ct_state_ttl", f"top {top} en commun"]
    return table.astype({c: int for c in counts})


def top_features(runs, top=10):
    """The top features of each run, side by side."""
    return pd.DataFrame({name: list(r["shap"].abs().mean().sort_values(ascending=False).index[:top])
                         for name, r in runs.items()}, index=range(1, top + 1))


def case_stability(runs, cases):
    """For each explained flow: its main contributor and the sttl contribution, run by run."""
    rows = []
    for case, idx in cases.items():
        for name, r in runs.items():
            contrib = r["shap"].loc[idx]
            main = contrib.abs().idxmax()
            rows.append({"cas": case, "variante": name, "variable principale": main,
                         "contribution de sttl": contrib["sttl"]})
    return pd.DataFrame(rows)
