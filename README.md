# Health Facility Accessibility Dashboard

A **multi-country Databricks Data App** built with Dash that visualises the location and population accessibility of health facilities for any configured country. It allows users to simulate the addition of up to 50 optimally-placed new facilities and instantly see the projected improvement in population coverage.

The active country is selected via a URL query parameter — a single codebase powers a separate, fully-branded geospatial hub for each country.

```
datanalytics.worldbank.org/pimpampath-xxxxx?country=zambia   → Zambia hub
datanalytics.worldbank.org/pimpampath-xxxxx?country=malawi   → Malawi hub
```

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Adding a New Country](#adding-a-new-country)
- [Data Sources](#data-sources)
- [Table Naming Convention](#table-naming-convention)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [Deploying to Posit Connect](#deploying-to-posit-connect)
- [How the Optimisation Logic Works](#how-the-optimisation-logic-works)
- [Troubleshooting](#troubleshooting)

---

## Overview

This dashboard is part of the **GoAT (Geospatial Optimisation and Accessibility Tool)** initiative under the World Bank's PIM-PAM team. It connects to Unity Catalog tables in Databricks to visualise:

- All **existing** health facilities in the selected country
- **Proposed new** facility locations ranked by optimisation score
- **Population accessibility** percentage before and after simulated additions
- **Sub-national views** (provinces, regions, or districts) with scoped maps and stats

The optimisation is pre-computed using a greedy MCLP (Maximum Coverage Location Problem) solver and stored in result tables. The app reads and visualises those results interactively.

---

## Features

- **URL-driven country selection** — `?country=zambia` or `?country=malawi`; one deployment, many hubs
- **Interactive Plotly Scattermap** — open-street-map tiles, no Mapbox token required
- **Sub-national location dropdown** — scoped to the active country's provinces / regions
- **Orange markers** — existing health facilities
- **Hollow numbered circles** — proposed new facilities
- **+/− stepper** — simulate adding 1 to 50 new facilities in real time
- **KPI cards** — existing facility count, current accessibility %, optimised accessibility %, delta
- **Accessibility curve** — Plotly line chart showing coverage vs. facility count
- **Recommended locations table** — coordinates (DMS), district, and estimated new people reached
- **In-memory TTL cache** — Databricks is queried once and cached per query; all stepper interactions are instant
- **OAuth M2M authentication** — service principal credentials for secure production access

---

## Project Structure

```
your-app/
│
├── app.py            # Dash application — layout, callbacks, UI
├── queries.py        # QueryService singleton — Databricks SQL + TTL cache
├── utils.py          # Map builder, chart helpers, accessibility logic
├── server.py         # Flask server + LoginManager
├── constants.py      # Country registry (COUNTRY_CONFIGS) + backward-compat constants
│
├── .env              # Local environment variables (never commit this)
├── requirements.txt  # Python dependencies
├── manifest.json     # Posit Connect deployment config
└── README.md
```

The only file you need to edit to add a new country is **`constants.py`**.

---

## Architecture

```
Browser
  └── ?country=zambia (or malawi, …)
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│                     Dash Frontend (app.py)               │
│                                                          │
│   dcc.Location  ── reads ?country= on page load         │
│   store-country ── drives all downstream callbacks       │
│                                                          │
│   ├── store-location   (country or sub-national unit)   │
│   ├── store-base-data  (center, boundary WKT, baseline) │
│   ├── store-existing-facilities                         │
│   ├── store-accessibility-results                       │
│   ├── store-distance-km                                 │
│   └── store-n-new                                       │
│                                                          │
│   UI: Header | Filter bar | Map | Stats pane            │
└────────────────────────────────────────┬─────────────────┘
                                         │ Callbacks
                                         ▼
┌──────────────────────────────────────────────────────────┐
│                 QueryService (queries.py)                │
│                                                          │
│   In-memory TTL cache (default 5 min, 256 entries)      │
│   └── Databricks SQL Connector (OAuth M2M)              │
│       └── Unity Catalog                                 │
│           ├── base_dashboard_data_{iso3}                │
│           ├── health_facilities_{iso3}                  │
│           ├── health_facilities_{iso3}_osm_{slug}_…     │
│           ├── lgu_accessibility_results_{iso3}_{band}  │
│           └── lgu_accessibility_results_{iso3}_{slug}…  │
└──────────────────────────────────────────────────────────┘
                                         ▲
                                         │ Config lookup
┌──────────────────────────────────────────────────────────┐
│              COUNTRY_CONFIGS (constants.py)              │
│                                                          │
│   "zambia": { center_lat, center_lon, subnational_units,│
│               catalog_env, table templates, … }         │
│   "malawi":  { … }                                       │
│   "<new>":   { … }   ← add one dict, done               │
└──────────────────────────────────────────────────────────┘
```

**Key design decisions:**

- **`dcc.Store` pattern** — data is fetched from Databricks into in-browser stores on load. All stepper and slider interactions read from stores, producing zero additional DB queries during a session.
- **`dcc.Location`** — reads the `?country=` query parameter on every page load without a full page refresh. Posit Connect vanity URLs preserve query-string parameters, so each embed link is self-contained.
- **`key`-based map remount** — the map `dcc.Graph` receives a unique `key` on every meaningful state change, forcing React to unmount and remount the component. This eliminates the stale-tile and viewport-lock issues that arise when Plotly tries to diff/patch an existing MapLibre instance.

---

## Adding a New Country

Only **`constants.py`** needs to change. Copy the `"zambia"` block, update every field, and the rest of the app adapts automatically.

```python
# constants.py  →  COUNTRY_CONFIGS dict

"ghana": {
    # ── Display ───────────────────────────────────────────────────────────
    "display_name":     "Ghana",
    "iso3":             "gha",

    # ── Map defaults ──────────────────────────────────────────────────────
    "center_lat":       7.95,
    "center_lon":       -1.02,
    "map_zoom":         6.5,
    "province_zoom":    7.5,

    # ── Population ────────────────────────────────────────────────────────
    "population":       33_475_870,

    # ── Databricks catalog / schema ───────────────────────────────────────
    # Add these env vars on Posit Connect before enabling this country.
    "catalog_env":               "GHANA_CATALOG",
    "catalog_default":           "prd_mega",
    "facilities_schema_env":     "GHANA_FACILITIES_SCHEMA",
    "facilities_schema_default": "pim",
    "results_schema_env":        "GHANA_RESULTS_SCHEMA",
    "results_schema_default":    "pim",

    # ── Sub-national units ────────────────────────────────────────────────
    "subnational_label": "Region",
    "subnational_units": ["Ashanti", "Greater Accra", "Northern", ...],
    "subnational_slugs": {
        "Ashanti":       "ashanti",
        "Greater Accra": "greater_accra",
        "Northern":      "northern",
        ...
    },

    # ── Distance bands ────────────────────────────────────────────────────
    "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

    # ── Fallback baselines (used when DB is unreachable) ──────────────────
    "fallback_baselines": {5: 0.0, 10: 0.0, "30min": 0.0, "1hr": 0.0},

    # ── Table naming templates ─────────────────────────────────────────────
    "db_country_name":               "Ghana",
    "base_table":                    "base_dashboard_data_gha",
    "country_facilities_table":      "health_facilities_gha",
    "province_facilities_template":  "health_facilities_gha_osm_{slug}_region",
    "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
    "country_results_template":      "lgu_accessibility_results_gha_{suffix}",
    "province_results_template":     "lgu_accessibility_results_gha_{slug}_region_{suffix}",
},
```

Then provision the Databricks tables (see [Table Naming Convention](#table-naming-convention)), set the env vars on Posit Connect, and share the link:

```
https://datanalytics.worldbank.org/pimpampath-xxxxx?country=ghana
```

No Python code changes are needed outside of `constants.py`.

---

## Data Sources

| Table | Description |
|---|---|
| `base_dashboard_data_{iso3}` | Map center coordinates, boundary WKT, baseline accessibility %, and total facility count — one row per location / distance band combination |
| `health_facilities_{iso3}` | All existing health facilities at country level — `id`, `lat`, `lon`, `name` |
| `health_facilities_{iso3}_osm_{slug}_{unit}` | Per-sub-national-unit facility tables (e.g. `_osm_central_province`) |
| `lgu_accessibility_results_{iso3}_{suffix}` | Country-level MCLP results — ranked new facility locations with cumulative accessibility % |
| `lgu_accessibility_results_{iso3}_{slug}_{unit}_{suffix}` | Sub-national MCLP results |

**Population data:** WorldPop constrained 100 m raster (pre-processed in the extraction notebook)

**Facility source:** OpenStreetMap via Overpass API

**Optimisation method:** Greedy MCLP (Maximum Coverage Location Problem) approximation

---

## Table Naming Convention

All table names are assembled from templates defined in `COUNTRY_CONFIGS`. The patterns for Zambia are shown below; substitute `zmb` and `province` for your country's ISO3 code and administrative unit type.

| View | Distance band | Table name |
|---|---|---|
| Zambia (country) | Driving 5 km | `lgu_accessibility_results_zmb_5km` |
| Zambia (country) | Driving 10 km | `lgu_accessibility_results_zmb_10km` |
| Zambia (country) | Walking 30 min | `lgu_accessibility_results_zmb_2km` |
| Zambia (country) | Walking 1 hr | `lgu_accessibility_results_zmb_4km` |
| Central Province | Driving 5 km | `lgu_accessibility_results_zmb_central_province_5km` |
| North-Western Province | Walking 1 hr | `lgu_accessibility_results_zmb_north_western_province_4km` |

The distance column in `base_dashboard_data_{iso3}` always stores integers (2, 4, 5, 10 km), with walking bands mapped to their km equivalents. This mapping is configured per-country in `distance_km_map`.

---

## Prerequisites

- Python **3.10+**
- Access to the Databricks workspace with:
  - Read permission on all relevant Unity Catalog tables for the target country
  - A running **SQL Warehouse** (serverless recommended)
- Either a **Personal Access Token** (local dev) or **Service Principal** (production)

---

## Local Setup

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd your-app
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
pip install python-dotenv pyarrow
```

> `python-dotenv` loads your `.env` file automatically.
> `pyarrow` is required by `databricks-sql-connector` v4.0+ for fetching results.

**4. Create your `.env` file**

```bash
cp .env.example .env
```

Then edit `.env` — see [Environment Variables](#environment-variables) below.

---

## Environment Variables

The app uses a **shared Databricks connection** (one warehouse, one service principal) and **per-country catalog / schema env vars**. You only need to add the per-country vars for countries you intend to enable.

```dotenv
# ── Databricks connection (shared across all countries) ────────────────────
DATABRICKS_SERVER_HOSTNAME=adb-xxxxxxxxxxxx.azuredatabricks.net
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/xxxxxxxxxxxxxxxx
DATABRICKS_CLIENT_ID=your-client-id
DATABRICKS_CLIENT_SECRET=your-client-secret

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<your-random-secret-key>

# ── Query cache tuning ─────────────────────────────────────────────────────
QUERY_CACHE_TTL_SECONDS=300
QUERY_CACHE_MAX_ENTRIES=256

# ── Zambia (always required — used as the default fallback country) ─────────
ZAMBIA_CATALOG=prd_mega
FACILITIES_SCHEMA=pim
RESULTS_SCHEMA=pim

# ── Malawi (add when Malawi data pipelines are ready) ─────────────────────
MALAWI_CATALOG=prd_mega
MALAWI_FACILITIES_SCHEMA=pim
MALAWI_RESULTS_SCHEMA=pim

# ── Ghana (add when Ghana data pipelines are ready) ───────────────────────
# GHANA_CATALOG=prd_mega
# GHANA_FACILITIES_SCHEMA=pim
# GHANA_RESULTS_SCHEMA=pim
```

On **Posit Connect**, these are set as environment variables in the deployment settings panel — not in a `.env` file.

---

## Running the App

> This is a **Dash** app. Do **not** run it with `streamlit run`. Use `python` directly.

```bash
python app.py
```

Open your browser at `http://127.0.0.1:8050/` and append the `?country=` parameter to test different countries:

```
http://127.0.0.1:8050/?country=zambia
http://127.0.0.1:8050/?country=malawi
```

Omitting the parameter defaults to Zambia. An unrecognised country slug also falls back to Zambia with a warning logged to stdout.

---

## Deploying to Posit Connect

1. **Push the code** to the connected Git repository or upload the bundle via the Posit Connect UI.
2. **Set environment variables** in the deployment settings panel (see [Environment Variables](#environment-variables)).
3. **Create a vanity URL** (or use the default content URL) for each country hub:

   | Country | URL |
   |---|---|
   | Zambia | `https://datanalytics.worldbank.org/pimpampath-xxxxx?country=zambia` |
   | Malawi | `https://datanalytics.worldbank.org/pimpampath-xxxxx?country=malawi` |

4. **Embed** the URL in the relevant ArcGIS Hub page or share it directly. The `?country=` parameter is preserved by Posit Connect's iframe embedding, so each link always loads the correct country without any server-side routing logic.

> A single Posit Connect content item serves all countries. There is no need to deploy separate apps.

---

## How the Optimisation Logic Works

The dashboard visualises the output of a **greedy MCLP (Maximum Coverage Location Problem)** solver run as a Databricks notebook.

1. **Population grid** — WorldPop 100 m raster, aggregated to H3 hexagons at an appropriate resolution for the country.
2. **Travel catchment** — each candidate facility location is assigned a set of H3 cells reachable within the chosen distance / time band.
3. **Greedy ranking** — facilities are added one at a time, each time selecting the location that maximally increases the number of newly-covered people.
4. **Results table** — each row represents the cumulative state after adding one more facility: `total_facilities`, `lat`, `lon`, `total_population_access_pct`, `district`.

The app reads this pre-computed table. No optimisation runs in the app itself — the stepper simply looks up rows by `total_facilities` count, making all interactions instant.

---

## Troubleshooting

**Map is blank on first load**

The startup pre-warm query (Zambia only) may have failed. Check the Posit Connect application logs for `Startup base data load failed`. Ensure `ZAMBIA_CATALOG`, `FACILITIES_SCHEMA`, and the Databricks connection variables are all set correctly.

**`?country=malawi` shows Zambia data**

Malawi's env vars (`MALAWI_CATALOG`, `MALAWI_FACILITIES_SCHEMA`, `MALAWI_RESULTS_SCHEMA`) are not set, or the Malawi Unity Catalog tables have not yet been provisioned. Check the app logs for `Unknown ?country=` or `DB MISS` errors followed by fallback warnings.

**`EnvironmentError: Missing required environment variables`**

The four core Databricks connection variables are missing. The app will not start without them. Set `DATABRICKS_SERVER_HOSTNAME`, `DATABRICKS_HTTP_PATH`, `DATABRICKS_CLIENT_ID`, and `DATABRICKS_CLIENT_SECRET`.

**Location dropdown shows wrong units after country switch**

The dropdown options are populated by the `update_location_dropdown` callback, which fires whenever `store-country` changes. If the dropdown still shows stale options, check that `suppress_callback_exceptions=True` is set in the `Dash(...)` constructor and that there are no JavaScript console errors blocking the callback cycle.

**Adding a new country slug returns a 404 or falls back to Zambia**

The slug must be registered in `COUNTRY_CONFIGS` in `constants.py` before it becomes a valid `?country=` value. Unrecognised slugs silently fall back to Zambia by design — check the app logs for the `Unknown ?country=` warning.