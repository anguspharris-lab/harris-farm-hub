"""
Harris Farm Hub — Adoption Dashboard
Usage analytics: who's using The Hub, which pages, how often.
"""

import os
from datetime import datetime

import requests
import streamlit as st

from shared.styles import render_header, render_footer, HFM_GREEN, HFM_DARK

user = st.session_state.get("auth_user")
API_URL = os.getenv("API_URL", "http://localhost:8000")

render_header(
    "Adoption Dashboard",
    "**Who's using The Hub** | Page views, active users, role breakdown",
    goals=["G5"],
    strategy_context="Proving platform value through real adoption data",
)


# ── Data Loading ──────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def _load_summary(days):
    try:
        r = requests.get(
            f"{API_URL}/api/analytics/summary", params={"days": days}, timeout=5
        )
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


@st.cache_data(ttl=60, show_spinner=False)
def _load_users(days):
    try:
        r = requests.get(
            f"{API_URL}/api/analytics/users", params={"days": days}, timeout=5
        )
        return r.json().get("users", []) if r.status_code == 200 else []
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _load_by_role(days):
    try:
        r = requests.get(
            f"{API_URL}/api/analytics/by-role", params={"days": days}, timeout=5
        )
        return r.json().get("roles", []) if r.status_code == 200 else []
    except Exception:
        return []


# ── Controls ──────────────────────────────────────────────────────────────

days = st.selectbox("Time range", [7, 14, 30, 90], index=0, format_func=lambda d: f"Last {d} days")

summary = _load_summary(days)
users = _load_users(days)
roles = _load_by_role(days)

# ── KPI Cards ─────────────────────────────────────────────────────────────

k1, k2, k3, k4 = st.columns(4)

unique = summary.get("unique_users", 0)
total = summary.get("total_views", 0)
avg_pp = summary.get("avg_pages_per_user", 0)

top_pages = summary.get("top_pages", [])
top_page_name = top_pages[0]["slug"] if top_pages else "—"

k1.metric("Unique Users", f"{unique:,}")
k2.metric("Total Page Views", f"{total:,}")
k3.metric("Avg Pages / User", f"{avg_pp}")
k4.metric("Top Page", top_page_name)

st.markdown("")

# ── Daily Users Chart ─────────────────────────────────────────────────────

views_by_day = summary.get("views_by_day", [])

if views_by_day:
    import plotly.graph_objects as go

    days_list = [d["day"] for d in views_by_day]
    user_counts = [d["users"] for d in views_by_day]
    view_counts = [d["views"] for d in views_by_day]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days_list, y=user_counts, name="Unique Users",
        line=dict(color=HFM_GREEN, width=3), fill="tozeroy",
        fillcolor="rgba(75, 160, 33, 0.12)",
    ))
    fig.add_trace(go.Bar(
        x=days_list, y=view_counts, name="Page Views",
        marker_color="rgba(75, 160, 33, 0.3)",
    ))
    fig.update_layout(
        title="Daily Activity",
        xaxis_title="", yaxis_title="Count",
        height=320, margin=dict(l=40, r=20, t=40, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No page-view data yet. Analytics will appear as users navigate The Hub.")

# ── Top Pages + Usage by Role ─────────────────────────────────────────────

col_left, col_right = st.columns(2)

with col_left:
    st.markdown(f"**Top Pages** (last {days} days)")
    if top_pages:
        import plotly.express as px
        import pandas as pd

        df_pages = pd.DataFrame(top_pages[:10])
        fig2 = px.bar(
            df_pages, x="views", y="slug", orientation="h",
            color_discrete_sequence=[HFM_GREEN],
            labels={"slug": "Page", "views": "Views"},
        )
        fig2.update_layout(
            height=300, margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.caption("No data yet.")

with col_right:
    st.markdown(f"**Usage by Role** (last {days} days)")
    if roles:
        import plotly.express as px
        import pandas as pd

        df_roles = pd.DataFrame(roles)
        fig3 = px.pie(
            df_roles, values="views", names="role",
            color_discrete_sequence=["#2ECC71", "#059669", "#d97706", "#7c3aed",
                                      "#ef4444", "#0ea5e9", "#f59e0b", "#6b7280"],
        )
        fig3.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.caption("No data yet.")

# ── User Activity Table ───────────────────────────────────────────────────

st.markdown(f"**User Activity** (last {days} days)")
if users:
    import pandas as pd

    df_users = pd.DataFrame(users)
    df_users = df_users.rename(columns={
        "email": "Email", "role": "Role", "page_views": "Page Views",
        "unique_pages": "Unique Pages", "last_active": "Last Active",
    })
    display_cols = ["Email", "Role", "Page Views", "Unique Pages", "Last Active"]
    st.dataframe(df_users[display_cols], use_container_width=True, hide_index=True)
else:
    st.caption("No user activity recorded yet.")

# ── Footer ────────────────────────────────────────────────────────────────

render_footer("Adoption Dashboard", "Proving value through real usage data", user)
