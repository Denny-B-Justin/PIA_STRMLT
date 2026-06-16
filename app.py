"""
GoAT — Governance Operations Analytics Tool
Dash application entry point.

Architecture
------------
  constants.py  ← app config, column names, chart defaults
  queries.py    ← QueryService (Databricks auth + TTL cache + SQL builders)
  utils.py      ← Plotly figure constructors
  app.py        ← Dash layout + callbacks (this file)

Callback flow
-------------
  1. init_filter_options   — page load → populate Lending Instrument + Keywords dropdowns
  2. cascade_regions       — Lending Instrument change → update Region options
  3. apply_filters         — "Apply Filters" click → fetch all chart / table data
  4. render_download_table — store-download change → populate DataTable + tooltips
  5. export_csv            — "Export CSV" click → send CSV via dcc.Download
"""

import logging
import pandas as pd

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc

from goat_src.constants import ABOUT_TEXT, APP_TITLE
from goat_src.queries import QueryService
from goat_src.utils import (
    build_project_status_chart,
    build_lending_instrument_chart,
    build_empty_chart,
)

# ── Logging ────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── App initialisation ─────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        # Bootstrap Icons for the funnel icon on the Apply button
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
# Style constants  (avoids repeating dicts; keep in sync with assets/goat.css)
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
    "color":          _TEXT_MUTED,
    "fontSize":       "11px",
    # "fontWeight":     "600",
    "letterSpacing":  "0.06em",
    "marginBottom":   "6px",
    "display":        "block",
}

_DD_STYLE = {"marginBottom": "20px"}

_MAIN_TAB  = {
    "color":            _TEXT_MUTED,
    "backgroundColor":  _BG_ROOT,
    "border":           "none",
    "borderBottom":     f"2px solid transparent",
    "padding":          "14px 24px",
    "fontFamily":       "Fira Sans",
    "fontSize":         "15px",
}
_MAIN_TAB_SEL = {
    **_MAIN_TAB,
    "color":        _ACCENT,
    "borderBottom": f"2px solid {_ACCENT}",
    "fontWeight":   "600",
}

_CHART_TAB  = {
    "color":            _TEXT_MUTED,
    "backgroundColor":  _BG_CARD,
    "border":           "none",
    "borderBottom":     f"2px solid transparent",
    "padding":          "10px 18px",
    "fontFamily":       "Fira Sans",
    "fontSize":         "13px",
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
    "border":          f"1px solid #3a3a3a",
    "fontSize":        "12px",
    "padding":         "8px 12px",
    "textAlign":       "left",
    "textTransform":   "uppercase",
    "letterSpacing":   "0.04em",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Layout helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _filter_sidebar() -> html.Div:
    """Left-hand sidebar with all Dashboard filter controls."""
    return html.Div(
        style=_SIDEBAR_STYLE,
        children=[

            # ── Lending Instrument ─────────────────────────────────────────────
            html.Label("Select Lending Instrument", style=_FILTER_LABEL),
            dcc.Dropdown(
                id="dd-lending-instr",
                multi=True,
                placeholder="Loading…",
                style=_DD_STYLE,
                optionHeight=40,
            ),

            # ── Region ─────────────────────────────────────────────────────────
            html.Label("Select Region", style=_FILTER_LABEL),
            dcc.Dropdown(
                id="dd-region",
                multi=True,
                placeholder="Loading…",
                style=_DD_STYLE,
                optionHeight=40,
            ),

            # ── Keywords ───────────────────────────────────────────────────────
            html.Label("Filter by Keywords", style=_FILTER_LABEL),
            dcc.Dropdown(
                id="dd-keywords",
                multi=True,
                placeholder="Choose hierarchy",
                style=_DD_STYLE,
            ),

            # ── AND / OR ───────────────────────────────────────────────────────
            html.Label("Keyword filter logic", style=_FILTER_LABEL),
            dcc.RadioItems(
                id="radio-and-or",
                options=[
                    {"label": "  AND  — project must match all selected hierarchies", "value": "AND"},
                    {"label": "  OR   — project must match any selected hierarchy",   "value": "OR"},
                ],
                value="AND",
                labelStyle={
                    "display":     "block",
                    "color":       _TEXT_SEC,
                    "fontSize":    "12px",
                    "marginBottom": "6px",
                    "cursor":      "pointer",
                },
                inputStyle={"marginRight": "6px", "accentColor": _ACCENT},
                style={"marginBottom": "24px"},
            ),

            # ── Apply Button ───────────────────────────────────────────────────
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
            # Header row: title + export button
            html.Div(
                style={
                    "display":         "flex",
                    "justifyContent":  "space-between",
                    "alignItems":      "center",
                    "marginBottom":    "14px",
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

            # Hidden dcc.Download target
            dcc.Download(id="download-csv"),

            # DataTable
            dash_table.DataTable(
                id="tbl-download",
                page_size=15,
                filter_action="native",
                sort_action="native",
                style_table={"overflowX": "auto"},
                style_cell=_TABLE_CELL,
                style_header=_TABLE_HEADER,
                style_data_conditional=[
                    {
                        "if":              {"row_index": "odd"},
                        "backgroundColor": "#222222",
                    }
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

            # ── Left: filters ──────────────────────────────────────────────────
            html.Div(
                _filter_sidebar(),
                style={"width": "300px", "flexShrink": "0"},
            ),

            # ── Right: metric + charts ─────────────────────────────────────────
            html.Div(
                style={"flex": "1", "minWidth": "0"},
                children=[

                    # Total projects metric
                    html.Div(
                        style={"marginBottom": "22px"},
                        children=[
                            html.Span(
                                "Total Number of Projects",
                                style={
                                    "color":    _TEXT_MUTED,
                                    "fontSize": "13px",
                                    "display":  "block",
                                },
                            ),
                            html.H2(
                                id="metric-total",
                                children="—",
                                style={
                                    "color":      _TEXT_PRI,
                                    "fontSize":   "44px",
                                    # "fontWeight": "700",
                                    "margin":     "4px 0 0",
                                    "lineHeight": "1",
                                    "fontFamily": "Fira Sans",
                                },
                            ),
                        ],
                    ),

                    # Chart sub-tabs wrapped in a loading spinner
                    dcc.Loading(
                        type="circle",
                        color=_ACCENT,
                        children=dcc.Tabs(
                            id="chart-tabs",
                            value="tab-status",
                            style={
                                "borderBottom":  f"1px solid {_BORDER}",
                                "marginBottom":  "0",
                            },
                            children=[

                                # ── Sub-tab A: Project Status ──────────────────
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

                                # ── Sub-tab B: Lending Instrument ──────────────
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

                                # ── Sub-tab C: Download Data ───────────────────
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
        # store-download holds project-level records for the DataTable + CSV export.
        dcc.Store(id="store-download"),

        # dcc.Location fires once on page load — used to trigger init callbacks.
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
                            src="/assets/Logo.png",
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
                    style={
                        "borderBottom": f"1px solid {_BORDER}",
                        "marginBottom": "0",
                    },
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
                            children=[
                                html.Div(
                                    style={
                                        "display":        "flex",
                                        "flexDirection":  "column",
                                        "alignItems":     "center",
                                        "justifyContent": "center",
                                        "padding":        "100px 0",
                                        "gap":            "16px",
                                    },
                                    children=[
                                        html.Span("🚧", style={"fontSize": "52px"}),
                                        html.H3(
                                            "Working on it…",
                                            style={"color": _TEXT_SEC, "margin": "0"},
                                        ),
                                        html.P(
                                            "Keyword hierarchy management will be available in an upcoming release.",
                                            style={"color": _TEXT_MUTED, "fontSize": "14px", "margin": "0"},
                                        ),
                                    ],
                                )
                            ],
                        ),

                        # ── Tab 3: About ───────────────────────────────────────
                        dcc.Tab(
                            label="About",
                            value="about",
                            style=_MAIN_TAB,
                            selected_style=_MAIN_TAB_SEL,
                            children=[
                                html.Div(
                                    style={
                                        "maxWidth":    "820px",
                                        "padding":     "40px 0",
                                        "color":       _TEXT_SEC,
                                        "lineHeight":  "1.75",
                                        "fontSize":    "15px",
                                    },
                                    children=[
                                        html.H2(
                                            "About",
                                            style={"color": _TEXT_PRI, "marginBottom": "20px"},
                                        ),
                                        # ── Replace with the full GoAT description ──
                                        html.P(ABOUT_TEXT
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Callbacks
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
    Fires once on page load (triggered by dcc.Location href becoming available).
    Fetches distinct lending instruments and hierarchy names from the UC table
    and pre-selects all instruments so the initial view shows all data.
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


# ── 2. Cascade: Region options update when Lending Instrument selection changes ─

@app.callback(
    Output("dd-region", "options"),
    Output("dd-region", "value"),
    Input("dd-lending-instr", "value"),
    prevent_initial_call=False,
)
def cascade_regions(instruments):
    """
    Re-queries distinct RGN_NAME values scoped to the currently selected
    lending instruments. Pre-selects all returned regions.
    """
    try:
        regions = qs.get_region_options(instruments or [])
        opts    = [{"label": v, "value": v} for v in regions]
        return opts, regions
    except Exception as exc:
        logger.error("[GoAT] cascade_regions error: %s", exc)
        return [], []


# ── 3. Apply Filters: execute all queries on button click ──────────────────────

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
    Central data-fetch callback.  Triggered on the initial page render
    (prevent_initial_call=False) and on every "Apply Filters" button click.

    On initial render all State values are None (no user selection yet), which
    means the WHERE clause is empty and all data is returned — matching the
    "show everything by default" behaviour of the original Streamlit app.
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
            "[GoAT] apply_filters: instruments=%d regions=%d keywords=%d "
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
    """Populate the DataTable and per-cell tooltips from the download store."""
    if not records:
        return [], [], []

    df   = pd.DataFrame(records)
    cols = [{"name": c, "id": c, "deletable": False} for c in df.columns]

    # Markdown tooltips for cells whose text is truncated (> 50 chars)
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
    Output("download-csv",   "data"),
    Input("btn-export-csv",  "n_clicks"),
    State("store-download",  "data"),
    prevent_initial_call=True,
)
def export_csv(n_clicks, records):
    """Send the current Download store contents as a CSV file download."""
    if not records:
        return None
    df = pd.DataFrame(records)
    return dcc.send_data_frame(df.to_csv, "goat_projects.csv", index=False)


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)