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

from dash import dcc, html, Dash, Input, Output, no_update
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
    "backgroundColor": BG_HEADER,
    "padding": "0 28px",
    "height": f"{HEADER_H}px",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "space-between",
    "flexShrink": "0",
    "borderBottom": "1px solid rgba(255,255,255,0.06)",
}

BADGE_STYLE = {
    "display": "inline-block",
    "background": "rgba(249,115,22,0.14)",
    "border": "1px solid rgba(249,115,22,0.38)",
    "borderRadius": "5px",
    "padding": "2px 8px",
    "fontFamily": FONT_MONO,
    "fontSize": "0.57rem",
    "color": "#F97316",
    "letterSpacing": "1.2px",
    "textTransform": "uppercase",
    "marginBottom": "4px",
}

LEGEND_PILL_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "7px",
    "background": "rgba(255,255,255,0.07)",
    "border": "1px solid rgba(255,255,255,0.12)",
    "borderRadius": "99px",
    "padding": "5px 13px",
    "fontSize": "0.78rem",
    "color": "#94A3B8",
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


def legend_dot(color: str, border_color: str | None = None) -> html.Span:
    style = {**LEGEND_DOT_BASE, "backgroundColor": color}
    if border_color:
        style["border"] = f"2px solid {border_color}"
        style["backgroundColor"] = "transparent"
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


def build_recommended_table(rows: list[dict]) -> html.Div:
    """HTML table for the Recommended Locations card."""
    if not rows:
        return html.Div(
            "Move the slider above to reveal optimal new facility locations.",
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
                            "color": "#F8FAFC",
                            "letterSpacing": "-0.3px",
                            "lineHeight": "1.2",
                        },
                    ),
                    html.Div(
                        "Facility placement optimisation & population accessibility",
                        style={
                            "fontSize": "0.74rem",
                            "fontWeight": "400",
                            "color": "#475569",
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

                # ── LEFT: Map ─────────────────────────────────────────────────
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

                                        # Slider
                                        html.Div(
                                            style={"marginBottom": "18px"},
                                            children=[
                                                html.Div(
                                                    "Number of new facilities",
                                                    style=SLIDER_LABEL_STYLE,
                                                ),
                                                dcc.Slider(
                                                    id="slider-new-facilities",
                                                    min=0,
                                                    max=MAX_NEW_FACILITIES,
                                                    step=1,
                                                    value=0,
                                                    marks={
                                                        0:  {"label": "0",  "style": {"color": TEXT_LO, "fontSize": "0.67rem"}},
                                                        10: {"label": "10", "style": {"color": TEXT_LO, "fontSize": "0.67rem"}},
                                                        20: {"label": "20", "style": {"color": TEXT_LO, "fontSize": "0.67rem"}},
                                                        30: {"label": "30", "style": {"color": TEXT_LO, "fontSize": "0.67rem"}},
                                                    },
                                                    tooltip={"placement": "bottom",
                                                             "always_visible": True},
                                                ),
                                            ],
                                        ),

                                        # Two stats: n_new + access %
                                        html.Div(
                                            style={**STAT_PAIR_STYLE,
                                                   "marginBottom": "14px"},
                                            children=[
                                                html.Div([
                                                    html.Div(
                                                        id="om-n-new",
                                                        style={**BIG_NUM_STYLE,
                                                               "fontSize": "1.8rem"},
                                                    ),
                                                    html.Div(
                                                        "New facilities added",
                                                        style=BIG_NUM_LABEL_STYLE,
                                                    ),
                                                ]),
                                                html.Div([
                                                    html.Div(
                                                        id="om-access-pct",
                                                        style={**BIG_NUM_STYLE,
                                                               "fontSize": "1.8rem",
                                                               "color": ACC_INDIGO},
                                                    ),
                                                    html.Div(
                                                        id="om-delta-label",
                                                        style=BIG_NUM_LABEL_STYLE,
                                                    ),
                                                ]),
                                            ],
                                        ),

                                        # Accessibility curve
                                        dcc.Graph(
                                            id="accessibility-chart",
                                            config={"displayModeBar": False},
                                            style={"marginLeft": "-10px"},
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
    Output("map-graph",           "figure"),
    Output("ca-total-fac",        "children"),
    Output("ca-access-pct",       "children"),
    Output("om-n-new",            "children"),
    Output("om-access-pct",       "children"),
    Output("om-delta-label",      "children"),
    Output("accessibility-chart", "figure"),
    Output("recommended-table",   "children"),
    Input("slider-new-facilities", "value"),
    Input("store-existing-facilities", "data"),
    Input("store-accessibility-results", "data"),
)
def update_dashboard(n_new, existing_records, results_records):
    """
    Master callback: rebuilds the map, KPI values, accessibility chart,
    and recommended locations table whenever the slider or data stores change.
    """
    if existing_records is None or results_records is None:
        return (
            _empty_figure(500),
            "—", "—", "—", "—",
            "Loading data…",
            _empty_figure(),
            build_recommended_table([]),
        )

    existing_df = pd.DataFrame(existing_records)
    results_df  = pd.DataFrame(results_records)

    # n_existing  = len(existing_df)
    n_existing = 1258
    new_df      = get_new_facility_rows(results_df, n_new)
    access_pct  = get_access_pct(results_df, n_new, n_existing)
    delta_pct   = round(access_pct - BASELINE_ACCESS_PCT, 2) if n_new > 0 else 0.0
    total_fac   = n_existing + n_new

    # Map
    map_fig = build_map_figure(existing_df, new_df, map_height_px=500)

    # Current Accessibility card
    ca_total = f"{total_fac:,}"
    ca_pct   = f"{access_pct:.2f}%"

    # Optimization Model card
    om_n_new    = str(n_new)
    om_pct      = f"{access_pct:.2f}%"
    delta_label = (
        "current baseline"
        if n_new == 0
        else f"{format_delta(delta_pct)} vs baseline"
    )

    # Accessibility chart
    chart = build_accessibility_chart(results_df, n_new, n_existing)

    # Recommended locations table
    table_rows = get_recommended_table_rows(results_df, n_new)
    table      = build_recommended_table(table_rows)

    return (map_fig, ca_total, ca_pct,
            om_n_new, om_pct, delta_label,
            chart, table)


if __name__ == "__main__":
    app.run(debug=True)