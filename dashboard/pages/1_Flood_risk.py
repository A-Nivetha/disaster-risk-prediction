import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ui

ui.setup("Flood risk", "Set the 20 ratings, then press Calculate. The model returns the probability of the flood class.")
import streamlit as st

from disaster_risk import alerts, history
from disaster_risk.predict import flood_features, predict_flood

feats = flood_features()
KEY = "flood_calc"


def save_flood():
    c = st.session_state.get(KEY)
    if c and not c["saved"]:
        history.log_prediction("flood", c["values"], c["out"]["predicted_class"],
                               {"Flood class": c["p"], "No-flood class": 1 - c["p"]},
                               c["lv"]["level"], c["lv"]["flagged"], place=c["place"])
        c["saved"] = True


left, right = st.columns([3, 2], gap="large")
values = {}
with left:
    with st.form("flood_form"):
        cols = st.columns(2, gap="large")
        for i, name in enumerate(feats["features"]):
            lo, hi = feats["ranges"][name]
            with cols[i % 2]:
                st.session_state.setdefault(f"flood_{name}", int(feats["medians"][name]))
                values[name] = st.slider(
                    ui.sentence_case(name), int(lo), int(hi), key=f"flood_{name}")
        st.subheader("Place (optional)")
        p1, p2, p3 = st.columns([2, 1, 1], gap="medium")
        place_name = p1.text_input("Place name", key="flood_place_name")
        place_lat = p2.number_input("Latitude", -90.0, 90.0, value=None, step=0.1, format="%.4f", key="flood_place_lat")
        place_lon = p3.number_input("Longitude", -180.0, 180.0, value=None, step=0.1, format="%.4f", key="flood_place_lon")
        submitted = st.form_submit_button("Calculate", type="primary")
    st.caption("Ratings are integers from the training dataset; sliders start at the median. The place only puts the calculation "
               "on the map. The flood model does not use location, so the result does not depend on the place.")

if submitted:
    out = predict_flood(values)
    p = out["flood_class_probability"]
    st.session_state[KEY] = {
        "values": dict(values), "out": out, "p": p, "lv": alerts.flood_level(p), "saved": False,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "place": ({"name": place_name.strip(), "latitude": place_lat, "longitude": place_lon}
                  if place_lat is not None and place_lon is not None else None)}

with right:
    st.header("Result")
    c = st.session_state.get(KEY)
    if not c:
        ui.notice("No result yet. Set the ratings and press <b>Calculate</b> below the inputs.", "blue")
    else:
        p, lv, pl = c["p"], c["lv"], c["place"]
        ui.result_card(lv["level"], lv["label"], f"Flag level: <b>{alerts.LEVEL_NAMES[lv['level']]}</b>")
        ui.prob_bars([("Flood class", p, ui.LEVEL["red"]), ("No-flood class", 1 - p, ui.LEVEL["green"])])
        where = (pl["name"] or "Unnamed place") + f" ({pl['latitude']:.4f}, {pl['longitude']:.4f})" if pl else "Not given"
        ui.detail_panel(
            "Calculation details",
            f"The model places this set of ratings in the {'flood' if p >= 0.5 else 'no-flood'} class. "
            f"The flood class applies at a probability of 0.5 or higher; the Elevated flag starts at {alerts.FLOOD_NEAR_THRESHOLD:.2f}.",
            [("Flag level", alerts.LEVEL_NAMES[lv["level"]]), ("Place", where), ("Calculated", c["time"])])
        if c["saved"]:
            ui.notice("Saved to history. " + ("This result is on the Alerts page." if lv["flagged"] else "No flag raised."), "green")
        else:
            st.button("Save to history", on_click=save_flood, key="flood_save")
        if pl:
            st.header("Place on the map")
            st.plotly_chart(ui.place_map(pl["longitude"], pl["latitude"], pl["name"] or "Flood calculation", lv["level"], zoom=8, height=400),
                            width="stretch")
        else:
            st.caption("Enter a latitude and longitude under Place and press Calculate to see the place on a map.")
