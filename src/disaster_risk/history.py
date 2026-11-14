"""Store every calculation made in the app in SQLite.

Two modes:
- Local (run.bat and run.sh set DISASTER_HISTORY_MODE=local): one file, storage/history.sqlite, kept between runs.
- Any other start (for example a hosted app): one file per browser session, storage/sessions/<hash of the session id>.sqlite.
  A visitor can read and change only the file of their own session. A session file is deleted after
  SESSION_MAX_AGE_HOURS without use, and a new browser session starts with an empty history.
Override both with the environment variable DISASTER_HISTORY_DB (one explicit file, used by the tests).
Outside Streamlit (scripts) there is no session, so the shared file is used. storage/ is ignored by git.
"""
import hashlib
import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from . import config as C

SESSION_MAX_AGE_HOURS = 24

COLUMNS = ["id", "created", "model", "inputs", "result_class", "probabilities", "level", "flagged", "place"]


def _session_id():
    """Streamlit session id of the visitor whose script is running; None outside a Streamlit run."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx(suppress_warning=True)
        return ctx.session_id if ctx else None
    except Exception:
        return None


def per_visitor() -> bool:
    """True when this run keeps its own private history (not the shared local file)."""
    if os.environ.get("DISASTER_HISTORY_DB") or os.environ.get("DISASTER_HISTORY_MODE", "").lower() == "local":
        return False
    return _session_id() is not None


def db_path():
    explicit = os.environ.get("DISASTER_HISTORY_DB")
    if explicit:
        return explicit
    if per_visitor():
        name = hashlib.sha256(_session_id().encode()).hexdigest()[:32]
        return str(C.STORAGE_DIR / "sessions" / f"{name}.sqlite")
    return str(C.STORAGE_DIR / "history.sqlite")


def _prune_sessions(folder: Path) -> None:
    """Delete session files (and their journals) that have not been used for SESSION_MAX_AGE_HOURS."""
    cutoff = time.time() - SESSION_MAX_AGE_HOURS * 3600
    for f in folder.glob("*.sqlite*"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:
            pass


def _connect():
    path = db_path()
    folder = Path(path).parent
    folder.mkdir(parents=True, exist_ok=True)
    if folder == C.STORAGE_DIR / "sessions" and not os.path.exists(path):
        _prune_sessions(folder)  # a new session: clear out old ones
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, "
        "model TEXT, inputs TEXT, result_class TEXT, probabilities TEXT, level TEXT, flagged INTEGER, place TEXT)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, "
        "prediction_id INTEGER, channel TEXT, department TEXT, message TEXT, status TEXT)"
    )
    # rows saved by the previous wording keep working
    con.execute("UPDATE notifications SET status = ? WHERE status LIKE ?", (STATUS_RECORDED, "%recorded, not delivered"))
    con.commit()
    try:
        os.utime(path, None)  # marks the session file as in use
    except OSError:
        pass
    return con


def log_prediction(model: str, inputs: dict, result_class: str, probabilities: dict, level: str, flagged: bool, place: dict = None, created: str = None):
    """place: optional {name, latitude, longitude}; a map label, not a model input.
    created: calculation time (YYYY-MM-DD HH:MM:SS); the save time is used when it is not given."""
    con = _connect()
    with con:
        con.execute(
            "INSERT INTO predictions (created, model, inputs, result_class, probabilities, level, flagged, place) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (created or datetime.now().strftime("%Y-%m-%d %H:%M:%S"), model, json.dumps(inputs),
             result_class, json.dumps(probabilities), level, int(flagged),
             json.dumps(place) if place else None),
        )
    con.close()


def read_all() -> list:
    """Newest first. Each row is a dict with inputs and probabilities decoded."""
    con = _connect()
    rows = con.execute(f"SELECT {', '.join(COLUMNS)} FROM predictions ORDER BY id DESC").fetchall()
    con.close()
    out = []
    for r in rows:
        d = dict(zip(COLUMNS, r))
        d["inputs"] = json.loads(d["inputs"])
        d["probabilities"] = json.loads(d["probabilities"])
        d["flagged"] = bool(d["flagged"])
        d["place"] = json.loads(d["place"]) if d["place"] else None
        out.append(d)
    return out


def clear():
    con = _connect()
    with con:
        con.execute("DELETE FROM predictions")
        con.execute("DELETE FROM notifications")
    con.close()


NOTIFICATION_COLUMNS = ["id", "created", "prediction_id", "channel", "department", "message", "status"]
STATUS_RECORDED = "Recorded"


def log_notification(prediction_id: int, channel: str, department: str, message: str) -> None:
    """Record a notification prepared for a department. Email, SMS and push delivery are not connected, so nothing is sent."""
    con = _connect()
    with con:
        con.execute(
            "INSERT INTO notifications (created, prediction_id, channel, department, message, status) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), prediction_id, channel, department, message, STATUS_RECORDED),
        )
    con.close()


def read_notifications() -> list:
    """Newest first."""
    con = _connect()
    rows = con.execute(f"SELECT {', '.join(NOTIFICATION_COLUMNS)} FROM notifications ORDER BY id DESC").fetchall()
    con.close()
    return [dict(zip(NOTIFICATION_COLUMNS, r)) for r in rows]
