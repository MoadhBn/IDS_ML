# 11 - Writing the conclusion and preparing the submission

The analysis is finished. This phase turns the notebook into a complete report and prepares the project for submission. The notebook now has every section the course asks for: problem, data, methods, results, critical analysis, limits, plus references.

## What was added to the notebook

**A summary at the top**, under the title. A reader who only has two minutes gets the question, the five key results and the conclusion. Juries tend to read the start of a report more carefully than the rest, so the main message should be there.

**Section 1, the problem.** It explains why explaining alerts matters for a SOC, why public intrusion datasets can mislead, and states the central question. It then lays out the approach in five steps, each pointing to the section where it is done. This section was deliberately written last, once we knew what the notebook actually contains.

**Section 6, the critical analysis.** This is where the central question gets its answer. The argument rests on five independent pieces of evidence, each obtained by a different method:

1. the evaluation: false alerts on the test file line up with two TTL values;
2. the global explanations: three different measures put the TTL features at the top;
3. the local explanations: `sttl` is the first reason in all five explained alerts, right or wrong;
4. the audit and the ablation: TTL describes machines, not behaviour, and removing it does not remove the shortcut, because the other features identify the machines perfectly;
5. the stability check: all of this holds across nine retrainings.

The conclusion is that on UNSW-NB15 the models largely learn which lab machines produced the traffic. We were careful not to overstate it. The section also says what the models do learn from behaviour: logistic regression, which cannot rebuild the machine identity, still scores well above chance without TTL. On this dataset, the two cannot be cleanly separated.

The section then steps back to what this says about evaluating detectors in general: a high score is not enough, explanations served as a diagnostic tool rather than a justification, and the share of attacks in real traffic changes everything (the base-rate problem). It ends with what we would do differently for a real deployment.

**Section 7, the limits.** Ten limits, stated plainly: one dataset, machine identity approximated by TTL, no chronological split, scores not comparable with papers using raw files, a limited hyperparameter search, fixed hyperparameters for ablation and stability, SHAP on a sample and only for the forest, a threshold chosen by F1, laptop timings, and flow features that cannot see packet content.

**Section 8, the references.** Twelve references in four groups: the dataset, the models and tools, explainability, and machine learning for security. Four of them support specific points of the critical analysis:

- Arp et al. (2022) on spurious correlations in security datasets;
- Geirhos et al. (2020) on shortcut learning;
- Axelsson (2000) on the base-rate fallacy in intrusion detection;
- Strobl et al. (2007) on the bias of the forest's internal importance.

## Checking against the specification

The minimum success criteria of subject 1, and where each one is met:

- three importance measures compared: section 5.1, with the comparison table and figure;
- five local explanations written up: section 5.2, two true positives, two false positives and one false negative, each with an analyst note;
- at least one suspicious feature identified and tested by ablation: sections 5.3 and 5.4, three suspicious features, two levels of ablation;
- an argued conclusion on whether the model learns attack behaviour or quirks of the dataset: section 6.

The common base:

- data description, cleaning and split without leakage: section 2;
- a baseline, a random forest and XGBoost tuned by cross-validation, compared on performance, training time and inference time: section 3;
- confusion matrices, precision, recall and F1 per class, precision-recall curves and PR-AUC, and the cost of false positives against false negatives: section 4.

The constraints: CPU only, SHAP on at most 2,000 flows, fixed seeds, public data only.

The pitfalls named in the specification:

- identifying features: none in the files, and `id` removed;
- correlated features read in isolation: addressed with the group permutation and the correlation table;
- explanations computed only on training data: all explanations use test flows.

## Before submitting

These steps are for you to do, in this order.

**1. Fill in the names.** The notebook title cell and the README both say "à compléter" / "to fill in" where the pair's names go.

**2. Do one complete run from scratch.** So far most runs reused the cache. The submitted results should come from one uninterrupted computation. In `src/config.py`, set:

```python
RETUNE = True
```

Then, in JupyterLab, restart the kernel and run all cells (Kernel, then Restart Kernel and Run All Cells). Expect 40 to 60 minutes. When it finishes, check that no cell shows an error, and that the key numbers match those in docs 05 to 10. They should be identical, since every seed is fixed. Timings will differ slightly. Then set `RETUNE` back to `False`, so that later runs use the fresh cache.

**3. Save the notebook with its outputs.** Until now, the repository copy had no outputs, because we tested on copies. The graded deliverable must show its results: tables, figures, printed numbers. Save the notebook in JupyterLab after the full run (Ctrl+S) and commit it with its outputs. It is close to 1 MB, which is fine for Git.

**4. Commit and push.**

```
git add .
```

```
git commit -m "Final run with outputs"
```

```
git push
```

**5. Make sure both members appear in the history.** The course grades each member's contributions from the Git history. If your partner has not committed yet, they should make their own commits from their own machine, under their own name. For example, they could fill in the team names, review the limits section, or prepare the presentation material in the repository.

## What is left

- The oral presentation: slides built from the figures in `reports/figures/`, and preparation for individual questions. The study guide (docs/project-guide.pdf) was updated after this phase: it covers every phase's results and gives twenty likely oral questions with short answers.

## Checking it yourself

Run the notebook. With the cache filled, it takes about 70 seconds and ends with section 8.
