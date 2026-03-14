"""
queries.py
Data-access layer for the trial version.

Instead of connecting to Databricks, all data is read from two CSV files
that live in the same directory as this script:

  health_facilities_zmb.csv          → existing health facilities
  lgu_accessibility_results_zmb.csv  → optimisation results

The public interface (QueryService.get_instance(), get_existing_facilities(),
get_accessibility_results()) is identical to the Databricks version so that
app.py and utils.py require no changes.
"""

import os
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# ── File paths (same folder as this script) ───────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))

FACILITIES_CSV = os.path.join(_HERE, "health_facilities_zmb.csv")
RESULTS_CSV    = os.path.join(_HERE, "lgu_accessibility_results_zmb_30.csv")


class QueryService:
    """
    Singleton data-access object.
    Loads CSVs once on first access and caches them in memory.
    """

    _instance = None

    @staticmethod
    def get_instance():
        if QueryService._instance is None:
            QueryService._instance = QueryService()
        return QueryService._instance

    def __init__(self):
        self._facilities_cache  = None
        self._results_cache     = None

    # ── Public domain queries (same signatures as Databricks version) ─────────

    def get_existing_facilities(self) -> pd.DataFrame:
        """
        Returns all existing health facilities.
        Columns: id, lat, lon, name
        """
        if self._facilities_cache is not None:
            logging.info("CACHE HIT: existing facilities")
            return self._facilities_cache.copy()

        logging.info("Loading existing facilities from %s", FACILITIES_CSV)
        df = pd.read_csv(FACILITIES_CSV)

        df["lat"]  = pd.to_numeric(df["lat"],  errors="coerce")
        df["lon"]  = pd.to_numeric(df["lon"],  errors="coerce")
        df["name"] = df["name"].fillna("Health Facility")
        df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

        self._facilities_cache = df
        logging.info("Loaded %d existing facilities", len(df))
        return df.copy()

    def get_accessibility_results(self) -> pd.DataFrame:
        """
        Returns the optimisation results table sorted ascending by
        total_facilities.  Row 0 = first new site added.
        Columns: total_facilities, new_facility, lat, lon,
                 total_population_access_pct
        """
        if self._results_cache is not None:
            logging.info("CACHE HIT: accessibility results")
            return self._results_cache.copy()

        logging.info("Loading accessibility results from %s", RESULTS_CSV)
        df = pd.read_csv(RESULTS_CSV)

        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        df["total_population_access_pct"] = pd.to_numeric(
            df["total_population_access_pct"], errors="coerce"
        )
        df = (
            df.dropna(subset=["lat", "lon"])
            .sort_values("total_facilities")
            .reset_index(drop=True)
        )

        self._results_cache = df
        logging.info("Loaded %d optimisation rows", len(df))
        return df.copy()

    # ── Cache management ──────────────────────────────────────────────────────

    def clear_cache(self):
        """Force a reload from CSV on next access."""
        self._facilities_cache = None
        self._results_cache    = None
        logging.info("Query cache cleared")