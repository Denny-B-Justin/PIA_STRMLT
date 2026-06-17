"""
GoAT — Governance Operations Analytics Tool
Dash application entry point.

Architecture
------------
  constants.py  ← app config, column names, chart defaults
  queries.py    ← QueryService (Databricks auth + TTL cache + SQL builders)
  utils.py      ← Plotly figure constructors
  app.py        ← Dash layout + callbacks (this file)

Callback flow — Dashboard
--------------------------
  1. init_filter_options   — page load → populate Lending Instrument + Keywords dropdowns
  2. cascade_regions       — Lending Instrument change → update Region options
  3. apply_filters         — "Apply Filters" click → fetch all chart / table data
  4. render_download_table — store-download change → populate DataTable + tooltips
  5. export_csv            — "Export CSV" click → send CSV via dcc.Download

Callback flow — Keywords tab
------------------------------
  6. init_keywords_tab     — Keywords tab activated → load sunburst + delete dropdown
  7. add_keyword           — "Add Keyword" click → run keyword search + INSERT rows
  8. delete_hierarchy      — "Delete Hierarchy" click → soft-delete (Valid_Hierarchy=False)
"""

from __future__ import annotations

import logging
import pandas as pd

import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context, no_update
import dash_bootstrap_components as dbc

from goat_src.constants import ABOUT_TEXT, APP_TITLE
from goat_src.queries import QueryService
from goat_src.utils import (
    build_project_status_chart,
    build_lending_instrument_chart,
    build_hierarchy_sunburst,
    build_empty_chart,
)

# ── Logging ────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── App initialisation ─────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
    ],
    suppress_callback_exceptions=True,
    title="GoAT",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server  # expose WSGI server for Posit Connect / gunicorn

# ── QueryService singleton ─────────────────────────────────────────────────────
qs = QueryService.get_instance()


# ═══════════════════════════════════════════════════════════════════════════════
# Style constants
# ═══════════════════════════════════════════════════════════════════════════════

_BG_ROOT    = "#141414"
_BG_SIDEBAR = "#1a1a1a"
_BG_CARD    = "#1e1e1e"
_BG_HEADER  = "#1a1a1a"
_BORDER     = "#2d2d2d"
_ACCENT     = "#E63946"
_TEXT_PRI   = "#FFFFFF"
_TEXT_SEC   = "#CBD5E0"
_TEXT_MUTED = "#A0AEC0"

_SIDEBAR_STYLE = {
    "backgroundColor": _BG_SIDEBAR,
    "border":          f"1px solid {_BORDER}",
    "borderRadius":    "8px",
    "padding":         "20px 16px",
}

_FILTER_LABEL = {
    "color":         _TEXT_MUTED,
    "fontSize":      "11px",
    "letterSpacing": "0.06em",
    "marginBottom":  "6px",
    "display":       "block",
}

_DD_STYLE = {"marginBottom": "20px"}

_MAIN_TAB = {
    "color":           _TEXT_MUTED,
    "backgroundColor": _BG_ROOT,
    "border":          "none",
    "borderBottom":    "2px solid transparent",
    "padding":         "14px 24px",
    "fontFamily":      "Fira Sans",
    "fontSize":        "15px",
}
_MAIN_TAB_SEL = {
    **_MAIN_TAB,
    "color":        _ACCENT,
    "borderBottom": f"2px solid {_ACCENT}",
    "fontWeight":   "600",
}

_KW_SUB_TAB = {
    "color":           _TEXT_MUTED,
    "backgroundColor": _BG_ROOT,
    "border":          "none",
    "borderBottom":    "2px solid transparent",
    "padding":         "10px 20px",
    "fontFamily":      "Fira Sans",
    "fontSize":        "13px",
}
_KW_SUB_TAB_SEL = {
    **_KW_SUB_TAB,
    "color":        _ACCENT,
    "borderBottom": f"2px solid {_ACCENT}",
    "fontWeight":   "600",
}

_CHART_TAB = {
    "color":           _TEXT_MUTED,
    "backgroundColor": _BG_CARD,
    "border":          "none",
    "borderBottom":    "2px solid transparent",
    "padding":         "10px 18px",
    "fontFamily":      "Fira Sans",
    "fontSize":        "13px",
}
_CHART_TAB_SEL = {
    **_CHART_TAB,
    "color":        _ACCENT,
    "borderBottom": f"2px solid {_ACCENT}",
    "fontWeight":   "600",
}

_TABLE_CELL = {
    "backgroundColor": _BG_CARD,
    "color":           _TEXT_SEC,
    "border":          f"1px solid {_BORDER}",
    "fontFamily":      "Fira Sans",
    "fontSize":        "12px",
    "padding":         "8px 12px",
    "textAlign":       "left",
    "overflow":        "hidden",
    "textOverflow":    "ellipsis",
    "maxWidth":        "260px",
    "whiteSpace":      "nowrap",
}
_TABLE_HEADER = {
    "backgroundColor": "#252525",
    "color":           _TEXT_PRI,
    "fontWeight":      "600",
    "border":          "1px solid #3a3a3a",
    "fontSize":        "12px",
    "padding":         "8px 12px",
    "textAlign":       "left",
    "textTransform":   "uppercase",
    "letterSpacing":   "0.04em",
}

# Shared input / button styles for the Keywords forms
_INPUT_STYLE = {
    "backgroundColor": "#252525",
    "color":           _TEXT_PRI,
    "border":          f"1px solid {_BORDER}",
    "borderRadius":    "6px",
    "padding":         "8px 12px",
    "width":           "100%",
    "fontFamily":      "Fira Sans",
    "fontSize":        "13px",
    "marginBottom":    "16px",
    "outline":         "none",
}

_FORM_LABEL = {
    "color":         _TEXT_MUTED,
    "fontSize":      "12px",
    "letterSpacing": "0.04em",
    "display":       "block",
    "marginBottom":  "6px",
}

_FORM_CARD = {
    "backgroundColor": _BG_SIDEBAR,
    "border":          f"1px solid {_BORDER}",
    "borderRadius":    "8px",
    "padding":         "24px",
    "maxWidth":        "640px",
}

_ALERT_SUCCESS = {
    "backgroundColor": "#1a3a2a",
    "border":          "1px solid #2d6a4f",
    "borderRadius":    "6px",
    "color":           "#68D391",
    "padding":         "10px 14px",
    "fontSize":        "13px",
    "fontFamily":      "Fira Sans",
    "marginTop":       "12px",
}

_ALERT_ERROR = {
    "backgroundColor": "#3a1a1a",
    "border":          "1px solid #E63946",
    "borderRadius":    "6px",
    "color":           "#FC8181",
    "padding":         "10px 14px",
    "fontSize":        "13px",
    "fontFamily":      "Fira Sans",
    "marginTop":       "12px",
}

_ALERT_INFO = {
    "backgroundColor": "#1a2a3a",
    "border":          "1px solid #4299E1",
    "borderRadius":    "6px",
    "color":           "#90CDF4",
    "padding":         "10px 14px",
    "fontSize":        "13px",
    "fontFamily":      "Fira Sans",
    "marginTop":       "12px",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Layout helpers — Dashboard tab
# ═══════════════════════════════════════════════════════════════════════════════

def _filter_sidebar() -> html.Div:
    """Left-hand sidebar with all Dashboard filter controls."""
    return html.Div(
        style=_SIDEBAR_STYLE,
        children=[
            html.Label("Select Lending Instrument", style=_FILTER_LABEL),
            dcc.Dropdown(
                id="dd-lending-instr",
                multi=True,
                placeholder="Loading…",
                style=_DD_STYLE,
                optionHeight=40,
            ),
            html.Label("Select Region", style=_FILTER_LABEL),
            dcc.Dropdown(
                id="dd-region",
                multi=True,
                placeholder="Loading…",
                style=_DD_STYLE,
                optionHeight=40,
            ),
            html.Label("Filter by Keywords", style=_FILTER_LABEL),
            dcc.Dropdown(
                id="dd-keywords",
                multi=True,
                placeholder="Choose hierarchy",
                style=_DD_STYLE,
            ),
            html.Label("Keyword filter logic", style=_FILTER_LABEL),
            dcc.RadioItems(
                id="radio-and-or",
                options=[
                    {"label": "  AND  — project must match all selected hierarchies", "value": "AND"},
                    {"label": "  OR   — project must match any selected hierarchy",   "value": "OR"},
                ],
                value="AND",
                labelStyle={
                    "display":      "block",
                    "color":        _TEXT_SEC,
                    "fontSize":     "12px",
                    "marginBottom": "6px",
                    "cursor":       "pointer",
                },
                inputStyle={"marginRight": "6px", "accentColor": _ACCENT},
                style={"marginBottom": "24px"},
            ),
            dbc.Button(
                children=[html.I(className="bi bi-funnel-fill me-2"), "Apply Filters"],
                id="btn-apply",
                color="danger",
                className="w-100",
                n_clicks=0,
                style={"borderRadius": "6px", "fontWeight": "600", "fontSize": "14px"},
            ),
        ],
    )


def _download_tab_content() -> html.Div:
    """Content of the Download Data sub-tab."""
    return html.Div(
        style={"padding": "16px 0"},
        children=[
            html.Div(
                style={
                    "display":        "flex",
                    "justifyContent": "space-between",
                    "alignItems":     "center",
                    "marginBottom":   "14px",
                },
                children=[
                    html.H5(
                        "Download Projects",
                        style={"color": _TEXT_PRI, "margin": "0", "fontWeight": "600"},
                    ),
                    dbc.Button(
                        [html.I(className="bi bi-download me-2"), "Export CSV"],
                        id="btn-export-csv",
                        color="danger",
                        outline=True,
                        size="sm",
                        n_clicks=0,
                        style={"borderRadius": "5px"},
                    ),
                ],
            ),
            dcc.Download(id="download-csv"),
            dash_table.DataTable(
                id="tbl-download",
                page_size=15,
                filter_action="native",
                sort_action="native",
                style_table={"overflowX": "auto"},
                style_cell=_TABLE_CELL,
                style_header=_TABLE_HEADER,
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#222222"}
                ],
                tooltip_delay=0,
                tooltip_duration=None,
            ),
        ],
    )


def _dashboard_content() -> html.Div:
    """Full Dashboard tab: sidebar + metric + chart sub-tabs."""
    return html.Div(
        style={"display": "flex", "gap": "20px", "padding": "20px 0"},
        children=[
            html.Div(_filter_sidebar(), style={"width": "300px", "flexShrink": "0"}),
            html.Div(
                style={"flex": "1", "minWidth": "0"},
                children=[
                    html.Div(
                        style={"marginBottom": "22px"},
                        children=[
                            html.Span(
                                "Total Number of Projects",
                                style={"color": _TEXT_MUTED, "fontSize": "13px", "display": "block"},
                            ),
                            html.H2(
                                id="metric-total",
                                children="—",
                                style={
                                    "color":      _TEXT_PRI,
                                    "fontSize":   "44px",
                                    "margin":     "4px 0 0",
                                    "lineHeight": "1",
                                    "fontFamily": "Fira Sans",
                                },
                            ),
                        ],
                    ),
                    dcc.Loading(
                        type="circle",
                        color=_ACCENT,
                        children=dcc.Tabs(
                            id="chart-tabs",
                            value="tab-status",
                            style={"borderBottom": f"1px solid {_BORDER}", "marginBottom": "0"},
                            children=[
                                dcc.Tab(
                                    label="Project Status",
                                    value="tab-status",
                                    style=_CHART_TAB,
                                    selected_style=_CHART_TAB_SEL,
                                    children=[
                                        dcc.Graph(
                                            id="chart-project-status",
                                            config={
                                                "displayModeBar": True,
                                                "displaylogo":    False,
                                                "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                                            },
                                            style={"height": "460px"},
                                        )
                                    ],
                                ),
                                dcc.Tab(
                                    label="Lending Instrument",
                                    value="tab-lending",
                                    style=_CHART_TAB,
                                    selected_style=_CHART_TAB_SEL,
                                    children=[
                                        dcc.Graph(
                                            id="chart-lending-instr",
                                            config={
                                                "displayModeBar": True,
                                                "displaylogo":    False,
                                                "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                                            },
                                            style={"height": "460px"},
                                        )
                                    ],
                                ),
                                dcc.Tab(
                                    label="Download Data",
                                    value="tab-download",
                                    style=_CHART_TAB,
                                    selected_style=_CHART_TAB_SEL,
                                    children=[_download_tab_content()],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Layout helpers — Keywords tab
# ═══════════════════════════════════════════════════════════════════════════════

def _keywords_available_hierarchies() -> html.Div:
    """
    Sub-tab 1: Available Hierarchies.
    Displays a sunburst chart where the inner ring = hierarchy full-name
    and the outer ring = individual keywords.
    """
    return html.Div(
        style={"padding": "24px 0"},
        children=[
            html.H5(
                "Available Keyword Hierarchies",
                style={"color": _TEXT_PRI, "marginBottom": "6px", "fontWeight": "600"},
            ),
            html.P(
                "The inner ring shows hierarchy names; the outer ring shows their individual keywords. "
                "Click a segment to zoom in.",
                style={"color": _TEXT_MUTED, "fontSize": "13px", "marginBottom": "20px"},
            ),
            dcc.Loading(
                id="loading-sunburst",
                type="circle",
                color=_ACCENT,
                children=dcc.Graph(
                    id="chart-hierarchy-sunburst",
                    config={
                        "displayModeBar": False,
                        "displaylogo":    False,
                    },
                    style={"height": "600px"},
                    figure=build_empty_chart("Loading hierarchy data…"),
                ),
            ),
        ],
    )


def _keywords_add_new() -> html.Div:
    """
    Sub-tab 2: Add New Keywords.

    Inputs:
      • Hierarchy Name  (short code, e.g. "PIM")
      • Full Name       (e.g. "Public Investment Management")
      • Keywords        (comma-separated)

    On submit:
      1. Vectorised keyword search over all project text columns.
      2. New rows inserted into the UC table with Valid_Hierarchy = 'True'.
    """
    return html.Div(
        style={"padding": "24px 0"},
        children=[
            html.H5(
                "Add New Keyword Hierarchy",
                style={"color": _TEXT_PRI, "marginBottom": "6px", "fontWeight": "600"},
            ),
            html.P(
                "Define a new thematic hierarchy and its associated keywords. "
                "A keyword search will be run across all project text fields and "
                "results will be persisted to the database.",
                style={"color": _TEXT_MUTED, "fontSize": "13px", "marginBottom": "24px"},
            ),

            html.Div(
                style=_FORM_CARD,
                children=[
                    # ── Hierarchy Name ─────────────────────────────────────────
                    html.Label("Hierarchy Name (e.g., PIM)", style=_FORM_LABEL),
                    dcc.Input(
                        id="input-hier-name",
                        type="text",
                        placeholder="e.g., PIM",
                        debounce=False,
                        style=_INPUT_STYLE,
                    ),

                    # ── Full Name ──────────────────────────────────────────────
                    html.Label("Full Name (e.g., Public Investment Management)", style=_FORM_LABEL),
                    dcc.Input(
                        id="input-hier-fullname",
                        type="text",
                        placeholder="e.g., Public Investment Management",
                        debounce=False,
                        style=_INPUT_STYLE,
                    ),

                    # ── Keywords ───────────────────────────────────────────────
                    html.Label("Keywords (comma-separated)", style=_FORM_LABEL),
                    dcc.Input(
                        id="input-hier-keywords",
                        type="text",
                        placeholder="e.g., public investment, capital budget, appraisal",
                        debounce=False,
                        style=_INPUT_STYLE,
                    ),

                    # ── Info note ──────────────────────────────────────────────
                    html.Div(
                        [
                            html.I(className="bi bi-info-circle me-2"),
                            "This will search ~10,000 project records. "
                            "Processing may take 30–90 seconds.",
                        ],
                        style={**_ALERT_INFO, "marginTop": "0", "marginBottom": "16px"},
                    ),

                    # ── Submit button ──────────────────────────────────────────
                    dbc.Button(
                        [html.I(className="bi bi-plus-circle me-2"), "Add Keyword"],
                        id="btn-add-keyword",
                        color="danger",
                        n_clicks=0,
                        style={
                            "borderRadius": "6px",
                            "fontWeight":   "600",
                            "fontSize":     "14px",
                            "minWidth":     "160px",
                        },
                        disabled=False,
                    ),

                    # ── Feedback area ──────────────────────────────────────────
                    dcc.Loading(
                        id="loading-add-kw",
                        type="dot",
                        color=_ACCENT,
                        children=html.Div(id="add-kw-feedback", style={"minHeight": "48px"}),
                    ),
                ],
            ),
        ],
    )


def _keywords_delete_hierarchy() -> html.Div:
    """
    Sub-tab 3: Delete Hierarchy.

    Shows a dropdown of all currently valid hierarchies.
    On submit, Valid_Hierarchy is flipped to 'False' in the UC table —
    no rows are physically deleted.
    """
    return html.Div(
        style={"padding": "24px 0"},
        children=[
            html.H5(
                "Deactivate a Hierarchy",
                style={"color": _TEXT_PRI, "marginBottom": "6px", "fontWeight": "600"},
            ),
            html.P(
                "Selecting a hierarchy below will mark it as inactive. "
                "It will no longer appear in the Dashboard filters or charts, "
                "but the data is preserved and can be restored if needed.",
                style={"color": _TEXT_MUTED, "fontSize": "13px", "marginBottom": "24px"},
            ),

            html.Div(
                style=_FORM_CARD,
                children=[
                    html.Label("Select a Hierarchy to Deactivate", style=_FORM_LABEL),
                    dcc.Dropdown(
                        id="dd-delete-hierarchy",
                        placeholder="Loading hierarchies…",
                        clearable=True,
                        style={
                            "backgroundColor": "#252525",
                            "color":           _TEXT_PRI,
                            "border":          f"1px solid {_BORDER}",
                            "borderRadius":    "6px",
                            "marginBottom":    "20px",
                        },
                    ),

                    # ── Warning banner ─────────────────────────────────────────
                    html.Div(
                        [
                            html.I(className="bi bi-exclamation-triangle me-2"),
                            "This action hides the hierarchy from all users immediately. "
                            "It does not permanently delete any data.",
                        ],
                        style={
                            "backgroundColor": "#3a2a1a",
                            "border":          "1px solid #F6AD55",
                            "borderRadius":    "6px",
                            "color":           "#F6AD55",
                            "padding":         "10px 14px",
                            "fontSize":        "13px",
                            "fontFamily":      "Fira Sans",
                            "marginBottom":    "20px",
                        },
                    ),

                    dbc.Button(
                        [html.I(className="bi bi-trash me-2"), "Delete Hierarchy"],
                        id="btn-delete-hierarchy",
                        color="danger",
                        outline=True,
                        n_clicks=0,
                        style={
                            "borderRadius": "6px",
                            "fontWeight":   "600",
                            "fontSize":     "14px",
                            "minWidth":     "180px",
                        },
                    ),

                    # ── Feedback area ──────────────────────────────────────────
                    html.Div(id="delete-hier-feedback", style={"minHeight": "48px"}),
                ],
            ),
        ],
    )


def _keywords_tab_content() -> html.Div:
    """Full Keywords tab: three sub-tabs."""
    return html.Div(
        style={"padding": "20px 0"},
        children=[
            dcc.Tabs(
                id="kw-sub-tabs",
                value="kw-available",
                style={"borderBottom": f"1px solid {_BORDER}", "marginBottom": "0"},
                children=[
                    dcc.Tab(
                        label="Available Hierarchies",
                        value="kw-available",
                        style=_KW_SUB_TAB,
                        selected_style=_KW_SUB_TAB_SEL,
                        children=[_keywords_available_hierarchies()],
                    ),
                    dcc.Tab(
                        label="Add New Keywords",
                        value="kw-add",
                        style=_KW_SUB_TAB,
                        selected_style=_KW_SUB_TAB_SEL,
                        children=[_keywords_add_new()],
                    ),
                    dcc.Tab(
                        label="Delete Hierarchy",
                        value="kw-delete",
                        style=_KW_SUB_TAB,
                        selected_style=_KW_SUB_TAB_SEL,
                        children=[_keywords_delete_hierarchy()],
                    ),
                ],
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Layout helper — About tab
# ═══════════════════════════════════════════════════════════════════════════════

def _about_content() -> html.Div:
    """
    Structured About page.

    Layout:
      1. Hero banner  — title, subtitle, operation-type pills
      2. Info cards   — three quick-fact tiles (what / who / how)
      3. Body section — four collapsible text sections with accent borders
      4. Data access  — small table of access modes
      5. Footer strip — maintainer credit
    """

    # ── Shared inline helpers ──────────────────────────────────────────────────
    def _tag(label: str) -> html.Span:
        return html.Span(label, className="about-tag")

    def _card(icon, title: str, body: str) -> html.Div:
        # icon can be a string (emoji) or a Dash component (html.I)
        icon_element = html.Span(icon, className="about-card-icon") if isinstance(icon, str) else html.Div(icon, className="about-card-icon")
        return html.Div(
            className="about-card",
            children=[
                icon_element,
                html.P(title, className="about-card-title"),
                html.P(body,  className="about-card-body"),
            ],
        )

    def _section(title: str, body) -> html.Div:
        """body can be a string or a list of Dash components."""
        return html.Div(
            className="about-section",
            children=[
                html.Div(
                    className="about-section-header",
                    children=[
                        html.Div(className="about-section-dot"),
                        html.P(title, className="about-section-title"),
                    ],
                ),
                html.P(body, className="about-section-text")
                if isinstance(body, str)
                else html.Div(body, className="about-section-text"),
            ],
        )

    # ── Access modes table rows ────────────────────────────────────────────────
    access_rows = [
        ("Public API",         "DPO, IPL, PfoR",    "World Bank Data Catalogue", "Public"),
        ("Internal / OUO",     "All operation types", "Internal deployment",     "Authenticated"),
        ("Generative AI demo", "PAG sub-types",      "Project-level text fields","Internal"),
    ]

    access_table = html.Table(
        className="about-access-table",
        children=[
            html.Thead(html.Tr([
                html.Th("Interface"),
                html.Th("Scope"),
                html.Th("Data Source"),
                html.Th("Access Level"),
            ])),
            html.Tbody([
                html.Tr([html.Td(c) for c in row])
                for row in access_rows
            ]),
        ],
    )

    # ── Assemble ───────────────────────────────────────────────────────────────
    return html.Div(
        style={"maxWidth": "980px", "padding": "36px 0 60px"},
        children=[

            # 1 ── Hero ────────────────────────────────────────────────────────
            html.Div(
                className="about-hero",
                children=[
                    # html.Span("WORLD BANK · PIIAG CoP · P179442", className="about-hero-eyebrow"),
                    html.H1("Governance Operations Analytics Tool", className="about-hero-title"),
                    html.P(
                        "GoAT enables targeted, keyword-driven searches across the World Bank's "
                        "three core operation types — providing a real-time operational intelligence "
                        "layer on top of public investment financing data.",
                        className="about-hero-subtitle",
                    ),
                    html.Div(
                        className="about-tag-row",
                        children=[
                            _tag("Development Policy Operations (DPO)"),
                            _tag("Investment Project Lending (IPL)"),
                            _tag("Program for Results (PfoR)"),
                            _tag("Climate Co-Benefits (CCBs)"),
                        ],
                    ),
                ],
            ),

            # 2 ── Info cards ──────────────────────────────────────────────────
            html.Div(
                className="about-cards-grid",
                children=[
                    _card(
                        html.I(className="bi bi-search"),
                        "What GoAT Does",
                        "Maps thematic keyword clusters — PIM, PAM, SOEs, CCBs — "
                        "to Bank operations, surfacing projects that match user-defined "
                        "search hierarchies across PDOs, indicators, and prior actions.",
                    ),
                    _card(
                        html.I(className="bi bi-building"),
                        "Who Maintains It",
                        "Operated by the World Bank's Global Community of Practice for "
                        "Public Infrastructure Investments and Asset Governance (PIIAG), "
                        "project P179442.",
                    ),
                    _card(
                        html.I(className="bi bi-lightning-fill"),
                        "How It Works",
                        "Combines a Databricks Unity Catalog backend with an interactive "
                        "Dash front-end. Users can add or modify keyword hierarchies on "
                        "the fly; results update in real time.",
                    ),
                ],
            ),

            # 3 ── Body sections ───────────────────────────────────────────────
            _section(
                "Keyword Hierarchy Search",
                "Clusters of keywords can be mapped to a thematic hierarchy — for example, "
                "Public Investment Management (PIM), Public Asset Management (PAM), or "
                "State-Owned Enterprises (SOEs). GoAT searches across project objectives, "
                "development-policy prior actions, results indicators, disbursement-linked "
                "indicators, and component descriptions, then tags each project "
                "Yes / No per hierarchy.",
            ),

            _section(
                "Data Coverage & Transparency",
                "GoAT targets Board-Approved operations as well as upstream pipeline "
                "operations (Concept and Appraisal stage). Where data is available through "
                "the World Bank's public Data Catalogue APIs, the tool operates in public "
                "mode. Datasets that are official-use-only are surfaced only via "
                "internally-authenticated deployments.",
            ),

            _section(
                "Generative AI Integration",
                "GoAT progressively demonstrates how generative AI can be applied to "
                "structured project information — for example, all World Bank projects "
                "with a substantive focus on Public Asset Governance or a sub-type "
                "thereof. This layer is currently scoped to internal demonstrations.",
            ),

            _section(
                "Interface Modes",
                [
                    html.Span(
                        "GoAT is available in two deployment modes. "
                        "The table below summarises current access paths.",
                        style={"display": "block", "marginBottom": "12px"},
                    ),
                    access_table,
                ],
            ),

            # 4 ── Footer strip ────────────────────────────────────────────────
            html.Div(
                className="about-footer",
                children=[
                    html.I(className="bi bi-mailbox", style={"fontSize": "20px", "flexShrink": "0"}),
                    html.P(
                        [
                            html.Strong("Maintained by "),
                            "the World Bank PIIAG Global CoP (P179442). "
                            "For questions, access requests, or to contribute a new keyword "
                            "hierarchy, contact the CoP team through the World Bank internal "
                            "collaboration channels.",
                        ],
                        className="about-footer-text",
                    ),
                ],
            ),

            # 5 ── Partner logos and contact ────────────────────────────────────
            html.Div(
                className="about-partners-section",
                children=[
                    html.Div(
                        className="about-partners-content",
                        children=[
                            html.Div(
                                className="about-logos-container",
                                children=[
                                    html.Div(
                                        className="about-logo-item",
                                        children=[
                                            html.Img(
                                                src=app.get_asset_url('The-World-Bank-group-white.png'),
                                                alt="World Bank",
                                                className="about-partner-logo",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="about-logo-item",
                                        children=[
                                            html.Img(
                                                src=app.get_asset_url('Pim-pam_white_logo.png'),
                                                alt="PIM-PAM",
                                                className="about-partner-logo",
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            html.Div(
                                className="about-contact-section",
                                children=[
                                    html.P(
                                        "For any questions, please email:",
                                        className="about-contact-label",
                                    ),
                                    html.A(
                                        "kkaiser@worldbank.org",
                                        href="mailto:kkaiser@worldbank.org",
                                        className="about-contact-email",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Full app layout
# ═══════════════════════════════════════════════════════════════════════════════

app.layout = html.Div(
    style={
        "backgroundColor": _BG_ROOT,
        "minHeight":       "100vh",
        "fontFamily":      "Fira Sans",
    },
    children=[
        # ── Hidden stores ──────────────────────────────────────────────────────
        dcc.Store(id="store-download"),
        # Stores for keywords tab state refresh triggers
        dcc.Store(id="store-kw-refresh", data=0),

        # dcc.Location fires once on page load — triggers init callbacks.
        dcc.Location(id="url", refresh=False),

        # ── Header ─────────────────────────────────────────────────────────────
        html.Div(
            style={
                "backgroundColor": _BG_HEADER,
                "borderBottom":    f"1px solid {_BORDER}",
                "padding":         "14px 32px",
            },
            children=[
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "14px"},
                    children=[
                        html.Img(
                            src=app.get_asset_url('Logo.png'),
                            style={"height": "55px", "width": "55px"},
                        ),
                        html.H1(
                            APP_TITLE,
                            style={
                                "color":         _TEXT_PRI,
                                "fontSize":      "35px",
                                "fontWeight":    "700",
                                "fontFamily":    "Fira Sans",
                                "margin":        "0",
                                "letterSpacing": "-0.01em",
                            },
                        ),
                    ],
                )
            ],
        ),

        # ── Main tab container ─────────────────────────────────────────────────
        html.Div(
            style={"maxWidth": "1440px", "margin": "0 auto", "padding": "0 32px 40px"},
            children=[
                dcc.Tabs(
                    id="main-tabs",
                    value="dashboard",
                    style={"borderBottom": f"1px solid {_BORDER}", "marginBottom": "0"},
                    children=[

                        # ── Tab 1: Dashboard ───────────────────────────────────
                        dcc.Tab(
                            label="Dashboard",
                            value="dashboard",
                            style=_MAIN_TAB,
                            selected_style=_MAIN_TAB_SEL,
                            children=[_dashboard_content()],
                        ),

                        # ── Tab 2: Keywords ────────────────────────────────────
                        dcc.Tab(
                            label="Keywords",
                            value="keywords",
                            style=_MAIN_TAB,
                            selected_style=_MAIN_TAB_SEL,
                            children=[_keywords_tab_content()],
                        ),

                        # ── Tab 3: About ───────────────────────────────────────
                        dcc.Tab(
                            label="About",
                            value="about",
                            style=_MAIN_TAB,
                            selected_style=_MAIN_TAB_SEL,
                            children=[_about_content()],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Callbacks — Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

# ── 1. Init: populate Lending Instrument + Keywords dropdowns on page load ─────

@app.callback(
    Output("dd-lending-instr", "options"),
    Output("dd-lending-instr", "value"),
    Output("dd-keywords",      "options"),
    Input("url",               "href"),
    prevent_initial_call=False,
)
def init_filter_options(href):
    """
    Fires once on page load.  Fetches distinct lending instruments and
    hierarchy names and pre-selects all instruments.
    """
    try:
        instruments, hierarchies = qs.get_filter_options()
        instr_opts = [{"label": v, "value": v} for v in instruments]
        hier_opts  = [{"label": v, "value": v} for v in hierarchies]
        logger.info(
            "[GoAT] Filter options loaded: %d instruments, %d hierarchies",
            len(instruments), len(hierarchies),
        )
        return instr_opts, instruments, hier_opts
    except Exception as exc:
        logger.error("[GoAT] init_filter_options error: %s", exc)
        return [], [], []


# ── 2. Cascade: Region options update when Lending Instrument changes ──────────

@app.callback(
    Output("dd-region", "options"),
    Output("dd-region", "value"),
    Input("dd-lending-instr", "value"),
    prevent_initial_call=False,
)
def cascade_regions(instruments):
    try:
        regions = qs.get_region_options(instruments or [])
        opts    = [{"label": v, "value": v} for v in regions]
        return opts, regions
    except Exception as exc:
        logger.error("[GoAT] cascade_regions error: %s", exc)
        return [], []


# ── 3. Apply Filters ────────────────────────────────────────────────────────────

@app.callback(
    Output("metric-total",         "children"),
    Output("chart-project-status", "figure"),
    Output("chart-lending-instr",  "figure"),
    Output("store-download",       "data"),
    Input("btn-apply",             "n_clicks"),
    State("dd-lending-instr",      "value"),
    State("dd-region",             "value"),
    State("dd-keywords",           "value"),
    State("radio-and-or",          "value"),
    prevent_initial_call=False,
)
def apply_filters(n_clicks, instruments, regions, keywords, and_or):
    """
    Central data-fetch callback.  Runs on page load and on every Apply click.
    """
    instrs = instruments or []
    rgns   = regions     or []
    kws    = keywords    or []
    ao     = and_or      or "AND"

    try:
        total      = qs.get_total_count(instrs, rgns, kws, ao)
        status_df  = qs.get_project_status_data(instrs, rgns, kws, ao)
        lending_df = qs.get_lending_instrument_data(instrs, rgns, kws, ao)
        dl_df      = qs.get_download_data(instrs, rgns, kws, ao)

        logger.info(
            "[GoAT] apply_filters: %d instruments, %d regions, %d keywords, "
            "and_or=%s → %d distinct projects",
            len(instrs), len(rgns), len(kws), ao, total,
        )

        return (
            f"{total:,}",
            build_project_status_chart(status_df),
            build_lending_instrument_chart(lending_df),
            dl_df.to_dict("records"),
        )

    except Exception as exc:
        logger.error("[GoAT] apply_filters error: %s", exc)
        err_fig = build_empty_chart(f"Query failed — {exc}")
        return "—", err_fig, err_fig, []


# ── 4. Render download DataTable from store ────────────────────────────────────

@app.callback(
    Output("tbl-download", "data"),
    Output("tbl-download", "columns"),
    Output("tbl-download", "tooltip_data"),
    Input("store-download", "data"),
)
def render_download_table(records):
    if not records:
        return [], [], []

    df   = pd.DataFrame(records)
    cols = [{"name": c, "id": c, "deletable": False} for c in df.columns]

    tooltip_data = [
        {
            col: {"value": str(row.get(col, "")), "type": "markdown"}
            for col in df.columns
            if isinstance(row.get(col), str) and len(str(row.get(col, ""))) > 50
        }
        for row in records
    ]

    return records, cols, tooltip_data


# ── 5. Export CSV ──────────────────────────────────────────────────────────────

@app.callback(
    Output("download-csv",  "data"),
    Input("btn-export-csv", "n_clicks"),
    State("store-download", "data"),
    prevent_initial_call=True,
)
def export_csv(n_clicks, records):
    if not records:
        return None
    df = pd.DataFrame(records)
    return dcc.send_data_frame(df.to_csv, "goat_projects.csv", index=False)


# ═══════════════════════════════════════════════════════════════════════════════
# Callbacks — Keywords tab
# ═══════════════════════════════════════════════════════════════════════════════

# ── 6a. Load sunburst when Keywords tab is active ──────────────────────────────

@app.callback(
    Output("chart-hierarchy-sunburst", "figure"),
    Input("main-tabs",       "value"),
    Input("kw-sub-tabs",     "value"),
    Input("store-kw-refresh","data"),
    prevent_initial_call=False,
)
def load_sunburst(main_tab, kw_sub_tab, _refresh):
    """
    Fetch the hierarchy table and render the sunburst chart.
    Fires when:
      • the main Keywords tab is selected, OR
      • the Available Hierarchies sub-tab is selected, OR
      • store-kw-refresh increments (after add/delete operations).
    """
    if main_tab != "keywords":
        return no_update

    try:
        df  = qs.get_hierarchy_table()
        fig = build_hierarchy_sunburst(df)
        return fig
    except Exception as exc:
        logger.error("[GoAT] load_sunburst error: %s", exc)
        return build_empty_chart(f"Failed to load hierarchy data: {exc}")


# ── 6b. Load delete dropdown when Keywords tab is active ──────────────────────

@app.callback(
    Output("dd-delete-hierarchy", "options"),
    Output("dd-delete-hierarchy", "value"),
    Input("main-tabs",        "value"),
    Input("store-kw-refresh", "data"),
    prevent_initial_call=False,
)
def load_delete_dropdown(main_tab, _refresh):
    """Populate the Delete Hierarchy dropdown with currently valid hierarchy names."""
    if main_tab != "keywords":
        return no_update, no_update

    try:
        names = qs.get_valid_hierarchy_names()
        opts  = [{"label": n, "value": n} for n in names]
        return opts, None
    except Exception as exc:
        logger.error("[GoAT] load_delete_dropdown error: %s", exc)
        return [], None


# ── 7. Add New Keyword ─────────────────────────────────────────────────────────

@app.callback(
    Output("add-kw-feedback",  "children"),
    Output("store-kw-refresh", "data", allow_duplicate=True),
    Output("input-hier-name",     "value"),
    Output("input-hier-fullname", "value"),
    Output("input-hier-keywords", "value"),
    Input("btn-add-keyword",   "n_clicks"),
    State("input-hier-name",      "value"),
    State("input-hier-fullname",  "value"),
    State("input-hier-keywords",  "value"),
    State("store-kw-refresh",     "data"),
    prevent_initial_call=True,
)
def add_keyword(n_clicks, hier_name, full_name, keywords_csv, refresh_count):
    """
    Run vectorised keyword search over all projects, then INSERT new rows
    into the UC table with Valid_Hierarchy = 'True'.
    Clears form inputs on success and bumps store-kw-refresh to reload charts.
    """
    # ── Validate presence of inputs ────────────────────────────────────────────
    hier_name    = (hier_name    or "").strip()
    full_name    = (full_name    or "").strip()
    keywords_csv = (keywords_csv or "").strip()

    if not hier_name or not full_name or not keywords_csv:
        feedback = html.Div(
            [html.I(className="bi bi-exclamation-circle me-2"), "All fields are required."],
            style=_ALERT_ERROR,
        )
        return feedback, no_update, no_update, no_update, no_update

    try:
        success, message = qs.add_new_hierarchy(hier_name, full_name, keywords_csv)

        if success:
            feedback = html.Div(
                [html.I(className="bi bi-check-circle me-2"), message],
                style=_ALERT_SUCCESS,
            )
            new_refresh = (refresh_count or 0) + 1
            # Clear inputs on success
            return feedback, new_refresh, "", "", ""
        else:
            feedback = html.Div(
                [html.I(className="bi bi-exclamation-circle me-2"), message],
                style=_ALERT_ERROR,
            )
            return feedback, no_update, no_update, no_update, no_update

    except Exception as exc:
        logger.exception("[GoAT] add_keyword callback error: %s", exc)
        feedback = html.Div(
            [html.I(className="bi bi-exclamation-circle me-2"), f"Unexpected error: {exc}"],
            style=_ALERT_ERROR,
        )
        return feedback, no_update, no_update, no_update, no_update


# ── 8. Delete Hierarchy ────────────────────────────────────────────────────────

@app.callback(
    Output("delete-hier-feedback", "children"),
    Output("store-kw-refresh",     "data", allow_duplicate=True),
    Input("btn-delete-hierarchy",  "n_clicks"),
    State("dd-delete-hierarchy",   "value"),
    State("store-kw-refresh",      "data"),
    prevent_initial_call=True,
)
def delete_hierarchy_callback(n_clicks, hierarchy_name, refresh_count):
    """
    Soft-delete: set Valid_Hierarchy = 'False' for the selected hierarchy.
    Bumps store-kw-refresh so the sunburst and delete dropdown reload.
    """
    if not hierarchy_name:
        feedback = html.Div(
            [html.I(className="bi bi-exclamation-circle me-2"), "Please select a hierarchy to delete."],
            style=_ALERT_ERROR,
        )
        return feedback, no_update

    try:
        success, message = qs.delete_hierarchy(hierarchy_name)

        if success:
            feedback = html.Div(
                [html.I(className="bi bi-check-circle me-2"), message],
                style=_ALERT_SUCCESS,
            )
            new_refresh = (refresh_count or 0) + 1
            return feedback, new_refresh
        else:
            feedback = html.Div(
                [html.I(className="bi bi-exclamation-circle me-2"), message],
                style=_ALERT_ERROR,
            )
            return feedback, no_update

    except Exception as exc:
        logger.exception("[GoAT] delete_hierarchy callback error: %s", exc)
        feedback = html.Div(
            [html.I(className="bi bi-exclamation-circle me-2"), f"Unexpected error: {exc}"],
            style=_ALERT_ERROR,
        )
        return feedback, no_update


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)


#Working well now