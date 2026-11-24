# Explaining an intrusion detector (UNSW-NB15)

Machine Learning for cyber security course project, subject 1: "Expliquer un détecteur d'intrusion".

We train three intrusion detectors on network flows (logistic regression, random forest, XGBoost), evaluate them with metrics suited to imbalanced classes, then use the forest's internal importance, permutation importance and SHAP to understand why they raise alerts. The central question is whether the models learn real attack behaviour or artefacts of how the dataset was collected.

Team: *to fill in*

## Main findings

- After cleaning (a leaking `id` column, duplicates, contradictory rows and overlap between the two official files), the tree models reach a PR-AUC of 0.985 on validation and about 0.945 on the test file.
- On the test file, precision drops from 0.93 to 0.69 for XGBoost: about one normal flow in four is flagged. Almost all false alerts have a source TTL of 254 or 62, the only two values attacks use in the training data.
- All three importance measures rank `sttl` first and `ct_state_ttl` second. Shuffled together, the TTL features remove half of the forest's lead over chance. In the five alerts explained with SHAP, `sttl` is always the main reason.
- Retraining without the TTL features changes almost nothing, and the false alerts keep the same pattern: the other features identify the lab machines perfectly (ROC-AUC 1.000 on normal traffic).
- These results hold across nine retrainings with other seeds and splits.

Conclusion: on UNSW-NB15, the models largely learn which lab machines produced the traffic, a collection artefact, rather than attack behaviour that would carry over to another network.

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

**Running time.** On a fresh clone the cache is empty, and the first full run takes roughly 40 to 60 minutes on a 12-core laptop (hyperparameter searches, SHAP, ablation and stability runs). Results are cached in `models/`, so later runs take about a minute. Setting `RETUNE = True` in `src/config.py` ignores the cache and recomputes everything. See [docs/05-models.md](docs/05-models.md) for how the cache decides when a saved result can be reused.

## Repository layout

- `notebooks/ids_explainability.ipynb`: the deliverable, code and report (in French).
- `src/`: shared code (configuration, data, preprocessing, models, cache, evaluation, explanations, stability).
- `scripts/`: environment and data checks.
- `reports/figures/`: figures saved by the notebook.
- `docs/`: one note per project phase, plus a study guide (in English).

## Reproducibility

Library versions are pinned in `requirements.txt` and printed in the first notebook cell. The random seed is set once in `src/config.py`. Raw data is not stored in the repository; `data/README.md` explains how to download it.

## Documentation

See [docs/](docs/README.md), one file per project phase.
