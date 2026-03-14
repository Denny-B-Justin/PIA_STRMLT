# Changes — Trial Version (CSV Mode)

This document describes every change made to convert the Databricks-backed
dashboard into a self-contained **trial version** that uses plain CSV files
instead of a cloud data warehouse.

---

## Summary

| File | Status | Change type |
|------|--------|-------------|
| `app.py` | Modified | Design enhancements + auth removal |
| `constants.py` | Minor edit | Comment updated |
| `queries.py` | Rewritten | Databricks → CSV data layer |
| `server.py` | Rewritten | Auth / flask-login removed |
| `utils.py` | Enhanced | `kpi_card()` gets optional progress bar |
| `health_facilities_zmb.csv` | **New** | 80-row sample facility dataset |
| `lgu_accessibility_results_zmb.csv` | **New** | 30-row sample optimisation dataset |
| `assets/custom.css` | **New** | Slider + global dark-theme CSS (Dash auto-serves) |
| `changes.md` | **New** | This file |

---

## File-by-file details

---

### `queries.py` — Full rewrite (Databricks → CSV)

**Problem:** The original file imported `databricks.sdk`, `databricks.sql`,
and used OAuth service-principal credentials from environment variables
(`DATABRICKS_SERVER_HOSTNAME`, `DATABRICKS_CLIENT_ID`, etc.).  This makes
the app unrunnable without a Databricks workspace.

**Solution:** The entire network / auth layer was removed.  Data is now read
from two CSV files placed in the same directory as the script.

Key changes:
- Removed all `databricks.*` imports.
- Removed `credentials_provider()` function.
- Removed `QUERY_CACHE_TTL_SECONDS`, `QUERY_CACHE_MAX_ENTRIES`,
  `ZAMBIA_CATALOG`, `FACILITIES_SCHEMA`, `RESULTS_SCHEMA`, and all
  environment-variable reads.
- `QueryService.__init__` now holds two simple `None` cache slots
  (`_facilities_cache`, `_results_cache`) instead of the TTL dict + lock.
- `execute_query()` removed entirely; replaced by `pd.read_csv()` calls
  inside each domain method.
- `get_existing_facilities()` and `get_accessibility_results()` signatures
  and return shapes are **identical** to the original — downstream code
  (`app.py`, `utils.py`) required no changes to the data-consumption paths.
- `clear_cache()` sets both slots back to `None` (same public API as before).
- `invalidate_query()` removed (no SQL queries to invalidate).
- Two file-path constants added at module level:
  ```python
  FACILITIES_CSV = os.path.join(_HERE, "health_facilities_zmb.csv")
  RESULTS_CSV    = os.path.join(_HERE, "lgu_accessibility_results_zmb.csv")
  ```

**No env file is required.**  The paths are resolved relative to the script
itself so the app works regardless of the working directory.

---

### `server.py` — Simplified (auth removed)

**Problem:** The original imported `flask_login.LoginManager` and a local
`auth.User` class (from `auth.py`, which was not provided and depends on an
external identity provider).

**Solution:**
- Removed `flask_login`, `LoginManager`, `@login_manager.user_loader`, and
  the `load_user` function.
- Removed the `os.getenv("SECRET_KEY")` call; a hardcoded trial secret is
  used instead so no `.env` file is needed.
- `server` (the Flask instance) is still exported under the same name so
  `app.py`'s `Dash(..., server=server, ...)` line is untouched.

---

### `app.py` — Design enhancements + auth references removed

**Structural changes:**
- Removed the `login_manager` / auth import chain (no longer needed).
- Loading message changed from `"Loading data from Databricks…"` to
  `"Loading data…"` to avoid referencing a service that is not connected.
- Status bar copy updated: `"optimisation rows 1259–…"` replaced with a
  dynamic count that does not hard-code Databricks row numbers.
- `n_new == 1` edge case handled (`"facility"` vs `"facilities"`).

**Design system changes:**

1. **Design tokens** — All colours and font stacks are now declared as named
   Python constants near the top of the file (`BG_BASE`, `BG_CARD`, `BORDER`,
   `ACC_ORANGE`, `ACC_BLUE`, `ACC_GREEN`, `ACC_SLATE`, `FONT_MONO`,
   `FONT_BODY`).  All style dicts reference these tokens, making future
   palette updates a single-line change.

2. **`BADGE_STYLE`** — A new pill badge ("TRIAL · CSV DATA MODE") is shown
   above the app title so it is visually obvious this is not production.

3. **`SLIDER_CSS`** — A `<style>` block injected via `dangerously_allow_html`
   overrides `rc-slider` default styles to match the dark theme: blue track
   gradient, glow handle, Space Mono tooltip.

4. **`section_label()`** — New helper that renders a small uppercase divider
   label above KPI cards and the map, adding visual hierarchy.

5. **KPI cards** — The `dbc.Card` / `dbc.CardBody` wrapper was removed;
   `kpi_card()` HTML is now rendered directly inside a plain `html.Div`.
   This removes Bootstrap card padding that was fighting the custom card
   styles.  The "Population Access" card now receives a `progress` value
   so a thin animated bar appears at the bottom of the card (see
   `utils.py` changes below).

6. **Header layout** — `flex: 1` / `maxWidth` added to the slider container
   so it reflows cleanly on smaller viewports.

7. **Footer copy** — `"DATA: SAMPLE CSV (TRIAL MODE)"` appended to the
   footer to communicate data provenance.

---

### `assets/custom.css` — New file

Dash automatically serves every file in an `assets/` folder as a static
asset.  This file contains:

- **`rc-slider` overrides** — Track gradient (navy → sky blue), themed
  handle with glow, Space Mono tooltip.  Previously these were injected via
  `dangerously_allow_html=True` on an `html.Div`, which was removed in
  **Dash 4.0**.  The `assets/` approach is the idiomatic Dash replacement.
- **Global resets** — `box-sizing: border-box`, body `margin: 0`,
  Bootstrap `.card-body` padding reset.
- **Custom scrollbar** — Subtle dark scrollbar matching the colour palette.

---

### `utils.py` — `kpi_card()` return type changed (Dash 4 compatibility)

**Dash 4.0 removed `dangerously_allow_html` from `html.Div`**, so the
previous approach of returning a raw HTML string and rendering it via
`html.Div(dangerously_allow_html=True, children=kpi_card(...))` no longer
works.

`kpi_card()` now returns a **Dash component tree** (`html.Div` with nested
`html.Div` children) that is structurally identical to the original HTML.
The function signature and visual output are unchanged.  The `app.py`
callback no longer wraps the result in `html.Div(dangerously_allow_html=...)`.

---

**Change:** `kpi_card()` accepts an optional `progress: float | None = None`
parameter (0–100).  When supplied, a thin gradient progress bar is rendered
at the bottom of the card using an inline CSS `width` transition.

The Population Access card in `app.py` passes `progress=access_pct` so the
bar animates smoothly as the slider moves.  All other cards pass nothing
(bar is hidden), preserving existing visual style.

All other functions (`build_folium_map`, `get_map_html`,
`get_new_facility_rows`, `get_access_pct`, `format_delta`) are **unchanged**.

---

### `constants.py` — Comment updated only

The `BASELINE_ACCESS_PCT = 79.31` value is unchanged.  The comment was
updated to reference the sample CSV rather than the Databricks notebook.
All other values are identical to the original.

---

## New data files

### `health_facilities_zmb.csv`

80 rows.  Columns: `id, lat, lon, name`.

Covers all nine provinces of Zambia (Lusaka, Copperbelt, Southern, Eastern,
Northern, Western, North-Western, Luapula, Muchinga, Central).  Coordinates
and names are representative — they reflect real cities and district-hospital
names but are not authoritative GIS data.  Replace with the real
`health_facilities_zmb` table export when connecting to Databricks.

### `lgu_accessibility_results_zmb.csv`

30 rows.  Columns: `total_facilities, new_facility, lat, lon,
total_population_access_pct`.

- `total_facilities` runs from 81 to 110 (= 80 existing + 1…30 new).
- `total_population_access_pct` increases monotonically from 79.93 % to
  87.54 %, simulating diminishing returns from successive optimal placements.
- New facility coordinates are distributed across underserved rural areas
  in North-Western, Northern, Southern, Western, and Luapula provinces.

Replace with the real `lgu_accessibility_results_zmb` table export when
connecting to Databricks.

---

## How to run

```bash
# 1. Install dependencies
pip install dash dash-bootstrap-components folium pandas flask

# 2. Make sure all files are in the same folder:
#    app.py  constants.py  queries.py  server.py  utils.py
#    health_facilities_zmb.csv  lgu_accessibility_results_zmb.csv

# 3. Start the app
python app.py
# Open http://127.0.0.1:8050 in a browser
```

No `.env` file, no Databricks connection, no API keys required.

---

## Switching back to Databricks

1. Restore `queries.py` to the original (Databricks-backed) version.
2. Restore `server.py` to the original (flask-login) version and supply the
   `auth.py` module.
3. Set the required environment variables:
   ```
   DATABRICKS_SERVER_HOSTNAME=...
   DATABRICKS_HTTP_PATH=...
   DATABRICKS_CLIENT_ID=...
   DATABRICKS_CLIENT_SECRET=...
   SECRET_KEY=...
   ```
4. `app.py`, `utils.py`, and `constants.py` require **no changes** —
   the public interface of `QueryService` is identical between both versions.