import dash_bootstrap_components as dbc
import pandas as pd
import json

from dash import (
    dcc,
    html,
    Dash,
    Input,
    Output,
    State,
    no_update,
)

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
        "https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,700&display=swap",
    ],
)

db = QueryService.get_instance()

# ── Inline styles ─────────────────────────────────────────────────────────────

PAGE_STYLE = {
    "backgroundColor": "#080D1A",
    "minHeight": "100vh",
    "fontFamily": "'DM Sans', sans-serif",
    "color": "#E2E8F0",
    "padding": "0",
    "margin": "0",
}

HEADER_STYLE = {
    "backgroundColor": "#080D1A",
    "borderBottom": "1px solid #182236",
    "padding": "18px 32px 14px",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "space-between",
}

CONTENT_STYLE = {
    "padding": "24px 32px",
    "backgroundColor": "#080D1A",
}

DIVIDER_STYLE = {
    "borderTop": "1px solid #182236",
    "margin": "0 32px",
}

MAP_IFRAME_STYLE = {
    "width": "100%",
    "height": "640px",
    "border": "none",
    "borderRadius": "14px",
}

MAP_WRAP_STYLE = {
    "border": "1px solid #182236",
    "borderRadius": "14px",
    "overflow": "hidden",
    "marginTop": "4px",
}

LEGEND_PILL_STYLE = {
    "display": "inline-flex",
    "alignItems": "center",
    "gap": "7px",
    "background": "#0C1625",
    "border": "1px solid #182236",
    "borderRadius": "99px",
    "padding": "6px 15px",
    "fontSize": "0.77rem",
    "color": "#64748B",
    "whiteSpace": "nowrap",
    "marginRight": "8px",
}

STATUS_STYLE = {
    "background": "linear-gradient(90deg, #080D1A, #0D1829, #080D1A)",
    "border": "1px solid #182236",
    "borderRadius": "10px",
    "padding": "9px 20px",
    "fontSize": "0.79rem",
    "color": "#3D5068",
    "textAlign": "center",
    "lineHeight": "1.55",
}

SLIDER_LABEL_STYLE = {
    "fontFamily": "'Space Mono', monospace",
    "fontSize": "0.72rem",
    "color": "#4A6080",
    "letterSpacing": "0.8px",
    "textTransform": "uppercase",
    "marginBottom": "6px",
}

FOOTER_STYLE = {
    "textAlign": "center",
    "fontFamily": "'Space Mono', monospace",
    "fontSize": "0.63rem",
    "color": "#182236",
    "letterSpacing": "0.9px",
    "padding": "14px 0 8px",
    "borderTop": "1px solid #0E1829",
    "marginTop": "20px",
}

# ── Legend dot helper ─────────────────────────────────────────────────────────

def legend_dot(bg, outline=None):
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


# ── App layout ────────────────────────────────────────────────────────────────

app.layout = html.Div(
    style=PAGE_STYLE,
    children=[

        # ── Data stores (populated once on load, never re-queried) ────────────
        dcc.Store(id="store-existing-facilities"),
        dcc.Store(id="store-accessibility-results"),

        # ── Header ────────────────────────────────────────────────────────────
        html.Div(
            style=HEADER_STYLE,
            children=[
                html.Div([
                    html.Div(
                        "🇿🇲  Zambia Health Access",
                        style={
                            "fontFamily": "'Space Mono', monospace",
                            "fontSize": "1.45rem",
                            "fontWeight": "700",
                            "color": "#F8FAFC",
                            "letterSpacing": "-0.4px",
                        },
                    ),
                    html.Div(
                        "Facility placement optimisation & population accessibility",
                        style={
                            "fontSize": "0.82rem",
                            "color": "#3D5068",
                            "marginTop": "3px",
                        },
                    ),
                ]),
                html.Div(
                    style={"minWidth": "320px"},
                    children=[
                        html.Div("NEW FACILITIES TO ADD", style=SLIDER_LABEL_STYLE),
                        dcc.Slider(
                            id="slider-new-facilities",
                            min=0,
                            max=MAX_NEW_FACILITIES,
                            step=1,
                            value=0,
                            marks={
                                0:  {"label": "0",  "style": {"color": "#475569", "fontSize": "0.72rem"}},
                                10: {"label": "10", "style": {"color": "#475569", "fontSize": "0.72rem"}},
                                20: {"label": "20", "style": {"color": "#475569", "fontSize": "0.72rem"}},
                                30: {"label": "30", "style": {"color": "#475569", "fontSize": "0.72rem"}},
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
                dbc.Row(
                    id="kpi-row",
                    className="g-3 mb-4",
                ),

                # ── Legend + status bar ───────────────────────────────────────
                dbc.Row(
                    className="mb-3 align-items-center",
                    children=[
                        dbc.Col(
                            width="auto",
                            children=html.Div(
                                style=LEGEND_PILL_STYLE,
                                children=[
                                    legend_dot("#F97316"),
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
                        "ZAMBIA · HEALTH FACILITY ACCESSIBILITY · DATABRICKS DATA APP"
                        "  |  POPULATION: WORLDPOP 2025 · FACILITIES: OPENSTREETMAP"
                        "  |  OPTIMISATION: ILP / GUROBI"
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
    # Guard: wait until both stores are populated
    if existing_records is None or results_records is None:
        loading_msg = "Loading data from Databricks…"
        return [], loading_msg, ""

    existing_df = pd.DataFrame(existing_records)
    results_df  = pd.DataFrame(results_records)

    n_existing  = len(existing_df)
    new_df      = get_new_facility_rows(results_df, n_new)
    access_pct  = get_access_pct(results_df, n_new, n_existing)
    delta_pct   = round(access_pct - BASELINE_ACCESS_PCT, 2) if n_new > 0 else 0.0
    total_fac   = n_existing + n_new

    # ── KPI cards ─────────────────────────────────────────────────────────────
    new_note = (
        "none selected — use slider" if n_new == 0
        else "optimally placed additions"
    )
    pct_note = (
        "current baseline" if n_new == 0
        else f"{format_delta(delta_pct)} vs baseline"
    )

    kpi_cards = [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Div(
                        dangerously_allow_html=True,
                        children=kpi_card(
                            label="Existing Facilities",
                            value=f"{n_existing:,}",
                            sub="health facilities in Zambia",
                            accent="#FB923C",
                        ),
                    )
                ),
                style={"background": "transparent", "border": "none", "padding": "0"},
            ),
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Div(
                        dangerously_allow_html=True,
                        children=kpi_card(
                            label="New Facilities",
                            value=str(n_new),
                            sub=new_note,
                            accent="#38BDF8",
                        ),
                    )
                ),
                style={"background": "transparent", "border": "none", "padding": "0"},
            ),
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Div(
                        dangerously_allow_html=True,
                        children=kpi_card(
                            label="Population Access",
                            value=f"{access_pct:.1f}%",
                            sub=pct_note,
                            accent="#34D399",
                        ),
                    )
                ),
                style={"background": "transparent", "border": "none", "padding": "0"},
            ),
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Div(
                        dangerously_allow_html=True,
                        children=kpi_card(
                            label="Total Facilities",
                            value=f"{total_fac:,}",
                            sub="after proposed additions",
                            accent="#94A3B8",
                        ),
                    )
                ),
                style={"background": "transparent", "border": "none", "padding": "0"},
            ),
        ),
    ]

    # ── Status bar text ───────────────────────────────────────────────────────
    if n_new == 0:
        status_text = (
            f"Displaying all {n_existing:,} existing facilities. "
            "Use the slider to simulate new placements and track accessibility gains."
        )
    else:
        status_text = (
            f"Showing {n_new} new facilities "
            f"(optimisation rows 1259–{1258 + n_new}). "
            f"Accessibility {BASELINE_ACCESS_PCT:.2f}% → {access_pct:.2f}% "
            f"({format_delta(delta_pct)} improvement)."
        )

    # ── Folium map HTML ───────────────────────────────────────────────────────
    map_html = get_map_html(existing_df, new_df)

    return kpi_cards, status_text, map_html


if __name__ == "__main__":
    app.run(debug=True)