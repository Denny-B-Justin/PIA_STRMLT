"""
utils.py
--------
Presentation-layer helpers for the Dash port of the PFM4CA Country
Benchmarking Tool: design constants, color/bucket math for the choropleth
maps, the Mapbox figure builder, and reusable layout builders (header, nav
sidebar, legend, click-popup, styled dropdown) that every page shares.

Nothing in here talks to a database or CSV file directly - that's all in
queries.py. This module is purely "given some already-computed data, build
the Dash component / Plotly figure that displays it".
"""

import json
import os

from dash import html, dcc

import queries as q

# ── Brand / layout constants ─────────────────────────────────────────────────

HEADER_BG = "#021420"
SIDEBAR_BG = "#EBEEF5"
ACCENT_BLUE = "#4472C4"
NAV_ACTIVE = "#374696"
NAV_INACTIVE = "#8c8c8c"

BASE_TITLE = "PFM4CA Country Benchmarking Tool"

# ── Region lists (order matters - first entry is the default selection) ──────

GLOBAL_REGIONS = [
    "Europe and Central Asia",
    "South Asia",
    "Middle East and North Africa",
    "East Asia & Pacific",
    "Western and Central Africa",
    "Eastern and South Africa",
    "Latin and Central America",
    "North America",
]

LOCAL_REGIONS = [
    "Western Balkans 6",
    "Central Asia",
    "European Union 27",
]

ZOOM_POINTS = {
    "Western Balkans 6": (43.800326, 21.709443),
    "Central Asia": (44.503016, 67.239120),
    "European Union 27": (48.132158, 14.635656),
    "Europe and Central Asia": (48.258602, 16.535900),
    "East Asia & Pacific": (13.8, 125.7),
    "Latin and Central America": (-14.607537, -54.609775),
    "South Asia": (27.62, 90.53),
    "Eastern and South Africa": (7.05, 44.80),
    "Western and Central Africa": (23.80, 3.3),
    "Middle East and North Africa": (30.099478, 30.214933),
    "North America": (44.891333, -97.795865),
}

HEX_CODES_5 = ["#d61f1f", "#FF8C01", "#ffe733", "#7BB662", "#024e1b"]
HEX_CODES_3 = ["#d61f1f", "#ffe733", "#024e1b"]
NO_DATA_COLOR = "#cccccc"

COUNTRY_COLORS = ["#4345aa", "#64cbd6", "#f26b23", "#37b37f", "#3675b7"]

PAGE_TITLES = {
    "/": "Overview",
    "/gccii": "GCCII",
    "/gtmi": "GTMI",
    "/ef": "Infrastructure Efficiency",
    "/ccia": "CCIA",
    "/infra": "Infrastructure",
    "/piiag": "PIIAG",
    "/pefa": "PEFA",
}


def get_mapbox_token() -> str:
    return os.environ.get("MAPBOX_TOKEN", "")


def get_mapbox_style() -> str:
    return "mapbox://styles/mapbox/light-v11" if get_mapbox_token() else "carto-positron"


# ── Color bucket math (mirrors constants.ts getScoreColor5 / categorical) ────

def heatmap_bucket(score, vmin, vmax):
    """0-4 bucket index for a continuous score, or None if score is missing."""
    if score is None:
        return None
    if vmax == vmin:
        return 2
    normalized = (score - vmin) / (vmax - vmin)
    if normalized < 0.2:
        return 0
    if normalized < 0.4:
        return 1
    if normalized < 0.6:
        return 2
    if normalized < 0.8:
        return 3
    return 4


def categorical_bucket(score, n_categories):
    """Direct integer bucket for an already-categorical score (e.g. grade index)."""
    if score is None:
        return None
    idx = int(round(score))
    return max(0, min(n_categories - 1, idx))


def _discrete_colorscale(colors):
    """
    Build a Plotly stepped colorscale with len(colors) equal-width bands.
    Paired with z-values offset to the *center* of each band (see build_map_figure)
    so every point lands cleanly inside its band regardless of float precision.
    """
    n = len(colors)
    scale = []
    for i, c in enumerate(colors):
        scale.append([i / n, c])
        scale.append([(i + 1) / n, c])
    return scale


# ── Figure builder ────────────────────────────────────────────────────────────

def build_map_figure(country_data, region, colors, mode="heatmap", vmin=None, vmax=None):
    """
    country_data: list of {"cntrCode", "score", "tooltip", "popupRows"} dicts
    mode: "heatmap" (continuous, bucketed into 5 bands) or "categorical"
          (score is already a 0..len(colors)-1 index)
    vmin/vmax: for heatmap mode only. If omitted, computed from the data itself
               (mirrors the RegionMap.tsx default when no explicit range is passed).
    """
    import plotly.graph_objects as go

    geojson = q.load_world_geojson()

    if mode == "heatmap" and (vmin is None or vmax is None):
        valid = [d["score"] for d in country_data if d.get("score") is not None]
        vmin = vmin if vmin is not None else (min(valid) if valid else 0)
        vmax = vmax if vmax is not None else (max(valid) if valid else 1)

    n_colors = len(colors)
    all_colors = list(colors) + [NO_DATA_COLOR]
    colorscale = _discrete_colorscale(all_colors)

    locations, z, opacity, customdata = [], [], [], []
    for d in country_data:
        score = d.get("score")
        if mode == "heatmap":
            bucket = heatmap_bucket(score, vmin, vmax)
        else:
            bucket = categorical_bucket(score, n_colors)

        band = bucket if bucket is not None else n_colors  # last band = "no data"
        locations.append(d["cntrCode"])
        z.append(band + 0.5)  # center of its band -> immune to float edge cases
        opacity.append(0.82 if bucket is not None else 0.18)
        customdata.append([d["cntrCode"], d.get("tooltip", d["cntrCode"]), json.dumps(d.get("popupRows", []))])

    zoom_point = ZOOM_POINTS.get(region, (20, 10))
    token = get_mapbox_token()

    fig = go.Figure(
        go.Choroplethmapbox(
            geojson=geojson,
            locations=locations,
            z=z,
            featureidkey="properties.iso_a3",
            colorscale=colorscale,
            zmin=0,
            zmax=n_colors + 1,
            showscale=False,
            marker=dict(opacity=opacity, line=dict(width=0.6, color="#ffffff")),
            customdata=customdata,
            hovertemplate="%{customdata[1]}<extra></extra>",
            below="",
        )
    )
    fig.update_layout(
        mapbox=dict(
            style=get_mapbox_style(),
            accesstoken=token if token else None,
            center={"lat": zoom_point[0], "lon": zoom_point[1]},
            zoom=3.5,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white",
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter, sans-serif", align="left"),
        uirevision="keep",
    )
    return fig


# ── Legend / popup builders ───────────────────────────────────────────────────

def build_legend(title, labels, colors, show_no_data=True):
    swatches = []
    for label, color in zip(labels, colors):
        swatches.append(
            html.Div(
                className="legend-row",
                children=[
                    html.Div(className="legend-swatch", style={"backgroundColor": color}),
                    html.Span(label),
                ],
            )
        )
    if show_no_data:
        swatches.append(
            html.Div(
                className="legend-row",
                children=[
                    html.Div(className="legend-swatch", style={"backgroundColor": NO_DATA_COLOR}),
                    html.Span("No data"),
                ],
            )
        )
    return html.Div(
        className="map-legend",
        children=[html.P(title, className="map-legend-title")] + swatches,
    )


def build_popup_panel(country_name=None, rows=None, visible=False):
    """
    Click-popup panel shown top-right of the map with per-indicator detail.
    The close button keeps a stable id and is always present in the DOM
    (only the outer wrapper's display is toggled) so the Dash callback that
    listens on it never targets a missing component.
    """
    rows = rows or []
    body_rows = [
        html.Tr([
            html.Td(country_name or "", className="popup-td popup-td-country"),
            html.Td(r.get("indicator", ""), className="popup-td"),
            html.Td(
                f"{r['score']:.2f}" if isinstance(r.get("score"), (int, float)) else str(r.get("score", "")),
                className="popup-td popup-td-score",
            ),
        ])
        for r in rows
    ]

    return html.Div(
        className="map-popup",
        style={"display": "flex" if (visible and country_name) else "none"},
        children=[
            html.Div(
                className="map-popup-header",
                children=[
                    html.H3(country_name or "", className="map-popup-title"),
                    html.Button("\u00d7", id="map-popup-close", className="map-popup-close", n_clicks=0),
                ],
            ),
            html.Div(
                className="map-popup-body",
                children=html.Table(
                    className="popup-table",
                    children=[
                        html.Thead(html.Tr([
                            html.Th("Country", className="popup-th"),
                            html.Th("Indicator", className="popup-th"),
                            html.Th("Score", className="popup-th popup-th-right"),
                        ])),
                        html.Tbody(body_rows),
                    ],
                ),
            ),
        ],
    )


# ── Header / Nav sidebar ──────────────────────────────────────────────────────

NAV_SECTIONS = [
    {
        "label": "Global Datasets",
        "links": [
            {"label": "Climate Change Institutional Indicators", "href": "/gccii"},
            {"label": "GovTech Maturity Index", "href": "/gtmi"},
            {"label": "Infra Efficiency", "href": "/ef"},
            {"label": "PEFA PI-11/12/16", "href": "/pefa"},
        ],
    },
    {
        "label": "Local Datasets",
        "links": [
            {"label": "CCIA", "href": "/ccia"},
            {"label": "Infrastructure", "href": "/infra"},
            {"label": "PIIAG", "href": "/piiag"},
        ],
    },
]


def build_header(pathname="/"):
    return html.Header(
        className="app-header",
        children=[
            dcc.Link(
                html.Img(src="/assets/cbd_logo_white.png", className="header-logo"),
                href="/",
                className="header-logo-link",
            ),
            html.Div(className="header-divider"),
            html.Nav(
                className="header-nav",
                children=[
                    dcc.Link(
                        "Home",
                        href="/",
                        className="header-nav-link" + (" active" if pathname == "/" else ""),
                    ),
                    html.A(
                        "Release Notes",
                        href="https://pim-pam.net/cbd-release-notes/",
                        target="_blank",
                        rel="noopener noreferrer",
                        className="header-nav-link",
                    ),
                ],
            ),
            html.Div(
                className="header-brand",
                children=[
                    html.P("Part of", className="header-brand-sub"),
                    html.A(
                        "PIM-PAM.net",
                        href="https://pim-pam.net",
                        target="_blank",
                        rel="noopener noreferrer",
                        className="header-brand-link",
                    ),
                ],
            ),
        ],
    )


def build_home_nav_sidebar(pathname="/"):
    """The Introduction page's sidebar: two cards of dataset links."""
    sections = []
    for section in NAV_SECTIONS:
        links = []
        for link in section["links"]:
            is_active = pathname == link["href"]
            links.append(
                dcc.Link(
                    link["label"],
                    href=link["href"],
                    className="nav-link" + (" active" if is_active else ""),
                )
            )
        sections.append(
            html.Div(
                className="nav-section-card",
                children=[
                    html.Div(section["label"], className="nav-section-title"),
                    html.Div(links, className="nav-section-links"),
                ],
            )
        )
    return html.Aside(sections, className="nav-sidebar")


def build_sub_nav_sidebar(children):
    """A dataset page's sidebar: back-link + page-specific controls."""
    return html.Aside(
        className="nav-sidebar",
        children=[
            html.Div(
                dcc.Link(
                    ["\u2190 Back To Overview"],
                    href="/",
                    className="back-link",
                ),
                className="back-link-wrap",
            ),
            html.Div(children, className="sub-sidebar-content"),
        ],
    )


# ── Small form / info-block helpers ──────────────────────────────────────────

def styled_select(select_id, options, value, placeholder=None):
    """
    A dcc.Dropdown themed via CSS (see assets/style.css) to match the
    original app's compact native <select> look: white background, gray
    border, 38px tall, small bold text, blue focus ring.
    """
    return html.Div(
        className="select-wrapper",
        children=[
            dcc.Dropdown(
                id=select_id,
                options=[{"label": o, "value": o} for o in options],
                value=value,
                clearable=False,
                searchable=False,
                placeholder=placeholder or "",
                className="select-control",
            )
        ],
    )


def form_field(label, select_component):
    children = ([html.Label(label, className="field-label")] if label else []) + [select_component]
    return html.Div(children, className="field-group")


def info_block(title, text):
    """
    text: a string -> rendered as a single <p> (unchanged behavior), or
          a list of strings -> rendered as a bulleted <ul><li>...</li></ul>.
    """
    if isinstance(text, (list, tuple)):
        body = html.Ul(
            [html.Li(item, className="info-list-item") for item in text],
            className="info-list",
        )
    else:
        body = html.P(text, className="info-text")
    return html.Div([html.H4(title, className="info-title"), body], className="info-block")


def info_blocks_section(blocks):
    """blocks: list of (title, text) tuples -> the bordered stack under the controls."""
    return html.Div([info_block(t, x) for t, x in blocks], className="info-section")
