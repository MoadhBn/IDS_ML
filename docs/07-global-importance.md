# 07 - What the model relies on: three importance measures

Up to now we measured how well the models detect attacks. From here on, the question is what they rely on to do it. This phase covers the first piece of work specific to subject 1: compare three measures of feature importance, put them in a table, and discuss why they disagree.

The code is in `src/explain.py`. Section 5.1 of the notebook uses it and comments the results in French. Two figures are saved in `reports/figures/`: `trois_mesures_importance.png` and `shap_beeswarm_foret.png`.

## Which model, and on which features

We explain the random forest. The specification explicitly asks for the forest's internal importance as one of the three measures, so computing the other two on the same model is the only way to compare like with like. Since the forest and XGBoost perform almost identically, we lose nothing by this choice. Comparing the explanations of the two models is listed as an optional extension.

There is one practical detail to settle first. The model does not see 42 features but 192 columns, because the three text features are one-hot encoded (`proto` alone becomes 133 columns). A ranking of 192 columns would scatter `proto` into 133 tiny pieces and make it look unimportant. So every measure is brought back to the 42 original features:

- for the forest's internal importance and for SHAP, we add up the values of all the one-hot columns of each text feature. This is legitimate because both measures are additive by construction;
- permutation importance shuffles the original columns before they go into the pipeline, so it is per original feature from the start.

## The three measures

**The forest's internal importance**, also called mean decrease in impurity. Each time a tree splits on a feature, the two groups it creates are purer than the one before. Adding up those gains over all splits and all trees gives a score per feature, and the scores sum to 1. It costs nothing to compute, but it has two known weaknesses: it is measured on the training data, so it describes how the model fitted, not how it generalises; and it favours features with many distinct values, which offer more possible split points.

**Permutation importance on the test set.** For one feature at a time, we shuffle its values across the test flows, which breaks its link with the label while keeping its distribution, and measure how much the PR-AUC drops. We repeat this five times per feature and average. It works on data the model has never seen. Its weakness is correlated features: if two features carry the same information, shuffling one leaves the other to compensate, and both look less important than they really are.

**Mean absolute SHAP value.** SHAP gives every feature a contribution, positive or negative, to each individual prediction (the guide explains the idea). Averaging the size of those contributions over many flows gives a global ranking. The specification limits SHAP to 2,000 flows. We drew them at random from the test set, stratified by attack family so that rare families are represented in their real proportions. For a forest, SHAP values are in probability points.

The notebook checks the defining property of SHAP before using it: for every flow, the base value (0.488, the average score) plus the sum of all the SHAP values equals the model's score. The largest difference over the 2,000 flows is 3.5e-14, which is rounding error.

The permutation and SHAP computations take about a minute each. They are cached with the same fingerprint mechanism as the hyperparameter searches (doc 05), and SHAP is split across the 12 cores.

## Results

All three measures put the same two features at the top, in the same order: `sttl` first, `ct_state_ttl` second. `dttl` is in the top 7 for all three. The values for the leading features:

- `sttl`: internal 0.374, permutation 0.172, SHAP 0.222;
- `ct_state_ttl`: internal 0.207, permutation 0.045, SHAP 0.093;
- `ct_srv_dst`: internal 0.046, permutation 0.015, SHAP 0.041;
- `dttl`: internal 0.039, permutation 0.015, SHAP 0.040;
- `ct_dst_src_ltm`: internal 0.028, permutation 0.023, SHAP 0.031.

The notebook shows the full comparison table, with values and ranks, for every feature that appears in the top 10 of at least one measure, as the deliverables require.

Over all 42 features, the rankings agree strongly. The Spearman rank correlation is 0.90 between internal importance and SHAP, 0.84 between permutation and SHAP, and 0.75 between internal importance and permutation.

## The weight of TTL, measured properly

The three TTL-related features (`sttl`, `ct_state_ttl`, `dttl`) account for 62 % of the forest's internal importance and 59 % of the total mean absolute SHAP.

They are also strongly linked. `ct_state_ttl` is computed by the dataset authors from the connection state and the TTL values, and its rank correlation with `sttl` is 0.84. That is precisely the situation where single-feature permutation underestimates things. So we added one more measurement: shuffle the three TTL features together, with the same row shuffle for all three, which keeps their relation to each other but cuts their link with the label.

The result: the forest's test PR-AUC drops by 0.29, from 0.943 to about 0.65. Shuffled one at a time, the three drops add up to only 0.23. When a single TTL feature is shuffled, the others make up for part of the loss.

A model guessing at random would score 0.361. The forest's lead over chance is 0.943 − 0.361 = 0.58, and the TTL features alone carry about half of it.

## Direction of the effects

The SHAP beeswarm figure shows each of the 2,000 flows as a dot on each feature's line. Its position is the feature's contribution, right for "towards attack" and left for "towards normal", and its colour is the feature's value, from blue (low) to red (high).

For `sttl` the picture is stark. Low values (31) sit far to the left, lowering the attack probability by about 0.3. High values (254) sit to the right, raising it by about 0.2. Against a base value of 0.49, that is almost enough to decide a flow on its own. It is the mechanism behind the false alerts found in phase 3: a normal flow with `sttl` = 254 starts with a strong push towards "attack".

## Why the rankings disagree where they do

The specification asks us to discuss the differences in ranking. Three effects explain most of them.

**Different data.** Internal importance comes from training; permutation and SHAP were computed on test. `dbytes` is 17th by internal importance but 3rd by permutation. Internal importance tells how much the forest used a feature to separate the training data. Permutation tells how much the feature contributes on new data. There is no reason for them to match, especially when the test traffic differs from the training traffic, as phase 3 showed it does.

**The bias of internal importance.** It favours features with many possible split points. `service` has only 13 values and is 13th by internal importance, but 4th by permutation and 6th by SHAP.

**Correlated features.** `dload` is 4th by internal importance but 9th by permutation and 10th by SHAP. It is strongly correlated with `sttl` (−0.81) and `ct_state_ttl` (−0.85). The forest uses it in some splits, but the information it carries is almost entirely available in the TTL features already, so shuffling it alone costs little. This is the specific pitfall the course warns about: reading the importance of correlated features as if each acted on its own.

Six features get a slightly negative permutation importance (at most −0.002): shuffling them made the score marginally better. This is noise around zero and means they contribute nothing useful.

## Where this leaves us

The three measures, computed independently, tell the same story: the forest relies on the TTL features far more than on anything else, and those features alone carry about half of what it knows beyond chance. Together with phase 3, where the false alerts lined up exactly with `sttl` values, this turns a suspicion into a well-supported finding.

What these measures cannot say is whether relying on TTL is legitimate from a network point of view, or what the model would be worth without it. The next phases answer that: explaining individual alerts (phase 5), then auditing the top ten features and retraining without the suspicious ones (phase 6).

## Checking it yourself

Run the notebook as usual. On a machine where the cache is empty, permutation and SHAP add about two minutes to the first run. With the cache, the whole notebook takes about 20 seconds. All values on this page should come out identical.
