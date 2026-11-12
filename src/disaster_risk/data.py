"""Dataset loading. Reads CSV or a single-file ZIP."""
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C


def load_flood(path):
    df = pd.read_csv(path)
    X = df.drop(columns=[C.FLOOD_TARGET])
    y = (df[C.FLOOD_TARGET] >= C.FLOOD_THRESHOLD).astype(int)
    return X, y


def severity_from_magnitude(mag: pd.Series) -> pd.Series:
    low, high = C.SEVERITY_EDGES
    bins = [-np.inf, low, high, np.inf]
    return pd.cut(mag, bins=bins, right=False, labels=range(3)).astype(int)


def load_earthquakes(path):
    """Return (X, y, info). info records how many rows were dropped and why."""
    cols = C.EQ_FEATURES + ["magnitudo"]
    df = pd.read_csv(Path(path), usecols=cols)
    n_raw = len(df)
    df = df.dropna()
    n_after_na = len(df)
    df = df[df["magnitudo"] > C.MIN_VALID_MAGNITUDE]
    info = {
        "rows_raw": int(n_raw),
        "rows_dropped_missing": int(n_raw - n_after_na),
        "rows_dropped_invalid_magnitude": int(n_after_na - len(df)),
        "rows_used": int(len(df)),
    }
    y = severity_from_magnitude(df["magnitudo"])
    return df[C.EQ_FEATURES].reset_index(drop=True), y.reset_index(drop=True), info
