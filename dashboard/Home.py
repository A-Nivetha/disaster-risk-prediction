import ui

ui.setup("Flood and earthquake risk dashboard",
         "Model results, flags and saved calculations for the flood and earthquake models.")
import streamlit as st

from disaster_risk import history

rows = history.read_all()
flagged = [r for r in rows if r["flagged"]]
n_red = sum(r["level"] == "red" for r in flagged)
n_amber = len(flagged) - n_red
last = rows[0] if rows else None

ui.kpi_row([
    ("Calculations saved", f"{len(rows):,}", "Every calculation on the model pages", "blue"),
    ("Flags at level High", f"{n_red:,}", "Flood class, or earthquake High class most probable", "red"),
    ("Flags at level Elevated", f"{n_amber:,}", "Near the flood rule, Medium class, or High-class probability flagged", "amber"),
    ("Latest calculation", last["model"].capitalize() if last else "None yet", last["created"] if last else "Run one on a model page", "teal"),
])
st.write("")

left, right = st.columns([5, 3], gap="large")
with left:
    st.header("Map of saved calculations")
    pts = ui.map_points(rows)
    if pts:
        st.plotly_chart(ui.saved_map(pts, 520), width="stretch")
        st.caption("Marker colour is the flag level: green no flag, amber Elevated, red High. Earthquake calculations are placed at their "
                   "coordinates. Flood calculations appear only when saved with a place; the flood model does not use the place.")
    else:
        ui.notice("<b>Nothing to show yet.</b> Calculate and save a result on the Earthquake severity page, or on the Flood risk page "
                  "with a place entered, and it appears here.", "blue")

with right:
    st.header("Alerts")
    if flagged:
        for r in flagged[:4]:
            st.markdown(ui.flag_card(r), unsafe_allow_html=True)
        st.page_link("pages/3_Alerts.py", label="Open all alerts")
    else:
        ui.notice("<b>No flags yet.</b> A flag appears here when a calculation reaches level Elevated or High.", "green")
    st.header("New calculation")
    st.page_link("pages/1_Flood_risk.py", label="Flood risk: 20 ratings")
    st.page_link("pages/2_Earthquake_severity.py", label="Earthquake severity: location and depth")
