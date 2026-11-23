"""Check that the Python environment matches requirements.txt.

Run from the project root, with the virtual environment active:
    python scripts/check_env.py

It prints the Python version and the version of every library we pinned,
and flags any library that is missing or installed in another version.
"""

import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pinned_requirements():
    """Read 'name==version' lines from requirements.txt."""
    pins = {}
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if "==" in line:
            name, version = line.split("==")
            pins[name.strip()] = version.strip()
    return pins


def main():
    print(f"Python {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info[:2] != (3, 11):
        print("  warning: the project was set up with Python 3.11")

    problems = 0
    for name, wanted in pinned_requirements().items():
        try:
            found = metadata.version(name)
        except metadata.PackageNotFoundError:
            print(f"  MISSING   {name} (expected {wanted})")
            problems += 1
            continue
        status = "ok       " if found == wanted else "MISMATCH "
        if found != wanted:
            problems += 1
        print(f"  {status} {name} {found}" + ("" if found == wanted else f" (expected {wanted})"))

    # Import the heavy libraries once, to catch broken installs early.
    import shap  # noqa: F401
    import sklearn  # noqa: F401
    import xgboost  # noqa: F401

    print()
    print("Environment OK." if problems == 0 else f"{problems} problem(s) found, see above.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
