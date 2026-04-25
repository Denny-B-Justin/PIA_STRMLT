# # ── Map defaults ──────────────────────────────────────────────────────────────
# ZAMBIA_CENTER_LAT   = -13.5
# ZAMBIA_CENTER_LON   = 28.0
# MAP_ZOOM            = 5.25
# PROVINCE_ZOOM       = 6.5          # default zoom when a province is selected

# # ── Province list and slug mapping ────────────────────────────────────────────
# PROVINCES = [
#     "Central", "Copperbelt", "Eastern", "Luapula",
#     "Lusaka", "Muchinga", "Northern", "North-Western",
#     "Southern", "Western",
# ]

# # Maps province display name → table slug used in result-table names
# PROVINCE_SLUGS: dict = {
#     "Central":       "central",
#     "Copperbelt":    "copperbelt",
#     "Eastern":       "eastern",
#     "Luapula":       "luapula",
#     "Lusaka":        "lusaka",
#     "Muchinga":      "muchinga",
#     "Northern":      "northern",
#     "North-Western": "northwestern",
#     "Southern":      "southern",
#     "Western":       "western",
# }

# # ── Distance-value → km integer for base_dashboard_data_zmb queries ───────────
# # The base_dashboard_data_zmb table stores distance_km as integers.
# # Walking travel-time bands are stored by their km equivalents (2 km ≈ 30 min).
# DISTANCE_KM_MAP: dict = {5: 5, 10: 10, "30min": 2, "1hr": 4}

# # ── Marker sizes ──────────────────────────────────────────────────────────────
# RADIUS_EXISTING_M   = 8_000
# RADIUS_NEW_M        = 14_000

# # ── Colours ───────────────────────────────────────────────────────────────────
# COLOUR_EXISTING     = "#F97316"   # warm orange  — existing facilities
# COLOUR_NEW          = "#FFFFFF"   # white fill   — new / proposed facilities
# COLOUR_NEW_RING     = "#0EA5E9"   # sky blue ring — new / proposed facilities

# # ── Slider bounds ─────────────────────────────────────────────────────────────
# MAX_NEW_FACILITIES  = 50

# # ── Fallback accessibility baselines ─────────────────────────────────────────
# # Used only when the DB query for base_dashboard_data_zmb fails.
# # Primary baseline is always fetched live from the UC table.
# BASELINE_ACCESS_PCT      = 79.31   # 10 km — kept for backward compat
# BASELINE_ACCESS_PCT_10KM = 79.31
# BASELINE_ACCESS_PCT_5KM  = 62.24
# BASELINE_ACCESS_PCT_30MIN = 39.52  # 30 min walking (≈ 2 km)
# BASELINE_ACCESS_PCT_1HR   = 56.36  # 1 hr  walking (≈ 4 km)



from __future__ import annotations

# ── Country registry ───────────────────────────────────────────────────────────

COUNTRY_CONFIGS: dict = {

    # ──────────────────────────────────────────────────────────────────────────
    "zambia": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Zambia",
        "iso3":             "zmb",

        # ── Map defaults ──────────────────────────────────────────────────────
        "center_lat":       -13.5,
        "center_lon":       28.0,
        "map_zoom":         5.25,
        "province_zoom":    6.5,

        # ── Population (latest estimate — used for "new people reached") ──────
        "population":       21_559_131,

        # ── Databricks catalog / schema (resolved from env vars at query time) ─
        "catalog_env":               "ZAMBIA_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        "subnational_label": "Province",
        "subnational_units": [
            "Central", "Copperbelt", "Eastern", "Luapula",
            "Lusaka", "Muchinga", "Northern", "North-Western",
            "Southern", "Western",
        ],
        "subnational_slugs": {
            "Central":       "central",
            "Copperbelt":    "copperbelt",
            "Eastern":       "eastern",
            "Luapula":       "luapula",
            "Lusaka":        "lusaka",
            "Muchinga":      "muchinga",
            "Northern":      "northern",
            "North-Western": "northwestern",
            "Southern":      "southern",
            "Western":       "western",
        },

        # ── Distance bands ────────────────────────────────────────────────────
        # Maps UI value → integer km stored in the base_dashboard_data table.
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        # Used ONLY when the DB is unreachable.  Live values come from the DB.
        "fallback_baselines": {
            5:       62.24,
            10:      79.31,
            "30min": 39.52,
            "1hr":   56.36,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Zambia",
        "base_table":                    "base_dashboard_data_zmb",
        "country_facilities_table":      "health_facilities_zmb",
        "province_facilities_template":  "health_facilities_zmb_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_zmb_{suffix}",
        "province_results_template":     "lgu_accessibility_results_zmb_{slug}_province_{suffix}",
    },

    # ──────────────────────────────────────────────────────────────────────────
    "malawi": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Malawi",
        "iso3":             "mwi",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Malawi spans roughly 8.5°S–17.5°S, 32.7°E–35.9°E
        "center_lat":       -13.25,
        "center_lon":       34.30,
        "map_zoom":         6.0,
        "province_zoom":    7.0,

        # ── Population (2023 World Bank estimate) ─────────────────────────────
        "population":       20_931_751,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set MALAWI_CATALOG, MALAWI_FACILITIES_SCHEMA, MALAWI_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "MALAWI_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "MALAWI_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "MALAWI_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Malawi has 3 regions; each contains districts.  Using regions as the
        # top-level granularity here; extend to districts when pipeline is ready.
        "subnational_label": "Region",
        "subnational_units": [
            "Northern", "Central", "Southern",
        ],
        "subnational_slugs": {
            "Northern": "northern",
            "Central":  "central",
            "Southern": "southern",
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        # Update once Malawi baseline data is available in Databricks.
        "fallback_baselines": {
            5:       0.0,
            10:      0.0,
            "30min": 0.0,
            "1hr":   0.0,
        },

        # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
        "db_country_name":               "Malawi",
        "base_table":                    "base_dashboard_data_mwi",
        "country_facilities_table":      "health_facilities_mwi_osm",
        "province_facilities_template":  "health_facilities_mwi_osm_{slug}_region_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_mwi_{suffix}",
        "province_results_template":     "lgu_accessibility_results_mwi_{slug}_region_province_{suffix}",
    },
}

# ── Registry helpers ───────────────────────────────────────────────────────────

DEFAULT_COUNTRY = "zambia"
VALID_COUNTRIES = set(COUNTRY_CONFIGS.keys())


def get_country_config(country: str) -> dict:
    """
    Return the config dict for *country* (a lowercase URL slug like "zambia").

    Always returns a fully-populated dict — falls back to Zambia for any
    unrecognised slug so callers never have to guard against KeyError.
    """
    key = (country or DEFAULT_COUNTRY).lower().strip()
    return COUNTRY_CONFIGS.get(key, COUNTRY_CONFIGS[DEFAULT_COUNTRY])


# ── Marker / colour constants (not country-specific) ──────────────────────────

RADIUS_EXISTING_M   = 8_000
RADIUS_NEW_M        = 14_000

COLOUR_EXISTING     = "#F97316"
COLOUR_NEW          = "#FFFFFF"
COLOUR_NEW_RING     = "#0EA5E9"

# ── Slider bound ──────────────────────────────────────────────────────────────

MAX_NEW_FACILITIES  = 50

# ── Backward-compatible module-level constants (Zambia only) ──────────────────
# These exist so that `from constants import ZAMBIA_CENTER_LAT` etc. continue
# to work in utils.py and any test/notebook code.
# New code should call get_country_config() instead.

_ZMB = COUNTRY_CONFIGS["zambia"]

ZAMBIA_CENTER_LAT         = _ZMB["center_lat"]
ZAMBIA_CENTER_LON         = _ZMB["center_lon"]
MAP_ZOOM                  = _ZMB["map_zoom"]
PROVINCE_ZOOM             = _ZMB["province_zoom"]
PROVINCES                 = _ZMB["subnational_units"]
PROVINCE_SLUGS            = _ZMB["subnational_slugs"]
DISTANCE_KM_MAP           = _ZMB["distance_km_map"]

BASELINE_ACCESS_PCT       = _ZMB["fallback_baselines"][10]
BASELINE_ACCESS_PCT_10KM  = _ZMB["fallback_baselines"][10]
BASELINE_ACCESS_PCT_5KM   = _ZMB["fallback_baselines"][5]
BASELINE_ACCESS_PCT_30MIN = _ZMB["fallback_baselines"]["30min"]
BASELINE_ACCESS_PCT_1HR   = _ZMB["fallback_baselines"]["1hr"]
