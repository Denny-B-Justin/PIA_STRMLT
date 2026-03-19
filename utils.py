"""
utils.py
Map, chart, and table helpers for the Zambia Health Access dashboard.

Map approach change:
  Folium + html.Iframe(srcDoc=...) was replaced with plotly go.Scattermap
  rendered as a standard dcc.Graph.  Folium/Leaflet relies on external CDN JS
  that can silently fail inside an iframe srcDoc, leaving a blank white panel.
  go.Scattermap uses the open-street-map tile style which requires no Mapbox
  token and renders reliably as a Plotly component inside Dash.

Chart x-axis:
  X-axis now shows actual total_facilities values from the results table
  (e.g. 80 → 110) rather than a 0-based new-facility count.
"""

import logging
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
from constants import (
    BASELINE_ACCESS_PCT,
    ZAMBIA_CENTER_LAT,
    ZAMBIA_CENTER_LON,
    MAP_ZOOM,
)

# Zambia 2025 population estimate — used for "new people reached" calculation
ZAMBIA_POPULATION = 21_559_131


# ── Geometry & colour helpers ─────────────────────────────────────────────────

def _boundary_wkt_to_coords(wkt_str: str) -> Tuple[List, List]:
    """
    Parse a WKT POLYGON / MULTIPOLYGON into parallel lat / lon lists suitable
    for a Plotly Scattermap line trace.

    Pure-Python implementation — no shapely or other spatial library needed.
    Ring segments are separated by None sentinels so Plotly draws each ring as
    an independent closed path with no cross-ring connecting artefacts.

    Supported WKT types: POLYGON(...) and MULTIPOLYGON(...)
    Falls back to ([], []) on any parse error.
    """
    import re

    if not wkt_str:
        return [], []
    try:
        lats: List = []
        lons: List = []

        # Extract every coordinate ring — contents of each innermost (…) group
        # that contains actual coordinate pairs (i.e. has at least one comma
        # between two numbers).
        ring_re   = re.compile(r"\(([^()]+)\)")
        coord_re  = re.compile(r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)")

        for ring_match in ring_re.finditer(wkt_str):
            ring_str = ring_match.group(1)
            pairs    = coord_re.findall(ring_str)
            if len(pairs) < 2:          # skip degenerate / empty rings
                continue
            for lon_s, lat_s in pairs:
                lons.append(float(lon_s))
                lats.append(float(lat_s))
            # None sentinel → Plotly lifts the pen between rings
            lons.append(None)
            lats.append(None)

        return lats, lons
    except Exception as exc:
        logging.warning("Boundary WKT parse failed: %s", exc)
        return [], []


def _rgba(hex_color: str, opacity: float) -> str:
    """Convert a #RRGGBB hex colour + scalar opacity → CSS rgba() string."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    a = max(0.0, min(1.0, float(opacity)))
    return f"rgba({r},{g},{b},{a:.2f})"


# ── DMS conversion ────────────────────────────────────────────────────────────

def _to_dms(decimal_deg: float, is_lat: bool) -> str:
    """Convert decimal-degree coordinate to DMS string, e.g. 28° 02' 26.67\" E."""
    direction = (
        ("N" if decimal_deg >= 0 else "S") if is_lat
        else ("E" if decimal_deg >= 0 else "W")
    )
    d       = abs(decimal_deg)
    deg     = int(d)
    minutes = (d - deg) * 60
    min_int = int(minutes)
    sec     = (minutes - min_int) * 60
    return f"{deg}° {min_int:02d}' {sec:05.2f}\" {direction}"


# ── Map (Plotly Scattermap) ───────────────────────────────────────────────────

# ── Map colour constants ──────────────────────────────────────────────────────

_CLR_BOUNDARY      = "#F97316"               # orange line
_CLR_BOUNDARY_FILL = "rgba(249,115,22,0.08)" # light beige/orange fill (low opacity)
_CLR_EXISTING_FAC  = "#2563EB"               # blue  — existing health facilities
_CLR_NEW_FAC       = "#16A34A"               # green — proposed new facilities
_CLR_POP_COVERED   = "#22C55E"               # green — population with access
_CLR_POP_UNCOVERED = "#EF4444"               # red   — population without access

# Discrete opacity levels written by the notebook transform; one Scattermap
# trace per level avoids unreliable per-point rgba string colouring.
_POP_OPACITY_LEVELS = [0.1, 0.3, 0.6, 1.0]


def build_map_figure(
    existing_df: pd.DataFrame,
    new_df: pd.DataFrame,
    pop_df: Optional[pd.DataFrame] = None,
    boundary_wkt: Optional[str] = None,
    map_height_px: Optional[int] = None,
) -> go.Figure:
    """
    Build a Plotly Scattermap that closely matches the reference Folium design.

    Layer render order (bottom → top)
    ──────────────────────────────────
    1  Boundary FILL       – light beige/orange polygon fill (fill='toself')
    2  Uncovered pop dots  – red, 4 separate traces one per opacity quartile
    3  Covered pop dots    – green, 4 separate traces one per opacity quartile
    4  Boundary LINE       – orange border, drawn above population dots
    5  Existing facilities – solid blue circles, size=12 (larger than pop dots)
    6  Proposed facilities – green numbered circles (one marker trace)
    7+ Proposed labels     – white digit text, one single-point trace per fac

    Population dots use per-trace opacity (marker.opacity) rather than
    per-point rgba strings because Plotly Scattermap reliably honours
    per-trace opacity but is inconsistent with per-point colour lists.
    """
    fig = go.Figure()

    # Pre-compute boundary coords once (reused for fill + border traces)
    b_lats: List = []
    b_lons: List = []
    if boundary_wkt:
        b_lats, b_lons = _boundary_wkt_to_coords(boundary_wkt)

    # ── LAYER 1: Boundary fill ────────────────────────────────────────────────
    # fill='toself' fills each ring segment separated by None sentinels.
    # The line is transparent here; the visible orange border is a separate
    # trace (layer 4) drawn above the population dots.
    if b_lats:
        fig.add_trace(go.Scattermap(
            lat=b_lats,
            lon=b_lons,
            mode="lines",
            fill="toself",
            fillcolor=_CLR_BOUNDARY_FILL,
            line=dict(color="rgba(0,0,0,0)", width=0),
            hoverinfo="skip",
            showlegend=False,
            name="boundary-fill",
        ))

    # ── LAYERS 2–3: Population dots ───────────────────────────────────────────
    # Split into 4 sub-traces per colour (one per discrete opacity value).
    # This guarantees correct opacity rendering on all Plotly/MapLibre versions.
    if pop_df is not None and not pop_df.empty:
        uncov = pop_df[~pop_df["covered"]]
        cov   = pop_df[ pop_df["covered"]]

        for op in _POP_OPACITY_LEVELS:
            tol = 0.09  # tolerance for floating-point representation of 0.1/0.3/…

            su = uncov[(uncov["opacity"] - op).abs() <= tol]
            if not su.empty:
                fig.add_trace(go.Scattermap(
                    lat=su["ycoord"].tolist(),
                    lon=su["xcoord"].tolist(),
                    mode="markers",
                    marker=dict(size=7, color=_CLR_POP_UNCOVERED, opacity=op),
                    hovertemplate="Population without access<extra></extra>",
                    showlegend=False,
                    name=f"uncov-{op}",
                ))

            sc = cov[(cov["opacity"] - op).abs() <= tol]
            if not sc.empty:
                fig.add_trace(go.Scattermap(
                    lat=sc["ycoord"].tolist(),
                    lon=sc["xcoord"].tolist(),
                    mode="markers",
                    marker=dict(size=7, color=_CLR_POP_COVERED, opacity=op),
                    hovertemplate="Population with access<extra></extra>",
                    showlegend=False,
                    name=f"cov-{op}",
                ))

    # ── LAYER 4: Boundary border line ─────────────────────────────────────────
    # Rendered after population dots so the orange line sits on top of them.
    if b_lats:
        fig.add_trace(go.Scattermap(
            lat=b_lats,
            lon=b_lons,
            mode="lines",
            line=dict(color=_CLR_BOUNDARY, width=2.5),
            hoverinfo="skip",
            showlegend=False,
            name="boundary-line",
        ))

    # ── LAYER 5: Existing facilities (blue) ───────────────────────────────────
    # size=8 keeps them clearly distinguishable from population dots (size=7)
    # without dominating the map when thousands of facilities are rendered.
    # Blue avoids confusion with red (uncovered) and green (covered) population.
    if not existing_df.empty:
        hover_text = [
            f"<b>{row.get('name', 'Health Facility')}</b><br>"
            f"{row['lat']:.4f}° N, {row['lon']:.4f}° E"
            for _, row in existing_df.iterrows()
        ]
        fig.add_trace(go.Scattermap(
            lat=existing_df["lat"].tolist(),
            lon=existing_df["lon"].tolist(),
            mode="markers",
            marker=dict(size=8, color=_CLR_EXISTING_FAC, opacity=0.85),
            text=hover_text,
            hoverinfo="text",
            name="Existing Facilities",
            showlegend=False,
        ))

    # ── LAYERS 6+: Proposed new facilities ────────────────────────────────────
    # Two-trace approach to defeat MapLibre collision-detection on labels:
    #   • ONE multi-point marker trace → all circles, never collision-checked
    #   • ONE single-point text trace per facility → nothing to collide with
    if not new_df.empty:
        hover_texts = [
            f"<b>Proposed Facility #{i + 1}</b><br>"
            f"ID: {row.get('new_facility', 'N/A')}<br>"
            f"{row['lat']:.4f}° N, {row['lon']:.4f}° E"
            for i, (_, row) in enumerate(new_df.iterrows())
        ]

        fig.add_trace(go.Scattermap(
            lat=new_df["lat"].tolist(),
            lon=new_df["lon"].tolist(),
            mode="markers",
            marker=dict(size=14, color=_CLR_NEW_FAC, opacity=1.0),
            hovertext=hover_texts,
            hoverinfo="text",
            name="Proposed Facilities",
            showlegend=False,
        ))

        for i, (_, row) in enumerate(new_df.iterrows()):
            fig.add_trace(go.Scattermap(
                lat=[row["lat"]],
                lon=[row["lon"]],
                mode="text",
                text=[str(i + 1)],
                textfont=dict(color="white", size=12,
                              family="Inter, sans-serif"),
                textposition="middle center",
                hoverinfo="skip",
                showlegend=False,
            ))

    # ── Layout ────────────────────────────────────────────────────────────────
    layout_kwargs: Dict = dict(
        map_style="open-street-map",
        map=dict(
            center=dict(lat=ZAMBIA_CENTER_LAT, lon=ZAMBIA_CENTER_LON),
            zoom=MAP_ZOOM,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        paper_bgcolor="white",
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#E2E8F0",
            font=dict(family="Inter, sans-serif", size=12, color="#0F172A"),
        ),
        uirevision="map",
    )
    if map_height_px is not None:
        layout_kwargs["height"] = map_height_px
    else:
        layout_kwargs["autosize"] = True

    fig.update_layout(**layout_kwargs)
    return fig


# ── Accessibility helpers ─────────────────────────────────────────────────────

def get_new_facility_rows(results_df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Return the first n rows from the optimisation results table."""
    if n == 0 or results_df.empty:
        return pd.DataFrame(columns=results_df.columns)
    return results_df.head(n).copy()


def get_access_pct(results_df: pd.DataFrame, n: int, n_existing: int) -> float:
    """
    Look up accessibility % for (n_existing + n) total facilities.
    Returns BASELINE_ACCESS_PCT when n == 0.
    """
    if n == 0 or results_df.empty:
        return BASELINE_ACCESS_PCT

    target = n_existing + n
    exact  = results_df.loc[
        results_df["total_facilities"] == target,
        "total_population_access_pct",
    ]
    if not exact.empty:
        return float(exact.iloc[0])

    fallback = results_df.head(n)["total_population_access_pct"]
    return float(fallback.iloc[-1]) if not fallback.empty else BASELINE_ACCESS_PCT


def format_delta(delta: float) -> str:
    """Return a signed, 2-decimal string for an accessibility delta."""
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.2f}%"


# ── Plotly accessibility chart ────────────────────────────────────────────────

def build_accessibility_chart(
    results_df: pd.DataFrame,
    n_new: int,
    n_existing: int,
) -> go.Figure:
    """
    Smooth line chart: total_population_access_pct (Y) vs total_facilities (X).

    X-axis uses actual total_facilities column values (e.g. 80 → 110),
    starting from n_existing (baseline) rather than 0.
    The highlighted dot marks the currently selected slider position.
    """
    # Include baseline as the first point (n_existing facilities, baseline %)
    x_vals = [n_existing] + list(results_df["total_facilities"])
    y_vals = [BASELINE_ACCESS_PCT] + list(results_df["total_population_access_pct"])

    current_x = n_existing + n_new
    current_y = get_access_pct(results_df, n_new, n_existing)

    y_min = round(min(y_vals) - 0.5, 1)
    y_max = round(max(y_vals) + 0.5, 1)

    fig = go.Figure()

    # Shaded fill under the curve
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        fill="tozeroy",
        fillcolor="rgba(79,70,229,0.07)",
        line=dict(color="#4F46E5", width=2.5, shape="spline"),
        mode="lines",
        hovertemplate="Facilities: %{x}<br>Access: %{y:.2f}%<extra></extra>",
        name="Accessibility",
    ))

    # Current selection dot
    fig.add_trace(go.Scatter(
        x=[current_x],
        y=[current_y],
        mode="markers",
        marker=dict(
            color="#4F46E5",
            size=11,
            line=dict(color="white", width=2.5),
        ),
        hovertemplate=f"Facilities: {current_x}<br>Access: {current_y:.2f}%<extra></extra>",
        name="Current",
    ))

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=48, r=12, t=10, b=44),
        xaxis=dict(
            title=dict(
                text="Number of Health Facilities",
                font=dict(size=10, color="#64748B", family="Inter, sans-serif"),
            ),
            gridcolor="#F1F5F9",
            zeroline=False,
            tickfont=dict(size=9, color="#94A3B8", family="Inter, sans-serif"),
            range=[min(x_vals) - 0.5, max(x_vals) + 0.5],
            tickmode="auto",
            nticks=8,
        ),
        yaxis=dict(
            tickformat=".0f",
            ticksuffix="%",
            gridcolor="#F1F5F9",
            zeroline=False,
            tickfont=dict(size=9, color="#94A3B8", family="Inter, sans-serif"),
            range=[y_min, y_max],
            title=dict(
                text="Accessibility",
                font=dict(size=10, color="#64748B", family="Inter, sans-serif"),
            ),
        ),
        showlegend=False,
        height=195,
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#E2E8F0",
            font=dict(family="Inter, sans-serif", size=11),
        ),
    )
    return fig


# ── Recommended locations table data ─────────────────────────────────────────

def get_recommended_table_rows(
    results_df: pd.DataFrame,
    n_new: int,
) -> List[Dict]:
    """
    Return a list of row dicts for the Recommended Locations table.
    Keys: no, lon_dms, lat_dms, new_people
    """
    if n_new == 0 or results_df.empty:
        return []

    rows = results_df.head(n_new).reset_index(drop=True)

    # Per-facility accessibility delta → estimate new people reached
    access_vals = [BASELINE_ACCESS_PCT] + list(rows["total_population_access_pct"])
    deltas      = [access_vals[i + 1] - access_vals[i] for i in range(len(rows))]

    result = []
    for i, (_, row) in enumerate(rows.iterrows()):
        result.append({
            "no":         i + 1,
            "lon_dms":    _to_dms(float(row["lon"]), is_lat=False),
            "lat_dms":    _to_dms(float(row["lat"]), is_lat=True),
            "district":   row.get("district") or "—",
            "new_people": max(0, int(deltas[i] / 100 * ZAMBIA_POPULATION)),
        })
    return result