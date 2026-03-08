"""
Harris Farm Hub — BigQuery Connector
Single source of truth for all data queries. Falls back to SQLite when
BigQuery is unavailable (local dev without credentials).

Usage:
    from shared.bigquery_connector import bq_query, is_bigquery_available
    from shared.bigquery_connector import get_weekly_sales, get_market_share

    # Direct query
    df = bq_query("SELECT * FROM `trading.weekly_sales` LIMIT 10")

    # Convenience functions (match data_access.py signatures)
    df = get_weekly_sales(stores=["10 - HFM Pennant Hills"], measure="Sales - Val")

    # Safe wrappers (BigQuery first, SQLite fallback)
    df = get_weekly_sales_safe(date_from="2025-07-01")
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import streamlit as st

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BQ_PROJECT = "oval-blend-488902-p2"
BQ_LOCATION = "australia-southeast1"

# Dataset fully-qualified prefixes
DS_TRADING = f"{BQ_PROJECT}.trading"
DS_MASTER = f"{BQ_PROJECT}.master_data"
DS_DEMOGRAPHICS = f"{BQ_PROJECT}.demographics"
DS_REFERENCE = f"{BQ_PROJECT}.reference"

# Service account key search paths (checked in order)
_KEY_PATHS = [
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
    str(Path.home() / ".config" / "gcloud" / "service-account-key.json"),
]

# ---------------------------------------------------------------------------
# Client initialisation (cached for app lifetime)
# ---------------------------------------------------------------------------


@st.cache_resource
def _get_bq_client():
    """Create and cache a BigQuery client. Returns None if unavailable."""
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
    except ImportError:
        _log.info("google-cloud-bigquery not installed — BigQuery unavailable")
        return None

    # Option 1: JSON string in env var (Render deployment)
    sa_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if sa_json:
        try:
            info = json.loads(sa_json)
            credentials = service_account.Credentials.from_service_account_info(info)
            client = bigquery.Client(
                project=BQ_PROJECT, credentials=credentials, location=BQ_LOCATION
            )
            client.query("SELECT 1").result()
            _log.info("BigQuery connected via GCP_SERVICE_ACCOUNT_JSON")
            return client
        except Exception as e:
            _log.warning("BigQuery JSON env var auth failed: %s", e)

    # Option 2: Key file on disk (local dev)
    for key_path in _KEY_PATHS:
        if key_path and Path(key_path).exists():
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    key_path
                )
                client = bigquery.Client(
                    project=BQ_PROJECT,
                    credentials=credentials,
                    location=BQ_LOCATION,
                )
                client.query("SELECT 1").result()
                _log.info("BigQuery connected via key file: %s", key_path)
                return client
            except Exception as e:
                _log.warning("BigQuery key file auth failed (%s): %s", key_path, e)

    _log.info("No BigQuery credentials found — BigQuery unavailable")
    return None


def is_bigquery_available() -> bool:
    """Check if BigQuery client is available and authenticated."""
    return _get_bq_client() is not None


# ---------------------------------------------------------------------------
# Core query function
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300)
def bq_query(sql, _params=None):
    """
    Execute a BigQuery SQL query and return a pandas DataFrame.
    Results are cached for 5 minutes per unique query.

    Args:
        sql: SQL query string. Use backtick-quoted table references.
        _params: Optional list of bigquery.ScalarQueryParameter (prefixed
                 with _ so Streamlit doesn't try to hash it).

    Returns:
        pd.DataFrame

    Raises:
        ConnectionError: If BigQuery is not available.
    """
    client = _get_bq_client()
    if client is None:
        raise ConnectionError("BigQuery not available")

    from google.cloud import bigquery

    job_config = bigquery.QueryJobConfig()
    if _params:
        job_config.query_parameters = _params

    return client.query(sql, job_config=job_config).to_dataframe()


# ---------------------------------------------------------------------------
# Convenience query functions (match data_access.py signatures)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300)
def get_stores() -> List[str]:
    """Get list of retail store names from BigQuery."""
    sql = f"""
        SELECT store_name
        FROM `{DS_MASTER}.stores`
        WHERE state IS NOT NULL
        ORDER BY store_name
    """
    df = bq_query(sql)
    return df["store_name"].tolist()


@st.cache_data(ttl=300)
def get_departments() -> List[Dict[str, Any]]:
    """Get department list with major groups."""
    sql = f"""
        SELECT
            department_code, department_name,
            major_group_code, major_group_name
        FROM `{DS_MASTER}.departments`
        ORDER BY department_code, major_group_code
    """
    df = bq_query(sql)
    return df.to_dict("records")


@st.cache_data(ttl=300)
def get_weekly_sales(
    stores=None,
    departments=None,
    major_groups=None,
    date_from=None,
    date_to=None,
    measure="Sales - Val",
    channel="Retail",
    promo="N",
):
    # type: (Optional[List[str]], Optional[List[str]], Optional[List[str]], Optional[str], Optional[str], str, str, str) -> pd.DataFrame
    """
    Query weekly_sales from BigQuery with optional filters.
    Returns DataFrame with columns: store, department, major_group, week_ending, value.
    """
    conditions = ["channel = @channel", "measure = @measure", "is_promotion = @promo"]
    from google.cloud import bigquery

    params = [
        bigquery.ScalarQueryParameter("channel", "STRING", channel),
        bigquery.ScalarQueryParameter("measure", "STRING", measure),
        bigquery.ScalarQueryParameter("promo", "STRING", promo),
    ]

    if date_from:
        conditions.append("week_ending >= @date_from")
        params.append(bigquery.ScalarQueryParameter("date_from", "STRING", date_from))
    if date_to:
        conditions.append("week_ending <= @date_to")
        params.append(bigquery.ScalarQueryParameter("date_to", "STRING", date_to))

    where = " AND ".join(conditions)

    sql = f"""
        SELECT store, department, major_group, week_ending, value
        FROM `{DS_TRADING}.weekly_sales`
        WHERE {where}
        ORDER BY week_ending, store, department
    """

    df = bq_query(sql, _params=params)

    # Apply in-memory filters for list params (BigQuery parameterised queries
    # don't support IN-lists cleanly without UNNEST)
    if stores:
        df = df[df["store"].isin(stores)]
    if departments:
        df = df[df["department"].isin(departments)]
    if major_groups:
        df = df[df["major_group"].isin(major_groups)]

    return df


@st.cache_data(ttl=300)
def get_customer_data(
    stores=None, date_from=None, date_to=None
):
    # type: (Optional[List[str]], Optional[str], Optional[str]) -> pd.DataFrame
    """Query customers from BigQuery."""
    conditions = ["1=1"]
    from google.cloud import bigquery

    params = []

    if date_from:
        conditions.append("week_ending >= @date_from")
        params.append(bigquery.ScalarQueryParameter("date_from", "STRING", date_from))
    if date_to:
        conditions.append("week_ending <= @date_to")
        params.append(bigquery.ScalarQueryParameter("date_to", "STRING", date_to))

    where = " AND ".join(conditions)

    sql = f"""
        SELECT store, channel, measure, week_ending, value
        FROM `{DS_TRADING}.weekly_customers`
        WHERE {where}
        ORDER BY week_ending, store
    """

    df = bq_query(sql, _params=params)
    if stores:
        df = df[df["store"].isin(stores)]
    return df


@st.cache_data(ttl=300)
def get_market_share(
    region_code=None, channel="Total", period_from=None, period_to=None
):
    # type: (Optional[str], str, Optional[int], Optional[int]) -> pd.DataFrame
    """Query market_share from BigQuery."""
    conditions = ["channel = @channel"]
    from google.cloud import bigquery

    params = [bigquery.ScalarQueryParameter("channel", "STRING", channel)]

    if region_code:
        conditions.append("region_code = @region_code")
        params.append(
            bigquery.ScalarQueryParameter("region_code", "STRING", region_code)
        )
    if period_from:
        conditions.append("period >= @period_from")
        params.append(
            bigquery.ScalarQueryParameter("period_from", "INT64", period_from)
        )
    if period_to:
        conditions.append("period <= @period_to")
        params.append(bigquery.ScalarQueryParameter("period_to", "INT64", period_to))

    where = " AND ".join(conditions)

    sql = f"""
        SELECT
            period, region_code, region_name, industry_name, channel,
            market_size_dollars, market_share_pct, customer_penetration_pct,
            spend_per_customer, spend_per_transaction, transactions_per_customer
        FROM `{DS_TRADING}.market_share`
        WHERE {where}
        ORDER BY period, region_code
    """
    return bq_query(sql, _params=params)


@st.cache_data(ttl=300)
def get_store_performance(fiscal_year=None):
    # type: (Optional[str]) -> pd.DataFrame
    """
    Get store-level performance summary.
    Uses weekly_sales_summary enriched view if available.
    """
    sql = f"""
        SELECT
            s.store_number,
            s.store_name,
            s.state,
            s.like_for_like,
            SUM(CASE WHEN ws.measure = 'Sales - Val' THEN ws.value ELSE 0 END) as total_sales,
            SUM(CASE WHEN ws.measure = 'Final Gross Prod - Val' THEN ws.value ELSE 0 END) as total_gp,
            SUM(CASE WHEN ws.measure = 'Bgt Sales - Val' THEN ws.value ELSE 0 END) as budget,
            SUM(CASE WHEN ws.measure = 'Total Shrinkage - Val' THEN ws.value ELSE 0 END) as shrinkage
        FROM `{DS_MASTER}.stores` s
        LEFT JOIN `{DS_TRADING}.weekly_sales` ws
            ON CAST(s.store_number AS STRING) = SPLIT(ws.store, ' - ')[OFFSET(0)]
        WHERE ws.channel = 'Retail' AND ws.is_promotion = 'N'
        GROUP BY s.store_number, s.store_name, s.state, s.like_for_like
        ORDER BY total_sales DESC
    """
    return bq_query(sql)


@st.cache_data(ttl=300)
def search_knowledge_base(query, category=None, limit=10):
    # type: (str, Optional[str], int) -> pd.DataFrame
    """Search knowledge base articles by keyword."""
    conditions = [
        "(LOWER(content) LIKE CONCAT('%', LOWER(@query), '%') "
        "OR LOWER(filename) LIKE CONCAT('%', LOWER(@query), '%'))"
    ]
    from google.cloud import bigquery

    params = [bigquery.ScalarQueryParameter("query", "STRING", query)]

    if category:
        conditions.append("category = @category")
        params.append(bigquery.ScalarQueryParameter("category", "STRING", category))

    where = " AND ".join(conditions)

    sql = f"""
        SELECT id, filename, category, content
        FROM `{DS_REFERENCE}.knowledge_base`
        WHERE {where}
        LIMIT {int(limit)}
    """
    return bq_query(sql, _params=params)


@st.cache_data(ttl=300)
def get_fiscal_calendar():
    # type: () -> pd.DataFrame
    """Get fiscal calendar from BigQuery."""
    sql = f"""
        SELECT *
        FROM `{DS_REFERENCE}.fiscal_calendar_weekly`
        ORDER BY week_ending_date
    """
    return bq_query(sql)


# ---------------------------------------------------------------------------
# Safe wrappers (BigQuery first, SQLite fallback)
# ---------------------------------------------------------------------------


def get_weekly_sales_safe(**kwargs):
    # type: (**Any) -> pd.DataFrame
    """Try BigQuery first, fall back to SQLite."""
    if is_bigquery_available():
        try:
            return get_weekly_sales(**kwargs)
        except Exception as e:
            _log.warning("BigQuery weekly_sales failed, falling back: %s", e)

    from shared.data_access import get_sales_data

    rows = get_sales_data(
        stores=kwargs.get("stores"),
        departments=kwargs.get("departments"),
        major_groups=kwargs.get("major_groups"),
        date_from=kwargs.get("date_from"),
        date_to=kwargs.get("date_to"),
        measure=kwargs.get("measure", "Sales - Val"),
        channel=kwargs.get("channel", "Retail"),
        promo=kwargs.get("promo", "N"),
    )
    return pd.DataFrame(rows)


def get_customer_data_safe(**kwargs):
    # type: (**Any) -> pd.DataFrame
    """Try BigQuery first, fall back to SQLite."""
    if is_bigquery_available():
        try:
            return get_customer_data(**kwargs)
        except Exception as e:
            _log.warning("BigQuery customers failed, falling back: %s", e)

    from shared.data_access import get_customer_data as _sqlite_customers

    rows = _sqlite_customers(
        stores=kwargs.get("stores"),
        date_from=kwargs.get("date_from"),
        date_to=kwargs.get("date_to"),
    )
    return pd.DataFrame(rows)


def get_market_share_safe(**kwargs):
    # type: (**Any) -> pd.DataFrame
    """Try BigQuery first, fall back to SQLite."""
    if is_bigquery_available():
        try:
            return get_market_share(**kwargs)
        except Exception as e:
            _log.warning("BigQuery market_share failed, falling back: %s", e)

    from shared.data_access import get_market_share as _sqlite_ms

    rows = _sqlite_ms(
        region_code=kwargs.get("region_code"),
        channel=kwargs.get("channel", "Total"),
        period_from=kwargs.get("period_from"),
        period_to=kwargs.get("period_to"),
    )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Supply Chain Review — Surveys dataset
# ---------------------------------------------------------------------------

DS_SURVEYS = f"{BQ_PROJECT}.Surveys"


def _bq_row_to_interview_format(row):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """Transform a flat BigQuery row into the nested interview JSON format
    expected by the React analysis artifact."""
    return {
        "meta": {
            "version": "5.0",
            "tool": "hfm-sc-interview",
            "timestamp": str(row.get("submitted_at", "")),
        },
        "respondent": {
            "name": row.get("name", ""),
            "role": row.get("role", ""),
            "department": "",
            "sc_touchpoint": row.get("sc_touch", ""),
        },
        "whats_working": {
            "protect": row.get("protect_processes", ""),
            "pain_points": "",
            "external_pressures": row.get("external_pressures", ""),
        },
        "scores": {
            "confidence": row.get("five_year_confidence") or 5,
            "leverage": row.get("leverage_strengths") or 5,
            "urgency": row.get("urgency") or 5,
            "desire": row.get("desire_score") or 5,
            "clarity": row.get("clarity_score") or 5,
            "readiness": row.get("readiness_score") or 5,
            "sustain": row.get("sustain_score") or 5,
        },
        "capabilities": {
            "visibility": row.get("rf_visibility") or 5,
            "disruption_response": row.get("rf_disruption") or 5,
            "data_quality": row.get("rf_data") or 5,
            "technology": row.get("rf_technology") or 5,
            "suppliers": row.get("rf_suppliers") or 5,
            "transport": row.get("rf_transport") or 5,
            "demand_planning": row.get("rf_demand") or 5,
            "sustainability": row.get("rf_sustainability") or 5,
        },
        "qualitative": {
            "excites": "",
            "worries": row.get("worries", ""),
            "ideal_5yr": row.get("ideal_5yr", ""),
            "one_big_thing": row.get("one_big_thing", ""),
            "impact_if_successful": row.get("customer_impact", ""),
            "additional_comments": row.get("additional", ""),
        },
    }


@st.cache_data(ttl=60)
def get_sc_responses():
    # type: () -> List[Dict[str, Any]]
    """Fetch all Supply Chain Review responses from BigQuery and return
    them in the nested interview JSON format."""
    sql = f"""
        SELECT *
        FROM `{DS_SURVEYS}.sc_review_responses`
        ORDER BY submitted_at DESC
    """
    df = bq_query(sql)
    rows = df.to_dict("records")
    return [_bq_row_to_interview_format(r) for r in rows]


# ---------------------------------------------------------------------------
# Transformation at Scale — query helpers
# ---------------------------------------------------------------------------

def _survey_table(test=False):
    # type: (bool) -> str
    """Return the correct survey table name."""
    suffix = "_test" if test else ""
    return f"`{DS_SURVEYS}.sc_review_responses{suffix}`"


@st.cache_data(ttl=300)
def get_response_count(workstream_name, test=False):
    # type: (str, bool) -> int
    """Count responses for a specific workstream (by transformation_focus)."""
    table = _survey_table(test)
    sql = f"""
        SELECT COUNT(*) AS cnt
        FROM {table}
        WHERE transformation_focus = @ws_name
    """
    from google.cloud import bigquery
    params = [bigquery.ScalarQueryParameter("ws_name", "STRING", workstream_name)]
    df = bq_query(sql, _params=params)
    return int(df["cnt"].iloc[0]) if len(df) > 0 else 0


@st.cache_data(ttl=300)
def get_response_counts_by_focus(test=False):
    # type: (bool) -> Dict[str, int]
    """Count responses grouped by transformation_focus. Returns {focus: count}."""
    table = _survey_table(test)
    sql = f"""
        SELECT
            COALESCE(transformation_focus, 'Unknown') AS focus,
            COUNT(*) AS cnt
        FROM {table}
        GROUP BY focus
    """
    df = bq_query(sql)
    return dict(zip(df["focus"].tolist(), df["cnt"].tolist()))


@st.cache_data(ttl=300)
def get_responses_by_email(email, test=False):
    # type: (str, bool) -> List[Dict[str, Any]]
    """Fetch all responses for a given email address."""
    table = _survey_table(test)
    sql = f"""
        SELECT *
        FROM {table}
        WHERE LOWER(email) = LOWER(@email)
        ORDER BY submitted_at DESC
    """
    from google.cloud import bigquery
    params = [bigquery.ScalarQueryParameter("email", "STRING", email)]
    df = bq_query(sql, _params=params)
    return df.to_dict("records")


@st.cache_data(ttl=300)
def get_department_counts(workstream_name, test=False):
    # type: (str, bool) -> Dict[str, int]
    """Count responses by department for a specific workstream."""
    table = _survey_table(test)
    sql = f"""
        SELECT
            COALESCE(department, 'Unknown') AS dept,
            COUNT(*) AS cnt
        FROM {table}
        WHERE transformation_focus = @ws_name
        GROUP BY dept
        ORDER BY cnt DESC
    """
    from google.cloud import bigquery
    params = [bigquery.ScalarQueryParameter("ws_name", "STRING", workstream_name)]
    df = bq_query(sql, _params=params)
    return dict(zip(df["dept"].tolist(), df["cnt"].tolist()))
