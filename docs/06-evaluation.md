# 06 - Evaluating the models

This phase covers the evaluation part of the common base: confusion matrices, precision, recall and F1 per class, precision-recall curves and PR-AUC, and a discussion of the cost of false positives against false negatives. It is also the moment the test set is opened, once, for the first and only time as an evaluation set.

The code is in `src/evaluation.py`. Section 4 of the notebook uses it and comments the results in French. The figures are saved in `reports/figures/` as `pr_validation.png`, `pr_test.png` and `matrices_confusion_test.png`.

## The protocol, and why the order matters

A model does not give a yes or no, it gives a score between 0 and 1. To turn it into an alert we need a threshold. The default of 0.5 has no special meaning: the scores of a forest or of XGBoost are not calibrated probabilities, and each model has its own useful range. So the threshold is a decision, and decisions are made on the validation set.

The rule we used: for each model, take the threshold that gives the best F1 on the validation set. F1 balances precision and recall with equal weight. We wrote this rule down before looking at any test result and did not change it afterwards. If we had looked at the test first and then picked a rule that looked good there, the test would no longer be an honest measure.

Then the test set is scored once, with those thresholds, and everything the course asks for is computed from that single pass. Everything after that in section 4 is analysis meant to understand the results. Nothing is retuned.

The thresholds chosen on validation were 0.10 for logistic regression, 0.48 for the forest and 0.53 for XGBoost.

## Results on validation

At those thresholds, on the validation set:

- logistic regression: precision 0.83, recall 0.998, F1 0.906;
- forest: precision 0.91, recall 0.96, F1 0.934;
- XGBoost: precision 0.93, recall 0.94, F1 0.934.

XGBoost flags 7 % of the normal validation flows by mistake (738 out of 10,333).

## Results on test

The test set has 52,640 flows, 36.1 % of them attacks. That 0.361 is also the PR-AUC a random model would get.

- logistic regression: PR-AUC 0.865, ROC-AUC 0.911, precision 0.58, recall 0.999, F1 0.732;
- forest: PR-AUC 0.943, ROC-AUC 0.963, precision 0.67, recall 0.97, F1 0.794;
- XGBoost: PR-AUC 0.948, ROC-AUC 0.965, precision 0.69, recall 0.96, F1 0.804.

The order of the models is the same as before, with both tree models ahead of the baseline. All are far above chance. But compared with validation, the scores drop clearly, and the way they drop is the most important finding of this phase.

## What went wrong on the test set

Recall stayed where it was. XGBoost catches 96 % of test attacks, the same as on validation. What collapsed is precision, from 0.93 to 0.69. In plain terms, the models still recognise attacks, but they now raise many false alarms on normal traffic: 7,993 of the 33,662 normal test flows, which is 24 %, against 7 % on validation.

Part of the precision drop is mechanical. The test has fewer attacks (36 % against 49 %), and with fewer attacks around, the same rate of false alarms makes up a bigger share of the alerts. But that cannot be the whole story, because the false alarm rate itself, which does not depend on how many attacks there are, more than tripled. Something about the normal traffic in the test file is different, and the models do not recognise it as normal.

To find out what, we compared the normal traffic of the two files, looking first at `sttl`, the feature flagged as suspicious in phase 1. The result was very clear.

- In the training file, attacks have an `sttl` of either 254 (72 %) or 62 (28 %), and practically nothing else.
- In the test file, normal flows with `sttl` = 31 (half of the normal traffic) never trigger a false alarm. Normal flows with `sttl` = 254 trigger one in 54 % of cases, and those with `sttl` = 62 in 25 %.
- Normal traffic with `sttl` = 254 is twice as common in the test file as in training (39 % against 19 %), and `sttl` = 62 three times as common (11 % against 4 %).
- 99.97 % of XGBoost's false alarms on test have `sttl` of 254 or 62.

It looks as if the model learned something close to "a TTL of 254 or 62 means attack". In the training file that rule is almost always right. In the test file, where far more normal traffic has those TTL values, it fires on thousands of innocent flows.

As explained in the guide, TTL is set by the sender's operating system and decreased by each router. It says nothing about whether traffic is malicious. On the UNSW test bed, the machines that generated the attacks apparently had particular TTL values, and so did some, but not all, of the normal hosts. What the model exploits looks like a trace of the lab setup rather than attack behaviour.

We are careful to call this a correlation for now. The errors line up with `sttl`, but that alone does not prove the model uses `sttl` to decide. Other features tied to the TTL or to the lab hosts (`dttl`, `ct_state_ttl`) could carry the same information. Phases 4 to 6 test it directly with importance measures, SHAP explanations and retraining without the suspicious features. This is the central question of subject 1, and the evaluation has handed us a strong lead.

## Results by attack family

Most families are caught at over 99 % by all three models. The weak spot of the tree models is Fuzzers (83 % for XGBoost, 89 % for the forest), then Analysis for XGBoost (94 %). Fuzzers send random or malformed input to a service, so a single flow of that kind can look like an ordinary connection.

The smallest families, Worms (43 test flows) and Backdoor (70), show high rates, but on so few flows one or two more errors would move them by several points.

Logistic regression has the best recall in every family. That is not a sign of quality: its low threshold makes it flag 41 % of normal traffic.

## The cost of errors

The course asks for a discussion of false positives against false negatives in an operational setting. We made it concrete by translating test results into workload per 10,000 flows.

For every 10,000 test flows, XGBoost raises about 4,965 alerts, 1,518 of them false, and misses 158 attacks. The forest makes the opposite trade: 1,729 false alerts but 96 missed attacks. Logistic regression misses only 6 but produces 2,625 false alerts. None of these is right or wrong in itself; it depends on what the security team can absorb.

Then there is the question of what these numbers would mean on a real network. The test set is 36 % attacks; a real network is nothing like that. Recall and the false alarm rate do not depend on the share of attacks, but precision does, and it can be recomputed for any share. With the false alarm rate measured on test, if attacks were 1 % of traffic, fewer than 4 % of XGBoost's alerts would be real attacks. At 0.1 % of traffic, precision would fall below 0.5 %. Even with the better false alarm rate seen on validation (7 %), precision at 1 % attacks would be around 12 %. A detector usable in a SOC needs a false alarm rate around one in a thousand or lower.

On the two kinds of error: a missed attack can cost far more than a false alert. A breach nobody sees can end in stolen data or encrypted servers, while a false alert costs an analyst a few minutes. That argues for favouring recall. But the argument has a limit. When false alerts come by the thousands, analysts saturate, process alerts faster and less carefully, and end up dismissing the real attack along with the noise. Past a certain volume, false positives create false negatives. This is alert fatigue.

F1, which we used to choose the threshold, weights both errors equally. In production the threshold would rather be set with the team, for example from a number of alerts per day they can handle, and on recent data from the network being monitored. The test precision-recall curve shows that a higher threshold would cut false alarms sharply at the cost of some attacks. We did not tune it there, since the test set must not be used for tuning.

## What this changes for the rest of the project

Before this phase, the scores from phase 2 looked excellent. The test set shows that they do not carry over from one official file to the other, and points at one feature as the likely reason. That is exactly the situation subject 1 was designed to study. In the next phases we stop asking how well the models score and start asking what they rely on:

- phase 4 compares three importance measures and should tell us whether `sttl` and its relatives dominate;
- phase 5 explains individual alerts, and the false positives with `sttl` = 254 are natural candidates;
- phase 6 retrains without the suspicious features to see whether the models hold up.

## Checking it yourself

Run the whole notebook as in the previous phases. With the cache filled, it takes about 15 seconds. All numbers on this page should come out identical. Section 4 prints the share of false alarms with `sttl` of 254 or 62 at the end of 4.4.
