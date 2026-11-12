"""Plotly helpers used by the dashboard: shared figure styling and street maps (OpenStreetMap tiles).

Street maps need an internet connection in the browser to load the tiles. No API key is needed.
"""
import plotly.graph_objects as go

from .theme import BLUE, CARD, LEVEL, MUTED, SEV, TEXT  # noqa: F401


def style_fig(fig, height=420):
    fig.update_layout(
        template="plotly_dark", height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=CARD,
        font=dict(size=16, color=TEXT), legend=dict(font=dict(size=16), orientation="h", y=-0.02, x=0),
        margin=dict(l=10, r=10, t=20, b=10))
    return fig


def _map_layout(fig, lon, lat, zoom, height):
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
        map=dict(style="open-street-map", center=dict(lon=float(lon), lat=float(lat)), zoom=zoom))
    return fig


def place_map(lon: float, lat: float, label: str, level: str, zoom: float = 5, height: int = 420):
    """One marker on a street map: the place of a single calculation. level: green | amber | red."""
    fig = go.Figure(go.Scattermap(
        lon=[lon], lat=[lat], mode="markers+text", text=[label], textposition="top center",
        textfont=dict(size=16, color="#0F172A"),
        marker=dict(size=22, color=LEVEL[level], opacity=0.95),
        hovertemplate=f"{label}<br>Longitude %{{lon:.4f}}, latitude %{{lat:.4f}}<extra></extra>"))
    return _map_layout(fig, lon, lat, zoom, height)


def saved_map(points: list, height: int = 520):
    """Street map of saved calculations. points: [(lon, lat, label, level)]."""
    lons, lats = [p[0] for p in points], [p[1] for p in points]
    fig = go.Figure(go.Scattermap(
        lon=lons, lat=lats, mode="markers", text=[p[2] for p in points],
        marker=dict(size=18, color=[LEVEL[p[3]] for p in points], opacity=0.95),
        hovertemplate="%{text}<br>Longitude %{lon:.4f}, latitude %{lat:.4f}<extra></extra>"))
    span = max(max(lons) - min(lons), max(lats) - min(lats))
    zoom = 1.5 if span > 90 else 3 if span > 30 else 5 if span > 5 else 8 if span > 0.5 else 10
    return _map_layout(fig, (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2, zoom, height)
