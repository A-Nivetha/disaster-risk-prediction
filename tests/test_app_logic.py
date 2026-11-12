from disaster_risk import alerts, history


def test_flood_levels():
    assert alerts.flood_level(0.5)["level"] == "red"
    assert alerts.flood_level(alerts.FLOOD_NEAR_THRESHOLD)["level"] == "amber"
    assert alerts.flood_level(0.1)["level"] == "green" and not alerts.flood_level(0.1)["flagged"]


def test_earthquake_levels():
    assert alerts.earthquake_level({"Low": 0.9, "Medium": 0.09, "High": 0.01})["level"] == "green"
    assert alerts.earthquake_level({"Low": 0.5, "Medium": 0.4, "High": 0.1})["level"] == "amber"  # High-class probability flag
    assert alerts.earthquake_level({"Low": 0.1, "Medium": 0.8, "High": 0.1})["level"] == "amber"
    assert alerts.earthquake_level({"Low": 0.1, "Medium": 0.2, "High": 0.7})["level"] == "red"


def test_history_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DISASTER_HISTORY_DB", str(tmp_path / "h.db"))
    history.log_prediction("flood", {"a": 1}, "Flood", {"Flood class": 0.6}, "red", True)
    rows = history.read_all()
    assert len(rows) == 1 and rows[0]["flagged"] and rows[0]["probabilities"]["Flood class"] == 0.6
    history.clear()
    assert history.read_all() == []


def test_notification_log_and_message(tmp_path, monkeypatch):
    monkeypatch.setenv("DISASTER_HISTORY_DB", str(tmp_path / "h.db"))
    history.log_prediction("flood", {"a": 1}, "Flood class", {"Flood class": 0.6, "No flood class": 0.4}, "red", True,
                           {"name": "Test place", "latitude": 12.5, "longitude": 77.5})
    row = history.read_all()[0]
    msg = alerts.notification_message(row)
    assert "0.6000" in msg and "Test place" in msg and "verify" in msg
    assert history.read_notifications() == []
    history.log_notification(row["id"], "SMS", alerts.DEPARTMENTS["flood"], msg)
    n = history.read_notifications()
    assert len(n) == 1 and n[0]["status"] == history.STATUS_RECORDED and n[0]["prediction_id"] == row["id"]
    history.clear()
    assert history.read_notifications() == []


def test_old_notification_status_is_converted(tmp_path, monkeypatch):
    import sqlite3
    monkeypatch.setenv("DISASTER_HISTORY_DB", str(tmp_path / "h.db"))
    history.log_prediction("flood", {"a": 1}, "Flood class", {"Flood class": 0.6, "No flood class": 0.4}, "red", True)
    row = history.read_all()[0]
    history.log_notification(row["id"], "SMS", alerts.DEPARTMENTS["flood"], "text")
    con = sqlite3.connect(str(tmp_path / "h.db"))
    con.execute("UPDATE notifications SET status = ?", ("Old: recorded, not delivered",))
    con.commit(); con.close()
    assert history.read_notifications()[0]["status"] == history.STATUS_RECORDED


# ---- per-visitor history -------------------------------------------------------------------------

import os
import time

from disaster_risk import config as C


def _visitors(tmp_path, monkeypatch, session):
    monkeypatch.delenv("DISASTER_HISTORY_DB", raising=False)
    monkeypatch.delenv("DISASTER_HISTORY_MODE", raising=False)
    monkeypatch.setattr(C, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(history, "_session_id", lambda: session["id"])


def _flood_high():
    history.log_prediction("flood", {"a": 1}, "Flood class", {"Flood class": 0.6, "No flood class": 0.4}, "red", True)


def test_visitors_cannot_see_or_change_each_other(tmp_path, monkeypatch):
    who = {"id": "visitor-A"}
    _visitors(tmp_path, monkeypatch, who)
    _flood_high()
    row = history.read_all()[0]
    history.log_notification(row["id"], "SMS", alerts.DEPARTMENTS["flood"], "text")
    assert len(history.read_all()) == 1 and len(history.read_notifications()) == 1
    who["id"] = "visitor-B"
    assert history.read_all() == [] and history.read_notifications() == []
    _flood_high()
    history.clear()  # B clears only B's history
    who["id"] = "visitor-A"
    assert len(history.read_all()) == 1 and len(history.read_notifications()) == 1
    assert len(list((tmp_path / "sessions").glob("*.sqlite"))) == 2
    assert not (tmp_path / "history.sqlite").exists()


def test_local_mode_uses_one_shared_file(tmp_path, monkeypatch):
    who = {"id": "visitor-A"}
    _visitors(tmp_path, monkeypatch, who)
    monkeypatch.setenv("DISASTER_HISTORY_MODE", "local")
    assert history.db_path() == str(tmp_path / "history.sqlite") and not history.per_visitor()
    _flood_high()
    who["id"] = "visitor-B"
    assert len(history.read_all()) == 1


def test_no_session_uses_shared_file(tmp_path, monkeypatch):
    _visitors(tmp_path, monkeypatch, {"id": None})
    assert history.db_path() == str(tmp_path / "history.sqlite") and not history.per_visitor()


def test_session_id_cannot_escape_the_sessions_folder(tmp_path, monkeypatch):
    _visitors(tmp_path, monkeypatch, {"id": "../../etc/passwd"})
    path = history.db_path()
    assert os.path.dirname(path) == str(tmp_path / "sessions") and ".." not in os.path.basename(path)


def test_old_session_files_are_pruned_when_a_new_session_starts(tmp_path, monkeypatch):
    who = {"id": "visitor-A"}
    _visitors(tmp_path, monkeypatch, who)
    folder = tmp_path / "sessions"
    folder.mkdir()
    old, recent = folder / "old.sqlite", folder / "recent.sqlite"
    old.write_text(""); recent.write_text("")
    past = time.time() - (history.SESSION_MAX_AGE_HOURS + 1) * 3600
    os.utime(old, (past, past))
    history.read_all()  # first use by a new session
    assert not old.exists() and recent.exists()
