# Explaining an intrusion detector (UNSW-NB15)

Machine Learning for cyber security course project, subject 1: "Expliquer un détecteur d'intrusion".

We train three intrusion detectors on network flows (logistic regression, random forest, XGBoost), evaluate them with metrics suited to imbalanced classes, then use feature importance, permutation importance and SHAP to understand why they raise alerts. The central question is whether the models learn real attack behaviour or artefacts of how the dataset was collected.

Team: *to fill in*

## Running the project

Requirements: Python 3.11 and Git. Full explanations are in [docs/01-environment-setup.md](docs/01-environment-setup.md).

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m ipykernel install --user --name ids-explainability --display-name "Python (ids-explainability)"
python scripts/check_env.py
```

Download the dataset as described in [data/README.md](data/README.md), then:

```powershell
python scripts/check_data.py
```

Open `notebooks/ids_explainability.ipynb` with the "Python (ids-explainability)" kernel and run all cells from top to bottom.

## Reproducibility

Library versions are pinned in `requirements.txt` and printed in the first notebook cell. The random seed is set once in `src/config.py`. Raw data is not stored in the repository.

## Documentation

See [docs/](docs/README.md), one file per project phase.
