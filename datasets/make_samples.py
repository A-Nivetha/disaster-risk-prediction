"""Build the small sample files used by the Streamlit map page.

The raw datasets are not committed. This script writes compact samples to
datasets/samples/ so the deployed app can draw maps without the raw files.

Usage:
    python datasets/make_samples.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import json
from pathlib import Path

import pandas as pd

from disaster_risk import config as C
from disaster_risk.data import severity_from_magnitude

SAMPLES_DIR = C.SAMPLES_DIR
PER_CLASS = 2000  # events drawn per severity class (stratified, not proportional)


def build_india(raw: Path) -> dict:
    df = pd.read_csv(raw, usecols=["Latitude", "Longitude", "Flood Occurred"])
    out = pd.DataFrame({
        "latitude": df["Latitude"].round(4),
        "longitude": df["Longitude"].round(4),
        "flood_occurred": df["Flood Occurred"].astype(int),
    })
    out.to_csv(SAMPLES_DIR / "india_flood_points.csv", index=False)
    return {"file": "india_flood_points.csv", "rows": int(len(out)),
            "flood_occurred_share": round(float(out["flood_occurred"].mean()), 4)}


def build_usgs(raw: Path) -> dict:
    cols = ["longitude", "latitude", "depth", "magnitudo"]
    df = pd.read_csv(raw, usecols=cols).dropna()
    df = df[df["magnitudo"] > C.MIN_VALID_MAGNITUDE].reset_index(drop=True)
    df["severity"] = severity_from_magnitude(df["magnitudo"]).map(dict(enumerate(C.SEVERITY_LABELS)))
    parts = [g.sample(n=min(PER_CLASS, len(g)), random_state=C.SEED) for _, g in df.groupby("severity")]
    out = pd.concat(parts).sort_values("severity").reset_index(drop=True)
    out[["longitude", "latitude"]] = out[["longitude", "latitude"]].round(4)
    out["depth"] = out["depth"].round(2)
    out.to_csv(SAMPLES_DIR / "usgs_events_sample.csv", index=False)
    return {"file": "usgs_events_sample.csv", "rows": int(len(out)),
            "per_class": {k: int(v) for k, v in out["severity"].value_counts().items()},
            "sampling": f"stratified, up to {PER_CLASS} events per class, seed {C.SEED}",
            "source_rows_used": int(len(df)),
            "feature_ranges": {c: [float(df[c].min()), float(df[c].max())]
                               for c in ["longitude", "latitude", "depth"]}}


def main():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    info = {
        "india_flood_points": build_india(C.RAW_DIR / "flood_risk_dataset_india.csv"),
        "usgs_events_sample": build_usgs(C.RAW_DIR / "Eartquakes-1990-2023.csv"),
    }
    (SAMPLES_DIR / "samples_info.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
