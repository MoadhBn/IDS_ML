# 02 - Project structure and Git

## The layout

```
ids-explainability/
├── README.md               entry point: what the project is, how to run it
├── requirements.txt        exact library versions
├── .gitignore              what Git must never track
├── data/
│   ├── README.md           how to download the dataset
│   ├── raw/                the CSV files as downloaded (not versioned)
│   └── processed/          cleaned data produced by the notebook (not versioned)
├── notebooks/
│   └── ids_explainability.ipynb   the deliverable: code and report together
├── src/
│   ├── __init__.py
│   ├── config.py           paths, random seed, column groups, SHAP limit
│   ├── data.py             loading, cleaning and splitting (phase 1)
│   ├── preprocessing.py    one-hot encoding and scaling (phase 1)
│   └── models.py           pipelines, hyperparameter search, timing (phase 2)
├── scripts/
│   ├── check_env.py        checks installed library versions
│   └── check_data.py       checks the downloaded files
├── reports/
│   └── figures/            figures exported from the notebook
└── docs/                   this documentation, one file per phase
```

## Why it is organised this way

The course asks for a single notebook that runs from top to bottom and also serves as the report. So the notebook is the centre of the project, and everything else exists to keep it short and readable.

`src/` holds the code the notebook would otherwise repeat. Right now that is only `config.py`, which gathers every setting in one place (where the data lives, the random seed, which columns are the target, the identifier and the text columns), and `data.py`, which reads the two CSV files and stops with a clear message if they are missing. When we reach the evaluation and SHAP phases, the helper functions for those will go into `src/` as well, so that the notebook shows the reasoning and the results rather than fifty lines of plotting code each time. We are not creating empty files for them in advance; they will be written when they are needed.

The seed lives in `config.py` and the notebook calls `config.set_seed()` in its first cell. The models will also receive `random_state=config.SEED` explicitly, because scikit-learn and XGBoost do not read the global seed reliably. Fixed seeds are one of the reproducibility requirements, and the stability check of the explanations (section 5.5 of the notebook) will deliberately change this seed to see whether the conclusions hold.

`scripts/` contains small checks you run from the terminal, outside the notebook. They exist so that a problem with the installation or the data shows up in ten seconds, not in the middle of a long notebook run.

`data/raw/` and `data/processed/` are ignored by Git, as the rules require. The empty `.gitkeep` files inside them are only there because Git does not track empty folders; they let the folder structure exist on a fresh clone.

`reports/figures/` will receive the figures we want to reuse in the presentation slides.

## The notebook outline

The notebook already contains its section titles, following the report structure the course asks for (problem, data, methods, results, critical analysis, limits) and the work listed in the specification for subject 1:

0. Setup: imports, library versions printed, seed fixed.
1. Problem statement.
2. Data: description, cleaning, train/validation/test split.
3. Models: baseline, random forest, XGBoost, and their comparison including training and inference time.
4. Evaluation: confusion matrices, per-class precision/recall/F1, precision-recall curves and PR-AUC, cost of false positives versus false negatives.
5. Explainability: the three importance measures, five explained alerts (two true positives, two false positives, one false negative), plausibility audit of the top ten features, ablation of suspicious features, stability of the explanations.
6. Critical analysis: does the model learn attack behaviour or quirks of the dataset?
7. Limits.
8. References.

The notebook text is in French because the report is graded in French. The documentation in `docs/` is in English, our working language. Only the first cell has code for now; it prints the library versions so they appear in the report, which also covers the "library versions" requirement.

## Git

Commits and pushes are done by hand, by us, never by an assistant. Each phase of the project ends with one or a few commits, so the history follows the phases described in `docs/`.

Because the course grades the history of each member's contributions, each of us must commit from our own machine with our own name and email set in Git, instead of one person committing everything.

### Initialising the repository (done once)

From the project folder:

```powershell
git init -b main
```

This creates the hidden `.git` folder and names the first branch `main`.

```powershell
git status
```

Before adding anything, read this list. You should see the code, the docs and the empty folders, and you should **not** see `.venv/`, any CSV file, or `__pycache__/`. If one of them appears, `.gitignore` is not doing its job and must be fixed first: once a file has been committed, ignoring it later does not remove it from the history.

```powershell
git add .
```

```powershell
git commit -m "Phase 0: subject choice, environment and project skeleton"
```

### Connecting to GitHub (or GitLab)

Create an empty repository on the website, without a README or .gitignore (we already have both), then:

```powershell
git remote add origin <the repository URL>
```

```powershell
git push -u origin main
```

The `-u` option remembers the link between the local `main` and the remote one, so later pushes are just `git push`.

Add the other member of the pair as a collaborator on the website so they can push too.
