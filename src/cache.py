"""Saving long computations to disk and reloading them on the next run.

The hyperparameter search takes about half an hour. Running it again every
time the notebook is executed would make later phases painful, so its result
is saved in the `models/` folder and reloaded.

A cached result is only reused when it was produced from exactly the same
inputs. Each saved file carries a fingerprint built from everything that
could change the result: the training data, the settings searched, the seed,
the number of folds and the library versions. If any of these changed, the
fingerprint no longer matches and the computation runs again. A stale result
can therefore never be reused by accident.

Setting `config.RETUNE = True` ignores the cache and recomputes everything,
which is what we do for the final run before submission.
"""

import hashlib

import joblib
import pandas as pd
import sklearn
import xgboost

from src import config


def data_fingerprint(X, y):
    """A short hash of the content of X and y (values, columns and order)."""
    h = hashlib.sha256()
    h.update(pd.util.hash_pandas_object(X, index=False).to_numpy().tobytes())
    h.update(pd.util.hash_pandas_object(y, index=False).to_numpy().tobytes())
    h.update(",".join(X.columns).encode())
    return h.hexdigest()


def fingerprint(*parts):
    """Combine any number of values into one hash, including library versions."""
    text = repr(parts) + f"|sklearn={sklearn.__version__}|xgboost={xgboost.__version__}"
    return hashlib.sha256(text.encode()).hexdigest()


def load_or_compute(filename, key, compute):
    """Return the saved result if its fingerprint matches `key`, otherwise compute and save it.

    Returns (result, from_cache) so the notebook can say which happened.
    """
    path = config.MODELS_DIR / filename
    if path.exists() and not config.RETUNE:
        saved = joblib.load(path)
        if saved.get("key") == key:
            return saved["result"], True
    result = compute()
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"key": key, "result": result}, path, compress=3)
    return result, False
