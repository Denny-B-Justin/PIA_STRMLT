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
