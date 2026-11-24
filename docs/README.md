# Documentation

One file per phase, in the order we worked. Each file explains what was done, why, and how to redo it.

For a single read from start to finish, [project-guide.pdf](project-guide.pdf) gathers the subject, the concepts (metrics, models, SHAP), what has been done and the plan for the remaining phases. It reflects the state of the project after phase 1.

- [00 - Choosing the subject](00-choice-of-subject.md): the seven subjects compared, why subject 1 and why UNSW-NB15.
- [01 - Preparing the working environment](01-environment-setup.md): Python, virtual environment, libraries, VS Code, checks.
- [02 - Project structure and Git](02-project-structure.md): what each folder is for, the notebook outline, setting up the repository.
- [03 - First look at the data](03-first-look-at-the-data.md): what the raw files contain, the problems found (duplicates, leaking `id`, overlap between files, suspicious TTL), and the published analysis we cite.
- [04 - Cleaning and splitting the data](04-cleaning-and-split.md): the cleaning rules, why they run in that order, the three final sets and the encoding.
- [05 - Training and tuning the three models](05-models.md): the common protocol, the hyperparameter searches, the results and what they mean.
- [06 - Evaluating the models](06-evaluation.md): threshold choice, test results, why precision collapses on the test file, and the cost of errors.
- [07 - What the model relies on: three importance measures](07-global-importance.md): internal, permutation and SHAP importance compared, the weight of the TTL features, and why the rankings differ.
