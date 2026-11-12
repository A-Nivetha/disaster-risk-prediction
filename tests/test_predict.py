import pytest

from disaster_risk import config as C
from disaster_risk.predict import flood_features, predict_flood, predict_severity

pytestmark = pytest.mark.skipif(
    not (C.MODELS_DIR / "flood_xgb.json").exists(), reason="models not trained")


def test_flood_probability_in_range():
    feats = flood_features()
    mid = {c: sum(r) // 2 for c, r in feats["ranges"].items()}
    out = predict_flood(mid)
    assert 0.0 <= out["flood_class_probability"] <= 1.0


def test_severity_probabilities_sum_to_one():
    out = predict_severity(85.3, 27.7, 10.0)
    assert set(out) == {"Low", "Medium", "High"}
    assert abs(sum(out.values()) - 1.0) < 1e-4
