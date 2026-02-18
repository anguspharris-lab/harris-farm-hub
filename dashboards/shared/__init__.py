"""
Harris Farm Hub - Shared Constants and Utilities
Centralized store network and common data structures.

Modules that depend on the backend (fiscal_selector, hierarchy_filter,
time_filter, hourly_charts) are imported lazily — they are only loaded
when explicitly imported by a dashboard that needs them. This allows
lightweight dashboards (e.g. landing.py) to run on Streamlit Cloud
without pulling in duckdb/backend dependencies.
"""

from .stores import STORES, REGIONS

__all__ = ["STORES", "REGIONS"]
