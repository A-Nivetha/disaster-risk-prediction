"""Load saved models and make predictions. Used by the Streamlit app."""
import json
from functools import lru_cache

import pandas as pd
from xgboost import XGBClassifier

from . import config as C


@lru_cache(maxsize=1)
def _flood_model():
    m = XGBClassifier()
    m.load_model(C.MODELS_DIR / "flood_xgb.json")
    return m


@lru_cache(maxsize=1)
def flood_features() -> dict:
    return json.loads((C.MODELS_DIR / "flood_features.json").read_text())


@lru_cache(maxsize=1)
def _severity_model():
    m = XGBClassifier()
    m.load_model(C.MODELS_DIR / "earthquake_severity_xgb.json")
    return m


def predict_flood(values: dict) -> dict:
    cols = flood_features()["features"]
    row = pd.DataFrame([[values[c] for c in cols]], columns=cols)
    p = float(_flood_model().predict_proba(row)[0, 1])
    return {"flood_class_probability": p, "predicted_class": "Flood" if p >= 0.5 else "No flood"}


def predict_severity(longitude: float, latitude: float, depth: float) -> dict:
    row = pd.DataFrame([[longitude, latitude, depth]], columns=C.EQ_FEATURES)
    probs = _severity_model().predict_proba(row)[0]
    return {label: float(p) for label, p in zip(C.SEVERITY_LABELS, probs)}
