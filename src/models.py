"""The three models, their hyperparameter search, and their timing.

Each model is a scikit-learn Pipeline: preprocessing first, then the
classifier. Tuning is done by stratified 5-fold cross-validation on the
training set only, scored with PR-AUC (`average_precision` in scikit-learn).
The validation and test sets are never seen during tuning.
"""

import time

from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from src import cache, config
from src.preprocessing import build_preprocessor

CV_FOLDS = 5
SCORING = "average_precision"  # PR-AUC
N_ITER = 12                    # random combinations tried for the forest and XGBoost


def make_pipelines(numeric_columns, seed=config.SEED):
    """Untuned pipelines for the three models.

    Each classifier runs on one core (`n_jobs=1`): the search runs several
    fits in parallel instead, which is faster than parallelising inside each
    fit, and it makes the timings comparable between models.
    """
    return {
        "Régression logistique": Pipeline([
            ("prep", build_preprocessor(numeric_columns, scale=True)),
            ("model", LogisticRegression(max_iter=3000, random_state=seed)),
        ]),
        "Forêt aléatoire": Pipeline([
            ("prep", build_preprocessor(numeric_columns)),
            ("model", RandomForestClassifier(n_jobs=1, random_state=seed)),
        ]),
        "XGBoost": Pipeline([
            ("prep", build_preprocessor(numeric_columns)),
            ("model", XGBClassifier(tree_method="hist", eval_metric="aucpr",
                                    n_jobs=1, random_state=seed)),
        ]),
    }


# Hyperparameters explored. The "model__" prefix tells the Pipeline which step
# the setting belongs to.
SEARCH_SPACES = {
    "Régression logistique": {
        # C is the inverse of the regularisation strength: small C = simpler model.
        "model__C": [0.01, 0.1, 1, 10, 100],
    },
    "Forêt aléatoire": {
        "model__n_estimators": [100, 200, 400],
        "model__max_depth": [None, 10, 20, 30],
        "model__min_samples_leaf": [1, 2, 5, 10],
        "model__max_features": ["sqrt", 0.3, 0.5],
    },
    "XGBoost": {
        "model__n_estimators": [200, 400, 800],
        "model__max_depth": [3, 4, 6, 8, 10],
        "model__learning_rate": [0.03, 0.05, 0.1, 0.2],
        "model__subsample": [0.7, 0.85, 1.0],
        "model__colsample_bytree": [0.5, 0.7, 1.0],
        "model__min_child_weight": [1, 3, 5],
    },
}


def tune(name, pipeline, X, y, seed=config.SEED):
    """Search the hyperparameters of one model by cross-validation.

    Logistic regression has a single setting with five values, so all of them
    are tried (grid search). The forest and XGBoost have thousands of possible
    combinations, so N_ITER random ones are tried (randomised search).

    Returns the fitted search object. Its `best_estimator_` is the pipeline
    refitted on the whole training set with the best settings.
    """
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=seed)
    space = SEARCH_SPACES[name]
    if name == "Régression logistique":
        search = GridSearchCV(pipeline, space, scoring=SCORING, cv=cv, n_jobs=-1)
    else:
        search = RandomizedSearchCV(pipeline, space, n_iter=N_ITER, scoring=SCORING, cv=cv,
                                    n_jobs=-1, random_state=seed)
    search.fit(X, y)
    return search


def time_model(estimator, X_fit, y_fit, X_pred, repeats=3):
    """Training time (seconds) and inference time (milliseconds per 1,000 flows).

    The estimator is cloned and refitted once on one core, so the three models
    are timed in the same conditions. Inference is repeated and the fastest
    run is kept, which removes most of the noise from other programs.
    """
    model = clone(estimator)
    start = time.perf_counter()
    model.fit(X_fit, y_fit)
    fit_seconds = time.perf_counter() - start

    runs = []
    for _ in range(repeats):
        start = time.perf_counter()
        model.predict_proba(X_pred)
        runs.append(time.perf_counter() - start)
    ms_per_1000 = min(runs) / len(X_pred) * 1000 * 1000
    return fit_seconds, ms_per_1000


# ---------------------------------------------------------------------------
# Cached versions (see src/cache.py)
# ---------------------------------------------------------------------------
FILE_NAMES = {
    "Régression logistique": "logistic_regression",
    "Forêt aléatoire": "random_forest",
    "XGBoost": "xgboost",
}


def tune_cached(name, pipeline, X, y, seed=config.SEED):
    """Same as `tune`, but reuses the saved search when nothing has changed.

    Returns (search, search_seconds, from_cache). `search_seconds` is the
    duration of the run that actually did the search.
    """
    key = cache.fingerprint("search", name, cache.data_fingerprint(X, y), SEARCH_SPACES[name],
                            CV_FOLDS, N_ITER, SCORING, seed, repr(pipeline))

    def compute():
        start = time.perf_counter()
        search = tune(name, pipeline, X, y, seed)
        return {"search": search, "seconds": time.perf_counter() - start}

    result, from_cache = cache.load_or_compute(f"search_{FILE_NAMES[name]}.joblib", key, compute)
    return result["search"], result["seconds"], from_cache


def time_model_cached(name, estimator, X_fit, y_fit, X_pred):
    """Same as `time_model`, but reuses the saved timings when nothing has changed.

    Timings reloaded from the cache are those measured on the run that
    produced them.
    """
    key = cache.fingerprint("timing", name, cache.data_fingerprint(X_fit, y_fit),
                            cache.data_fingerprint(X_pred, y_fit.iloc[:0]), repr(estimator))
    result, from_cache = cache.load_or_compute(
        f"timing_{FILE_NAMES[name]}.joblib", key, lambda: time_model(estimator, X_fit, y_fit, X_pred))
    return result[0], result[1], from_cache


def refit_without_cached(name, best_params, X, y, drop, tag, seed=config.SEED):
    """Retrain one model without some features, keeping its tuned settings.

    Used for the ablation: the hyperparameters found in section 3 are kept so
    that the only change is the set of features. The preprocessing is rebuilt
    for the remaining columns. `tag` names the variant in the cache file.
    """
    from src.preprocessing import numeric_columns
    X_kept = X.drop(columns=drop)
    pipeline = make_pipelines(numeric_columns(X_kept), seed)[name]
    pipeline.set_params(**best_params)
    key = cache.fingerprint("ablation", name, tuple(drop), cache.data_fingerprint(X_kept, y), repr(pipeline))

    def compute():
        # Parallel training only speeds things up; results do not depend on it.
        if name != "Régression logistique":
            pipeline.set_params(model__n_jobs=-1)
        return pipeline.fit(X_kept, y)

    model, _ = cache.load_or_compute(f"ablation_{tag}_{FILE_NAMES[name]}.joblib", key, compute)
    return model


def short_params(best_params):
    """Best settings without the 'model__' prefix, for display."""
    return {k.replace("model__", ""): v for k, v in best_params.items()}


def cv_summary(search):
    """Mean and standard deviation of the PR-AUC across folds for the best setting."""
    i = search.best_index_
    res = search.cv_results_
    return float(res["mean_test_score"][i]), float(res["std_test_score"][i])
