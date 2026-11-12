import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ui

ui.setup("Alerts", "Model flags raised by the calculations saved in history.")
import pandas as pd
import streamlit as st

from disaster_risk import alerts, history

rows = history.read_all()
flagged = [r for r in rows if r["flagged"]]
n_red = sum(r["level"] == "red" for r in flagged)
n_amber = sum(r["level"] == "amber" for r in flagged)

ui.kpi_row([
    ("Calculations saved", f"{len(rows):,}", "All calculations in history", "blue"),
    ("Flags raised", f"{len(flagged):,}", "Level Elevated or High", "amber" if flagged else "green"),
    ("Level High", f"{n_red:,}", "Flood class, or High class most probable", "red"),
    ("Level Elevated", f"{n_amber:,}", "Near the flood rule, Medium class, or High-class probability flagged", "amber"),
])
st.write("")

st.header("Flags")
pick = st.radio("Show", ["All flags", "Flood model", "Earthquake model", "Level High", "Level Elevated"], horizontal=True)
shown = [r for r in flagged if (
    pick == "All flags" or (pick == "Flood model" and r["model"] == "flood") or
    (pick == "Earthquake model" and r["model"] == "earthquake") or
    (pick == "Level High" and r["level"] == "red") or (pick == "Level Elevated" and r["level"] == "amber"))]
if not shown:
    ui.notice("<b>No flags to show.</b> Calculate and save a result on the Flood risk or Earthquake severity page. "
              "A flag is raised when a saved result reaches level Elevated or High.", "green")
for r in shown[:30]:
    st.markdown(ui.flag_card(r), unsafe_allow_html=True)
if len(shown) > 30:
    st.caption(f"Showing the newest 30 of {len(shown)} flags. All calculations are on the Prediction history page.")

st.header("Notify the department")
st.markdown(
    "1. The model raises a **High** flag.  \n"
    "2. The app prepares the message for the department by SMS, email or push and records it in the notification log.  \n"
    "3. The department verifies the flag and acts. This step happens outside this app.")
high = [r for r in flagged if r["level"] == alerts.DISPATCH_LEVEL]
if not high:
    ui.notice("<b>No High flag yet.</b> A notification is prepared only for a High flag. Elevated flags are not notified.", "blue")
else:
    by_id = {r["id"]: r for r in high}
    pick_id = st.selectbox(
        "High flag", list(by_id),
        format_func=lambda i: f"{by_id[i]['created']}  |  {by_id[i]['model'].capitalize()}  |  {by_id[i]['result_class']}")
    row = by_id[pick_id]
    channel = st.radio("Channel", alerts.CHANNELS, horizontal=True)
    dept = alerts.DEPARTMENTS[row["model"]]
    msg = alerts.notification_message(row)
    ui.detail_panel("Message preview", msg, [("To", dept), ("Channel", channel), ("Status", history.STATUS_RECORDED)])
    sent_before = [n for n in history.read_notifications() if n["prediction_id"] == pick_id and n["channel"] == channel]
    if sent_before:
        ui.notice(f"Already recorded for this flag by {channel} at {sent_before[0]['created']}.", "green")
    elif st.button("Notify department", type="primary", key="notify_dept"):
        history.log_notification(pick_id, channel, dept, msg)
        st.rerun()

st.header("Notification log")
log = history.read_notifications()
if not log:
    st.caption("No notifications recorded yet.")
else:
    ui.html_table(pd.DataFrame([{"Time": n["created"], "Department": n["department"], "Channel": n["channel"],
                                 "Status": n["status"]} for n in log[:30]]))
