"""Project-wide settings: paths, random seed, column groups.

Everything that could change between machines or between experiments lives
here, so the notebook never hard-codes a path or a seed.
"""

import os
import random
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED = 42


def set_seed(seed: int = SEED) -> None:
    """Fix the seeds of every random generator we rely on.

    scikit-learn and XGBoost also receive `random_state=seed` explicitly in
    each model, this function only covers the global generators.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


# ---------------------------------------------------------------------------
# Paths (all relative to the project root, whatever the machine)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"
MODELS_DIR = ROOT / "models"  # cached searches and timings (not versioned)

# False: reuse the cached hyperparameter searches when their inputs have not
# changed (see src/cache.py). True: redo every search from scratch. Set it to
# True for the final run before submission.
RETUNE = False

# Official UNSW-NB15 partition files (see data/README.md to download them).
# Note: the "training-set" file is the larger one (~175k rows) and the
# "testing-set" file the smaller one (~82k rows).
TRAIN_FILE = DATA_RAW / "UNSW_NB15_training-set.csv"
TEST_FILE = DATA_RAW / "UNSW_NB15_testing-set.csv"

# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------
TARGET = "label"          # 0 = normal, 1 = attack (our binary target)
ATTACK_CAT = "attack_cat"  # attack family, kept for analysis only, never a feature
ID_COLUMNS = ["id"]        # row number, carries no network meaning

# Text columns that must be encoded before training
CATEGORICAL = ["proto", "service", "state"]

# ---------------------------------------------------------------------------
# Limits imposed by the specification
# ---------------------------------------------------------------------------
SHAP_MAX_SAMPLES = 2000  # SHAP is computed on at most 2,000 flows
