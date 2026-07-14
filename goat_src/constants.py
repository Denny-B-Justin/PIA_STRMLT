"""
GoAT — Governance Operations Analytics Tool
Global constants and configuration.

Single source of truth for table names, column identifiers,
chart colour sequences, and Plotly layout defaults.
"""

from __future__ import annotations
import os

# ── App metadata ───────────────────────────────────────────────────────────────
APP_TITLE = "Governance Operations Analytics Tool (GoAT)"
APP_ICON  = "📊"

# ── Unity Catalog source tables ────────────────────────────────────────────────
# Backtick-quoted because the table name starts with a digit.
GOAT_TABLE      = "`prd_mega`.`sgpbpi163`.`2b_overall_goat_df`"
HIERARCHY_TABLE = "`prd_mega`.`sgpbpi163`.`0c_hierarchy_table_goat`"

# ── Query cache tuning ─────────────────────────────────────────────────────────
QUERY_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "300"))
QUERY_CACHE_MAX_ENTRIES = int(os.getenv("QUERY_CACHE_MAX_ENTRIES", "256"))

# ── Column names — 1b_overall_goat_df ─────────────────────────────────────────
COL_PROJ_ID        = "PROJ_ID"
COL_PROJ_NAME      = "PROJ_DISPLAY_NAME"
COL_APPRVL_FY      = "PROJ_APPRVL_FY"
COL_PROJ_OBJ       = "PROJ_DEV_OBJECTIVE_DESC"
COL_PROJ_STAT      = "PROJ_STAT_NAME"
COL_LEND_INSTR     = "LNDNG_INSTR_LONG_NAME"
COL_REGION         = "RGN_NAME"
COL_HIERARCHY      = "hierarchy_name"
COL_IS_HIER        = "Ishierarchy_present"
COL_IS_HIER_YES    = "Yes"
COL_VALID_HIER     = "Valid_Hierarchy"          # "True" / "False" (string)
COL_COUNTRY        = "CNTRY_SHORT_NAME"
COL_DLI            = "DLI"
# COL_DLR           = "DLR"

# ── Keyword-searchable text columns (in 1b_overall_goat_df) ───────────────────
# Order matters: checked left-to-right; all five must exist in the table.
KEYWORD_SEARCH_COLUMNS: list[str] = [
    "Indicators",
    "PriorActions",
    "PROJ_DEV_OBJECTIVE_DESC",
    "Components",
    "DLI,"
]

# ── Column names — 0c_hierarchy_table_goat ────────────────────────────────────
COL_HIER_SHORT     = "hierarchy"           # short code, e.g. "PIM"
COL_HIER_FULLNAME  = "fullname"            # display name, e.g. "Public Investment Management"
COL_HIER_CATEGORY  = "keyword_catagory"   # thematic grouping
COL_HIER_KEYWORD   = "keyword"            # individual keyword

# ── Download columns ───────────────────────────────────────────────────────────
DOWNLOAD_COLUMNS: list[str] = [
    COL_PROJ_ID,
    COL_PROJ_NAME,
    COL_COUNTRY,
    COL_APPRVL_FY,
    COL_PROJ_STAT,
    COL_LEND_INSTR,
    COL_REGION,
    COL_PROJ_OBJ,
    COL_DLI,
    # COL_DLR,
]

# ── Chart colour sequence ──────────────────────────────────────────────────────
CHART_COLORS: list[str] = [
    "#4299E1",  # blue
    "#90CDF4",  # light-blue
    "#FC8181",  # pink-red
    "#68D391",  # green
    "#F6AD55",  # orange
    "#B794F4",  # purple
    "#76E4F7",  # cyan
    "#F687B3",  # pink
    "#FBD38D",  # yellow
    "#9AE6B4",  # mint
]

# ── Sunburst colours for hierarchy chart (inner ring) ─────────────────────────
SUNBURST_INNER_COLORS: list[str] = [
    "#4A90D9",  # blue
    "#357ABD",
    "#2E6DA4",
    "#1F5C8B",
    "#3B82C4",
    "#5A9FD4",
]

# ── Plotly dark-theme layout defaults ─────────────────────────────────────────
CHART_LAYOUT_DEFAULTS: dict = dict(
    paper_bgcolor="#1e1e1e",
    plot_bgcolor="#1e1e1e",
    barmode="stack",
    font=dict(
        family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        color="#E2E8F0",
        size=12,
    ),
    legend=dict(
        bgcolor="#252525",
        bordercolor="#333333",
        borderwidth=1,
        font=dict(color="#CBD5E0", size=11),
    ),
    xaxis=dict(
        gridcolor="#2d2d2d",
        zeroline=False,
        tickfont=dict(color="#A0AEC0", size=11),
        title_font=dict(color="#A0AEC0", size=12),
    ),
    yaxis=dict(
        gridcolor="#2d2d2d",
        zeroline=False,
        tickfont=dict(color="#A0AEC0", size=11),
        title_font=dict(color="#A0AEC0", size=12),
    ),
    margin=dict(l=60, r=24, t=44, b=60),
    hoverlabel=dict(
        bgcolor="#252525",
        bordercolor="#3a3a3a",
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            size=12,
            color="#E2E8F0",
        ),
    ),
)

ABOUT_TEXT = """
The Governance Operations Analytics Tool (GoAT) allows for targeted searches in core fields of the World Bank's three operation types. These encompass Development Policy Operations (DPO), Investment Project Lending (IPL), and Program for Results (PfoR). Clusters of keywords can be mapped to a particular thematic cluster of terms, for example, focused on Public Investment Management (PIM), public asset management (PAM), or State-Owned Enterprises (SOEs). The identified operations can also be an asset for the level of climate co-benefits (CCBs). GoAT also allows users to modify their thematic cluster of terms and vary the document sections considered in searches (e.g., PDOs and/or indicators or prior actions in DPOs). \n

The GoAT tool is being operated and maintained by the World Bank's Global Community of Practice (CoP) for Public Infrastructure Investments and Asset Governance (PIIAG) (P179442). To the extent enabled by the World Bank's public and internal data resources, the GoAT aims to provide a real-time view of the current state of Bank operations. These include Board Approved operations and upstream operations before Board approval (i.e., Concept and Appraisal). The GoAT initiative also progressively demonstrates how generative AI can be applied to a subset of relevant project information (e.g., all World Bank projects with a substantive focus on Public Asset Governance or a sub-type thereof).   \n

The GoAT tool provides interfaces for both general and more data science-oriented users. The public version of GoAT offers a user-friendly interface. The GoAT tool was developed to demonstrate the power of Web Applications and Interactive Development Interface (IDE) codebooks as applied to gleaning operational intelligence from public investment financing data. In line with the World Bank's commitment to public investment financing transparency, the recent GoAT interfaces in Table 1 have focused on leveraging openly accessible data through the World Bank's Data Catalogue, mainly as implemented by Application Programming Interfaces (APIs). Where specific data is not yet available via public APIs, and/or is for official use only, the GoAT interfaces are deployed for official/internal access only.
"""