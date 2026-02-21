"""
Harris Farm Hub - Trending & Self-Improvement Dashboard
Shows usage analytics, LLM performance, feedback trends, and system health.
"""

import os

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000")

from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.voice_realtime import render_voice_data_box

user = st.session_state.get("auth_user")

# ============================================================================
# HEADER
# ============================================================================

render_header(
    "Trending & Self-Improvement",
    "**System Analytics** | Usage patterns, LLM performance & feedback trends",
    goals=["G5"],
    strategy_context="The Hub watches itself \u2014 measurably better this week than last week.",
)

# ============================================================================
# LOAD DATA FROM API
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def _load_weekly_data():
    try:
        resp = requests.get(f"{API_URL}/api/analytics/weekly-report", timeout=5)
        return resp.json() if resp.status_code == 200 else {}
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def _load_performance_data():
    try:
        resp = requests.get(f"{API_URL}/api/analytics/performance", timeout=5)
        return resp.json() if resp.status_code == 200 else {}
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def _load_template_count():
    try:
        resp = requests.get(f"{API_URL}/api/templates", timeout=5)
        return resp.json().get("count", 0) if resp.status_code == 200 else 0
    except Exception:
        return 0


weekly_data = _load_weekly_data()
performance_data = _load_performance_data()

# ============================================================================
# WEEKLY KPIs
# ============================================================================

st.subheader("This Week's Numbers")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_queries = weekly_data.get("total_queries", 0)
    st.metric("Total Queries", total_queries,
              help="Natural language queries + rubric evaluations this week")

with col2:
    avg_rating = weekly_data.get("average_rating", 0)
    st.metric("Avg Rating", f"{avg_rating:.1f}/5.0" if avg_rating else "No ratings yet",
              help="Average user satisfaction rating")

with col3:
    success_rate = weekly_data.get("sql_success_rate", 0)
    st.metric("SQL Success Rate", f"{success_rate:.0f}%" if success_rate else "N/A",
              help="Percentage of NL queries that generated valid SQL")

with col4:
    template_count = _load_template_count()
    st.metric("Templates", template_count, help="Number of prompt templates in library")

st.markdown("---")

# ============================================================================
# LLM PERFORMANCE
# ============================================================================

st.subheader("⚖️ LLM Performance (The Rubric)")

llm_wins = performance_data.get("llm_performance", [])

if llm_wins:
    col1, col2 = st.columns(2)

    with col1:
        df_wins = pd.DataFrame(llm_wins)
        fig_wins = px.bar(
            df_wins,
            x="winner",
            y="wins",
            color="winner",
            title="Chairman's Decision — Win Count by LLM",
            labels={"winner": "LLM Provider", "wins": "Wins"},
            color_discrete_sequence=["#1e3a8a", "#10b981", "#f59e0b"]
        )
        fig_wins.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_wins,
                        key="trending_wins_chart")

    with col2:
        # Win rate as pie
        fig_pie = px.pie(
            df_wins,
            values="wins",
            names="winner",
            title="Win Rate Distribution",
            color_discrete_sequence=["#1e3a8a", "#10b981", "#f59e0b"]
        )
        fig_pie.update_layout(height=350)
        st.plotly_chart(fig_pie,
                        key="trending_pie_chart")
else:
    st.info("No Rubric evaluations yet. Use **The Rubric** page to compare AI responses and pick winners.")

# ============================================================================
# TOP QUERIES
# ============================================================================

st.subheader("🔝 Top Rated Queries")

top_queries = performance_data.get("top_queries", [])

if top_queries:
    df_queries = pd.DataFrame(top_queries)
    df_queries["avg_rating"] = df_queries["avg_rating"].round(1)
    st.dataframe(
        df_queries.rename(columns={
            "question": "Question",
            "avg_rating": "Avg Rating",
            "feedback_count": "Feedback Count"
        }),
        hide_index=True,
        key="trending_top_queries",
    )
else:
    st.info("No rated queries yet. Submit feedback on query results to build this list.")

# ============================================================================
# TEMPLATE USAGE
# ============================================================================

st.subheader("📚 Popular Templates")

popular = performance_data.get("popular_templates", [])

if popular:
    df_popular = pd.DataFrame(popular)
    fig_templates = px.bar(
        df_popular,
        x="title",
        y="uses",
        color="category",
        title="Most Used Prompt Templates",
        labels={"title": "Template", "uses": "Times Used"}
    )
    fig_templates.update_layout(height=350)
    fig_templates.update_xaxis(tickangle=-45)
    st.plotly_chart(fig_templates,
                    key="trending_templates_chart")
else:
    st.info("No template usage recorded yet. Templates gain usage stats when loaded from the Prompt Builder.")

# ============================================================================
# SYSTEM HEALTH SUMMARY
# ============================================================================

st.markdown("---")
st.subheader("🏥 System Health")

col1, col2, col3 = st.columns(3)

api_healthy = False
try:
    r = requests.get(f"{API_URL}/", timeout=3)
    if r.status_code in (200, 302):
        api_healthy = True
except Exception:
    pass

with col1:
    st.metric("API Backend", "Up" if api_healthy else "Down")

with col2:
    st.metric("Dashboard Pages", "17")

with col3:
    if api_healthy:
        st.success("ALL HEALTHY")
    else:
        st.error("API Backend Down")

# ============================================================================
# INSIGHTS
# ============================================================================

st.markdown("---")
st.subheader("💡 Insights")

insights = weekly_data.get("insights", [])
if insights:
    for insight in insights:
        st.markdown(f"- {insight}")
else:
    st.info("Insights will appear here after the system has been used for a week.")

# Self-improvement learnings
st.markdown("### 🧠 Self-Improvement Status")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **How The Hub Gets Smarter:**
    1. Users rate query results (1-5 stars)
    2. Chairman picks winning LLM responses
    3. Popular templates rise to the top
    4. Feedback identifies areas for improvement
    """)
with col2:
    st.markdown("""
    **Current Learning Status:**
    - Feedback loop: Active (via /api/feedback)
    - LLM comparison: Active (via The Rubric)
    - Template ranking: Active (by usage + rating)
    - Watchdog scoring: Active (7 criteria per task)
    """)

# ============================================================================
# SUBMIT FEEDBACK (embedded form)
# ============================================================================

st.markdown("---")
st.subheader("📝 Submit Feedback")

col1, col2 = st.columns([2, 1])

with col1:
    feedback_query_id = st.number_input("Query ID", min_value=1, value=1,
                                         help="The query ID from your dashboard result")
    feedback_rating = st.slider("Rating", 1, 5, 4, help="1=Poor, 5=Excellent")
    feedback_comment = st.text_input("Comment (optional)",
                                      placeholder="What was good or bad about this result?")
    feedback_user = st.text_input("Your name", value="finance_team")

with col2:
    st.markdown("### Rating Guide")
    st.markdown("""
    - **5** — Perfect, exactly what I needed
    - **4** — Good, minor improvements possible
    - **3** — Okay, somewhat useful
    - **2** — Poor, missed the point
    - **1** — Wrong or unhelpful
    """)

if st.button("📝 Submit Feedback", type="primary"):
    try:
        resp = requests.post(
            f"{API_URL}/api/feedback",
            json={
                "query_id": feedback_query_id,
                "rating": feedback_rating,
                "comment": feedback_comment if feedback_comment else None,
                "user_id": feedback_user
            },
            timeout=10
        )
        if resp.status_code == 200:
            st.success(f"Feedback recorded! Rating: {feedback_rating}/5")
        else:
            st.error(f"Failed: API returned {resp.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to API. Is the backend running?")
    except Exception as e:
        st.error(f"Error: {e}")

# ============================================================================
# ASK A QUESTION
# ============================================================================

render_voice_data_box("trending")
render_ask_question("trending")

# ============================================================================
# FOOTER
# ============================================================================

render_footer("Trending & Self-Improvement", user=user)
