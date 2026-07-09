# PFM4CA Country Benchmarking Tool — Dash Edition

A Python/Dash port of the PIMPAM Country Benchmarking Tool. No FastAPI
server in front — Dash callbacks call straight into `queries.py`, which reads
its tables from **Databricks Unity Catalog** (previously local CSVs).

## Project layout

```
app.py            Dash app: routing, page layouts, all callbacks, startup
                    Databricks connection check, /health/databricks route
queries.py         All data access: queries Unity Catalog tables (cbd_*),
                    computes map scores, popup rows, EF (DEA/FDH) frontier,
                    etc. Also handles the Databricks OAuth service-principal
                    connection and logs every connection/query attempt.
utils.py           Presentation helpers: colors, Mapbox figure builder, header/
                    sidebar/legend/popup builders, styled dropdown
assets/            style.css (auto-loaded by Dash) + logo + favicon
```

## Setup

```bash
pip install -r requirements.txt
```

Key dependencies added for the Databricks migration:
```
databricks-sql-connector
databricks-sdk
python-dotenv
```
(`pandas`, `numpy`, `scipy` were already required.)

## Data source: Databricks Unity Catalog

Every table that used to be a CSV in `./data` now lives in Unity Catalog,
prefixed `cbd_` (e.g. `ccia_score.csv` → `cbd_ccia_score`). Only
`world_countries.geojson` stays a local file. ISO A3-coded country 
boundaries used for every choropleth. Score/desc/master tables now live in Databricks.

Set these environment variables (a `.env` file in the project root is picked
up automatically via `python-dotenv`; see `.env.example`):

```bash
DATABRICKS_SERVER_HOSTNAME=adb-xxxx.azuredatabricks.net
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123
DATABRICKS_CLIENT_ID=your-client-id
DATABRICKS_CLIENT_SECRET=your-client-secret

CBD_CATALOG=prd_mega   # catalog holding the cbd_* tables
CBD_SCHEMA=sgpbpi163     # schema holding the cbd_* tables
```

`queries.py` fails fast at import time with a clear error listing exactly
which of these are missing.

**Column names matter.** The code references some columns by exact case
(`"Code"`, `"Economy"`, `"Year"`, `"Framework"`, `"ISO"`, `"varname"`,
`"method"`, `"sample"`, `"short_name"`, `"2019-2023"`) alongside snake_case
ones (`cntr_code`, `grp_name`, `gccii_id`, `score`, `indicator_name`, ...).
Make sure the Unity Catalog tables preserve these exact names.

## Mapbox

The maps use Plotly's `Choroplethmapbox` trace. To get the exact
`mapbox://styles/mapbox/light-v11` look from the original app, set a Mapbox
access token before running:

```bash
export MAPBOX_TOKEN=pk.your_token_here   # macOS/Linux
set MAPBOX_TOKEN=pk.your_token_here      # Windows (cmd)
```

Without a token the app still runs fine — maps fall back to the free
"carto-positron" basemap style automatically.

Note: Mapbox's `light-v11` style renders its own place labels (city/country
names) on top of the choropleth fill, which can look illegible over a solid
highlight color. `build_map_figure()` sets `below=""` on the trace so the
fill draws above the label layer, hiding labels inside highlighted regions
rather than clashing with them.

## Run

```bash
python app.py
```

Then open http://127.0.0.1:8050

## Notes on the port

- **Region/pillar dropdowns** are `dcc.Dropdown` (Dash's raw `html.Select`
  has no bindable `value` prop), themed via CSS in `assets/style.css` to
  match the original's compact native-select look.
- **Choropleth colors** are computed the same way as the original
  `getScoreColor5` / categorical logic in `constants.ts`: continuous scores
  are bucketed into 5 bands (Low → High); PIMS and PEFA use their own fixed
  categorical color sets. Countries with no data render at low opacity gray.
- **Click-to-see-detail** replaces the original's map-anchored Mapbox popup
  with a floating panel pinned to the top-right of the map (same table
  layout: Country / Indicator / Score). Hover tooltips use Plotly's native
  hover label.
- **Sidebar info blocks** (`utils.info_block`) accept either a string
  (rendered as a paragraph) or a list of strings (rendered as a bulleted
  list) — see the PEFA page's "Indicators" block for an example.
- **PEFA's region dropdown** only re-centers the map (as in the original) —
  it does not filter the data, since PEFA scores aren't tied to World Bank
  regions in the source data.
- The world boundary file is Natural Earth data (public domain), simplified
  and reduced to ISO A3 + name only to keep the app fast.