"""Check that the UNSW-NB15 files are in place and look like what we expect.

Run from the project root, with the virtual environment active:
    python scripts/check_data.py

This does not clean or change anything. It only confirms we downloaded the
right files before we start working on them.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config  # noqa: E402
from src.data import load_raw  # noqa: E402

# Values published with the official partition files.
EXPECTED_ROWS = {"training-set": 175_341, "testing-set": 82_332}
EXPECTED_COLUMNS = 45


def describe(name, df):
    print(f"{name}: {len(df):,} rows, {df.shape[1]} columns")
    if len(df) != EXPECTED_ROWS[name]:
        print(f"  warning: expected {EXPECTED_ROWS[name]:,} rows")
    if df.shape[1] != EXPECTED_COLUMNS:
        print(f"  warning: expected {EXPECTED_COLUMNS} columns")
    for col in (config.TARGET, config.ATTACK_CAT, *config.CATEGORICAL):
        if col not in df.columns:
            print(f"  warning: column '{col}' is missing")
    if config.TARGET in df.columns:
        share = df[config.TARGET].mean()
        print(f"  share of attacks (label = 1): {share:.1%}")


def main():
    train, test = load_raw()
    describe("training-set", train)
    describe("testing-set", test)
    print("\nFiles found and readable.")


if __name__ == "__main__":
    main()
