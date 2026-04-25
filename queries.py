
import os
import time
import logging
import threading
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal
from typing import Dict, Optional, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.info("Loaded environment from .env file")
except ImportError:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logging.warning("python-dotenv not installed — reading env vars from system only")

# ── Backward-compat module-level catalog / schema constants ───────────────────
# These are kept so that get_user_credentials / get_gadm_boundary_wkt (which
# are Zambia-only helpers) continue to resolve the correct tables.
# Country-aware methods resolve their own catalog / schema via _get_catalog() etc.

ZAMBIA_CATALOG    = os.getenv("ZAMBIA_CATALOG",    "prd_mega")
FACILITIES_SCHEMA = os.getenv("FACILITIES_SCHEMA", "sgpbpi163")
RESULTS_SCHEMA    = os.getenv("RESULTS_SCHEMA",    "sgpbpi163")

QUERY_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "300"))
QUERY_CACHE_MAX_ENTRIES = int(os.getenv("QUERY_CACHE_MAX_ENTRIES", "256"))

SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME")

_REQUIRED = {
    "DATABRICKS_SERVER_HOSTNAME": SERVER_HOSTNAME,
    "DATABRICKS_HTTP_PATH":       os.getenv("DATABRICKS_HTTP_PATH"),
    "DATABRICKS_CLIENT_ID":       os.getenv("DATABRICKS_CLIENT_ID"),
    "DATABRICKS_CLIENT_SECRET":   os.getenv("DATABRICKS_CLIENT_SECRET"),
}
_missing = [k for k, v in _REQUIRED.items() if not v]
if _missing:
    raise EnvironmentError(
        "\n\nMissing required environment variables:\n"
        + "\n".join(f"  {k}" for k in _missing)
        + "\n\nCreate a .env file in the project folder with:\n"
        + "  DATABRICKS_SERVER_HOSTNAME=adb-xxxx.azuredatabricks.net\n"
        + "  DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123\n"
        + "  DATABRICKS_CLIENT_ID=your-client-id\n"
        + "  DATABRICKS_CLIENT_SECRET=your-client-secret\n"
    )


def credentials_provider():
    """OAuth2 service-principal credentials for Databricks SQL connector."""
    config = Config(
        host          = f"https://{SERVER_HOSTNAME}",
        client_id     = os.getenv("DATABRICKS_CLIENT_ID"),
        client_secret = os.getenv("DATABRICKS_CLIENT_SECRET"),
    )
    return oauth_service_principal(config)


# ── Per-country catalog / schema helpers ──────────────────────────────────────

def _get_catalog(cfg: dict) -> str:
    """Resolve the Unity Catalog name for the given country config."""
    return os.getenv(cfg["catalog_env"], cfg["catalog_default"])


def _get_facilities_schema(cfg: dict) -> str:
    """Resolve the facilities schema name for the given country config."""
    return os.getenv(cfg["facilities_schema_env"], cfg["facilities_schema_default"])


def _get_results_schema(cfg: dict) -> str:
    """Resolve the results schema name for the given country config."""
    return os.getenv(cfg["results_schema_env"], cfg["results_schema_default"])


class QueryService:
    """
    Singleton data-access object with in-memory TTL query cache.

    Thread-safe: uses a lock around cache reads/writes so multiple Dash
    worker threads share a single cache without race conditions.

    All public domain methods accept a `country` keyword argument (default
    "zambia") so the same instance serves every country without separate
    connections or caches.
    """

    _instance = None

    @staticmethod
    def get_instance() -> "QueryService":
        if QueryService._instance is None:
            QueryService._instance = QueryService()
        return QueryService._instance

    def __init__(self):
        # {sql_string: (expires_at_epoch, dataframe)}
        self._cache: Dict[str, Tuple[float, pd.DataFrame]] = {}
        self._lock  = threading.Lock()

    # ── Cache helpers ──────────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> Optional[pd.DataFrame]:
        now = time.time()
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            expires_at, df = entry
            if now >= expires_at:
                del self._cache[key]
                return None
            return df

    def _cache_set(self, key: str, df: pd.DataFrame) -> None:
        expires_at = time.time() + QUERY_CACHE_TTL_SECONDS
        with self._lock:
            if len(self._cache) >= QUERY_CACHE_MAX_ENTRIES:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[key] = (expires_at, df)

    def clear_cache(self) -> None:
        """Flush the entire query cache."""
        with self._lock:
            self._cache.clear()
        logging.info("Query cache cleared")

    def invalidate_query(self, query: str) -> None:
        """Remove a single query's cached result."""
        with self._lock:
            removed = self._cache.pop(query, None) is not None
        if removed:
            logging.info("Invalidated cache for query: %s", query[:80])

    # ── Core executor ─────────────────────────────────────────────────────────

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query against Databricks and return a pandas DataFrame.
        Results are cached for QUERY_CACHE_TTL_SECONDS seconds.
        """
        cached = self._cache_get(query)
        if cached is not None:
            logging.info("CACHE HIT (TTL=%ss): %s…", QUERY_CACHE_TTL_SECONDS, query[:60])
            return cached.copy(deep=True)

        t0 = time.time()
        with sql.connect(
            server_hostname      = SERVER_HOSTNAME,
            http_path            = os.getenv("DATABRICKS_HTTP_PATH"),
            credentials_provider = credentials_provider,
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows    = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df      = pd.DataFrame(rows, columns=columns)

        logging.info(
            "DB MISS — queried in %.2fs: %s…",
            time.time() - t0,
            query[:60],
        )
        self._cache_set(query, df)
        return df.copy(deep=True)

    # ── Backward-compat wrappers (Zambia-only) ────────────────────────────────

    def get_existing_facilities(self) -> pd.DataFrame:
        """Backward-compat wrapper — returns all national Zambia facilities."""
        return self.get_existing_facilities_for_location("zambia", country="zambia")

    def get_accessibility_results(self) -> pd.DataFrame:
        """Backward-compat wrapper — fetches the default 10 km Zambia results."""
        return self.get_accessibility_results_for_location("zambia", 10, country="zambia")

    def get_accessibility_results_by_distance(self, distance_km=10) -> pd.DataFrame:
        """Backward-compat wrapper — fetches Zambia-level results for the given distance."""
        return self.get_accessibility_results_for_location("zambia", distance_km, country="zambia")

    # ── Country-aware domain queries ──────────────────────────────────────────

    def get_existing_facilities_for_location(
        self,
        location: str = "zambia",
        *,
        country: str = "zambia",
    ) -> pd.DataFrame:
        """
        Fetch existing health facilities for the given location and country.

        Table resolution (driven by COUNTRY_CONFIGS templates):
          Country-level  → cfg["country_facilities_table"]
          Subnational    → cfg["province_facilities_template"].format(slug=slug)

        The `location` value equals the country slug for country-level views
        (e.g. "zambia" when country="zambia", "malawi" when country="malawi")
        and equals the subnational unit display name otherwise
        (e.g. "Central", "Northern").

        QueryService caches each table result independently, so switching
        between locations after the first load is near-instant.
        """
        from constants import get_country_config

        cfg    = get_country_config(country)
        loc    = (location or country).strip()
        cat    = _get_catalog(cfg)
        schema = _get_facilities_schema(cfg)

        if loc.lower() == country.lower():
            # Country-level view
            table = cfg["country_facilities_table"]
        else:
            # Subnational view — look up the slug from the config, fall back to
            # a normalised form of the display name if not found.
            slug  = cfg["subnational_slugs"].get(
                loc,
                loc.lower().replace("-", "_").replace(" ", "_"),
            )
            table = cfg["province_facilities_template"].format(slug=slug)

        logging.info(
            "Fetching existing facilities from %s.%s.%s (country=%s, location=%s)",
            cat, schema, table, country, loc,
        )

        query = f"""
            SELECT id, lat, lon, name
            FROM {cat}.{schema}.{table}
            ORDER BY id ASC
        """
        df = self.execute_query(query)
        df["lat"]  = pd.to_numeric(df["lat"],  errors="coerce")
        df["lon"]  = pd.to_numeric(df["lon"],  errors="coerce")
        df["name"] = df["name"].fillna("Health Facility")
        logging.info(
            "Fetched %d existing facilities for country='%s' location='%s' (table=%s)",
            len(df), country, loc, table,
        )
        return df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    def get_base_dashboard_data(
        self,
        location: str = "zambia",
        distance_km=5,
        *,
        country: str = "zambia",
    ) -> dict:
        """
        Fetch map-center coordinates, boundary WKT, baseline access %, and
        total new facilities from the country's base_dashboard_data table.

        location   : country slug (e.g. "zambia") for the whole country, or a
                     subnational unit display name (e.g. "Lusaka", "Northern").
        distance_km: 5 | 10 | "30min" | "1hr"
        country    : country slug (e.g. "zambia", "malawi")

        Returns a plain dict with keys:
          center_lat, center_lon, zoom, geometry_wkt,
          current_access, total_new_facilities, location
        """
        from constants import get_country_config

        cfg      = get_country_config(country)
        loc      = (location or country).strip()
        cat      = _get_catalog(cfg)
        schema   = _get_facilities_schema(cfg)
        table    = cfg["base_table"]
        dist_map = cfg["distance_km_map"]

        # The table stores distance_km as integers; map walk-time bands to km.
        dist_int = dist_map.get(distance_km if distance_km is not None else 5, 5)

        if loc.lower() == country.lower():
            province_clause = "province IS NULL"
            default_zoom    = cfg["map_zoom"]
        else:
            # Escape single quotes defensively
            safe_province   = loc.replace("'", "''")
            province_clause = f"province = '{safe_province}'"
            if country.lower() == "malawi":
                province_clause = f"province = '{safe_province} Region'"
            default_zoom    = cfg["province_zoom"]

        db_country = cfg["db_country_name"].replace("'", "''")

        query = f"""
            SELECT central_lat, central_long, current_access,
                   total_new_facilities, geometry_wkt
            FROM {cat}.{schema}.{table}
            WHERE country = '{db_country}'
              AND {province_clause}
              AND distance_km = {dist_int}
            LIMIT 1
        """
        df = self.execute_query(query)

        fallback_baselines = cfg["fallback_baselines"]
        fallback_access    = fallback_baselines.get(distance_km, fallback_baselines.get(5, 0.0))

        fallback = {
            "center_lat":           cfg["center_lat"],
            "center_lon":           cfg["center_lon"],
            "zoom":                 default_zoom,
            "geometry_wkt":         None,
            "current_access":       fallback_access,
            "total_new_facilities": 50,
            "location":             loc,
        }
        if df.empty:
            logging.warning(
                "%s returned no rows for country=%s location=%s dist_int=%s",
                table, country, loc, dist_int,
            )
            return fallback

        row = df.iloc[0]

        def _safe_float(val, default):
            try:
                return float(val) if pd.notna(val) else default
            except (TypeError, ValueError):
                return default

        def _safe_int(val, default):
            try:
                return int(val) if pd.notna(val) else default
            except (TypeError, ValueError):
                return default

        return {
            "center_lat":           _safe_float(row.get("central_lat"),         cfg["center_lat"]),
            "center_lon":           _safe_float(row.get("central_long"),         cfg["center_lon"]),
            "zoom":                 default_zoom,
            "geometry_wkt":         str(row["geometry_wkt"]) if pd.notna(row.get("geometry_wkt")) else None,
            "current_access":       _safe_float(row.get("current_access"),       fallback_access),
            "total_new_facilities": _safe_int(row.get("total_new_facilities"),   50),
            "location":             loc,
        }

    def get_accessibility_results_for_location(
        self,
        location: str = "zambia",
        distance_km=5,
        *,
        country: str = "zambia",
    ) -> pd.DataFrame:
        """
        Fetch MCLP optimisation results for the given location, distance, and country.

        Table-name resolution is driven entirely by the COUNTRY_CONFIGS templates,
        so new countries or naming conventions only require a constants.py change.

        Example resolutions for Zambia:
          country-level, Driving 5 km   → lgu_accessibility_results_zmb_5km
          country-level, Walking 30 min → lgu_accessibility_results_zmb_2km
          province, Driving 10 km       → lgu_accessibility_results_zmb_central_province_10km

        Example resolutions for Malawi:
          country-level, Driving 5 km   → lgu_accessibility_results_mwi_5km
          region, Walking 1 hr          → lgu_accessibility_results_mwi_northern_region_4km
        """
        from constants import get_country_config

        cfg    = get_country_config(country)
        loc    = (location or country).strip()
        cat    = _get_catalog(cfg)
        schema = _get_results_schema(cfg)

        suffix_map = cfg["results_suffix_map"]
        suffix     = suffix_map.get(distance_km, "5km")

        if loc.lower() == country.lower():
            table = cfg["country_results_template"].format(suffix=suffix)
        else:
            slug  = cfg["subnational_slugs"].get(
                loc,
                loc.lower().replace("-", "_").replace(" ", "_"),
            )
            table = cfg["province_results_template"].format(slug=slug, suffix=suffix)

        logging.info(
            "Fetching results from %s.%s.%s (country=%s, location=%s, distance=%s)",
            cat, schema, table, country, loc, distance_km,
        )

        query = f"""
            SELECT
                total_facilities,
                new_facility,
                lat,
                lon,
                total_population_access_pct,
                district
            FROM {cat}.{schema}.{table}
            ORDER BY total_facilities ASC
        """
        df = self.execute_query(query)
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        df["district"] = df["district"].fillna("—")
        df["total_population_access_pct"] = pd.to_numeric(
            df["total_population_access_pct"], errors="coerce"
        )
        return df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    # ── Zambia-specific helpers (kept for backward compat) ────────────────────

    def get_user_credentials(self) -> Dict[str, str]:
        query = f"""
            SELECT username, password_hash
            FROM {ZAMBIA_CATALOG}.{FACILITIES_SCHEMA}.user_credentials
        """
        df = self.execute_query(query)
        return dict(zip(df["username"], df["password_hash"]))

    def get_gadm_boundary_wkt(self) -> Optional[str]:
        """
        Return the Zambia national boundary geometry as a WKT string.
        Kept for backward compatibility; prefer get_base_dashboard_data().
        """
        query = f"""
            SELECT geometry_wkt
            FROM {ZAMBIA_CATALOG}.{FACILITIES_SCHEMA}.gadm_boundaries_zmb
            LIMIT 1
        """
        df = self.execute_query(query)
        if df.empty:
            logging.warning("gadm_boundaries_zmb returned no rows")
            return None
        val = df["geometry_wkt"].iloc[0]
        if val is None:
            logging.warning("gadm_boundaries_zmb geometry_wkt is NULL")
            return None
        return str(val)