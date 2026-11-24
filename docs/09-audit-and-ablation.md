# 09 - Auditing the top features and removing the suspicious ones

This is the heart of the critical analysis. The specification asks for three things here: audit the ten most important features from a network and security point of view, identify at least one suspicious feature, then retrain without the suspicious features and measure the impact. The question to answer is whether the original model was robust.

The code is in `src/models.py` (`refit_without_cached`) and `src/explain.py` (`host_group_probe`). Sections 5.3 and 5.4 of the notebook hold the audit, the ablation and their analysis in French.

## The audit

We took the ten most important features according to SHAP and asked of each one: would a network analyst accept this as a reason for an alert? Each feature got one of three verdicts:

- **plausible**: it describes behaviour that can genuinely separate an attack from normal traffic;
- **to watch**: it describes traffic, but it is strongly tied to a suspicious feature or depends on how the capture was done;
- **suspicious**: it describes the machine or the lab network rather than behaviour, and should not identify an attack anywhere else.

The verdicts:

- `sttl`, the source TTL: **suspicious**. It is set by the sender's operating system and decreased by each router, so it identifies the machine and its position, not the attack.
- `ct_state_ttl`: **suspicious**. It is computed by the dataset authors from the connection state and TTL ranges, and it re-encodes `sttl` and `dttl` directly. For example, its value 1 corresponds exactly to an `sttl` of 62 or 254 with a `dttl` of 252.
- `dttl`, the destination TTL: **suspicious**, for the same reason on the responding side.
- `ct_srv_dst`, `ct_dst_src_ltm` and `ct_srv_src`, counts of recent connections sharing the same service, source or destination: **to watch**. They are plausible, since scans and repeated attacks raise them, but the counts depend on the pace at which the lab generated traffic, and phase 5's missed attack showed that a high count can mean "busy server" as much as "repeated attack".
- `service`: **plausible**. The service targeted is normal context for an alert.
- `dmean` and `dbytes`, the size of the destination's responses: **plausible**.
- `dload`, the destination's throughput: **to watch**. It is derived from bytes and duration, so it is plausible on its face, but it is strongly correlated with the TTL (−0.81).

The evidence behind the three suspicious verdicts is in the notebook, and it is hard to argue with:

- in the training data, not a single attack has `sttl` = 31, and all 31,283 flows with `sttl` = 31 have `dttl` = 29, which is the signature of one pair of machine groups;
- every attack family, without exception, uses only `sttl` 62 or 254;
- normal traffic uses 31 mostly, but also 254 and 62.

So the TTL pair tells you which group of lab machines sent the traffic, and in this lab, the attacking machines are a distinct group.

The specification also warns about identifying features such as addresses, ports and timestamps. Those are not in the partition files, and `id` was removed in phase 1.

## The ablation

We retrained the three models without `sttl`, `dttl` and `ct_state_ttl`. Each model kept the hyperparameters found in phase 2, so the only difference from the original is the set of features. Re-tuning them would have mixed two effects, the missing features and the new settings. The threshold of each model was chosen again on validation with the same rule as before (best F1). The retrained models are cached like everything else.

What we expected: if the models had learned attack behaviour, losing the TTL would cost them a little; if they were leaning on the TTL as a shortcut, they would lose a lot.

What happened was neither.

**The tree models lost almost nothing.** The forest and XGBoost still score 0.985 PR-AUC on validation. On test they lose 0.005 (the forest goes from 0.943 to 0.938, XGBoost from 0.948 to 0.943). Precision, recall and F1 move by one or two points.

**Logistic regression lost a lot.** Its test PR-AUC fell from 0.865 to 0.720. It relied on the TTL, and a linear model cannot rebuild that information by combining other features.

**The false alerts kept exactly the same shape.** This is the key observation. The retrained forest no longer sees `sttl` at all, yet on the normal test traffic:

- flows with `sttl` = 31 are almost never flagged (0.2 %);
- flows with `sttl` = 254 are flagged in 59 to 66 % of cases, slightly more than before;
- flows with `sttl` = 62 are flagged in 28 to 29 % of cases.

If removing the TTL had removed the shortcut, this link between TTL value and errors would have faded. It is intact. The model still sorts traffic by which machines sent it, without needing the TTL columns to do so.

## Proving the machine identity is still there

To check this directly, we built a small test. Using normal traffic only, so the attack label plays no part, we trained a quick XGBoost model to recognise whether a flow has `sttl` 62 or 254 (the values of the attacking machines) or another value, using every feature except the three TTL ones. It was trained on the training set and evaluated on the test set.

It reaches a ROC-AUC of 1.000 and a balanced accuracy of 0.999. In other words, the remaining features identify the machine group perfectly. The probe relies mostly on `dload` (68 % of its importance), the feature the audit had flagged as "to watch" because of its correlation with TTL.

We then removed the three TCP handshake timings as well (`tcprtt`, `synack`, `ackdat`), since they also depend on the machines and their network path. The probe still scored 1.000, and the three detectors retrained without TTL and without timings behaved as before: test PR-AUC of 0.934 and 0.939 for the trees, and the same distribution of false alerts.

Finally, we looked at what the forest relies on once the TTL is gone. Its top SHAP features become `ackdat`, `dload` and `tcprtt`: handshake timings and throughput, the very relays of machine identity.

## So, was the original model robust?

The specification asks this question, and our answer has two parts.

**Robust to ablation, yes.** Its scores survive the removal of the suspicious features.

**But that does not mean it learned attack behaviour.** The ablation shows that the artefact is not a column that can be taken out. It is the layout of the test bed itself. In UNSW-NB15, the attacks come from a specific set of machines, and everything that characterises those machines can be used to recognise them: their TTL, their network delays, their throughput. Removing columns moves the shortcut to other columns without getting rid of it.

**Not robust to a change in normal traffic.** Phase 3 already showed this. As soon as the test file contained more normal traffic coming from the "62/254" machines, the false alarm rate tripled. That kind of robustness is the one that matters for a real deployment, and the model does not have it, with or without the TTL columns.

This is the answer to the central question of subject 1, and section 6 of the notebook will state it as the conclusion: on UNSW-NB15, the models learn largely to recognise which lab machines produced the traffic, a collection artefact, rather than attack behaviour that would carry over to another network.

## Limits of this phase

- The "machine group" is approximated by the TTL value. We do not have IP addresses in the partition files, so we cannot name the machines. The TTL pairs are a strong proxy, but still a proxy.
- We kept the original hyperparameters for the retrained models. Re-tuning them might change the scores slightly. Given how little the scores moved, it would not change the conclusion.
- The probe shows that machine identity can be recovered from the remaining features. It does not show that the detector uses that route for every decision, only that the route is open, and the unchanged pattern of false alerts shows that it is taken.

## Checking it yourself

Run the notebook. On a machine with an empty cache, the six retrained models and the extra SHAP computation add about two minutes. With the cache, the whole notebook runs in under 30 seconds.
