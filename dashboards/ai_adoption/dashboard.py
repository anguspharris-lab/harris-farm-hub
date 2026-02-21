"""
Harris Farm Hub — AI Adoption Tracker
Tracks AI platform usage across the organisation.
Pulls from OpenAI and Anthropic admin APIs, caches in SQLite, serves from cache.
"""
from __future__ import annotations

import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared.styles import render_header, render_footer, HFM_GREEN

user = st.session_state.get("auth_user")

render_header(
    "AI Adoption Tracker",
    "Organisation-wide AI platform usage | Claude & ChatGPT | Auto-refreshing",
    goals=["G3", "G5"],
    strategy_context="Tracking AI capability growth across the business \u2014 are our people becoming superstars?",
)

# ── Lazy imports (cache/fetcher depend on yaml) ─────────────────────────────

from ai_adoption.cache import (
    init_cache_db, needs_refresh, last_sync_time, log_sync,
    upsert_users, upsert_usage,
    get_active_users, get_total_messages, get_platform_split,
    get_weekly_active_users, get_all_usage_csv,
)
from ai_adoption.data_fetcher import get_all_fetchers, get_fetcher

# Ensure cache tables exist
init_cache_db()


# ── Auto-refresh logic ──────────────────────────────────────────────────────

def _sync_platform(platform_key: str) -> tuple[bool, str]:
    """Sync a single platform. Returns (success, message)."""
    fetcher = get_fetcher(platform_key)
    if not fetcher or not fetcher.is_configured():
        return False, f"Not configured (missing {platform_key} API key)"
    try:
        # Fetch users
        users = fetcher.fetch_users()
        upsert_users(platform_key, users)

        # Fetch usage for last 90 days
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
        records = fetcher.fetch_usage(start_date, end_date)
        upsert_usage(platform_key, records)

        log_sync(platform_key, "success",
                 f"Synced {len(users)} users, {len(records)} usage records",
                 users_synced=len(users), records_synced=len(records))
        return True, f"Synced {len(users)} users, {len(records)} usage records"
    except Exception as e:
        log_sync(platform_key, "error", str(e))
        return False, str(e)


def _auto_refresh():
    """Check each platform and refresh if stale."""
    for fetcher in get_all_fetchers():
        if fetcher.is_configured() and needs_refresh(fetcher.platform_key):
            _sync_platform(fetcher.platform_key)


# Run auto-refresh on page load (cached in session to avoid repeated calls)
if "ai_adoption_refreshed" not in st.session_state:
    _auto_refresh()
    st.session_state["ai_adoption_refreshed"] = True

# ── Check for stale data warnings ───────────────────────────────────────────

for fetcher in get_all_fetchers():
    last = last_sync_time(fetcher.platform_key)
    if fetcher.is_configured() and not last:
        st.warning(
            f"**{fetcher.label}**: No data synced yet. "
            "Use the Admin panel below to test connection and trigger a sync."
        )
    elif fetcher.is_configured() and needs_refresh(fetcher.platform_key):
        st.warning(
            f"**{fetcher.label}**: Data may be stale (last sync: {last}). "
            "Auto-refresh will run on next page load."
        )
    elif not fetcher.is_configured():
        st.info(
            f"**{fetcher.label}**: Not configured. "
            f"Set `{fetcher.config.get('env_var', '?')}` environment variable to enable."
        )

# ── Time Range Toggle ────────────────────────────────────────────────────────

time_range = st.radio(
    "Time range", ["Last 7 days", "Last 30 days", "All time"],
    horizontal=True, key="ai_adoption_range"
)
days = {"Last 7 days": 7, "Last 30 days": 30, "All time": 9999}[time_range]


# ══════════════════════════════════════════════════════════════════════════════
# TOP ROW — METRIC CARDS
# ══════════════════════════════════════════════════════════════════════════════

active_users = get_active_users(days)
total_msgs = get_total_messages(days)
platform_split = get_platform_split(days)
weekly_wau = get_weekly_active_users(12)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("Active Users", len(active_users),
              help="Unique emails with at least 1 message in selected period")

with k2:
    st.metric("Total Messages", f"{total_msgs:,}",
              help="Sum of all messages across all platforms")

with k3:
    # Platform split donut
    if platform_split:
        fig_donut = go.Figure(data=[go.Pie(
            labels=list(platform_split.keys()),
            values=list(platform_split.values()),
            hole=0.55,
            marker_colors=["#7c3aed", "#16a34a"] if "Claude" in platform_split else ["#16a34a", "#7c3aed"],
            textinfo="label+percent",
            textfont_size=12,
        )])
        fig_donut.update_layout(
            height=160, margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_donut, use_container_width=True, key="platform_donut")
    else:
        st.metric("Platform Split", "No data")

with k4:
    # Weekly active users sparkline
    if weekly_wau:
        wau_df = pd.DataFrame(weekly_wau)
        fig_spark = px.area(
            wau_df, x="week", y="active_users",
            color_discrete_sequence=[HFM_GREEN],
        )
        fig_spark.update_layout(
            height=160, margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            showlegend=False,
        )
        fig_spark.update_traces(fill="tozeroy", line_shape="spline")
        st.plotly_chart(fig_spark, use_container_width=True, key="wau_sparkline")
    else:
        st.metric("Weekly Trend", "No data")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SECTION — USER TABLE
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("User Activity")

# Search box
search = st.text_input("Search by name or email", key="ai_adoption_search",
                        placeholder="e.g. john, jane@harrisfarm.com.au")

if active_users:
    df = pd.DataFrame(active_users)

    # Apply search filter
    if search:
        mask = (
            df["name"].str.contains(search, case=False, na=False) |
            df["email"].str.contains(search, case=False, na=False)
        )
        df = df[mask]

    if not df.empty:
        # Add trophy emojis to top 3
        df = df.sort_values("total_messages", ascending=False).reset_index(drop=True)
        trophies = {0: "🏆", 1: "🥈", 2: "🥉"}
        df["Name"] = df.apply(
            lambda row: f"{trophies.get(row.name, '')} {row['name']}".strip(),
            axis=1,
        )

        display = df[["Name", "email", "claude_messages", "chatgpt_messages",
                       "total_messages", "last_active"]].copy()
        display.columns = ["Name", "Email", "Claude Messages", "ChatGPT Messages",
                           "Total", "Last Active"]

        st.dataframe(display, use_container_width=True, hide_index=True, height=500)
    else:
        st.info("No users match your search.")
else:
    st.info(
        "No usage data yet. Configure API keys and run a sync from the Admin panel below."
    )


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("Admin"):
    st.markdown("**API Connection Status**")

    for fetcher in get_all_fetchers():
        last = last_sync_time(fetcher.platform_key)
        configured = fetcher.is_configured()
        status_icon = "🟢" if configured and last else ("🟡" if configured else "🔴")
        status_text = (
            f"Last sync: {last}" if last
            else ("Configured but not synced" if configured else "Not configured")
        )
        st.markdown(f"{status_icon} **{fetcher.label}** — {status_text}")

    st.markdown("---")

    col_test, col_refresh = st.columns(2)

    with col_test:
        if st.button("Test Connection", key="ai_test_conn"):
            for fetcher in get_all_fetchers():
                if fetcher.is_configured():
                    with st.spinner(f"Testing {fetcher.label}..."):
                        ok, msg = fetcher.test_connection()
                    if ok:
                        st.success(f"{fetcher.label}: {msg}")
                    else:
                        st.error(f"{fetcher.label}: {msg}")
                else:
                    st.warning(f"{fetcher.label}: Not configured")

    with col_refresh:
        if st.button("Refresh Now", key="ai_refresh_now"):
            for fetcher in get_all_fetchers():
                if fetcher.is_configured():
                    with st.spinner(f"Syncing {fetcher.label}..."):
                        ok, msg = _sync_platform(fetcher.platform_key)
                    if ok:
                        st.success(f"{fetcher.label}: {msg}")
                    else:
                        st.error(f"{fetcher.label}: {msg}")
            # Clear the refresh flag to let auto-refresh re-evaluate
            st.session_state.pop("ai_adoption_refreshed", None)
            st.rerun()

    # CSV export
    st.markdown("---")
    all_data = get_all_usage_csv()
    if all_data:
        csv_df = pd.DataFrame(all_data)
        csv = csv_df.to_csv(index=False)
        st.download_button(
            "Export All Data (CSV)", csv,
            file_name=f"ai_adoption_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", key="ai_export_csv",
        )
    else:
        st.caption("No data available for export.")


# ── Footer ───────────────────────────────────────────────────────────────────

render_footer("AI Adoption Tracker", "Auto-refreshes every 6 hours", user=user)
