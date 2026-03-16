"""
queries.py
Databricks SQL data-access layer for the Zambia Health Access dashboard.

Required environment variables:
    DATABRICKS_SERVER_HOSTNAME   — e.g. adb-1234567890.12.azuredatabricks.net
    DATABRICKS_HTTP_PATH         — e.g. /sql/1.0/warehouses/abc123
    DATABRICKS_CLIENT_ID         — OAuth2 service-principal client ID
    DATABRICKS_CLIENT_SECRET     — OAuth2 service-principal client secret

Optional environment variables (override catalog / schema defaults):
    ZAMBIA_CATALOG               — default: prd_mega
    FACILITIES_SCHEMA            — default: sgpbpi163
    RESULTS_SCHEMA               — default: sgpbpi163
    QUERY_CACHE_TTL_SECONDS      — default: 300  (5 minutes)
    QUERY_CACHE_MAX_ENTRIES      — default: 256

The public interface (QueryService.get_instance(), get_existing_facilities(),
get_accessibility_results()) is identical to the CSV trial version so that
app.py and utils.py require zero changes when switching between environments.
"""

import os
import time
import logging
import threading
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal

# ── Load .env file (must happen before any os.getenv calls) ──────────────────
# Install if missing:  pip install python-dotenv
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

# ── Catalog / schema configuration ───────────────────────────────────────────
ZAMBIA_CATALOG    = os.getenv("ZAMBIA_CATALOG",    "prd_mega")
FACILITIES_SCHEMA = os.getenv("FACILITIES_SCHEMA", "sgpbpi163")
RESULTS_SCHEMA    = os.getenv("RESULTS_SCHEMA",    "sgpbpi163")

# ── Cache tuning ──────────────────────────────────────────────────────────────
QUERY_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "300"))
QUERY_CACHE_MAX_ENTRIES = int(os.getenv("QUERY_CACHE_MAX_ENTRIES", "256"))

SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME")

# ── Startup credential validation ─────────────────────────────────────────────
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
        self._cache: dict[str, tuple[float, pd.DataFrame]] = {}
        self._lock  = threading.Lock()

    # ── Cache helpers ──────────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> pd.DataFrame | None:
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
            # Simple FIFO eviction when capacity is reached
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
        """
        Returns all existing health facilities for Zambia.
        Columns: id, lat, lon, name
        """
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
        """
        Returns the optimisation results table sorted ascending by
        total_facilities.  Row 0 = best single new site.
        Columns: total_facilities, new_facility, lat, lon,
                 total_population_access_pct
        """
        query = f"""
            SELECT
                total_facilities,
                new_facility,
                lat,
                lon,
                total_population_access_pct
            FROM {ZAMBIA_CATALOG}.{RESULTS_SCHEMA}.lgu_accessibility_results_zmb
            ORDER BY total_facilities ASC
        """
        df = self.execute_query(query)
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        df["total_population_access_pct"] = pd.to_numeric(
            df["total_population_access_pct"], errors="coerce"
        )
        return df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    def get_user_credentials(self) -> dict[str, str]:
        """
        Returns a {username: bcrypt_hash} mapping for login authentication.
        Only called when AUTH_ENABLED=true.

        Expects a table with columns: username, password_hash
        """
        query = f"""
            SELECT username, password_hash
            FROM {ZAMBIA_CATALOG}.{FACILITIES_SCHEMA}.user_credentials
        """
        df = self.execute_query(query)
        return dict(zip(df["username"], df["password_hash"]))