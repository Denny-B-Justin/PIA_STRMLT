"""
app.py
------
PFM4CA Country Benchmarking Tool - Dash port.

Run with:  python app.py
Then open  http://127.0.0.1:8050

Set the MAPBOX_TOKEN environment variable to use real Mapbox raster/vector
styles (mapbox://styles/mapbox/light-v11), matching the original React app.
Without a token, maps still render using the open "carto-positron" style.
"""

import json
import warnings
from urllib.parse import parse_qs

import dash
from dash import Dash, dcc, html, Input, Output, State, ALL, ctx
import plotly.graph_objects as go

import queries as q
import utils as u

warnings.filterwarnings("ignore", category=DeprecationWarning)

app = Dash(__name__, suppress_callback_exceptions=True, title=u.BASE_TITLE)
server = app.server

# ══════════════════════════════════════════════════════════════════════════
# Asset URLs
# ══════════════════════════════════════════════════════════════════════════
# app.get_asset_url(...) must be called here, where `app` actually exists -
# utils.py has no Dash app instance and must never call it directly (that
# was the cause of the header's NameError). Resolve every image up front and
# hand the resulting URLs down into the layout builders.

LOGO_WHITE_URL = app.get_asset_url("cbd_logo_white.png")
# Placeholder - swap in the real filename once the hero image is added to
# /assets. Used by introduction_layout() below for the front-page banner.
HERO_BANNER_URL = app.get_asset_url("cbd_hero_banner.png")

# ══════════════════════════════════════════════════════════════════════════
# Static content
# ══════════════════════════════════════════════════════════════════════════

BENCHMARKS = [
    {
        "name": "Climate Change Institutional Indicators (GCCIIs)",
        "coverage": "Global",
        "source": "World Bank",
        "focus": "12 Indicators: law, coordination, long term strategy, national adaptation plan, fiscal "
                 "risk statements, local climate risk, budget guidelines, expenditure tracking, public "
                 "investment, SOE disclosure, sub-national strategies and risk assessments, environment in "
                 "procurement",
    },
    {
        "name": "GovTech Maturity Index: Core Government Systems Index (CGSI): Public Investment Management Systems",
        "coverage": "Global",
        "source": "World Bank",
        "focus": "I-14: Is there a Public Investment Management System (PIMS) in place? I-15: Is there a "
                 "government Open-Source Software (OSS) policy/action plan for public sector? I-17: Does "
                 "government have a national strategy on disruptive / innovative technologies? I-1: Is "
                 "there a cloud platform available for all government entities?",
    },
    {
        "name": "Infrastructure Efficient Frontier",
        "coverage": "Global",
        "source": "World Bank",
        "focus": "Based on the work of the Fiscal Policy Unit at the World Bank, the infrastructure "
                 "efficiency analysis uses eight output indicators following the methodology developed by "
                 "Herrera and Ouedraogo (2018) and Herrera, Isaka, and Ouedraogo (2025).",
    },
    {
        "name": "Climate Change Institutional Assessment (CCIA)",
        "coverage": "ECA Selected",
        "source": "World Bank",
        "focus": "74 indicators",
    },
    {
        "name": "Climate-informed PIM Indicators",
        "coverage": "ECA Selected (Western Balkans)",
        "source": "World Bank",
        "focus": "Policy (11), implementation (10), Climate (9)",
    },
    {
        "name": "Infrastructure Services Evaluation",
        "coverage": "Global",
        "source": "IMF Methodology, Updated Global Data",
        "focus": "Measures of infrastructure services such as road, rail, power, water, and digital access",
    },
    {
        "name": "Global Quality Infrastructure Index (GQII)",
        "coverage": "Global",
        "source": "WBG Methodology, Updated Global Data",
        "focus": "Measures of infrastructure services and quality of public investment",
    },
]

EF_CUSTOM_ORDER = q.EF_SHORT_NAME_ORDER


# ══════════════════════════════════════════════════════════════════════════
# Layouts
# ══════════════════════════════════════════════════════════════════════════

def introduction_layout(current_page):
    rows = []
    for b in BENCHMARKS:
        rows.append(
            html.Tr([
                html.Td(b["name"], className="bench-name"),
                html.Td(b["coverage"], className="bench-cell"),
                html.Td(b["source"], className="bench-cell"),
                html.Td(b["focus"], className="bench-focus"),
            ])
        )

    table = html.Table(
        className="benchmarks-table",
        children=[
            html.Thead(html.Tr([
                html.Th("Benchmarks"), html.Th("Coverage"), html.Th("Source"), html.Th("Focus"),
            ])),
            html.Tbody(rows),
        ],
    )

    main = html.Main(
        className="intro-main",
        children=html.Div(
            className="intro-content",
            children=[
                # html.Img(className="intro-hero-banner", alt="PFM4CA Country Benchmarking Tool"),
                html.H1("PFM4CA Country Benchmarking Tool", className="intro-title"),
                html.P(
                    "The Country Benchmarking Tool (CBT) helps visualize PFM4CA performance across a "
                    "curated set of global and regional measures. PFM4CA benchmarking typically can be "
                    "done through a single summary measure, as well as looking at sub-indicators. The "
                    "current CBT presents the selection of indicators set out below. Feel free to explore "
                    "the summary mappings, as well as to review country-specific indicators by hovering "
                    "over the maps!",
                    className="intro-desc",
                ),
                html.Div(table, className="table-scroll"),
            ],
        ),
    )

    return html.Div(
        className="page-shell",
        children=[
            u.build_header(current_page, LOGO_WHITE_URL),
            html.Div(className="body-shell", children=[u.build_home_nav_sidebar(current_page), main]),
        ],
    )


def _map_page_shell(current_page, sidebar_children, map_id, legend_id, popup_id):
    main = html.Main(
        className="map-main",
        children=html.Div(
            className="map-container",
            children=[
                dcc.Graph(
                    id=map_id,
                    className="map-graph",
                    style={"width": "100%", "height": "100%"},
                    config={"displayModeBar": False, "scrollZoom": True},
                    figure=go.Figure(),
                ),
                html.Div(id=legend_id),
                html.Div(id=popup_id, children=u.build_popup_panel(visible=False)),
                html.Div(
                    className="map-loading-overlay",
                    id=f"{map_id}-loading",
                    style={"display": "none"},
                ),
            ],
        ),
    )
    return html.Div(
        className="page-shell",
        children=[
            u.build_header(current_page, LOGO_WHITE_URL),
            html.Div(
                className="body-shell",
                children=[u.build_sub_nav_sidebar(sidebar_children), main],
            ),
        ],
    )


def gccii_layout(current_page):
    sidebar = [
        u.form_field("Region", u.styled_select("gccii-region", u.GLOBAL_REGIONS, u.GLOBAL_REGIONS[0])),
        u.info_blocks_section([
            ("Data Visualization", "Global Climate Change Institutional Indicators (GCCIIs), produced by "
                                    "the Climate Governance Program of the Prosperity Vertical Institutions "
                                    "Development"),
            ("Data Overview", "The current draft dataset for 2024 covers 12 indicators for 182 countries"),
            ("Explore", "Use the drop-down menu to focus on a World Bank Group Region, and click on the "
                        "country to see the detailed indicators"),
            ("Notes", "The indicators are quantified as 0 (no information/none), partial (0.5), and "
                      "present (1). The summary is the average of these scores."),
        ]),
    ]
    return _map_page_shell(current_page, sidebar, "gccii-map", "gccii-legend", "gccii-popup")


def gtmi_layout(current_page):
    sidebar = [
        u.form_field("Region", u.styled_select("gtmi-region", u.GLOBAL_REGIONS, u.GLOBAL_REGIONS[0])),
        u.form_field("Main Pillar", u.styled_select("gtmi-pillar", q.GTMI_PILLARS, "PIMS")),
        u.info_blocks_section([
            ("Data Visualization", "2022 Central Government (CG) GTMI survey data produced by the World "
                                    "Bank Group"),
            ("Data Overview", "The current draft dataset for 2024 covers 48 key indicators with 4 main "
                               "groups for 198 countries"),
            ("Explore", "Use the drop-down menu to focus on a World Bank Group Region, and click on the "
                        "country to see the detailed indicators"),
        ]),
    ]
    return _map_page_shell(current_page, sidebar, "gtmi-map", "gtmi-legend", "gtmi-popup")


def ccia_layout(current_page):
    pillars = ["Overall"] + q.ccia_pillars()
    sidebar = [
        u.form_field("Country Management Unit", u.styled_select("ccia-region", u.LOCAL_REGIONS, u.LOCAL_REGIONS[0])),
        u.form_field("Pillar", u.styled_select("ccia-pillar", pillars, "Overall")),
        u.info_blocks_section([
            ("Data Visualization", "Climate Change Institutional Assessment (CCIA), produced by the "
                                    "Climate Governance Program of the Prosperity Vertical Institutions "
                                    "Development"),
            ("Data Overview", "The current draft dataset for 2024 covers 74 indicators for 11 countries"),
            ("Explore", "Use the drop-down menu to focus on a World Bank Group Country Management Unit, "
                        "and click on the country to see the detailed indicators"),
            ("Notes", "The indicators are quantified based on the scale of 1 to 6. The summary is the "
                      "average of these scores."),
        ]),
    ]
    return _map_page_shell(current_page, sidebar, "ccia-map", "ccia-legend", "ccia-popup")


def infra_layout(current_page):
    sidebar = [
        u.form_field("Region", u.styled_select("infra-region", u.GLOBAL_REGIONS, u.GLOBAL_REGIONS[0])),
        u.info_blocks_section([
            ("Data Visualization", "Infrastructure Services Evaluation, produced by the Climate Governance "
                                    "Program of the Prosperity Vertical Institutions Development"),
            ("Data Overview", "The current draft dataset for 2019 covers 6 indicators for 220 countries"),
            ("Notes", "The Infrastructure gap is done using the gap between countries' scores and regional "
                      "average score of each indicator. Countries in which one or more scores are missing "
                      "are exempted from the calculation and shown in gray."),
        ]),
    ]
    return _map_page_shell(current_page, sidebar, "infra-map", "infra-legend", "infra-popup")


def piiag_layout(current_page):
    sections = ["Overall"] + q.piiag_sections()
    sidebar = [
        u.form_field("Country Management Unit", u.styled_select("piiag-region", u.LOCAL_REGIONS, u.LOCAL_REGIONS[0])),
        u.form_field("Section", u.styled_select("piiag-section", sections, "Overall")),
        u.info_blocks_section([
            ("Data Visualization", "ECA Public Infrastructure Investment and Asset Governance Tracker (PIIAG)"),
            ("Data Overview", "The current draft dataset for 2024 covers 29 indicators across 3 sections "
                               "for 6 countries"),
            ("Notes", "The indicators are quantified as 0 (no information/none), partial (0.5), and "
                      "present (1). The summary is the average of these scores."),
        ]),
    ]
    return _map_page_shell(current_page, sidebar, "piiag-map", "piiag-legend", "piiag-popup")


def pefa_layout(current_page):
    sidebar = [
        u.form_field("Region", u.styled_select("pefa-region", u.GLOBAL_REGIONS, u.GLOBAL_REGIONS[0])),
        u.form_field("Indicator", u.styled_select("pefa-indicator", q.PEFA_INDICATORS, q.PEFA_INDICATORS[0])),
        u.info_blocks_section([
            ("About PEFA", "Public Expenditure and Financial Accountability (PEFA) framework assesses the "
                            "strength of public financial management systems. Scores shown use the latest "
                            "assessment per country."),
            ("Indicators", [
                "PI-11 — Public Investment Management",
                "PI-11.3 — Project costing & budget alignment",
                "PI-11.4 — Investment project monitoring",
                "PI-12 — Public Asset Management",
                "PI-16 — Medium-term fiscal perspective",
            ]),
            ("Explore", "Select a region and indicator, then click a country to see all PI scores for "
                        "that assessment."),
        ]),
    ]
    return _map_page_shell(current_page, sidebar, "pefa-map", "pefa-legend", "pefa-popup")


def ef_layout(current_page):
    filters = q.ef_get_filters()
    methods = filters["methods"]
    samples = filters["samples"]

    sidebar = [
        u.info_blocks_section([
            ("Data Visualization", "Based on the work of the Fiscal Policy Unit at the World Bank, the "
                                    "infrastructure efficiency analysis uses eight output indicators "
                                    "following the methodology developed by Herrera and Ouedraogo (2018) "
                                    "and Herrera, Isaka, and Ouedraogo (2025)"),
            ("Data Overview", "The eight Indicators considered are Quality of overall infrastructure, "
                               "Transport infrastructure, roads, port infrastructure, air transport, "
                               "railroads, electricity supply, and the country scores on the World Bank's "
                               "Logistics Performance Index."),
            ("Explore", "Use the drop-down menu to focus on a country and click on the country to see the "
                        "graph. Maximum of 5 countries can be selected."),
            ("Notes", "Public investment per capita is treated as an input. Efficiency Scores focus on "
                      "technical efficiency based on non-parametric methods of Conditional DEA, Conditional "
                      "FDH, Bootstrapped DEA and Bootstrapped FDH and parametric method of Stochastic "
                      "frontier analysis."),
        ]),
    ]

    main = html.Main(
        className="ef-main",
        children=[
            html.H1("Infrastructure Efficiency Dashboard", className="ef-title"),
            html.Div(
                className="ef-controls-row",
                children=[
                    u.form_field("Method", u.styled_select("ef-method", methods, methods[0] if methods else None)),
                    html.Div(
                        className="ef-country-field",
                        children=[
                            html.Label("Country (ISO) — max 5", className="field-label"),
                            html.Div(id="ef-country-badges", className="ef-badges"),
                            u.form_field("", u.styled_select("ef-country-add", [], None, placeholder="Select a country...")),
                        ],
                    ),
                    u.form_field("Sample", u.styled_select("ef-sample", samples, samples[0] if samples else None)),
                ],
            ),
            html.Div(
                className="ef-chart-block",
                children=[
                    html.H2("Frontier Line Graph", className="ef-h2"),
                    html.P("Infrastructure Efficiency Frontier (DEA & FDH)", className="ef-sub"),
                    dcc.Graph(id="ef-frontier-graph", config={"displayModeBar": False}, figure=go.Figure()),
                ],
            ),
            html.Div(id="ef-bar-block"),
            dcc.Store(id="ef-selected-countries", data=[]),
        ],
    )

    return html.Div(
        className="page-shell",
        children=[
            u.build_header(current_page, LOGO_WHITE_URL),
            html.Div(className="body-shell", children=[u.build_sub_nav_sidebar(sidebar), main]),
        ],
    )


def not_found_layout(current_page):
    return html.Div(
        className="page-shell",
        children=[
            u.build_header(current_page, LOGO_WHITE_URL),
            html.Div(
                className="body-shell",
                children=html.Main(
                    className="intro-main",
                    children=html.Div(
                        className="intro-content",
                        children=[
                            html.H1("404 - Page Not Found", className="intro-title"),
                            html.P("The page you're looking for doesn't exist.", className="intro-desc"),
                            dcc.Link("← Back to Overview", href="/", className="back-link"),
                        ],
                    ),
                ),
            ),
        ],
    )


PAGE_BUILDERS = {
    "": introduction_layout,
    "gccii": gccii_layout,
    "gtmi": gtmi_layout,
    "ef": ef_layout,
    "ccia": ccia_layout,
    "infra": infra_layout,
    "piiag": piiag_layout,
    "pefa": pefa_layout,
}

# ══════════════════════════════════════════════════════════════════════════
# App shell / routing
# ══════════════════════════════════════════════════════════════════════════
# Routing is driven by the ?page=xxx query string rather than distinct
# paths (e.g. /gtmi). This is deliberate: Posit Connect deploys each app
# under its own path prefix (e.g. /content/<guid>/), and dcc.Location's
# "pathname" reflects that full real-world URL, so exact-string path
# matching like PAGE_BUILDERS.get("/gtmi") silently breaks in production
# (every route - including "/" - falls through to the 404 page). A query
# string tacked onto whatever the real base path happens to be keeps
# working regardless of where Connect mounts the app.

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content"),
])


def _get_page_key(search):
    """search: dcc.Location's raw query string, e.g. '?page=gtmi' or ''."""
    if not search:
        return ""
    qs = parse_qs(search.lstrip("?"))
    return qs.get("page", [""])[0]


@app.callback(Output("page-content", "children"), Input("url", "search"))
def render_page(search):
    current_page = _get_page_key(search)
    builder = PAGE_BUILDERS.get(current_page, not_found_layout)
    return builder(current_page)


app.clientside_callback(
    """
    function(search) {
        const titles = """ + json.dumps(u.PAGE_TITLES) + """;
        const base = """ + json.dumps(u.BASE_TITLE) + """;
        const params = new URLSearchParams(search || "");
        const page = params.get("page") || "";
        const subtitle = titles[page];
        document.title = subtitle ? (base + " - " + subtitle) : base;
        return "";
    }
    """,
    Output("page-content", "title"),
    Input("url", "search"),
)


# ══════════════════════════════════════════════════════════════════════════
# Generic map-page callback factory
# ══════════════════════════════════════════════════════════════════════════

def register_simple_map_page(map_id, legend_id, region_dropdown_id, data_fn, colors, mode,
                               legend_title, legend_labels, vmin=None, vmax=None, extra_dropdown_id=None):
    """
    Wires up a region-only (or region+one-more-dropdown) map page:
      Inputs  -> region dropdown value [+ extra dropdown value]
      Outputs -> map figure, legend content
    `data_fn(region)` or `data_fn(region, extra_value)` must return the
    country_data list of {"cntrCode","score","tooltip","popupRows"} dicts.
    """
    inputs = [Input(region_dropdown_id, "value")]
    if extra_dropdown_id:
        inputs.append(Input(extra_dropdown_id, "value"))

    def _callback(region, extra=None):
        if extra is not None:
            country_data = data_fn(region, extra)
        else:
            country_data = data_fn(region)
        fig = u.build_map_figure(country_data, region, colors, mode=mode, vmin=vmin, vmax=vmax)
        legend = u.build_legend(legend_title, legend_labels, colors)
        return fig, legend

    app.callback(
        Output(map_id, "figure"),
        Output(legend_id, "children"),
        *inputs,
    )(_callback)


def register_popup_callback_simple(map_id, popup_id, reset_inputs):
    """
    Wires up the click-to-show / X-to-close popup panel.
    `reset_inputs` is a list of Input(...) for the page's filter dropdowns -
    changing any of them clears the currently open popup (since it belongs to
    the previous filter state).
    """
    def _callback(click_data, _close_clicks, *_filters):
        triggered = ctx.triggered_id
        if triggered == "map-popup-close":
            return u.build_popup_panel(visible=False)
        if triggered == map_id and click_data and click_data.get("points"):
            point = click_data["points"][0]
            customdata = point.get("customdata")
            if not customdata:
                return u.build_popup_panel(visible=False)
            country_code, _tooltip, popup_json = customdata
            rows = json.loads(popup_json)
            if not rows:
                return u.build_popup_panel(visible=False)
            name = q.get_country_name_map().get(country_code, country_code)
            return u.build_popup_panel(country_name=name, rows=rows, visible=True)
        # filters changed (or initial load) -> hide any stale popup
        return u.build_popup_panel(visible=False)

    app.callback(
        Output(popup_id, "children"),
        Input(map_id, "clickData"),
        Input("map-popup-close", "n_clicks"),
        *reset_inputs,
        prevent_initial_call=False,
    )(_callback)


# ── GCCII ──────────────────────────────────────────────────────────────────

register_simple_map_page(
    "gccii-map", "gccii-legend", "gccii-region",
    data_fn=q.gccii_country_data,
    colors=u.HEX_CODES_5, mode="heatmap",
    legend_title="Average GCCII Score",
    legend_labels=["Low", "Med-Low", "Medium", "Med-High", "High"],
    vmin=0, vmax=1,
)
register_popup_callback_simple("gccii-map", "gccii-popup", [Input("gccii-region", "value")])


# ── GTMI ───────────────────────────────────────────────────────────────────

def _gtmi_data(region, pillar):
    return q.gtmi_country_data(region, pillar)


@app.callback(
    Output("gtmi-map", "figure"),
    Output("gtmi-legend", "children"),
    Input("gtmi-region", "value"),
    Input("gtmi-pillar", "value"),
)
def _update_gtmi(region, pillar):
    country_data = _gtmi_data(region, pillar)
    is_pims = pillar == "PIMS"
    if is_pims:
        fig = u.build_map_figure(country_data, region, u.HEX_CODES_3, mode="categorical")
        legend = u.build_legend(
            "PIMS Implementation Status",
            ["Not yet implemented", "PIMS under implementation", "PIMS Implemented"],
            u.HEX_CODES_3,
        )
    else:
        fig = u.build_map_figure(country_data, region, u.HEX_CODES_5, mode="heatmap", vmin=0, vmax=1)
        legend = u.build_legend(
            "Average GovTech Score",
            ["Low", "Med-Low", "Medium", "Med-High", "High"],
            u.HEX_CODES_5,
        )
    return fig, legend


register_popup_callback_simple("gtmi-map", "gtmi-popup", [Input("gtmi-region", "value"), Input("gtmi-pillar", "value")])


# ── CCIA ───────────────────────────────────────────────────────────────────

register_simple_map_page(
    "ccia-map", "ccia-legend", "ccia-region",
    data_fn=q.ccia_country_data,
    colors=u.HEX_CODES_5, mode="heatmap",
    legend_title="Average CCIA Score",
    legend_labels=["Low", "Med-Low", "Medium", "Med-High", "High"],
    vmin=1, vmax=6,
    extra_dropdown_id="ccia-pillar",
)
register_popup_callback_simple("ccia-map", "ccia-popup", [Input("ccia-region", "value"), Input("ccia-pillar", "value")])


# ── Infra ──────────────────────────────────────────────────────────────────

register_simple_map_page(
    "infra-map", "infra-legend", "infra-region",
    data_fn=q.infra_country_data,
    colors=u.HEX_CODES_5, mode="heatmap",
    legend_title="Infrastructure Gap Index",
    legend_labels=["Low", "Med-Low", "Medium", "Med-High", "High"],
    vmin=None, vmax=None,
)
register_popup_callback_simple("infra-map", "infra-popup", [Input("infra-region", "value")])


# ── PIIAG ──────────────────────────────────────────────────────────────────

register_simple_map_page(
    "piiag-map", "piiag-legend", "piiag-region",
    data_fn=q.piiag_country_data,
    colors=u.HEX_CODES_5, mode="heatmap",
    legend_title="Average PIIAG Score",
    legend_labels=["Low", "Med-Low", "Medium", "Med-High", "High"],
    vmin=1, vmax=6,
    extra_dropdown_id="piiag-section",
)
register_popup_callback_simple("piiag-map", "piiag-popup", [Input("piiag-region", "value"), Input("piiag-section", "value")])


# ── PEFA ───────────────────────────────────────────────────────────────────

GRADE_COLORS = [q.SCORE_COLOR_MAP[g] for g in q.GRADE_ORDER]


@app.callback(
    Output("pefa-map", "figure"),
    Output("pefa-legend", "children"),
    Input("pefa-region", "value"),
    Input("pefa-indicator", "value"),
)
def _update_pefa(region, indicator):
    country_data = q.pefa_country_data(indicator=indicator, framework="Annex 2011")
    fig = u.build_map_figure(country_data, region, GRADE_COLORS, mode="categorical")
    legend = u.build_legend(f"PEFA {indicator} Score", q.GRADE_ORDER, GRADE_COLORS)
    return fig, legend


register_popup_callback_simple("pefa-map", "pefa-popup", [Input("pefa-region", "value"), Input("pefa-indicator", "value")])


# ══════════════════════════════════════════════════════════════════════════
# EF (Infrastructure Efficiency) page callbacks
# ══════════════════════════════════════════════════════════════════════════

def _frontier_y(x, frontier):
    if not frontier:
        return None
    pts = sorted(frontier, key=lambda p: p["x"])
    if x <= pts[0]["x"]:
        return pts[0]["y"]
    if x >= pts[-1]["x"]:
        return pts[-1]["y"]
    for i in range(len(pts) - 1):
        if pts[i]["x"] <= x <= pts[i + 1]["x"]:
            span = pts[i + 1]["x"] - pts[i]["x"]
            t = (x - pts[i]["x"]) / span if span else 0
            return pts[i]["y"] + t * (pts[i + 1]["y"] - pts[i]["y"])
    return None


def _build_frontier_figure(selected_countries):
    frontier = q.ef_get_frontier()
    names = q.get_country_name_map()
    dea, fdh, scatter = frontier["dea"], frontier["fdh"], frontier["scatter"]

    fig = go.Figure()

    other = [p for p in scatter if p["iso"] not in selected_countries]
    fig.add_trace(go.Scatter(
        x=[p["x"] for p in other], y=[p["y"] for p in other],
        mode="markers", name="Other",
        marker=dict(color="#cccccc", size=8, opacity=0.6),
        customdata=[[p["iso"], names.get(p["iso"], p["iso"])] for p in other],
        hovertemplate="<b>%{customdata[1]}</b><br>Input: %{x:.3f}<br>Output: %{y:.3f}<extra></extra>",
    ))

    for i, iso in enumerate(selected_countries):
        pts = [p for p in scatter if p["iso"] == iso]
        color = u.COUNTRY_COLORS[i % len(u.COUNTRY_COLORS)]
        fig.add_trace(go.Scatter(
            x=[p["x"] for p in pts], y=[p["y"] for p in pts],
            mode="markers", name=iso, showlegend=False,
            marker=dict(color=color, size=11, line=dict(width=1, color="#1f2937")),
            customdata=[[p["iso"], names.get(p["iso"], p["iso"])] for p in pts],
            hovertemplate="<b>%{customdata[1]}</b><br>Input: %{x:.3f}<br>Output: %{y:.3f}<extra></extra>",
        ))

    if dea:
        dea_sorted = sorted(dea, key=lambda p: p["x"])
        fig.add_trace(go.Scatter(
            x=[p["x"] for p in dea_sorted], y=[p["y"] for p in dea_sorted],
            mode="lines", name="DEA (VRS) frontier",
            line=dict(color="#2ca02c", width=2),
        ))
    if fdh:
        fdh_sorted = sorted(fdh, key=lambda p: p["x"])
        fig.add_trace(go.Scatter(
            x=[p["x"] for p in fdh_sorted], y=[p["y"] for p in fdh_sorted],
            mode="lines", name="FDH frontier",
            line=dict(color="#1f77b4", width=2, dash="dash"),
        ))

    fig.update_layout(
        height=460,
        margin=dict(l=70, r=20, t=40, b=60),
        xaxis=dict(title="Public Investment per Capita (Log)", gridcolor="#f0f0f0"),
        yaxis=dict(title="Global Quality Infrastructure Index", gridcolor="#f0f0f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter, sans-serif"),
    )
    return fig


def _build_bar_figure(selected_countries, method, sample):
    if not selected_countries:
        return None
    df = q.ef_get_scores(method=method, sample=sample, isos=selected_countries)
    if df.empty:
        return None

    by_var = {}
    for _, row in df.iterrows():
        short_name = row["short_name"] or row.get("varname", "")
        by_var.setdefault(short_name, {})[row["ISO"]] = row["score"]

    def sort_key(name):
        try:
            return EF_CUSTOM_ORDER.index(name)
        except ValueError:
            return 999

    names_sorted = sorted(by_var.keys(), key=sort_key)

    fig = go.Figure()
    for i, iso in enumerate(selected_countries):
        color = u.COUNTRY_COLORS[i % len(u.COUNTRY_COLORS)]
        y_vals = [by_var[n].get(iso) for n in names_sorted]
        fig.add_trace(go.Bar(x=names_sorted, y=y_vals, name=iso, marker_color=color))

    fig.update_layout(
        height=480,
        margin=dict(l=55, r=20, t=40, b=90),
        yaxis=dict(title="Infrastructure Score", gridcolor="#f0f0f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        barmode="group",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


@app.callback(
    Output("ef-selected-countries", "data"),
    Output("ef-country-add", "value"),
    Input("ef-country-add", "value"),
    Input({"type": "ef-remove", "iso": ALL}, "n_clicks"),
    State("ef-selected-countries", "data"),
    prevent_initial_call=True,
)
def _update_selected_countries(added_iso, _remove_clicks, current):
    current = current or []
    triggered = ctx.triggered_id

    if triggered == "ef-country-add":
        if added_iso and added_iso not in current and len(current) < 5:
            current = current + [added_iso]
        return current, None

    if isinstance(triggered, dict) and triggered.get("type") == "ef-remove":
        iso = triggered.get("iso")
        current = [c for c in current if c != iso]
        return current, None

    return current, None


@app.callback(
    Output("ef-country-badges", "children"),
    Output("ef-country-add", "options"),
    Input("ef-selected-countries", "data"),
)
def _render_badges(selected):
    selected = selected or []
    filters = q.ef_get_filters()
    all_countries = filters["countries"]

    badges = []
    for i, iso in enumerate(selected):
        color = u.COUNTRY_COLORS[i % len(u.COUNTRY_COLORS)]
        badges.append(
            html.Span(
                [iso, html.Button("\u00d7", id={"type": "ef-remove", "iso": iso}, className="badge-remove", n_clicks=0)],
                className="country-badge",
                style={"backgroundColor": color},
            )
        )

    remaining = [c for c in all_countries if c not in selected]
    options = [{"label": c, "value": c} for c in remaining]
    return badges, options


@app.callback(
    Output("ef-frontier-graph", "figure"),
    Input("ef-selected-countries", "data"),
)
def _update_frontier(selected):
    return _build_frontier_figure(selected or [])


@app.callback(
    Output("ef-bar-block", "children"),
    Input("ef-selected-countries", "data"),
    Input("ef-method", "value"),
    Input("ef-sample", "value"),
)
def _update_bar_block(selected, method, sample):
    selected = selected or []
    if not selected:
        return None
    fig = _build_bar_figure(selected, method, sample)
    if fig is None:
        return None
    return [
        html.H2(f"Data Components by Variable: {method} | {sample}", className="ef-h2"),
        dcc.Graph(figure=fig, config={"displayModeBar": False}),
    ]


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)