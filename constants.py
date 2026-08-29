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
# BASELINE_ACCESS_PCT_5KM  = 71.80
# BASELINE_ACCESS_PCT_30MIN = 39.52  # 30 min walking (≈ 2 km)
# BASELINE_ACCESS_PCT_1HR   = 56.36  # 1 hr  walking (≈ 4 km)



from __future__ import annotations

# ── Country registry ───────────────────────────────────────────────────────────

COUNTRY_CONFIGS: dict = {

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
            5:       71.80,
            10:      87.71,
            "30min": 48.45,
            "1hr":   66.04,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Zambia",
        "base_table":                    "base_dashboard_data_zmb",
        "country_facilities_table":      "health_facilities_zmb_osm",
        "province_facilities_template":  "health_facilities_zmb_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_zmb_{suffix}",
        "province_results_template":     "lgu_accessibility_results_zmb_{slug}_province_{suffix}",
    },

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

        # ── Population (2025 World Bank estimate) ─────────────────────────────
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
            5:       63.56,
            10:      88.75,
            "30min": 36.44,
            "1hr":   55.52,
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

    "serbia": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Serbia",
        "iso3":             "srb",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Serbia spans roughly 42.2°N–46.8°N, 18.8°E–23.0°E
        "center_lat":       44.0165,
        "center_lon":       20.9029,
        "map_zoom":         6.0,
        "province_zoom":    7.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       9_515_039,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set SERBIA_CATALOG, SERBIA_FACILITIES_SCHEMA, SERBIA_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "SERBIA_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "SERBIA_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "SERBIA_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Serbia has 3 regions; each contains districts.  Using regions as the
        # top-level granularity here; extend to districts when pipeline is ready.
        "subnational_label": "Districts",
        "subnational_units": [
            'Borski', 'Branicevski', 'Grad Beograd', 'Jablanicki', 'Juzno-backi', 
            'Juzno-banatski', 'Kolubarski', 'Macvanski', 'Moravicki', 'Nisavski', 
            'Pcinjski', 'Pirotski', 'Podunavski', 'Pomoravski', 'Rasinski', 'Raski', 
            'Severno-backi', 'Severno-banatski', 'Srednje-banatski', 'Sremski', 
            'Sumadijski', 'Toplicki', 'Zajecarski', 'Zapadno-backi', 'Zlatiborski'
        ],
        "subnational_slugs": {
            "Borski": "borski",
            "Branicevski": "branicevski",
            "Grad Beograd": "grad_beograd",
            "Jablanicki": "jablanicki",
            "Juzno-backi": "juzno_backi",
            "Juzno-banatski": "juzno_banatski",
            "Kolubarski": "kolubarski",
            "Macvanski": "macvanski",
            "Moravicki": "moravicki",
            "Nisavski": "nisavski",
            "Pcinjski": "pcinjski",
            "Pirotski": "pirotski",
            "Podunavski": "podunavski",
            "Pomoravski": "pomoravski",
            "Rasinski": "rasinski",
            "Raski": "raski",
            "Severno-backi": "severno_backi",
            "Severno-banatski": "severno_banatski",
            "Srednje-banatski": "srednje_banatski",
            "Sremski": "sremski",
            "Sumadijski": "sumadijski",
            "Toplicki": "toplicki",
            "Zajecarski": "zajecarski",
            "Zapadno-backi": "zapadno_backi",
            "Zlatiborski": "zlatiborski",
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        # Update once Serbia baseline data is available in Databricks.
        "fallback_baselines": {
            5:       95.27,
            10:      99.99,
            "30min": 80.76,
            "1hr":   91.62,
        },

        # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
        "db_country_name":               "Serbia",
        "base_table":                    "base_dashboard_data_srb",
        "country_facilities_table":      "health_facilities_srb_osm",
        "province_facilities_template":  "health_facilities_srb_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_srb_{suffix}",
        "province_results_template":     "lgu_accessibility_results_srb_{slug}_province_{suffix}",
    },

    "nepal": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Nepal",
        "iso3":             "npl",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Nepal spans roughly 26.4°N–30.4°N, 80.0°E–88.2°E
        "center_lat":       28.37,
        "center_lon":       84.30,
        "map_zoom":         6.0,
        "province_zoom":    7.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       29_543_807,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set NEPAL_CATALOG, NEPAL_FACILITIES_SCHEMA, NEPAL_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "NEPAL_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "NEPAL_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "NEPAL_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Nepal has 7 provinces; each contains districts.  Using regions as the
        # top-level granularity here; extend to districts when pipeline is ready.
        "subnational_label": "Province",
        "subnational_units": [
            'Bagmati', 'Gandaki', 'Karnali', 'Koshi', 
            'Lumbini', 'Madhesh', 'Sudurpashchim',
        ],
        "subnational_slugs": {
            "Bagmati": "bagmati",
            "Gandaki": "gandaki",
            "Karnali": "karnali",
            "Koshi": "koshi",
            "Lumbini": "lumbini",
            "Madhesh": "madhesh",
            "Sudurpashchim": "sudurpashchim",
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        # Update once Malawi baseline data is available in Databricks.
        "fallback_baselines": {
            5:       95.66,
            10:      99.78,
            "30min": 79.87,
            "1hr":   92.47,
        },

        # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
        "db_country_name":               "Nepal",
        "base_table":                    "base_dashboard_data_npl",
        "country_facilities_table":      "health_facilities_npl_osm",
        "province_facilities_template":  "health_facilities_npl_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_npl_{suffix}",
        "province_results_template":     "lgu_accessibility_results_npl_{slug}_province_{suffix}",
    },

    "uzbekistan": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Uzbekistan",
        "iso3":             "uzb",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Uzbekistan spans roughly 39.5°N–42.8°N, 64.0°E–73.0°E
        "center_lat":       40.5,
        "center_lon":       68.5,
        "map_zoom":         4.5,
        "province_zoom":    6.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       36_586_558,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set UZBEKISTAN_CATALOG, UZBEKISTAN_FACILITIES_SCHEMA, UZBEKISTAN_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "UZBEKISTAN_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "UZBEKISTAN_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "UZBEKISTAN_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Uzbekistan has 12 regions; each contains districts.  Using regions as the
        # top-level granularity here; extend to districts when pipeline is ready.
        "subnational_label": "Province",
        "subnational_units": [
            'Andijan', 'Bukhara', 'Fergana', 'Jizzakh', 'Karakalpakstan', 
            'Kashkadarya', 'Khorezm', 'Namangan', 'Navoiy', 'Samarkand', 
            'Sirdarya', 'Surkhandarya', 'Tashkent', 'Tashkent city'
        ],
        "subnational_slugs": {
            "Andijan": "andijan",
            "Bukhara": "bukhara",
            "Fergana": "fergana",
            "Jizzakh": "jizzakh",
            "Karakalpakstan": "karakalpakstan",
            "Kashkadarya": "kashkadarya",
            "Khorezm": "khorezm",
            "Namangan": "namangan",
            "Navoiy": "navoiy",
            "Samarkand": "samarkand",
            "Sirdarya": "sirdarya",
            "Surkhandarya": "surkhandarya",
            "Tashkent": "tashkent",
            "Tashkent city": "tashkent_city"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        # Update once Malawi baseline data is available in Databricks.
        "fallback_baselines": {
            5:       83.65,
            10:      97.03,
            "30min": 57.42,
            "1hr":   77.36,
        },

        # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
        "db_country_name":               "Uzbekistan",
        "base_table":                    "base_dashboard_data_uzb",
        "country_facilities_table":      "health_facilities_uzb_osm",
        "province_facilities_template":  "health_facilities_uzb_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_uzb_{suffix}",
        "province_results_template":     "lgu_accessibility_results_uzb_{slug}_province_{suffix}",
    },

    "pakistan": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Pakistan",
        "iso3":             "pak",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Pakistan spans roughly 23.6°N–37.0°N, 60.8°E–77.0°E
        "center_lat":       30.37,
        "center_lon":       69.30,
        "map_zoom":         5.0,
        "province_zoom":    6.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       23_199_335,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set PAKISTAN_CATALOG, PAKISTAN_FACILITIES_SCHEMA, PAKISTAN_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "PAKISTAN_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "PAKISTAN_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "PAKISTAN_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Pakistan has 4 provinces; each contains districts.  Using regions as the
        # top-level granularity here; extend to districts when pipeline is ready.
        "subnational_label": "Province",
        "subnational_units": [
            'Balochistan', 'Federal Capital Territory', 'Khyber Pakhtunkhwa', 
            'Punjab', 'Sindh',
        ],
        "subnational_slugs": {
            "Balochistan": "balochistan",
            "Federal Capital Territory": "federal_capital_territory",
            "Khyber Pakhtunkhwa": "khyber_pakhtunkhwa",
            "Punjab": "punjab",
            "Sindh": "sindh",
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        # Update once Malawi baseline data is available in Databricks.
        "fallback_baselines": {
            5:       61.35,
            10:      83.68,
            "30min": 42.63,
            "1hr":   55.46,
        },

        # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
        "db_country_name":               "Pakistan",
        "base_table":                    "base_dashboard_data_pak",
        "country_facilities_table":      "health_facilities_pak_osm",
        "province_facilities_template":  "health_facilities_pak_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_pak_{suffix}",
        "province_results_template":     "lgu_accessibility_results_pak_{slug}_province_{suffix}",
    },
    
    "cambodia": {
            # ── Display ───────────────────────────────────────────────────────────
            "display_name":     "Cambodia",
            "iso3":             "khm",
    
            # ── Map defaults ──────────────────────────────────────────────────────
            # Cambodia spans roughly 10.6°N–14.6°N, 102.2°E–107.6°E
            "center_lat":       12.5,
            "center_lon":       104.5,
            "map_zoom":         4.5,
            "province_zoom":    6.0,
    
            # ── Population (2025 World Bank estimate) ─────────────────────────────
            "population":       17_847_982,
    
            # ── Databricks catalog / schema ───────────────────────────────────────
            # Set CAMBODIA_CATALOG, CAMBODIA_FACILITIES_SCHEMA, CAMBODIA_RESULTS_SCHEMA
            # as env vars on Posit Connect before enabling this country.
            "catalog_env":               "CAMBODIA_CATALOG",
            "catalog_default":           "prd_mega",
            "facilities_schema_env":     "CAMBODIA_FACILITIES_SCHEMA",
            "facilities_schema_default": "sgpbpi163",
            "results_schema_env":        "CAMBODIA_RESULTS_SCHEMA",
            "results_schema_default":    "sgpbpi163",
    
            # ── Sub-national administrative units ─────────────────────────────────
            # Cambodia has 23 provinces; each contains districts.  Using provinces as the
            # top-level granularity here; extend to districts when pipeline is ready.
            "subnational_label": "Province",
            "subnational_units": ['Banteay Meanchey', 'Battambang', 'Kampong Cham', 'Kampong Speu', 'Kampong Thom', 
                            'Kampot', 'Kandal', 'Kep', 'Koh Kong', 'Kratie', 'Mondul Kiri', 'Oddar Meanchey', 'Pailin', 'Phnom Penh', 
                            'Preah Sihanouk', 'Preah Vihear', 'Prey Veng', 'Pursat', 'Ratanak Kiri', 'Siemreap', 'Svay Rieng', 'Takeo', 'Tboung Khmum'
                            ],
            "subnational_slugs": {
                "Banteay Meanchey": "banteay_meachey",
                "Battambang": "battambang",
                "Kampong Cham": "kampong_cham",
                "Kampong Speu": "kampong_speu",
                "Kampong Thom": "kampong_thom",
                "Kampot": "kampot",
                "Kandal": "kandal",
                "Kep": "kep",
                "Koh Kong": "koh_kong",
                "Kratie": "kratie",
                "Mondul Kiri": "mondul_kiri",
                "Oddar Meanchey": "oddar_meachey",
                "Pailin": "pailin",
                "Phnom Penh": "phnom_penh",
                "Preah Sihanouk": "preah_sihanouk",
                "Preah Vihear": "preah_vihear",
                "Prey Veng": "prey_veng",
                "Pursat": "pursat",
                "Ratanak Kiri": "ratanak_kiri",
                "Siemreap": "siemreap",
                "Svay Rieng": "svay_rieng",
                "Takeo": "takeo",
                "Tboung Khmum": "tboung_khmum",
            },
    
            # ── Distance bands (same convention as Zambia) ────────────────────────
            "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},
    
            # ── Hardcoded baseline fallbacks ──────────────────────────────────────
            # Update once Malawi baseline data is available in Databricks.
            "fallback_baselines": {
                5:       63.18,
                10:      87.17,
                "30min": 41.63,
                "1hr":   56.4,
            },
    
            # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
            "db_country_name":               "Cambodia",
            "base_table":                    "base_dashboard_data_khm",
            "country_facilities_table":      "health_facilities_khm_osm",
            "province_facilities_template":  "health_facilities_khm_osm_{slug}_province",
            "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
            "country_results_template":      "lgu_accessibility_results_khm_{suffix}",
            "province_results_template":     "lgu_accessibility_results_khm_{slug}_province_{suffix}",
        },

    "burkina_faso": {
            # ── Display ───────────────────────────────────────────────────────────
            "display_name":     "Burkina Faso",
            "iso3":             "bfa",
    
            # ── Map defaults ──────────────────────────────────────────────────────
            # Burkina Faso spans roughly 10.2°N–14.2°N, 7.3°W–3.7°E
            "center_lat":       12.2,
            "center_lon":       0.5,
            "map_zoom":         6.0,
            "province_zoom":    7.0,
    
            # ── Population (2025 World Bank estimate) ─────────────────────────────
            "population":       24_074_580,
    
            # ── Databricks catalog / schema ───────────────────────────────────────
            # Set BURKINA_FASO_CATALOG, BURKINA_FASO_FACILITIES_SCHEMA, BURKINA_FASO_RESULTS_SCHEMA
            # as env vars on Posit Connect before enabling this country.
            "catalog_env":               "BURKINA_FASO_CATALOG",
            "catalog_default":           "prd_mega",
            "facilities_schema_env":     "BURKINA_FASO_FACILITIES_SCHEMA",
            "facilities_schema_default": "sgpbpi163",
            "results_schema_env":        "BURKINA_FASO_RESULTS_SCHEMA",
            "results_schema_default":    "sgpbpi163",
    
            # ── Sub-national administrative units ─────────────────────────────────
            # Burkina Faso has 13 regions; each contains provinces.  Using regions as the
            # top-level granularity here; extend to provinces when pipeline is ready.
            "subnational_label": "Region",
            "subnational_units": [
                "Boucle Du Mouhoun", "Cascades", "Centre", "Centre-est", "Centre-nord", "Centre-ouest", "Centre-sud", 
                "Est", "Hauts-bassins", "Nord", "Plateau Central", "Sahel", "Sud-ouest"
            ],
            "subnational_slugs": {
                "Boucle Du Mouhoun": "boucle_du_mouhoun",
                "Cascades": "cascades",
                "Centre": "centre",
                "Centre-est": "centre_est",
                "Centre-nord": "centre_nord",
                "Centre-ouest": "centre_ouest",
                "Centre-sud": "centre_sud",
                "Est": "est",
                "Hauts-bassins": "hauts_bassins",
                "Nord": "nord",
                "Plateau Central": "plateau_central",
                "Sahel": "sahel",
                "Sud-ouest": "sud_ouest"
            },
    
            # ── Distance bands (same convention as Zambia) ────────────────────────
            "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},
    
            # ── Hardcoded baseline fallbacks ──────────────────────────────────────
            # Update once Malawi baseline data is available in Databricks.
            "fallback_baselines": {
                5:       54.13,
                10:      71.1,
                "30min": 40.3,
                "1hr":   50.33,
            },
    
            # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
            "db_country_name":               "Burkina Faso",
            "base_table":                    "base_dashboard_data_bfa",
            "country_facilities_table":      "health_facilities_bfa_osm",
            "province_facilities_template":  "health_facilities_bfa_osm_{slug}_province",
            "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
            "country_results_template":      "lgu_accessibility_results_bfa_{suffix}",
            "province_results_template":     "lgu_accessibility_results_bfa_{slug}_province_{suffix}",
        },

    "cote_d_ivoire": {
                # ── Display ───────────────────────────────────────────────────────────
                "display_name":     "Côte d'Ivoire",
                "iso3":             "civ",
        
                # ── Map defaults ──────────────────────────────────────────────────────
                # Côte d'Ivoire spans roughly 10.2°N–14.2°N, 7.3°W–3.7°E
                "center_lat":       7.54,
                "center_lon":       -5.55,
                "map_zoom":         6.0,
                "province_zoom":    7.0,
        
                # ── Population (2025 World Bank estimate) ─────────────────────────────
                "population":       32_711_547,
        
                # ── Databricks catalog / schema ───────────────────────────────────────
                # Set COTE_D_IVOIRE_CATALOG, COTE_D_IVOIRE_FACILITIES_SCHEMA, COTE_D_IVOIRE_RESULTS_SCHEMA
                # as env vars on Posit Connect before enabling this country.
                "catalog_env":               "COTE_D_IVOIRE_CATALOG",
                "catalog_default":           "prd_mega",
                "facilities_schema_env":     "COTE_D_IVOIRE_FACILITIES_SCHEMA",
                "facilities_schema_default": "sgpbpi163",
                "results_schema_env":        "COTE_D_IVOIRE_RESULTS_SCHEMA",
                "results_schema_default":    "sgpbpi163",
        
                # ── Sub-national administrative units ─────────────────────────────────
                # Côte d'Ivoire has 14 regions; each contains provinces.  Using regions as the
                # top-level granularity here; extend to provinces when pipeline is ready.
                "subnational_label": "Administrative District",
                "subnational_units": [
                    'Abidjan', 'Bas-Sassandra', 'Comoé', 'Denguélé', 'Gôh-Djiboua', 'Lacs', 'Lagunes', 'Montagnes', 
                    'Sassandra-Marahoué', 'Savanes', 'Vallée du Bandama', 'Woroba', 'Yamoussoukro', 'Zanzan'
                ],

                "subnational_slugs": {
                    "Abidjan": "abidjan",
                    "Bas-Sassandra": "bas_sassandra",
                    "Comoé": "comoe",
                    "Denguélé": "denguele",
                    "Gôh-Djiboua": "goh_djiboua",
                    "Lacs": "lacs",
                    "Lagunes": "lagunes",
                    "Montagnes": "montagnes",
                    "Sassandra-Marahoué": "sassandra_marahoue",
                    "Savanes": "savanes",
                    "Vallée du Bandama": "vallee_du_bandama",
                    "Woroba": "woroba",
                    "Yamoussoukro": "yamoussoukro",
                    "Zanzan": "zanzan"
                },
        
                # ── Distance bands (same convention as Zambia) ────────────────────────
                "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},
        
                # ── Hardcoded baseline fallbacks ──────────────────────────────────────
                # Update once Malawi baseline data is available in Databricks.
                "fallback_baselines": {
                    5:       54.13,
                    10:      71.1,
                    "30min": 40.3,
                    "1hr":   50.33,
                },
        
                # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
                "db_country_name":               "Côte d'Ivoire",
                "base_table":                    "base_dashboard_data_civ",
                "country_facilities_table":      "health_facilities_civ_osm",
                "province_facilities_template":  "health_facilities_civ_osm_{slug}_province",
                "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
                "country_results_template":      "lgu_accessibility_results_civ_{suffix}",
                "province_results_template":     "lgu_accessibility_results_civ_{slug}_province_{suffix}",
            },
    
    "chad": {
                # ── Display ───────────────────────────────────────────────────────────
                "display_name":     "Chad",
                "iso3":             "tcd",
        
                # ── Map defaults ──────────────────────────────────────────────────────
                # Chad spans roughly 10.6°N–14.6°N, 102.2°E–107.6°E
                "center_lat":       15.5,
                "center_lon":       18.7,
                "map_zoom":         4.5,
                "province_zoom":    6.0,
        
                # ── Population (2025 World Bank estimate) ─────────────────────────────
                "population":       21_003_705,
        
                # ── Databricks catalog / schema ───────────────────────────────────────
                # Set CHAD_CATALOG, CHAD_FACILITIES_SCHEMA, CHAD_RESULTS_SCHEMA
                # as env vars on Posit Connect before enabling this country.
                "catalog_env":               "CHAD_CATALOG",
                "catalog_default":           "prd_mega",
                "facilities_schema_env":     "CHAD_FACILITIES_SCHEMA",
                "facilities_schema_default": "sgpbpi163",
                "results_schema_env":        "CHAD_RESULTS_SCHEMA",
                "results_schema_default":    "sgpbpi163",
        
                # ── Sub-national administrative units ─────────────────────────────────
                # Chad has 19 Regions; each contains districts.  Using regions as the
                # top-level granularity here; extend to districts when pipeline is ready.
                "subnational_label": "Region",
                "subnational_units": ['Barh el Ghazel', 'Batha', 'Borkou', 'Chari-Baguirmi', 'Hadjer-Lamis', 'Kanem', 
                                      'Lac', 'Logone Occidental', 'Logone Oriental', 'Mandoul', 'Mayo-Kebbi Est', 
                                      'Mayo-Kebbi Ouest', 'Moyen-Chari', 'Ouaddaï', 'Salamat', 'Sila', 'Tandjilé', 'Wadi Fira'
                                      ],
                "subnational_slugs": {
                    "Barh el Ghazel": "barh_el_ghazel",
                    "Batha": "batha",
                    "Borkou": "borkou",
                    "Chari-Baguirmi": "chari_baguirmi",
                    "Hadjer-Lamis": "hadjer_lamis",
                    "Kanem": "kanem",
                    "Lac": "lac",
                    "Logone Occidental": "logone_occidental",
                    "Logone Oriental": "logone_oriental",
                    "Mandoul": "mandoul",
                    "Mayo-Kebbi Est": "mayo_kebbi_est",
                    "Mayo-Kebbi Ouest": "mayo_kebbi_ouest",
                    "Moyen-Chari": "moyen_chari",
                    "Ouaddaï": "ouaddai",
                    "Salamat": "salamat",
                    "Sila": "sila",
                    "Tandjilé": "tandjile",
                    "Wadi Fira": "wadi_fira"
                },
        
                # ── Distance bands (same convention as Zambia) ────────────────────────
                "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},
        
                # ── Hardcoded baseline fallbacks ──────────────────────────────────────
                # Update once Malawi baseline data is available in Databricks.
                "fallback_baselines": {
                    5:       30.06,
                    10:      45.09,
                    "30min": 21.58,
                    "1hr":   27.33,
                },
        
                # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
                "db_country_name":               "Chad",
                "base_table":                    "base_dashboard_data_tcd",
                "country_facilities_table":      "health_facilities_tcd_osm",
                "province_facilities_template":  "health_facilities_tcd_osm_{slug}_province",
                "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
                "country_results_template":      "lgu_accessibility_results_tcd_{suffix}",
                "province_results_template":     "lgu_accessibility_results_tcd_{slug}_province_{suffix}",
            },

    "gabon": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Gabon",
        "iso3":             "gab",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Gabon spans roughly 0.3°N–4.3°N, 8.5°E–14.5°E
        "center_lat":       2.0,
        "center_lon":       11.5,
        "map_zoom":         6.0,
        "province_zoom":    7.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       2_593_130,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set GABON_CATALOG, GABON_FACILITIES_SCHEMA, GABON_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "GABON_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "GABON_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "GABON_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Gabon has 14 regions; each contains provinces.  Using regions as the
        # top-level granularity here; extend to provinces when pipeline is ready.
        "subnational_label": "Administrative District",
        "subnational_units": ['Estuaire', 'Haut-Ogooue', 'Moyen-Ogooue', 'Ngounie', 
                                'Ogooue-Maritime', 'Ogooue-lolo'],

        "subnational_slugs": {
            "Estuaire": "abidjan",
            "Haut-Ogooue": "haut_ogooue",
            "Moyen-Ogooue": "moyen_ogooue",
            "Ngounie": "ngounie",
            "Ogooue-Maritime": "ogooue_maritime",
            "Ogooue-lolo": "ogooue_lolo"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        # Update once Malawi baseline data is available in Databricks.
        "fallback_baselines": {
            5:       65.55,
            10:      71.41,
            "30min": 52.74,
            "1hr":   63.28,
        },

        # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
        "db_country_name":               "Gabon",
        "base_table":                    "base_dashboard_data_gab",
        "country_facilities_table":      "health_facilities_gab_osm",
        "province_facilities_template":  "health_facilities_gab_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_gab_{suffix}",
        "province_results_template":     "lgu_accessibility_results_gab_{slug}_province_{suffix}",
    },

    "guinea": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Guinea",
        "iso3":             "gin",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Guinea spans roughly 7.5°N–12.5°N, 7.5°W–15.5°W
        "center_lat":       9.95,
        "center_lon":       -9.70,
        "map_zoom":         6.0,
        "province_zoom":    7.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       15_099_727,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set GABON_CATALOG, GABON_FACILITIES_SCHEMA, GABON_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "GABON_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "GABON_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "GABON_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Gabon has 14 regions; each contains provinces.  Using regions as the
        # top-level granularity here; extend to provinces when pipeline is ready.
        "subnational_label": "Region",
        "subnational_units":  ['Boke', 'Conakry', 'Faranah', 'Kankan', 
                               'Kindia', 'Labe', 'Mamou', 'Nzerekore'
                               ],

        "subnational_slugs": {
            "Boke": "boke",
            "Conakry": "conakry",
            "Faranah": "faranah",
            "Kankan": "kankan",
            "Kindia": "kindia",
            "Labe": "labe",
            "Mamou": "mamou",
            "Nzerekore": "nzerekore"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        # Update once Malawi baseline data is available in Databricks.
        "fallback_baselines": {
            5:       62.25,
            10:      80.59,
            "30min": 46.41,
            "1hr":   57.43,
        },

        # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
        "db_country_name":               "Guinea",
        "base_table":                    "base_dashboard_data_gin",
        "country_facilities_table":      "health_facilities_gin_osm",
        "province_facilities_template":  "health_facilities_gin_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_gin_{suffix}",
        "province_results_template":     "lgu_accessibility_results_gin_{slug}_province_{suffix}",
    },

    "the_gambia": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "The Gambia",
        "iso3":             "gmb",

        # ── Map defaults ──────────────────────────────────────────────────────
        # The Gambia spans roughly 12.5°N–13.5°N, 14.5°W–17.5°W
        "center_lat":       13.0,
        "center_lon":       -15.5,
        "map_zoom":         7.0,
        "province_zoom":    8.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       2_822_093,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set THE_GAMBIA_CATALOG, THE_GAMBIA_FACILITIES_SCHEMA, THE_GAMBIA_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "THE_GAMBIA_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "THE_GAMBIA_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "THE_GAMBIA_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # The Gambia has 14 regions; each contains provinces.  Using regions as the
        # top-level granularity here; extend to provinces when pipeline is ready.
        "subnational_label": "Region",
        "subnational_units":  [
                            'Central River North', 'Central River South', 'Kanifing Municipal Council', 
                            'Lower River', 'North Bank', 'Upper River', 'West Coast'
                            ],

        "subnational_slugs": {
            "Central River North": "central_river_north",
            "Central River South": "central_river_south",
            "Kanifing Municipal Council": "kanifing_municipal_council",
            "Lower River": "lower_river",
            "North Bank": "north_bank",
            "Upper River": "upper_river",
            "West Coast": "west_coast"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        # Update once Malawi baseline data is available in Databricks.
        "fallback_baselines": {
            5:       85.14,
            10:      99.75,
            "30min": 59.01,
            "1hr":   78.98,
        },

        # ── Table naming conventions (mirror Zambia; zmb → mwi) ───────────────
        "db_country_name":               "The Gambia",
        "base_table":                    "base_dashboard_data_gmb",
        "country_facilities_table":      "health_facilities_gmb_osm",
        "province_facilities_template":  "health_facilities_gmb_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_gmb_{suffix}",
        "province_results_template":     "lgu_accessibility_results_gmb_{slug}_province_{suffix}",
    },
    
    "cameroon": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Cameroon",
        "iso3":             "cmr",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Cameroon spans roughly 2°N–13°N, 8°E–16°E
        "center_lat":       8.0,
        "center_lon":       12.0,
        "map_zoom":         4.75,
        "province_zoom":    6.50,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       30_915_000,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set CAMEROON_CATALOG, CAMEROON_FACILITIES_SCHEMA, CAMEROON_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "CAMEROON_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "CAMEROON_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "CAMEROON_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Cameroon has 10 regions; using the region-level granularity here.
        "subnational_label": "Region",
        "subnational_units": [
            'Adamaoua', 'Centre', 'Est', 'Extrême - Nord', 'Littoral', 'Nord', 
            'Nord - Ouest', 'Ouest', 'Sud', 'Sud - Ouest'
        ],
        "subnational_slugs": {
            "Adamaoua": "adamaoua",
            "Centre": "centre",
            "Est": "est",
            "Extrême - Nord": "extreme_nord",
            "Littoral": "littoral",
            "Nord": "nord",
            "Nord - Ouest": "nord_ouest",
            "Ouest": "ouest",
            "Sud": "sud",
            "Sud - Ouest": "sud_ouest",
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       56.12,
            10:      73.44,
            "30min": 39.61,
            "1hr":   51.27,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Cameroon",
        "base_table":                    "base_dashboard_data_cmr",
        "country_facilities_table":      "health_facilities_cmr_osm",
        "province_facilities_template":  "health_facilities_cmr_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_cmr_{suffix}",
        "province_results_template":     "lgu_accessibility_results_cmr_{slug}_province_{suffix}",
    },

    "mali": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Mali",
        "iso3":             "mli",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Mali spans roughly 2°N–13°N, 8°E–16°E
        "center_lat":       17.57,
        "center_lon":       -4.00,
        "map_zoom":         4.50,
        "province_zoom":    6.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       24_478_595,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set MALI_CATALOG, MALI_FACILITIES_SCHEMA, MALI_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "MALI_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "MALI_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "MALI_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Mali has 10 regions; using the region-level granularity here.
        "subnational_label": "Province",
        "subnational_units": [
            'District de Bamako', 'Gao', 'Kayes', 'Kidal', 'Koulikoro', 
            'Mopti', 'Sikasso', 'Tombouctou'
        ],
        "subnational_slugs": {
            "District de Bamako": "district_de_bamako",
            "Gao": "gao",
            "Kayes": "kayes",
            "Kidal": "kidal",
            "Koulikoro": "koulikoro",
            "Mopti": "mopti",
            "Sikasso": "sikasso",
            "Tombouctou": "tombouctou"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       60.81,
            10:      0.0,
            "30min": 47.56,
            "1hr":   57.04,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Mali",
        "base_table":                    "base_dashboard_data_mli",
        "country_facilities_table":      "health_facilities_mli_osm",
        "province_facilities_template":  "health_facilities_mli_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_mli_{suffix}",
        "province_results_template":     "lgu_accessibility_results_mli_{slug}_province_{suffix}",
    },

    "niger": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Niger",
        "iso3":             "ner",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Niger spans roughly 10°N–23°N, 0°E–15°E
        "center_lat":       17.60,
        "center_lon":       8.08,
        "map_zoom":         4.50,
        "province_zoom":    6.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       27_917_831,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set NIGER_CATALOG, NIGER_FACILITIES_SCHEMA, NIGER_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "NIGER_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "NIGER_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "NIGER_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Niger has 10 regions; using the region-level granularity here.
        "subnational_label": "Region",
        "subnational_units": [
            'Agadez', 'Communauté Urbaine de Niamey', 'Diffa', 'Dosso', 
            'Maradi', 'Tahoua', 'Tillabéri', 'Zinder'
        ],
        "subnational_slugs": {
            "Agadez": "agadez",
            "Communauté Urbaine de Niamey": "communaute_urbaine_de_niamey",
            "Diffa": "diffa",
            "Dosso": "dosso",
            "Maradi": "maradi",
            "Tahoua": "tahoua",
            "Tillabéri": "tillaberi",
            "Zinder": "zinder"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       37.15,
            10:      0.0,
            "30min": 24.56,
            "1hr":   0.0,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Niger",
        "base_table":                    "base_dashboard_data_ner",
        "country_facilities_table":      "health_facilities_ner_osm",
        "province_facilities_template":  "health_facilities_ner_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_ner_{suffix}",
        "province_results_template":     "lgu_accessibility_results_ner_{slug}_province_{suffix}",
    },

    "afghanistan": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Afghanistan",
        "iso3":             "afg",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Afghanistan spans roughly 29°N–38°N, 60°E–75°E
        "center_lat":       33.97,
        "center_lon":       67.71,
        "map_zoom":         5.0,
        "province_zoom":    6.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       43_844_111,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set AFGHANISTAN_CATALOG, AFGHANISTAN_FACILITIES_SCHEMA, AFGHANISTAN_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "AFGHANISTAN_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "AFGHANISTAN_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "AFGHANISTAN_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Afghanistan has 34 provinces; using the province-level granularity here.
        "subnational_label": "Province",
        "subnational_units": [
            'Badakhshan', 'Baghlan', 'Balkh', 'Bamyan', 'Daykundi', 'Ghazni', 
            'Ghor', 'Hilmand', 'Hirat', 'Kabul', 'Kandahar', 'Kunar', 'Kunduz', 
            'Logar', 'Nangarhar', 'Nimroz', 'Paktya', 'Parwan', 'Samangan'
        ],
        "subnational_slugs": {
            "Badakhshan": "badakhshan",
            "Baghlan": "baghlan",
            "Balkh": "balkh",
            "Bamyan": "bamyan",
            "Daykundi": "daykundi",
            "Ghazni": "ghazni",
            "Ghor": "ghor",
            "Hilmand": "hilmand",
            "Hirat": "hirat",
            "Kabul": "kabul",
            "Kandahar": "kandahar",
            "Kunar": "kunar",
            "Kunduz": "kunduz",
            "Logar": "logar",
            "Nangarhar": "nangarhar",
            "Nimroz": "nimroz",
            "Paktya": "paktya",
            "Parwan": "parwan",
            "Samangan": "samangan"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       41.10,
            10:      53.68,
            "30min": 27.60,
            "1hr":   37.21,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Afghanistan",
        "base_table":                    "base_dashboard_data_afg",
        "country_facilities_table":      "health_facilities_afg_osm",
        "province_facilities_template":  "health_facilities_afg_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_afg_{suffix}",
        "province_results_template":     "lgu_accessibility_results_afg_{slug}_province_{suffix}",
    },

    "somalia": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Somalia",
        "iso3":             "som",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Somalia spans roughly 29°N–38°N, 60°E–75°E
        "center_lat":       5.17,
        "center_lon":       46.2,
        "map_zoom":         5.0,
        "province_zoom":    6.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       19_654_739,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set SOMALIA_CATALOG, SOMALIA_FACILITIES_SCHEMA, SOMALIA_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "SOMALIA_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "SOMALIA_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "SOMALIA_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Somalia has 18 regions; using the region-level granularity here.
        "subnational_label": "Region",
        "subnational_units": [
            'Awdal', 'Banadir', 'Bari', 'Bay', 'Galgaduud', 'Hiraan', 'Juba Hoose', 
            'Shabelle Dhexe', 'Shabelle Hoose', 'Sool', 'Togdheer', 'Woqooyi Galbeed'
        ],
        "subnational_slugs": {
            "Awdal": "awdal",
            "Banadir": "banadir",
            "Bari": "bari",
            "Bay": "bay",
            "Galgaduud": "galgaduud",
            "Hiraan": "hiraan",
            "Juba Hoose": "juba_hoose",
            "Shabelle Dhexe": "shabelle_dhexe",
            "Shabelle Hoose": "shabelle_hoose",
            "Sool": "sool",
            "Togdheer": "togdheer",
            "Woqooyi Galbeed": "woqooyi_galbeed"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       34.01,
            10:      0.0,
            "30min": 24.64,
            "1hr":   0.0,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Somalia",
        "base_table":                    "base_dashboard_data_som",
        "country_facilities_table":      "health_facilities_som_osm",
        "province_facilities_template":  "health_facilities_som_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_som_{suffix}",
        "province_results_template":     "lgu_accessibility_results_som_{slug}_province_{suffix}",
    },

    "sudan": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Sudan",
        "iso3":             "sdn",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Sudan spans roughly 3°N–22°N, 21°E–39°E
        "center_lat":       12.76,
        "center_lon":       30.84,
        "map_zoom":         4.75,
        "province_zoom":    6.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       51_662_147,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set SUDAN_CATALOG, SUDAN_FACILITIES_SCHEMA, SUDAN_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "SUDAN_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "SUDAN_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "SUDAN_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Sudan has 15 states; using the state-level granularity here.
        "subnational_label": "State",
        "subnational_units": [
                'Al Jazeera', 'Blue Nile', 'Gadaref', 'Kassala', 'Khartoum', 'Nile', 'Northern', 
                'Northern Darfur', 'Northern Kordofan', 'Red Sea', 'Southern Darfur', 'Southern Kordofan', 
                'Western Darfur', 'White Nile'
        ],
        "subnational_slugs": {
            "Al Jazeera": "al_jazeera",
            "Blue Nile": "blue_nile",
            "Gadaref": "gadaref",
            "Kassala": "kassala",
            "Khartoum": "khartoum",
            "Nile": "nile",
            "Northern": "northern",
            "Northern Darfur": "northern_darfur",
            "Northern Kordofan": "northern_kordofan",
            "Red Sea": "red_sea",
            "Southern Darfur": "southern_darfur",
            "Southern Kordofan": "southern_kordofan",
            "Western Darfur": "western_darfur",
            "White Nile": "white_nile"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       0.0,
            10:      0.0,
            "30min": 0.0,
            "1hr":   0.0,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Sudan",
        "base_table":                    "base_dashboard_data_sdn",
        "country_facilities_table":      "health_facilities_sdn_osm",
        "province_facilities_template":  "health_facilities_sdn_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_sdn_{suffix}",
        "province_results_template":     "lgu_accessibility_results_sdn_{slug}_province_{suffix}",
    },

    "bangladesh": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Bangladesh",
        "iso3":             "bgd",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Bangladesh spans roughly 20°N–27°N, 88°E–93°E
        "center_lat":       23.68,
        "center_lon":       30.84,
        "map_zoom":         6.0,
        "province_zoom":    7.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       175_686_899,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set BANGLADESH_CATALOG, BANGLADESH_FACILITIES_SCHEMA, BANGLADESH_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "BANGLADESH_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "BANGLADESH_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "BANGLADESH_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Bangladesh has 8 divisions; using the division-level granularity here.
        "subnational_label": "Division",
        "subnational_units": [
            'Barishal', 'Chattogram', 'Dhaka', 'Khulna', 'Mymensingh', 'Rajshahi', 
            'Rangpur', 'Sylhet'
        ],
        "subnational_slugs": {
            "Barishal": "barishal",
            "Chattogram": "chattogram",
            "Dhaka": "dhaka",
            "Khulna": "khulna",
            "Mymensingh": "mymensingh",
            "Rajshahi": "rajshahi",
            "Rangpur": "rangpur",
            "Sylhet": "sylhet"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       88.01,
            10:      0.0,
            "30min": 51.10,
            "1hr":   0.0,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Bangladesh",
        "base_table":                    "base_dashboard_data_bgd",
        "country_facilities_table":      "health_facilities_bgd_osm",
        "province_facilities_template":  "health_facilities_bgd_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_bgd_{suffix}",
        "province_results_template":     "lgu_accessibility_results_bgd_{slug}_province_{suffix}",
    },

    "ethiopia": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Ethiopia",
        "iso3":             "eth",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Ethiopia spans roughly 3°N–15°N, 33°E–48°E
        "center_lat":       8.46,
        "center_lon":       39.82,
        "map_zoom":         5.0,
        "province_zoom":    6.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       135_472_051,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set ETHIOPIA_CATALOG, ETHIOPIA_FACILITIES_SCHEMA, ETHIOPIA_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "ETHIOPIA_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "ETHIOPIA_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "ETHIOPIA_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Ethiopia has 12 regions; using the region-level granularity here.
        "subnational_label": "Region",
        "subnational_units": [
            'Addis Ababa', 'Afar', 'Amhara', 'Dire Dawa', 'Gambela', 'Harari', 'Oromia', 
            'SNNP', 'Sidama', 'Somali', 'South West Ethiopia', 'Tigray'
        ],
        "subnational_slugs": {
            "Addis Ababa": "addis_ababa",
            "Afar": "afar",
            "Amhara": "amhara",
            "Dire Dawa": "dire_dawa",
            "Gambela": "gambela",
            "Harari": "harari",
            "Oromia": "oromia",
            "SNNP": "snnps",
            "Sidama": "sidama",
            "Somali": "somali",
            "Tigray": "tigray",
            "South West Ethiopia": "south_west_ethiopia",
        },
        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       0.0,
            10:      0.0,
            "30min": 15.95,
            "1hr":   0.0,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Ethiopia",
        "base_table":                    "base_dashboard_data_eth",
        "country_facilities_table":      "health_facilities_eth_osm",
        "province_facilities_template":  "health_facilities_eth_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_eth_{suffix}",
        "province_results_template":     "lgu_accessibility_results_eth_{slug}_province_{suffix}",
    },

    "south_sudan": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "South Sudan",
        "iso3":             "ssd",

        # ── Map defaults ──────────────────────────────────────────────────────
        # South Sudan spans roughly 3°N–15°N, 33°E–48°E
        "center_lat":       6.87,
        "center_lon":       31.32,
        "map_zoom":         5.0,
        "province_zoom":    6.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       12_188_788,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set SOUTH_SUDAN_CATALOG, SOUTH_SUDAN_FACILITIES_SCHEMA, SOUTH_SUDAN_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "SOUTH_SUDAN_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "SOUTH_SUDAN_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "SOUTH_SUDAN_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # South Sudan has 10 states; using the state-level granularity here.
        "subnational_label": "State",
        "subnational_units": [
            'Central Equatoria', 'Eastern Equatoria', 'Jonglei', 'Lakes', 
            'Northern Bahr el Ghazal', 'Pibor Administrative Area', 
            'Ruweng Administrative Area', 'Unity', 'Upper Nile', 'Warrap', 
            'Western Bahr el Ghazal', 'Western Equatoria'
        ],
        "subnational_slugs": {
            "Central Equatoria": "central_equatoria",
            "Eastern Equatoria": "eastern_equatoria",
            "Jonglei": "jonglei",
            "Lakes": "lakes",
            "Northern Bahr el Ghazal": "northern_bahr_el_ghazal",
            "Pibor Administrative Area": "pibor_administrative_area",
            "Ruweng Administrative Area": "ruweng_administrative_area",
            "Unity": "unity",
            "Upper Nile": "upper_nile",
            "Warrap": "warrap",
            "Western Bahr el Ghazal": "western_bahr_el_ghazal",
            "Western Equatoria": "western_equatoria"
        },
        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       0.0,
            10:      0.0,
            "30min": 40.21,
            "1hr":   0.0,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "South Sudan",
        "base_table":                    "base_dashboard_data_ssd",
        "country_facilities_table":      "health_facilities_ssd_osm",
        "province_facilities_template":  "health_facilities_ssd_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_ssd_{suffix}",
        "province_results_template":     "lgu_accessibility_results_ssd_{slug}_province_{suffix}",
    },

    "romania": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Romania",
        "iso3":             "rou",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Romania spans roughly 43°N–48°N, 20°E–29°E
        "center_lat":       45.94,
        "center_lon":       24.96,
        "map_zoom":         5.0,
        "province_zoom":    6.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       19_020_271,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set ROMANIA_CATALOG, ROMANIA_FACILITIES_SCHEMA, ROMANIA_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "ROMANIA_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "ROMANIA_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "ROMANIA_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Romania has 42 counties; using the county-level granularity here.
        "subnational_label": "Countie",
        "subnational_units": [
            'Alba', 'Arad', 'Argeş', 'Bacău', 'Bihor', 'Bistriţa-Năsaud', 'Botoşani', 
            'Braşov', 'Brăila', 'Bucureşti', 'Buzău', 'Caraş-Severin', 'Cluj', 'Constanţa', 
            'Covasna', 'Călăraşi', 'Dolj', 'Dâmboviţa', 'Galaţi', 'Giurgiu', 'Gori', 
            'Harghita', 'Hunedoara',  'Iaşi', 'Ilfov', 'Maramureş', 'Mehedinţi', 'Mureş', 
            'Neamţ', 'Olt', 'Prahova', 'Satu Mare', 'Sibiu', 'Suceava', 'Sălaj', 'Teleorman', 
            'Timiş', 'Tulcea', 'Vaslui', 'Vrancea', 'Vâlcea'
        ],
        "subnational_slugs": {
            "Alba": "alba",
            "Arad": "arad",
            "Argeş": "arges",
            "Bacău": "bacau",
            "Bihor": "bihor",
            "Bistriţa-Năsaud": "bistrita_nasaud",
            "Botoşani": "botosani",
            "Braşov": "brasov",
            "Brăila": "braila",
            "Bucureşti": "bucuresti",
            "Buzău": "buzau",
            "Caraş-Severin": "caras_severin",
            "Cluj": "cluj",
            "Constanţa": "constanta",
            "Covasna": "covasna",
            "Călăraşi": "calarasi",
            "Dolj": "dolj",
            "Dâmboviţa": "dambovita",
            "Galaţi": "galati",
            "Giurgiu": "giurgiu",
            "Gorj": "gorj",
            "Harghita": "harghita",
            "Hunedoara": "hunedoara",
            "Iaşi": "iasi",
            "Ilfov": "ilfov",
            "Maramureş": "maramures",
            "Mehedinţi": "mehedinti",
            "Mureş": "mures",
            "Neamţ": "neamt",
            "Olt": "olt",
            "Prahova": "prahova",
            "Satu Mare": "satu_mare",
            "Sibiu": "sibiu",
            "Suceava": "suceava",
            "Sălaj": "salaj",
            "Teleorman": "teleorman",
            "Timiş": "timis",
            "Tulcea": "tulcea",
            "Vaslui": "vaslui",
            "Vrancea": "vrancea",
            "Vâlcea": "valcea",
        },
        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       0.0,
            10:      0.0,
            "30min": 0.0,
            "1hr":   0.0,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Romania",
        "base_table":                    "base_dashboard_data_rou",
        "country_facilities_table":      "health_facilities_rou_osm",
        "province_facilities_template":  "health_facilities_rou_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_rou_{suffix}",
        "province_results_template":     "lgu_accessibility_results_rou_{slug}_province_{suffix}",
    },

    "syria": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Syrian Arab Republic",
        "iso3":             "syr",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Syria spans roughly 32°N–37°N, 36°E–42°E
        "center_lat":       35.0,
        "center_lon":       38.0,
        "map_zoom":         6.0,
        "province_zoom":    7.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       25_620_427,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set SYRIA_CATALOG, SYRIA_FACILITIES_SCHEMA, SYRIA_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "SYRIA_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "SYRIA_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "SYRIA_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Syria has 15 governorates; using the governorate-level granularity here.
        "subnational_label": "Governorate",
        "subnational_units": [
             'Al Ḥasakah', 'Aleppo', 'Ar Raqqah', 'Damascus', 
              'Dar`ā', 'Dayr az Zawr', 'Hama', 'Idlib', 'Latakia', 'Quneitra', 
              'Rif Dimashq', 'Ţarţūs', 'Ḥimṣ'
        ],
        "subnational_slugs": {
            "Al Ḥasakah": "al_hasakah",
            "Aleppo": "aleppo",
            "Ar Raqqah": "ar_raqqah",
            "As Suwaydā'": "as_suwayda",
            "Damascus": "damascus",
            "Dar`ā": "dar_a",
            "Dayr az Zawr": "dayr_az_zawr",
            "Hama": "hama",
            "Idlib": "idlib",
            "Latakia": "latakia",
            "Quneitra": "quneitra",
            "Rif Dimashq": "rif_dimashq",
            "Ţarţūs": "tar_tus",
            "Ḥimṣ": "him_s"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       74.00,
            10:      89.06,
            "30min": 58.09,
            "1hr":   69.00,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Syrian Arab Republic",
        "base_table":                    "base_dashboard_data_syr",
        "country_facilities_table":      "health_facilities_syr_osm",
        "province_facilities_template":  "health_facilities_syr_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_syr_{suffix}",
        "province_results_template":     "lgu_accessibility_results_syr_{slug}_province_{suffix}",
    },

    "west_bank_and_gaza": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "West Bank and Gaza",
        "iso3":             "pse",

        # ── Map defaults ──────────────────────────────────────────────────────
        # West Bank and Gaza spans roughly 31°N–33°N, 34°E–36°E
        "center_lat":       32.0,
        "center_lon":       35.0,
        "map_zoom":         8.0,
        "province_zoom":    9.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       5_413_596,

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set WEST_BANK_GAZA_CATALOG, WEST_BANK_GAZA_FACILITIES_SCHEMA, WEST_BANK_GAZA_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "WEST_BANK_GAZA_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "WEST_BANK_GAZA_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "WEST_BANK_GAZA_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Syria has 15 governorates; using the governorate-level granularity here.
        "subnational_label": "Governorate",
        "subnational_units": [
                'Al Khalil (Hebron)', 'Al Quds (Jerusalem)', 'Bethlehem', 'Deir al Balah', 
                'Gaza', 'Jabalya', 'Jenin', 'Khan Yunis', 'Nablus', 'Qalqiliya', 
                'Rafah', 'Ramallah', 'Salfit', 'Tubas', 'Tulkarm'
        ],
        "subnational_slugs": {
            "Al Khalil (Hebron)": "al_khalil",
            "Al Quds (Jerusalem)": "al_quds",
            "Bethlehem": "bethlehem",
            "Deir al Balah": "deir_al_balah",
            "Gaza": "gaza",
            "Jabalya": "jabalya",
            "Jenin": "jenin",
            "Khan Yunis": "khan_yunis",
            "Nablus": "nablus",
            "Qalqiliya": "qalqiliya",
            "Rafah": "rafah",
            "Ramallah": "ramallah",
            "Salfit": "salfit",
            "Tubas": "tubas",
            "Tulkarm": "tulkarm"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       99.73,
            10:      00.00,
            "30min": 96.93,
            "1hr":   100,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "West Bank and Gaza",
        "base_table":                    "base_dashboard_data_pse",
        "country_facilities_table":      "health_facilities_pse_osm",
        "province_facilities_template":  "health_facilities_pse_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_pse_{suffix}",
        "province_results_template":     "lgu_accessibility_results_pse_{slug}_province_{suffix}",
    },

    "yeman": {
            # ── Display ───────────────────────────────────────────────────────────
            "display_name":     "Republic of Yemen",
            "iso3":             "yem",
    
            # ── Map defaults ──────────────────────────────────────────────────────
            # Yeman spans roughly 12°N–19°N, 42°E–55°E
            "center_lat":       15.5,
            "center_lon":       48.5,
            "map_zoom":         5.0,
            "province_zoom":    6.0,
    
            # ── Population (2025 World Bank estimate) ─────────────────────────────
            "population":       41_773_878,
    
            # ── Databricks catalog / schema ───────────────────────────────────────
            # Set YEMAN_CATALOG, YEMAN_FACILITIES_SCHEMA, YEMAN_RESULTS_SCHEMA
            # as env vars on Posit Connect before enabling this country.
            "catalog_env":               "YEMAN_CATALOG",
            "catalog_default":           "prd_mega",
            "facilities_schema_env":     "YEMAN_FACILITIES_SCHEMA",
            "facilities_schema_default": "sgpbpi163",
            "results_schema_env":        "YEMAN_RESULTS_SCHEMA",
            "results_schema_default":    "sgpbpi163",
    
            # ── Sub-national administrative units ─────────────────────────────────
            # Syria has 15 governorates; using the governorate-level granularity here.
            "subnational_label": "Governorate",
            "subnational_units": [
                    "Abyan", "Al Bayda'", "Al Dali'", "Al Hudaydah", "Al Jawf", "Al Mahrah", 
                    "Al Mahwit", "Amran", "Dhamar", "Hadramawt", "Hajjah", "Ibb", "Lahij", "Ma'rib", "Raymah", "Sa`dah", 
                    "San`a'", "San`a' [City]", "Shabwah", "Socotra", "Ta`izz", "`Adan"
            ],
            "subnational_slugs": {
                "Abyan": "abyan",
                "Al Bayda'": "al_bayda",
                "Al Dali'": "al_dali",
                "Al Hudaydah": "al_hudaydah",
                "Al Jawf": "al_jawf",
                "Al Mahrah": "al_mahrah",
                "Al Mahwit": "al_mahwit",
                "Amran": "amran",
                "Dhamar": "dhamar",
                "Hadramawt": "hadramawt",
                "Hajjah": "hajjah",
                "Ibb": "ibb",
                "Lahij": "lahij",
                "Ma'rib": "ma_rib",
                "Raymah": "raymah",
                "Sa`dah": "sa_dah",
                "San`a'": "san_a",
                "San`a' [City]": "san_a_city",
                "Shabwah": "shabwah",
                "Socotra": "socotra",
                "Ta`izz": "ta_izz",
                "`Adan": "adan"
            },
    
            # ── Distance bands (same convention as Zambia) ────────────────────────
            "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},
    
            # ── Hardcoded baseline fallbacks ──────────────────────────────────────
            "fallback_baselines": {
                5:       97.47,
                10:      100.00,
                "30min": 96.93,
                "1hr":   100,
            },
    
            # ── Table naming conventions ──────────────────────────────────────────
            "db_country_name":               "Republic of Yemen",
            "base_table":                    "base_dashboard_data_yem",
            "country_facilities_table":      "health_facilities_yem_osm",
            "province_facilities_template":  "health_facilities_yem_osm_{slug}_province",
            "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
            "country_results_template":      "lgu_accessibility_results_yem_{suffix}",
            "province_results_template":     "lgu_accessibility_results_yem_{slug}_province_{suffix}",
        },
        
    "haiti": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Haiti",
        "iso3":             "hti",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Haiti spans roughly 18°N–20°N, 71°W–75°W
        "center_lat":       18.5,
        "center_lon":       73.0,
        "map_zoom":         7.0,
        "province_zoom":    8.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       11_906_095, #

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set HAITI_CATALOG, HAITI_FACILITIES_SCHEMA, HAITI_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "HAITI_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "HAITI_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "HAITI_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Haiti has 10 departments; using the department-level granularity here.
        "subnational_label": "Department",
        "subnational_units": [
                'Artibonite', 'Centre', 'Grand-Anse', 'Nippes', 'Nord', 'Nord-Est', 'Nord-Ouest', 'Ouest', 'Sud', 'Sud-Est'
        ],
        "subnational_slugs": {
            "Artibonite": "artibonite",
            "Centre": "centre",
            "Grand-Anse": "grand_anse",
            "Nippes": "nippes",
            "Nord": "nord",
            "Nord-Est": "nord_est",
            "Nord-Ouest": "nord_ouest",
            "Ouest": "ouest",
            "Sud": "sud",
            "Sud-Est": "sud_est"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       99.17,
            10:      100,
            "30min": 83.57,
            "1hr":   97.40,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Haiti",
        "base_table":                    "base_dashboard_data_hti",
        "country_facilities_table":      "health_facilities_hti_osm",
        "province_facilities_template":  "health_facilities_hti_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_hti_{suffix}",
        "province_results_template":     "lgu_accessibility_results_hti_{slug}_province_{suffix}",
    },

    "benin": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Benin",
        "iso3":             "ben",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Benin spans roughly 18°N–20°N, 71°W–75°W
        "center_lat":       18.5,
        "center_lon":       73.0,
        "map_zoom":         6.0,
        "province_zoom":    7.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       14_814_460, #

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set BENIN_CATALOG, BENIN_FACILITIES_SCHEMA, BENIN_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "BENIN_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "BENIN_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "BENIN_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Benin has 10 departments; using the department-level granularity here.
        "subnational_label": "Department",
        "subnational_units": [
                'Alibori', 'Atacora', 'Atlantique', 'Borgou', 'Collines', 
                'Couffo', 'Donga', 'Littoral', 'Mono', 'Oueme', 'Plateau', 
                'Zou'
        ],
        "subnational_slugs": {
            "Alibori": "alibori",
            "Atacora": "atacora",
            "Atlantique": "atlantique",
            "Borgou": "borgou",
            "Collines": "collines",
            "Couffo": "couffo",
            "Donga": "donga",
            "Littoral": "littoral",
            "Mono": "mono",
            "Oueme": "oueme",
            "Plateau": "plateau",
            "Zou": "zou"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       66.49,
            10:      100,
            "30min": 83.57,
            "1hr":   97.40,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Benin",
        "base_table":                    "base_dashboard_data_ben",
        "country_facilities_table":      "health_facilities_ben_osm",
        "province_facilities_template":  "health_facilities_ben_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_ben_{suffix}",
        "province_results_template":     "lgu_accessibility_results_ben_{slug}_province_{suffix}",
    },

    "djibouti": {
        # ── Display ───────────────────────────────────────────────────────────
        "display_name":     "Djibouti",
        "iso3":             "dji",

        # ── Map defaults ──────────────────────────────────────────────────────
        # Djibouti spans roughly 11°N–22°N, 42°E–47°E
        "center_lat":       16.5,
        "center_lon":       45.0,
        "map_zoom":         6.0,
        "province_zoom":    7.0,

        # ── Population (2025 World Bank estimate) ─────────────────────────────
        "population":       1_184_076, #

        # ── Databricks catalog / schema ───────────────────────────────────────
        # Set DJIBOUTI_CATALOG, DJIBOUTI_FACILITIES_SCHEMA, DJIBOUTI_RESULTS_SCHEMA
        # as env vars on Posit Connect before enabling this country.
        "catalog_env":               "DJIBOUTI_CATALOG",
        "catalog_default":           "prd_mega",
        "facilities_schema_env":     "DJIBOUTI_FACILITIES_SCHEMA",
        "facilities_schema_default": "sgpbpi163",
        "results_schema_env":        "DJIBOUTI_RESULTS_SCHEMA",
        "results_schema_default":    "sgpbpi163",

        # ── Sub-national administrative units ─────────────────────────────────
        # Djibouti has 10 departments; using the department-level granularity here.
        "subnational_label": "Region",
        "subnational_units": [
                'Ali Sabieh', 'Jibuti',
        ],
        "subnational_slugs": {
            "Ali Sabieh": "ali_sabieh",
            "Jibuti": "jibuti"
        },

        # ── Distance bands (same convention as Zambia) ────────────────────────
        "distance_km_map": {5: 5, 10: 10, "30min": 2, "1hr": 4},

        # ── Hardcoded baseline fallbacks ──────────────────────────────────────
        "fallback_baselines": {
            5:       76.77,
            10:      0.00,
            "30min": 0.00,
            "1hr":   0.00,
        },

        # ── Table naming conventions ──────────────────────────────────────────
        "db_country_name":               "Djibouti",
        "base_table":                    "base_dashboard_data_dji",
        "country_facilities_table":      "health_facilities_dji_osm",
        "province_facilities_template":  "health_facilities_dji_osm_{slug}_province",
        "results_suffix_map": {5: "5km", 10: "10km", "30min": "2km", "1hr": "4km"},
        "country_results_template":      "lgu_accessibility_results_dji_{suffix}",
        "province_results_template":     "lgu_accessibility_results_dji_{slug}_province_{suffix}",
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
