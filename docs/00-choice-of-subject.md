# 00 - Choosing the subject

## What we had to choose from

The course gives us two documents. The first one, "Sujets", describes a common base that every pair has to do, plus six themes to go deeper on (seven if you count the "opening" option on phishing embeddings). The second one, the "Cahiers des charges", turns each theme into a precise specification: what data to use, what work is expected, the minimum success criteria and the classic mistakes to avoid. We treat the specification document as the reference whenever the two disagree, because it is the more detailed and more recent of the two.

Whatever the subject, the common base is the same and is not negotiable:

- describe and clean the dataset, then split it into training, validation and test sets without any leakage (nothing learned from the data is allowed to see the test set, and the test set is used only once, for the final numbers);
- train three models: a simple baseline (logistic regression or a shallow decision tree), a random forest and XGBoost, with hyperparameters tuned by cross-validation;
- evaluate them with metrics that respect the class imbalance: confusion matrix, precision, recall, F1, the precision-recall curve and its area (PR-AUC), and a discussion of what a false positive and a false negative cost in a real security team. Accuracy on its own is refused;
- make everything reproducible: a Git repository showing who did what, a README, fixed random seeds, library versions written down, and raw data kept out of the repository.

Since this base is identical for everyone, the choice of subject only changes the extra work on top of it. That is what we compared.

## How we weighed the subjects

We had three criteria, in this order of importance:

1. How fast the project can be finished (70 % of the decision).
2. How easy it is to understand and to defend in front of the jury (20 %).
3. How useful it is as a line on a CV (10 %).

For speed we looked at three things: the size and state of the dataset (download time, how much cleaning it needs), the number of separate experiments the specification asks for, and whether any part needs tricky engineering. For ease of understanding we asked ourselves whether we could explain every step to someone who has only followed the course. For career value we thought about what a recruiter for a SOC analyst, security engineer or ML-for-security role would actually recognise.

Each subject got a mark out of 10 on each criterion, then a weighted total. The marks are our own judgment, not a measurement, but writing them down forced us to be honest about the reasons.

## Subject by subject

**1. Explaining an intrusion detector** (difficulty ★★). Speed 8, ease 8, career 8, weighted total 8.0.
Once the common base is done, the extra work is mostly analysis of the models we already trained: compare three importance rankings, explain five individual alerts with SHAP, look at the ten most important features with a network eye, retrain without the suspicious ones, and check that the explanations stay stable when the seed changes. There is only one dataset, no attack to simulate and no long series of experiments. SHAP is new to us, but it is well documented and the specification even caps it at 2,000 flows, so it runs quickly on a laptop. Explainability is also a skill people ask for in SOC work: an analyst has to justify why an alert fired.

**2. Attacking your own detector** (★★★). Speed 4, ease 4, career 8, total 4.4.
Very attractive on a CV, but it needs a threat model, a table classifying every feature by how much the attacker controls it, an evasion attack with a query budget, realism checks on the modified samples, a hardened model, and the whole attack replayed against it. Many moving parts, and the realism checks alone can take days.

**3. Poisoning the training data** (★★). Speed 6, ease 7, career 6, total 6.2.
Easy idea to grasp, but the specification asks for two attack types, five contamination rates, at least two models and three seeds per point, plus two defences. That is a lot of training runs and a lot of curves to produce and explain.

**4. Drift and model ageing** (★★★). Speed 3, ease 5, career 7, total 3.8.
Needs a chronological split, two statistical drift tests, three maintenance strategies with their costs, and separating normal-traffic drift from brand-new attacks in CIC-IDS2017. Interesting but clearly the longest one.

**5. Auditing a published evaluation** (★★). Speed 5, ease 7, career 5, total 5.4.
Great for critical thinking, but it needs two datasets, finding and reproducing a public notebook, and a cross-dataset test where features of NSL-KDD have to be matched by hand to those of a recent dataset. That matching step is slow and easy to get wrong.

**6. Anomaly detection without labels** (★★). Speed 5, ease 6, career 7, total 5.4.
Replaces the supervised base with an adapted one, and asks for four detectors, a threshold chosen without test labels, a per-family analysis and a contamination test. DBSCAN cannot predict on new points and One-Class SVM is slow, so both need workarounds that have to be justified.

**7. Pre-trained embeddings for phishing** (★★★). Speed 4, ease 5, career 7, total 4.5.
Three text representations to build and compare, a split by domain, cost measurements, error analysis and an obfuscation test. It also pulls in a sentence-embedding model, which is outside the course tools.

## Decision

We take subject 1, explaining an intrusion detector. It scores highest on speed by a clear margin, which is the criterion that matters most, and it is also the easiest to defend because almost everything we add is reading and questioning the models we already built for the common base. It does not lose anything on career value either.

## Which dataset: UNSW-NB15 rather than CIC-IDS2017

The specification lets us pick between CIC-IDS2017 and UNSW-NB15. We pick UNSW-NB15, again mostly for speed.

The authors of UNSW-NB15 publish a ready-made training file and testing file, two CSV files of about 175,000 and 82,000 flows with 42 features each, a binary label and an attack family column. They are small enough to load in seconds and to work on with a normal laptop or free Colab, which is the computing budget the course allows.

CIC-IDS2017 comes as eight CSV files, close to a gigabyte, split by day. It is known to contain infinite values, duplicate rows, a duplicated column and labelling errors, so the cleaning alone would eat a good part of our time. It would also force a split by day, since the course asks to respect time when data is spread over days.

UNSW-NB15 is not perfect either, and that is actually useful for our subject. The specification asks us to find at least one feature that looks like a collection artefact rather than real attack behaviour, and to back the cleaning with a published analysis of the dataset's known defects. UNSW-NB15 has been studied enough for that. We will look for and cite that analysis during the data phase rather than quoting something now that we have not read.

## Things to confirm with the teacher

The specification says each project is given to a limited number of pairs and that the subject had to be chosen by 5 November. If the choice has not been registered yet, we need the teacher's agreement that subject 1 is still available. The 12 November milestone (a one-page report validating the baseline and the evaluation protocol) should also be checked with the teacher if it was not handed in.
