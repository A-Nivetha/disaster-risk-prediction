import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ui

ui.setup("Earthquake severity", "Enter longitude, latitude and depth, then press Calculate. The model returns Low, Medium and High class probabilities.")
import streamlit as st

from disaster_risk import alerts, history
from disaster_risk import config as C
from disaster_risk.predict import predict_severity

eq = ui.load_metrics()["earthquake_severity"]
rng = ui.load_samples_info()["usgs_events_sample"]["feature_ranges"]
labels = eq["labels"]
KEY = "eq_calc"


def save_eq():
    c = st.session_state.get(KEY)
    if c and not c["saved"]:
        history.log_prediction("earthquake", c["inputs"], c["lv"]["top"], c["probs"], c["lv"]["level"], c["lv"]["flagged"])
        c["saved"] = True


left, right = st.columns([2, 3], gap="large")
with left:
    with st.form("eq_form"):
        lon = st.number_input("Longitude (degrees east)", -180.0, 180.0, None, step=0.1, format="%.4f",
                              placeholder="-180 to 180", key="eq_lon")
        lat = st.number_input("Latitude (degrees north)", -90.0, 90.0, None, step=0.1, format="%.4f",
                              placeholder="-90 to 90", key="eq_lat")
        st.session_state.setdefault("eq_depth", 10.0)
        depth = st.number_input(
            "Depth (km)",
            C.MIN_INPUT_DEPTH, float(rng["depth"][1]), step=1.0, format="%.2f", key="eq_depth")
        submitted = st.form_submit_button("Calculate", type="primary")
    st.caption(f"Depth accepts {C.MIN_INPUT_DEPTH:.1f} to {rng['depth'][1]:.1f} km. "
               "The model returns probabilities for any coordinates, including places with no recorded events.")

if submitted and (lon is None or lat is None):
    st.session_state.pop(KEY, None)
    st.session_state["eq_missing"] = True
elif submitted:
    st.session_state["eq_missing"] = False
    probs = predict_severity(lon, lat, depth)
    st.session_state[KEY] = {
        "inputs": {"longitude": lon, "latitude": lat, "depth": depth},
        "probs": probs, "lv": alerts.earthquake_level(probs), "saved": False,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

with right:
    st.header("Result")
    c = st.session_state.get(KEY)
    if st.session_state.get("eq_missing"):
        ui.notice("<b>Longitude and latitude are required.</b> Enter both, then press <b>Calculate</b>.", "red")
    elif not c:
        ui.notice("No result yet. Enter the location and depth and press <b>Calculate</b> below the inputs.", "blue")
    else:
        probs, lv, i = c["probs"], c["lv"], c["inputs"]
        ui.result_card(lv["level"], f"{lv['top']} class", f"{lv['label']}. Flag level: <b>{alerts.LEVEL_NAMES[lv['level']]}</b>")
        ui.prob_bars([(f"{k} class", probs[k], ui.SEV[k]) for k in labels])
        ui.detail_panel(
            "Calculation details",
            f"At longitude {i['longitude']:.4f}, latitude {i['latitude']:.4f} and depth {i['depth']:.1f} km, "
            f"the {lv['top']} class is the most probable.",
            [("Flag level", alerts.LEVEL_NAMES[lv["level"]]), ("Longitude, latitude", f"{i['longitude']:.4f}, {i['latitude']:.4f}"),
             ("Depth", f"{i['depth']:.1f} km"), ("Calculated", c["time"])])
        if c["saved"]:
            ui.notice("Saved to history. " + ("This result is on the Alerts page." if lv["flagged"] else "No flag raised."), "green")
        else:
            st.button("Save to history", on_click=save_eq, key="eq_save")
        st.header("Location on the map")
        st.plotly_chart(ui.place_map(i["longitude"], i["latitude"], f"{lv['top']} class", lv["level"], zoom=4, height=420), width="stretch")
