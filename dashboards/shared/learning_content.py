"""Harris Farm Hub — Learning Centre Content

12 learning modules across 3 pillars, lesson content, role-based mappings,
and rubric evaluator system prompt.
"""

import json

# ---------------------------------------------------------------------------
# 12 LEARNING MODULES (L1-L4, D1-D4, K1-K4)
# ---------------------------------------------------------------------------

MODULES = [
    # --- Core AI Skills ---
    {
        "code": "L1",
        "pillar": "core_ai",
        "name": "Prompting Fundamentals",
        "description": (
            "Learn the building blocks of effective AI prompts. "
            "Master Task, Context, Format, and Constraints to get "
            "useful answers from any AI tool."
        ),
        "duration_minutes": 30,
        "difficulty": "beginner",
        "prerequisites": "[]",
        "sort_order": 1,
        "icon": "🎯",
    },
    {
        "code": "L2",
        "pillar": "core_ai",
        "name": "Rubric-Based Optimisation",
        "description": (
            "Use a structured rubric to evaluate and improve AI responses. "
            "Learn to score outputs systematically and refine prompts "
            "until they deliver what you need."
        ),
        "duration_minutes": 45,
        "difficulty": "intermediate",
        "prerequisites": '["L1"]',
        "sort_order": 2,
        "icon": "⚖️",
    },
    {
        "code": "L3",
        "pillar": "core_ai",
        "name": "Advanced Techniques",
        "description": (
            "Chain-of-thought reasoning, few-shot examples, and multi-step "
            "workflows. Take your prompting to the next level with techniques "
            "used by AI power users."
        ),
        "duration_minutes": 60,
        "difficulty": "advanced",
        "prerequisites": '["L1", "L2"]',
        "sort_order": 3,
        "icon": "🧠",
    },
    {
        "code": "L4",
        "pillar": "core_ai",
        "name": "Role-Specific Applications",
        "description": (
            "Ready-to-use prompt templates tailored for Buyers, Store Managers, "
            "Finance, Marketing, and Operations. Real Harris Farm scenarios "
            "you can use tomorrow."
        ),
        "duration_minutes": 45,
        "difficulty": "intermediate",
        "prerequisites": '["L1"]',
        "sort_order": 4,
        "icon": "👤",
    },
    # --- Applied Data Skills ---
    {
        "code": "D1",
        "pillar": "data",
        "name": "HFM Data Overview",
        "description": (
            "Understand what data Harris Farm collects, where it lives, "
            "and how it flows. From store sales to customer analytics — "
            "know your data landscape."
        ),
        "duration_minutes": 30,
        "difficulty": "beginner",
        "prerequisites": "[]",
        "sort_order": 5,
        "icon": "🗂️",
    },
    {
        "code": "D2",
        "pillar": "data",
        "name": "Querying & Analysis",
        "description": (
            "Use AI to query Harris Farm data. Learn to filter, aggregate, "
            "and compare store performance, sales trends, and customer metrics "
            "without writing code."
        ),
        "duration_minutes": 45,
        "difficulty": "intermediate",
        "prerequisites": '["D1", "L1"]',
        "sort_order": 6,
        "icon": "🔍",
    },
    {
        "code": "D3",
        "pillar": "data",
        "name": "Interpreting Results",
        "description": (
            "Read analytics dashboards with confidence. Identify trends, "
            "spot anomalies, and contextualise numbers with business knowledge. "
            "Turn data into decisions."
        ),
        "duration_minutes": 45,
        "difficulty": "intermediate",
        "prerequisites": '["D1"]',
        "sort_order": 7,
        "icon": "📊",
    },
    {
        "code": "D4",
        "pillar": "data",
        "name": "Custom Analytics",
        "description": (
            "Build your own reports and department-specific views. "
            "Design recurring analytics workflows that answer the questions "
            "your team asks every week."
        ),
        "duration_minutes": 60,
        "difficulty": "advanced",
        "prerequisites": '["D2", "D3"]',
        "sort_order": 8,
        "icon": "📈",
    },
    # --- Harris Farm Knowledge Base ---
    {
        "code": "K1",
        "pillar": "knowledge",
        "name": "Company Foundation",
        "description": (
            "Harris Farm Markets history, values, B-Corp certification, "
            "and strategic direction. Understand the company you work for "
            "and where it's headed."
        ),
        "duration_minutes": 20,
        "difficulty": "beginner",
        "prerequisites": "[]",
        "sort_order": 9,
        "icon": "🏪",
    },
    {
        "code": "K2",
        "pillar": "knowledge",
        "name": "Policies & Procedures",
        "description": (
            "HR policies, operational standards, food safety compliance, "
            "and workplace rules. Know the standards that keep Harris Farm "
            "running safely and legally."
        ),
        "duration_minutes": 30,
        "difficulty": "beginner",
        "prerequisites": "[]",
        "sort_order": 10,
        "icon": "📋",
    },
    {
        "code": "K3",
        "pillar": "knowledge",
        "name": "Employment Information",
        "description": (
            "Pay awards, leave entitlements, career development pathways, "
            "and employee benefits. Everything you need to know about "
            "working at Harris Farm."
        ),
        "duration_minutes": 25,
        "difficulty": "beginner",
        "prerequisites": "[]",
        "sort_order": 11,
        "icon": "💼",
    },
    {
        "code": "K4",
        "pillar": "knowledge",
        "name": "Operational Excellence",
        "description": (
            "Product standards, customer service best practices, visual "
            "merchandising, and department-specific golden rules. "
            "The playbook for excellence on the shop floor."
        ),
        "duration_minutes": 35,
        "difficulty": "beginner",
        "prerequisites": "[]",
        "sort_order": 12,
        "icon": "⭐",
    },
]


# ---------------------------------------------------------------------------
# LESSON CONTENT — at least 1 lesson per module
# ---------------------------------------------------------------------------

LESSONS = [
    # ===== L1: Prompting Fundamentals =====
    {
        "module_code": "L1",
        "lesson_number": 1,
        "title": "The 4 Elements of Effective Prompts",
        "content_type": "theory",
        "duration_minutes": 15,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "Why Prompt Structure Matters",
                    "body": (
                        "AI tools like ChatGPT and Claude are powerful, but they only work well "
                        "when you tell them clearly what you need. Think of it like placing an order "
                        "at a supplier — if you just say 'send me some fruit', you'll get random fruit. "
                        "But if you specify the variety, quantity, ripeness, and delivery date, "
                        "you get exactly what you need.\n\n"
                        "Every great prompt has **4 elements**:\n\n"
                        "1. **Task** — What do you want the AI to do? Use action words: Analyse, Compare, List, Explain\n"
                        "2. **Context** — What background does the AI need? Mention Harris Farm, your department, the situation\n"
                        "3. **Format** — How should the answer look? A numbered list, table, bullet points, step-by-step\n"
                        "4. **Constraints** — What limits apply? Time period, number of results, what to include or exclude"
                    ),
                },
                {
                    "type": "example",
                    "title": "Harris Farm Example",
                    "bad": "Tell me about fruit wastage",
                    "good": (
                        "Analyse the top 3 causes of stone fruit wastage at our Bondi store "
                        "over the last 4 weeks. Present as a numbered list with estimated "
                        "cost impact and one specific action for each cause."
                    ),
                    "explanation": (
                        "The good prompt has all 4 elements: Task (Analyse top 3 causes), "
                        "Context (stone fruit, Bondi store), Format (numbered list with cost + action), "
                        "Constraints (last 4 weeks, top 3 only)."
                    ),
                },
                {
                    "type": "exercise",
                    "title": "Your Turn: Rewrite a Weak Prompt",
                    "scenario": (
                        "Your manager asks: 'Can you use AI to find out why we're wasting so much bread?' "
                        "Rewrite this as an effective prompt using all 4 elements."
                    ),
                    "hints": [
                        "Start with an action word like 'Analyse' or 'Identify'",
                        "Mention Harris Farm, the bakery department, and a specific store if possible",
                        "Ask for the answer in a specific format (list, table, etc.)",
                        "Set a time period (last week, last month, etc.)",
                    ],
                    "criteria": [
                        "Has a clear task with an action verb",
                        "Mentions Harris Farm context (bakery, store, etc.)",
                        "Specifies an output format",
                        "Includes at least one constraint",
                    ],
                },
            ],
        }),
    },
    {
        "module_code": "L1",
        "lesson_number": 2,
        "title": "Adding a Role to Your Prompts",
        "content_type": "theory",
        "duration_minutes": 10,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "The Power of Role Assignment",
                    "body": (
                        "One of the most powerful techniques in prompting is telling the AI **who to be**. "
                        "When you say 'You are a Harris Farm fresh produce specialist with 10 years of experience', "
                        "the AI adjusts its language, expertise level, and perspective.\n\n"
                        "**Good roles for Harris Farm prompts:**\n"
                        "- 'You are a Harris Farm store manager responsible for the dairy section'\n"
                        "- 'Act as a buying analyst for Harris Farm Markets'\n"
                        "- 'You are a customer service expert at a premium grocery retailer'\n\n"
                        "**Tips:**\n"
                        "- Be specific about the role's department and experience\n"
                        "- Match the role to the question you're asking\n"
                        "- Start with 'You are a...' or 'Act as a...'"
                    ),
                },
                {
                    "type": "example",
                    "title": "Role Makes the Difference",
                    "bad": "How should I arrange the cheese display?",
                    "good": (
                        "You are a Harris Farm visual merchandising expert who specialises "
                        "in premium cheese displays. Recommend an arrangement for our "
                        "artisan cheese section that maximises customer engagement and "
                        "cross-selling. Include 5 specific tips with examples."
                    ),
                    "explanation": (
                        "Adding the role of 'visual merchandising expert' means the AI draws "
                        "on retail display expertise rather than giving generic advice."
                    ),
                },
            ],
        }),
    },
    # ===== L2: Rubric-Based Optimisation =====
    {
        "module_code": "L2",
        "lesson_number": 1,
        "title": "Introduction to Rubric Scoring",
        "content_type": "theory",
        "duration_minutes": 15,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "What is a Rubric?",
                    "body": (
                        "A rubric is a scoring guide that helps you evaluate quality consistently. "
                        "Instead of just saying 'that's a good answer' or 'that's not helpful', "
                        "a rubric breaks quality into specific criteria you can measure.\n\n"
                        "**The Hub uses 5 scoring criteria for AI responses:**\n\n"
                        "| Criteria | What it Measures | Score 1 | Score 5 |\n"
                        "|----------|-----------------|---------|----------|\n"
                        "| Request Clarity | Is the prompt clear? | Vague, ambiguous | Crystal clear, specific |\n"
                        "| Context Provision | HFM-relevant details? | No context | Rich with specifics |\n"
                        "| Data Specification | What data to use? | No data mentioned | Exact sources named |\n"
                        "| Output Format | Desired structure? | No format requested | Precise format defined |\n"
                        "| Actionability | Leads to action? | Theoretical only | Every point actionable |\n\n"
                        "**Total possible score: 25 points**\n\n"
                        "Scoring rubrics help you improve systematically — each low score "
                        "tells you exactly what to fix."
                    ),
                },
                {
                    "type": "exercise",
                    "title": "Score This Prompt",
                    "scenario": (
                        "Score the following prompt against all 5 criteria (1-5 each):\n\n"
                        "'Tell me about our sales performance recently'"
                    ),
                    "hints": [
                        "Request Clarity: Is 'sales performance' specific enough?",
                        "Context: Does it mention Harris Farm, a store, a department?",
                        "Data Specification: Does it say which data to look at?",
                        "Output Format: Does it say how to present the answer?",
                        "Actionability: Would the answer help you do something specific?",
                    ],
                    "criteria": [
                        "Should score low (1-2) on most criteria",
                        "Can identify specific improvements for each criterion",
                    ],
                },
            ],
        }),
    },
    # ===== L3: Advanced Techniques =====
    {
        "module_code": "L3",
        "lesson_number": 1,
        "title": "Chain-of-Thought Prompting",
        "content_type": "theory",
        "duration_minutes": 20,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "Think Step by Step",
                    "body": (
                        "Chain-of-thought prompting asks the AI to show its reasoning, "
                        "not just its answer. This is powerful for complex analysis where "
                        "you need to understand *how* the AI reached its conclusion.\n\n"
                        "**The technique:** Add phrases like:\n"
                        "- 'Think through this step by step'\n"
                        "- 'Show your reasoning at each stage'\n"
                        "- 'First analyse X, then consider Y, finally recommend Z'\n\n"
                        "**When to use it at Harris Farm:**\n"
                        "- Diagnosing why a store is underperforming\n"
                        "- Comparing supplier options with multiple trade-offs\n"
                        "- Planning staffing changes based on traffic patterns\n"
                        "- Investigating root causes of wastage spikes"
                    ),
                },
                {
                    "type": "example",
                    "title": "Chain-of-Thought for Root Cause Analysis",
                    "bad": "Why is wastage high at Mosman?",
                    "good": (
                        "You are a Harris Farm operations analyst. Investigate why fresh produce "
                        "wastage at Mosman has increased 15% this month compared to last month. "
                        "Think through this step by step:\n"
                        "1. First, identify the top 3 product categories with the biggest increase\n"
                        "2. For each, analyse possible causes (ordering, storage, display, demand)\n"
                        "3. Compare with similar-sized stores that didn't see an increase\n"
                        "4. Recommend 3 specific actions ranked by expected impact\n\n"
                        "Present each step clearly with your reasoning."
                    ),
                    "explanation": (
                        "Breaking the analysis into numbered steps forces the AI to be methodical "
                        "and show its work, making the answer more trustworthy and actionable."
                    ),
                },
            ],
        }),
    },
    # ===== L4: Role-Specific Applications =====
    {
        "module_code": "L4",
        "lesson_number": 1,
        "title": "Prompt Templates by Department",
        "content_type": "theory",
        "duration_minutes": 15,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "Ready-to-Use Templates",
                    "body": (
                        "Different roles at Harris Farm need different types of AI assistance. "
                        "Here are starter templates for common tasks:\n\n"
                        "**Store Managers:**\n"
                        "- Daily department health check\n"
                        "- Staff roster optimisation analysis\n"
                        "- Customer complaint response drafting\n"
                        "- Halo product identification for store entrance displays\n"
                        "- Intraday stockout monitoring for high-value items\n\n"
                        "**Buyers:**\n"
                        "- Supplier performance comparison\n"
                        "- Seasonal demand forecasting\n"
                        "- Over/under ordering detection\n"
                        "- Specials uplift forecasting: how many units to order per store on special\n"
                        "- Slow mover identification for range review\n\n"
                        "**Finance:**\n"
                        "- Shrinkage analysis by department\n"
                        "- Margin trend identification\n"
                        "- Budget variance explanation\n"
                        "- Price dispersion across stores\n\n"
                        "**Marketing:**\n"
                        "- Campaign performance analysis\n"
                        "- Customer segment insights\n"
                        "- Competitor activity summary\n"
                        "- Basket analysis for cross-promotion planning"
                    ),
                },
                {
                    "type": "example",
                    "title": "Buyer Template: Supplier Scorecard",
                    "bad": "How are our suppliers doing?",
                    "good": (
                        "You are a Harris Farm buying analyst. Create a supplier performance "
                        "scorecard for our top 5 stone fruit suppliers over the last quarter. "
                        "Score each supplier on: on-time delivery rate, quality rejection rate, "
                        "price competitiveness vs market, and order fill rate. "
                        "Present as a comparison table with an overall ranking and one "
                        "improvement action per supplier."
                    ),
                    "explanation": (
                        "This template gives buyers a reusable framework — they just swap in "
                        "the product category and time period for any category review."
                    ),
                },
                {
                    "type": "example",
                    "title": "Buyer Template: Specials Order Forecast",
                    "bad": "How much should I order for the avocado special?",
                    "good": (
                        "Run a specials uplift analysis for avocados across all stores for the "
                        "last 90 days. I need to know: what is the typical demand multiplier "
                        "when avocados go on special? What discount percentage triggers the "
                        "best uplift? How many units should each store order per week during "
                        "the special? Present as a table by store with the weekly forecast quantity."
                    ),
                    "explanation": (
                        "This template uses the Specials Uplift analysis. The system detects "
                        "historical price drops, measures the volume increase, and forecasts "
                        "the order quantity buyers should place per store."
                    ),
                },
                {
                    "type": "example",
                    "title": "Store Manager Template: Halo Products",
                    "bad": "What should I put at the front of the store?",
                    "good": (
                        "Run a halo effect analysis for my store (Mosman) over the last 30 days. "
                        "Which 10 products have the highest basket value multiplier with at least "
                        "20 baskets? I want to know the average basket value when each product "
                        "is present vs the store average. Show the value uplift in dollars."
                    ),
                    "explanation": (
                        "This template uses the Halo Effect analysis. Products with high "
                        "multipliers attract customers who spend more overall — these are "
                        "ideal for prominent placement."
                    ),
                },
            ],
        }),
    },
    # ===== D1: HFM Data Overview =====
    {
        "module_code": "D1",
        "lesson_number": 1,
        "title": "The Harris Farm Data Landscape",
        "content_type": "theory",
        "duration_minutes": 15,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "Where Our Data Lives",
                    "body": (
                        "Harris Farm Markets collects data across every part of the business. "
                        "Understanding what's available helps you ask better questions.\n\n"
                        "**Key Data Sources:**\n\n"
                        "| Source | What It Contains | Scale |\n"
                        "|--------|-----------------|-------|\n"
                        "| POS Transactions | Every item sold: PLU, qty, price, store, time | 383.6M rows, 3 fiscal years |\n"
                        "| Product Hierarchy | Dept > Major Group > Minor Group > HFM Item > SKU | 72,911 products |\n"
                        "| Fiscal Calendar | 5-4-4 retail weeks, periods, quarters, years | Mon-Sun weeks |\n"
                        "| Sales by Store | Revenue, units, GP by department and product | Weekly |\n"
                        "| Customer Analytics | Customer counts, channel mix, demographics | Weekly |\n"
                        "| Market Share | Postcode-level penetration, share vs competitors | Monthly |\n"
                        "| Fresh Buying | Purchase orders, supplier data, cost prices | Daily |\n"
                        "| Transport | Delivery routes, costs, fleet utilisation | Daily |\n"
                        "| Profitability | Margins, shrinkage, department P&L | Weekly |\n\n"
                        "**The Hub dashboards** give you visual access to this data. "
                        "**AI queries** let you ask questions in plain English. "
                        "**Intelligence reports** are generated automatically by AI agents "
                        "scanning 383.6M POS transactions for actionable insights.\n\n"
                        "**Key dimensions:**\n"
                        "- **34 stores** across NSW and QLD\n"
                        "- **9 departments** with 72,911 products across 5 hierarchy levels\n"
                        "- **5-4-4 fiscal calendar** (weeks run Monday-Sunday, 13-week quarters)\n"
                        "- **11 intelligence analysis types** run by AI agents against live transaction data"
                    ),
                },
            ],
        }),
    },
    # ===== D2: Querying & Analysis =====
    {
        "module_code": "D2",
        "lesson_number": 1,
        "title": "Asking AI About Your Data",
        "content_type": "theory",
        "duration_minutes": 15,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "From Question to Insight",
                    "body": (
                        "You don't need to know SQL or coding to analyse Harris Farm data. "
                        "The Hub's AI can translate your plain English questions into data queries.\n\n"
                        "**How it works:**\n"
                        "1. You ask a question in natural language\n"
                        "2. AI translates it into a data query\n"
                        "3. The query runs against our databases (383.6M POS transactions)\n"
                        "4. Results come back in a readable format\n\n"
                        "**Good data questions have:**\n"
                        "- A specific metric (sales, wastage, customer count, margin)\n"
                        "- A scope (which stores, which products, which period)\n"
                        "- A comparison (vs last week, vs other stores, vs budget)\n"
                        "- An output format (table, top 5, summary)"
                    ),
                },
                {
                    "type": "example",
                    "title": "Data Query Examples",
                    "bad": "How are sales going?",
                    "good": (
                        "Compare weekly fresh produce sales for Bondi vs Mosman "
                        "over the last 4 weeks. Show each week's revenue, units sold, "
                        "and gross profit percentage. Highlight any week where either "
                        "store dropped more than 10% vs the prior week."
                    ),
                    "explanation": (
                        "The good query specifies: metric (sales, units, GP%), scope "
                        "(2 stores, fresh produce, 4 weeks), comparison (store vs store, "
                        "week vs prior week), and a specific threshold (10% drop)."
                    ),
                },
            ],
        }),
    },
    {
        "module_code": "D2",
        "lesson_number": 2,
        "title": "Using the Intelligence System",
        "content_type": "theory",
        "duration_minutes": 20,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "AI Agents That Analyse for You",
                    "body": (
                        "The Hub has 11 AI agents that automatically scan 383.6M POS transactions "
                        "to find actionable insights. You don't need to write queries — the agents "
                        "know what to look for.\n\n"
                        "**The 11 Intelligence Analysis Types:**\n\n"
                        "| Analysis | What It Finds | Who It Helps |\n"
                        "|----------|--------------|-------------|\n"
                        "| Basket Analysis | Products frequently bought together | Merchandising, Store Layout |\n"
                        "| Stockout Detection | Products with zero-sale days | Store Managers, Buyers |\n"
                        "| Intraday Stockout | Products that stop selling mid-day | Store Managers, Replenishment |\n"
                        "| Price Dispersion | Inconsistent pricing across stores | Buyers, Finance |\n"
                        "| Demand Pattern | Peak and trough trading periods | Roster Planning, Operations |\n"
                        "| Slow Movers | Underperforming products for range review | Buyers, Category Managers |\n"
                        "| Halo Effect | Products that grow customer basket value | Merchandising, Store Managers |\n"
                        "| Specials Uplift | Demand multiplier when products go on special | Buyers, Promotions |\n"
                        "| Margin Erosion | Products with GP% below department average | Buyers, Finance |\n"
                        "| Customer Segmentation | Loyalty customer RFM segments (Champion, At Risk, etc.) | Marketing, Store Managers |\n"
                        "| Store Benchmark | All-store KPI ranking with percentiles | Area Managers, Exec Team |\n\n"
                        "**How to request an analysis:**\n"
                        "1. Go to the Intelligence Dashboard\n"
                        "2. Describe what you want in plain English (e.g., 'which products grow baskets at Mosman?')\n"
                        "3. The system routes your question to the right agent\n"
                        "4. A proposal is created for approval\n"
                        "5. Once approved, the agent runs the analysis against real data\n"
                        "6. Results appear as Board-ready intelligence reports\n\n"
                        "**Natural language examples:**\n"
                        "- 'What products run out during the day at Bondi?' → Intraday Stockout\n"
                        "- 'Which items drive bigger baskets?' → Halo Effect\n"
                        "- 'How much extra should we order when avocados go on special?' → Specials Uplift\n"
                        "- 'Show me cross-sell opportunities in dairy' → Basket Analysis\n"
                        "- 'Which products have worst margins?' → Margin Erosion\n"
                        "- 'Who are our best customers at Mosman?' → Customer Segmentation\n"
                        "- 'Rank all stores by performance' → Store Benchmark"
                    ),
                },
                {
                    "type": "exercise",
                    "title": "Route the Right Analysis",
                    "scenario": (
                        "Match each business question to the correct analysis type:\n\n"
                        "1. 'Mangoes are going on special next week — how many should each store order?'\n"
                        "2. 'Customers who buy sourdough bread — what else do they buy?'\n"
                        "3. 'Are we selling Wagyu steaks at different prices in different stores?'\n"
                        "4. 'Which products should we put at the front of store to increase spend?'"
                    ),
                    "hints": [
                        "Q1 is about forecasting demand during a price drop",
                        "Q2 is about products purchased together",
                        "Q3 is about price consistency across stores",
                        "Q4 is about products that lift overall basket value",
                    ],
                    "criteria": [
                        "Q1 = Specials Uplift (forecast order quantities for price drops)",
                        "Q2 = Basket Analysis (cross-sell / market basket)",
                        "Q3 = Price Dispersion (pricing inconsistency)",
                        "Q4 = Halo Effect (products that grow basket value)",
                    ],
                },
            ],
        }),
    },
    # ===== D3: Interpreting Results =====
    {
        "module_code": "D3",
        "lesson_number": 1,
        "title": "Reading Dashboards with Confidence",
        "content_type": "theory",
        "duration_minutes": 15,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "What the Numbers Actually Mean",
                    "body": (
                        "Data is only useful if you can interpret it correctly. "
                        "Here are the key metrics you'll see in Harris Farm dashboards "
                        "and what they actually tell you:\n\n"
                        "**Revenue vs GP (Gross Profit):**\n"
                        "- Revenue = total sales value\n"
                        "- GP = revenue minus cost of goods\n"
                        "- GP% = how much profit per dollar of sales\n"
                        "- High revenue + low GP% = selling a lot but not making money\n\n"
                        "**Shrinkage:**\n"
                        "- The value of product lost (waste, theft, damage, write-offs)\n"
                        "- Measured as % of sales — lower is better\n"
                        "- Fresh departments typically 3-8%, grocery under 2%\n\n"
                        "**Period-over-Period (PoP):**\n"
                        "- This week vs last week (WoW)\n"
                        "- This period vs same period last year (YoY)\n"
                        "- Always check if changes are seasonal before raising alarms\n\n"
                        "**Customer Metrics:**\n"
                        "- Basket size = average spend per transaction\n"
                        "- Frequency = how often customers return\n"
                        "- Penetration = % of postcodes shopping with us"
                    ),
                },
            ],
        }),
    },
    {
        "module_code": "D3",
        "lesson_number": 2,
        "title": "Reading Intelligence Reports",
        "content_type": "theory",
        "duration_minutes": 20,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "Understanding AI-Generated Intelligence",
                    "body": (
                        "Intelligence reports are generated by AI agents scanning 383.6M POS "
                        "transactions. Every report follows a standard structure and is scored "
                        "on a presentation rubric (Board-ready / Exec-ready / Draft).\n\n"
                        "**Every intelligence report contains:**\n"
                        "- **Executive Summary** — Key finding in one paragraph\n"
                        "- **Evidence Table** — Data backing the finding (products, stores, numbers)\n"
                        "- **Financial Impact** — Estimated dollar value of the opportunity\n"
                        "- **Recommendations** — Specific actions ranked by priority\n"
                        "- **Methodology** — How the analysis was done\n"
                        "- **Confidence Level** — How reliable the finding is (0-1.0)\n\n"
                        "**How to read key report types:**\n\n"
                        "**Halo Effect Report:**\n"
                        "- 'Value Multiplier' > 1.0 means the product lifts basket value\n"
                        "- A multiplier of 2.5x means baskets with that product are 2.5x larger\n"
                        "- 'Value Uplift' is the dollar amount added per basket\n"
                        "- Use this to decide which products to feature at store entrance\n\n"
                        "**Specials Uplift Report:**\n"
                        "- 'Demand Multiplier' shows how much more you sell on special\n"
                        "- A multiplier of 3.2x means volume triples during a price drop\n"
                        "- 'Weekly Forecast' tells buyers how many units to order\n"
                        "- 'Discount %' shows the typical price reduction that triggers uplift\n\n"
                        "**Stockout Report:**\n"
                        "- 'Consecutive Zero Days' = how many days a product had no sales\n"
                        "- 'Expected Daily' = what the product normally sells\n"
                        "- 'Revenue at Risk' = money lost per day the product is unavailable\n\n"
                        "**Basket Analysis Report:**\n"
                        "- 'Lift Score' > 1.0 means products are bought together more than chance\n"
                        "- 'Support' = how often the pair appears in all baskets\n"
                        "- Use this for cross-merchandising and bundle promotions\n\n"
                        "**Margin Erosion Report:**\n"
                        "- 'GP%' = gross profit as percentage of revenue\n"
                        "- 'Dept Avg GP%' = the benchmark for that department\n"
                        "- 'Gap' = how far below the department average this product sits\n"
                        "- Products with large gaps need cost renegotiation or markdown review\n\n"
                        "**Customer Segmentation Report:**\n"
                        "- 'Champion' = high frequency + high spend (your best customers)\n"
                        "- 'At Risk' = used to shop often but haven't visited recently\n"
                        "- 'Avg Basket' = what each segment spends per visit\n"
                        "- At Risk segment is your biggest retention opportunity\n\n"
                        "**Store Benchmark Report:**\n"
                        "- Each store ranked on revenue, basket value, items/basket, GP%\n"
                        "- 'Percentile' shows where a store sits vs the network (100% = best)\n"
                        "- Bottom-quartile stores are candidates for best-practice sharing"
                    ),
                },
                {
                    "type": "exercise",
                    "title": "Interpret a Halo Report",
                    "scenario": (
                        "A Halo Effect report shows these results for Mosman store:\n\n"
                        "| Product | Baskets | Avg Basket | Store Avg | Multiplier |\n"
                        "|---------|---------|-----------|-----------|------------|\n"
                        "| Lescure Butter | 245 | $128.50 | $24.80 | 5.18x |\n"
                        "| Organic Salmon | 189 | $95.20 | $24.80 | 3.84x |\n"
                        "| Truffle Oil | 67 | $142.00 | $24.80 | 5.73x |\n\n"
                        "Which product would you recommend featuring at the store entrance? "
                        "Consider both the multiplier AND the number of baskets."
                    ),
                    "hints": [
                        "High multiplier + low baskets = niche product (Truffle Oil)",
                        "High multiplier + high baskets = reliable halo product (Lescure Butter)",
                        "The best halo product combines both high multiplier and high volume",
                    ],
                    "criteria": [
                        "Lescure Butter is the best choice: highest basket count (245) with strong multiplier (5.18x)",
                        "Truffle Oil has a higher multiplier but too few baskets (67) to drive meaningful store impact",
                        "The recommendation considers both uplift potential and volume",
                    ],
                },
            ],
        }),
    },
    # ===== D4: Custom Analytics =====
    {
        "module_code": "D4",
        "lesson_number": 1,
        "title": "Building Your Own Reports",
        "content_type": "theory",
        "duration_minutes": 20,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "From Ad-Hoc to Recurring",
                    "body": (
                        "Once you're comfortable querying data, the next step is building "
                        "recurring reports that answer the same questions every week — "
                        "automatically.\n\n"
                        "**Steps to build a custom report:**\n"
                        "1. Identify the question your team asks repeatedly\n"
                        "2. Define the metrics, scope, and format\n"
                        "3. Create a prompt template in the Prompt Builder\n"
                        "4. Test it with this week's data\n"
                        "5. Save it for weekly reuse\n\n"
                        "**Example recurring reports by department:**\n"
                        "- **Store Manager**: Weekly department scorecard (sales, waste, labour)\n"
                        "- **Buyer**: Supplier fill rate and price variance tracker\n"
                        "- **Finance**: Store P&L variance to budget\n"
                        "- **Online**: Pick accuracy and order fulfilment report"
                    ),
                },
            ],
        }),
    },
    # ===== K1: Company Foundation =====
    {
        "module_code": "K1",
        "lesson_number": 1,
        "title": "The Harris Farm Story",
        "content_type": "theory",
        "duration_minutes": 10,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "From Family Farm to 34 Stores",
                    "body": (
                        "Harris Farm Markets was founded in 1971 by the Harris family, "
                        "starting with a single fruit stand in Villawood, Sydney. Today, "
                        "we operate 34 stores across NSW and QLD, employing over 3,000 staff.\n\n"
                        "**Our Values:**\n"
                        "- Fresh food obsession — premium quality, locally sourced where possible\n"
                        "- Community connection — each store reflects its neighbourhood\n"
                        "- Sustainability — B-Corp certified, committed to reducing waste\n"
                        "- Family culture — family-owned, treating staff as family\n\n"
                        "**B-Corp Certification:**\n"
                        "Harris Farm is a certified B Corporation, meeting rigorous standards "
                        "of social and environmental performance. This means every business "
                        "decision considers impact on workers, community, and the environment.\n\n"
                        "**Strategic Direction:**\n"
                        "- Expanding into new communities across NSW and QLD\n"
                        "- Investing in AI and data to improve operations\n"
                        "- Strengthening online ordering and delivery\n"
                        "- Deepening relationships with local producers"
                    ),
                },
            ],
        }),
    },
    # ===== K2: Policies & Procedures =====
    {
        "module_code": "K2",
        "lesson_number": 1,
        "title": "Key Workplace Policies",
        "content_type": "theory",
        "duration_minutes": 15,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "Policies That Apply to Everyone",
                    "body": (
                        "All Harris Farm team members should be familiar with these core policies. "
                        "Full details are available in the Knowledge Base (ask the Hub Assistant).\n\n"
                        "**Food Safety:**\n"
                        "- Temperature checks on all cold chain products\n"
                        "- Date coding and rotation (FIFO)\n"
                        "- Hygiene and handwashing standards\n"
                        "- Allergen management\n\n"
                        "**Workplace Health & Safety:**\n"
                        "- Report all incidents and near-misses immediately\n"
                        "- Manual handling training required for all floor staff\n"
                        "- PPE requirements by department\n"
                        "- Emergency procedures and evacuation plans\n\n"
                        "**Code of Conduct:**\n"
                        "- Respectful treatment of all colleagues and customers\n"
                        "- Responsible use of company resources and technology\n"
                        "- Confidentiality of business information\n"
                        "- Social media guidelines\n\n"
                        "For detailed policy documents, use the Hub Assistant to search "
                        "the Knowledge Base."
                    ),
                },
            ],
        }),
    },
    # ===== K3: Employment Information =====
    {
        "module_code": "K3",
        "lesson_number": 1,
        "title": "Your Employment at Harris Farm",
        "content_type": "theory",
        "duration_minutes": 10,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "Pay, Leave, and Career Development",
                    "body": (
                        "**Pay & Awards:**\n"
                        "- Harris Farm follows the General Retail Industry Award\n"
                        "- Pay classes: Casual, Permanent Full-Time, Permanent Part-Time\n"
                        "- Penalty rates apply for weekends, public holidays, and late shifts\n"
                        "- Pay is processed fortnightly through Dayforce\n\n"
                        "**Leave Entitlements (Permanent Staff):**\n"
                        "- Annual leave: 4 weeks per year\n"
                        "- Personal/sick leave: 10 days per year\n"
                        "- Long service leave: after 10 years continuous service\n"
                        "- Parental leave: as per NES (National Employment Standards)\n\n"
                        "**Career Development:**\n"
                        "- Shop Assistant → Section Lead → Supervisor → Department Head\n"
                        "- Store pathway: 2IC → Trainee Store Manager → Store Manager → Senior Store Manager → Area Manager\n"
                        "- Support Office roles available for experienced retail staff\n"
                        "- Internal transfers between stores and departments supported\n\n"
                        "For specific questions about your pay or leave, ask the Hub Assistant."
                    ),
                },
            ],
        }),
    },
    # ===== K4: Operational Excellence =====
    {
        "module_code": "K4",
        "lesson_number": 1,
        "title": "Golden Rules by Department",
        "content_type": "theory",
        "duration_minutes": 15,
        "content": json.dumps({
            "sections": [
                {
                    "type": "theory",
                    "title": "Standards That Define Harris Farm Quality",
                    "body": (
                        "Each department has golden rules that ensure we deliver the Harris Farm "
                        "experience our customers expect.\n\n"
                        "**Fruit & Vegetables:**\n"
                        "- Display must be full, fresh, and vibrant by 7:30am\n"
                        "- Check and remove damaged items every 2 hours\n"
                        "- Seasonal produce featured prominently\n"
                        "- Local grower signage visible\n\n"
                        "**Proteins (Butcher):**\n"
                        "- Cabinet temperature checked and logged 3x daily\n"
                        "- All meat dated, labelled, and rotated\n"
                        "- Customer orders prepared within 2 minutes\n\n"
                        "**Online Orders:**\n"
                        "- Pick accuracy target: 98%+\n"
                        "- Substitutions require customer approval\n"
                        "- Cold chain maintained from pick to pack\n"
                        "- Order ready within 15 minutes of scheduled time\n\n"
                        "**Customer Service:**\n"
                        "- Greet every customer within 3 metres\n"
                        "- If you don't know, find someone who does\n"
                        "- Handle complaints with empathy first, solution second\n"
                        "- The Imperfect Picks section reduces waste and offers value"
                    ),
                },
            ],
        }),
    },
]


# ---------------------------------------------------------------------------
# ROLE-MODULE PRIORITY MAPPINGS
# ---------------------------------------------------------------------------

# Maps (function_pattern, department_pattern) → {essential, recommended, optional}
# Patterns use substring matching — "Buying" matches "Buying Team Fresh", etc.

ROLE_MAPPINGS = [
    {
        "function": "Retail",
        "department_pattern": "Store Management",
        "essential": ["L1", "K1", "K4"],
        "recommended": ["L2", "D1", "K2", "K3"],
        "optional": ["L3", "L4", "D2", "D3", "D4"],
    },
    {
        "function": "Retail",
        "department_pattern": "Online",
        "essential": ["L1", "K1", "K4"],
        "recommended": ["L2", "D1", "D2", "K2"],
        "optional": ["L3", "L4", "D3", "D4", "K3"],
    },
    {
        "function": "Retail",
        "department_pattern": None,  # Default retail
        "essential": ["L1", "K1"],
        "recommended": ["K2", "K3", "K4"],
        "optional": ["L2", "L3", "L4", "D1", "D2", "D3", "D4"],
    },
    {
        "function": "Support Office",
        "department_pattern": "IT",
        "essential": ["L1", "D1", "D2"],
        "recommended": ["L2", "L3", "D3", "D4"],
        "optional": ["L4", "K1", "K2", "K3", "K4"],
    },
    {
        "function": "Support Office",
        "department_pattern": "Finance",
        "essential": ["L1", "D1", "D2", "D3"],
        "recommended": ["L2", "D4", "K1"],
        "optional": ["L3", "L4", "K2", "K3", "K4"],
    },
    {
        "function": "Support Office",
        "department_pattern": "Buying",
        "essential": ["L1", "D1", "D2"],
        "recommended": ["L2", "L4", "D3", "K4"],
        "optional": ["L3", "D4", "K1", "K2", "K3"],
    },
    {
        "function": "Support Office",
        "department_pattern": "Marketing",
        "essential": ["L1", "L4", "D1"],
        "recommended": ["L2", "D2", "D3", "K1"],
        "optional": ["L3", "D4", "K2", "K3", "K4"],
    },
    {
        "function": "Support Office",
        "department_pattern": "People and Culture",
        "essential": ["L1", "K1", "K2", "K3"],
        "recommended": ["L2", "D1", "K4"],
        "optional": ["L3", "L4", "D2", "D3", "D4"],
    },
    {
        "function": None,  # Default for all others
        "department_pattern": None,
        "essential": ["L1", "K1"],
        "recommended": ["L2", "D1", "K2"],
        "optional": ["L3", "L4", "D2", "D3", "D4", "K3", "K4"],
    },
]


def get_role_priorities(function: str, department: str) -> dict:
    """Return module priorities for a given role.

    Returns dict with keys: essential, recommended, optional (each a list of module codes).
    Uses pattern matching — most specific match wins.
    """
    best_match = None
    best_specificity = -1

    for mapping in ROLE_MAPPINGS:
        specificity = 0
        if mapping["function"] is not None:
            if mapping["function"] != function:
                continue
            specificity += 1
        if mapping["department_pattern"] is not None:
            if mapping["department_pattern"] not in department:
                continue
            specificity += 2

        if specificity > best_specificity:
            best_specificity = specificity
            best_match = mapping

    if best_match is None:
        # Fallback: last entry is the default
        best_match = ROLE_MAPPINGS[-1]

    return {
        "essential": best_match["essential"],
        "recommended": best_match["recommended"],
        "optional": best_match["optional"],
    }


# ---------------------------------------------------------------------------
# RUBRIC EVALUATOR SYSTEM PROMPT (for Practice Lab)
# ---------------------------------------------------------------------------

RUBRIC_EVALUATOR_PROMPT = """You are a prompt quality evaluator for Harris Farm Markets staff. \
Your job is to score a prompt against 5 criteria using a rubric.

THE PROMPT TO EVALUATE:
{user_prompt}

Score the prompt against these 5 criteria, each scored 1-5:

1. REQUEST CLARITY: Is the request clear and unambiguous?
   1 = Vague, could mean anything
   3 = Mostly clear but some ambiguity
   5 = Crystal clear, specific, and unambiguous

2. CONTEXT PROVISION: Does it include relevant Harris Farm context?
   1 = No context at all
   3 = Some context but generic
   5 = Rich with Harris Farm specifics (stores, departments, products)

3. DATA SPECIFICATION: Does it specify what data or information to use?
   1 = No data mentioned
   3 = General data reference
   5 = Exact data sources, metrics, and time periods named

4. OUTPUT FORMAT: Does it define how the answer should be structured?
   1 = No format specified
   3 = Basic format request (e.g. "list")
   5 = Precise format with structure, length, and style defined

5. ACTIONABILITY: Will the result lead to concrete actions?
   1 = Purely theoretical, no practical use
   3 = Some actionable elements
   5 = Every point directly actionable in the Harris Farm context

Respond in EXACTLY this JSON format:
{{
  "scores": {{
    "request_clarity": <1-5>,
    "context_provision": <1-5>,
    "data_specification": <1-5>,
    "output_format": <1-5>,
    "actionability": <1-5>
  }},
  "total": <sum out of 25>,
  "level": "<Needs Work|Getting There|Good|Excellent>",
  "feedback": "<2-3 sentences: what they did well, what to improve>",
  "improved_prompt": "<rewritten prompt scoring 20+ on the rubric>"
}}

Level thresholds: 0-10 = Needs Work, 11-15 = Getting There, 16-20 = Good, 21-25 = Excellent

Be encouraging but honest. These are retail workers learning AI skills, not developers."""


# ---------------------------------------------------------------------------
# PILLAR METADATA (for display)
# ---------------------------------------------------------------------------

PILLARS = {
    "core_ai": {
        "name": "Core AI Skills",
        "icon": "🎯",
        "color": "#2563eb",
        "description": "Master prompting techniques from basics to advanced",
    },
    "data": {
        "name": "Applied Data Skills",
        "icon": "📊",
        "color": "#059669",
        "description": "Query, analyse, and interpret Harris Farm data",
    },
    "knowledge": {
        "name": "Harris Farm Knowledge",
        "icon": "🏪",
        "color": "#d97706",
        "description": "Company policies, procedures, and operational standards",
    },
}


# ---------------------------------------------------------------------------
# DIFFICULTY METADATA
# ---------------------------------------------------------------------------

DIFFICULTY_META = {
    "beginner": {"label": "Beginner", "color": "#22c55e", "icon": "🌱"},
    "intermediate": {"label": "Intermediate", "color": "#f59e0b", "icon": "📈"},
    "advanced": {"label": "Advanced", "color": "#ef4444", "icon": "🎓"},
}
