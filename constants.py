# ── Map defaults ──────────────────────────────────────────────────────────────
ZAMBIA_CENTER_LAT   = -13.5
ZAMBIA_CENTER_LON   = 28.0
MAP_ZOOM            = 6

# ── Marker sizes ──────────────────────────────────────────────────────────────
RADIUS_EXISTING_M   = 8_000
RADIUS_NEW_M        = 14_000

# ── Colours ───────────────────────────────────────────────────────────────────
COLOUR_EXISTING     = "#F97316"   # warm orange  — existing facilities
COLOUR_NEW          = "#FFFFFF"   # white fill   — new / proposed facilities
COLOUR_NEW_RING     = "#0EA5E9"   # sky blue ring — new / proposed facilities

# ── Accessibility baseline ────────────────────────────────────────────────────
# Matches row 0 of lgu_accessibility_results_zmb.csv (0 new facilities added).
# Update this value if you regenerate the sample CSVs.
BASELINE_ACCESS_PCT = 79.31

# ── Slider bounds ─────────────────────────────────────────────────────────────
MAX_NEW_FACILITIES  = 30