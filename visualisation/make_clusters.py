"""K-means exploration for both datasets (unsupervised, not used by the classifiers).

Earthquake: longitude, latitude, depth (standardised), random 50,000 valid events.
Flood: the 20 ratings (standardised), all 50,000 rows.
For K = 2..7 the script records inertia and silhouette (silhouette is computed on a
random 10,000-row subsample for speed). K = 3 is drawn for interpretation only;
the figures and cluster_info.json report which K has the highest silhouette.

Usage: python visualisation/make_clusters.py
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
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from disaster_risk import config as C
from disaster_risk.data import load_flood

K_RANGE = list(range(2, 8))
K_SHOWN = 3
N_SIL = 10_000
COLORS = ["#2563EB", "#F97316", "#16A34A"]
FIG_DIR = C.REPORTS_DIR / "figures"
plt.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                     "axes.spines.top": False, "axes.spines.right": False})


def evaluate(Z):
    rng = np.random.RandomState(C.SEED)
    sil_idx = rng.choice(len(Z), size=min(N_SIL, len(Z)), replace=False)
    inertia, sil, labels = [], [], {}
    for k in K_RANGE:
        km = KMeans(n_clusters=k, n_init=10, random_state=C.SEED).fit(Z)
        inertia.append(float(km.inertia_))
        sil.append(float(silhouette_score(Z[sil_idx], km.labels_[sil_idx])))
        labels[k] = km.labels_
    return inertia, sil, labels


def eval_figure(name, inertia, sil, title):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for a, vals, yl in [(ax[0], inertia, "Inertia"), (ax[1], sil, "Silhouette score")]:
        a.plot(K_RANGE, vals, "o-", color="#1D4ED8")
        a.axvline(K_SHOWN, color="#1F2933", ls="--", label=f"K = {K_SHOWN} (used for interpretation)")
        a.set(xlabel="Number of clusters (K)", ylabel=yl)
        a.set_xticks(K_RANGE)
    best = K_RANGE[int(np.argmax(sil))]
    ax[0].set_title("Inertia by K")
    ax[1].set_title(f"Silhouette by K (highest at K = {best})")
    ax[1].plot(best, max(sil), "o", ms=12, mfc="none", mec="#1F2933")
    ax[0].legend()
    fig.suptitle(title, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}_cluster_evaluation.png", dpi=150)
    plt.close(fig)
    return best


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    info = {"settings": {"k_range": K_RANGE, "k_shown": K_SHOWN, "seed": C.SEED,
                         "silhouette_subsample": N_SIL, "n_init": 10}}

    # ---- earthquake
    eq = pd.read_csv(C.RAW_DIR / "Eartquakes-1990-2023.csv",
                     usecols=["longitude", "latitude", "depth", "magnitudo"]).dropna()
    eq = eq[eq["magnitudo"] > C.MIN_VALID_MAGNITUDE].sample(50_000, random_state=C.SEED).reset_index(drop=True)
    Z = StandardScaler().fit_transform(eq[["longitude", "latitude", "depth"]])
    inertia, sil, labels = evaluate(Z)
    best = eval_figure("earthquake", inertia, sil, "Earthquake events: K-means evaluation (longitude, latitude, depth)")
    lab = labels[K_SHOWN]
    fig, ax = plt.subplots(figsize=(11, 6))
    for c in range(K_SHOWN):
        m = lab == c
        ax.scatter(eq.loc[m, "longitude"], eq.loc[m, "latitude"], s=3, alpha=0.4, color=COLORS[c], label=f"Cluster {c}")
    ax.set(xlabel="Longitude (degrees east)", ylabel="Latitude (degrees north)",
           title=f"Earthquake events by K-means cluster (K = {K_SHOWN}, 50,000 events)")
    ax.legend(markerscale=5)
    fig.tight_layout(); fig.savefig(FIG_DIR / "earthquake_clusters.png", dpi=150); plt.close(fig)
    info["earthquake"] = {"features": ["longitude", "latitude", "depth"], "rows": len(eq), "inertia": inertia,
                          "silhouette": sil, "highest_silhouette_k": best,
                          "k3_cluster_sizes": [int((lab == c).sum()) for c in range(K_SHOWN)],
                          "k3_mean_depth_km": [round(float(eq.loc[lab == c, "depth"].mean()), 2) for c in range(K_SHOWN)]}

    # ---- flood
    X, y = load_flood(C.RAW_DIR / "flood1.csv")
    prob = pd.read_csv(C.RAW_DIR / "flood1.csv", usecols=[C.FLOOD_TARGET])[C.FLOOD_TARGET]
    Z = StandardScaler().fit_transform(X)
    inertia, sil, labels = evaluate(Z)
    best = eval_figure("flood", inertia, sil, "Flood dataset: K-means evaluation (20 ratings)")
    lab = labels[K_SHOWN]
    pca = PCA(n_components=2, random_state=C.SEED).fit(Z)
    P = pca.transform(Z)
    fig, ax = plt.subplots(figsize=(9, 6))
    for c in range(K_SHOWN):
        m = lab == c
        ax.scatter(P[m, 0], P[m, 1], s=3, alpha=0.4, color=COLORS[c], label=f"Cluster {c}")
    ax.set(xlabel=f"Principal component 1 ({pca.explained_variance_ratio_[0]:.1%} of variance)",
           ylabel=f"Principal component 2 ({pca.explained_variance_ratio_[1]:.1%} of variance)",
           title=f"Flood dataset by K-means cluster (K = {K_SHOWN}, 50,000 rows)")
    ax.legend(markerscale=5)
    fig.tight_layout(); fig.savefig(FIG_DIR / "flood_clusters.png", dpi=150); plt.close(fig)
    info["flood"] = {"features": list(X.columns), "rows": len(X), "inertia": inertia, "silhouette": sil,
                     "highest_silhouette_k": best,
                     "pca_explained_variance_ratio": [round(float(v), 4) for v in pca.explained_variance_ratio_],
                     "k3_cluster_sizes": [int((lab == c).sum()) for c in range(K_SHOWN)],
                     "k3_mean_flood_probability": [round(float(prob[lab == c].mean()), 4) for c in range(K_SHOWN)]}

    (FIG_DIR / "cluster_info.json").write_text(json.dumps(info, indent=2))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "features"} if isinstance(v, dict) and k != "settings" else v
                      for k, v in info.items()}, indent=1))


if __name__ == "__main__":
    main()
