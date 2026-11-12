"""Regenerate the exploratory figures from the raw data (corrected versions).

Fixes against the first notebook versions: class labels match the data
(flood share is 51.03%), the single-class tsunami pie is dropped, and the
invalid magnitude sentinel (-10) is excluded and reported.

Usage: python visualisation/make_figures.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from disaster_risk import config as C
from disaster_risk.data import load_flood, severity_from_magnitude

ACCENT, GRAY, LIGHT = "#1D4ED8", "#9CA3AF", "#93C5FD"
FIG_DIR = C.REPORTS_DIR / "figures"
plt.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                     "axes.spines.top": False, "axes.spines.right": False})


def flood_eda():
    raw = pd.read_csv(C.RAW_DIR / "flood1.csv")
    X, y = load_flood(C.RAW_DIR / "flood1.csv")
    fig, ax = plt.subplots(2, 2, figsize=(13, 10))

    ax[0, 0].hist(raw[C.FLOOD_TARGET], bins=50, color=ACCENT, edgecolor="white")
    ax[0, 0].axvline(C.FLOOD_THRESHOLD, color="#1F2933", ls="--", label="Class threshold (0.5)")
    ax[0, 0].set(title="FloodProbability distribution", xlabel="FloodProbability", ylabel="Rows")
    ax[0, 0].legend(loc="upper left")

    counts = y.map({0: "No flood", 1: "Flood"}).value_counts().reindex(["No flood", "Flood"])
    bars = ax[0, 1].bar(counts.index, counts.values, color=[GRAY, ACCENT])
    for b, v in zip(bars, counts.values):
        ax[0, 1].text(b.get_x() + b.get_width() / 2, v, f"{v:,} ({v / len(y):.2%})", ha="center", va="bottom")
    ax[0, 1].set(title="Class balance", ylabel="Rows",
                 ylim=(0, counts.max() * 1.15))

    corr = X.corrwith(raw[C.FLOOD_TARGET]).abs().sort_values().tail(10)
    ax[1, 0].barh(corr.index, corr.values, color=ACCENT)
    ax[1, 0].set(title="Ten strongest absolute correlations with FloodProbability",
                 xlabel="Absolute Pearson correlation")

    sel = ["MonsoonIntensity", "Deforestation", "ClimateChange", "Urbanization"]
    pos = np.arange(len(sel))
    for off, cls, col in [(-0.18, 0, GRAY), (0.18, 1, ACCENT)]:
        data = [X.loc[y == cls, c] for c in sel]
        bp = ax[1, 1].boxplot(data, positions=pos + off, widths=0.3, patch_artist=True)
        for patch in bp["boxes"]:
            patch.set_facecolor(col)
        for med in bp["medians"]:
            med.set_color("#1F2933")
    ax[1, 1].set_xticks(pos, sel, rotation=15)
    ax[1, 1].set(title="Selected ratings by class", ylabel="Rating")
    ax[1, 1].legend([plt.Rectangle((0, 0), 1, 1, color=GRAY), plt.Rectangle((0, 0), 1, 1, color=ACCENT)],
                    ["No flood", "Flood"], loc="upper left")
    fig.suptitle("Flood dataset: exploratory analysis", fontsize=15, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "flood_eda.png", dpi=150)
    plt.close(fig)
    return {"top_correlations": {k: round(float(v), 4) for k, v in corr.sort_values(ascending=False).items()}}


def earthquake_eda():
    df = pd.read_csv(C.RAW_DIR / "Eartquakes-1990-2023.csv", usecols=["magnitudo", "depth", "significance"]).dropna()
    n_invalid = int((df["magnitudo"] <= C.MIN_VALID_MAGNITUDE).sum())
    df = df[df["magnitudo"] > C.MIN_VALID_MAGNITUDE].reset_index(drop=True)
    sev = severity_from_magnitude(df["magnitudo"]).map(dict(enumerate(C.SEVERITY_LABELS)))
    corr_all = float(df["magnitudo"].corr(df["significance"]))
    sample = df.sample(300_000, random_state=C.SEED)
    sev_s = sev.loc[sample.index]

    fig, ax = plt.subplots(2, 2, figsize=(13, 10))
    ax[0, 0].hist(df["magnitudo"], bins=60, color=ACCENT, edgecolor="white")
    for edge in C.SEVERITY_EDGES:
        ax[0, 0].axvline(edge, color="#1F2933", ls="--")
    ax[0, 0].set(title=f"Magnitude distribution ({n_invalid} invalid values excluded)",
                 xlabel="Magnitude", ylabel="Events (log scale)", yscale="log")

    counts = sev.value_counts().reindex(C.SEVERITY_LABELS)
    bars = ax[0, 1].bar(counts.index, counts.values, color=[GRAY, LIGHT, ACCENT])
    for b, v in zip(bars, counts.values):
        ax[0, 1].text(b.get_x() + b.get_width() / 2, v, f"{v:,}\n({v / len(sev):.2%})", ha="center", va="bottom")
    ax[0, 1].set(title="Severity class counts (log scale)", ylabel="Events", yscale="log",
                 ylim=(1, counts.max() * 12), xlabel="Severity class")

    bp = ax[1, 0].boxplot([sample.loc[sev_s == c, "depth"] for c in C.SEVERITY_LABELS],
                          tick_labels=C.SEVERITY_LABELS, patch_artist=True)
    for patch, col in zip(bp["boxes"], [GRAY, LIGHT, ACCENT]):
        patch.set_facecolor(col)
    for med in bp["medians"]:
        med.set_color("#1F2933")
    ax[1, 0].set(title="Depth by severity (random sample of 300,000 events)",
                 xlabel="Severity class", ylabel="Depth (km)")

    sub = sample.sample(50_000, random_state=C.SEED)
    ax[1, 1].scatter(sub["magnitudo"], sub["significance"], s=2, color=ACCENT, alpha=0.3)
    ax[1, 1].set(title=f"Significance vs magnitude (correlation {corr_all:.3f}, all events)",
                 xlabel="Magnitude", ylabel="Significance")
    fig.suptitle("Earthquake dataset: exploratory analysis", fontsize=15, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "earthquake_eda.png", dpi=150)
    plt.close(fig)
    return {"invalid_magnitude_rows": n_invalid, "magnitude_significance_corr": round(corr_all, 4),
            "class_counts": {k: int(v) for k, v in counts.items()}}


if __name__ == "__main__":
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = {"flood": flood_eda(), "earthquake": earthquake_eda()}
    (FIG_DIR / "eda_info.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
