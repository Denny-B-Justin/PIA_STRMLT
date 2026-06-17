"""
GoAT — Chart utility functions.

All Plotly figure construction lives here so app.py stays callback-only
and chart logic is independently testable.

Public API
----------
build_project_status_chart(df)     → go.Figure
build_lending_instrument_chart(df) → go.Figure
build_hierarchy_sunburst(df)       → go.Figure   (Keywords tab)
build_empty_chart(message)         → go.Figure   (placeholder / error state)
"""

from __future__ import annotations

import logging
import pandas as pd
import plotly.graph_objects as go
from typing import Optional

from goat_src.constants import (
    CHART_COLORS,
    CHART_LAYOUT_DEFAULTS,
    SUNBURST_INNER_COLORS,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _merged_layout(**overrides) -> dict:
    """
    Return a layout dict starting from CHART_LAYOUT_DEFAULTS with chart-specific
    overrides applied (shallow merge — callers supply full nested dicts).
    """
    base = dict(CHART_LAYOUT_DEFAULTS)
    base.update(overrides)
    return base


def _safe_str_list(series: pd.Series) -> list:
    """Convert a column to a clean Python list of strings (for Plotly x-axis)."""
    return series.fillna("Unknown").astype(str).tolist()


# ═══════════════════════════════════════════════════════════════════════════════
# Public chart builders
# ═══════════════════════════════════════════════════════════════════════════════

def build_project_status_chart(df: Optional[pd.DataFrame]) -> go.Figure:
    """
    Stacked bar chart — Number of Projects (Y) vs Approval FY (X),
    one bar segment per Project Status value.

    Expected input columns:
        approval_fy, project_status, project_count
    """
    if df is None or df.empty:
        logger.warning("[GoAT] build_project_status_chart: empty dataframe")
        return build_empty_chart("No project status data for the selected filters.")

    df = df.copy()
    df["approval_fy"] = pd.to_numeric(df["approval_fy"], errors="coerce")
    sorted_years = [str(int(y)) for y in sorted(df["approval_fy"].dropna().unique())]
    fig      = go.Figure()
    statuses = sorted(df["project_status"].dropna().unique())

    for idx, status in enumerate(statuses):
        subset = (
            df[df["project_status"] == status]
            .assign(approval_fy=lambda d: d["approval_fy"].astype(int))
            .sort_values("approval_fy")
        )
        colour = CHART_COLORS[idx % len(CHART_COLORS)]
        fig.add_trace(go.Bar(
            x    = _safe_str_list(subset["approval_fy"]),
            y    = subset["project_count"].tolist(),
            name = status,
            marker_color = colour,
            hovertemplate = (
                f"<b>{status}</b><br>"
                "FY %{x}<br>"
                "Projects: <b>%{y:,}</b>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_merged_layout(
            title=dict(
                text    = "Project Status",
                font    = dict(size=15, color="#E2E8F0"),
                x       = 0,
                xanchor = "left",
            ),
            xaxis=dict(
                title         = dict(text="Approval FY", font=dict(color="#A0AEC0", size=12)),
                gridcolor     = "#2d2d2d",
                zeroline      = False,
                tickfont      = dict(color="#A0AEC0", size=11),
                categoryorder = "array",
                categoryarray = sorted_years,
            ),
            yaxis=dict(
                title    = dict(text="Number of Projects", font=dict(color="#A0AEC0", size=12)),
                gridcolor = "#2d2d2d",
                zeroline  = False,
                tickfont  = dict(color="#A0AEC0", size=11),
            ),
        )
    )
    return fig


def build_lending_instrument_chart(df: Optional[pd.DataFrame]) -> go.Figure:
    """
    Stacked bar chart — Number of Projects (Y) vs Approval FY (X),
    one bar segment per Lending Instrument value.

    Expected input columns:
        approval_fy, lending_instrument, project_count
    """
    if df is None or df.empty:
        logger.warning("[GoAT] build_lending_instrument_chart: empty dataframe")
        return build_empty_chart("No lending instrument data for the selected filters.")

    df = df.copy()
    df["approval_fy"] = pd.to_numeric(df["approval_fy"], errors="coerce")
    sorted_years = [str(int(y)) for y in sorted(df["approval_fy"].dropna().unique())]
    fig         = go.Figure()
    instruments = sorted(df["lending_instrument"].dropna().unique())

    for idx, instr in enumerate(instruments):
        subset = (
            df[df["lending_instrument"] == instr]
            .assign(approval_fy=lambda d: d["approval_fy"].astype(int))
            .sort_values("approval_fy")
        )
        colour = CHART_COLORS[idx % len(CHART_COLORS)]
        fig.add_trace(go.Bar(
            x    = _safe_str_list(subset["approval_fy"]),
            y    = subset["project_count"].tolist(),
            name = instr,
            marker_color = colour,
            hovertemplate = (
                f"<b>{instr}</b><br>"
                "FY %{x}<br>"
                "Projects: <b>%{y:,}</b>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_merged_layout(
            title=dict(
                text    = "Lending Instrument",
                font    = dict(size=15, color="#E2E8F0"),
                x       = 0,
                xanchor = "left",
            ),
            xaxis=dict(
                title         = dict(text="Approval FY", font=dict(color="#A0AEC0", size=12)),
                gridcolor     = "#2d2d2d",
                zeroline      = False,
                tickfont      = dict(color="#A0AEC0", size=11),
                categoryorder = "array",
                categoryarray = sorted_years,
            ),
            yaxis=dict(
                title    = dict(text="Number of Projects", font=dict(color="#A0AEC0", size=12)),
                gridcolor = "#2d2d2d",
                zeroline  = False,
                tickfont  = dict(color="#A0AEC0", size=11),
            ),
        )
    )
    return fig


def build_hierarchy_sunburst(df: Optional[pd.DataFrame]) -> go.Figure:
    """
    Two-ring sunburst chart for the Keywords > Available Hierarchies tab.

    Inner ring  — unique hierarchy full-names (one sector per hierarchy).
    Outer ring  — individual keywords belonging to each hierarchy.

    Expected input columns (from QUERY_HIERARCHY_TABLE):
        fullname   : hierarchy display name  (inner ring label)
        keyword    : individual keyword      (outer ring label)

    Both fullname and keyword are de-duplicated before rendering to avoid
    duplicate-id errors in Plotly's sunburst id system.
    """
    if df is None or df.empty:
        logger.warning("[GoAT] build_hierarchy_sunburst: empty dataframe")
        return build_empty_chart("No hierarchy data found.")

    df = df.copy()
    df["fullname"] = df["fullname"].fillna("Unknown").astype(str).str.strip()
    df["keyword"]  = df["keyword"].fillna("").astype(str).str.strip()
    df = df[df["keyword"] != ""]

    # Deduplicate: each (fullname, keyword) pair should appear exactly once.
    df = df.drop_duplicates(subset=["fullname", "keyword"])

    fullnames = df["fullname"].unique().tolist()

    # ── Build Plotly sunburst data arrays ──────────────────────────────────────
    # Plotly sunburst uses flat parent/label/value arrays.
    # Root (invisible) → hierarchy fullname → keyword

    ids      = [""]                  # root
    labels   = [""]
    parents  = [""]
    values   = [0]
    colors   = ["rgba(0,0,0,0)"]    # root is invisible

    kw_counts = df.groupby("fullname")["keyword"].count().to_dict()

    for i, fn in enumerate(fullnames):
        fn_id  = f"__fn__{fn}"
        fn_clr = SUNBURST_INNER_COLORS[i % len(SUNBURST_INNER_COLORS)]

        ids.append(fn_id)
        labels.append(fn)
        parents.append("")
        values.append(kw_counts.get(fn, 0))
        colors.append(fn_clr)

        # Outer ring: keywords — each gets a slightly lighter shade of the
        # hierarchy colour via rgba opacity variation.
        kws = df[df["fullname"] == fn]["keyword"].tolist()
        for j, kw in enumerate(kws):
            # Ensure globally unique id: combine fullname prefix + keyword
            kw_id = f"{fn_id}::{kw}"
            ids.append(kw_id)
            labels.append(kw)
            parents.append(fn_id)
            values.append(1)
            # Alternate opacity for visual rhythm inside each segment
            alpha = 0.65 if j % 2 == 0 else 0.45
            colors.append(_hex_to_rgba(fn_clr, alpha))

    fig = go.Figure(
        go.Sunburst(
            ids       = ids,
            labels    = labels,
            parents   = parents,
            values    = values,
            branchvalues = "total",
            marker    = dict(colors=colors),
            hovertemplate = (
                "<b>%{label}</b><br>"
                "Keywords: %{value}<br>"
                "<extra></extra>"
            ),
            insidetextorientation = "radial",
            textfont = dict(
                family = "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                size   = 11,
                color  = "#FFFFFF",
            ),
            leaf = dict(opacity=0.85),
        )
    )

    fig.update_layout(
        paper_bgcolor = "#1e1e1e",
        plot_bgcolor  = "#1e1e1e",
        margin        = dict(l=0, r=0, t=10, b=0),
        font          = dict(
            family = "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            color  = "#E2E8F0",
            size   = 12,
        ),
        hoverlabel = dict(
            bgcolor     = "#252525",
            bordercolor = "#3a3a3a",
            font        = dict(
                family = "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                size   = 12,
                color  = "#E2E8F0",
            ),
        ),
    )
    return fig


def build_empty_chart(message: str = "No data available.") -> go.Figure:
    """
    Return a blank dark-themed placeholder figure.
    Used when a query returns no rows, or when a DB error occurs.
    """
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor = "#1e1e1e",
        plot_bgcolor  = "#1e1e1e",
        xaxis         = dict(visible=False),
        yaxis         = dict(visible=False),
        margin        = dict(l=0, r=0, t=0, b=0),
        annotations   = [
            dict(
                text      = message,
                x=0.5, y=0.5,
                xref      = "paper",
                yref      = "paper",
                showarrow = False,
                font      = dict(
                    color  = "#718096",
                    size   = 13,
                    family = "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                ),
            )
        ],
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# Private colour utilities
# ═══════════════════════════════════════════════════════════════════════════════

def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert a #RRGGBB hex string to an rgba(...) CSS string."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha:.2f})"