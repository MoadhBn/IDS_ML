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

Cost, measured on one core: logistic regression trains in about 11 seconds and predicts 1,000 flows in 3.4 ms. The forest needs about 208 seconds and 35 ms. XGBoost needs about 15 seconds and 10 ms.

For reference, a model that ranks flows at random would get a PR-AUC of 0.488 on validation, the share of attacks there.

## What the results say

**All three are far above chance**, and the cross-validation scores match the validation scores almost exactly. The variation between folds is tiny. So the models are not overfitting their training folds, and the tuning is stable.

**The tree models clearly beat the baseline.** The easiest way to see it is through the error left over, one minus the PR-AUC. It goes from 0.041 for logistic regression to 0.015 for the trees, about two thirds less. The relations between the features and the label are not linear, and trees capture that.

**The best `C` sits at the edge of the grid.** When the best value is the largest one tried, a larger one might be better still. We checked this outside the notebook: with `C` from 10 to 10,000 the cross-validation PR-AUC stays between 0.9603 and 0.9605. The setting barely matters. What limits logistic regression is that it can only draw a straight boundary.

**The forest and XGBoost cannot be separated on performance.** They differ by 0.0002 on validation, which is smaller than the variation between folds (about 0.001). Saying one is better would be reading noise. XGBoost's best depth, 10, is also the largest we allowed. Allowing deeper trees might gain a few thousandths, but with the two models already this close it would not change any conclusion. We note it as a limit rather than rerun a 35-minute search.

**They do differ on cost.** The forest trains about fourteen times slower than XGBoost and predicts about three times slower. All three remain fast enough for near real-time detection: even the forest handles one flow in well under a tenth of a millisecond. Timings depend on the machine; the ratios between models are what to compare.

## Why these scores should make us suspicious

A PR-AUC of 0.985 looks excellent. Subject 1 exists precisely to question numbers like this. In phase 1 we saw that `sttl` alone separates large groups of normal and attack flows almost perfectly, for reasons that probably have more to do with the lab than with attacks. Before trusting these models we need to know what they rely on. That is phases 4 to 6.

## Running time

The whole notebook now takes about 35 minutes. Most of it is the forest search (23 minutes), because some of the combinations it draws are heavy (400 trees using half the features at each split, on one core each). XGBoost's search takes about 5 minutes and logistic regression's under a minute. Timing the forest once more for the comparison table adds about 3.5 minutes.

## Checking it yourself

With the virtual environment active, start JupyterLab, open the notebook and run all cells, as in phase 1. The best settings and the scores should come out identical, since every seed is fixed. Training and inference times will differ slightly from run to run and from machine to machine.
