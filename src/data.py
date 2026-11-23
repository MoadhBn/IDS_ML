"""Loading the raw UNSW-NB15 files.

Cleaning and splitting will be added here in the data phase. For now this
module only reads the CSV files and fails with a clear message if they are
missing.
"""

import pandas as pd

from src import config


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
