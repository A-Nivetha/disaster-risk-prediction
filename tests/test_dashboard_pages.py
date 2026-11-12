"""Run each dashboard page with Streamlit's AppTest, using the real models and a temporary history file."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from disaster_risk import config as C, history

ROOT = Path(__file__).resolve().parents[1]
needs_models = pytest.mark.skipif(not (C.MODELS_DIR / "flood_xgb.json").exists(), reason="models not trained")
pytestmark = needs_models


@pytest.fixture(autouse=True)
def temp_history(tmp_path, monkeypatch):
    monkeypatch.setenv("DISASTER_HISTORY_DB", str(tmp_path / "h.db"))


def page(name):
    return AppTest.from_file(str(ROOT / "dashboard" / name), default_timeout=60)


def button(at, label):
    return next(b for b in at.button if b.label == label)


@pytest.mark.parametrize("name", ["Home.py", "pages/3_Alerts.py", "pages/4_Prediction_history.py", "pages/5_Model_reliability.py"])
def test_page_runs(name):
    at = page(name).run()
    assert not at.exception


@pytest.mark.parametrize("name,expect", [("pages/1_Flood_risk.py", 10), ("pages/2_Earthquake_severity.py", 2)])
def test_calculate_does_not_save_and_save_saves_once(name, expect):
    at = page(name).run()
    assert not at.exception
    if "Earthquake" in name:  # longitude and latitude start empty
        at.number_input(key="eq_lon").set_value(92.35)
        at.number_input(key="eq_lat").set_value(26.06)
    assert not [b for b in at.button if b.label == "Save to history"]  # nothing to save before Calculate
    at.get("form_submit_button")[0].click().run()
    assert not at.exception
    assert history.read_all() == []  # Calculate alone saves nothing
    button(at, "Save to history").click().run()
    assert len(history.read_all()) == 1
    assert not [b for b in at.button if b.label == "Save to history"]  # cannot be saved twice
    assert len(history.read_all()) == 1


def test_flood_place_saved_and_mapped():
    at = page("pages/1_Flood_risk.py").run()
    at.text_input(key="flood_place_name").set_value("Test place")
    at.number_input(key="flood_place_lat").set_value(12.5)
    at.number_input(key="flood_place_lon").set_value(77.5)
    at.get("form_submit_button")[0].click().run()
    button(at, "Save to history").click().run()
    row = history.read_all()[0]
    assert row["place"] == {"name": "Test place", "latitude": 12.5, "longitude": 77.5}
    home = page("Home.py").run()
    assert not home.exception


def test_alerts_notify_department_once():
    history.log_prediction("earthquake", {"longitude": 1.0, "latitude": 2.0, "depth": 10.0}, "High",
                           {"Low": 0.1, "Medium": 0.2, "High": 0.7}, "red", True)
    at = page("pages/3_Alerts.py").run()
    assert not at.exception
    button(at, "Notify department").click().run()
    assert not at.exception
    assert len(history.read_notifications()) == 1
    assert not [b for b in at.button if b.label == "Notify department"]  # same flag and channel cannot repeat
    assert len(history.read_notifications()) == 1


def test_alerts_no_send_for_elevated_only():
    history.log_prediction("flood", {"a": 1}, "No flood class", {"Flood class": 0.45, "No flood class": 0.55}, "amber", True)
    at = page("pages/3_Alerts.py").run()
    assert not at.exception
    assert not [b for b in at.button if b.label == "Notify department"]


def test_earthquake_empty_coordinates_give_no_result():
    at = page("pages/2_Earthquake_severity.py").run()
    assert at.number_input(key="eq_lon").value is None and at.number_input(key="eq_lat").value is None
    at.get("form_submit_button")[0].click().run()
    assert not at.exception
    assert not [b for b in at.button if b.label == "Save to history"]
    assert history.read_all() == []


def test_earthquake_depth_minimum_is_minus_3():
    at = page("pages/2_Earthquake_severity.py").run()
    depth = next(n for n in at.number_input if n.label.startswith("Depth"))
    assert depth.min == C.MIN_INPUT_DEPTH == -3.0
    assert depth.value == 10.0


def test_earthquake_form_has_no_tsunami_input():
    at = page("pages/2_Earthquake_severity.py").run()
    assert not at.exception
    assert not at.radio  # the form has only longitude, latitude and depth
    assert C.EQ_FEATURES == ["longitude", "latitude", "depth"]


def test_hosted_mode_saves_into_a_private_session_file(tmp_path, monkeypatch):
    import sqlite3
    monkeypatch.delenv("DISASTER_HISTORY_DB", raising=False)
    monkeypatch.delenv("DISASTER_HISTORY_MODE", raising=False)
    monkeypatch.setattr(C, "STORAGE_DIR", tmp_path)
    at = page("pages/2_Earthquake_severity.py").run()
    at.number_input(key="eq_lon").set_value(92.35)
    at.number_input(key="eq_lat").set_value(26.06)
    at.get("form_submit_button")[0].click().run()
    button(at, "Save to history").click().run()  # a button callback must also reach the session file
    assert not at.exception
    files = list((tmp_path / "sessions").glob("*.sqlite"))
    assert len(files) == 1 and not (tmp_path / "history.sqlite").exists()
    assert sqlite3.connect(str(files[0])).execute("SELECT COUNT(*) FROM predictions").fetchone()[0] == 1
    hist = page("pages/4_Prediction_history.py").run()
    assert not hist.exception and any("browser session" in c.value for c in hist.caption)


def _app(main="Home.py"):
    return AppTest.from_file(str(ROOT / "dashboard" / main), default_timeout=60).run()


def test_earthquake_form_keeps_its_values_after_leaving_the_page():
    at = _app()
    at.switch_page("pages/2_Earthquake_severity.py").run()
    at.number_input(key="eq_lon").set_value(92.35)
    at.number_input(key="eq_lat").set_value(26.06)
    at.number_input(key="eq_depth").set_value(12.0)
    at.get("form_submit_button")[0].click().run()
    at.switch_page("Home.py").run()
    at.switch_page("pages/2_Earthquake_severity.py").run()
    assert (at.number_input(key="eq_lon").value, at.number_input(key="eq_lat").value,
            at.number_input(key="eq_depth").value) == (92.35, 26.06, 12.0)


def test_flood_form_keeps_its_values_after_leaving_the_page():
    at = _app()
    at.switch_page("pages/1_Flood_risk.py").run()
    at.slider(key="flood_MonsoonIntensity").set_value(9)
    at.text_input(key="flood_place_name").set_value("Mumbai")
    at.get("form_submit_button")[0].click().run()
    at.switch_page("pages/3_Alerts.py").run()
    at.switch_page("pages/1_Flood_risk.py").run()
    assert at.slider(key="flood_MonsoonIntensity").value == 9
    assert at.text_input(key="flood_place_name").value == "Mumbai"


def test_text_kpi_values_use_the_small_class():
    at = _app()
    html = " ".join(str(m.value) for m in at.markdown)
    assert 'class="kpi-value kpi-text"' in html  # "None yet" on an empty history
    assert 'class="kpi-value" ' in html  # numeric values keep the large size


def test_save_button_then_page_switch_does_not_raise_flood():
    at = _app()
    at.switch_page("pages/1_Flood_risk.py").run()
    at.get("form_submit_button")[0].click().run()
    at.slider(key="flood_MonsoonIntensity").set_value(7).run()  # any rerun once the Save button exists
    assert not at.exception
    button(at, "Save to history").click().run()
    assert not at.exception
    at.run()
    assert not at.exception
    at.switch_page("pages/3_Alerts.py").run()
    assert not at.exception
    at.switch_page("pages/1_Flood_risk.py").run()
    assert not at.exception


def test_save_button_then_page_switch_does_not_raise_earthquake():
    at = _app()
    at.switch_page("pages/2_Earthquake_severity.py").run()
    at.number_input(key="eq_lon").set_value(92.35)
    at.number_input(key="eq_lat").set_value(26.06)
    at.get("form_submit_button")[0].click().run()
    at.number_input(key="eq_depth").set_value(11.0).run()  # any rerun once the Save button exists
    assert not at.exception
    button(at, "Save to history").click().run()
    assert not at.exception
    at.run()
    assert not at.exception
    at.switch_page("Home.py").run()
    assert not at.exception
    at.switch_page("pages/2_Earthquake_severity.py").run()
    assert not at.exception


def test_full_walkthrough_has_no_exceptions_on_any_page_or_rerun():
    pages = ["Home.py", "pages/1_Flood_risk.py", "pages/2_Earthquake_severity.py", "pages/3_Alerts.py",
             "pages/4_Prediction_history.py", "pages/5_Model_reliability.py"]
    at = _app()
    # earthquake: High point, calculate, save
    at.switch_page("pages/2_Earthquake_severity.py").run()
    at.number_input(key="eq_lon").set_value(-179.306)
    at.number_input(key="eq_lat").set_value(-15.879)
    at.number_input(key="eq_depth").set_value(9.0)
    at.get("form_submit_button")[0].click().run()
    button(at, "Save to history").click().run()
    assert not at.exception
    # flood: calculate, save
    at.switch_page("pages/1_Flood_risk.py").run()
    at.slider(key="flood_MonsoonIntensity").set_value(12)
    at.get("form_submit_button")[0].click().run()
    button(at, "Save to history").click().run()
    assert not at.exception
    # alerts: record a notification for the first High flag
    at.switch_page("pages/3_Alerts.py").run()
    assert not at.exception
    notify = [b for b in at.button if b.label == "Notify department"]
    if notify:
        notify[0].click().run()
        assert not at.exception
    # every page, twice, with a plain rerun on each
    for _ in range(2):
        for p in pages:
            at.switch_page(p).run()
            assert not at.exception, p
            at.run()
            assert not at.exception, p
