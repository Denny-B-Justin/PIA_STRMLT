"""
GoAT — Databricks SQL query service.

Design:
  • OAuth2 service-principal credentials (no PAT)
  • In-memory TTL cache, thread-safe via a lock
  • All SQL assembled from filter parameters — never hand-edited strings in app.py
  • Keyword search runs fully in-process via vectorised Pandas (no row-wise apply)
    for optimal performance on ~10 000-row DataFrames.

All public methods return plain pandas DataFrames; callers never import `sql`.
"""

from __future__ import annotations

import os
import re
import time
import logging
import threading
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal
from typing import Dict, List, Optional, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.info("Loaded environment from .env file")
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.warning("python-dotenv not installed — reading env vars from system only")

from goat_src.constants import (
    GOAT_TABLE,
    HIERARCHY_TABLE,
    QUERY_CACHE_TTL_SECONDS,
    QUERY_CACHE_MAX_ENTRIES,
    COL_PROJ_ID,
    COL_APPRVL_FY,
    COL_PROJ_STAT,
    COL_LEND_INSTR,
    COL_REGION,
    COL_HIERARCHY,
    COL_IS_HIER,
    COL_IS_HIER_YES,
    COL_VALID_HIER,
    COL_HIER_FULLNAME,
    COL_HIER_KEYWORD,
    COL_HIER_SHORT,
    COL_HIER_CATEGORY,
    DOWNLOAD_COLUMNS,
    KEYWORD_SEARCH_COLUMNS,
)

logger = logging.getLogger(__name__)

# ── Environment variable validation ───────────────────────────────────────────
SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME")

_REQUIRED: Dict[str, Optional[str]] = {
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
        + "\n\nCreate a .env file in the project root.  See .env.sample for reference.\n"
    )


# ── OAuth2 credentials provider ────────────────────────────────────────────────

def credentials_provider():
    """Return OAuth2 service-principal credentials for the Databricks SQL connector."""
    config = Config(
        host          = f"https://{SERVER_HOSTNAME}",
        client_id     = os.getenv("DATABRICKS_CLIENT_ID"),
        client_secret = os.getenv("DATABRICKS_CLIENT_SECRET"),
    )
    return oauth_service_principal(config)


# ═══════════════════════════════════════════════════════════════════════════════
# SQL builder helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _quote_list(values: List[str]) -> str:
    """
    Produce a SQL IN-list literal: ('val1', 'val2', ...).
    Internal single-quotes are doubled to prevent injection.
    """
    escaped = ", ".join(f"'{v.replace(chr(39), chr(39) * 2)}'" for v in values)
    return f"({escaped})"


def _hierarchy_subquery(hierarchies: List[str], and_or: str) -> str:
    """
    Return a correlated subquery selecting PROJ_IDs that satisfy the
    keyword / hierarchy filter.

    AND  (n > 1) → project must contain ALL listed hierarchies
    OR            → project must contain ANY listed hierarchy
    """
    hier_sql = _quote_list(hierarchies)
    n        = len(hierarchies)

    if and_or == "AND" and n > 1:
        return (
            f"(\n"
            f"    SELECT   {COL_PROJ_ID}\n"
            f"    FROM     {GOAT_TABLE}\n"
            f"    WHERE    {COL_HIERARCHY}     IN {hier_sql}\n"
            f"      AND    {COL_IS_HIER}       = '{COL_IS_HIER_YES}'\n"
            f"      AND    {COL_VALID_HIER}    = 'True'\n"
            f"    GROUP BY {COL_PROJ_ID}\n"
            f"    HAVING   COUNT(DISTINCT {COL_HIERARCHY}) = {n}\n"
            f")"
        )

    return (
        f"(\n"
        f"    SELECT DISTINCT {COL_PROJ_ID}\n"
        f"    FROM            {GOAT_TABLE}\n"
        f"    WHERE           {COL_HIERARCHY}  IN {hier_sql}\n"
        f"      AND           {COL_IS_HIER}    = '{COL_IS_HIER_YES}'\n"
        f"      AND           {COL_VALID_HIER} = 'True'\n"
        f")"
    )


def _build_where(
    instruments: Optional[List[str]],
    regions:     Optional[List[str]],
    hierarchies: Optional[List[str]],
    and_or:      str,
) -> str:
    """
    Assemble a WHERE clause from the three filter dimensions.
    Always includes Valid_Hierarchy = 'True' guard.
    Returns a WHERE string (may be empty for unfiltered queries).
    """
    conditions: List[str] = [f"{COL_VALID_HIER} = 'True'"]

    if instruments:
        conditions.append(f"{COL_LEND_INSTR} IN {_quote_list(instruments)}")

    if regions:
        conditions.append(f"{COL_REGION} IN {_quote_list(regions)}")

    if hierarchies:
        conditions.append(
            f"{COL_PROJ_ID} IN {_hierarchy_subquery(hierarchies, and_or)}"
        )

    return "WHERE\n    " + "\n    AND ".join(conditions)


# ═══════════════════════════════════════════════════════════════════════════════
# Named query builders — Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

def build_project_status_query(
    instruments: Optional[List[str]] = None,
    regions:     Optional[List[str]] = None,
    hierarchies: Optional[List[str]] = None,
    and_or:      str                 = "AND",
) -> str:
    """Stacked-bar: distinct project count by approval FY × project status."""
    where = _build_where(instruments, regions, hierarchies, and_or)
    return (
        f"SELECT\n"
        f"    {COL_APPRVL_FY}                AS approval_fy,\n"
        f"    {COL_PROJ_STAT}                AS project_status,\n"
        f"    COUNT(DISTINCT {COL_PROJ_ID})  AS project_count\n"
        f"FROM {GOAT_TABLE}\n"
        f"{where}\n"
        f"GROUP BY {COL_APPRVL_FY}, {COL_PROJ_STAT}\n"
        f"ORDER BY {COL_APPRVL_FY} ASC"
    )


def build_lending_instrument_query(
    instruments: Optional[List[str]] = None,
    regions:     Optional[List[str]] = None,
    hierarchies: Optional[List[str]] = None,
    and_or:      str                 = "AND",
) -> str:
    """Stacked-bar: distinct project count by approval FY × lending instrument."""
    where = _build_where(instruments, regions, hierarchies, and_or)
    return (
        f"SELECT\n"
        f"    {COL_APPRVL_FY}                AS approval_fy,\n"
        f"    {COL_LEND_INSTR}               AS lending_instrument,\n"
        f"    COUNT(DISTINCT {COL_PROJ_ID})  AS project_count\n"
        f"FROM {GOAT_TABLE}\n"
        f"{where}\n"
        f"GROUP BY {COL_APPRVL_FY}, {COL_LEND_INSTR}\n"
        f"ORDER BY {COL_APPRVL_FY} ASC"
    )


def build_total_count_query(
    instruments: Optional[List[str]] = None,
    regions:     Optional[List[str]] = None,
    hierarchies: Optional[List[str]] = None,
    and_or:      str                 = "AND",
) -> str:
    """Scalar: total distinct project count matching the active filters."""
    where = _build_where(instruments, regions, hierarchies, and_or)
    return (
        f"SELECT COUNT(DISTINCT {COL_PROJ_ID}) AS total_projects\n"
        f"FROM {GOAT_TABLE}\n"
        f"{where}"
    )


def build_download_query(
    instruments: Optional[List[str]] = None,
    regions:     Optional[List[str]] = None,
    hierarchies: Optional[List[str]] = None,
    and_or:      str                 = "AND",
) -> str:
    """
    Project-level rows for Download Data tab / CSV export — one row per PROJ_ID.

    NOTE: this used to be `SELECT DISTINCT` over DOWNLOAD_COLUMNS, but that only
    collapses rows that are identical across EVERY selected column. DOWNLOAD_COLUMNS
    includes COL_DLI ("DLI_AMT"), which also appears in KEYWORD_SEARCH_COLUMNS —
    i.e. it's a granular field that varies across the same hierarchy-duplicated
    GOAT_TABLE rows this whole app has to dedupe around. So DISTINCT was silently
    emitting multiple rows per project whenever DLI_AMT differed between a
    project's hierarchy-tagged rows. Fixed by picking one deterministic row per
    project (same tiebreak pattern as _get_full_goat_df_deduplicated) instead of
    relying on column-wise DISTINCT.
    """
    cols  = ",\n    ".join(DOWNLOAD_COLUMNS)
    where = _build_where(instruments, regions, hierarchies, and_or)
    return (
        f"SELECT\n"
        f"    {cols}\n"
        f"FROM (\n"
        f"    SELECT\n"
        f"        {cols},\n"
        f"        ROW_NUMBER() OVER (\n"
        f"            PARTITION BY {COL_PROJ_ID}\n"
        f"            ORDER BY {COL_APPRVL_FY} DESC,\n"
        f"                     COALESCE({COL_HIERARCHY}, '') ASC\n"
        f"        ) AS _rn\n"
        f"    FROM {GOAT_TABLE}\n"
        f"    {where}\n"
        f") t\n"
        f"WHERE _rn = 1\n"
        f"ORDER BY {COL_APPRVL_FY} DESC, {COL_PROJ_ID} ASC"
    )


def build_regions_query(instruments: Optional[List[str]] = None) -> str:
    """Distinct region values, optionally scoped to selected lending instruments."""
    base = (
        f"SELECT DISTINCT {COL_REGION}\n"
        f"FROM {GOAT_TABLE}\n"
        f"WHERE {COL_REGION} IS NOT NULL\n"
        f"  AND {COL_VALID_HIER} = 'True'\n"
    )
    if instruments:
        base += f"  AND {COL_LEND_INSTR} IN {_quote_list(instruments)}\n"
    return base + f"ORDER BY {COL_REGION} ASC"


# ── Static option queries ──────────────────────────────────────────────────────

QUERY_LENDING_INSTRUMENTS = (
    f"SELECT DISTINCT {COL_LEND_INSTR}\n"
    f"FROM {GOAT_TABLE}\n"
    f"WHERE {COL_LEND_INSTR} IS NOT NULL\n"
    f"  AND {COL_VALID_HIER} = 'True'\n"
    f"ORDER BY {COL_LEND_INSTR} ASC"
)

QUERY_HIERARCHIES = (
    f"SELECT DISTINCT {COL_HIERARCHY}\n"
    f"FROM {GOAT_TABLE}\n"
    f"WHERE {COL_HIERARCHY} IS NOT NULL\n"
    f"  AND {COL_VALID_HIER} = 'True'\n"
    f"ORDER BY {COL_HIERARCHY} ASC"
)


# ═══════════════════════════════════════════════════════════════════════════════
# Named query builders — Keyword / Hierarchy tab
# ═══════════════════════════════════════════════════════════════════════════════

# Full fetch of the hierarchy definition table (used by the sunburst chart).
QUERY_HIERARCHY_TABLE = (
    f"SELECT DISTINCT\n"
    f"    {COL_HIER_SHORT}    AS hierarchy,\n"
    f"    {COL_HIER_FULLNAME} AS fullname,\n"
    f"    {COL_HIER_CATEGORY} AS keyword_category,\n"
    f"    {COL_HIER_KEYWORD}  AS keyword\n"
    f"FROM {HIERARCHY_TABLE}\n"
    f"WHERE {COL_HIER_FULLNAME} IS NOT NULL\n"
    f"  AND {COL_HIER_KEYWORD}  IS NOT NULL\n"
    f"  AND {COL_VALID_HIER}    = 'True'\n"   # ← ADD THIS LINE
    f"ORDER BY {COL_HIER_FULLNAME}, {COL_HIER_KEYWORD} ASC"
)

# Distinct hierarchy full-names — drives the Delete Hierarchy dropdown.
QUERY_VALID_HIERARCHY_NAMES = (
    f"SELECT DISTINCT {COL_HIERARCHY} AS hierarchy_name\n"
    f"FROM {GOAT_TABLE}\n"
    f"WHERE {COL_HIERARCHY}  IS NOT NULL\n"
    f"  AND {COL_VALID_HIER} = 'True'\n"
    f"ORDER BY hierarchy_name ASC"
)

# Full project text columns needed for the in-process keyword search.
# Only rows with Valid_Hierarchy = 'True' are fetched (de-duped per project).
_SEARCH_COLS = ", ".join([COL_PROJ_ID] + KEYWORD_SEARCH_COLUMNS)
QUERY_PROJECT_TEXT_FOR_SEARCH = (
    f"SELECT DISTINCT {_SEARCH_COLS}\n"
    f"FROM {GOAT_TABLE}\n"
    f"WHERE {COL_VALID_HIER} = 'True'"
)


def build_delete_hierarchy_query(hierarchy_name: str) -> str:
    """
    Soft-delete: flip Valid_Hierarchy to 'False' for every row whose
    hierarchy_name matches the supplied value.
    Single-quote escaping is applied to prevent SQL injection.
    """
    safe = hierarchy_name.replace("'", "''")
    return (
        f"UPDATE {GOAT_TABLE}\n"
        f"SET    {COL_VALID_HIER} = 'False'\n"
        f"WHERE  {COL_HIERARCHY}  = '{safe}'"
    )

def build_insert_hierarchy_table_query(rows: list[dict]) -> str:
    """
    INSERT rows into the HIERARCHY_TABLE (0c_hierarchy_table_goat).
    Each dict must have keys: hierarchy, fullname, keyword_catagory, keyword, Valid_Hierarchy
    """
    if not rows:
        raise ValueError("No rows to insert into hierarchy table.")
    col_list = f"{COL_HIER_SHORT}, {COL_HIER_FULLNAME}, {COL_HIER_CATEGORY}, {COL_HIER_KEYWORD}, {COL_VALID_HIER}"
    values_parts = []
    for r in rows:
        def esc(v): return "NULL" if v is None else f"'{str(v).replace(chr(39), chr(39)*2)}'"
        values_parts.append(
            f"({esc(r['hierarchy'])}, {esc(r['fullname'])}, "
            f"{esc(r['keyword_catagory'])}, {esc(r['keyword'])}, {esc(r['Valid_Hierarchy'])})"
        )
    return (
        f"INSERT INTO {HIERARCHY_TABLE} ({col_list})\n"
        f"VALUES {', '.join(values_parts)}"
    )


def build_delete_hierarchy_table_query(hierarchy_short: str) -> str:
    """
    Soft-delete in HIERARCHY_TABLE: set Valid_Hierarchy = 'False'
    for all rows matching the hierarchy short code.
    """
    safe = hierarchy_short.replace("'", "''")
    return (
        f"UPDATE {HIERARCHY_TABLE}\n"
        f"SET    {COL_VALID_HIER} = 'False'\n"
        f"WHERE  {COL_HIER_SHORT} = '{safe}'"
    )

def build_insert_hierarchy_query(df_name: str = "new_hierarchy_df") -> str:
    """
    Template INSERT … SELECT used for adding new hierarchy rows.
    Callers pass a temporary view name created via CREATE OR REPLACE TEMP VIEW.
    """
    return f"INSERT INTO {GOAT_TABLE} SELECT * FROM {df_name}"


# ═══════════════════════════════════════════════════════════════════════════════
# Vectorised keyword search  (O(n·k) where n = rows, k = keywords)
# ═══════════════════════════════════════════════════════════════════════════════

def keyword_search_vectorised(
    df: pd.DataFrame,
    keywords: List[str],
    search_columns: Optional[List[str]] = None,
) -> pd.Series:
    """
    Return a boolean Series (True = keyword found in any search column).

    Strategy — compile a single OR-alternation regex from all keywords, then
    apply it once per column via Series.str.contains (which uses the C-level
    re engine).  This is O(n·c) string scans regardless of the number of
    keywords k, whereas a naïve Python loop is O(n·c·k).

    Parameters
    ----------
    df              : project-level DataFrame with text columns.
    keywords        : list of keyword strings (already stripped/lower-cased by caller).
    search_columns  : columns to search; defaults to KEYWORD_SEARCH_COLUMNS.

    Returns
    -------
    pd.Series of bool, indexed like df.
    """
    cols = search_columns or KEYWORD_SEARCH_COLUMNS

    if not keywords:
        return pd.Series(False, index=df.index)

    # Escape special regex chars in each keyword, then join with |
    pattern = "|".join(re.escape(kw) for kw in keywords if kw)
    if not pattern:
        return pd.Series(False, index=df.index)

    found = pd.Series(False, index=df.index)
    for col in cols:
        if col not in df.columns:
            logger.warning("[GoAT] keyword_search: column '%s' not found — skipped", col)
            continue
        # fillna("") avoids NaN propagation; na=False keeps dtype bool
        mask = (
            df[col]
            .fillna("")
            .astype(str)
            .str.contains(pattern, case=False, regex=True, na=False)
        )
        found = found | mask
        if found.all():
            # Short-circuit: every row already matched — no need to check more columns
            break

    return found


# ═══════════════════════════════════════════════════════════════════════════════
# QueryService — singleton data-access object
# ═══════════════════════════════════════════════════════════════════════════════

class QueryService:
    """
    Singleton Databricks SQL data-access object with in-memory TTL cache.

    Thread-safe: a threading.Lock guards all cache reads and writes so that
    multiple Dash worker threads share a single cache safely.

    Usage:
        qs = QueryService.get_instance()
        df = qs.get_project_status_data(instruments, regions, hierarchies, and_or)
    """

    _instance: Optional["QueryService"] = None

    @staticmethod
    def get_instance() -> "QueryService":
        """Return the process-wide singleton, creating it on first call."""
        if QueryService._instance is None:
            QueryService._instance = QueryService()
        return QueryService._instance

    def __init__(self) -> None:
        self._cache: Dict[str, Tuple[float, pd.DataFrame]] = {}
        self._lock  = threading.Lock()

    # ── Cache helpers ──────────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> Optional[pd.DataFrame]:
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            expires_at, df = entry
            if time.time() >= expires_at:
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
        """Flush the entire query cache (useful after data updates)."""
        with self._lock:
            self._cache.clear()
        logger.info("[GoAT] Query cache cleared")

    def invalidate_query(self, query: str) -> None:
        """Remove a single query's cached result."""
        with self._lock:
            removed = self._cache.pop(query, None) is not None
        if removed:
            logger.info("[GoAT] Cache invalidated for: %.80s…", query)

    # ── Core executor ──────────────────────────────────────────────────────────

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute a SELECT query against Databricks and return a pandas DataFrame.
        Results are cached by query string for QUERY_CACHE_TTL_SECONDS seconds.
        """
        cached = self._cache_get(query)
        if cached is not None:
            logger.info("[GoAT] CACHE HIT: %.60s…", query)
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

        elapsed = time.time() - t0
        logger.info("[GoAT] DB MISS — %.2fs: %.60s…", elapsed, query)
        self._cache_set(query, df)
        return df.copy(deep=True)

    def execute_write(self, statement: str) -> None:
        """
        Execute a non-SELECT statement (UPDATE / INSERT) against Databricks.
        Write statements are never cached.  Cache is fully cleared afterwards
        so subsequent reads see the updated data.
        """
        t0 = time.time()
        with sql.connect(
            server_hostname      = SERVER_HOSTNAME,
            http_path            = os.getenv("DATABRICKS_HTTP_PATH"),
            credentials_provider = credentials_provider,
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(statement)
            conn.commit()

        elapsed = time.time() - t0
        logger.info("[GoAT] WRITE — %.2fs: %.60s…", elapsed, statement)
        self.clear_cache()

    # ── Domain methods — Dashboard ─────────────────────────────────────────────

    def get_filter_options(self) -> Tuple[List[str], List[str]]:
        """Fetch distinct lending instruments and hierarchy names."""
        instr_df    = self.execute_query(QUERY_LENDING_INSTRUMENTS)
        hier_df     = self.execute_query(QUERY_HIERARCHIES)
        instruments = instr_df[COL_LEND_INSTR].dropna().tolist()
        hierarchies = hier_df[COL_HIERARCHY].dropna().tolist()
        return instruments, hierarchies

    def get_region_options(
        self, instruments: Optional[List[str]] = None
    ) -> List[str]:
        """Distinct region names, optionally scoped to selected lending instruments."""
        query = build_regions_query(instruments or [])
        df    = self.execute_query(query)
        return df[COL_REGION].dropna().tolist()

    def get_project_status_data(
        self,
        instruments: Optional[List[str]] = None,
        regions:     Optional[List[str]] = None,
        hierarchies: Optional[List[str]] = None,
        and_or:      str                 = "AND",
    ) -> pd.DataFrame:
        query = build_project_status_query(instruments, regions, hierarchies, and_or)
        logger.info("[GoAT] Project-status query:\n%s", query)
        return self.execute_query(query)

    def get_lending_instrument_data(
        self,
        instruments: Optional[List[str]] = None,
        regions:     Optional[List[str]] = None,
        hierarchies: Optional[List[str]] = None,
        and_or:      str                 = "AND",
    ) -> pd.DataFrame:
        query = build_lending_instrument_query(instruments, regions, hierarchies, and_or)
        logger.info("[GoAT] Lending-instrument query:\n%s", query)
        return self.execute_query(query)

    def get_total_count(
        self,
        instruments: Optional[List[str]] = None,
        regions:     Optional[List[str]] = None,
        hierarchies: Optional[List[str]] = None,
        and_or:      str                 = "AND",
    ) -> int:
        query = build_total_count_query(instruments, regions, hierarchies, and_or)
        df    = self.execute_query(query)
        if df.empty:
            return 0
        return int(df["total_projects"].iloc[0])

    def get_download_data(
        self,
        instruments: Optional[List[str]] = None,
        regions:     Optional[List[str]] = None,
        hierarchies: Optional[List[str]] = None,
        and_or:      str                 = "AND",
    ) -> pd.DataFrame:
        query = build_download_query(instruments, regions, hierarchies, and_or)
        logger.info("[GoAT] Download query:\n%s", query)
        return self.execute_query(query)

    # ── Domain methods — Keywords tab ──────────────────────────────────────────

    def get_hierarchy_table(self) -> pd.DataFrame:
        """
        Fetch the full hierarchy definition table for the sunburst chart.
        Columns: hierarchy, fullname, keyword_category, keyword
        """
        return self.execute_query(QUERY_HIERARCHY_TABLE)

    def get_valid_hierarchy_names(self) -> List[str]:
        """
        Return distinct hierarchy_name values where Valid_Hierarchy = 'True'.
        Used to populate the Delete Hierarchy dropdown.
        """
        df = self.execute_query(QUERY_VALID_HIERARCHY_NAMES)
        return df["hierarchy_name"].dropna().tolist()

    def add_new_hierarchy(
        self,
        hierarchy_name: str,
        full_name:      str,
        keywords_csv:   str,
    ) -> Tuple[bool, str]:
        """
        Full pipeline for adding a new keyword hierarchy:

        1. Fetch all project text rows from the UC table (cached).
        2. Run vectorised keyword search → boolean mask per project.
        3. Build a DataFrame that mirrors 1b_overall_goat_df's required columns
           with one row per project, hierarchy_name = hierarchy_name,
           Ishierarchy_present = 'Yes'/'No', Valid_Hierarchy = 'True'.
        4. Write the new rows to the table via INSERT INTO … SELECT.

        Returns (success: bool, message: str).
        """
        # ── 1. Input validation ────────────────────────────────────────────────
        keywords_raw = [kw.strip() for kw in keywords_csv.split(",") if kw.strip()]
        if not hierarchy_name or not full_name or not keywords_raw:
            return False, "All fields are required."

        hierarchy_name = hierarchy_name.strip()
        full_name      = full_name.strip()
        keywords_lower = [kw.lower() for kw in keywords_raw]

        logger.info(
            "[GoAT] add_new_hierarchy: name=%s | keywords=%s",
            hierarchy_name, keywords_lower,
        )

        try:
            # ── 2. Load project text data ──────────────────────────────────────
            text_df = self.execute_query(QUERY_PROJECT_TEXT_FOR_SEARCH)
            if text_df.empty:
                return False, "No project data found in the source table."

            # ── 3. Vectorised keyword search ───────────────────────────────────
            mask = keyword_search_vectorised(text_df, keywords_lower)
            text_df[COL_IS_HIER] = mask.map({True: "Yes", False: "No"})
            text_df[COL_HIERARCHY]  = hierarchy_name
            text_df[COL_VALID_HIER] = "True"

            # ── 4. Fetch full project rows for matched & unmatched projects ────
            # We need all columns of 1b_overall_goat_df, not just the text cols.
            # Strategy: pull the full table once (cached), then left-join the
            # Ishierarchy_present result from the search.
            full_df = self._get_full_goat_df_deduplicated()
            if full_df.empty:
                return False, "Could not load project master data."

            # Merge the keyword-search result onto the full project records
            result_df = full_df.merge(
                text_df[[COL_PROJ_ID, COL_IS_HIER]].drop_duplicates(subset=[COL_PROJ_ID]),
                on=COL_PROJ_ID,
                how="left",
                suffixes=("", "_new"),
            )

            # Fill any projects that were absent in text_df with "No"
            if COL_IS_HIER + "_new" in result_df.columns:
                result_df[COL_IS_HIER] = result_df[COL_IS_HIER + "_new"].fillna("No")
                result_df.drop(columns=[COL_IS_HIER + "_new"], inplace=True)
            else:
                result_df[COL_IS_HIER] = result_df[COL_IS_HIER].fillna("No")

            # Stamp new hierarchy metadata
            result_df[COL_HIERARCHY]  = hierarchy_name
            result_df[COL_VALID_HIER] = "True"

            matched = int(result_df[COL_IS_HIER].eq("Yes").sum())
            total   = len(result_df)
            logger.info(
                "[GoAT] Keyword search complete: %d/%d projects matched.", matched, total
            )

            # ── 5. Insert into UC table ────────────────────────────────────────
            self._insert_dataframe(result_df)

            # ── 6. Insert keyword rows into HIERARCHY_TABLE ────────────────────────
            hier_rows = [
                {
                    "hierarchy":       hierarchy_name,
                    "fullname":        full_name,
                    "keyword_catagory": "",          # no category supplied at add-time; extend UI if needed
                    "keyword":         kw,
                    "Valid_Hierarchy": "True",
                }
                for kw in keywords_raw
            ]
            hier_insert_sql = build_insert_hierarchy_table_query(hier_rows)
            self.execute_write(hier_insert_sql)

            return True, (
                f"Hierarchy '{hierarchy_name}' added successfully. "
                f"{matched:,} of {total:,} projects matched the keywords. "
                f"{len(keywords_raw)} keyword(s) written to the hierarchy table."
            )

        except Exception as exc:
            logger.exception("[GoAT] add_new_hierarchy failed: %s", exc)
            return False, f"An error occurred: {exc}"

    def delete_hierarchy(self, hierarchy_name: str) -> Tuple[bool, str]:
        """
        Soft-delete: set Valid_Hierarchy = 'False' for all rows with the
        given hierarchy_name in the GOAT_TABLE.

        Returns (success: bool, message: str).
        """
        if not hierarchy_name:
            return False, "No hierarchy selected."
        try:
            # Soft-delete in GOAT_TABLE
            query = build_delete_hierarchy_query(hierarchy_name)
            logger.info("[GoAT] delete_hierarchy (goat table): %s", hierarchy_name)
            self.execute_write(query)

            # Soft-delete in HIERARCHY_TABLE  ← NEW
            hier_query = build_delete_hierarchy_table_query(hierarchy_name)
            logger.info("[GoAT] delete_hierarchy (hierarchy table): %s", hierarchy_name)
            self.execute_write(hier_query)

            return True, f"Hierarchy '{hierarchy_name}' has been deactivated."
        except Exception as exc:
            logger.exception("[GoAT] delete_hierarchy failed: %s", exc)
            return False, f"An error occurred: {exc}"

    # ── Private helpers ────────────────────────────────────────────────────────

    def _get_full_goat_df_deduplicated(self) -> pd.DataFrame:
        """
        Fetch one representative row per PROJ_ID from the GOAT table.
        The GOAT table may contain multiple rows per project (one per hierarchy),
        so we deduplicate on PROJ_ID after fetching, keeping one row per project.
        The result is cached like any other query.

        IMPORTANT — deterministic tiebreak:
        PROJ_APPRVL_FY is a project-level attribute, identical across every
        hierarchy-duplicated row for a given PROJ_ID. That means an
        `ORDER BY PROJ_APPRVL_FY DESC` alone leaves every row in the partition
        tied, so ROW_NUMBER() has nothing left to break the tie with and Spark
        falls back to physical/shuffle order — which is NOT guaranteed to be
        stable across query executions (AQE re-planning, cluster size, data
        layout can all change it run-to-run). That's why the "representative"
        row picked here has been inconsistent: it wasn't actually being chosen
        deterministically at all.

        Fix: extend the ORDER BY with COL_HIERARCHY (unique per project row,
        since each row = one project × one hierarchy tag) so the sort fully
        orders every partition and ROW_NUMBER() = 1 resolves to the exact same
        physical row on every execution.
        """
        dedup_query = (
            f"SELECT *\n"
            f"FROM (\n"
            f"    SELECT *, ROW_NUMBER() OVER (\n"
            f"        PARTITION BY {COL_PROJ_ID}\n"
            f"        ORDER BY {COL_APPRVL_FY} DESC,\n"
            f"                 COALESCE({COL_HIERARCHY}, '') ASC\n"
            f"    ) AS _rn\n"
            f"    FROM {GOAT_TABLE}\n"
            f"    WHERE {COL_VALID_HIER} = 'True'\n"
            f") t\n"
            f"WHERE _rn = 1"
        )
        df = self.execute_query(dedup_query)
        # Drop the helper column before returning
        if "_rn" in df.columns:
            df = df.drop(columns=["_rn"])

        # ── Safety net ──────────────────────────────────────────────────────
        # Even with a deterministic ORDER BY, guard against edge cases (e.g. two
        # rows sharing the same hierarchy tag due to an upstream data issue) by
        # enforcing uniqueness client-side and surfacing it if it ever triggers,
        # rather than silently shipping duplicate PROJ_IDs downstream.
        if COL_PROJ_ID in df.columns:
            dupe_mask = df.duplicated(subset=[COL_PROJ_ID], keep="first")
            if dupe_mask.any():
                logger.warning(
                    "[GoAT] _get_full_goat_df_deduplicated: %d residual duplicate "
                    "PROJ_ID row(s) after SQL dedup — dropping extras client-side. "
                    "This likely indicates duplicate (PROJ_ID, %s) combinations "
                    "upstream in %s.",
                    int(dupe_mask.sum()), COL_HIERARCHY, GOAT_TABLE,
                )
            df = df.loc[~dupe_mask].reset_index(drop=True)

        return df

    def _insert_dataframe(self, df: pd.DataFrame) -> None:
        """
        Insert a DataFrame into the GOAT_TABLE by creating a temporary view
        and then executing INSERT INTO … SELECT * FROM <temp_view>.

        The temp-view approach avoids having to build a VALUES(...) string for
        thousands of rows, which would exceed SQL length limits.
        """
        view_name = "goat_new_hierarchy_tmp"
        with sql.connect(
            server_hostname      = SERVER_HOSTNAME,
            http_path            = os.getenv("DATABRICKS_HTTP_PATH"),
            credentials_provider = credentials_provider,
        ) as conn:
            cursor = conn.cursor()

            # Register the pandas DataFrame as a temporary Spark view via
            # the Databricks SQL connector's arrow-based batch insert.
            # The connector supports cursor.execute with parameterised VALUES
            # only for small payloads; for large frames we batch-insert using
            # INSERT INTO … VALUES with chunks of 500 rows to stay within
            # Databricks statement-length limits.
            chunk_size = 500
            columns    = list(df.columns)
            col_list   = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))

            for start in range(0, len(df), chunk_size):
                chunk = df.iloc[start : start + chunk_size]
                rows  = [tuple(row) for row in chunk.itertuples(index=False, name=None)]
                # Build VALUES string — each row as (val1, val2, ...)
                values_parts = []
                for row in rows:
                    escaped_vals = []
                    for v in row:
                        if v is None or (isinstance(v, float) and pd.isna(v)):
                            escaped_vals.append("NULL")
                        elif isinstance(v, str):
                            escaped_vals.append("'" + v.replace("'", "''") + "'")
                        else:
                            escaped_vals.append(str(v))
                    values_parts.append(f"({', '.join(escaped_vals)})")

                insert_sql = (
                    f"INSERT INTO {GOAT_TABLE} ({col_list})\n"
                    f"VALUES {', '.join(values_parts)}"
                )
                cursor.execute(insert_sql)

            conn.commit()

        logger.info(
            "[GoAT] _insert_dataframe: inserted %d rows into %s", len(df), GOAT_TABLE
        )
        self.clear_cache()