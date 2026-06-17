# GoAT — Governance Operations Analytics Tool

GoAT allows targeted searches across core fields of the World Bank's three operation types — **Development Policy Operations (DPO)**, **Investment Project Financing (IPF)**, and **Program-for-Results (PfoR)**. Clusters of keywords are mapped to thematic hierarchies such as Public Investment Management (PIM), Public Asset Management (PAM), and State-Owned Enterprises (SOEs), enabling users to analyse operational trends, filter projects by region and lending instrument, and manage keyword sets — all in real time against a live Unity Catalog data source.

The tool is operated by the World Bank's Global Community of Practice for **Public Infrastructure Investments and Asset Governance (PIIAG)** (P179442) and is deployed for official/internal access only where data is not available via public APIs.

---
### World Bank Data Analytics Deployment: https://datanalytics.worldbank.org/content/5e009cdd-7b07-4567-8f45-eb3a3f476abc/
---

## Architecture

```
Browser
  │
  ▼
Dash App (app.py)
  ├── Layout & Callbacks
  ├── Chart Builders       utils.py
  ├── SQL + Write Layer    queries.py
  └── Config               constants.py
        │
        ▼
  Azure Databricks SQL Warehouse
  (OAuth2 M2M — Service Principal)
        │
        ├── Master Projects Table       ← project × hierarchy rows (main data)
        └── Hierarchy Table  ← keyword reference table
```

All queries are built dynamically from filter state. Results are served from an in-process TTL cache (default 5 min) before hitting the warehouse.

---

## Project Structure

| File | Role |
|------|------|
| `app.py` | Dash layout, all callbacks, WSGI export |
| `queries.py` | `QueryService` singleton — SQL builders, Databricks auth, TTL cache, keyword search engine, write operations |
| `utils.py` | Plotly figure builders (bar charts + sunburst) |
| `constants.py` | Table names, column identifiers, colours, layout defaults |
| `assets/goat.css` | Dark theme, red multi-value dropdown pills |
| `.env` | Databricks credentials (never committed) |

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in the four Databricks values
python app.py          # open http://localhost:8050
```

**Required env vars** — `DATABRICKS_SERVER_HOSTNAME`, `DATABRICKS_HTTP_PATH`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`. Find the first two under *SQL Warehouses → Connection details* in your Databricks workspace; the latter two come from your Azure service principal.

---

## Tabs

**Dashboard** — Filter by Lending Instrument, Region, and Keyword Hierarchy (AND/OR logic). Renders a live project count metric, two stacked bar charts (Project Status and Lending Instrument by approval FY), and a downloadable project table.

**Keywords** — Three sub-tabs:
- *Available Hierarchies* — sunburst chart of all active hierarchies and their keywords, sourced directly from `0c_hierarchy_table_goat`.
- *Add New Keywords* — enter a hierarchy name, full name, and comma-separated keywords. GoAT runs a vectorised keyword search across ~10,000 projects (across `Indicators`, `PriorActions`, `PROJ_DEV_OBJECTIVE_DESC`, `Components`) and inserts one row per project into `0b_overall_goat_df` with `Ishierarchy_present = Yes/No` and `Valid_Hierarchy = True`.
- *Delete Hierarchy* — soft-deletes a hierarchy by setting `Valid_Hierarchy = False` on all matching rows. No data is permanently removed; all dashboard queries filter on `Valid_Hierarchy = True`.

**About** — Tool background and CoP context.

---

## Keyword Search Design

The search uses vectorised pandas string matching — a `.str.contains()` call per text column, case-insensitive, applied across all project rows in a single DataFrame operation.

For production deployments on Posit Connect, set the four env vars under *Content Settings → Vars* and ensure the service principal has `CAN USE` on the SQL warehouse and `SELECT` / `MODIFY` on both UC tables.