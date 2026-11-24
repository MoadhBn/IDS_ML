"""Turning the raw features into numbers a model can use.

The transformation is a scikit-learn ColumnTransformer. It is placed inside
each model's Pipeline, so that it is fitted on the training data only, and,
during cross-validation, on the training folds only. That is what keeps the
validation and test sets out of every learned operation.
"""

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src import config


def build_preprocessor(numeric_columns, scale=False):
    """One-hot encode the text columns, optionally standardise the numeric ones.

    - Text columns (`proto`, `service`, `state`): one-hot encoding, with
      `handle_unknown="ignore"` because the test file contains `state` values
      never seen in training. An unknown value simply gets all zeros.
    - Numeric columns: standardised (mean 0, standard deviation 1) only when
      `scale=True`. Logistic regression needs it; trees do not, and leaving
      the raw values makes the tree explanations readable in real units
      (bytes, seconds, TTL).
    """
    numeric = StandardScaler() if scale else "passthrough"
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), config.CATEGORICAL),
            ("num", numeric, list(numeric_columns)),
        ],
        verbose_feature_names_out=False,
    )


def numeric_columns(X):
    """Every feature that is not one of the text columns."""
    return [c for c in X.columns if c not in config.CATEGORICAL]
