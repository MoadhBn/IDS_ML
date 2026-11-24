"""Loading, cleaning and splitting the UNSW-NB15 partition files.

Every function here returns new DataFrames and never modifies its input, so
the notebook can always compare "before" and "after".

Order used in the notebook (see docs/04-cleaning-and-split.md):
    1. load_raw            read the two official files
    2. clean               drop `id`, duplicates and contradictory rows
    3. remove_overlap      drop test rows whose features already appear in training
    4. split_train_val     cut the cleaned training file into training / validation
    5. get_xy              separate the features from the label
"""

import pandas as pd
from sklearn.model_selection import train_test_split

from src import config


# ---------------------------------------------------------------------------
# 1. Loading
# ---------------------------------------------------------------------------
def _read(path):
    if not path.exists():
        raise FileNotFoundError(
            f"{path.name} not found in {path.parent}.\n"
            "Download the UNSW-NB15 partition files first (see data/README.md)."
        )
    return pd.read_csv(path)


def load_raw():
    """Return the official training and testing partitions as two DataFrames."""
    train = _read(config.TRAIN_FILE)
    test = _read(config.TEST_FILE)
    return train, test


def feature_columns(df):
    """The 42 flow features: everything except the identifier, family and label."""
    excluded = set(config.ID_COLUMNS) | {config.ATTACK_CAT, config.TARGET}
    return [c for c in df.columns if c not in excluded]


# ---------------------------------------------------------------------------
# 2. Cleaning
# ---------------------------------------------------------------------------
def clean(df):
    """Drop the identifier, duplicate rows and contradictory rows.

    - `id` only reflects the row order of the file, and that order is grouped
      by label, so it is removed.
    - Two rows are duplicates when they have the same features and the same
      label. We keep the first one.
    - A feature vector seen with both labels (normal and attack) cannot be
      classified correctly on both sides. All its rows are removed.

    Returns the cleaned DataFrame and a dict of counts for the report.
    """
    features = feature_columns(df)
    out = df.drop(columns=config.ID_COLUMNS)
    report = {"rows_before": len(out)}

    # Duplicates: same features and same label
    dup_mask = out.duplicated(subset=features + [config.TARGET], keep="first")
    out = out[~dup_mask]
    report["duplicates_removed"] = int(dup_mask.sum())

    # Contradictions: same features, different labels
    n_labels = out.groupby(features, sort=False)[config.TARGET].transform("nunique")
    conflict_mask = n_labels > 1
    report["conflicting_vectors"] = int(out[conflict_mask][features].drop_duplicates().shape[0])
    report["conflicting_rows_removed"] = int(conflict_mask.sum())
    out = out[~conflict_mask]

    report["rows_after"] = len(out)
    return out.reset_index(drop=True), report


def remove_overlap(test, train):
    """Drop test rows whose feature vector also appears in the training data.

    A model can get these rows right by memory alone, which would make the
    test score a measure of memory rather than generalisation. The check is
    made on the features only, whatever the label.
    """
    features = feature_columns(test)
    seen = train[features].drop_duplicates()
    merged = test.merge(seen, on=features, how="left", indicator=True)
    keep = (merged["_merge"] == "left_only").to_numpy()
    report = {"rows_before": len(test), "overlap_removed": int((~keep).sum())}
    out = test[keep].reset_index(drop=True)
    report["rows_after"] = len(out)
    return out, report


# ---------------------------------------------------------------------------
# 3. Splitting
# ---------------------------------------------------------------------------
def split_train_val(df, val_size=0.2, seed=config.SEED):
    """Split the cleaned training file into training and validation sets.

    Stratified on the attack family, so that small families (Worms, Shellcode)
    appear in both parts in the same proportion. Stratifying on the family
    also keeps the normal/attack ratio, since "Normal" is one of the families.
    """
    train, val = train_test_split(
        df,
        test_size=val_size,
        stratify=df[config.ATTACK_CAT],
        random_state=seed,
        shuffle=True,
    )
    return train.reset_index(drop=True), val.reset_index(drop=True)


def get_xy(df):
    """Return (X, y, family): features, binary label, and attack family for analysis."""
    return df[feature_columns(df)], df[config.TARGET], df[config.ATTACK_CAT]
