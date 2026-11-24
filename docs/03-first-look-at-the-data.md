# 03 - First look at the data

Before writing any cleaning code, we looked at the two raw files to know what we are dealing with. Nothing was modified. The numbers below come from the files placed in `data/raw/` on 23 November 2026 and checked with `scripts/check_data.py`.

## The files match what the authors published

The training file has 175,341 rows and the testing file 82,332, both with 45 columns: the `id` column, 42 flow features, the attack family (`attack_cat`) and the binary label (`label`, 1 for an attack). There are 30 integer columns, 11 decimal columns and 4 text columns (`proto`, `service`, `state` and `attack_cat`).

## Things that are fine

There are no missing values and no infinite values in either file, and no negative numbers. No column is constant. This is a real difference from CIC-IDS2017, where infinite values have to be handled.

## Things that need a decision

**Attacks are the majority, not the minority.** 68.1 % of the training rows and 55.1 % of the testing rows are attacks. The course text assumes attacks are rare, which is true in real networks but not in these files, because the authors kept a sample of the normal traffic rather than all of it. This matters for two reasons. First, the reference level of PR-AUC is the share of positives: a model that guesses at random already scores about 0.55 on the test set, so a PR-AUC of 0.95 is less impressive than it looks. Second, the share of attacks is not the same in the two files, so the test set does not have the same distribution as the training set. We have to say this in the report.

The attack families themselves are very unbalanced. In the training file, Generic has 40,000 rows and Worms only 130. Our main model is binary (normal against attack), as the specification asks, but the families will matter when we look at which alerts are explained well and which are missed.

**The `id` column gives the answer away.** The rows are sorted by `id`, and the label is grouped along it: in the training file the first quarter of the ids are all normal and the last quarter are all attacks. A model given `id` would learn the row order, not the traffic. It must be dropped, and the order of the rows must never be used.

**Many rows are exact copies.** Ignoring `id`, 67,601 training rows (38.6 %) and 26,387 testing rows (32.0 %) are exact duplicates of another row in the same file. If we keep them, cross-validation will put copies of the same flow on both sides of a fold, which inflates the scores. Ignoring the label as well, 229 feature vectors appear in the training file with both labels (normal and attack). The model cannot be right on both, and they are an example of the labelling problems the specification warns about.

**Some test rows also appear in training.** 4,247 test rows (5.2 %) are identical, label included, to a row in the training file. A model can get them right just by remembering them. This is a small leak between the two official files.

**One text column has values the model will not have seen.** `state` takes 9 values in training. Two of the test values, `ACC` and `CLO`, never appear in training. The encoding step has to handle unknown values without failing. Also, `service` is `-` (unknown) for 53.7 % of the training rows. That is a real category ("no recognised service"), not a missing value.

**A first suspicious feature: `sttl`.** `sttl` is the time-to-live of the packets sent by the source. In the training file, flows with a TTL of 254 are 90 % attacks, and all 39,455 flows with a TTL of 31 are normal. A TTL mostly depends on the operating system and on the number of routers between the two machines, not on whether the traffic is malicious. A split this clean suggests it reflects how the testbed was built (which machines generated the attacks) rather than attack behaviour. This is exactly the kind of collection artefact subject 1 asks us to find. We note it now and will test it properly in the audit and ablation steps. `ct_state_ttl`, which is computed from the TTL values, is probably affected too.

## The published analysis we will cite

Zoghi and Serpen, "UNSW-NB15 Computer Security Dataset: Analysis through Visualization" (arXiv:2101.05067, 2021). They identify class imbalance and class overlap as the two main problems of the dataset and show them with visualisations. Class overlap means rows that look alike but have different labels. Our 229 contradictory feature vectors are the extreme case of it.

The dataset itself is described in Moustafa and Slay, "UNSW-NB15: a comprehensive data set for network intrusion detection systems" (MilCIS 2015).

## Why we cannot split by time

The course asks for a chronological or by-day split whenever the data is timestamped. The partition files do not contain the start and end time columns (`stime`, `ltime`) of the full dataset, so there is no time to respect. The official train/test separation was made by the authors. We keep it and say why in the report.
