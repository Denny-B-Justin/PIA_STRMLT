# PFM4CA Country Benchmarking Tool — Dash Edition

A pure Python/Dash port of the original React + FastAPI app. No database, no
API server — every page reads straight from the CSV files in `./data`.

## Project layout

```
app.py            Dash app: routing, page layouts, all callbacks
queries.py         All data access: loads CSVs from ./data, computes map scores,
                    popup rows, EF (DEA/FDH) frontier, etc.
utils.py           Presentation helpers: colors, Mapbox figure builder, header/
                    sidebar/legend/popup builders, styled dropdown
data/              CSVs (score/desc tables, country lookup, PEFA master, EF
                    indicators) + world_countries.geojson (ISO A3-coded
                    country boundaries used for every choropleth)
assets/            style.css (auto-loaded by Dash) + logo + favicon
```

## Setup

```bash
pip install -r requirements.txt
```

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
- **PEFA's region dropdown** only re-centers the map (as in the original) —
  it does not filter the data, since PEFA scores aren't tied to World Bank
  regions in the source data.
- The world boundary file is Natural Earth data (public domain), simplified
  and reduced to ISO A3 + name only to keep the app fast.
