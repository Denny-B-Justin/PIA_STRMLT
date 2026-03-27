"""
queries.py
Databricks SQL data-access layer for the Zambia Health Access dashboard.
...
"""

import os
import time
import logging
import threading
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal
from typing import Dict, Optional, Tuple  # ← all generics from typing

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


class QueryService:
    """
    Singleton data-access object with in-memory TTL query cache.

    Thread-safe: uses a lock around cache reads/writes so multiple Dash
    worker threads share a single cache without race conditions.
    """

    _instance = None

    @staticmethod
    def get_instance() -> "QueryService":
        if QueryService._instance is None:
            QueryService._instance = QueryService()
        return QueryService._instance

    def __init__(self):
        # {sql_string: (expires_at_epoch, dataframe)}
        self._cache: Dict[str, Tuple[float, pd.DataFrame]] = {}  # ← Dict/Tuple from typing
        self._lock  = threading.Lock()

    # ── Cache helpers ──────────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> Optional[pd.DataFrame]:          # ← Optional (already correct)
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

    # ── Domain queries ────────────────────────────────────────────────────────

    def get_existing_facilities(self) -> pd.DataFrame:
        query = f"""
            SELECT id, lat, lon, name
            FROM {ZAMBIA_CATALOG}.{FACILITIES_SCHEMA}.health_facilities_zmb
            ORDER BY id ASC
        """
        df = self.execute_query(query)
        df["lat"]  = pd.to_numeric(df["lat"],  errors="coerce")
        df["lon"]  = pd.to_numeric(df["lon"],  errors="coerce")
        df["name"] = df["name"].fillna("Health Facility")
        return df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    def get_accessibility_results(self) -> pd.DataFrame:
        query = f"""
            SELECT
                total_facilities,
                new_facility,
                lat,
                lon,
                total_population_access_pct,
                district
            FROM {ZAMBIA_CATALOG}.{RESULTS_SCHEMA}.lgu_accessibility_results_zmb_10km
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

    def get_accessibility_results_by_distance(self, distance_km: int = 10) -> pd.DataFrame:
        """
        Fetch optimisation results for the given catchment radius.
        distance_km must be 5 or 10; maps to:
          5  → lgu_accessibility_results_zmb_5km
          10 → lgu_accessibility_results_zmb_10km
        """
        table = f"lgu_accessibility_results_zmb_{distance_km}km"
        query = f"""
            SELECT
                total_facilities,
                new_facility,
                lat,
                lon,
                total_population_access_pct,
                district
            FROM {ZAMBIA_CATALOG}.{RESULTS_SCHEMA}.{table}
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

    def get_user_credentials(self) -> Dict[str, str]:              # ← Dict from typing
        query = f"""
            SELECT username, password_hash
            FROM {ZAMBIA_CATALOG}.{FACILITIES_SCHEMA}.user_credentials
        """
        df = self.execute_query(query)
        return dict(zip(df["username"], df["password_hash"]))
    
    def get_gadm_boundary_wkt(self) -> Optional[str]:
        """
        Return the Zambia national boundary geometry as a WKT string.

        The gadm_boundaries_zmb table contains the country-level (GADM level-0)
        polygon(s).  We take the first row; for a single-country dashboard this
        is always the full national boundary.
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