"""Shared page setup, styling and display helpers for the Streamlit app.

Every number shown in the app is read from reports/metrics.json,
models/flood_features.json, datasets/samples/samples_info.json or a model run.
"""
import html as _html
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # lets the app import disaster_risk without pip install
sys.path.insert(0, str(ROOT))          # lets the app import visualisation

from visualisation.theme import BG, BLUE, BORDER, CARD, KPI, LEVEL, LEVEL_TEXT, MUTED, SEV, TEXT  # noqa: E402


CSS = f"""
<style>
html {{ font-size: 20px; }}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background: {BG}; color: {TEXT}; }}
[data-testid="stSidebar"] {{ background: #0F1A2E; border-right: 1px solid {BORDER}; }}
[data-testid="stSidebar"] a, [data-testid="stSidebar"] a span, [data-testid="stSidebar"] a p,
[data-testid="stSidebarNav"] a, [data-testid="stSidebarNav"] a span, [data-testid="stSidebarNavLink"] span {{ font-size: 21px !important; font-weight: 500; }}
.block-container {{ padding-top: 5.5rem; max-width: 1600px; }}
p, li {{ font-size: 20px; line-height: 1.55; }}
[data-testid="stWidgetLabel"] p, label p {{ font-size: 20px; font-weight: 500; color: #E2E8F0; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ font-size: 18px; color: {MUTED}; }}
[data-testid="stSliderThumbValue"], [data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"],
[data-testid="stTickBarMin"], [data-testid="stTickBarMax"] {{ font-size: 18px; color: {TEXT}; }}
input {{ font-size: 20px !important; }}
[data-testid="stRadio"] label p {{ font-size: 20px; }}
button[data-baseweb="tab"] p {{ font-size: 21px; font-weight: 600; }}
.stButton button, .stFormSubmitButton button, .stDownloadButton button {{ min-height: 3.2rem; padding: 0.4rem 1.6rem; border-radius: 6px; }}
.stButton button p, .stFormSubmitButton button p, .stDownloadButton button p {{ font-size: 20px; font-weight: 600; }}
.stTable td, .stTable th, .stMarkdown table td, .stMarkdown table th {{ font-size: 19px; color: {TEXT}; }}
h2 {{ font-size: 32px !important; font-weight: 700; color: {TEXT}; }}
h3 {{ font-size: 26px !important; font-weight: 600; color: {TEXT}; }}
.topbar {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 4px; }}
.page-title {{ font-size: 44px; font-weight: 700; color: {TEXT}; line-height: 1.2; }}
.page-sub {{ font-size: 22px; color: {MUTED}; margin: 4px 0 20px 0; }}
.pill {{ display: inline-block; font-size: 17px; font-weight: 600; padding: 5px 14px; border-radius: 999px; border: 1px solid; white-space: nowrap; }}
.pill-blue {{ background: rgba(59,130,246,.15); color: #93C5FD; border-color: #3B82F6; }}
.pill-green {{ background: rgba(34,197,94,.15); color: #4ADE80; border-color: #22C55E; }}
.pill-amber {{ background: rgba(245,158,11,.15); color: #FBBF24; border-color: #F59E0B; }}
.pill-red {{ background: rgba(239,68,68,.15); color: #F87171; border-color: #EF4444; }}
.kpi {{ background: {CARD}; border: 1px solid {BORDER}; border-top-width: 5px; border-radius: 8px; padding: 16px 18px; height: 100%; }}
.kpi-label {{ font-size: 19px; color: {MUTED}; font-weight: 500; }}
.kpi-value {{ font-size: 44px; font-weight: 700; line-height: 1.15; margin: 4px 0; }}
.kpi-text {{ font-size: 30px; overflow-wrap: normal; word-break: keep-all; }}
.kpi-sub {{ font-size: 18px; color: {MUTED}; line-height: 1.4; }}
.rcard {{ border: 2px solid; border-radius: 10px; padding: 20px 22px; margin-bottom: 14px; }}
.rcard-title {{ font-size: 42px; font-weight: 700; line-height: 1.15; }}
.rcard-sub {{ font-size: 21px; color: {TEXT}; margin-top: 6px; }}
.rcard-red {{ background: rgba(239,68,68,.13); border-color: #EF4444; }}
.rcard-amber {{ background: rgba(245,158,11,.13); border-color: #F59E0B; }}
.rcard-green {{ background: rgba(34,197,94,.13); border-color: #22C55E; }}
.rcard-red .rcard-title {{ color: #F87171; }} .rcard-amber .rcard-title {{ color: #FBBF24; }} .rcard-green .rcard-title {{ color: #4ADE80; }}
.pbar {{ display: flex; align-items: center; gap: 12px; margin: 10px 0; }}
.pbar-label {{ width: 190px; font-size: 21px; font-weight: 600; }}
.pbar-track {{ flex: 1; height: 26px; background: #1E2B45; border-radius: 5px; overflow: hidden; }}
.pbar-fill {{ height: 100%; border-radius: 5px; }}
.pbar-value {{ width: 90px; text-align: right; font-size: 23px; font-weight: 700; }}
.notice {{ background: {CARD}; border: 1px solid {BORDER}; border-left: 6px solid; border-radius: 8px; padding: 14px 18px; margin: 10px 0 16px 0; font-size: 20px; line-height: 1.55; }}
.notice b {{ color: {TEXT}; }}
.notice-blue {{ border-left-color: {BLUE}; }} .notice-red {{ border-left-color: #EF4444; }} .notice-amber {{ border-left-color: #F59E0B; }} .notice-green {{ border-left-color: #22C55E; }}
.flag {{ background: {CARD}; border: 1px solid {BORDER}; border-left: 6px solid; border-radius: 8px; padding: 14px 18px; margin: 0 0 12px 0; }}
.flag-red {{ border-left-color: #EF4444; background: rgba(239,68,68,.08); }} .flag-amber {{ border-left-color: #F59E0B; background: rgba(245,158,11,.08); }} .flag-green {{ border-left-color: #22C55E; }}
.flag-top {{ display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }}
.flag-title {{ font-size: 22px; font-weight: 700; }}
.flag-body {{ font-size: 20px; color: {TEXT}; margin-top: 6px; line-height: 1.5; }}
.flag-time {{ font-size: 18px; color: {MUTED}; margin-top: 6px; }}
.htable {{ width: 100%; border-collapse: collapse; font-size: 19px; }}
.htable th {{ text-align: left; padding: 10px 12px; background: #1B2A44; color: {TEXT}; border-bottom: 2px solid {BORDER}; font-weight: 600; }}
.htable td {{ padding: 10px 12px; border-bottom: 1px solid {BORDER}; vertical-align: top; }}
.figcard {{ background: #FFFFFF; border-radius: 8px; padding: 10px; margin: 8px 0 4px 0; }}
.dp {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 20px 22px; margin: 4px 0 14px 0; }}
.dp-eyebrow {{ font-size: 16px; letter-spacing: .08em; text-transform: uppercase; color: {MUTED}; font-weight: 600; margin-bottom: 10px; }}
.dp-title {{ font-size: 30px; font-weight: 700; color: {TEXT}; margin: 2px 0 12px 0; }}
.dp-summary {{ background: #0F1A2E; border: 1px solid {BORDER}; border-radius: 8px; padding: 14px 18px; font-size: 21px; line-height: 1.55; margin-bottom: 14px; }}
.tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }}
.tile {{ background: #0F1A2E; border: 1px solid {BORDER}; border-radius: 8px; padding: 12px 16px; }}
.tile-label {{ font-size: 15px; letter-spacing: .08em; text-transform: uppercase; color: {MUTED}; font-weight: 600; }}
.tile-value {{ font-size: 23px; font-weight: 600; color: {TEXT}; margin-top: 4px; }}
</style>
"""


def setup(title: str, subtitle: str = "", needs_files: bool = True):
    st.set_page_config(page_title=title, layout="wide", initial_sidebar_state="expanded")
    keep_form_state()
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        f'<div class="topbar"><div class="page-title">{_html.escape(title)}</div>'
        f'<span class="pill pill-blue">Prototype on historical data</span></div>'
        + (f'<div class="page-sub">{_html.escape(subtitle)}</div>' if subtitle else ""),
        unsafe_allow_html=True,
    )
    if needs_files:
        check_files()


def pill(text: str, level: str) -> str:
    return f'<span class="pill pill-{level}">{_html.escape(text)}</span>'


def notice(body_html: str, level: str = "blue"):
    st.markdown(f'<div class="notice notice-{level}">{body_html}</div>', unsafe_allow_html=True)


def kpi(label: str, value: str, sub: str = "", colour: str = "blue") -> str:
    return (f'<div class="kpi" style="border-top-color:{KPI[colour]}"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value{" kpi-text" if any(ch.isalpha() for ch in str(value)) else ""}" style="color:{LEVEL_TEXT.get(colour, TEXT)}">{value}</div>'
            f'<div class="kpi-sub">{sub}</div></div>')


# Keys that start with flood_ or eq_ but are not form inputs: buttons cannot be assigned through session state,
# and the saved results are plain keys that Streamlit never removes.
_NOT_FORM_INPUTS = {"flood_save", "eq_save", "flood_calc", "eq_calc", "eq_missing"}


def keep_form_state():
    """Streamlit drops a widget's value when a run does not show that widget (for example on another page).
    Re-assigning the value on every page keeps the Flood and Earthquake forms as the user left them."""
    for k in list(st.session_state.keys()):
        if isinstance(k, str) and k.startswith(("flood_", "eq_")) and k not in _NOT_FORM_INPUTS:
            v = st.session_state[k]
            if not isinstance(v, bool):  # buttons hold True or False and are read-only
                st.session_state[k] = v


def kpi_row(items: list):
    cols = st.columns(len(items), gap="medium")
    for col, it in zip(cols, items):
        col.markdown(kpi(*it), unsafe_allow_html=True)


def result_card(level: str, title: str, sub: str = ""):
    st.markdown(
        f'<div class="rcard rcard-{level}"><div class="rcard-title">{_html.escape(title)}</div>'
        f'<div class="rcard-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def detail_panel(eyebrow: str, summary: str, tiles: list):
    """Result panel: small label, one-sentence summary and a grid of label/value tiles. tiles: [(label, value)]."""
    grid = "".join(f'<div class="tile"><div class="tile-label">{_html.escape(l)}</div>'
                   f'<div class="tile-value">{_html.escape(str(v))}</div></div>' for l, v in tiles)
    st.markdown(
        f'<div class="dp"><div class="dp-eyebrow">{_html.escape(eyebrow)}</div>'
        f'<div class="dp-summary">{_html.escape(summary)}</div><div class="tiles">{grid}</div></div>',
        unsafe_allow_html=True)


def prob_bars(items: list):
    """items: (label, probability, hex colour)."""
    rows = "".join(
        f'<div class="pbar"><div class="pbar-label">{_html.escape(lab)}</div>'
        f'<div class="pbar-track"><div class="pbar-fill" style="width:{max(p, 0.004) * 100:.2f}%;background:{col}"></div></div>'
        f'<div class="pbar-value">{p:.4f}</div></div>'
        for lab, p, col in items
    )
    st.markdown(rows, unsafe_allow_html=True)


def flag_card(row: dict) -> str:
    lvl = row["level"]
    name = {"red": "High", "amber": "Elevated", "green": "No flag"}[lvl]
    if row["model"] == "flood":
        title = f"Flood model: {row['result_class']}"
        p = row["probabilities"]["Flood class"]
        body = f"Probability of flood class {p:.4f}. Class rule: flood class at 0.5 or higher."
        pl = row.get("place")
        if pl:
            body += f" Place: {pl.get('name') or 'not named'} ({pl['latitude']:.2f}, {pl['longitude']:.2f})."
    else:
        i = row["inputs"]
        title = f"Earthquake model: {row['result_class']}"
        pr = row["probabilities"]
        body = (f"Longitude {i['longitude']:.2f}, latitude {i['latitude']:.2f}, depth {i['depth']:.1f} km. "
                f"Low {pr['Low']:.4f}, Medium {pr['Medium']:.4f}, High {pr['High']:.4f}.")
    return (f'<div class="flag flag-{lvl}"><div class="flag-top"><div class="flag-title" style="color:{LEVEL_TEXT[lvl]}">'
            f'{_html.escape(title)}</div>{pill(name, lvl)}</div>'
            f'<div class="flag-body">{_html.escape(body)}</div><div class="flag-time">{row["created"]}</div></div>')


def html_table(df: pd.DataFrame):
    head = "".join(f"<th>{_html.escape(str(c))}</th>" for c in df.columns)
    body = "".join("<tr>" + "".join(f"<td>{_html.escape(str(v))}</td>" for v in r) + "</tr>" for r in df.itertuples(index=False))
    st.markdown(f'<table class="htable"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>', unsafe_allow_html=True)


@st.cache_data
def load_metrics() -> dict:
    return json.loads((ROOT / "reports" / "metrics.json").read_text())


@st.cache_data
def load_samples_info() -> dict:
    return json.loads((ROOT / "datasets" / "samples" / "samples_info.json").read_text())


@st.cache_data
def load_sample(name: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / "datasets" / "samples" / name)


def sentence_case(camel: str) -> str:
    out = ""
    for i, ch in enumerate(camel):
        out += (" " + ch.lower()) if (ch.isupper() and i > 0) else ch
    return out[0].upper() + out[1:]


def place_map(*a, **k):
    from visualisation.maps import place_map as f
    return f(*a, **k)


def saved_map(*a, **k):
    from visualisation.maps import saved_map as f
    return f(*a, **k)


def map_points(rows: list, limit: int = 50) -> list:
    """Saved calculations that can be placed on a map: [(lon, lat, label, level)].
    Earthquake rows use their input coordinates; flood rows only when saved with a place."""
    pts = []
    for r in rows:
        if r["model"] == "earthquake":
            i = r["inputs"]
            pts.append((i["longitude"], i["latitude"], f"Earthquake: {r['result_class']} class", r["level"]))
        elif r.get("place"):
            pl = r["place"]
            pts.append((pl["longitude"], pl["latitude"], f"{pl.get('name') or 'Flood calculation'}: {r['result_class']}", r["level"]))
    return pts[:limit]


REQUIRED = {
    "reports/metrics.json": "python -m disaster_risk.train_flood, then python -m disaster_risk.train_earthquake",
    "datasets/samples/samples_info.json": "python datasets/make_samples.py",
}


def check_files():
    """Stop with the exact command to run when a generated file is missing (fresh clone)."""
    missing = {k: v for k, v in REQUIRED.items() if not (ROOT / k).exists()}
    if missing:
        cmds = "".join(f"<li><code>{v}</code> creates <code>{k}</code></li>" for k, v in missing.items())
        notice("<b>Generated files are missing.</b> Put the three Kaggle CSV files in <code>datasets/raw/</code> "
               f"(see datasets/README.md), then run from the repository root:<ul>{cmds}</ul>", "red")
        st.stop()
