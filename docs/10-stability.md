# 10 - Are the explanations stable?

The last analysis step asked by the specification: check that the explanations do not depend on the random seed or on the way the data was split. If they did, everything concluded in phases 4 to 6 could be an accident of one particular training run.

The code is in `src/stability.py`. Section 5.5 of the notebook runs the experiment and comments it in French.

## What we varied, and what we kept fixed

Two sources of randomness can change a trained forest:

- **the model's seed**, which decides which rows and which features each tree sees;
- **the train/validation split**, which decides which flows the model learns from at all.

We varied them separately, to see which one matters if anything moves:

- four runs with the same split as the original and forest seeds 1, 2, 3 and 4;
- four runs with forest seed 42 and four other splits (split seeds 1, 2, 3 and 4).

Together with the reference run (seed 42, split 42), that makes nine forests.

What stays fixed:

- **the hyperparameters** found in phase 2, so that only the randomness changes;
- **the 2,000 test flows** on which SHAP is computed, the same ones as in phases 4 and 5. Any difference in the explanations therefore comes from the model, not from explaining different flows.

The reference run was recomputed through the same code path as the eight others. It reproduces the importance values of section 5.1 exactly, with a difference of 0.0, which confirms the experiment is set up correctly.

Each run retrains the forest and computes SHAP on 2,000 flows. The nine runs took about 15 minutes the first time and are cached. With the cache, the whole notebook now takes about a minute, most of it spent loading the nine saved runs.

## Results

**The top of the ranking does not move.** In all nine runs, `sttl` is first and `ct_state_ttl` second. Places 3 to 5 are always taken by the same three features, `ct_srv_dst`, `dttl` and `ct_dst_src_ltm`, sometimes in a different order. The share of the TTL features in the total SHAP importance stays between 56 % and 59 %.

**The bottom of the top 10 shuffles, within a small group.** Places 6 to 10 rotate among `service`, `dload`, `dbytes`, `dmean`, `ct_srv_src`, `smean` and `sbytes`. Each run shares 8 to 10 of its top 10 features with the reference. Over all 42 features, the Spearman rank correlation with the reference is at least 0.97, for SHAP and for the forest's internal importance alike. These lower features have close importance values and are correlated with one another, so a small change in the model is enough to swap their order. The practical lesson: do not read anything into the exact position of a feature below the top 5.

**The local explanations are stable too.** For each of the five flows explained in phase 5, `sttl` is the largest contributor in all nine runs, 45 times out of 45, with a contribution between +0.16 and +0.22.

**Performance is stable.** Validation PR-AUC stays between 0.984 and 0.986, test PR-AUC between 0.941 and 0.944.

## What this means

The conclusions of phases 4 to 6 do not depend on the seed or the split. The dominant role of TTL is not a fluke of one training run: it comes back every time, at the same rank and with the same weight.

This matters for the oral. If asked "how do you know SHAP did not just happen to pick TTL this time?", the answer is that nine differently trained forests all put it first, and all five individual explanations kept it as their main reason in every run.

## Limits

- The hyperparameters were not re-tuned for each run. Re-tuning adds its own randomness, but with scores this stable it would be unlikely to change the ranking.
- All runs come from the same training file. Stability here means the model behaves consistently on UNSW-NB15. It says nothing about whether the same model would transfer to another network. Phase 3 and the ablation in phase 6 suggest it would not.
- Only the forest was tested. Comparing the stability of XGBoost's explanations is part of the optional extension.

## Checking it yourself

Run the notebook. With an empty cache, section 5.5 alone takes about 15 minutes. With the cache, about a minute for the whole notebook. The reference check at the start of section 5.5 should print a difference of 0.0e+00.
