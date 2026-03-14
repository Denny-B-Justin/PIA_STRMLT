"""
app.py
Zambia Health Access – Facility Placement Optimisation Dashboard
Trial version: data is read from CSV files instead of Databricks.

Run:
    pip install dash dash-bootstrap-components folium pandas flask
    python app.py
"""

import pandas as pd

from dash import (
    dcc,
    html,
    Dash,
    Input,
    Output,
    State,
    no_update,
)
import dash_bootstrap_components as dbc

from queries import QueryService
from server import server
from utils import (
    get_map_html,
    get_new_facility_rows,
    get_access_pct,
    format_delta,
    kpi_card,
)
from constants import (
    BASELINE_ACCESS_PCT,
    MAX_NEW_FACILITIES,
)

# ── Dash app ──────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        # Space Mono  — monospace figures & labels
        # DM Sans     — clean readable body text
        "https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&"
        "family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,700&display=swap",
    ],
)

db = QueryService.get_instance()


# ── Design tokens (all colours / sizes in one place) ─────────────────────────

BG_BASE     = "#080D1A"   # page background
BG_CARD     = "#0C1625"   # card / panel background
BG_CARD2    = "#101E30"   # card gradient end
BORDER      = "#182236"   # subtle borders
TEXT_HI     = "#E2E8F0"   # high-emphasis text
TEXT_MID    = "#64748B"   # medium-emphasis text
TEXT_LO     = "#3D5068"   # low-emphasis / labels

ACC_ORANGE  = "#F97316"   # existing facilities
ACC_BLUE    = "#38BDF8"   # new / proposed facilities
ACC_GREEN   = "#34D399"   # positive metrics / accessibility
ACC_SLATE   = "#94A3B8"   # neutral / totals

FONT_MONO   = "'Space Mono', monospace"
FONT_BODY   = "'DM Sans', sans-serif"


# ── Inline style dictionaries ─────────────────────────────────────────────────

PAGE_STYLE = {
    "backgroundColor": BG_BASE,
    "minHeight": "100vh",
    "fontFamily": FONT_BODY,
    "color": TEXT_HI,
    "padding": "0",
    "margin": "0",
}

HEADER_STYLE = {
    "backgroundColor": BG_BASE,
    "borderBottom": f"1px solid {BORDER}",
    "padding": "20px 32px 16px",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "space-between",
    "gap": "32px",
    "flexWrap": "wrap",
}

BADGE_STYLE = {
    "display": "inline-block",
    "background": f"linear-gradient(135deg, {ACC_ORANGE}22, {ACC_BLUE}22)",
    "border": f"1px solid {ACC_ORANGE}44",
    "borderRadius": "6px",
    "padding": "3px 10px",
    "fontFamily": FONT_MONO,
    "fontSize": "0.6rem",
    "color": ACC_ORANGE,
    "letterSpacing": "1.2px",
    "textTransform": "uppercase",
    "marginBottom": "6px",
}

CONTENT_STYLE = {
    "padding": "24px 32px",
    "backgroundColor": BG_BASE,
}

DIVIDER_STYLE = {
    "borderTop": f"1px solid {BORDER}",
    "margin": "0",
}

MAP_IFRAME_STYLE = {
    "width": "100%",
    "height": "600px",
    "border": "none",
    "borderRadius": "14px",
}

MAP_WRAP_STYLE = {
    "border": f"1px solid {BORDER}",
    "borderRadius": "14px",
    "overflow": "hidden",
    "marginTop": "4px",
}

LEGEND_PILL_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "7px",
    "background": BG_CARD,
    "border": f"1px solid {BORDER}",
    "borderRadius": "99px",
    "padding": "6px 15px",
    "fontSize": "0.77rem",
    "color": TEXT_MID,
    "whiteSpace": "nowrap",
    "marginRight": "8px",
}

STATUS_STYLE = {
    "background": f"linear-gradient(90deg, {BG_BASE}, #0D1829, {BG_BASE})",
    "border": f"1px solid {BORDER}",
    "borderRadius": "10px",
    "padding": "9px 20px",
    "fontSize": "0.79rem",
    "color": TEXT_LO,
    "textAlign": "center",
    "lineHeight": "1.55",
}

SLIDER_LABEL_STYLE = {
    "fontFamily": FONT_MONO,
    "fontSize": "0.68rem",
    "color": TEXT_LO,
    "letterSpacing": "1px",
    "textTransform": "uppercase",
    "marginBottom": "8px",
}

SECTION_LABEL_STYLE = {
    "fontFamily": FONT_MONO,
    "fontSize": "0.63rem",
    "color": TEXT_LO,
    "letterSpacing": "1.3px",
    "textTransform": "uppercase",
    "marginBottom": "10px",
    "borderBottom": f"1px solid {BORDER}",
    "paddingBottom": "6px",
}

FOOTER_STYLE = {
    "textAlign": "center",
    "fontFamily": FONT_MONO,
    "fontSize": "0.6rem",
    "color": "#111E30",
    "letterSpacing": "0.9px",
    "padding": "14px 0 8px",
    "borderTop": f"1px solid #0E1829",
    "marginTop": "20px",
}

# ── Reusable component helpers ────────────────────────────────────────────────

def legend_dot(bg: str, outline: str | None = None) -> html.Span:
    style = {
        "width": "11px",
        "height": "11px",
        "borderRadius": "50%",
        "flexShrink": "0",
        "display": "inline-block",
        "backgroundColor": bg,
    }
    if outline:
        style["outline"] = f"2.5px solid {outline}"
    return html.Span(style=style)


def section_label(text: str) -> html.Div:
    return html.Div(text, style=SECTION_LABEL_STYLE)


# ── App layout ────────────────────────────────────────────────────────────────

app.layout = html.Div(
    style=PAGE_STYLE,
    children=[

        # ── Data stores (populated once on load) ──────────────────────────────
        dcc.Store(id="store-existing-facilities"),
        dcc.Store(id="store-accessibility-results"),

        # ── Header ────────────────────────────────────────────────────────────
        html.Div(
            style=HEADER_STYLE,
            children=[

                # Brand block
                html.Div([
                    html.Div("TRIAL  ·  CSV DATA MODE", style=BADGE_STYLE),
                    html.Div(
                        "🇿🇲  Zambia Health Access",
                        style={
                            "fontFamily": FONT_MONO,
                            "fontSize": "1.4rem",
                            "fontWeight": "700",
                            "color": "#F8FAFC",
                            "letterSpacing": "-0.4px",
                            "lineHeight": "1.2",
                        },
                    ),
                    html.Div(
                        "Facility placement optimisation & population accessibility",
                        style={
                            "fontSize": "0.82rem",
                            "color": TEXT_LO,
                            "marginTop": "4px",
                        },
                    ),
                ]),

                # Slider block
                html.Div(
                    style={"minWidth": "340px", "flex": "1", "maxWidth": "480px"},
                    children=[
                        html.Div("New facilities to add", style=SLIDER_LABEL_STYLE),
                        dcc.Slider(
                            id="slider-new-facilities",
                            min=0,
                            max=MAX_NEW_FACILITIES,
                            step=1,
                            value=0,
                            marks={
                                0:  {"label": "0",  "style": {"color": TEXT_LO, "fontSize": "0.68rem"}},
                                10: {"label": "10", "style": {"color": TEXT_LO, "fontSize": "0.68rem"}},
                                20: {"label": "20", "style": {"color": TEXT_LO, "fontSize": "0.68rem"}},
                                30: {"label": "30", "style": {"color": TEXT_LO, "fontSize": "0.68rem"}},
                            },
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ],
                ),
            ],
        ),

        html.Hr(style=DIVIDER_STYLE),

        # ── Main content ──────────────────────────────────────────────────────
        html.Div(
            style=CONTENT_STYLE,
            children=[

                # ── KPI row ───────────────────────────────────────────────────
                section_label("Key Metrics"),
                dbc.Row(id="kpi-row", className="g-3 mb-4"),

                # ── Legend + status ───────────────────────────────────────────
                dbc.Row(
                    className="mb-3 align-items-center",
                    children=[
                        dbc.Col(
                            width="auto",
                            children=html.Div(
                                style=LEGEND_PILL_STYLE,
                                children=[
                                    legend_dot(ACC_ORANGE),
                                    html.Span("Existing facility"),
                                ],
                            ),
                        ),
                        dbc.Col(
                            width="auto",
                            children=html.Div(
                                style=LEGEND_PILL_STYLE,
                                children=[
                                    legend_dot("#FFFFFF", outline="#0EA5E9"),
                                    html.Span("Proposed new facility"),
                                ],
                            ),
                        ),
                        dbc.Col(
                            html.Div(id="status-bar", style=STATUS_STYLE),
                        ),
                    ],
                ),

                # ── Map ───────────────────────────────────────────────────────
                section_label("Facility Map — Zambia"),
                html.Div(
                    style=MAP_WRAP_STYLE,
                    children=html.Iframe(
                        id="map-iframe",
                        style=MAP_IFRAME_STYLE,
                    ),
                ),

                # ── Footer ────────────────────────────────────────────────────
                html.Div(
                    style=FOOTER_STYLE,
                    children=(
                        "ZAMBIA · HEALTH FACILITY ACCESSIBILITY  "
                        "|  POPULATION: WORLDPOP 2025 · FACILITIES: OPENSTREETMAP  "
                        "|  OPTIMISATION: ILP / GUROBI  "
                        "|  DATA: SAMPLE CSV (TRIAL MODE)"
                    ),
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
    Output("kpi-row", "children"),
    Output("status-bar", "children"),
    Output("map-iframe", "srcDoc"),
    Input("slider-new-facilities", "value"),
    Input("store-existing-facilities", "data"),
    Input("store-accessibility-results", "data"),
)
def update_dashboard(n_new, existing_records, results_records):
    """
    Master callback: re-renders KPI cards, status bar, and Folium map
    whenever the slider changes or data finishes loading.
    """
    if existing_records is None or results_records is None:
        return [], "Loading data…", ""

    existing_df = pd.DataFrame(existing_records)
    results_df  = pd.DataFrame(results_records)

    n_existing  = len(existing_df)
    new_df      = get_new_facility_rows(results_df, n_new)
    access_pct  = get_access_pct(results_df, n_new, n_existing)
    delta_pct   = round(access_pct - BASELINE_ACCESS_PCT, 2) if n_new > 0 else 0.0
    total_fac   = n_existing + n_new

    # ── KPI label / note strings ──────────────────────────────────────────────
    new_note = (
        "none selected — use slider" if n_new == 0
        else "optimally placed additions"
    )
    pct_note = (
        "current baseline" if n_new == 0
        else f"{format_delta(delta_pct)} vs baseline"
    )


    # ── KPI cards ─────────────────────────────────────────────────────────────
    kpi_cards = [
        dbc.Col(kpi_card(
            label="Existing Facilities",
            value=f"{n_existing:,}",
            sub="health facilities in Zambia",
            accent=ACC_ORANGE,
        )),
        dbc.Col(kpi_card(
            label="New Facilities",
            value=str(n_new),
            sub=new_note,
            accent=ACC_BLUE,
        )),
        dbc.Col(kpi_card(
            label="Population Access",
            value=f"{access_pct:.1f}%",
            sub=pct_note,
            accent=ACC_GREEN,
            progress=access_pct,
        )),
        dbc.Col(kpi_card(
            label="Total Facilities",
            value=f"{total_fac:,}",
            sub="after proposed additions",
            accent=ACC_SLATE,
        )),
    ]

    # ── Status bar text ───────────────────────────────────────────────────────
    if n_new == 0:
        status_text = (
            f"Displaying all {n_existing:,} existing facilities. "
            "Use the slider above to simulate new placements and track accessibility gains."
        )
    else:
        status_text = (
            f"Showing {n_new} new proposed facilit{'y' if n_new == 1 else 'ies'}. "
            f"Accessibility {BASELINE_ACCESS_PCT:.2f}% → {access_pct:.2f}% "
            f"({format_delta(delta_pct)} improvement)."
        )

    # ── Folium map HTML ───────────────────────────────────────────────────────
    map_html = get_map_html(existing_df, new_df)

    return kpi_cards, status_text, map_html


if __name__ == "__main__":
    app.run(debug=True)