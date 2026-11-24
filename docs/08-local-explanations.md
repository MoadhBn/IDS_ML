# 08 - Five alerts explained one by one

Phase 4 looked at the model as a whole. This phase looks at individual decisions, as an analyst in a security operations centre would. The specification asks for at least five flows from the test set, explained with SHAP: two true positives, two false positives and one false negative. For each, we write what an analyst would write.

The helpers are in `src/explain.py` (`pick_cases`, `explanation_for`, `plot_waterfall`). Section 5.2 of the notebook holds the five explanations and the analyst notes in French. The five charts are saved in `reports/figures/` as `alerte_vp1.png`, `alerte_vp2.png`, `alerte_fp1.png`, `alerte_fp2.png` and `alerte_fn.png`.

## How the five flows were chosen

The easy trap would be to browse the test set and pick flows that tell a nice story. To avoid it, we wrote the selection rules down first and let a seeded random draw do the rest:

- two true positives from two different attack families, namely the two most common families among the true positives;
- two false positives, one with `sttl` = 254 and one with `sttl` = 62, because phase 3 showed that these two values produce the false alerts;
- one false negative.

All five come from the same 2,000 test flows used for SHAP in phase 4, so no new SHAP computation is needed. The model is the random forest, at the threshold chosen on validation (0.482).

In that sample, the forest gives 716 true positives, 355 false positives, 924 true negatives and only 5 false negatives, all five of them Fuzzers. The two most common families among true positives are Exploits and Fuzzers.

## How to read the charts

Each chart is a SHAP waterfall. It starts at the bottom from the base value, 0.488, which is the model's average score. Each bar adds one feature's contribution, red when it pushes towards "attack" and blue when it pushes towards "normal", until it reaches the flow's final score at the top. On the left, each feature's value for this flow is shown in its real units: TTL, bytes, seconds, counts. That is why the trees were left unscaled in phase 1.

The text features are shown as one line each (for example `service = http`), because their one-hot columns were added back together.

## The five flows

**True positive 1, Exploits, score 0.905.** A two-second HTTP connection with 10 packets each way, about 830 bytes sent and 1,360 received, closed normally. The alert comes almost entirely from the TTL features: `sttl` = 62 adds 0.18, and `ct_state_ttl` and `dttl` add 0.13 more between them. Low connection counters follow (first exchange of this kind between these hosts recently). Nothing in the volumes or the timing looks abnormal. An analyst would say the alert is right but rests on a reason they cannot check: a TTL of 62 typically means a system starting at 64, such as Linux, two routers away. The exploit itself, if there is one, lives in the HTTP content, which the flow features do not describe.

**True positive 2, Fuzzers, score 0.559.** A one-second TCP connection with no recognised service, 10 packets out and 6 back, 534 bytes sent and 268 received. Just above the threshold. `sttl` = 254 adds 0.19 and the small volumes take away 0.16. Without the TTL this flow would fall below the threshold. Nothing in it describes fuzzing, which shows up as many repeated connections to the same service rather than as one flow.

**False positive 1, normal traffic with `sttl` = 254, score 0.649.** Same shape as the previous flow: 10 packets out, 6 back, the same 268 bytes received, the same TTL values. It only sends more data. `sttl` = 254 adds 0.19 and decides the alert. This is the pattern behind most of the thousands of false alerts on the test set.

**False positive 2, normal traffic with `sttl` = 62, score 0.880.** The most instructive of the five. A one-second HTTP connection with 10 packets each way, 810 bytes sent and 1,160 received. Its explanation is almost a copy of true positive 1, with the same features in the same order and nearly the same contributions. The two flows are practically twins: same protocol, service, packet counts and TTLs, and very close volumes. To the model they are the same flow. To an analyst holding only these statistics, they would be too. What separates a legitimate web request from one that exploits a vulnerability is the content.

**False negative, a missed Fuzzers attack, score 0.359.** Again the same shape: 10 packets out, 6 back, 268 bytes received, `sttl` = 254. The TTL pushes towards "attack" (+0.16), but the connection counters pull harder the other way: `ct_srv_dst` = 13, meaning 13 recent connections to the same service, takes away 0.14. The model has learned that a busy service is usually normal, which is true on average (an active server), but repeated connections to one service are also exactly what a fuzzer produces. The same value can mean "busy server" or "repeated attack" depending on context, and a per-flow model has no access to that context.

The notebook ends section 5.2 with a table showing the five flows side by side. The resemblances are plain to see.

## What the five explanations show together

**TTL dominates every decision, whatever the answer.** In all five flows, `sttl` is the largest push towards "attack", between +0.16 and +0.19, whether the flow is an attack or normal traffic. A feature that pushes the same way for attacks and for normal flows is not recognising attacks. It is recognising the kind of machine that sent the packets.

**The errors come from flows that cannot be told apart.** True positive 1 and false positive 2 are near twins. So are true positive 2, false positive 1 and the false negative. This is not a tuning problem. These flows have the same statistics, and the decision is made on small differences in volume or in counters. It is the class overlap that Zoghi and Serpen (2021) describe for UNSW-NB15, seen here one flow at a time.

**The explanations would not help an analyst confirm an alert.** "Alert because TTL = 62" gives an analyst nothing to verify. They would have to go back to the packet contents anyway. Explainability did its job, but not the job we might have hoped for. It did not justify the alerts. It showed that they rest on a clue unrelated to the attacks.

We are careful not to generalise from five flows. Phase 6 checks the plausibility of the ten most important features from a network point of view, and measures what the model is worth once the suspicious ones are removed.

## A note for the oral

Two of the specification's pitfalls are relevant here. Explanations must be computed on test data, not only on training data: all five flows come from the test set. And correlated features must not be read as isolated effects: when we say "TTL", we mean the group `sttl`, `ct_state_ttl` and `dttl`, which move together and are shown separately in the charts.

## Checking it yourself

Run the notebook. With the cache filled it takes under 30 seconds. The same five flows are selected every time, because the draw uses the project seed. The scores and contributions quoted here should come out identical.
