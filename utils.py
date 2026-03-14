"""
utils.py
Map-building helpers, KPI card HTML, and accessibility calculation utilities.

Public interface is unchanged from the Databricks version.
"""

import folium
import pandas as pd

from constants import (
    BASELINE_ACCESS_PCT,
    ZAMBIA_CENTER_LAT,
    ZAMBIA_CENTER_LON,
    MAP_ZOOM,
    COLOUR_EXISTING,
    COLOUR_NEW,
    COLOUR_NEW_RING,
)


# ── Map helpers ───────────────────────────────────────────────────────────────

def build_folium_map(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> folium.Map:
    """
    Build a Folium map with two feature groups:
      • Orange circle markers  → existing health facilities
      • White circle markers   → new / proposed health facilities
    Returns a folium.Map object.
    """
    fmap = folium.Map(
        location=[ZAMBIA_CENTER_LAT, ZAMBIA_CENTER_LON],
        zoom_start=MAP_ZOOM,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # ── Existing facilities ───────────────────────────────────────────────────
    existing_group = folium.FeatureGroup(name="Existing Facilities", show=True)
    for _, row in existing_df.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=5,
            color=COLOUR_EXISTING,
            weight=1.5,
            fill=True,
            fill_color=COLOUR_EXISTING,
            fill_opacity=0.85,
            tooltip=folium.Tooltip(
                f"<b>{row.get('name', 'Health Facility')}</b><br>"
                f"Lat: {row['lat']:.4f} | Lon: {row['lon']:.4f}",
                sticky=False,
            ),
        ).add_to(existing_group)
    existing_group.add_to(fmap)

    # ── New proposed facilities ───────────────────────────────────────────────
    if not new_df.empty:
        new_group = folium.FeatureGroup(name="New Facilities", show=True)
        for _, row in new_df.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=8,
                color=COLOUR_NEW_RING,
                weight=2.5,
                fill=True,
                fill_color=COLOUR_NEW,
                fill_opacity=0.95,
                tooltip=folium.Tooltip(
                    f"<b>Proposed Facility</b><br>"
                    f"ID: {row.get('new_facility', 'N/A')}<br>"
                    f"Lat: {row['lat']:.4f} | Lon: {row['lon']:.4f}",
                    sticky=False,
                ),
            ).add_to(new_group)
        new_group.add_to(fmap)

    folium.LayerControl(collapsed=False).add_to(fmap)
    return fmap


def get_map_html(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> str:
    """
    Build a Folium map and return its full HTML representation as a string
    suitable for embedding in a Dash html.Iframe srcDoc attribute.
    """
    fmap = build_folium_map(existing_df, new_df)
    return fmap._repr_html_()


# ── Accessibility helpers ─────────────────────────────────────────────────────

def get_new_facility_rows(results_df: pd.DataFrame, n: int) -> pd.DataFrame:
    """
    Return the first n rows from the optimisation results table.
    Returns an empty DataFrame when n == 0.
    """
    if n == 0 or results_df.empty:
        return pd.DataFrame(columns=results_df.columns)
    return results_df.head(n).copy()


def get_access_pct(results_df: pd.DataFrame, n: int, n_existing: int) -> float:
    """
    Look up accessibility % for exactly (n_existing + n) total facilities.
    Falls back to the tail of the first-n slice if the exact row is absent.
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

    # Fallback: last row of the first-n slice
    fallback = results_df.head(n)["total_population_access_pct"]
    return float(fallback.iloc[-1]) if not fallback.empty else BASELINE_ACCESS_PCT


# ── KPI formatting helpers ────────────────────────────────────────────────────

def format_delta(delta: float) -> str:
    """Return a signed, 2-decimal string for an accessibility delta."""
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.2f}%"


def kpi_card(label: str, value: str, sub: str, accent: str,
             progress: float | None = None):
    """
    Return a Dash component tree for a single KPI scorecard block.

    Parameters
    ----------
    label    : uppercase label shown at the top
    value    : large displayed metric
    sub      : small subtitle / context line
    accent   : CSS hex colour for the top border and value text
    progress : optional 0–100 float that renders a thin animated progress bar
    """
    # Lazily import here to avoid a circular dependency at module import time
    from dash import html

    children = [
        # Coloured top accent bar
        html.Div(style={
            "position": "absolute", "top": "0", "left": "0", "right": "0",
            "height": "3px", "background": accent,
            "borderRadius": "14px 14px 0 0",
        }),
        # Label
        html.Div(label, style={
            "fontSize": "0.63rem", "fontWeight": "700",
            "textTransform": "uppercase", "letterSpacing": "1.5px",
            "color": "#3D5068", "marginBottom": "8px",
            "fontFamily": "'Space Mono', monospace",
        }),
        # Value
        html.Div(value, style={
            "fontFamily": "'Space Mono', monospace",
            "fontSize": "2.1rem", "fontWeight": "700",
            "lineHeight": "1", "color": accent,
        }),
        # Subtitle
        html.Div(sub, style={
            "fontSize": "0.73rem", "color": "#3D5068", "marginTop": "5px",
        }),
    ]

    # Optional progress bar
    if progress is not None:
        pct = max(0.0, min(100.0, progress))
        children.append(
            html.Div(
                html.Div(style={
                    "width": f"{pct:.1f}%",
                    "height": "100%",
                    "background": f"linear-gradient(90deg, {accent}88, {accent})",
                    "borderRadius": "99px",
                    "transition": "width 0.6s cubic-bezier(.4,0,.2,1)",
                }),
                style={
                    "marginTop": "14px", "background": "#0E1829",
                    "borderRadius": "99px", "height": "4px", "overflow": "hidden",
                },
            )
        )

    return html.Div(
        children=children,
        style={
            "background": "linear-gradient(155deg, #0C1625 0%, #101E30 100%)",
            "border": "1px solid #182236",
            "borderRadius": "14px",
            "padding": "20px 20px 16px",
            "position": "relative",
            "overflow": "hidden",
            "height": "100%",
            "boxSizing": "border-box",
        },
    )