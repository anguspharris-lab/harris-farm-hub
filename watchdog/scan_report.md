# WATCHDOG Dashboard Scan Report
Generated: 2026-02-17T01:09:59

## Summary
- Dashboards scanned: 17
- Total components: 192
- Total issues: 0
- Critical (nested expanders): 0

## Issues
No issues found.

## Component Inventory

### buying_hub_dashboard.py (500 lines)
Page title: Buying Hub | Harris Farm Hub

- **expander**: 1 instance(s)
  - line 233: Detail table
- **selectbox**: 2 instance(s)
  - line 270, key='drill_dept': Department
  - line 302, key='drill_mg': Select Major Group to drill into
- **Tabs** (line 129): Department Overview, Category Drill-Down, Buyer Dashboard, Range Review, Trading Patterns

### chatbot_dashboard.py (170 lines)
Page title: Hub Assistant | Harris Farm Hub

- **button**: 2 instance(s)
  - line 62: Clear Chat
  - line 82
- **expander**: 2 instance(s)
  - line 98
  - line 147
- **selectbox**: 2 instance(s)
  - line 40: AI Provider
  - line 56: Filter by Category

### customer_dashboard.py (299 lines)
Page title: Customer Analytics | Harris Farm Hub

- **expander**: 1 instance(s)
  - line 288: Detailed Data Table
- **multiselect**: 1 instance(s)
  - line 127: Stores
- **selectbox**: 2 instance(s)
  - line 119: Time Period
  - line 136: Channel

### hub_portal.py (2589 lines)
Page title: Hub Portal | Harris Farm Hub

- **button**: 14 instance(s)
  - line 359
  - line 368
  - line 377
  - line 654, key='portal_save_prompt': Save to History
  - line 785, key='portal_award_btn': Award
  - ... and 9 more
- **expander**: 13 instance(s)
  - line 323
  - line 442
  - line 595
  - line 616
  - line 777: Award Points (Admin)
  - ... and 8 more
- **number_input**: 1 instance(s)
  - line 780, key='portal_award_pts': Points
- **radio**: 3 instance(s)
  - line 744, key='portal_lb_period': Period
  - line 1241, key='insight_type_filter': Type
  - line 2151, key='wd_proposal_filter': Filter
- **selectbox**: 7 instance(s)
  - line 782, key='portal_award_cat': Category
  - line 936, key='arena_team_select': Select team
  - line 1017, key='arena_eval_select': Select proposal to evaluate
  - line 1155, key='agent_bu_filter': Filter by Business Unit
  - line 1399, key='di_analysis_type': Analysis Type
  - ... and 2 more
- **slider**: 4 instance(s)
  - line 651, key='portal_prompt_rating': Rate this prompt
  - line 1036
  - line 1421, key='di_days_slider': Lookback (days)
  - line 1649, key='at_days_slider': Lookback (days)
- **Tabs** (line 299): Documentation, Data Catalog, Showcase, Prompt Library, Scoreboard, The Arena, Agent Network, Data Intelligence, WATCHDOG Safety, Self-Improvement, Agent Control
- **Tabs** (line 586): Browse Library, My History, Submit Prompt
- **Tabs** (line 1359): Run Analysis, Generated Reports, Agent Tasks, Demo Insights
- **Tabs** (line 2192): Analysis Log, Decision Log
- **Tabs** (line 2421): Pending Approval, Agent Performance, Task History
- **text_area**: 2 instance(s)
  - line 636, key='portal_submit_prompt': Your prompt
  - line 1627, key='at_query_input': What do you want to analyse?
- **text_input**: 8 instance(s)
  - line 315, key='portal_search': Search all documentation
  - line 641, key='portal_prompt_context': Context (optional)
  - line 646, key='portal_prompt_outcome': Outcome (optional)
  - line 778, key='portal_award_user': User ID
  - line 784, key='portal_award_reason': Reason
  - ... and 3 more

### learning_centre.py (619 lines)
Page title: Learning Centre | Harris Farm Hub

- **button**: 5 instance(s)
  - line 215
  - line 438, key='quick_check': Quick Check (instant)
  - line 446, key='ai_coach': AI Coach (detailed)
  - line 497, key='score_prompt': Score My Prompt
  - line 585, key='sandbox_send': Send
- **checkbox**: 2 instance(s)
  - line 149: Show hints
  - line 155: Show success criteria
- **expander**: 5 instance(s)
  - line 333: Quick Reference: The 5 Building Blocks of Good Pro
  - line 367
  - line 424: Hints
  - line 467: Success criteria for this challenge
  - line 479: View the 5 scoring criteria
- **radio**: 2 instance(s)
  - line 393, key='lab_mode': Choose a tool:
  - line 408, key='challenge_difficulty': Difficulty:
- **selectbox**: 4 instance(s)
  - line 183: Select a module:
  - line 244, key='lc_function': Your function:
  - line 415, key='challenge_select': Select a challenge:
  - line 579, key='sandbox_provider': AI Provider
- **Tabs** (line 228): My Dashboard, AI Prompting Skills, Data Prompting, Company Knowledge, Practice Lab
- **text_area**: 3 instance(s)
  - line 428, key='challenge_prompt': Write your prompt here:
  - line 490, key='rubric_prompt': Write your prompt here:
  - line 572, key='sandbox_prompt': Your prompt:
- **text_input**: 2 instance(s)
  - line 250, key='lc_department': Your department:
  - line 359, key='kb_search': Search for policies, procedures, or information...
- **API calls**: 2 endpoint(s)
  - /api/knowledge/search
  - /api/learning/modules

### market_share_dashboard.py (324 lines)
Page title: Market Share | Harris Farm Hub

- **expander**: 1 instance(s)
  - line 309: Full Region Data Table
- **multiselect**: 1 instance(s)
  - line 122: Regions (search to filter)
- **selectbox**: 2 instance(s)
  - line 114: Channel
  - line 118: Period

### product_intel_dashboard.py (480 lines)
Page title: Product Intelligence | Harris Farm Hub

- **selectbox**: 1 instance(s)
  - line 124: Top N Items
- **slider**: 1 instance(s)
  - line 409: Transaction Threshold
- **Tabs** (line 189): Top Items, PLU Deep Dive, Basket Analysis, Slow Movers, Trading Patterns
- **text_input**: 1 instance(s)
  - line 258: Enter PLU ID

### profitability_dashboard.py (738 lines)
Page title: Store Profitability | Harris Farm Hub

- **multiselect**: 1 instance(s)
  - line 260: Stores
- **radio**: 1 instance(s)
  - line 267: View By
- **selectbox**: 1 instance(s)
  - line 257: Analysis Period

### prompt_builder.py (571 lines)
Page title: Prompt Builder | Harris Farm Hub

- **button**: 7 instance(s)
  - line 92, key='pb_load_btn': Load This Prompt
  - line 280, key='pb_run_test': ▶️ Run Test Query
  - line 372, key='pb_save_btn': 💾 Save Prompt
  - line 430, key='pb_export_sql': 📄 Export as SQL
  - line 439, key='pb_copy_url': 📋 Copy Prompt URL
  - ... and 2 more
- **checkbox**: 1 instance(s)
  - line 347, key='pb_schedule': Schedule this prompt to run automatically
- **expander**: 2 instance(s)
  - line 497
  - line 521: ℹ️ Help & Documentation
- **multiselect**: 6 instance(s)
  - line 130, key='pb_data_sources': Tables to Query
  - line 151, key='pb_stores': Stores
  - line 159, key='pb_product_categories': Product Categories
  - line 189, key='pb_group_by': Group Results By
  - line 356, key='pb_notify': Notify Users
  - ... and 1 more
- **number_input**: 2 instance(s)
  - line 168, key='pb_threshold': Alert Threshold (if applicable)
  - line 202, key='pb_limit_results': Limit Results To
- **radio**: 1 instance(s)
  - line 181, key='pb_output_type': Primary Output
- **selectbox**: 8 instance(s)
  - line 67, key='pb_sidebar_difficulty': Difficulty
  - line 71, key='pb_sidebar_category': Category
  - line 84, key='pb_load_template': Load Template
  - line 139, key='pb_time_range': Time Range
  - line 196, key='pb_sort_by': Sort By
  - ... and 3 more
- **Tabs** (line 99): 🎯 Design, 🧪 Test, 💾 Save & Share, 📖 Examples
- **text_area**: 1 instance(s)
  - line 116, key='pb_business_question': Business Question
- **text_input**: 2 instance(s)
  - line 109, key='pb_prompt_name': Prompt Name
  - line 341, key='pb_tags': Tags (comma-separated)

### revenue_bridge_dashboard.py (509 lines)
Page title: Revenue Bridge | Harris Farm Hub

- **expander**: 5 instance(s)
  - line 242: View monthly data
  - line 288: View decomposition data
  - line 377: Detail table
  - line 428: View store data
  - line 479: View YoY data table
- **Tabs** (line 198): Monthly Revenue, Revenue Decomposition, Department Breakdown, Store Rankings, Year-over-Year, Trading Patterns

### rubric_dashboard.py (645 lines)
Page title: The Rubric | Harris Farm Hub

- **button**: 6 instance(s)
  - line 184, key='rubric_check_prompt': 🎯 Check My Prompt
  - line 193, key='rubric_try_real': 🚀 Try It For Real
  - line 323, key='run_compare': ⚖️ Run The Rubric
  - line 419, key='cmp_decide': Record Decision
  - line 559, key='save_scorecard': Save My Evaluation
  - ... and 1 more
- **checkbox**: 4 instance(s)
  - line 291, key='cmp_claude': Claude
  - line 292, key='cmp_chatgpt': ChatGPT
  - line 293, key='cmp_grok': Grok
  - line 305, key='cmp_kb': Include KB context
- **expander**: 8 instance(s)
  - line 95
  - line 106
  - line 157: Hints (click for help)
  - line 252
  - line 394
  - ... and 3 more
- **radio**: 3 instance(s)
  - line 145, key='rubric_practice_difficulty': Difficulty
  - line 148, key='rubric_practice_challenge': Challenge
  - line 416, key='cmp_winner': Select the winner
- **slider**: 1 instance(s)
  - line 500
- **Tabs** (line 62): 📖 Learn, ✏️ Practice, ⚖️ Compare, 📋 Scorecard, 🏅 My Progress
- **text_area**: 3 instance(s)
  - line 161: Write your prompt here:
  - line 275, key='compare_prompt': Your question
  - line 282, key='compare_context': Additional context (optional)
- **text_input**: 1 instance(s)
  - line 417, key='cmp_feedback': Why? (optional)

### sales_dashboard.py (780 lines)
Page title: Sales Performance | Harris Farm Hub

- **button**: 1 instance(s)
  - line 746, key='sales_nl_search': Search
- **expander**: 1 instance(s)
  - line 764: View Generated SQL
- **multiselect**: 3 instance(s)
  - line 306, key='sales_stores': Stores
  - line 310, key='sales_depts': Department
  - line 334: Major Group
- **selectbox**: 1 instance(s)
  - line 299, key='sales_period': Time Period
- **text_input**: 1 instance(s)
  - line 740, key='sales_nl_query': Natural Language Query
- **API calls**: 1 endpoint(s)
  - http://localhost:8000/api/query

### store_ops_dashboard.py (610 lines)
Page title: Store Operations | Harris Farm Hub

- **checkbox**: 1 instance(s)
  - line 217, key='so_lfl_toggle': Like-for-like stores only
- **expander**: 1 instance(s)
  - line 422: View data table
- **Tabs** (line 360): Daily Trend, Trading Patterns, Category Mix, Anomaly Detection

### transport_dashboard.py (591 lines)
Page title: Transport Costs | Harris Farm Hub

- **button**: 1 instance(s)
  - line 574: Analyze
- **multiselect**: 1 instance(s)
  - line 218: Stores
- **selectbox**: 3 instance(s)
  - line 215: Time Period
  - line 225: Supplier Type
  - line 231: Vehicle Type
- **slider**: 1 instance(s)
  - line 500: Target Cost Reduction %
- **text_input**: 1 instance(s)
  - line 569: Question

### trending_dashboard.py (324 lines)
Page title: Trending | Harris Farm Hub

- **button**: 1 instance(s)
  - line 299: 📝 Submit Feedback
- **number_input**: 1 instance(s)
  - line 282: Query ID
- **slider**: 1 instance(s)
  - line 284: Rating
- **text_input**: 2 instance(s)
  - line 285: Comment (optional)
  - line 287: Your name
