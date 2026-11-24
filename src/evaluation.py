"""Evaluation helpers: threshold choice, metrics, figures.

The threshold is always chosen on the validation set. The functions that
take test data only compute and draw; they never choose anything.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (ConfusionMatrixDisplay, average_precision_score, confusion_matrix,
                             f1_score, precision_recall_curve, precision_score, recall_score,
                             roc_auc_score)

from src import config


# ---------------------------------------------------------------------------
# Threshold
# ---------------------------------------------------------------------------
def best_f1_threshold(y_true, scores):
    """The threshold that maximises F1 on the given data (meant for validation).

    precision_recall_curve tries every distinct score as a threshold. F1 is
    computed for each and the best one is kept.
    """
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    # The last precision/recall pair has no threshold attached, so it is dropped.
    p, r = precision[:-1], recall[:-1]
    f1 = np.divide(2 * p * r, p + r, out=np.zeros_like(p), where=(p + r) > 0)
    i = int(np.argmax(f1))
    return float(thresholds[i]), float(f1[i])


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def summary(y_true, scores, threshold):
    """Main metrics for one model at one threshold."""
    pred = scores >= threshold
    tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()
    return {
        "PR-AUC": average_precision_score(y_true, scores),
        "ROC-AUC": roc_auc_score(y_true, scores),
        "précision": precision_score(y_true, pred),
        "rappel": recall_score(y_true, pred),
        "F1": f1_score(y_true, pred),
        "VP": int(tp), "FP": int(fp), "FN": int(fn), "VN": int(tn),
    }


def per_class_report(y_true, scores, threshold):
    """Precision, recall and F1 for each class (normal and attack)."""
    pred = (scores >= threshold).astype(int)
    rows = {}
    for label, name in [(0, "normal"), (1, "attaque")]:
        t, p = (y_true == label), (pred == label)
        rows[name] = {
            "précision": precision_score(t, p),
            "rappel": recall_score(t, p),
            "F1": f1_score(t, p),
            "effectif": int(t.sum()),
        }
    return pd.DataFrame(rows).T


def recall_by_family(families, y_true, scores, threshold):
    """Share of flows of each family flagged as attack.

    For attack families this is the recall. For "Normal" it is the false
    positive rate (normal flows wrongly flagged).
    """
    pred = scores >= threshold
    df = pd.DataFrame({"famille": families.to_numpy(), "alerte": pred})
    out = df.groupby("famille")["alerte"].agg(["mean", "size"])
    out.columns = ["part signalée", "effectif"]
    return out.sort_values("effectif", ascending=False)


def alert_load(y_true, scores, threshold, per=10_000):
    """Alerts per `per` flows, and how many of them are real attacks."""
    pred = scores >= threshold
    alerts = pred.sum()
    true_alerts = (pred & (y_true == 1)).sum()
    return {
        f"alertes pour {per:,} flux".replace(",", " "): alerts / len(pred) * per,
        "dont vraies attaques": true_alerts / len(pred) * per,
        "dont fausses alertes": (alerts - true_alerts) / len(pred) * per,
        f"attaques manquées pour {per:,} flux".replace(",", " "): ((~pred) & (y_true == 1)).sum() / len(pred) * per,
    }


def precision_at_prevalence(recall, false_positive_rate, prevalence):
    """Precision the same detector would have if attacks were `prevalence` of the traffic.

    Recall and false positive rate do not depend on how many attacks there
    are, but precision does. This rescales precision to another share of
    attacks, e.g. the 1 % or 0.1 % one would expect on a real network.
    """
    tp = recall * prevalence
    fp = false_positive_rate * (1 - prevalence)
    return tp / (tp + fp) if (tp + fp) > 0 else float("nan")


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def plot_pr_curves(y_true, scores_by_model, title, filename=None, thresholds=None):
    """Precision-recall curves of several models, with the random-model level."""
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for name, scores in scores_by_model.items():
        p, r, _ = precision_recall_curve(y_true, scores)
        ap = average_precision_score(y_true, scores)
        line, = ax.plot(r, p, label=f"{name} (PR-AUC = {ap:.3f})")
        if thresholds and name in thresholds:
            pred = scores >= thresholds[name]
            ax.plot(recall_score(y_true, pred), precision_score(y_true, pred), "o",
                    color=line.get_color(), markersize=7)
    base = float(np.mean(y_true))
    ax.axhline(base, color="grey", linestyle="--", linewidth=1,
               label=f"modèle au hasard (= part d'attaques, {base:.3f})")
    ax.set_xlabel("rappel")
    ax.set_ylabel("précision")
    ax.set_ylim(0, 1.02)
    ax.set_title(title)
    ax.legend(loc="lower left")
    fig.tight_layout()
    if filename:
        fig.savefig(config.FIGURES / filename, dpi=150)
    plt.show()


def plot_confusion_matrices(y_true, scores_by_model, thresholds, filename=None):
    """One confusion matrix per model, side by side."""
    fig, axes = plt.subplots(1, len(scores_by_model), figsize=(5 * len(scores_by_model), 4.2))
    for ax, (name, scores) in zip(np.atleast_1d(axes), scores_by_model.items()):
        cm = confusion_matrix(y_true, scores >= thresholds[name])
        ConfusionMatrixDisplay(cm, display_labels=["normal", "attaque"]).plot(
            ax=ax, colorbar=False, values_format=",d", cmap="Blues")
        ax.set_title(f"{name}\n(seuil {thresholds[name]:.2f})")
        ax.set_xlabel("prédit")
        ax.set_ylabel("réel")
    fig.tight_layout()
    if filename:
        fig.savefig(config.FIGURES / filename, dpi=150)
    plt.show()
