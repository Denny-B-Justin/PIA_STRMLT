import os
import time
import logging
import threading
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ── Schema / table configuration (env overrides optional) ────────────────────
ZAMBIA_CATALOG       = os.getenv("ZAMBIA_CATALOG", "prd_mega")
FACILITIES_SCHEMA    = os.getenv("FACILITIES_SCHEMA", "sgbpi163")
RESULTS_SCHEMA       = os.getenv("RESULTS_SCHEMA", "sgpbpi163")

# ── Cache tuning (env overrides optional) ─────────────────────────────────────
QUERY_CACHE_TTL_SECONDS = int(os.getenv("QUERY_CACHE_TTL_SECONDS", "300"))   # 5 min
QUERY_CACHE_MAX_ENTRIES = int(os.getenv("QUERY_CACHE_MAX_ENTRIES", "256"))

SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME")


def credentials_provider():
    print("Initializing credential provider...")
    config = Config(
        host          = f"https://{SERVER_HOSTNAME}",
        client_id     = os.getenv("DATABRICKS_CLIENT_ID"),
        client_secret = os.getenv("DATABRICKS_CLIENT_SECRET"),
    )
    return oauth_service_principal(config)


class QueryService:
    _instance = None

    @staticmethod
    def get_instance():
        if QueryService._instance is None:
            QueryService._instance = QueryService()
        return QueryService._instance

    def __init__(self):
        # Simple TTL cache: {query: (expires_at_epoch, dataframe)}
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._cache_ttl = QUERY_CACHE_TTL_SECONDS
        self._cache_max_entries = QUERY_CACHE_MAX_ENTRIES

    # ── Cache helpers ──────────────────────────────────────────────────────────

    def _cache_get(self, key):
        now = time.time()
        with self._cache_lock:
            hit = self._cache.get(key)
            if not hit:
                return None
            expires_at, df = hit
            if now >= expires_at:
                # expired; remove and miss
                del self._cache[key]
                return None
            return df

    def _cache_set(self, key, df):
        expires_at = time.time() + self._cache_ttl
        with self._cache_lock:
            # Evict oldest entry if we exceed max size (simple FIFO)
            if len(self._cache) >= self._cache_max_entries:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            self._cache[key] = (expires_at, df)

    def clear_cache(self):
        with self._cache_lock:
            self._cache.clear()
        logging.info("Query cache cleared")

    def invalidate_query(self, query: str):
        with self._cache_lock:
            removed = self._cache.pop(query, None) is not None
        if removed:
            logging.info("Invalidated cache for query: %s", query)

    # ── Core query executor ───────────────────────────────────────────────────

    def execute_query(self, query):
        """
        Executes a SQL query against Databricks and returns a pandas DataFrame.
        Results are cached in-memory for QUERY_CACHE_TTL_SECONDS seconds.
        """
        cached = self._cache_get(query)
        if cached is not None:
            logging.info("CACHE HIT for query (TTL=%ss): %s", self._cache_ttl, query)
            return cached.copy(deep=True)

        start = time.time()
        with sql.connect(
            server_hostname    = SERVER_HOSTNAME,
            http_path          = os.getenv("DATABRICKS_HTTP_PATH"),
            credentials_provider = credentials_provider,
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            df = cursor.fetchall_arrow().to_pandas()

        logging.info(
            "DB MISS (queried) took %.2f sec. query: %s",
            time.time() - start,
            query,
        )

        self._cache_set(query, df)
        return df.copy(deep=True)

    # ── Domain queries ────────────────────────────────────────────────────────

    def get_existing_facilities(self):
        """
        Returns all existing health facilities for Zambia.
        Columns: id, lat, lon, name
        """
        query = f"""
            SELECT id, lat, lon, name
            FROM {ZAMBIA_CATALOG}.{FACILITIES_SCHEMA}.health_facilities_zmb
        """
        df = self.execute_query(query)
        df["lat"]  = pd.to_numeric(df["lat"],  errors="coerce")
        df["lon"]  = pd.to_numeric(df["lon"],  errors="coerce")
        df["name"] = df["name"].fillna("Health Facility")
        return df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    def get_accessibility_results(self):
        """
        Returns the full optimisation results table sorted ascending by
        total_facilities. Row 0 = best single new site (total_facilities = 1259).
        Columns: total_facilities, new_facility, lat, lon, total_population_access_pct
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