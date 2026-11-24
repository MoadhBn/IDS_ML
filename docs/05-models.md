# 05 - Training and tuning the three models

The common base asks for three models: a simple baseline, a random forest and XGBoost, with hyperparameters tuned by cross-validation, and a short comparison of their performance, training time and inference time. This phase does exactly that. The full evaluation (confusion matrices, per-class metrics, curves, threshold, test set) is the next phase.

The code is in `src/models.py`. Section 3 of the notebook calls it and comments the results in French.

## One protocol for all three

To compare models fairly, they have to be treated the same way. All three follow these rules.

**Each model is a pipeline.** The preprocessing from phase 1 (one-hot encoding, plus scaling for logistic regression) is glued to the classifier in a scikit-learn `Pipeline`. During cross-validation the whole pipeline is refitted on the training folds of each round, so even the list of protocol values or the means used for scaling never come from the fold being scored.

**Tuning uses the training set only.** We use stratified 5-fold cross-validation. The training set is cut into five parts with the same share of attacks in each. Every candidate setting is trained on four parts and scored on the fifth, five times, and the five scores are averaged. The validation and test sets play no part in this.

**The score is PR-AUC.** In scikit-learn it is called `average_precision`. We chose it over F1 because F1 depends on the 0.5 threshold, and we will choose our own threshold later. PR-AUC judges how well the model ranks attacks above normal flows across all thresholds. It is also the metric the course puts first for imbalanced data.

**The seed is 42 everywhere:** for the folds, for drawing the random combinations and for the randomness inside the models.

## Searching the settings

Settings like the number of trees or the depth are not learned by the model. We choose them, and the search tries several and keeps the one with the best cross-validation score.

For logistic regression there is one setting, `C`, the inverse of the regularisation strength. A small `C` forces a simple model, a large `C` lets it fit the data more closely. We try all five values from 0.01 to 100. This is a grid search.

The forest and XGBoost have several settings each, which gives thousands of combinations. Trying them all is out of reach on a laptop, so we draw 12 at random and try those. This is a randomised search. With 5 folds, that makes 60 training runs per model. Twelve is a compromise with computing time, and we state it as such.

What we let vary:

- **Forest:** number of trees (100 to 400), maximum depth (10, 20, 30 or unlimited), minimum number of flows in a leaf (1 to 10), share of features considered at each split (square root of the count, 30 % or 50 %).
- **XGBoost:** number of trees (200 to 800), depth (3 to 10), learning rate (0.03 to 0.2), share of rows and of features drawn for each tree, and minimum leaf weight.

Each classifier runs on a single core, and the search runs twelve fits in parallel instead. That is faster overall, and it lets us time the three models in the same conditions.

## Results

These come from the full notebook run on 24 November 2026, on Moadh's laptop with 12 cores.

The best settings found:

- logistic regression: `C` = 100;
- forest: 200 trees, depth 20, leaves of at least 1 flow, 50 % of features at each split;
- XGBoost: 200 trees, depth 10, learning rate 0.1, 85 % of rows and all features per tree, minimum leaf weight 1.

Performance, with PR-AUC first as cross-validation mean (and standard deviation across folds), then on the validation set:

- logistic regression: 0.9604 (± 0.0026), validation 0.9590, F1 at threshold 0.5 of 0.904;
- forest: 0.9845 (± 0.0009), validation 0.9850, F1 0.933;
- XGBoost: 0.9853 (± 0.0010), validation 0.9852, F1 0.934.

Cost, measured on one core, on two complete runs of the notebook the same day (first run, then second run):

- logistic regression: training 11.4 s then 5.3 s; prediction of 1,000 flows 3.4 ms then 1.5 ms;
- forest: training 208 s then 120 s; prediction 35 ms then 17 ms;
- XGBoost: training 15.1 s then 14.0 s; prediction 9.9 ms then 19.3 ms.

The second run is the one saved in the cache, so its numbers are the ones the notebook shows.

For reference, a model that ranks flows at random would get a PR-AUC of 0.488 on validation, the share of attacks there.

## What the results say

**All three are far above chance**, and the cross-validation scores match the validation scores almost exactly. The variation between folds is tiny. So the models are not overfitting their training folds, and the tuning is stable.

**The tree models clearly beat the baseline.** The easiest way to see it is through the error left over, one minus the PR-AUC. It goes from 0.041 for logistic regression to 0.015 for the trees, about two thirds less. The relations between the features and the label are not linear, and trees capture that.

**The best `C` sits at the edge of the grid.** When the best value is the largest one tried, a larger one might be better still. We checked this outside the notebook: with `C` from 10 to 10,000 the cross-validation PR-AUC stays between 0.9603 and 0.9605. The setting barely matters. What limits logistic regression is that it can only draw a straight boundary.

**The forest and XGBoost cannot be separated on performance.** They differ by 0.0002 on validation, which is smaller than the variation between folds (about 0.001). Saying one is better would be reading noise. XGBoost's best depth, 10, is also the largest we allowed. Allowing deeper trees might gain a few thousandths, but with the two models already this close it would not change any conclusion. We note it as a limit rather than rerun a 35-minute search.

**They differ on training cost, not on prediction cost.** Timings moved a lot between the two runs, sometimes by a factor of two, because other programs on the laptop compete for the processor. So we only keep what held both times. The forest is always by far the slowest to train, eight to fourteen times slower than XGBoost. For prediction, the forest and XGBoost are in the same range, and their order flipped between the two runs: the forest was slower the first time, XGBoost the second. We therefore draw no conclusion on prediction speed between them. All three remain fast enough for near real-time detection, at under 0.05 ms per flow.

This is a small lesson in itself. After the first run we had written that XGBoost predicts three times faster than the forest. A second measurement showed that the difference was noise. A timing taken once on a laptop is a rough indication, not a result.

## Why these scores should make us suspicious

A PR-AUC of 0.985 looks excellent. Subject 1 exists precisely to question numbers like this. In phase 1 we saw that `sttl` alone separates large groups of normal and attack flows almost perfectly, for reasons that probably have more to do with the lab than with attacks. Before trusting these models we need to know what they rely on. That is phases 4 to 6.

## Running time

A full run of the notebook took about 35 minutes the first time and 20 minutes the second, depending on what else the laptop was doing. Most of it is the forest search (23 then 14 minutes), because some of the combinations it draws are heavy (400 trees using half the features at each split, on one core each). XGBoost's search takes 2 to 5 minutes and logistic regression's about a minute. Timing the forest once more for the comparison table adds 2 to 3.5 minutes.

During a full search, the terminal or the notebook may print a few `KeyError` lines mentioning a `joblib_memmapping_folder`. They come from joblib, the library that runs the parallel fits, failing to delete a temporary folder on Windows when its workers shut down. They do not affect the results; the run completes normally.

Every later phase needs the tuned models, and we will run the notebook many times while working on them. Paying 35 minutes each time was not reasonable, so we added a cache.

## The cache

The idea is simple: the first run does the searches and saves their results to disk, and later runs reload them instead of searching again. The code is in `src/cache.py`, and the saved files go to a new `models/` folder.

The danger with any cache is reusing a result that no longer matches the code or the data. Imagine we change a cleaning rule in phase 6: if the notebook silently reloaded models tuned on the old data, every number after that would be wrong, and nothing would tell us. To prevent this, each saved file carries a fingerprint. It is a hash, a short code computed from everything that can change the result of a search:

- the content of the training data, value by value, including the labels, the column names and the row order;
- the search range of the model;
- the seed, the number of folds, the number of random combinations and the scoring metric;
- the pipeline itself (preprocessing and model settings);
- the versions of scikit-learn and XGBoost.

When the notebook asks for a search, the fingerprint of the current inputs is computed and compared with the one stored in the file. If they match, the saved search is reloaded. If anything differs, even one value in one row, the fingerprints differ and the search runs again, then overwrites the file. We checked this on a small example: changing one value, one label, the order of the rows or the search range each produced a different fingerprint.

The timings for the comparison table are cached the same way. A reloaded timing is the one measured on the run that produced it, and the notebook says so.

There is one switch, in `src/config.py`:

```python
RETUNE = False
```

With `False`, the cache is used when it matches. With `True`, it is ignored and every search runs from scratch. Before handing the project in, we will set it to `True` and run the whole notebook once, so that the submitted results come from a complete, uninterrupted run.

The `models/` folder is not versioned: saved searches are large, and anyone can rebuild them by running the notebook. On a fresh clone of the repository the cache is empty, so the first run takes the full 35 minutes. The notebook prints, for each model, whether its search was computed or reloaded, and how long the original search took.

## Checking it yourself

With the virtual environment active, start JupyterLab, open the notebook and run all cells, as in phase 1. On the first run on a machine, expect 20 to 35 minutes. Run it again and section 3 should take seconds and report that each search was reloaded from the cache. We did exactly this: the second run of the whole notebook took 15 seconds, and every score and setting was identical to the run before. The best settings and scores are the same whether computed or reloaded, since every seed is fixed. Training and inference times differ slightly between machines.
