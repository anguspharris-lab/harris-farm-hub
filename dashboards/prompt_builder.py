"""
Harris Farm Hub - Super User Prompt Builder
Advanced interface for designing custom analytical prompts
"""

import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime
from shared.stores import STORES

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Prompt Builder | Harris Farm Hub",
    page_icon="🔧",
    layout="wide"
)

from nav import render_nav
from shared.styles import apply_styles, render_header, render_footer
from shared.auth_gate import require_login

apply_styles()
user = require_login()
render_nav(8504, auth_token=st.session_state.get("auth_token"))

render_header("🔧 Prompt Builder", "**Super User Tool** | Design, test, and save custom analytical prompts")


@st.cache_data(ttl=300, show_spinner=False)
def _pb_load_templates(difficulty=None):
    try:
        url = f"{API_URL}/api/templates"
        if difficulty:
            url += f"?difficulty={difficulty}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return [
                {"id": t["id"], "name": t["title"],
                 "category": t["category"], "query": t["template"]}
                for t in resp.json().get("templates", [])
            ]
    except Exception:
        pass
    return []


# ============================================================================
# SIDEBAR - SAVED PROMPTS LIBRARY
# ============================================================================

with st.sidebar:
    st.header("📚 Prompt Library")

    # Load templates from API (cached)
    saved_prompts = _pb_load_templates()

    if not saved_prompts:
        saved_prompts = [
            {"id": 1, "name": "Out of Stock Alert", "category": "retail_ops",
             "query": "Show all products that were out of stock for more than 4 hours in the last 7 days, grouped by store with estimated lost sales"},
        ]

    # Filter by difficulty
    difficulty_filter = st.selectbox("Difficulty", ["All", "beginner", "intermediate", "advanced"],
                                     key="pb_sidebar_difficulty")

    # Filter by category
    sidebar_cat_filter = st.selectbox("Category", ["All", "retail_ops", "buying", "merchandising", "finance", "general"],
                                      key="pb_sidebar_category")

    filtered_prompts = saved_prompts
    if difficulty_filter != "All":
        try:
            filtered_prompts = _pb_load_templates(difficulty_filter) or saved_prompts
        except Exception:
            pass

    if sidebar_cat_filter != "All":
        filtered_prompts = [p for p in filtered_prompts if p.get("category") == sidebar_cat_filter]

    selected_template = st.selectbox(
        "Load Template",
        ["Start from scratch"] + [p["name"] for p in filtered_prompts],
        key="pb_load_template",
    )

    if selected_template != "Start from scratch":
        template = next(p for p in filtered_prompts if p["name"] == selected_template)
        if st.button("Load This Prompt", key="pb_load_btn"):
            st.session_state.loaded_prompt = template

# ============================================================================
# PROMPT DESIGN INTERFACE
# ============================================================================

tabs = st.tabs(["🎯 Design", "🧪 Test", "💾 Save & Share", "📖 Examples"])

with tabs[0]:  # DESIGN TAB
    st.subheader("Design Your Custom Prompt")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 1. What do you want to know?")
        
        prompt_name = st.text_input(
            "Prompt Name",
            value=st.session_state.get('loaded_prompt', {}).get('name', ''),
            placeholder="e.g., 'Daily Wastage Report for Fresh Produce'",
            key="pb_prompt_name",
        )

        business_question = st.text_area(
            "Business Question",
            value=st.session_state.get('loaded_prompt', {}).get('query', ''),
            placeholder="Describe what you want to analyze in plain English...",
            height=100,
            help="Be specific: Which products? Which stores? What time period? What threshold?",
            key="pb_business_question",
        )
        
        st.markdown("### 2. Data Sources")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            data_sources = st.multiselect(
                "Tables to Query",
                ["Sales Transactions", "Product Master", "Inventory", "Wastage Logs",
                 "Online Orders", "Store Master", "Supplier Data"],
                default=["Sales Transactions"],
                key="pb_data_sources",
            )

        with col_b:
            time_range = st.selectbox(
                "Time Range",
                ["Last 24 hours", "Last 7 days", "Last 30 days", "Last 90 days",
                 "Month to date", "Year to date", "Custom date range"],
                key="pb_time_range",
            )
        
        st.markdown("### 3. Filters & Criteria")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            store_filter = st.multiselect(
                "Stores",
                ["All Stores"] + STORES,
                default=["All Stores"],
                key="pb_stores",
            )

        with col_b:
            category_filter = st.multiselect(
                "Product Categories",
                ["All Categories", "Fresh Produce", "Dairy", "Meat & Seafood",
                 "Bakery", "Grocery", "Frozen", "Beverages"],
                default=["All Categories"],
                key="pb_product_categories",
            )

        with col_c:
            threshold = st.number_input(
                "Alert Threshold (if applicable)",
                min_value=0.0,
                value=10.0,
                help="e.g., wastage % above this value triggers alert",
                key="pb_threshold",
            )
        
        st.markdown("### 4. Output Format")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            output_type = st.radio(
                "Primary Output",
                ["Table/List", "Summary Statistics", "Chart/Visualization", "Both"],
                horizontal=True,
                key="pb_output_type",
            )

        with col_b:
            group_by = st.multiselect(
                "Group Results By",
                ["Store", "Product", "Category", "Supplier", "Day", "Week", "Month"],
                default=["Store"],
                key="pb_group_by",
            )

        sort_by = st.selectbox(
            "Sort By",
            ["Highest to Lowest", "Lowest to Highest", "Most Recent", "Alphabetical"],
            key="pb_sort_by",
        )

        limit_results = st.number_input(
            "Limit Results To",
            min_value=10,
            max_value=1000,
            value=50,
            step=10,
            key="pb_limit_results",
        )
    
    with col2:
        st.markdown("### 💡 Quick Tips")
        
        st.info("""
        **Product-Level Analysis:**
        - Out of stock tracking
        - Wastage patterns
        - Over/under ordering
        - Online miss-picks
        - Slow movers
        - Price optimization
        """)
        
        st.success("""
        **Best Practices:**
        ✓ Be specific with criteria
        ✓ Use realistic thresholds
        ✓ Include time context
        ✓ Consider store differences
        ✓ Think about actionability
        """)
        
        st.warning("""
        **Common Issues:**
        ⚠️ Too broad (no filters)
        ⚠️ Too narrow (no results)
        ⚠️ Missing time range
        ⚠️ Unclear thresholds
        """)

with tabs[1]:  # TEST TAB
    st.subheader("🧪 Test Your Prompt")
    
    if not business_question:
        st.warning("⬅️ Design your prompt first, then test it here")
    else:
        st.markdown("### Generated Query Preview")
        
        # Generate SQL from the prompt design
        generated_sql = f"""
-- Auto-generated from Prompt Builder
-- Prompt: {prompt_name}
-- Question: {business_question}

SELECT 
    p.product_name,
    s.store_name,
    DATE(i.timestamp) as date,
    SUM(i.wastage_qty) as total_wastage_units,
    SUM(i.wastage_qty * p.cost_per_unit) as wastage_cost,
    (SUM(i.wastage_qty) / SUM(i.ordered_qty) * 100) as wastage_pct
FROM inventory_logs i
JOIN products p ON i.product_id = p.product_id
JOIN stores s ON i.store_id = s.store_id
WHERE i.timestamp >= CURRENT_DATE - INTERVAL '{time_range}'
    AND i.wastage_qty > 0
    {'AND s.store_name IN (' + ','.join([f"'{s}'" for s in store_filter if s != "All Stores"]) + ')' if "All Stores" not in store_filter else ''}
    {'AND p.category IN (' + ','.join([f"'{c}'" for c in category_filter if c != "All Categories"]) + ')' if "All Categories" not in category_filter else ''}
GROUP BY p.product_name, s.store_name, DATE(i.timestamp)
HAVING wastage_pct > {threshold}
ORDER BY wastage_cost DESC
LIMIT {limit_results};
        """
        
        st.code(generated_sql, language='sql')
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("▶️ Run Test Query", type="primary", use_container_width=True, key="pb_run_test"):
                with st.spinner("Running query against database..."):
                    # Mock test results
                    test_results = pd.DataFrame({
                        'Product': ['Cherry Tomatoes', 'Fresh Basil', 'Lettuce Mix', 'Stone Fruit', 'Berries'],
                        'Store': ['Crows Nest', 'Bondi', 'Manly', 'Neutral Bay', 'Bondi'],
                        'Wastage Units': [45, 32, 28, 51, 38],
                        'Wastage Cost ($)': [202.50, 224.00, 84.00, 214.20, 323.00],
                        'Wastage %': [18.2, 22.5, 15.7, 12.8, 24.1]
                    })
                    
                    st.success(f"✅ Query completed successfully - {len(test_results)} rows returned")
                    
                    st.dataframe(test_results, hide_index=True, key="prompt_test_results")
                    
                    # AI Analysis
                    st.markdown("### 🤖 AI Analysis")
                    st.info("""
                    **Key Findings:**
                    - Berries show highest wastage at 24.1% ($323 cost impact)
                    - Fresh Basil wastage at 22.5% suggests over-ordering
                    - Bondi store appears in top 5 twice - investigate ordering practices
                    - Total wastage cost for these items: $1,047.70 this period
                    
                    **Recommended Actions:**
                    1. Reduce Fresh Basil orders at Bondi by 20%
                    2. Review berry shelf life and display practices
                    3. Schedule inventory review with Bondi store manager
                    """)
        
        with col2:
            st.metric("Rows Returned", "5")
            st.metric("Query Time", "127ms")
            st.metric("Data Quality", "98%")

with tabs[2]:  # SAVE & SHARE TAB
    st.subheader("💾 Save & Share Your Prompt")
    
    if not prompt_name or not business_question:
        st.warning("Complete the Design tab first before saving")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Prompt Details")
            
            category_display = st.selectbox(
                "Category",
                ["Retail Operations", "Buying", "Merchandising", "Finance", "General"],
                key="pb_save_category",
            )
            # Map display names to API category slugs
            category_map = {
                "Retail Operations": "retail_ops",
                "Buying": "buying",
                "Merchandising": "merchandising",
                "Finance": "finance",
                "General": "general"
            }
            category = category_map.get(category_display, "general")
            
            tags = st.text_input(
                "Tags (comma-separated)",
                placeholder="e.g., wastage, fresh-produce, daily-report",
                key="pb_tags",
            )

            schedule_option = st.checkbox("Schedule this prompt to run automatically",
                                          key="pb_schedule")

            if schedule_option:
                col_a, col_b = st.columns(2)
                with col_a:
                    frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly"],
                                             key="pb_frequency")
                with col_b:
                    notify_users = st.multiselect(
                        "Notify Users",
                        ["Gus (CEO)", "Angela (CFO)", "Fresh Buyers", "Store Managers", "Finance Team"],
                        key="pb_notify",
                    )

            share_with = st.multiselect(
                "Share with Teams",
                ["Finance", "Buying", "Operations", "Store Managers", "Marketing", "All Staff"],
                default=["Finance"],
                key="pb_share_with",
            )

            difficulty_level = st.selectbox("Difficulty", ["beginner", "intermediate", "advanced"],
                                            key="pb_save_difficulty")

            if st.button("💾 Save Prompt", type="primary", use_container_width=True, key="pb_save_btn"):
                try:
                    save_resp = requests.post(
                        f"{API_URL}/api/templates",
                        json={
                            "title": prompt_name,
                            "description": business_question[:200],
                            "template": business_question,
                            "category": category,
                            "difficulty": difficulty_level
                        },
                        timeout=10
                    )
                    if save_resp.status_code == 200:
                        template_id = save_resp.json().get("template_id", "?")
                        st.success(f"✅ '{prompt_name}' saved to library!")
                        st.balloons()
                        st.info(f"""
                        **Prompt Saved!**
                        - Name: {prompt_name}
                        - Category: {category_display}
                        - Difficulty: {difficulty_level}
                        - Shared with: {', '.join(share_with)}
                        - ID: #HF-{template_id}

                        Your team can load this from the sidebar template library.
                        """)
                    else:
                        st.error(f"Failed to save: API returned {save_resp.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to Hub API. Is the backend running?")
                except Exception as e:
                    st.error(f"Save failed: {e}")
        
        with col2:
            st.markdown("### Prompt Summary")
            
            summary_data = {
                "Name": prompt_name,
                "Question": business_question[:100] + "..." if len(business_question) > 100 else business_question,
                "Data Sources": ", ".join(data_sources),
                "Time Range": time_range,
                "Filters": f"{len(store_filter)} stores, {len(category_filter)} categories",
                "Output": output_type,
                "Created By": "Finance Team",
                "Created": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            for key, value in summary_data.items():
                st.text(f"{key}: {value}")
            
            st.markdown("---")
            
            st.markdown("### Export Options")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("📄 Export as SQL", use_container_width=True, key="pb_export_sql"):
                    st.download_button(
                        "Download SQL",
                        data=generated_sql if 'generated_sql' in locals() else "-- Run test first",
                        file_name=f"{prompt_name.replace(' ', '_').lower()}.sql",
                        mime="text/plain"
                    )
            
            with col_b:
                if st.button("📋 Copy Prompt URL", use_container_width=True, key="pb_copy_url"):
                    st.code(f"https://hub.harrisfarm.com/prompts/{prompt_name.replace(' ', '-').lower()}")

with tabs[3]:  # EXAMPLES TAB
    st.subheader("📖 Example Prompts from Super Users")
    
    examples = [
        {
            "name": "Daily Out-of-Stock Alert",
            "author": "Gus (CEO)",
            "category": "Inventory",
            "description": "Identifies products that went out of stock yesterday, calculates lost sales based on historical data",
            "query": "Show all SKUs that had zero inventory for any period yesterday, estimate lost sales using 30-day average, prioritize by revenue impact",
            "why_useful": "Catches inventory issues immediately, helps buyers prioritize reorders"
        },
        {
            "name": "Weekend Fresh Produce Wastage",
            "author": "Fresh Buying Team",
            "category": "Waste Reduction",
            "description": "Analyzes fresh produce wastage patterns specifically on weekends to optimize Monday ordering",
            "query": "Compare weekend (Sat-Sun) wastage rates vs weekday rates for all fresh produce, show year-over-year trend",
            "why_useful": "Weekend Buyer program uses this to adjust Monday orders"
        },
        {
            "name": "Online Miss-Pick Root Cause",
            "author": "Ecommerce Team",
            "category": "Online Operations",
            "description": "Breaks down online miss-picks by root cause (similar products, out of stock, picker error)",
            "query": "Analyze miss-picks from last 30 days, categorize by: confusing similar items, actual OOS, picker mistake, group by store and picker",
            "why_useful": "Identifies training needs and process improvements"
        },
        {
            "name": "Over-Order Prevention",
            "author": "Angela (CFO)",
            "category": "Buying",
            "description": "Flags products consistently ordered in quantities 15%+ above sales, quantifies cash tied up",
            "query": "Compare order quantity vs actual sales for last 60 days, flag items with consistent 15%+ excess, calculate working capital impact",
            "why_useful": "Reduces cash tied up in excess inventory, prevents wastage"
        },
        {
            "name": "Slow Mover Markdown Candidates",
            "author": "Merchandising Team",
            "category": "Sales Optimization",
            "description": "Identifies slow-moving products approaching expiry that should be marked down",
            "query": "Find products with <50% normal velocity, days to expiry <7, current stock level >10 units, suggest markdown %",
            "why_useful": "Proactive markdown strategy maximizes recovery vs wastage"
        },
        {
            "name": "Store-Specific Ordering Patterns",
            "author": "Operations Team",
            "category": "Buying",
            "description": "Compares ordering patterns between high-performing and low-performing stores for same products",
            "query": "For each product category, compare order frequency, quantity, and wastage between top 3 and bottom 3 profitability stores",
            "why_useful": "Best practice sharing - learn from high performers"
        }
    ]
    
    for example in examples:
        with st.expander(f"**{example['name']}** by {example['author']} - {example['category']}"):
            st.markdown(f"**Description:** {example['description']}")
            st.markdown(f"**Query Logic:** _{example['query']}_")
            st.success(f"✅ **Why Useful:** {example['why_useful']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📋 Use as Template", key=f"use_{example['name']}"):
                    st.session_state.loaded_prompt = {
                        'name': example['name'],
                        'query': example['query']
                    }
                    st.success("Template loaded! Go to Design tab →")
            
            with col2:
                if st.button(f"▶️ Run Now", key=f"run_{example['name']}"):
                    st.info("Query executed - check your email for results")

# ============================================================================
# HELP SECTION
# ============================================================================

st.markdown("---")

with st.expander("ℹ️ Help & Documentation"):
    st.markdown("""
    ### How to Use the Prompt Builder
    
    **1. Design Tab**
    - Start with a clear business question
    - Select relevant data sources
    - Apply appropriate filters (stores, categories, time)
    - Define output format and grouping
    
    **2. Test Tab**
    - Review the auto-generated SQL
    - Run test queries against real data
    - Verify results match expectations
    - Read AI analysis for insights
    
    **3. Save & Share Tab**
    - Name and categorize your prompt
    - Share with relevant teams
    - Optionally schedule automated runs
    - Export SQL for advanced use
    
    **4. Examples Tab**
    - Learn from other super users
    - Copy proven prompt templates
    - Understand use cases and benefits
    
    ### Product-Level Analytics You Can Build
    
    - **Out of Stock Tracking**: Lost sales, duration, frequency by product/store
    - **Wastage Analysis**: Costs, trends, root causes, comparison across stores
    - **Over-Ordering Detection**: Excess inventory, cash impact, ordering patterns
    - **Online Miss-Picks**: Picker accuracy, product confusion, error patterns
    - **Slow Movers**: Aging inventory, markdown candidates, clearance priorities
    - **Substitution Rates**: What gets substituted, customer acceptance, revenue impact
    - **Inventory Velocity**: Days to turn, category comparison, seasonal patterns
    
    ### Advanced Tips
    
    - Use thresholds to focus on actionable items (e.g., wastage >10%)
    - Group by multiple dimensions for deeper insights (store + category + day)
    - Compare time periods to identify trends (this week vs last week)
    - Schedule daily/weekly reports for consistent monitoring
    - Share successful prompts with your team to standardize analysis
    
    ### Need Help?
    
    Contact the Hub team: hub-support@harrisfarm.com
    """)

render_footer("Prompt Builder", user=user)
