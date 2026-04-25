
import logging
from urllib.parse import parse_qs

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional
from dash import dcc, html, Dash, Input, Output, State, ctx, no_update
import dash_bootstrap_components as dbc

from queries import QueryService
from server import server
from utils import (
    build_standard_map,
    build_map_figure,
    get_new_facility_rows,
    get_access_pct,
    format_delta,
    build_accessibility_chart,
    get_recommended_table_rows,
)
from constants import (
    # Country registry helpers
    get_country_config,
    DEFAULT_COUNTRY,
    VALID_COUNTRIES,
    # Zambia backward-compat (used as defaults in utils.py function signatures)
    BASELINE_ACCESS_PCT,
    BASELINE_ACCESS_PCT_5KM,
    BASELINE_ACCESS_PCT_10KM,
    BASELINE_ACCESS_PCT_30MIN,
    BASELINE_ACCESS_PCT_1HR,
    MAX_NEW_FACILITIES,
    ZAMBIA_CENTER_LAT,
    ZAMBIA_CENTER_LON,
    MAP_ZOOM,
)

# ── Dash app ──────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800"
        "&family=Space+Mono:wght@400;700&display=swap",
    ],
)

db = QueryService.get_instance()

# ── Startup: pre-warm the Zambia query cache ───────────────────────────────────
# Keyed by country slug so multiple countries can be cached independently.
# Only Zambia is pre-loaded at startup (most common default).
# For any other country the first user page-load triggers the DB fetch; after
# that, subsequent loads hit the QueryService TTL cache.

_BOUNDARY_WKT_CACHE: dict = {}

try:
    _init_base = db.get_base_dashboard_data("zambia", 5, country="zambia")
    _BOUNDARY_WKT_CACHE["zambia"] = _init_base.get("geometry_wkt")
    logging.info(
        "Startup boundary WKT pre-loaded for Zambia (len=%d)",
        len(_BOUNDARY_WKT_CACHE.get("zambia") or ""),
    )
except Exception as _e:
    logging.warning("Startup base-data load failed: %s", _e)


# ── Baseline helper ────────────────────────────────────────────────────────────

def _get_baseline(
    distance_km,
    base_data: Optional[dict] = None,
    country: str = DEFAULT_COUNTRY,
) -> float:
    """
    Return the correct baseline access %.

    Priority:
      1. Live value from store-base-data (fetched from Databricks).
      2. Hardcoded fallback from COUNTRY_CONFIGS[country]["fallback_baselines"].

    The country argument is needed for step 2 so non-Zambia countries return
    their own fallback rather than Zambia's.
    """
    if base_data and base_data.get("current_access") is not None:
        try:
            return float(base_data["current_access"])
        except (ValueError, TypeError):
            pass
    cfg = get_country_config(country)
    return cfg["fallback_baselines"].get(distance_km, cfg["fallback_baselines"].get(5, 0.0))


# ── Design tokens ─────────────────────────────────────────────────────────────

BG_PAGE    = "#F8FAFC"
BG_HEADER  = "#0B1120"
BG_CARD    = "#FFFFFF"
BORDER     = "#E2E8F0"
BORDER_HVR = "#CBD5E1"
TEXT_HI    = "#0F172A"
TEXT_MID   = "#475569"
TEXT_LO    = "#94A3B8"

ACC_INDIGO = "#4F46E5"
ACC_GREEN  = "#16A34A"
ACC_RED    = "#DC2626"

FONT_BODY  = "'Inter', sans-serif"
FONT_MONO  = "'Space Mono', monospace"

HEADER_H   = 68

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

LEGEND_PIN_BASE = {
    "display":      "inline-block",
    "width":        "12px",
    "height":       "12px",
    "borderRadius": "50% 50% 50% 0",
    "transform":    "rotate(-45deg)",
    "flexShrink":   "0",
    "marginBottom": "4px",
}

def legend_pin(color: str) -> html.Span:
    return html.Span(style={**LEGEND_PIN_BASE, "backgroundColor": color})

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
    "fontWeight": "900",
    "fontSize": "0.78rem",
    "letterSpacing": "1.1px",
    "textTransform": "uppercase",
    "color": TEXT_HI,
    "marginBottom": "16px",
    "fontFamily": FONT_BODY,
}

BIG_NUM_STYLE = {
    "fontFamily": FONT_BODY,
    "fontSize": "1.4rem",
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
    "maxWidth": "400px",
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

VIEW_BTN_STYLE_DISABLED = {
    **VIEW_BTN_STYLE,
    "background": TEXT_LO,
    "cursor":     "not-allowed",
    "opacity":    "0.55",
}

CLEAR_BTN_STYLE = {
    **VIEW_BTN_STYLE,
    "background": "#DC2626",
    "cursor":     "pointer",
}

STAT_PAIR_STYLE = {
    "display": "flex",
    "flexDirection": "row",
    "flexWrap": "nowrap",
    "alignItems": "flex-start",
    "gap": "48px",
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
        style["backgroundColor"] = BG_PAGE
    return html.Span(style=style)


def filter_chip(label: str, value: str) -> html.Div:
    """Static non-interactive filter chip."""
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
                        style={"color": TEXT_LO, "fontSize": "0.72rem", "flexShrink": "0"},
                    ),
                ],
            ),
        ],
    )


def filter_dropdown(label: str, options: list, value, dropdown_id: str,
                    disabled: bool = False) -> html.Div:
    """Interactive filter dropdown styled to match the existing filter chips."""
    return html.Div(
        style={"display": "flex", "flexDirection": "column"},
        children=[
            html.Span(label, style=FILTER_FIELD_LABEL),
            dcc.Dropdown(
                id=dropdown_id,
                options=options,
                value=value,
                clearable=False,
                searchable=False,
                disabled=disabled,
                style={
                    "minWidth": "130px",
                    "fontSize": "0.84rem",
                    "fontFamily": FONT_BODY,
                    "fontWeight": "500",
                    "color": TEXT_HI,
                    "borderRadius": "8px",
                    "cursor": "pointer" if not disabled else "default",
                },
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
        html.Th("DISTRICT",                  style=TH_STYLE),
        html.Th("ACCESS GAINED POPULATION",  style={**TH_STYLE, "textAlign": "right"}),
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
            html.Td(row["lon_dms"],          style=row_td_style),
            html.Td(row["lat_dms"],          style=row_td_style),
            html.Td(row["district"],         style=row_td_style),
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

        # ── URL location component (reads ?country= query param) ──────────────
        # refresh=False: URL changes do not cause a full page reload.
        # Posit Connect iframe embedding preserves query-string parameters, so
        # dcc.Location.search will contain e.g. "?country=malawi" on load.
        dcc.Location(id="url", refresh=False),

        # ── Data stores ───────────────────────────────────────────────────────
        # store-country: set once from the URL query param; drives everything else.
        dcc.Store(id="store-country",  data=DEFAULT_COUNTRY),
        dcc.Store(id="store-existing-facilities"),
        dcc.Store(id="store-accessibility-results"),
        dcc.Store(id="store-n-new",       data=0),
        dcc.Store(id="store-distance-km", data=5),
        dcc.Store(id="store-map-active",  data=False),
        # store-location: country slug for country-level view, sub-unit name
        # (e.g. "Central") for sub-national view.  Initialised to None;
        # immediately populated by callback once store-country is set.
        dcc.Store(id="store-location",    data=None),
        dcc.Store(id="store-base-data",   data=None),

        # ── Header ────────────────────────────────────────────────────────────
        html.Div(
            style=HEADER_STYLE,
            children=[

                # Left: brand (title updated dynamically by callback)
                html.Div([
                    html.Div(
                        id="header-title",
                        children="Health Access Dashboard",
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

                # Right: location dropdown + map legend pills
                html.Div(
                    style={"display": "flex", "gap": "10px", "alignItems": "center"},
                    children=[

                        # ── Location dropdown ─────────────────────────────────
                        # Options and value are populated dynamically by the
                        # update_location_dropdown callback whenever store-country
                        # changes.  Initialised empty to avoid a flash of stale
                        # Zambia options when loading the Malawi URL.
                        html.Div(
                            style={"display": "flex", "flexDirection": "column"},
                            children=[
                                html.Span(
                                    style={
                                        **FILTER_FIELD_LABEL,
                                        "marginBottom": "3px",
                                        "fontSize": "0.63rem",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="dropdown-location",
                                    options=[],      # populated by callback
                                    value=None,      # populated by callback
                                    clearable=False,
                                    searchable=False,
                                    placeholder="Loading…",
                                    optionHeight=32,
                                    style={
                                        "minWidth": "195px",
                                        "maxWidth": "220px",
                                        "fontSize": "0.82rem",
                                        "fontFamily": FONT_BODY,
                                        "fontWeight": "500",
                                        "color": TEXT_HI,
                                        "borderRadius": "8px",
                                        "cursor": "pointer",
                                    },
                                ),
                            ],
                        ),

                        # ── Legend pills ──────────────────────────────────────
                        html.Div(style=LEGEND_PILL_STYLE, children=[
                            legend_pin(ACC_RED),
                            html.Span("Existing facility"),
                        ]),
                        html.Div(style=LEGEND_PILL_STYLE, children=[
                            legend_dot("#FFFFFF", border_color=ACC_GREEN),
                            html.Span("Proposed facility"),
                        ]),
                        html.Div(style=LEGEND_PILL_STYLE, children=[
                            html.Span(style={
                                "display": "inline-block",
                                "width": "18px",
                                "height": "3px",
                                "backgroundColor": "#F67215",
                                "borderRadius": "2px",
                                "flexShrink": "0",
                                "verticalAlign": "middle",
                                "marginBottom": "1px",
                            }),
                            html.Span(id="legend-boundary-label", children="—"),
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
                        "flex": "0 0 50%",
                        "height": "100%",
                        "borderRight": f"1px solid {BORDER}",
                        "overflow": "hidden",
                        "backgroundColor": "#EEF0F4",
                    },
                    id="map-container",
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

                        # Filter bar
                        html.Div(
                            style=FILTER_BAR_STYLE,
                            children=[
                                filter_chip("Type of facility", "Hospitals and Clinics"),
                                filter_dropdown(
                                    "Travel mode",
                                    options=[
                                        {"label": "Driving", "value": "Driving"},
                                        {"label": "Walking", "value": "Walking"},
                                    ],
                                    value="Driving",
                                    dropdown_id="dropdown-travel-mode",
                                ),
                                filter_dropdown(
                                    "Measure",
                                    options=[
                                        {"label": "Distance", "value": "Distance"},
                                        {"label": "Time",     "value": "Time"},
                                    ],
                                    value="Distance",
                                    dropdown_id="dropdown-measure",
                                    disabled=True,
                                ),
                                filter_dropdown(
                                    "Value",
                                    options=[
                                        {"label": "5 km",  "value": 5},
                                        {"label": "10 km", "value": 10},
                                    ],
                                    value=5,
                                    dropdown_id="dropdown-distance-km",
                                ),
                            ],
                        ),

                        # Scrollable content
                        html.Div(
                            style={
                                "flex": "1",
                                "overflowY": "auto",
                                "padding": "16px 42px",
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
                                                        [
                                                            "Number of health facilities in ",
                                                            html.Span(id="ca-location-label",
                                                                      children="—"),
                                                        ],
                                                        style=BIG_NUM_LABEL_STYLE,
                                                    ),
                                                ]),
                                                html.Div([
                                                    html.Div(
                                                        id="ca-access-pct",
                                                        style={
                                                            **BIG_NUM_STYLE,
                                                            "color": TEXT_HI,
                                                        },
                                                    ),
                                                    html.Div(
                                                        [
                                                            "Percentage of population with access to ",
                                                            html.I("all"),
                                                            " health facilities in ",
                                                            html.Span(id="location-label-detail",
                                                                      children="—"),
                                                            " within ",
                                                            html.U(id="distance-value-label",
                                                                   children="5 km"),
                                                            " travel ",
                                                            html.Span(
                                                                id="travel-mode-description",
                                                                children=[html.I("distance"),
                                                                          " by driving"],
                                                            ),
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

                                        html.Div(
                                            style={
                                                "display": "flex",
                                                "gap": "10px",
                                                "alignItems": "flex-start",
                                            },
                                            children=[

                                                # LEFT COL: steppers + button + stats
                                                html.Div(
                                                    style={"flex": "0 0 200px"},
                                                    children=[

                                                        html.Div(
                                                            style={
                                                                "display": "flex",
                                                                "flexDirection": "row",
                                                                "gap": "8px",
                                                                "marginBottom": "16px",
                                                            },
                                                            children=[
                                                                html.Div([
                                                                    html.Div(
                                                                        id="om-n-new",
                                                                        style={**BIG_NUM_STYLE, "fontSize": "1.65rem"},
                                                                    ),
                                                                    html.Div(
                                                                        "New facilities added",
                                                                        style=BIG_NUM_LABEL_STYLE,
                                                                    ),
                                                                ]),
                                                            ],
                                                        ),

                                                        html.Div(
                                                            style={"marginBottom": "12px"},
                                                            children=[
                                                                html.Div("Number of new facilities",
                                                                         style=SLIDER_LABEL_STYLE),
                                                                html.Div(
                                                                    style=STEPPER_WRAP_STYLE,
                                                                    children=[
                                                                        html.Div(id="stepper-display",
                                                                                 style=STEPPER_VALUE_STYLE,
                                                                                 children="0"),
                                                                        html.Div(
                                                                            style=STEPPER_BTN_GROUP_STYLE,
                                                                            children=[
                                                                                html.Button("+", id="btn-increase",
                                                                                            n_clicks=0,
                                                                                            style=STEPPER_BTN_STYLE),
                                                                                html.Div(style={
                                                                                    "height": "1px",
                                                                                    "background": BORDER,
                                                                                    "flexShrink": "0",
                                                                                }),
                                                                                html.Button("−", id="btn-decrease",
                                                                                            n_clicks=0,
                                                                                            style=STEPPER_BTN_STYLE),
                                                                            ],
                                                                        ),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),

                                                        html.Div(
                                                            style={"marginBottom": "0"},
                                                            children=[
                                                                html.Div("Optimized Accessibility %",
                                                                         style=SLIDER_LABEL_STYLE),
                                                                html.Div(
                                                                    style=STEPPER_WRAP_STYLE,
                                                                    children=[
                                                                        html.Div(
                                                                            id="stepper-access-display",
                                                                            style={**STEPPER_VALUE_STYLE,
                                                                                   "color": ACC_INDIGO,
                                                                                   "fontWeight": "600"},
                                                                            children="—",
                                                                        ),
                                                                        html.Div(
                                                                            style=STEPPER_BTN_GROUP_STYLE,
                                                                            children=[
                                                                                html.Button("+", id="btn-increase-2",
                                                                                            n_clicks=0,
                                                                                            style=STEPPER_BTN_STYLE),
                                                                                html.Div(style={
                                                                                    "height": "1px",
                                                                                    "background": BORDER,
                                                                                    "flexShrink": "0",
                                                                                }),
                                                                                html.Button("−", id="btn-decrease-2",
                                                                                            n_clicks=0,
                                                                                            style=STEPPER_BTN_STYLE),
                                                                            ],
                                                                        ),
                                                                    ],
                                                                ),
                                                            ],
                                                        ),

                                                        html.Button(
                                                            "View locations",
                                                            id="btn-view-locations",
                                                            n_clicks=0,
                                                            disabled=True,
                                                            style=VIEW_BTN_STYLE,
                                                        ),
                                                    ],
                                                ),

                                                # RIGHT COL: accessibility curve
                                                html.Div(
                                                    style={
                                                        "flex": "1 1 0",
                                                        "minWidth": "0",
                                                        "display": "flex",
                                                        "flexDirection": "column",
                                                        "gap": "8px",
                                                    },
                                                    children=[
                                                        html.Div([
                                                            html.Div(
                                                                id="om-access-pct",
                                                                style={**BIG_NUM_STYLE,
                                                                       "fontSize": "1.65rem",
                                                                       "color": ACC_INDIGO},
                                                            ),
                                                            html.Div(
                                                                id="om-delta-label",
                                                                style=BIG_NUM_LABEL_STYLE,
                                                            ),
                                                        ]),
                                                        dcc.Graph(
                                                            id="accessibility-chart",
                                                            figure=_empty_figure(),
                                                            config={"displayModeBar": False},
                                                            style={"flex": "1", "minHeight": "0"},
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

                                # Footer (updated dynamically by callback)
                                html.Div(id="footer-text", style=FOOTER_STYLE),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


# ── Map graph factory ─────────────────────────────────────────────────────────

def _make_graph(figure: go.Figure, key: str) -> html.Div:
    """
    Wrap a Plotly figure in a div with a unique `key` to force React remount.

    React uses `key` to decide whether a component is the same element or a
    new one.  When `key` changes, React unmounts the old div and mounts a
    brand-new one — guaranteeing that Plotly initialises fresh instead of
    trying to diff/patch the existing MapLibre instance.
    """
    return html.Div(
        key=key,
        children=dcc.Graph(
            id="map-graph",
            figure=figure,
            config={"displayModeBar": False, "scrollZoom": True},
            style={"width": "100%", "height": f"calc(100vh - {HEADER_H}px)"},
        ),
    )


# ── Callbacks ─────────────────────────────────────────────────────────────────

# ── 0. Parse country from URL query string ────────────────────────────────────

@app.callback(
    Output("store-country", "data"),
    Input("url", "search"),
    prevent_initial_call=False,   # must fire on first render to read the URL
)
def parse_country_from_url(search: str) -> str:
    """
    Read the ?country=<slug> query parameter and write it to store-country.

    Fires immediately on page load so the rest of the callback graph uses the
    correct country before any data is fetched.

    Invalid slugs are silently replaced with DEFAULT_COUNTRY ("zambia") so
    misconfigured embed links degrade gracefully rather than crashing.
    """
    if not search:
        return DEFAULT_COUNTRY

    try:
        params      = parse_qs(search.lstrip("?"))
        country_raw = params.get("country", [DEFAULT_COUNTRY])[0].lower().strip()
    except Exception:
        return DEFAULT_COUNTRY

    if country_raw in VALID_COUNTRIES:
        logging.info("URL param country=%s accepted", country_raw)
        return country_raw

    logging.warning(
        "Unknown ?country=%s; defaulting to '%s'. "
        "Valid values: %s",
        country_raw, DEFAULT_COUNTRY, sorted(VALID_COUNTRIES),
    )
    return DEFAULT_COUNTRY


# ── 1. Populate location dropdown from active country ─────────────────────────

@app.callback(
    Output("dropdown-location", "options"),
    Output("dropdown-location", "value"),
    Input("store-country", "data"),
)
def update_location_dropdown(country: str):
    """
    Rebuild the location dropdown whenever the active country changes.

    The top entry is the country itself (country-level view).
    Below it is a disabled separator followed by the subnational units
    (provinces, regions, …) defined in COUNTRY_CONFIGS.
    """
    country      = country or DEFAULT_COUNTRY
    cfg          = get_country_config(country)
    display_name = cfg["display_name"]
    sub_label    = cfg["subnational_label"]
    units        = cfg["subnational_units"]

    options = [
        {"label": display_name, "value": country},
        {"label": f"── {sub_label}s ──", "value": "_sep", "disabled": True},
    ] + [
        {"label": f"      {u}", "value": u}
        for u in units
    ]

    # Reset to country-level view whenever country changes
    return options, country


# ── 2. Sync store-location from dropdown or country change ────────────────────

@app.callback(
    Output("store-location", "data"),
    Input("dropdown-location", "value"),
    Input("store-country",     "data"),
)
def update_location_store(dropdown_val: str, country: str) -> str:
    """
    Write the selected location to store-location.

    When the trigger is store-country (country changed), the location resets
    to the country-level view (country slug).  When the trigger is
    dropdown-location, the chosen value is used (filtered against the sentinel
    "_sep" which is the disabled separator row).
    """
    country  = country or DEFAULT_COUNTRY
    triggered = ctx.triggered_id

    if triggered == "store-country":
        # Country just changed — reset location to country level
        return country

    # Dropdown interaction
    if not dropdown_val or dropdown_val == "_sep":
        return country

    return dropdown_val


# ── 3. Fetch base dashboard data (center, boundary, baseline) ─────────────────

@app.callback(
    Output("store-base-data", "data"),
    Input("store-location",    "data"),
    Input("store-distance-km", "data"),
    State("store-country",     "data"),
)
def fetch_base_data(location, distance_km, country):
    """
    Re-fetch base dashboard data whenever location or distance changes.
    Drives: map centre, zoom, boundary WKT, and baseline access %.
    """
    country = country or DEFAULT_COUNTRY
    loc     = location or country
    km      = distance_km if distance_km is not None else 5

    try:
        data = db.get_base_dashboard_data(loc, km, country=country)
        logging.info(
            "Base data fetched: country=%s location=%s km=%s access=%.2f%%",
            country, loc, km, data.get("current_access", 0),
        )
        return data
    except Exception as exc:
        logging.error("fetch_base_data error (country=%s loc=%s): %s", country, loc, exc)
        cfg = get_country_config(country)
        return {
            "center_lat":           cfg["center_lat"],
            "center_lon":           cfg["center_lon"],
            "zoom":                 cfg["map_zoom"] if loc.lower() == country.lower()
                                    else cfg["province_zoom"],
            "geometry_wkt":         _BOUNDARY_WKT_CACHE.get(country),
            "current_access":       _get_baseline(km, country=country),
            "total_new_facilities": MAX_NEW_FACILITIES,
            "location":             loc,
        }


# ── 4. Fetch existing facilities (scoped to location + country) ───────────────

@app.callback(
    Output("store-existing-facilities", "data"),
    Input("store-location", "data"),
    State("store-country",  "data"),
)
def fetch_existing_facilities(location, country):
    """
    Load existing health facilities scoped to the selected location.

    For country-level views, the full national table is queried.
    For subnational views, the dedicated per-unit table is used so the map
    only shows facilities that belong to that unit.
    """
    country = country or DEFAULT_COUNTRY
    loc     = location or country

    try:
        df = db.get_existing_facilities_for_location(loc, country=country)
        logging.info(
            "Loaded %d facilities for country='%s' location='%s'", len(df), country, loc,
        )
        return df.to_dict("records")
    except Exception as exc:
        logging.error(
            "fetch_existing_facilities error (country=%s location=%s): %s",
            country, loc, exc,
        )
        return []


# ── 5. Fetch MCLP optimisation results ───────────────────────────────────────

@app.callback(
    Output("store-accessibility-results", "data"),
    Input("store-distance-km", "data"),
    Input("store-location",    "data"),
    State("store-country",     "data"),
)
def fetch_accessibility_results(distance_km, location, country):
    """Re-fetch results whenever distance or location changes."""
    country = country or DEFAULT_COUNTRY
    loc     = location or country
    km      = distance_km if distance_km is not None else 5

    try:
        df = db.get_accessibility_results_for_location(loc, km, country=country)
        return df.to_dict("records")
    except Exception as exc:
        logging.error(
            "fetch_accessibility_results error (country=%s loc=%s km=%s): %s",
            country, loc, km, exc,
        )
        return []


# ── 6. Sync distance store from Value dropdown ────────────────────────────────

@app.callback(
    Output("store-distance-km", "data"),
    Input("dropdown-distance-km", "value"),
)
def sync_distance_store(value):
    """Persist the selected catchment radius / travel-time band."""
    return value if value is not None else 5


# ── 7. Reset on distance switch ───────────────────────────────────────────────

@app.callback(
    Output("store-n-new",      "data", allow_duplicate=True),
    Output("store-map-active", "data", allow_duplicate=True),
    Input("store-distance-km", "data"),
    prevent_initial_call=True,
)
def reset_on_distance_change(distance_km):
    return 0, False


# ── 8. Reset on location switch ───────────────────────────────────────────────

@app.callback(
    Output("store-n-new",      "data", allow_duplicate=True),
    Output("store-map-active", "data", allow_duplicate=True),
    Input("store-location", "data"),
    prevent_initial_call=True,
)
def reset_on_location_change(location):
    return 0, False


# ── 9. Travel mode → Measure (auto, read-only) ────────────────────────────────

@app.callback(
    Output("dropdown-measure", "value"),
    Input("dropdown-travel-mode", "value"),
)
def update_measure_on_travel_mode(travel_mode):
    return "Distance" if travel_mode == "Driving" else "Time"


# ── 10. Travel mode → Value dropdown options ──────────────────────────────────

@app.callback(
    Output("dropdown-distance-km", "options"),
    Output("dropdown-distance-km", "value"),
    Input("dropdown-travel-mode", "value"),
)
def update_value_dropdown_on_travel_mode(travel_mode):
    if travel_mode == "Walking":
        return [
            {"label": "30 min", "value": "30min"},
            {"label": "1 hr",   "value": "1hr"},
        ], "30min"
    return [
        {"label": "5 km",  "value": 5},
        {"label": "10 km", "value": 10},
    ], 5


# ── 11. Distance value label in Current Accessibility description ─────────────

@app.callback(
    Output("distance-value-label", "children"),
    Input("store-distance-km", "data"),
)
def update_distance_value_label(distance_km):
    label_map = {5: "5 km", 10: "10 km", "30min": "30 min", "1hr": "1 hr"}
    return label_map.get(distance_km, "5 km")


# ── 12. Travel mode description in Current Accessibility ─────────────────────

@app.callback(
    Output("travel-mode-description", "children"),
    Input("dropdown-travel-mode", "value"),
)
def update_travel_mode_description(travel_mode):
    if travel_mode == "Walking":
        return [html.I("time"), " by walking"]
    return [html.I("distance"), " by driving"]


# ── 13. Header title (country-aware) ─────────────────────────────────────────

@app.callback(
    Output("header-title", "children"),
    Input("store-country", "data"),
)
def update_header_title(country):
    cfg = get_country_config(country)
    return f"{cfg['display_name']} Health Access"


# ── 14. Footer text (country-aware) ──────────────────────────────────────────

@app.callback(
    Output("footer-text", "children"),
    Input("store-country", "data"),
)
def update_footer_text(country):
    cfg = get_country_config(country)
    return f"World Bank · Public Infrastructure Investment · GoAT · {cfg['display_name']} 2025"


# ── 15. Legend boundary label ─────────────────────────────────────────────────

@app.callback(
    Output("legend-boundary-label", "children"),
    Input("store-location", "data"),
    State("store-country",  "data"),
)
def update_legend_boundary_label(location, country):
    """Show '<Country> boundary' at country level, '<Unit> boundary' at subnational."""
    country = country or DEFAULT_COUNTRY
    cfg     = get_country_config(country)

    if not location or location.lower() == country.lower():
        return f"{cfg['display_name']} boundary"
    return f"{location} boundary"


# ── 16. Location label in Current Accessibility description ───────────────────

@app.callback(
    Output("location-label-detail", "children"),
    Input("store-location", "data"),
    State("store-country",  "data"),
)
def update_location_label_detail(location, country):
    country = country or DEFAULT_COUNTRY
    cfg     = get_country_config(country)
    if not location or location.lower() == country.lower():
        return cfg["display_name"]
    return location.title()


# ── 17. Location label in facilities count ────────────────────────────────────

@app.callback(
    Output("ca-location-label", "children"),
    Input("store-location", "data"),
    State("store-country",  "data"),
)
def update_ca_location_label(location, country):
    country = country or DEFAULT_COUNTRY
    cfg     = get_country_config(country)
    if not location or location.lower() == country.lower():
        return cfg["display_name"]
    return location.title()


# ── 18. Stepper: +/- buttons update store-n-new ──────────────────────────────

@app.callback(
    Output("store-n-new", "data"),
    Input("btn-increase",   "n_clicks"),
    Input("btn-decrease",   "n_clicks"),
    Input("btn-increase-2", "n_clicks"),
    Input("btn-decrease-2", "n_clicks"),
    State("store-n-new", "data"),
)
def update_stepper(inc, dec, inc2, dec2, current):
    triggered = ctx.triggered_id
    n = current if current is not None else 0

    if triggered in ("btn-increase", "btn-increase-2"):
        n = min(n + 1, MAX_NEW_FACILITIES)
    elif triggered in ("btn-decrease", "btn-decrease-2"):
        n = max(n - 1, 0)

    return n


# ── 19. View / Clear button toggle ───────────────────────────────────────────

@app.callback(
    Output("store-map-active", "data"),
    Output("store-n-new",      "data", allow_duplicate=True),
    Input("btn-view-locations", "n_clicks"),
    State("store-map-active",  "data"),
    prevent_initial_call=True,
)
def handle_button_click(n_clicks, is_active):
    if is_active:
        return False, 0
    return True, no_update


# ── 20. View / Clear button label + style ────────────────────────────────────

@app.callback(
    Output("btn-view-locations", "children"),
    Output("btn-view-locations", "disabled"),
    Output("btn-view-locations", "style"),
    Input("store-map-active",            "data"),
    Input("store-n-new",                 "data"),
    Input("store-accessibility-results", "data"),
    State("store-existing-facilities",   "data"),
    State("store-distance-km",           "data"),
)
def update_button(is_active, n_new, results_records, existing_records, distance_km):
    n_new = n_new or 0
    if is_active:
        return "Clear map", False, CLEAR_BTN_STYLE

    is_ready = bool(results_records) and n_new > 0

    return (
        "View locations",
        not is_ready,
        VIEW_BTN_STYLE if is_ready else VIEW_BTN_STYLE_DISABLED,
    )


# ── 21. Stepper display sync ──────────────────────────────────────────────────

@app.callback(
    Output("stepper-display",        "children"),
    Output("stepper-access-display", "children"),
    Input("store-n-new",                  "data"),
    State("store-accessibility-results",  "data"),
    State("store-existing-facilities",    "data"),
    State("store-distance-km",            "data"),
    State("store-base-data",              "data"),
    State("store-country",                "data"),
)
def sync_stepper_display(n_new, results_records, existing_records,
                         distance_km, base_data, country):
    country  = country or DEFAULT_COUNTRY
    n_new    = n_new or 0
    baseline = _get_baseline(distance_km, base_data, country)

    if results_records and existing_records:
        results_df  = pd.DataFrame(results_records)
        n_existing  = len(pd.DataFrame(existing_records))
        access_pct  = get_access_pct(results_df, n_new, n_existing, baseline)
        access_text = f"{access_pct:.2f}%"
    else:
        access_text = f"{baseline:.2f}%" if baseline else "—"

    return str(n_new), access_text


# ── 22. Map ───────────────────────────────────────────────────────────────────

@app.callback(
    Output("map-container", "children"),

    Input("btn-view-locations",        "n_clicks"),
    Input("store-existing-facilities", "data"),
    Input("store-distance-km",         "data"),
    Input("store-n-new",               "data"),
    Input("store-base-data",           "data"),   # triggers on location/country change

    State("store-map-active",           "data"),
    State("store-accessibility-results","data"),
    State("store-location",             "data"),
    State("store-country",              "data"),

    prevent_initial_call=False,
)
def update_map(n_clicks, existing_records, distance_km, n_new, base_data,
               is_map_active, results_records, location, country):
    """
    Returns a complete dcc.Graph element (not just a figure) so React remounts
    the graph fresh on every meaningful state change.

    The `key` on the returned dcc.Graph forces the remount:
      standard map  → key "std-{country}-{loc}-{km}"
      optimised map → key "opt-{country}-{loc}-{km}-{nc}-{n}"
      cleared map   → key "clr-{country}-{loc}-{km}-{nc}"

    Including both country and loc in the key guarantees a full remount on
    country or location switches, even when km and n_new are unchanged.
    """
    country   = country or DEFAULT_COUNTRY
    cfg       = get_country_config(country)
    km        = distance_km or 5
    n_new     = n_new or 0
    clicks    = n_clicks or 0
    loc_slug  = (location or country).lower().replace(" ", "_").replace("-", "_")
    triggered = ctx.triggered_id

    # ── Extract dynamic map config from base_data ──────────────────────────────
    # Fallback values come from the country config, not hardcoded Zambia constants.
    boundary_wkt = _BOUNDARY_WKT_CACHE.get(country)   # startup pre-warm cache
    center_lat   = cfg["center_lat"]
    center_lon   = cfg["center_lon"]
    zoom         = cfg["map_zoom"]

    if base_data:
        boundary_wkt = base_data.get("geometry_wkt") or boundary_wkt
        center_lat   = base_data.get("center_lat",  center_lat)
        center_lon   = base_data.get("center_lon",  center_lon)
        zoom         = base_data.get("zoom",        zoom)
        # Cache the boundary WKT for this country so future renders
        # have a synchronous fallback without a DB round-trip.
        if base_data.get("geometry_wkt"):
            _BOUNDARY_WKT_CACHE[country] = base_data["geometry_wkt"]

    # Stable map key prefix: encodes country + location + distance
    key_prefix = f"{country}-{loc_slug}-{km}"

    if existing_records is None:
        return _make_graph(_empty_figure(500), key=f"empty-{key_prefix}")

    existing_df = pd.DataFrame(existing_records)

    def _std_map(uirevision="standard"):
        return build_standard_map(
            existing_df,
            boundary_wkt=boundary_wkt,
            center_lat=center_lat,
            center_lon=center_lon,
            zoom=zoom,
            uirevision=uirevision,
        )

    def _opt_map():
        results_df = pd.DataFrame(results_records)
        new_df     = get_new_facility_rows(results_df, n_new)
        return build_map_figure(
            existing_df, new_df,
            boundary_wkt=boundary_wkt,
            center_lat=center_lat,
            center_lon=center_lon,
            zoom=zoom,
        )

    # ── Initial load / distance switch / location or country change ────────────
    if triggered in (None, "store-existing-facilities", "store-distance-km", "store-base-data"):
        logging.info("Standard map  trigger=%s country=%s loc=%s km=%s",
                     triggered, country, loc_slug, km)
        return _make_graph(_std_map(), key=f"std-{key_prefix}")

    # ── Stepper changed ────────────────────────────────────────────────────────
    if triggered == "store-n-new":
        if n_new == 0:
            return _make_graph(_std_map(), key=f"clr-{key_prefix}-{clicks}")

        if is_map_active and results_records:
            return _make_graph(_opt_map(), key=f"opt-{key_prefix}-{clicks}-{n_new}")

        return no_update

    # ── Button click ───────────────────────────────────────────────────────────
    if triggered == "btn-view-locations":
        viewing = not is_map_active

        if viewing and results_records:
            logging.info("View locations: %d facilities  country=%s loc=%s",
                         n_new, country, loc_slug)
            return _make_graph(_opt_map(), key=f"opt-{key_prefix}-{clicks}-{n_new}")

        logging.info("Clear map  country=%s loc=%s clicks=%d", country, loc_slug, clicks)
        return _make_graph(_std_map(), key=f"clr-{key_prefix}-{clicks}")

    logging.warning("Unhandled trigger: %s", triggered)
    return no_update


# ── 23. KPI cards, accessibility chart, recommended table ────────────────────

@app.callback(
    Output("ca-total-fac",        "children"),
    Output("ca-access-pct",       "children"),
    Output("om-n-new",            "children"),
    Output("om-access-pct",       "children"),
    Output("om-delta-label",      "children"),
    Output("accessibility-chart", "figure"),
    Output("recommended-table",   "children"),
    Input("store-n-new",                  "data"),
    Input("store-existing-facilities",    "data"),
    Input("store-accessibility-results",  "data"),
    State("store-distance-km",            "data"),
    State("store-base-data",              "data"),
    State("store-country",                "data"),
)
def update_stats(n_new, existing_records, results_records,
                 distance_km, base_data, country):
    """
    Update KPI cards, accessibility chart, and recommended table on every
    stepper or data change.

    The country_population from COUNTRY_CONFIGS is passed to
    get_recommended_table_rows so the "new people reached" figure reflects the
    correct national population for non-Zambia countries.
    """
    country = country or DEFAULT_COUNTRY
    cfg     = get_country_config(country)

    if existing_records is None or results_records is None:
        return (
            "—", "—", "—", "—",
            "Loading data…",
            _empty_figure(),
            build_recommended_table([]),
        )

    n_new       = n_new or 0
    baseline    = _get_baseline(distance_km, base_data, country)
    existing_df = pd.DataFrame(existing_records)
    results_df  = pd.DataFrame(results_records)
    n_existing  = len(existing_df)

    cur_pct    = get_access_pct(results_df, 0,     n_existing, baseline)
    access_pct = get_access_pct(results_df, n_new, n_existing, baseline)
    delta_pct  = round(access_pct - baseline, 2) if n_new > 0 else 0.0

    ca_total   = f"{n_existing:,}"
    ca_pct     = f"{cur_pct:.2f}%"
    om_n_new   = str(n_new)
    om_pct     = f"{access_pct:.2f}%"
    delta_label = (
        "current baseline"
        if n_new == 0
        else f"{format_delta(delta_pct)} vs baseline"
    )
    chart      = build_accessibility_chart(results_df, n_new, n_existing, baseline)
    table_rows = get_recommended_table_rows(
        results_df,
        n_new,
        baseline,
        country_population=cfg["population"],   # ← country-specific population
    )
    table = build_recommended_table(table_rows)

    return (ca_total, ca_pct, om_n_new, om_pct, delta_label, chart, table)


if __name__ == "__main__":
    app.run(debug=True)
