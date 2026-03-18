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

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional
from constants import (
    BASELINE_ACCESS_PCT,
    ZAMBIA_CENTER_LAT,
    ZAMBIA_CENTER_LON,
    MAP_ZOOM,
)

# Zambia 2025 population estimate — used for "new people reached" calculation
ZAMBIA_POPULATION = 20_500_000


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

def build_map_figure(
    existing_df: pd.DataFrame,
    new_df: pd.DataFrame,
    map_height_px: Optional[int] = None,
) -> go.Figure:
    """
    Build a Plotly Scattermap figure with:
      • Red filled circles  → existing health facilities
      • Green numbered circles → new / proposed facilities

    Uses open-street-map tiles (no Mapbox token required).
    Rendered as dcc.Graph — no iframe or external CDN needed.
    """
    fig = go.Figure()

    # ── Existing facilities ───────────────────────────────────────────────────
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
            marker=dict(size=7, color="#DC2626", opacity=0.75),
            text=hover_text,
            hoverinfo="text",
            name="Existing Facilities",
        ))

    # ── New proposed facilities ───────────────────────────────────────────────
    # Why previous approaches failed:
    #
    #  ✗  Single trace, mode="markers+text"  — MapLibre collision detection
    #     suppresses all but one labelled marker within the same trace layer.
    #
    #  ✗  Per-facility traces sharing legendgroup — legendgroup linkage can
    #     still trigger MapLibre layer suppression across sibling traces.
    #
    # Definitive fix — two completely independent rendering layers:
    #
    #  ✓  Layer 1: ONE trace containing ALL green circles (mode="markers",
    #     no text). Multi-point marker-only traces are never collision-checked.
    #
    #  ✓  Layer 2: ONE text-only trace PER facility (single point each).
    #     Single-point text traces have nothing to collide with and always render.
    #     They are completely decoupled from the marker layer.
    if not new_df.empty:
        hover_texts = [
            f"<b>Proposed Facility #{i + 1}</b><br>"
            f"ID: {row.get('new_facility', 'N/A')}<br>"
            f"{row['lat']:.4f}° N, {row['lon']:.4f}° E"
            for i, (_, row) in enumerate(new_df.iterrows())
        ]

        # Layer 1 — all green circles in one trace (always renders all points)
        fig.add_trace(go.Scattermap(
            lat=new_df["lat"].tolist(),
            lon=new_df["lon"].tolist(),
            mode="markers",
            marker=dict(size=24, color="#16A34A", opacity=1.0),
            hovertext=hover_texts,
            hoverinfo="text",
            name="Proposed Facilities",
            showlegend=False,
        ))

        # Layer 2 — one independent text trace per facility
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

    layout_kwargs = dict(
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
            "new_people": max(0, int(deltas[i] / 100 * ZAMBIA_POPULATION)),
        })
    return result