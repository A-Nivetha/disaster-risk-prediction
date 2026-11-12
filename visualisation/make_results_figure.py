"""Draw the README results figure from reports/metrics.json (no numbers are typed in here).

Left: test accuracy against the majority-class baseline for both models.
Right: earthquake recall per class on the test set, with the number of test events in each class.

Usage: python visualisation/make_results_figure.py
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme as T

ROOT = Path(__file__).resolve().parents[1]
m = json.loads((ROOT / "reports" / "metrics.json").read_text())
fl, eq = m["flood"], m["earthquake_severity"]
cm = eq["saved_model"]["confusion_matrix"]
labels = eq["labels"]
support = [sum(row) for row in cm]
recall = [cm[i][i] / support[i] for i in range(3)]

fig, (a, b) = plt.subplots(1, 2, figsize=(12.5, 5.2), gridspec_kw={"width_ratios": [1, 1.1]})
fig.patch.set_facecolor(T.BG)
for ax in (a, b):
    ax.set_facecolor(T.CARD)
    for s in ax.spines.values():
        s.set_color(T.BORDER)
    ax.tick_params(colors=T.MUTED, labelsize=12)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.grid(axis="y", color=T.BORDER, linewidth=0.8)
    ax.set_axisbelow(True)


def label_bars(ax, bars, values):
    for rect, v in zip(bars, values):
        ax.text(rect.get_x() + rect.get_width() / 2, v + 0.015, f"{v:.4f}", ha="center", va="bottom",
                color=T.TEXT, fontsize=12, fontweight="bold")


# left: accuracy against the majority-class baseline
groups = ["Flood risk\n(50,000 rows)", "Earthquake severity\n(3,445,104 rows)"]
base = [fl["class_share_flood"], eq["majority_class_baseline_accuracy"]]
acc = [fl["test_accuracy"], eq["saved_model"]["test_accuracy"]]
x = [0, 1]
w = 0.34
b1 = a.bar([i - w / 2 for i in x], base, w, color="#64748B", label="Majority-class baseline")
b2 = a.bar([i + w / 2 for i in x], acc, w, color=T.BLUE, label="Test accuracy")
label_bars(a, b1, base)
label_bars(a, b2, acc)
a.set_xticks(x)
a.set_xticklabels(groups, color=T.TEXT, fontsize=12)
a.set_title("Test accuracy against the baseline", color=T.TEXT, fontsize=15, pad=12, loc="left")
leg = a.legend(loc="lower center", frameon=False, fontsize=11, ncol=2, bbox_to_anchor=(0.5, -0.30))
for t in leg.get_texts():
    t.set_color(T.MUTED)

# right: earthquake recall per class
bars = b.bar(range(3), recall, 0.55, color=[T.SEV[k] for k in labels])
label_bars(b, bars, recall)
b.set_xticks(range(3))
b.set_xticklabels([f"{k}\n{n:,} test events" for k, n in zip(labels, support)], color=T.TEXT, fontsize=12)
b.set_title("Earthquake severity: recall per class", color=T.TEXT, fontsize=15, pad=12, loc="left")

fig.suptitle("Held-out test set (20% stratified split, seed 42)", color=T.MUTED, fontsize=12, x=0.065, ha="left", y=0.985)
fig.tight_layout(rect=(0, 0.02, 1, 0.95))
out = ROOT / "reports" / "figures" / "model_results.png"
fig.savefig(out, dpi=200, facecolor=T.BG)
print("wrote", out.relative_to(ROOT), "| baselines", base, "| accuracy", acc, "| recall", [round(r, 4) for r in recall], "| support", support)
