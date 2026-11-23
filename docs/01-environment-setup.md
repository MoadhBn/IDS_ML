# 01 - Preparing the working environment

This page explains what we install, why, and in which order. Every command below is typed in PowerShell, from the project folder `C:\Users\moadh\Documents\ids-explainability`, unless said otherwise.

## The tools and why we need them

**Python 3.11.** The course requires Python and scikit-learn. We use 3.11 rather than the newest Python on purpose: every library we need has had ready-made Windows packages for 3.11 for a long time, so nothing has to be compiled during installation. It is also close to what Google Colab runs, which matters if one of us works there. On this machine, 3.11 is reachable through the Windows launcher with `py -3.11`. Another Python (3.13, installed with Laragon) is also on the PATH, which is exactly why we always name the version explicitly instead of typing just `python` before the virtual environment exists.

**A virtual environment (`.venv`).** It is a private copy of Python that lives inside the project folder. Libraries installed there do not touch the rest of the computer, and other projects cannot break ours by upgrading a shared library. It also makes the reproducibility requirement concrete: the environment is rebuilt from one file, `requirements.txt`.

**Git.** Already installed (version 2.52). The course asks for a repository that shows each member's contributions over time.

**Visual Studio Code** with the Python and Jupyter extensions, to edit the code and run the notebook. The Python extensions are already installed; the Jupyter extension (`ms-toolsai.jupyter`) is not yet. JupyterLab in the browser works just as well if one of us prefers it, it is installed with the libraries.

## The libraries and what each one is for

All versions are pinned in `requirements.txt`. Pinning means we write the exact version (`pandas==2.2.3`) instead of just the name. Without it, someone installing the project in three months could get newer versions that behave slightly differently and produce different numbers. Before writing the file we checked that this exact set of versions can be installed together on Python 3.11 under Windows.

- `numpy` and `scipy`: arrays and the maths underneath everything else.
- `pandas`: reading the CSV files and handling them as tables.
- `scikit-learn`: the baseline (logistic regression), the random forest, cross-validation, the metrics (confusion matrix, precision, recall, F1, PR-AUC) and permutation importance.
- `xgboost`: the gradient boosting model required by the common base.
- `shap`: explains individual predictions and gives a global importance ranking. It relies on `numba`, which we pin as well because SHAP is picky about its version.
- `matplotlib` and `seaborn`: every figure (confusion matrices, precision-recall curves, SHAP plots).
- `jupyterlab` and `ipykernel`: running the notebook, which is the main deliverable.

We deliberately do not add anything else. No deep learning framework, no experiment tracker, no data versioning tool: the subject does not need them and every extra tool is one more thing to install and explain.

## Step by step

### 1. Create the virtual environment

```powershell
py -3.11 -m venv .venv
```

This creates a `.venv` folder in the project. It is listed in `.gitignore`, so it will never be pushed.

### 2. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

That is the PowerShell version. In the classic Command Prompt (cmd), where the prompt looks like `C:\...>` with no `PS` in front, the activation script is a different file:

```
.venv\Scripts\activate.bat
```

All the other commands on this page are the same in both shells.

Either way, the prompt now starts with `(.venv)`. From here on, `python` and `pip` refer to the project's own copy. You need to activate it again each time you open a new terminal.

If PowerShell refuses with a message about scripts being disabled on this system, that is a Windows security policy, not a project problem. You can skip activation entirely and call the environment's Python by its path instead, for example `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. Every command below works the same way with that prefix.

### 3. Upgrade pip, then install the libraries

```powershell
python -m pip install --upgrade pip
```

```powershell
python -m pip install -r requirements.txt
```

The second command downloads around a hundred packages (the libraries plus what they depend on). It takes a few minutes the first time.

### 4. Register the environment as a notebook kernel

```powershell
python -m ipykernel install --user --name ids-explainability --display-name "Python (ids-explainability)"
```

A kernel is the Python process that runs the notebook cells. This command makes our environment show up under the name "Python (ids-explainability)" in VS Code and JupyterLab, so the notebook runs with the right libraries and not with another Python on the machine. The notebook already asks for that kernel by name.

### 5. Install the Jupyter extension for VS Code

```powershell
code --install-extension ms-toolsai.jupyter
```

### 6. Check the environment

```powershell
python scripts/check_env.py
```

The script reads `requirements.txt`, compares each pinned version with what is actually installed, and tries to import scikit-learn, XGBoost and SHAP. It should end with "Environment OK.". If it reports a mismatch, the usual cause is that the environment was not activated and another Python answered.

### 7. Download the data

The steps are in `data/README.md`. In short: download the two official UNSW-NB15 partition files, put them in `data/raw/` without renaming them, then run:

```powershell
python scripts/check_data.py
```

It prints the number of rows and columns of each file and the share of attacks, and warns if anything differs from the published figures. It does not modify the files.

## What happened when we ran it

On 23 November 2026 we ran these steps on Moadh's laptop (Windows 11), from the Command Prompt rather than PowerShell. The virtual environment was created with Python 3.11.9. Every pinned library installed with no conflict. The notebook kernel was registered in `C:\Users\moadh\AppData\Roaming\jupyter\kernels\ids-explainability`. `check_env.py` reported all eleven libraries at the expected version and ended with "Environment OK.".

## Working on Google Colab instead

The course allows free Colab. The project works there too: clone the repository, upload the two CSV files into `data/raw/`, and run `pip install -r requirements.txt` in a first cell. Colab's Python version may differ from ours, so if a pinned version refuses to install there, note which one and we will adjust together rather than silently changing the file.
