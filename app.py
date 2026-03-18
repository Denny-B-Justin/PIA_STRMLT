"""
app.py
Zambia Health Access – Facility Placement Optimisation Dashboard
Trial version: data read from CSV files; no Databricks connection required.

Map: Plotly go.Scattermap with open-street-map tiles (no token, no iframe).
Font: Inter throughout the UI; Space Mono only for coordinate values.

Run:
    pip install dash dash-bootstrap-components pandas flask plotly
    python app.py
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional
from dash import dcc, html, Dash, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from queries import QueryService
from server import server
from utils import (
    build_map_figure,
    get_new_facility_rows,
    get_access_pct,
    format_delta,
    build_accessibility_chart,
    get_recommended_table_rows,
)
from constants import BASELINE_ACCESS_PCT, MAX_NEW_FACILITIES

# ── Dash app ──────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        # Inter — clean geometric sans-serif matching the Figma design
        # Space Mono — kept for coordinate values only
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800"
        "&family=Space+Mono:wght@400;700&display=swap",
    ],
)

db = QueryService.get_instance()


# ── Design tokens ─────────────────────────────────────────────────────────────

BG_PAGE    = "#F8FAFC"
BG_HEADER  = "#0B1120"
BG_CARD    = "#FFFFFF"
BORDER     = "#E2E8F0"
BORDER_HVR = "#CBD5E1"
TEXT_HI    = "#0F172A"
TEXT_MID   = "#475569"
TEXT_LO    = "#94A3B8"

ACC_INDIGO = "#4F46E5"     # primary — chart, active stats
ACC_GREEN  = "#16A34A"     # proposed facility markers
ACC_RED    = "#DC2626"     # existing facility markers

FONT_BODY  = "'Inter', sans-serif"
FONT_MONO  = "'Space Mono', monospace"

HEADER_H   = 68            # px — controls split viewport height calc

# ── Style dictionaries ────────────────────────────────────────────────────────

PAGE_STYLE = {
    "backgroundColor": BG_PAGE,
    "height": "100vh",
    "overflow": "hidden",
    "fontFamily": FONT_BODY,
    "color": TEXT_HI,
    "margin": "0",
    "padding": "0",
}

HEADER_STYLE = {
    "backgroundColor": BG_CARD,
    "borderBottom": f"1px solid {BORDER}",
    "padding": "0 28px",
    "height": f"{HEADER_H}px",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "space-between",
    "flexShrink": "0",
}

BADGE_STYLE = {
    "display": "inline-block",
    "background": "rgba(249,115,22,0.10)",
    "border": "1px solid rgba(249,115,22,0.32)",
    "borderRadius": "5px",
    "padding": "2px 8px",
    "fontFamily": FONT_BODY,
    "fontSize": "0.57rem",
    "color": "#EA580C",
    "letterSpacing": "1.2px",
    "textTransform": "uppercase",
    "marginBottom": "4px",
}

LEGEND_PILL_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "7px",
    "background": BG_PAGE,
    "border": f"1px solid {BORDER}",
    "borderRadius": "99px",
    "padding": "5px 13px",
    "fontSize": "0.78rem",
    "fontWeight": "500",
    "color": TEXT_MID,
    "whiteSpace": "nowrap",
}

LEGEND_DOT_BASE = {
    "display": "inline-block",
    "width": "9px",
    "height": "9px",
    "borderRadius": "50%",
    "flexShrink": "0",
}

FILTER_BAR_STYLE = {
    "backgroundColor": BG_CARD,
    "borderBottom": f"1px solid {BORDER}",
    "padding": "14px 24px",
    "display": "flex",
    "alignItems": "flex-end",
    "gap": "12px",
    "flexWrap": "wrap",
    "flexShrink": "0",
}

FILTER_FIELD_LABEL = {
    "fontSize": "0.68rem",
    "fontWeight": "500",
    "color": TEXT_MID,
    "display": "block",
    "marginBottom": "4px",
    "letterSpacing": "0.1px",
}

FILTER_CHIP_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "8px",
    "background": BG_CARD,
    "border": f"1px solid {BORDER}",
    "borderRadius": "8px",
    "padding": "7px 12px",
    "fontSize": "0.84rem",
    "fontWeight": "500",
    "color": TEXT_HI,
    "cursor": "default",
    "userSelect": "none",
    "whiteSpace": "nowrap",
    "minWidth": "130px",
}

CARD_STYLE = {
    "backgroundColor": BG_CARD,
    "border": f"1px solid {BORDER}",
    "borderRadius": "10px",
    "padding": "20px 22px",
    "marginBottom": "12px",
}

SECTION_TITLE_STYLE = {
    "fontWeight": "700",
    "fontSize": "0.72rem",
    "letterSpacing": "1.1px",
    "textTransform": "uppercase",
    "color": TEXT_HI,
    "marginBottom": "16px",
    "fontFamily": FONT_BODY,
}

BIG_NUM_STYLE = {
    "fontFamily": FONT_BODY,
    "fontSize": "2.4rem",
    "fontWeight": "800",
    "lineHeight": "1",
    "color": TEXT_HI,
    "letterSpacing": "-0.5px",
}

BIG_NUM_LABEL_STYLE = {
    "fontSize": "0.75rem",
    "fontWeight": "400",
    "color": TEXT_MID,
    "marginTop": "6px",
    "lineHeight": "1.5",
    "maxWidth": "200px",
}

SLIDER_LABEL_STYLE = {
    "fontSize": "0.72rem",
    "fontWeight": "500",
    "color": TEXT_MID,
    "letterSpacing": "0.1px",
    "marginBottom": "8px",
}

# ── +/- stepper control ───────────────────────────────────────────────────────

STEPPER_WRAP_STYLE = {
    "display": "flex",
    "alignItems": "stretch",
    "border": f"1px solid {BORDER}",
    "borderRadius": "8px",
    "overflow": "hidden",
    "height": "46px",
}

STEPPER_VALUE_STYLE = {
    "flex": "1",
    "border": "none",
    "outline": "none",
    "padding": "0 14px",
    "fontFamily": FONT_BODY,
    "fontSize": "1.05rem",
    "fontWeight": "500",
    "color": TEXT_HI,
    "backgroundColor": BG_CARD,
    "minWidth": "0",
    "lineHeight": "46px",
}

STEPPER_BTN_GROUP_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "borderLeft": f"1px solid {BORDER}",
    "flexShrink": "0",
}

STEPPER_BTN_STYLE = {
    "width": "36px",
    "flex": "1",
    "border": "none",
    "borderRadius": "0",
    "background": BG_CARD,
    "color": TEXT_MID,
    "fontSize": "0.75rem",
    "fontWeight": "700",
    "cursor": "pointer",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "userSelect": "none",
    "transition": "background 0.12s, color 0.12s",
    "padding": "0",
    "lineHeight": "1",
}

VIEW_BTN_STYLE = {
    "display": "block",
    "width": "100%",
    "padding": "12px 0",
    "marginTop": "18px",
    "background": ACC_INDIGO,
    "color": "#FFFFFF",
    "border": "none",
    "borderRadius": "8px",
    "fontFamily": FONT_BODY,
    "fontSize": "0.88rem",
    "fontWeight": "600",
    "letterSpacing": "0.2px",
    "cursor": "pointer",
    "textAlign": "center",
    "transition": "background 0.15s",
}

STAT_PAIR_STYLE = {
    "display": "flex",
    "gap": "36px",
    "flexWrap": "wrap",
    "alignItems": "flex-start",
}

TABLE_WRAP_STYLE = {
    "overflowX": "auto",
    "borderRadius": "8px",
    "border": f"1px solid {BORDER}",
}

TH_STYLE = {
    "fontFamily": FONT_MONO,
    "fontSize": "0.6rem",
    "fontWeight": "700",
    "color": TEXT_MID,
    "letterSpacing": "1px",
    "textTransform": "uppercase",
    "padding": "9px 12px",
    "backgroundColor": BG_PAGE,
    "borderBottom": f"1px solid {BORDER}",
    "whiteSpace": "nowrap",
    "textAlign": "left",
}

TD_STYLE = {
    "fontFamily": FONT_MONO,
    "fontSize": "0.77rem",
    "color": TEXT_HI,
    "padding": "10px 12px",
    "borderBottom": f"1px solid {BORDER}",
    "whiteSpace": "nowrap",
}

TD_ARROW_STYLE = {
    **TD_STYLE,
    "color": ACC_INDIGO,
    "fontWeight": "700",
    "fontSize": "0.9rem",
    "padding": "10px 8px 10px 4px",
}

FOOTER_STYLE = {
    "fontFamily": FONT_BODY,
    "fontSize": "0.57rem",
    "fontWeight": "400",
    "color": TEXT_LO,
    "letterSpacing": "0.5px",
    "textAlign": "center",
    "padding": "10px 0 4px",
}


# ── Component helpers ─────────────────────────────────────────────────────────

def section_title(text: str) -> html.Div:
    return html.Div(text, style=SECTION_TITLE_STYLE)


def legend_dot(color: str, border_color: Optional[str] = None) -> html.Span:
    style = {**LEGEND_DOT_BASE, "backgroundColor": color}
    if border_color:
        style["border"] = f"2px solid {border_color}"
        style["backgroundColor"] = BG_PAGE   # matches header background
    return html.Span(style=style)


def filter_chip(label: str, value: str) -> html.Div:
    """Static non-interactive filter chip matching the Figma dropdown style."""
    return html.Div(
        style={"display": "flex", "flexDirection": "column"},
        children=[
            html.Span(label, style=FILTER_FIELD_LABEL),
            html.Div(
                style=FILTER_CHIP_STYLE,
                children=[
                    html.Span(value, style={"flex": "1"}),
                    html.Span(
                        "▾",
                        style={"color": TEXT_LO, "fontSize": "0.72rem",
                               "flexShrink": "0"},
                    ),
                ],
            ),
        ],
    )


def _empty_figure(height: int = 195) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        height=height,
        margin=dict(l=48, r=12, t=10, b=44),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def build_recommended_table(rows: List[Dict]) -> html.Div:
    """HTML table for the Recommended Locations card."""
    if not rows:
        return html.Div(
            "Move the + button above to reveal optimal new facility locations.",
            style={
                "color": TEXT_LO, "fontSize": "0.82rem",
                "padding": "20px 0", "textAlign": "center",
                "fontFamily": FONT_BODY,
            },
        )

    thead = html.Thead(html.Tr([
        html.Th("NO",                        style=TH_STYLE),
        html.Th("LONGITUDE",                 style=TH_STYLE),
        html.Th("LATITUDE",                  style=TH_STYLE),
        html.Th("N OF NEW PEOPLE WITHIN 10KM", style={**TH_STYLE, "textAlign": "right"}),
        html.Th("",                          style={**TH_STYLE, "width": "30px"}),
    ]))

    tbody_rows = []
    for i, row in enumerate(rows):
        is_last = (i == len(rows) - 1)
        row_td_style = {
            **TD_STYLE,
            "borderBottom": "none" if is_last else f"1px solid {BORDER}",
        }
        row_arrow_style = {
            **TD_ARROW_STYLE,
            "borderBottom": "none" if is_last else f"1px solid {BORDER}",
        }
        tbody_rows.append(html.Tr([
            html.Td(str(row["no"]),          style=row_td_style),
            html.Td(row["lon_dms"],           style=row_td_style),
            html.Td(row["lat_dms"],           style=row_td_style),
            html.Td(
                f"{row['new_people']:,}",
                style={**row_td_style, "textAlign": "right"},
            ),
            html.Td("→", style=row_arrow_style),
        ]))

    return html.Div(
        style=TABLE_WRAP_STYLE,
        children=html.Table(
            [thead, html.Tbody(tbody_rows)],
            style={"width": "100%", "borderCollapse": "collapse"},
        ),
    )


# ── Layout ────────────────────────────────────────────────────────────────────

app.layout = html.Div(
    style=PAGE_STYLE,
    children=[

        # ── Data stores ───────────────────────────────────────────────────────
        dcc.Store(id="store-existing-facilities"),
        dcc.Store(id="store-accessibility-results"),
        dcc.Store(id="store-n-new",  data=0),   # current stepper value
        dcc.Store(id="store-n-view", data=0),   # value committed by "View locations"

        # ── Header ────────────────────────────────────────────────────────────
        html.Div(
            style=HEADER_STYLE,
            children=[

                # Left: brand
                html.Div([
                    html.Div("TRIAL  ·  CSV DATA MODE", style=BADGE_STYLE),
                    html.Div(
                        "Zambia Health Access",
                        style={
                            "fontFamily": FONT_BODY,
                            "fontSize": "1.2rem",
                            "fontWeight": "700",
                            "color": TEXT_HI,
                            "letterSpacing": "-0.3px",
                            "lineHeight": "1.2",
                        },
                    ),
                    html.Div(
                        "Facility placement optimisation & population accessibility",
                        style={
                            "fontSize": "0.74rem",
                            "fontWeight": "400",
                            "color": TEXT_MID,
                            "marginTop": "3px",
                        },
                    ),
                ]),

                # Right: map legend
                html.Div(
                    style={"display": "flex", "gap": "10px",
                           "alignItems": "center"},
                    children=[
                        html.Div(style=LEGEND_PILL_STYLE, children=[
                            legend_dot(ACC_RED),
                            html.Span("Existing facility"),
                        ]),
                        html.Div(style=LEGEND_PILL_STYLE, children=[
                            legend_dot("#FFFFFF", border_color=ACC_GREEN),
                            html.Span("Proposed facility"),
                        ]),
                    ],
                ),
            ],
        ),

        # ── Main split ────────────────────────────────────────────────────────
        html.Div(
            style={
                "display": "flex",
                "height": f"calc(100vh - {HEADER_H}px)",
                "overflow": "hidden",
            },
            children=[

                # ── LEFT: Map ────────────────────────────────────────────────
                html.Div(
                    style={
                        "flex": "0 0 52%",
                        "height": "100%",
                        "borderRight": f"1px solid {BORDER}",
                        "overflow": "hidden",
                        "backgroundColor": "#EEF0F4",
                    },
                    children=dcc.Graph(
                        id="map-graph",
                        config={
                            "displayModeBar": False,
                            "scrollZoom": True,
                        },
                        style={"width": "100%", "height": "100%"},
                    ),
                ),

                # ── RIGHT: Stats pane ─────────────────────────────────────────
                html.Div(
                    style={
                        "flex": "1",
                        "height": "100%",
                        "display": "flex",
                        "flexDirection": "column",
                        "backgroundColor": BG_PAGE,
                        "overflow": "hidden",
                    },
                    children=[

                        # Static filter bar
                        html.Div(
                            style=FILTER_BAR_STYLE,
                            children=[
                                filter_chip("Type of facility",  "Hospitals and Clinics"),
                                filter_chip("Travel mode",       "Driving"),
                                filter_chip("Measure",           "Distance"),
                                filter_chip("Distance value",    "10 km"),
                            ],
                        ),

                        # Scrollable content
                        html.Div(
                            style={
                                "flex": "1",
                                "overflowY": "auto",
                                "padding": "16px 22px",
                            },
                            children=[

                                # ── Current Accessibility ─────────────────────
                                html.Div(
                                    style=CARD_STYLE,
                                    children=[
                                        section_title("Current Accessibility"),
                                        html.Div(
                                            style=STAT_PAIR_STYLE,
                                            children=[
                                                html.Div([
                                                    html.Div(
                                                        id="ca-total-fac",
                                                        style=BIG_NUM_STYLE,
                                                    ),
                                                    html.Div(
                                                        "Number of health facilities",
                                                        style=BIG_NUM_LABEL_STYLE,
                                                    ),
                                                ]),
                                                html.Div([
                                                    html.Div(
                                                        id="ca-access-pct",
                                                        style={
                                                            **BIG_NUM_STYLE,
                                                            "color": ACC_INDIGO,
                                                        },
                                                    ),
                                                    html.Div(
                                                        [
                                                            "Percentage of population with access to ",
                                                            html.I("all"),
                                                            " health facilities within ",
                                                            html.U("10 km"),
                                                            " travel ",
                                                            html.I("distance"),
                                                            " by driving",
                                                        ],
                                                        style=BIG_NUM_LABEL_STYLE,
                                                    ),
                                                ]),
                                            ],
                                        ),
                                    ],
                                ),

                                # ── Optimization Model ────────────────────────
                                html.Div(
                                    style=CARD_STYLE,
                                    children=[
                                        section_title("Optimization Model"),

                                        # ── Two-column inner layout ───────────
                                        html.Div(
                                            style={
                                                "display": "flex",
                                                "gap": "20px",
                                                "alignItems": "flex-start",
                                            },
                                            children=[

                                                # LEFT COL: steppers + button + stats
                                                html.Div(
                                                    style={"flex": "0 0 200px"},
                                                    children=[

                                                        # Field 1: Number of new facilities
                                                        html.Div(
                                                            style={"marginBottom": "12px"},
                                                            children=[
                                                                html.Div(
                                                                    "Number of new facilities",
                                                                    style=SLIDER_LABEL_STYLE,
                                                                ),
                                                                html.Div(
                                                                    style=STEPPER_WRAP_STYLE,
                                                                    children=[
                                                                        html.Div(
                                                                            id="stepper-display",
                                                                            style=STEPPER_VALUE_STYLE,
                                                                            children="0",
                                                                        ),
                                                                        html.Div(
                                                                            style=STEPPER_BTN_GROUP_STYLE,
                                                                            children=[
                                                                                html.Button("+", id="btn-increase",  n_clicks=0, style=STEPPER_BTN_STYLE),
                                                                                html.Div(style={"height": "1px", "background": BORDER, "flexShrink": "0"}),
                                                                                html.Button("−", id="btn-decrease",  n_clicks=0, style=STEPPER_BTN_STYLE),
                                                                            ],
                                                                        ),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),

                                                        # Field 2: Optimized Accessibility %
                                                        html.Div(
                                                            style={"marginBottom": "0"},
                                                            children=[
                                                                html.Div(
                                                                    "Optimized Accessibility %",
                                                                    style=SLIDER_LABEL_STYLE,
                                                                ),
                                                                html.Div(
                                                                    style=STEPPER_WRAP_STYLE,
                                                                    children=[
                                                                        html.Div(
                                                                            id="stepper-access-display",
                                                                            style={
                                                                                **STEPPER_VALUE_STYLE,
                                                                                "color": ACC_INDIGO,
                                                                                "fontWeight": "600",
                                                                            },
                                                                            children="79.31%",
                                                                        ),
                                                                        html.Div(
                                                                            style=STEPPER_BTN_GROUP_STYLE,
                                                                            children=[
                                                                                html.Button("+", id="btn-increase-2", n_clicks=0, style=STEPPER_BTN_STYLE),
                                                                                html.Div(style={"height": "1px", "background": BORDER, "flexShrink": "0"}),
                                                                                html.Button("−", id="btn-decrease-2", n_clicks=0, style=STEPPER_BTN_STYLE),
                                                                            ],
                                                                        ),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),

                                                        # View locations button
                                                        html.Button(
                                                            "View locations",
                                                            id="btn-view-locations",
                                                            n_clicks=0,
                                                            style=VIEW_BTN_STYLE,
                                                        ),

                                                        # Stats: n_new + access %
                                                        html.Div(
                                                            style={"marginTop": "16px"},
                                                            children=[
                                                                html.Div(
                                                                    id="om-n-new",
                                                                    style={**BIG_NUM_STYLE, "fontSize": "1.65rem"},
                                                                ),
                                                                html.Div(
                                                                    "New facilities added",
                                                                    style={**BIG_NUM_LABEL_STYLE, "marginBottom": "10px"},
                                                                ),
                                                                html.Div(
                                                                    id="om-access-pct",
                                                                    style={**BIG_NUM_STYLE, "fontSize": "1.65rem", "color": ACC_INDIGO},
                                                                ),
                                                                html.Div(
                                                                    id="om-delta-label",
                                                                    style=BIG_NUM_LABEL_STYLE,
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                ),

                                                # RIGHT COL: accessibility curve
                                                html.Div(
                                                    style={"flex": "1", "minWidth": "0"},
                                                    children=[
                                                        dcc.Graph(
                                                            id="accessibility-chart",
                                                            config={"displayModeBar": False},
                                                            style={"marginLeft": "-8px"},
                                                        ),
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),

                                # ── Recommended Locations ─────────────────────
                                html.Div(
                                    style={**CARD_STYLE, "marginBottom": "4px"},
                                    children=[
                                        section_title("Recommended Locations"),
                                        html.Div(id="recommended-table"),
                                    ],
                                ),

                                # Footer
                                html.Div(
                                    "ZAMBIA · HEALTH FACILITY ACCESSIBILITY  "
                                    "|  POPULATION: WORLDPOP 2025 · FACILITIES: OPENSTREETMAP  "
                                    "|  OPTIMISATION: ILP / GUROBI  "
                                    "|  DATA: SAMPLE CSV (TRIAL MODE)",
                                    style=FOOTER_STYLE,
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("store-existing-facilities", "data"),
    Input("store-existing-facilities", "data"),
)
def fetch_existing_facilities_once(data):
    """Load existing facilities from CSV on first render; never re-query."""
    if data is None:
        df = db.get_existing_facilities()
        return df.to_dict("records")
    return no_update


@app.callback(
    Output("store-accessibility-results", "data"),
    Input("store-accessibility-results", "data"),
)
def fetch_accessibility_results_once(data):
    """Load optimisation results from CSV on first render; never re-query."""
    if data is None:
        df = db.get_accessibility_results()
        return df.to_dict("records")
    return no_update


@app.callback(
    Output("store-n-new",           "data"),
    Output("stepper-display",       "children"),
    Output("stepper-access-display","children"),
    Input("btn-increase",   "n_clicks"),
    Input("btn-decrease",   "n_clicks"),
    Input("btn-increase-2", "n_clicks"),
    Input("btn-decrease-2", "n_clicks"),
    State("store-n-new", "data"),
    State("store-accessibility-results", "data"),
    State("store-existing-facilities", "data"),
)
def update_stepper(inc, dec, inc2, dec2, current, results_records, existing_records):
    """
    Handle all four +/- button clicks.
    Both field-1 (+/-) and field-2 (+/-) step the same n_new counter.
    The accessibility display in field-2 is read-only and auto-updates.
    """
    from dash import ctx
    triggered = ctx.triggered_id

    n = current if current is not None else 0

    if triggered in ("btn-increase", "btn-increase-2"):
        n = min(n + 1, MAX_NEW_FACILITIES)
    elif triggered in ("btn-decrease", "btn-decrease-2"):
        n = max(n - 1, 0)

    # Compute the access % for the new n
    if results_records and existing_records:
        results_df  = pd.DataFrame(results_records)
        n_existing  = len(pd.DataFrame(existing_records))
        access_pct  = get_access_pct(results_df, n, n_existing)
        access_text = f"{access_pct:.2f}%"
    else:
        access_text = f"{BASELINE_ACCESS_PCT:.2f}%"

    return n, str(n), access_text


@app.callback(
    Output("store-n-view", "data"),
    Input("btn-view-locations", "n_clicks"),
    State("store-n-new", "data"),
    prevent_initial_call=True,
)
def commit_view(n_clicks, n_new):
    """Copy the current stepper value into store-n-view when 'View locations' is clicked."""
    return n_new or 0


@app.callback(
    Output("map-graph", "figure"),
    Input("store-n-view", "data"),
    Input("store-existing-facilities", "data"),
    Input("store-accessibility-results", "data"),
)
def update_map(n_view, existing_records, results_records):
    """
    Rebuild the map only when 'View locations' is clicked or data first loads.
    Proposed-facility markers reflect the n committed by the button, not the
    live stepper value — so panning/zooming is never interrupted mid-edit.
    """
    if existing_records is None or results_records is None:
        return _empty_figure(500)

    n_view      = n_view or 0
    existing_df = pd.DataFrame(existing_records)
    results_df  = pd.DataFrame(results_records)
    new_df      = get_new_facility_rows(results_df, n_view)
    return build_map_figure(existing_df, new_df, map_height_px=500)


@app.callback(
    Output("ca-total-fac",        "children"),
    Output("ca-access-pct",       "children"),
    Output("om-n-new",            "children"),
    Output("om-access-pct",       "children"),
    Output("om-delta-label",      "children"),
    Output("accessibility-chart", "figure"),
    Output("recommended-table",   "children"),
    Input("store-n-new", "data"),
    Input("store-existing-facilities", "data"),
    Input("store-accessibility-results", "data"),
)
def update_stats(n_new, existing_records, results_records):
    """
    Update KPI cards, accessibility chart, and recommended table on every
    stepper change — instant feedback without touching the map.
    """
    if existing_records is None or results_records is None:
        return (
            "—", "—", "—", "—",
            "Loading data…",
            _empty_figure(),
            build_recommended_table([]),
        )

    n_new       = n_new or 0
    existing_df = pd.DataFrame(existing_records)
    results_df  = pd.DataFrame(results_records)
    n_existing  = len(existing_df)

    access_pct  = get_access_pct(results_df, n_new, n_existing)
    delta_pct   = round(access_pct - BASELINE_ACCESS_PCT, 2) if n_new > 0 else 0.0
    total_fac   = n_existing + n_new

    ca_total    = f"{total_fac:,}"
    ca_pct      = f"{access_pct:.2f}%"
    om_n_new    = str(n_new)
    om_pct      = f"{access_pct:.2f}%"
    delta_label = (
        "current baseline"
        if n_new == 0
        else f"{format_delta(delta_pct)} vs baseline"
    )
    chart      = build_accessibility_chart(results_df, n_new, n_existing)
    table_rows = get_recommended_table_rows(results_df, n_new)
    table      = build_recommended_table(table_rows)

    return (ca_total, ca_pct, om_n_new, om_pct, delta_label, chart, table)


if __name__ == "__main__":
    app.run(debug=True)