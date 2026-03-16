"""
app.py
Zambia Health Access – Facility Placement Optimisation Dashboard
Production version: data served from Databricks Unity Catalog.

Map: Plotly go.Scattermap with open-street-map tiles (no token required).
Font: Inter throughout the UI; Space Mono for monospaced coordinate values.

Required environment variables:
    DATABRICKS_SERVER_HOSTNAME
    DATABRICKS_HTTP_PATH
    DATABRICKS_CLIENT_ID
    DATABRICKS_CLIENT_SECRET
    SECRET_KEY

Optional:
    AUTH_ENABLED=true    — enable login gate (default: false)
    ZAMBIA_CATALOG       — default: prd_mega
    FACILITIES_SCHEMA    — default: sgpbpi163
    RESULTS_SCHEMA       — default: sgpbpi163

Run:
    pip install dash dash-bootstrap-components pandas flask plotly \
                databricks-sql-connector databricks-sdk flask-login bcrypt
    python app.py
"""

import os
import pandas as pd
import plotly.graph_objects as go

from flask import redirect, url_for, request, render_template_string
from flask_login import login_required, logout_user

from dash import dcc, html, Dash, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from queries import QueryService
from server import server
from auth import authenticate, AUTH_ENABLED
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
        # Space Mono — kept for monospaced coordinate/figure values
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800"
        "&family=Space+Mono:wght@400;700&display=swap",
    ],
)

db = QueryService.get_instance()


# ── Design tokens ─────────────────────────────────────────────────────────────

BG_PAGE    = "#F8FAFC"
BG_CARD    = "#FFFFFF"
BORDER     = "#E2E8F0"
TEXT_HI    = "#0F172A"
TEXT_MID   = "#475569"
TEXT_LO    = "#94A3B8"

ACC_INDIGO = "#4F46E5"
ACC_GREEN  = "#16A34A"
ACC_RED    = "#DC2626"

FONT_BODY  = "'Inter', sans-serif"
FONT_MONO  = "'Space Mono', monospace"

HEADER_H   = 68    # px — controls the split-viewport height calculation


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


def legend_dot(color: str, border_color: str | None = None) -> html.Span:
    style = {**LEGEND_DOT_BASE, "backgroundColor": color}
    if border_color:
        style["border"]           = f"2px solid {border_color}"
        style["backgroundColor"]  = BG_PAGE
    return html.Span(style=style)


def filter_chip(label: str, value: str) -> html.Div:
    """Static non-interactive filter chip — matches the Figma dropdown style."""
    return html.Div(
        style={"display": "flex", "flexDirection": "column"},
        children=[
            html.Span(label, style=FILTER_FIELD_LABEL),
            html.Div(
                style=FILTER_CHIP_STYLE,
                children=[
                    html.Span(value, style={"flex": "1"}),
                    html.Span("▾", style={"color": TEXT_LO, "fontSize": "0.72rem",
                                          "flexShrink": "0"}),
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
            "Move the + button above to reveal optimal new facility locations.",
            style={
                "color": TEXT_LO, "fontSize": "0.82rem",
                "padding": "20px 0", "textAlign": "center",
                "fontFamily": FONT_BODY,
            },
        )

    thead = html.Thead(html.Tr([
        html.Th("NO",                          style=TH_STYLE),
        html.Th("LONGITUDE",                   style=TH_STYLE),
        html.Th("LATITUDE",                    style=TH_STYLE),
        html.Th("N OF NEW PEOPLE WITHIN 10KM", style={**TH_STYLE, "textAlign": "right"}),
        html.Th("",                            style={**TH_STYLE, "width": "30px"}),
    ]))

    tbody_rows = []
    for i, row in enumerate(rows):
        is_last      = (i == len(rows) - 1)
        td           = {**TD_STYLE,       "borderBottom": "none" if is_last else f"1px solid {BORDER}"}
        td_arrow     = {**TD_ARROW_STYLE, "borderBottom": "none" if is_last else f"1px solid {BORDER}"}
        tbody_rows.append(html.Tr([
            html.Td(str(row["no"]),    style=td),
            html.Td(row["lon_dms"],    style=td),
            html.Td(row["lat_dms"],    style=td),
            html.Td(f"{row['new_people']:,}", style={**td, "textAlign": "right"}),
            html.Td("→",              style=td_arrow),
        ]))

    return html.Div(
        style=TABLE_WRAP_STYLE,
        children=html.Table(
            [thead, html.Tbody(tbody_rows)],
            style={"width": "100%", "borderCollapse": "collapse"},
        ),
    )


# ── Login page (Flask route) ──────────────────────────────────────────────────
# Only visible / enforced when AUTH_ENABLED=true.
# When AUTH_ENABLED=false the login form auto-submits with any credentials.

_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Zambia Health Access — Sign in</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
        rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh;
      display: flex; align-items: center; justify-content: center;
      background: #F8FAFC;
      font-family: 'Inter', sans-serif;
    }
    .card {
      background: #fff;
      border: 1px solid #E2E8F0;
      border-radius: 14px;
      padding: 40px 36px;
      width: 360px;
      box-shadow: 0 4px 24px rgba(15,23,42,0.07);
    }
    h1 {
      margin: 0 0 4px;
      font-size: 1.25rem;
      font-weight: 700;
      color: #0F172A;
      letter-spacing: -0.3px;
    }
    .sub {
      font-size: 0.78rem;
      color: #64748B;
      margin-bottom: 28px;
    }
    label {
      display: block;
      font-size: 0.72rem;
      font-weight: 500;
      color: #475569;
      margin-bottom: 4px;
    }
    input[type=text], input[type=password] {
      width: 100%;
      padding: 9px 12px;
      border: 1px solid #E2E8F0;
      border-radius: 8px;
      font-family: inherit;
      font-size: 0.9rem;
      color: #0F172A;
      outline: none;
      margin-bottom: 14px;
      transition: border-color 0.15s;
    }
    input:focus { border-color: #4F46E5; }
    button {
      width: 100%;
      padding: 11px;
      background: #4F46E5;
      color: #fff;
      border: none;
      border-radius: 8px;
      font-family: inherit;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      margin-top: 4px;
      transition: background 0.15s;
    }
    button:hover { background: #4338CA; }
    .error {
      background: #FEF2F2;
      border: 1px solid #FECACA;
      border-radius: 6px;
      padding: 8px 12px;
      font-size: 0.78rem;
      color: #DC2626;
      margin-bottom: 14px;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>Zambia Health Access</h1>
    <p class="sub">Facility placement optimisation &amp; population accessibility</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="POST">
      <label for="username">Username</label>
      <input id="username" name="username" type="text" autocomplete="username" required>
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required>
      <button type="submit">Sign in</button>
    </form>
  </div>
</body>
</html>
"""


@server.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if authenticate(username, password):
            return redirect(url_for("index"))
        error = "Invalid username or password."
    return render_template_string(_LOGIN_TEMPLATE, error=error)


@server.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


# ── App layout ────────────────────────────────────────────────────────────────

app.layout = html.Div(
    style=PAGE_STYLE,
    children=[

        # ── Data stores ───────────────────────────────────────────────────────
        dcc.Store(id="store-existing-facilities"),
        dcc.Store(id="store-accessibility-results"),
        dcc.Store(id="store-n-new", data=0),

        # ── Header ────────────────────────────────────────────────────────────
        html.Div(
            style=HEADER_STYLE,
            children=[

                # Left: brand
                html.Div([
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

                # Right: map legend + logout
                html.Div(
                    style={"display": "flex", "gap": "10px", "alignItems": "center"},
                    children=[
                        html.Div(style=LEGEND_PILL_STYLE, children=[
                            legend_dot(ACC_RED),
                            html.Span("Existing facility"),
                        ]),
                        html.Div(style=LEGEND_PILL_STYLE, children=[
                            legend_dot("#FFFFFF", border_color=ACC_GREEN),
                            html.Span("Proposed facility"),
                        ]),
                        # Logout link (only visible when AUTH_ENABLED)
                        html.A(
                            "Sign out",
                            href="/logout",
                            style={
                                "fontSize": "0.74rem",
                                "color": TEXT_LO,
                                "textDecoration": "none",
                                "marginLeft": "6px",
                                "display": "block" if AUTH_ENABLED else "none",
                            },
                        ),
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
                        config={"displayModeBar": False, "scrollZoom": True},
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
                                filter_chip("Type of facility", "Hospitals and Clinics"),
                                filter_chip("Travel mode",      "Driving"),
                                filter_chip("Measure",          "Distance"),
                                filter_chip("Distance value",   "10 km"),
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
                                                    html.Div(id="ca-total-fac",  style=BIG_NUM_STYLE),
                                                    html.Div("Number of health facilities", style=BIG_NUM_LABEL_STYLE),
                                                ]),
                                                html.Div([
                                                    html.Div(
                                                        id="ca-access-pct",
                                                        style={**BIG_NUM_STYLE, "color": ACC_INDIGO},
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

                                        # Two-column inner layout
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
                                                                html.Div("Number of new facilities", style=SLIDER_LABEL_STYLE),
                                                                html.Div(
                                                                    style=STEPPER_WRAP_STYLE,
                                                                    children=[
                                                                        html.Div(id="stepper-display", style=STEPPER_VALUE_STYLE, children="0"),
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
                                                                html.Div("Optimized Accessibility %", style=SLIDER_LABEL_STYLE),
                                                                html.Div(
                                                                    style=STEPPER_WRAP_STYLE,
                                                                    children=[
                                                                        html.Div(
                                                                            id="stepper-access-display",
                                                                            style={**STEPPER_VALUE_STYLE, "color": ACC_INDIGO, "fontWeight": "600"},
                                                                            children=f"{BASELINE_ACCESS_PCT:.2f}%",
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
                                                                html.Div(id="om-n-new",     style={**BIG_NUM_STYLE, "fontSize": "1.65rem"}),
                                                                html.Div("New facilities added", style={**BIG_NUM_LABEL_STYLE, "marginBottom": "10px"}),
                                                                html.Div(id="om-access-pct",style={**BIG_NUM_STYLE, "fontSize": "1.65rem", "color": ACC_INDIGO}),
                                                                html.Div(id="om-delta-label", style=BIG_NUM_LABEL_STYLE),
                                                            ],
                                                        ),
                                                    ],
                                                ),

                                                # RIGHT COL: accessibility chart
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
                                    "|  POPULATION: WORLDPOP 2025  "
                                    "|  FACILITIES: OPENSTREETMAP  "
                                    "|  OPTIMISATION: ILP / GUROBI  "
                                    "|  DATA: DATABRICKS UNITY CATALOG",
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
    """Load existing facilities from Databricks on first render; never re-query."""
    if data is None:
        df = db.get_existing_facilities()
        return df.to_dict("records")
    return no_update


@app.callback(
    Output("store-accessibility-results", "data"),
    Input("store-accessibility-results", "data"),
)
def fetch_accessibility_results_once(data):
    """Load optimisation results from Databricks on first render; never re-query."""
    if data is None:
        df = db.get_accessibility_results()
        return df.to_dict("records")
    return no_update


@app.callback(
    Output("store-n-new",            "data"),
    Output("stepper-display",        "children"),
    Output("stepper-access-display", "children"),
    Input("btn-increase",   "n_clicks"),
    Input("btn-decrease",   "n_clicks"),
    Input("btn-increase-2", "n_clicks"),
    Input("btn-decrease-2", "n_clicks"),
    State("store-n-new", "data"),
    State("store-accessibility-results", "data"),
    State("store-existing-facilities",   "data"),
)
def update_stepper(inc, dec, inc2, dec2, current, results_records, existing_records):
    """
    Handle +/- button clicks.  Both field pairs control the same n_new counter.
    The Optimized Accessibility % display updates automatically.
    """
    from dash import ctx
    triggered = ctx.triggered_id

    n = current if current is not None else 0

    if triggered in ("btn-increase", "btn-increase-2"):
        n = min(n + 1, MAX_NEW_FACILITIES)
    elif triggered in ("btn-decrease", "btn-decrease-2"):
        n = max(n - 1, 0)

    if results_records and existing_records:
        results_df  = pd.DataFrame(results_records)
        n_existing  = len(pd.DataFrame(existing_records))
        access_pct  = get_access_pct(results_df, n, n_existing)
        access_text = f"{access_pct:.2f}%"
    else:
        access_text = f"{BASELINE_ACCESS_PCT:.2f}%"

    return n, str(n), access_text


@app.callback(
    Output("map-graph",           "figure"),
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
def update_dashboard(n_new, existing_records, results_records):
    """
    Master callback: rebuilds the map, KPI values, accessibility chart, and
    recommended locations table whenever n_new or a data store changes.
    """
    if existing_records is None or results_records is None:
        return (
            _empty_figure(500),
            "—", "—", "—", "—",
            "Loading data from Databricks…",
            _empty_figure(),
            build_recommended_table([]),
        )

    n_new = n_new or 0

    existing_df = pd.DataFrame(existing_records)
    results_df  = pd.DataFrame(results_records)
    n_existing  = len(existing_df)

    new_df     = get_new_facility_rows(results_df, n_new)
    access_pct = get_access_pct(results_df, n_new, n_existing)
    delta_pct  = round(access_pct - BASELINE_ACCESS_PCT, 2) if n_new > 0 else 0.0
    total_fac  = n_existing + n_new

    map_fig     = build_map_figure(existing_df, new_df, map_height_px=500)
    ca_total    = f"{total_fac:,}"
    ca_pct      = f"{access_pct:.2f}%"
    om_n_new    = str(n_new)
    om_pct      = f"{access_pct:.2f}%"
    delta_label = (
        "current baseline"
        if n_new == 0
        else f"{format_delta(delta_pct)} vs baseline"
    )
    chart       = build_accessibility_chart(results_df, n_new, n_existing)
    table_rows  = get_recommended_table_rows(results_df, n_new)
    table       = build_recommended_table(table_rows)

    return (map_fig, ca_total, ca_pct,
            om_n_new, om_pct, delta_label,
            chart, table)


if __name__ == "__main__":
    app.run(debug=os.getenv("DASH_DEBUG", "False").lower() == "true")