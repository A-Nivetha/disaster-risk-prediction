import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ui

ui.setup("Prediction history", "Every calculation made on the Flood risk and Earthquake severity pages.")
import pandas as pd
import streamlit as st

from disaster_risk import history

if history.per_visitor():
    st.caption(f"This history belongs to your browser session only. Other visitors cannot see or change it. "
               f"A new session starts empty, and a session's history is deleted after {history.SESSION_MAX_AGE_HOURS} hours without use.")
rows = history.read_all()
if not rows:
    ui.notice("<b>Nothing saved yet.</b> Press the calculate button on the Flood risk or Earthquake severity page.", "blue")
    st.stop()

pick = st.radio("Model", ["All", "Flood", "Earthquake"], horizontal=True)
shown = [r for r in rows if pick == "All" or r["model"] == pick.lower()]


def summary(r):
    i = r["inputs"]
    if r["model"] == "earthquake":
        return f"Longitude {i['longitude']:.2f}, latitude {i['latitude']:.2f}, depth {i['depth']:.1f} km"
    return "20 ratings: " + ", ".join(f"{k[:3]} {v}" for k, v in list(i.items())[:4]) + " ..."


def place(r):
    if r["model"] == "earthquake":
        return f"{r['inputs']['latitude']:.2f}, {r['inputs']['longitude']:.2f}"
    pl = r.get("place")
    return f"{pl.get('name') or 'not named'} ({pl['latitude']:.2f}, {pl['longitude']:.2f})" if pl else "not given"


def probs(r):
    return ", ".join(f"{k} {v:.4f}" for k, v in r["probabilities"].items())


table = pd.DataFrame({
    "Time": [r["created"] for r in shown],
    "Model": [r["model"].capitalize() for r in shown],
    "Place (latitude, longitude)": [place(r) for r in shown],
    "Inputs": [summary(r) for r in shown],
    "Result": [r["result_class"] for r in shown],
    "Probabilities": [probs(r) for r in shown],
    "Flag level": [{"red": "High", "amber": "Elevated", "green": "No flag"}[r["level"]] for r in shown],
})
ui.html_table(table.head(100))
if len(table) > 100:
    st.caption(f"Showing the newest 100 of {len(table)} rows. The download holds all rows.")

full = pd.DataFrame([{"time": r["created"], "model": r["model"], "place": place(r), "inputs": str(r["inputs"]), "result": r["result_class"],
                      "probabilities": str(r["probabilities"]), "flag_level": r["level"]} for r in shown])
st.write("")
c1, c2 = st.columns([1, 3])
c1.download_button("Download CSV", full.to_csv(index=False).encode(), "prediction_history.csv", "text/csv")
with c2.expander("Clear history"):
    if st.checkbox("I understand this deletes every saved calculation"):
        if st.button("Delete all saved calculations"):
            history.clear()
            st.rerun()
st.caption("History is stored in a local SQLite file. On a hosted copy of the app the file may be reset when the app restarts.")
