"""
Harris Farm Hub - Prompt-to-Approval: Prompt Engine
The front door to data-driven decisions. Choose your task, add context, let AI analyse.
"""

import os
import json

import requests
import streamlit as st
from datetime import datetime, timedelta

from shared.styles import render_header, render_footer
from shared.stores import STORES
from shared.pta_rubric import (
    STANDARD_RUBRIC,
    APPROVAL_ROUTING,
    NINJA_LEVELS,
    get_ninja_level,
    render_rubric_scorecard,
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

user = st.session_state.get("auth_user")

render_header(
    "Prompt Engine",
    "**Prompt-to-Approval** | Choose your task, add context, let AI analyse",
    goals=["G2", "G3"],
    strategy_context="The universal AI workflow — prompt the data, add your judgment, submit for approval.",
)

# ============================================================================
# 20 TASK TEMPLATES
# ============================================================================

TASK_TEMPLATES = {
    "weekly_store_performance": {
        "name": "Weekly Store Performance Report",
        "roles": ["Store Manager", "Area Manager"],
        "default_prompt": (
            "Analyse {store_name} performance for week ending {date}. Compare sales vs budget, "
            "vs last week, vs same week last year. Break down by department. Show waste % by "
            "category vs target. Show sales per labour hour. Identify top 5 over-performers "
            "and top 5 under-performers by product. Provide 3 recommended actions for next week."
        ),
        "data_sources": ["POS", "Waste", "Roster", "Budget"],
        "output_format": "Executive Summary",
    },
    "supplier_price_comparison": {
        "name": "Supplier Price Comparison",
        "roles": ["Buyer", "Head of Buying"],
        "default_prompt": (
            "Compare pricing from all suppliers for {category} over the last {period}. "
            "Rank by average price per unit. Show price volatility (standard deviation). "
            "Show quality score trend if available. Calculate optimal order split to minimise "
            "cost while maintaining quality. Flag any supplier consistently >10% above cheapest."
        ),
        "data_sources": ["Supplier", "Procurement", "Quality"],
        "output_format": "Detailed Report",
    },
    "monthly_variance": {
        "name": "Monthly Variance Analysis",
        "roles": ["Finance Analyst", "CFO"],
        "default_prompt": (
            "Prepare budget vs actual variance report for {month} by cost centre. Flag all "
            "variances >5%. For each flagged variance provide: amount, percentage, likely root "
            "cause (based on historical patterns), and whether it is timing, permanent, or "
            "one-off. Summarise total impact on EBITDA."
        ),
        "data_sources": ["Financial", "Budget"],
        "output_format": "Board Paper Format",
    },
    "board_paper": {
        "name": "Board Paper",
        "roles": ["Executive", "CFO", "Head of Buying"],
        "default_prompt": (
            "Prepare a board paper on {topic}. Structure: Executive Summary (1 paragraph), "
            "Background & Context, Current State (with data), Proposed Changes, Financial Impact "
            "(3 scenarios: conservative, base, optimistic), Risk Analysis (with mitigations), "
            "Implementation Timeline, Recommendation."
        ),
        "data_sources": ["All Available"],
        "output_format": "Board Paper Format",
    },
    "trading_meeting_prep": {
        "name": "Trading Meeting Report",
        "roles": ["Area Manager", "Head of Buying", "Executive"],
        "default_prompt": (
            "Compile trading meeting report for week ending {date}. For each store: sales vs "
            "budget ($ and %), sales vs LY, transaction count trend, basket size trend, waste %, "
            "labour efficiency. Rank stores best to worst on sales vs budget. Highlight top 3 "
            "wins and top 3 concerns across the network."
        ),
        "data_sources": ["POS", "Budget", "Waste", "Roster"],
        "output_format": "Executive Summary",
    },
    "roster_optimisation": {
        "name": "Roster Optimisation",
        "roles": ["Store Manager", "Area Manager", "HR"],
        "default_prompt": (
            "Analyse roster efficiency for {store_name} over last 4 weeks. Show: sales per "
            "labour hour by day of week, peak trading hours vs rostered hours, overtime as % "
            "of total hours, department-level labour allocation vs sales contribution. "
            "Recommend roster adjustments to improve sales per labour hour by at least 5%."
        ),
        "data_sources": ["Roster", "POS"],
        "output_format": "Detailed Report",
    },
    "waste_analysis": {
        "name": "Waste Analysis",
        "roles": ["Store Manager", "Buyer", "Area Manager"],
        "default_prompt": (
            "Analyse waste for {store_or_category} over last {period}. Show: waste % by "
            "category, waste $ by category, trend vs prior period, comparison to network "
            "average. Identify top 10 SKUs by waste $ value. For each, provide: likely root "
            "cause and recommended action. Calculate potential savings if waste reduced to "
            "network best practice."
        ),
        "data_sources": ["Waste", "POS", "Inventory"],
        "output_format": "Detailed Report",
    },
    "customer_demographics": {
        "name": "Customer Demographics Analysis",
        "roles": ["Executive", "Marketing", "Area Manager"],
        "default_prompt": (
            "Analyse the demographic profile within {radius}km of {location}. Show: population, "
            "household income distribution, % professionals/managers, age distribution. Compare "
            "to our current store network averages. Score the location's alignment with our "
            "target customer (50%+ professionals/managers)."
        ),
        "data_sources": ["CBAS", "ABS", "POS"],
        "output_format": "Executive Summary",
    },
    "category_review": {
        "name": "Category Review",
        "roles": ["Buyer", "Head of Buying"],
        "default_prompt": (
            "Prepare a full category review for {category}. Include: sales trend (13 weeks), "
            "margin trend, market share (CBAS within 3/5/10/20km tiers — remember low share "
            "does not equal opportunity), supplier performance ranking, range analysis "
            "(top/bottom performers by margin contribution), and recommended actions."
        ),
        "data_sources": ["POS", "CBAS", "Supplier", "Margin"],
        "output_format": "Detailed Report",
    },
    "it_architecture_proposal": {
        "name": "IT Architecture Proposal",
        "roles": ["IT"],
        "default_prompt": (
            "Prepare a technical proposal for {project}. Include: current state architecture, "
            "proposed architecture, technology selection with justification, integration points "
            "with existing systems (Fabric, POS, Azure AD), security considerations, cost "
            "estimate (build + run), implementation timeline with dependencies, risk register."
        ),
        "data_sources": ["Infrastructure", "Vendor"],
        "output_format": "Board Paper Format",
    },
    "one_on_one_prep": {
        "name": "One-on-One Meeting Prep",
        "roles": ["Executive", "Area Manager", "Head of Buying"],
        "default_prompt": (
            "Prepare for my one-on-one with {person_name} ({their_role}). Pull their area's "
            "key metrics for last {period}: sales performance vs budget, key project status, "
            "team metrics. Show trends. Suggest 3 discussion points based on the data."
        ),
        "data_sources": ["POS", "Budget", "HR", "Projects"],
        "output_format": "Executive Summary",
    },
    "stockout_revenue_analysis": {
        "name": "Stockout & Lost Revenue Analysis",
        "roles": ["Buyer", "Store Manager", "Head of Buying"],
        "default_prompt": (
            "Identify stockout events across {scope} for last {period}. For each: calculate "
            "revenue lost (normal hourly rate x hours out of stock x avg price). Rank by $ "
            "impact. Identify root cause pattern. Provide buyer-specific action list. "
            "Calculate total revenue recovery opportunity."
        ),
        "data_sources": ["POS", "Inventory", "Supplier"],
        "output_format": "Detailed Report",
    },
    "energy_cost_analysis": {
        "name": "Energy & Sustainability Report",
        "roles": ["Finance Analyst", "Executive", "Store Manager"],
        "default_prompt": (
            "Analyse energy costs for {scope} over last {period}. Show: cost per store, cost "
            "per sqm, trend vs prior year, breakdown by type. Identify top 5 stores by energy "
            "cost per $ of sales. Estimate ROI on solar installation for stores without it. "
            "Link to B-Corp sustainability metrics."
        ),
        "data_sources": ["Financial", "Utilities", "Sustainability"],
        "output_format": "Detailed Report",
    },
    "transport_cost_analysis": {
        "name": "Transport & Logistics Cost Analysis",
        "roles": ["Executive", "Finance Analyst"],
        "default_prompt": (
            "Analyse transport costs from Greystanes DC to all stores for last {period}. "
            "Show: cost per store, cost per carton, cost per $ of sales. Map routes and "
            "identify optimisation opportunities. Compare current costs to market rates. "
            "Flag stores where direct-to-store may be cheaper than via DC."
        ),
        "data_sources": ["Financial", "Logistics", "Supplier"],
        "output_format": "Board Paper Format",
    },
    "competitor_pricing": {
        "name": "Competitor Price Check",
        "roles": ["Buyer", "Marketing", "Executive"],
        "default_prompt": (
            "Compare our pricing on {category_or_products} against Coles and Woolworths "
            "within {radius}km of {store}. Show: our price, Coles price, Woolworths price, "
            "our margin, price index. Flag items where we are >15% more expensive. Flag items "
            "where we could increase price. Recommend pricing actions."
        ),
        "data_sources": ["POS", "Competitor", "Margin"],
        "output_format": "Executive Summary",
    },
    "new_store_feasibility": {
        "name": "New Store Feasibility Study",
        "roles": ["Executive"],
        "default_prompt": (
            "Assess feasibility of a new Harris Farm store at {location}. Include: demographics "
            "within 3/5/10/20km (target: 50%+ professionals/managers), existing competition "
            "mapping, estimated catchment population, comparable store benchmarks, estimated "
            "build cost, estimated annual sales (conservative/base/optimistic), payback period, "
            "cannibalisation risk to existing stores."
        ),
        "data_sources": ["CBAS", "ABS", "POS", "Financial", "Property"],
        "output_format": "Board Paper Format",
    },
    "hr_workforce_planning": {
        "name": "Workforce Planning Report",
        "roles": ["HR", "Executive"],
        "default_prompt": (
            "Prepare workforce planning report for {scope}. Show: current headcount by "
            "department and role, turnover rate (13-week and 52-week), average tenure, "
            "vacancies and time-to-fill, training completion rates, upcoming leave liabilities. "
            "Compare to budget and flag variances. Identify departments at risk of understaffing."
        ),
        "data_sources": ["HR", "Roster", "Budget"],
        "output_format": "Detailed Report",
    },
    "marketing_campaign_analysis": {
        "name": "Marketing Campaign Performance",
        "roles": ["Marketing", "Executive"],
        "default_prompt": (
            "Analyse performance of {campaign_name} campaign. Show: incremental sales during "
            "campaign period vs control period, transaction count uplift, new vs returning "
            "customer split, cost of campaign, ROI calculation, category-level impact, "
            "store-level impact. Compare to previous campaigns. Recommend learnings."
        ),
        "data_sources": ["POS", "Marketing", "Financial"],
        "output_format": "Detailed Report",
    },
    "amazon_partnership_review": {
        "name": "Amazon Partnership Performance",
        "roles": ["Executive", "Head of Buying"],
        "default_prompt": (
            "Review Amazon Fresh partnership performance for {period}. Show: orders, revenue, "
            "average order value, product mix, margin after fees, fulfilment accuracy, customer "
            "feedback themes. Compare to in-store equivalent metrics. Assess strategic value "
            "vs operational cost. Recommend adjustments."
        ),
        "data_sources": ["Amazon", "POS", "Financial", "Margin"],
        "output_format": "Board Paper Format",
    },
    "custom": {
        "name": "Custom Analysis",
        "roles": ["All"],
        "default_prompt": "",
        "data_sources": ["User Selected"],
        "output_format": "Executive Summary",
    },
}

ALL_ROLES = [
    "Store Manager", "Area Manager", "Buyer", "Head of Buying",
    "Finance Analyst", "CFO", "Marketing", "IT", "HR",
    "Warehouse", "Executive",
]

OUTPUT_FORMATS = [
    "Executive Summary",
    "Detailed Report",
    "Board Paper Format",
    "Quick Insights",
    "Data Table with Commentary",
]

ANALYSIS_TYPES = ["Compare", "Trend", "Rank", "Root Cause", "Forecast", "Recommend"]

ALL_DATA_SOURCES = [
    "POS", "Budget", "Waste", "Roster", "Supplier", "Inventory",
    "Financial", "CBAS", "ABS", "HR", "Marketing", "Logistics",
    "Procurement", "Quality", "Amazon", "Margin", "Sustainability",
    "Infrastructure", "Vendor", "Property", "Competitor", "Projects",
    "Utilities",
]


# ============================================================================
# SIDEBAR — User profile & submissions
# ============================================================================

with st.sidebar:
    st.header("Your Profile")

    user_role = st.selectbox(
        "Your Role",
        ALL_ROLES,
        help="Determines which templates you see and who approves your work",
        key="pta_role",
    )

    routing = APPROVAL_ROUTING.get(user_role, {})
    st.caption(
        f"Approval route: {user_role} -> {routing.get('approver_role', 'N/A')} "
        f"({routing.get('level', '')})"
    )

    # AI Ninja level
    try:
        stats_resp = requests.get(f"{API_URL}/api/pta/user-stats/staff", timeout=3)
        if stats_resp.status_code == 200:
            stats = stats_resp.json()
            level = stats.get("level", "Prompt Apprentice")
            points = stats.get("total_points", 0)
            level_info = NINJA_LEVELS.get(level, {})
            level_colour = level_info.get("colour", "#6b7280")
            st.markdown(
                f"<div style='background:{level_colour}15; border:1px solid {level_colour}; "
                f"padding:10px; border-radius:8px; text-align:center; margin:8px 0;'>"
                f"<div style='font-size:1.1em; font-weight:700; color:{level_colour};'>{level}</div>"
                f"<div style='font-size:0.85em; color:#666;'>{points} points</div>"
                f"<div style='font-size:0.75em; color:#999;'>"
                f"{stats.get('approved', 0)} approved | {stats.get('avg_rubric_score', 0)}/10 avg</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    except Exception:
        pass

    st.markdown("---")

    # My Submissions
    st.subheader("My Submissions")
    try:
        resp = requests.get(
            f"{API_URL}/api/pta/submissions",
            params={"user_id": "staff", "limit": 5},
            timeout=5,
        )
        if resp.status_code == 200:
            subs = resp.json().get("submissions", [])
            if subs:
                for s in subs:
                    avg = s.get("rubric_average") or 0
                    verdict = s.get("rubric_verdict", "")
                    status = s.get("status", "draft")
                    colour = "#2ECC71" if status == "approved" else "#d97706" if status == "pending_approval" else "#6b7280"
                    st.markdown(
                        f"<div style='padding:4px 0; border-bottom:1px solid #f3f4f6;'>"
                        f"<strong>{s.get('task_type', 'custom')}</strong><br/>"
                        f"<span style='font-size:0.8em; color:{colour};'>{status}</span>"
                        f" | <span style='font-size:0.8em;'>{avg}/10</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No submissions yet. Create your first one below.")
        else:
            st.caption("Could not load submissions.")
    except Exception:
        st.caption("Backend unavailable.")


# ============================================================================
# MAIN CONTENT — Tabbed interface
# ============================================================================

tabs = st.tabs(["Build Prompt", "AI Output & Scorecard", "Submit for Approval", "Template Library"])

# ---------------------------------------------------------------------------
# TAB 1: BUILD PROMPT
# ---------------------------------------------------------------------------
with tabs[0]:

    # Section A — What do you need?
    st.subheader("What do you need?")

    # Filter templates by role
    available_templates = {
        k: v for k, v in TASK_TEMPLATES.items()
        if user_role in v["roles"] or "All" in v["roles"]
    }

    template_names = {k: v["name"] for k, v in available_templates.items()}
    selected_key = st.selectbox(
        "Task Type",
        list(template_names.keys()),
        format_func=lambda k: template_names[k],
        help="Choose the type of analysis you need. Templates are filtered by your role.",
        key="pta_task_type",
    )

    template = available_templates[selected_key]

    # Section B — Context
    st.subheader("Add Your Context")

    col1, col2 = st.columns([2, 1])

    with col1:
        default_prompt = template["default_prompt"]
        prompt_text = st.text_area(
            "Your Prompt",
            value=default_prompt,
            height=180,
            help="Edit the template or write your own. Be specific: which store, what dates, what thresholds.",
            key="pta_prompt_text",
        )

        context_text = st.text_area(
            "Additional Context (optional)",
            placeholder="Add any specific context the AI should know — recent events, special circumstances, deadlines...",
            height=80,
            key="pta_context",
        )

    with col2:
        # Store/scope selector
        if user_role in ("Store Manager",):
            scope = st.selectbox("Your Store", STORES, key="pta_store")
        elif user_role in ("Area Manager",):
            scope = st.selectbox("Area", ["All Stores"] + STORES, key="pta_area")
        else:
            scope = st.text_input("Scope", placeholder="e.g. All stores, Fresh Produce, Sydney region", key="pta_scope")

        # Date range
        date_range = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 4 weeks", "Last 13 weeks", "Last 12 months",
             "Month to date", "Year to date", "Custom"],
            key="pta_date_range",
        )

        # Analysis type
        analysis_types = st.multiselect(
            "Analysis Approach",
            ANALYSIS_TYPES,
            default=["Compare", "Recommend"],
            help="What kind of analysis do you want?",
            key="pta_analysis_types",
        )

    # Data sources & output
    col_a, col_b = st.columns(2)
    with col_a:
        default_sources = template.get("data_sources", [])
        data_sources = st.multiselect(
            "Data Sources",
            ALL_DATA_SOURCES,
            default=[s for s in default_sources if s in ALL_DATA_SOURCES],
            help="Which data should the AI reference?",
            key="pta_data_sources",
        )
    with col_b:
        output_format = st.selectbox(
            "Output Format",
            OUTPUT_FORMATS,
            index=OUTPUT_FORMATS.index(template.get("output_format", "Executive Summary")),
            key="pta_output_format",
        )

    # Provider selection
    provider = st.radio(
        "AI Provider",
        ["claude", "chatgpt", "grok"],
        horizontal=True,
        help="Claude (recommended), ChatGPT, or Grok",
        key="pta_provider",
    )

    # Data confidence badge
    if data_sources:
        source_reliability = {
            "POS": 10, "Budget": 9, "Financial": 9, "Waste": 8, "Roster": 8,
            "Inventory": 7, "Supplier": 7, "CBAS": 7, "ABS": 8, "HR": 8,
            "Margin": 8, "Marketing": 6, "Logistics": 7, "Procurement": 7,
            "Quality": 6, "Amazon": 7, "Sustainability": 6, "Infrastructure": 5,
            "Vendor": 5, "Property": 5, "Competitor": 4, "Projects": 5, "Utilities": 6,
        }
        avg_reliability = sum(source_reliability.get(s, 5) for s in data_sources) / len(data_sources)
        conf_colour = "#2ECC71" if avg_reliability >= 8 else "#d97706" if avg_reliability >= 6 else "#dc2626"
        st.markdown(
            f"<div style='background:{conf_colour}10; border:1px solid {conf_colour}; "
            f"padding:8px 12px; border-radius:6px; margin:8px 0;'>"
            f"<strong style='color:{conf_colour};'>Data Confidence: {avg_reliability:.0f}/10</strong>"
            f" — Sources: {', '.join(data_sources)}</div>",
            unsafe_allow_html=True,
        )

    # Similar prompts hint
    try:
        lib_resp = requests.get(f"{API_URL}/api/templates", timeout=3)
        if lib_resp.status_code == 200:
            lib_templates = lib_resp.json().get("templates", [])
            matching = [t for t in lib_templates if t.get("category") == selected_key]
            if matching:
                st.info(
                    f"**{len(matching)} similar prompt(s)** found in the library. "
                    f"Check the **Template Library** tab to build on existing work."
                )
    except Exception:
        pass

    st.markdown("---")

    # Generate button
    if st.button("Send to AI", type="primary", use_container_width=True, key="pta_generate_btn"):
        if not prompt_text.strip():
            st.error("Please write a prompt before sending.")
        else:
            with st.spinner("AI is analysing your data..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/api/pta/generate",
                        json={
                            "user_id": "staff",
                            "user_role": user_role,
                            "task_type": selected_key,
                            "prompt_text": prompt_text,
                            "context": context_text or None,
                            "data_sources": data_sources,
                            "analysis_types": analysis_types,
                            "output_format": output_format,
                            "provider": provider,
                        },
                        timeout=120,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "success":
                            st.session_state["pta_output"] = data.get("output", "")
                            st.session_state["pta_submission_id"] = data.get("submission_id")
                            st.session_state["pta_generation_done"] = True
                            st.session_state["pta_scores"] = None  # reset scores
                            st.success(
                                f"Output generated ({data.get('tokens', 0)} tokens, "
                                f"{data.get('latency_ms', 0):.0f}ms). "
                                f"Go to **AI Output & Scorecard** tab to review."
                            )
                        else:
                            st.error(f"Generation failed: {data.get('message', 'Unknown error')}")
                    else:
                        st.error(f"API error {resp.status_code}. Is the backend running?")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to Hub backend. Please try again.")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The AI may be slow — try again.")


# ---------------------------------------------------------------------------
# TAB 2: AI OUTPUT & SCORECARD
# ---------------------------------------------------------------------------
with tabs[1]:
    st.subheader("AI Output")

    output = st.session_state.get("pta_output", "")
    submission_id = st.session_state.get("pta_submission_id")

    if not output:
        st.info("No output yet. Go to **Build Prompt** tab and click **Send to AI**.")
    else:
        # Show the output
        st.markdown(output)

        st.markdown("---")

        # Score button
        st.subheader("Rubric Scorecard")

        scores = st.session_state.get("pta_scores")
        if scores:
            render_rubric_scorecard(scores)
        else:
            if st.button("Score This Output", type="primary", key="pta_score_btn"):
                with st.spinner("Scoring against 8-criteria rubric..."):
                    try:
                        resp = requests.post(
                            f"{API_URL}/api/pta/score",
                            json={
                                "submission_id": submission_id,
                                "output_text": output[:8000],
                                "task_type": st.session_state.get("pta_task_type", "custom"),
                                "user_role": st.session_state.get("pta_role", "Store Manager"),
                            },
                            timeout=60,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("status") == "success":
                                st.session_state["pta_scores"] = data["scores"]
                                st.rerun()
                            else:
                                st.error(f"Scoring failed: {data.get('message', 'Unknown error')}")
                        else:
                            st.error(f"API error {resp.status_code}")
                    except Exception as e:
                        st.error(f"Scoring error: {e}")

        # Iterate section
        st.markdown("---")
        st.subheader("Iterate")

        iteration_context = st.text_area(
            "Add context or challenge the AI",
            placeholder="Tell the AI what it got wrong, add context it was missing, or request changes...",
            key="pta_iterate_context",
        )
        if st.button("Iterate", key="pta_iterate_btn"):
            if not iteration_context.strip():
                st.warning("Add some context before iterating.")
            elif submission_id:
                with st.spinner("AI is refining the analysis..."):
                    try:
                        # Send iteration as a new generation with context
                        original_prompt = st.session_state.get("pta_prompt_text", "")
                        resp = requests.post(
                            f"{API_URL}/api/pta/generate",
                            json={
                                "user_id": "staff",
                                "user_role": st.session_state.get("pta_role", "Store Manager"),
                                "task_type": st.session_state.get("pta_task_type", "custom"),
                                "prompt_text": original_prompt,
                                "context": f"Previous output to refine:\n\n{output[:3000]}\n\nUser feedback:\n{iteration_context}",
                                "data_sources": st.session_state.get("pta_data_sources", []),
                                "analysis_types": st.session_state.get("pta_analysis_types", []),
                                "output_format": st.session_state.get("pta_output_format", "Executive Summary"),
                                "provider": st.session_state.get("pta_provider", "claude"),
                            },
                            timeout=120,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data["status"] == "success":
                                st.session_state["pta_output"] = data["output"]
                                st.session_state["pta_submission_id"] = data["submission_id"]
                                st.session_state["pta_scores"] = None
                                st.rerun()
                        else:
                            st.error("Iteration failed.")
                    except Exception as e:
                        st.error(f"Error: {e}")


# ---------------------------------------------------------------------------
# TAB 3: SUBMIT FOR APPROVAL
# ---------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Submit for Approval")

    # 4P Workflow Progress Indicator
    _4P_STAGES = [
        ("\u270d\ufe0f", "Prompt", "#579BFC"),
        ("\U0001f4ca", "Prove", "#00C875"),
        ("\U0001f4e4", "Propose", "#FDAB3D"),
        ("\U0001f680", "Progress", "#E040FB"),
    ]
    output = st.session_state.get("pta_output", "")
    submission_id = st.session_state.get("pta_submission_id")
    scores = st.session_state.get("pta_scores")

    # Determine current stage
    if not output:
        _current_stage = 0  # Still in Prompt
    elif not scores:
        _current_stage = 1  # In Prove (has output, needs scoring)
    else:
        _current_stage = 2  # Ready to Propose

    # Render 4P progress bar
    _stage_html = "<div style='display:flex;gap:4px;margin-bottom:16px;'>"
    for i, (icon, name, colour) in enumerate(_4P_STAGES):
        if i < _current_stage:
            bg = colour
            text_col = "white"
            opacity = "1"
        elif i == _current_stage:
            bg = f"{colour}30"
            text_col = colour
            opacity = "1"
        else:
            bg = "#f3f4f6"
            text_col = "#9ca3af"
            opacity = "0.6"
        _stage_html += (
            f"<div style='flex:1;text-align:center;padding:10px 6px;background:{bg};"
            f"border-radius:8px;opacity:{opacity};'>"
            f"<div style='font-size:1.2em;'>{icon}</div>"
            f"<div style='font-size:0.8em;font-weight:600;color:{text_col};'>{name}</div>"
            f"</div>"
        )
    _stage_html += "</div>"
    st.markdown(_stage_html, unsafe_allow_html=True)

    if not output:
        st.info("Generate and score an output first. You are in the **Prompt** stage.")
    elif not scores:
        st.warning("Score your output before submitting. Go to **AI Output & Scorecard** tab. You are in the **Prove** stage.")
    else:
        # Show summary
        avg = scores.get("average", 0)
        verdict = scores.get("verdict", "REVISE")
        routing = APPROVAL_ROUTING.get(st.session_state.get("pta_role", "Store Manager"), {})

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rubric Average", f"{avg}/10")
        with col2:
            st.metric("Verdict", verdict)
        with col3:
            st.metric("Approval Level", routing.get("level", "L1"))

        st.caption(
            f"This will be sent to **{routing.get('approver_role', 'your manager')}** for review."
        )

        # Link to project (optional)
        st.markdown("---")
        st.markdown("**Link to a Project** (optional)")
        try:
            _proj_resp = requests.get(f"{API_URL}/api/workflow/projects", params={"status": "active"}, timeout=5)
            _projects = _proj_resp.json().get("projects", []) if _proj_resp.status_code == 200 else []
        except Exception:
            _projects = []
        _proj_options = ["None"] + [f"{p['name']} ({p['priority']})" for p in _projects]
        _proj_ids = [None] + [p["id"] for p in _projects]
        _selected_proj_idx = st.selectbox(
            "Project", range(len(_proj_options)),
            format_func=lambda i: _proj_options[i],
            key="pta_project_select",
        )

        st.markdown("---")

        # Mandatory human annotation
        st.markdown(
            "**Add your human judgment** \u2014 at least one annotation is required. "
            "Your insight is what makes this valuable."
        )
        annotation = st.text_area(
            "Your Annotation",
            placeholder="What context does the AI not know? What would you change? What's your recommendation?",
            key="pta_annotation",
        )

        if st.button("Submit for Approval", type="primary", use_container_width=True, key="pta_submit_btn"):
            if not annotation.strip():
                st.error(
                    "Add at least one piece of context or feedback before submitting. "
                    "Your human judgment is what makes this valuable."
                )
            elif submission_id:
                try:
                    resp = requests.post(
                        f"{API_URL}/api/pta/submit",
                        json={
                            "submission_id": submission_id,
                            "human_annotations": [annotation],
                        },
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        # Link to project if selected
                        _pid = _proj_ids[_selected_proj_idx] if _selected_proj_idx and _selected_proj_idx < len(_proj_ids) else None
                        if _pid:
                            try:
                                requests.post(
                                    f"{API_URL}/api/workflow/link",
                                    params={"submission_id": submission_id, "project_id": _pid},
                                    timeout=5,
                                )
                            except Exception:
                                pass

                        # Advance workflow to proposing
                        try:
                            requests.post(
                                f"{API_URL}/api/workflow/transition",
                                json={
                                    "submission_id": submission_id,
                                    "to_stage": "proposing",
                                    "triggered_by": user,
                                    "reason": "Submitted for approval",
                                },
                                timeout=5,
                            )
                        except Exception:
                            pass

                        st.success("Submitted for approval! Your manager will review it.")
                        st.balloons()
                    else:
                        err = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                        st.error(err.get("detail", f"Submission failed ({resp.status_code})"))
                except Exception as e:
                    st.error(f"Error: {e}")


# ---------------------------------------------------------------------------
# TAB 4: TEMPLATE LIBRARY
# ---------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Template Library")
    st.markdown("Browse all 20 task templates. Templates are filtered by your role.")

    current_role = st.session_state.get("pta_role", "Store Manager")

    for key, tmpl in TASK_TEMPLATES.items():
        if current_role not in tmpl["roles"] and "All" not in tmpl["roles"]:
            continue

        with st.expander(f"**{tmpl['name']}**"):
            st.markdown(f"**Roles:** {', '.join(tmpl['roles'])}")
            st.markdown(f"**Data Sources:** {', '.join(tmpl.get('data_sources', []))}")
            st.markdown(f"**Output Format:** {tmpl.get('output_format', 'Executive Summary')}")
            if tmpl["default_prompt"]:
                st.code(tmpl["default_prompt"], language=None)

            if st.button("Use This Template", key=f"pta_use_{key}"):
                st.session_state["pta_task_type"] = key
                st.session_state["pta_prompt_text"] = tmpl["default_prompt"]
                st.rerun()

    # Also show templates from API library
    st.markdown("---")
    st.markdown("### Saved Prompts")
    try:
        resp = requests.get(f"{API_URL}/api/templates", timeout=5)
        if resp.status_code == 200:
            templates = resp.json().get("templates", [])
            if templates:
                for t in templates:
                    with st.expander(f"**{t['title']}** — {t.get('category', '')}"):
                        st.markdown(f"**Difficulty:** {t.get('difficulty', 'beginner')}")
                        st.markdown(f"**Uses:** {t.get('uses', 0)}")
                        if t.get("template"):
                            st.code(t["template"], language=None)
            else:
                st.caption("No saved prompts yet.")
    except Exception:
        st.caption("Could not load saved prompts.")


# ============================================================================
# FOOTER
# ============================================================================

render_footer("Prompt Engine", user=user)
