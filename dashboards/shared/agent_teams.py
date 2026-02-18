"""
Harris Farm Hub -- Agent Competition System Constants
Defines 5 competing agent teams, 41 department analyst agents,
5-tier evaluation rubric (130 points max), and pre-seeded demo data.
"""

# ---------------------------------------------------------------------------
# BUSINESS UNITS (8 groupings of HFM departments)
# ---------------------------------------------------------------------------

BUSINESS_UNITS = [
    {"id": "fresh_produce", "name": "Fresh Produce", "icon": "\U0001f34e",
     "departments": ["Fruit and Vegetables", "Flowers", "Fresh Juice"]},
    {"id": "proteins", "name": "Proteins", "icon": "\U0001f969",
     "departments": ["Butcher Proteins", "Cheese Cutting", "Seafood"]},
    {"id": "bakery_perishable", "name": "Bakery & Perishable", "icon": "\U0001f35e",
     "departments": ["Bakery", "Perishable", "Yoghurt Production"]},
    {"id": "grocery_liquor", "name": "Grocery & Liquor", "icon": "\U0001f6d2",
     "departments": ["Grocery", "Liquor"]},
    {"id": "buying_supply", "name": "Buying & Supply Chain", "icon": "\U0001f69a",
     "departments": ["Buying Team Fresh", "Buying Team Gourmet",
                      "Buying Team Proteins", "Logistics"]},
    {"id": "store_ops", "name": "Store Operations", "icon": "\U0001f3ea",
     "departments": ["Store Management", "Service", "Online", "Back of House"]},
    {"id": "support_office", "name": "Support Office", "icon": "\U0001f3e2",
     "departments": ["Finance", "IT", "Marketing", "People & Culture",
                      "Training", "Property", "Safety & Compliance"]},
    {"id": "wholesale", "name": "Wholesale", "icon": "\U0001f4e6",
     "departments": ["Wholesale Business"]},
]

# ---------------------------------------------------------------------------
# 5 COMPETING AGENT TEAMS
# ---------------------------------------------------------------------------

AGENT_TEAMS = [
    {
        "id": "alpha",
        "name": "Team Alpha",
        "firm": "AWS / Amazon",
        "color": "#FF9900",
        "icon": "\u0391",
        "philosophy": "Customer obsession, working backwards from outcomes, "
                      "data-driven frugality, bias for action",
        "strengths": ["Cloud infrastructure & scalability",
                      "Customer analytics at scale",
                      "Operational automation"],
        "approach": "Start with the customer and work backwards. Build for "
                    "scale. Measure everything.",
        "motto": "Customer obsession, not competitor obsession",
    },
    {
        "id": "beta",
        "name": "Team Beta",
        "firm": "McKinsey & Company",
        "color": "#003C71",
        "icon": "\u0392",
        "philosophy": "Structured problem-solving, 80/20 analysis, MECE "
                      "frameworks, hypothesis-driven thinking",
        "strengths": ["Strategic frameworks & market sizing",
                      "Executive communication",
                      "Organisational design"],
        "approach": "Hypothesis-driven. Disaggregate the problem. Prioritise "
                    "by impact. Communicate with clarity.",
        "motto": "Everything is solvable with the right framework",
    },
    {
        "id": "gamma",
        "name": "Team Gamma",
        "firm": "Anthropic",
        "color": "#D4A574",
        "icon": "\u0393",
        "philosophy": "Careful reasoning, transparency about uncertainty, "
                      "human-AI alignment, safety-first design",
        "strengths": ["AI governance & safety",
                      "Knowledge system architecture",
                      "Prompt engineering excellence"],
        "approach": "Think carefully. Be transparent about uncertainty. Align "
                    "with human values. Build trust through reliability.",
        "motto": "AI that is helpful, harmless, and honest",
    },
    {
        "id": "delta",
        "name": "Team Delta",
        "firm": "Bain & Company",
        "color": "#CC0000",
        "icon": "\u0394",
        "philosophy": "Results delivery, Full Potential methodology, "
                      "Founder's Mentality, speed to value",
        "strengths": ["Performance improvement & cost optimisation",
                      "Operational excellence",
                      "Rapid execution & measurement"],
        "approach": "Focus on results. What is the full potential? Execute "
                    "with speed. Measure relentlessly.",
        "motto": "True North: Results, not just recommendations",
    },
    {
        "id": "epsilon",
        "name": "Team Epsilon",
        "firm": "Google / DeepMind",
        "color": "#4285F4",
        "icon": "\u0395",
        "philosophy": "Organise information, 10x thinking, rapid "
                      "experimentation, moonshot + pragmatism",
        "strengths": ["Machine learning & search",
                      "Data infrastructure at scale",
                      "User experience research"],
        "approach": "Think 10x, not 10%. Use data at scale. Rapid "
                    "experimentation. Ship and iterate.",
        "motto": "Organise the world's information and make it universally useful",
    },
]

# ---------------------------------------------------------------------------
# 41 DEPARTMENT ANALYST AGENTS
# ---------------------------------------------------------------------------

DEPARTMENT_AGENTS = [
    # ---- FRESH PRODUCE (5 agents) ----
    {
        "id": "fp_demand", "name": "Fresh Demand Analyst",
        "team_id": "alpha", "department": "Fruit and Vegetables",
        "business_unit": "fresh_produce",
        "role": "Demand Forecasting & Order Optimisation",
        "capabilities": [
            "Daily demand forecasting by store and product",
            "Weather-adjusted order recommendations",
            "Shrinkage pattern detection and reduction",
            "Seasonal product lifecycle modelling",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy",
                         "Fiscal Calendar"],
        "status": "active",
    },
    {
        "id": "fp_pricing", "name": "Produce Pricing Strategist",
        "team_id": "beta", "department": "Fruit and Vegetables",
        "business_unit": "fresh_produce",
        "role": "Dynamic Pricing & Markdown Optimisation",
        "capabilities": [
            "Price elasticity modelling by category",
            "Competitor price monitoring alerts",
            "Markdown timing optimisation per SKU",
            "Margin-volume trade-off analysis",
        ],
        "data_sources": ["Transaction Data", "Weekly Aggregated"],
        "status": "active",
    },
    {
        "id": "fp_waste", "name": "Waste Reduction Specialist",
        "team_id": "gamma", "department": "Fruit and Vegetables",
        "business_unit": "fresh_produce",
        "role": "Waste Analytics & Sustainability",
        "capabilities": [
            "Shrinkage root cause analysis by store",
            "Shelf-life optimisation recommendations",
            "Donation vs markdown decision support",
            "Sustainability impact measurement",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy"],
        "status": "active",
    },
    {
        "id": "fp_quality", "name": "Quality Monitor",
        "team_id": "delta", "department": "Fruit and Vegetables",
        "business_unit": "fresh_produce",
        "role": "Quality Assurance & Supplier Compliance",
        "capabilities": [
            "Supplier quality score tracking",
            "Returns and complaint pattern analysis",
            "Temperature chain monitoring alerts",
            "Freshness benchmark comparisons",
        ],
        "data_sources": ["Transaction Data"],
        "status": "active",
    },
    {
        "id": "fp_seasonal", "name": "Seasonal Planner",
        "team_id": "epsilon", "department": "Flowers",
        "business_unit": "fresh_produce",
        "role": "Seasonal Range & Event Planning",
        "capabilities": [
            "Event-driven demand modelling (Easter, Mothers Day)",
            "Seasonal range planning with 12-week horizon",
            "New product introduction forecasting",
            "Store-specific assortment recommendations",
        ],
        "data_sources": ["Transaction Data", "Fiscal Calendar"],
        "status": "active",
    },
    # ---- PROTEINS (4 agents) ----
    {
        "id": "pr_demand", "name": "Protein Demand Analyst",
        "team_id": "alpha", "department": "Butcher Proteins",
        "business_unit": "proteins",
        "role": "Protein Category Demand Intelligence",
        "capabilities": [
            "Cut-level demand forecasting",
            "BBQ season uplift modelling",
            "Cross-store inventory balancing",
            "Promotional lift prediction",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy"],
        "status": "active",
    },
    {
        "id": "pr_pricing", "name": "Protein Pricing Analyst",
        "team_id": "beta", "department": "Butcher Proteins",
        "business_unit": "proteins",
        "role": "Meat & Seafood Pricing Strategy",
        "capabilities": [
            "Cost-plus margin optimisation",
            "Wholesale vs retail price arbitrage",
            "Weight-price consistency monitoring",
            "Premium positioning analysis",
        ],
        "data_sources": ["Transaction Data", "Weekly Aggregated"],
        "status": "active",
    },
    {
        "id": "pr_supplier", "name": "Protein Supplier Analyst",
        "team_id": "delta", "department": "Butcher Proteins",
        "business_unit": "proteins",
        "role": "Supplier Performance & Risk Management",
        "capabilities": [
            "Supplier delivery performance scoring",
            "Cost trend analysis and negotiation support",
            "Alternative supplier identification",
            "Supply risk early warning system",
        ],
        "data_sources": ["Transaction Data"],
        "status": "active",
    },
    {
        "id": "pr_margin", "name": "Cheese & Specialty Margin Analyst",
        "team_id": "gamma", "department": "Cheese Cutting",
        "business_unit": "proteins",
        "role": "Specialty Product Margin Optimisation",
        "capabilities": [
            "Specialty cheese margin tracking",
            "Portion size optimisation",
            "Product substitution recommendations",
            "Premium product mix analysis",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy"],
        "status": "active",
    },
    # ---- BAKERY & PERISHABLE (4 agents) ----
    {
        "id": "bk_production", "name": "Bakery Production Planner",
        "team_id": "alpha", "department": "Bakery",
        "business_unit": "bakery_perishable",
        "role": "In-Store Bakery Production Optimisation",
        "capabilities": [
            "Daily bake schedule optimisation by store",
            "Ingredient usage forecasting",
            "Production waste minimisation",
            "Peak trading time preparation planning",
        ],
        "data_sources": ["Transaction Data", "Fiscal Calendar"],
        "status": "active",
    },
    {
        "id": "bk_waste", "name": "Perishable Waste Analyst",
        "team_id": "gamma", "department": "Perishable",
        "business_unit": "bakery_perishable",
        "role": "Perishable Category Waste Reduction",
        "capabilities": [
            "End-of-day markdown optimisation",
            "Product rotation compliance monitoring",
            "Shelf-life-based ordering adjustments",
            "Cross-category waste benchmarking",
        ],
        "data_sources": ["Transaction Data"],
        "status": "active",
    },
    {
        "id": "bk_range", "name": "Range Optimisation Analyst",
        "team_id": "beta", "department": "Bakery",
        "business_unit": "bakery_perishable",
        "role": "Product Range & Innovation",
        "capabilities": [
            "SKU rationalisation analysis",
            "New product performance prediction",
            "Store-size-appropriate ranging",
            "Customer preference trending",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy"],
        "status": "active",
    },
    {
        "id": "bk_freshness", "name": "Freshness Standards Monitor",
        "team_id": "delta", "department": "Yoghurt Production",
        "business_unit": "bakery_perishable",
        "role": "Freshness & Quality Compliance",
        "capabilities": [
            "Production batch quality tracking",
            "Temperature chain monitoring",
            "Freshness score benchmarking",
            "Customer feedback sentiment analysis",
        ],
        "data_sources": ["Transaction Data"],
        "status": "active",
    },
    # ---- GROCERY & LIQUOR (4 agents) ----
    {
        "id": "gl_category", "name": "Category Performance Analyst",
        "team_id": "beta", "department": "Grocery",
        "business_unit": "grocery_liquor",
        "role": "Grocery Category Management Intelligence",
        "capabilities": [
            "Category growth vs decline analysis",
            "Space-to-sales ratio optimisation",
            "Promotional calendar effectiveness",
            "Cross-category basket analysis",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy",
                         "Weekly Aggregated"],
        "status": "active",
    },
    {
        "id": "gl_shelf", "name": "Shelf Space Optimiser",
        "team_id": "epsilon", "department": "Grocery",
        "business_unit": "grocery_liquor",
        "role": "Planogram & Space Allocation",
        "capabilities": [
            "Space-to-sales performance scoring",
            "Adjacency optimisation recommendations",
            "Eye-level placement ROI analysis",
            "Store format-specific planograms",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy"],
        "status": "active",
    },
    {
        "id": "gl_pricing", "name": "Grocery Pricing Analyst",
        "team_id": "delta", "department": "Grocery",
        "business_unit": "grocery_liquor",
        "role": "Competitive Pricing & Margin Management",
        "capabilities": [
            "Competitive price index tracking",
            "Private label vs branded margin analysis",
            "Price perception optimisation",
            "Promotional depth recommendation",
        ],
        "data_sources": ["Transaction Data", "Weekly Aggregated"],
        "status": "active",
    },
    {
        "id": "gl_promo", "name": "Liquor Promotional Analyst",
        "team_id": "alpha", "department": "Liquor",
        "business_unit": "grocery_liquor",
        "role": "Liquor Promotions & Event Planning",
        "capabilities": [
            "Promotional lift and cannibalisation analysis",
            "Seasonal event planning (wine, craft beer)",
            "Supplier-funded promotional ROI",
            "Customer trade-up opportunity mapping",
        ],
        "data_sources": ["Transaction Data", "Fiscal Calendar"],
        "status": "active",
    },
    # ---- BUYING & SUPPLY CHAIN (6 agents) ----
    {
        "id": "bs_supplier", "name": "Supplier Performance Analyst",
        "team_id": "delta", "department": "Buying Team Fresh",
        "business_unit": "buying_supply",
        "role": "Supplier Scorecard & Relationship Management",
        "capabilities": [
            "Supplier delivery performance scoring",
            "Quality compliance tracking",
            "Cost trend forecasting per supplier",
            "Supplier consolidation opportunity analysis",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy"],
        "status": "active",
    },
    {
        "id": "bs_logistics", "name": "Logistics Network Analyst",
        "team_id": "alpha", "department": "Logistics",
        "business_unit": "buying_supply",
        "role": "Transport & Distribution Optimisation",
        "capabilities": [
            "Route optimisation and cost modelling",
            "Delivery frequency vs freshness trade-offs",
            "Warehouse capacity utilisation",
            "Last-mile delivery cost analysis",
        ],
        "data_sources": ["Transaction Data"],
        "status": "active",
    },
    {
        "id": "bs_forecast", "name": "Demand Forecast Analyst",
        "team_id": "epsilon", "department": "Buying Team Fresh",
        "business_unit": "buying_supply",
        "role": "Enterprise Demand Planning",
        "capabilities": [
            "Multi-horizon demand forecasting (daily/weekly/monthly)",
            "Promotional uplift modelling",
            "New store demand estimation",
            "External factor integration (weather, events)",
        ],
        "data_sources": ["Transaction Data", "Fiscal Calendar",
                         "Product Hierarchy"],
        "status": "active",
    },
    {
        "id": "bs_procurement", "name": "Procurement Intelligence Agent",
        "team_id": "beta", "department": "Buying Team Gourmet",
        "business_unit": "buying_supply",
        "role": "Strategic Procurement & Sourcing",
        "capabilities": [
            "Category sourcing strategy development",
            "Import vs local cost-benefit analysis",
            "Supplier negotiation data packages",
            "Tender evaluation support",
        ],
        "data_sources": ["Transaction Data", "Weekly Aggregated"],
        "status": "active",
    },
    {
        "id": "bs_cost", "name": "Cost Control Analyst",
        "team_id": "gamma", "department": "Buying Team Proteins",
        "business_unit": "buying_supply",
        "role": "Cost Management & COGS Tracking",
        "capabilities": [
            "COGS variance analysis by category",
            "Shrinkage cost attribution",
            "Labour cost per unit tracking",
            "Overhead allocation optimisation",
        ],
        "data_sources": ["Transaction Data", "Weekly Aggregated"],
        "status": "active",
    },
    {
        "id": "bs_network", "name": "Supply Network Planner",
        "team_id": "alpha", "department": "Logistics",
        "business_unit": "buying_supply",
        "role": "Distribution Network Design",
        "capabilities": [
            "Store delivery frequency optimisation",
            "Cross-dock vs direct delivery analysis",
            "Seasonal capacity planning",
            "Emergency supply chain response",
        ],
        "data_sources": ["Transaction Data", "Fiscal Calendar"],
        "status": "active",
    },
    # ---- STORE OPERATIONS (7 agents) ----
    {
        "id": "so_performance", "name": "Store Performance Analyst",
        "team_id": "beta", "department": "Store Management",
        "business_unit": "store_ops",
        "role": "Store-Level P&L Intelligence",
        "capabilities": [
            "Store P&L decomposition and benchmarking",
            "Labour productivity analysis",
            "Trading hour optimisation",
            "Store ranking and clustering",
        ],
        "data_sources": ["Transaction Data", "Weekly Aggregated",
                         "Fiscal Calendar"],
        "status": "active",
    },
    {
        "id": "so_cx", "name": "Customer Experience Analyst",
        "team_id": "epsilon", "department": "Service",
        "business_unit": "store_ops",
        "role": "In-Store Customer Journey Intelligence",
        "capabilities": [
            "Peak hour customer flow analysis",
            "Queue time estimation and alerts",
            "Department visit sequence analysis",
            "Customer satisfaction driver identification",
        ],
        "data_sources": ["Transaction Data", "Fiscal Calendar"],
        "status": "active",
    },
    {
        "id": "so_inventory", "name": "Inventory Optimisation Agent",
        "team_id": "alpha", "department": "Back of House",
        "business_unit": "store_ops",
        "role": "Stock Level & Replenishment Intelligence",
        "capabilities": [
            "Optimal stock level calculation by SKU",
            "Out-of-stock prediction and alerting",
            "Overstock identification and markdown triggers",
            "Auto-replenishment parameter tuning",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy"],
        "status": "active",
    },
    {
        "id": "so_merch", "name": "Merchandising Insights Agent",
        "team_id": "delta", "department": "Store Management",
        "business_unit": "store_ops",
        "role": "Visual Merchandising & Display Effectiveness",
        "capabilities": [
            "Endcap and display ROI measurement",
            "Cross-merchandising opportunity identification",
            "Seasonal display planning calendar",
            "Impulse purchase driver analysis",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy"],
        "status": "active",
    },
    {
        "id": "so_staffing", "name": "Workforce Planning Analyst",
        "team_id": "gamma", "department": "Store Management",
        "business_unit": "store_ops",
        "role": "Labour Scheduling & Productivity",
        "capabilities": [
            "Traffic-based labour scheduling",
            "Department-level labour productivity benchmarks",
            "Peak trading roster optimisation",
            "Absenteeism pattern prediction",
        ],
        "data_sources": ["Transaction Data", "Fiscal Calendar"],
        "status": "active",
    },
    {
        "id": "so_basket", "name": "Basket Intelligence Analyst",
        "team_id": "epsilon", "department": "Store Management",
        "business_unit": "store_ops",
        "role": "Basket Composition & Cross-Sell Analysis",
        "capabilities": [
            "Market basket analysis (association rules)",
            "Average basket size optimisation",
            "Cross-category affinity mapping",
            "Customer mission segmentation",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy"],
        "status": "active",
    },
    {
        "id": "so_online", "name": "Online Channel Analyst",
        "team_id": "alpha", "department": "Online",
        "business_unit": "store_ops",
        "role": "E-Commerce & Omnichannel Intelligence",
        "capabilities": [
            "Online vs in-store behaviour comparison",
            "Fulfilment efficiency tracking",
            "Product substitution recommendation engine",
            "Delivery slot demand forecasting",
        ],
        "data_sources": ["Transaction Data"],
        "status": "active",
    },
    # ---- SUPPORT OFFICE (8 agents) ----
    {
        "id": "su_finance", "name": "Financial Planning Analyst",
        "team_id": "beta", "department": "Finance",
        "business_unit": "support_office",
        "role": "Budget & Financial Forecasting",
        "capabilities": [
            "Revenue forecasting by store and department",
            "Budget variance analysis and alerting",
            "Cash flow projection modelling",
            "Capital expenditure ROI tracking",
        ],
        "data_sources": ["Weekly Aggregated", "Fiscal Calendar"],
        "status": "active",
    },
    {
        "id": "su_pnl", "name": "P&L Analysis Agent",
        "team_id": "delta", "department": "Finance",
        "business_unit": "support_office",
        "role": "Profitability Analysis & Reporting",
        "capabilities": [
            "Department-level P&L decomposition",
            "Gross margin trend analysis",
            "Cost centre performance benchmarking",
            "Profitability driver waterfall analysis",
        ],
        "data_sources": ["Weekly Aggregated", "Transaction Data"],
        "status": "active",
    },
    {
        "id": "su_cashflow", "name": "Cash Flow Monitor",
        "team_id": "alpha", "department": "Finance",
        "business_unit": "support_office",
        "role": "Working Capital & Liquidity Management",
        "capabilities": [
            "Daily cash position forecasting",
            "Accounts payable optimisation",
            "Seasonal cash flow pattern analysis",
            "Working capital efficiency metrics",
        ],
        "data_sources": ["Transaction Data", "Fiscal Calendar"],
        "status": "active",
    },
    {
        "id": "su_it", "name": "IT Systems Health Agent",
        "team_id": "gamma", "department": "IT",
        "business_unit": "support_office",
        "role": "Technology Infrastructure Monitoring",
        "capabilities": [
            "POS system uptime monitoring",
            "Integration health dashboard",
            "Data pipeline latency tracking",
            "Security event correlation",
        ],
        "data_sources": ["Hub Metadata"],
        "status": "active",
    },
    {
        "id": "su_marketing", "name": "Marketing Effectiveness Agent",
        "team_id": "epsilon", "department": "Marketing",
        "business_unit": "support_office",
        "role": "Campaign Performance & Brand Intelligence",
        "capabilities": [
            "Campaign ROI measurement by channel",
            "Customer acquisition cost tracking",
            "Brand sentiment analysis",
            "Promotional attribution modelling",
        ],
        "data_sources": ["Transaction Data", "Weekly Aggregated"],
        "status": "active",
    },
    {
        "id": "su_people", "name": "People Analytics Agent",
        "team_id": "beta", "department": "People & Culture",
        "business_unit": "support_office",
        "role": "Workforce Analytics & Engagement",
        "capabilities": [
            "Turnover prediction and retention modelling",
            "Employee engagement driver analysis",
            "Compensation benchmarking",
            "Diversity and inclusion metrics",
        ],
        "data_sources": ["Hub Metadata"],
        "status": "active",
    },
    {
        "id": "su_training", "name": "Training Effectiveness Agent",
        "team_id": "gamma", "department": "Training",
        "business_unit": "support_office",
        "role": "Learning Impact Measurement",
        "capabilities": [
            "Training completion and competency tracking",
            "Learning path effectiveness analysis",
            "Skill gap identification by role",
            "Onboarding time-to-productivity measurement",
        ],
        "data_sources": ["Hub Metadata"],
        "status": "active",
    },
    {
        "id": "su_property", "name": "Property & Expansion Analyst",
        "team_id": "delta", "department": "Property",
        "business_unit": "support_office",
        "role": "Site Analysis & Expansion Intelligence",
        "capabilities": [
            "Demographic analysis for new site selection",
            "Lease cost benchmarking and optimisation",
            "Store format-to-catchment matching",
            "Cannibalisation risk assessment",
        ],
        "data_sources": ["Transaction Data", "Weekly Aggregated"],
        "status": "active",
    },
    # ---- WHOLESALE (3 agents) ----
    {
        "id": "ws_volume", "name": "Wholesale Volume Analyst",
        "team_id": "alpha", "department": "Wholesale Business",
        "business_unit": "wholesale",
        "role": "Wholesale Volume & Revenue Intelligence",
        "capabilities": [
            "Account-level volume forecasting",
            "Seasonal demand pattern identification",
            "Order frequency optimisation",
            "Revenue growth opportunity mapping",
        ],
        "data_sources": ["Transaction Data"],
        "status": "active",
    },
    {
        "id": "ws_pricing", "name": "Wholesale Pricing Analyst",
        "team_id": "beta", "department": "Wholesale Business",
        "business_unit": "wholesale",
        "role": "Wholesale Pricing & Margin Strategy",
        "capabilities": [
            "Tiered pricing optimisation by volume",
            "Margin analysis by customer segment",
            "Competitive wholesale price monitoring",
            "Contract renewal pricing support",
        ],
        "data_sources": ["Transaction Data", "Weekly Aggregated"],
        "status": "active",
    },
    {
        "id": "ws_customer", "name": "Wholesale Customer Analyst",
        "team_id": "epsilon", "department": "Wholesale Business",
        "business_unit": "wholesale",
        "role": "Wholesale Customer Relationship Intelligence",
        "capabilities": [
            "Customer health score tracking",
            "Churn risk prediction and prevention",
            "Cross-sell opportunity identification",
            "Customer profitability ranking",
        ],
        "data_sources": ["Transaction Data"],
        "status": "active",
    },
]


# ---------------------------------------------------------------------------
# 5-TIER EVALUATION RUBRIC (130 points max)
# ---------------------------------------------------------------------------

EVALUATION_TIERS = [
    {
        "id": "cto",
        "name": "CTO Panel",
        "description": "Technical feasibility, data architecture, "
                       "integration complexity, and scalability",
        "max_points": 25,
        "panelists": ["CTO Amazon", "CTO Uber", "CTO Anthropic",
                      "CTO OpenAI", "CTO Canva"],
        "criteria": [
            {"name": "Technical Feasibility", "max": 5,
             "description": "Can this be built with the current stack?"},
            {"name": "Data Availability", "max": 5,
             "description": "Is the required data accessible and clean?"},
            {"name": "Integration Complexity", "max": 5,
             "description": "How well does it fit existing systems?"},
            {"name": "Scalability", "max": 5,
             "description": "Will it scale across all 34 stores?"},
            {"name": "Security & Governance", "max": 5,
             "description": "WATCHDOG compliance and data safety"},
        ],
    },
    {
        "id": "clo",
        "name": "CLO Panel",
        "description": "Learning impact, adoption readiness, and "
                       "organisational capability building",
        "max_points": 25,
        "panelists": ["CLO McKinsey", "CLO Bain", "CLO Kearney",
                      "CLO Google", "CLO Amazon"],
        "criteria": [
            {"name": "Learning Impact", "max": 5,
             "description": "Does this upskill the team?"},
            {"name": "Adoption Readiness", "max": 5,
             "description": "How easy is it for staff to use?"},
            {"name": "Knowledge Transfer", "max": 5,
             "description": "Can insights be shared and taught?"},
            {"name": "Role Alignment", "max": 5,
             "description": "Does it serve existing job roles?"},
            {"name": "Capability Building", "max": 5,
             "description": "Long-term organisational capability?"},
        ],
    },
    {
        "id": "strategic",
        "name": "Strategic Alignment",
        "description": "Business value, competitive advantage, and "
                       "Harris Farm mission fit",
        "max_points": 30,
        "panelists": ["Harris Farm Board"],
        "criteria": [
            {"name": "Revenue Impact", "max": 5,
             "description": "Direct or indirect revenue uplift"},
            {"name": "Cost Reduction", "max": 5,
             "description": "Operational savings potential"},
            {"name": "Customer Experience", "max": 5,
             "description": "Impact on the shopper experience"},
            {"name": "Competitive Advantage", "max": 5,
             "description": "Differentiation from Coles/Woolworths"},
            {"name": "Mission Alignment", "max": 5,
             "description": "Fits Harris Farm's premium fresh positioning"},
            {"name": "Sustainability", "max": 5,
             "description": "Environmental and community impact"},
        ],
    },
    {
        "id": "implementation",
        "name": "Implementation Readiness",
        "description": "Resource requirements, timeline realism, and "
                       "risk assessment",
        "max_points": 25,
        "panelists": ["Implementation Committee"],
        "criteria": [
            {"name": "Resource Efficiency", "max": 5,
             "description": "People, time, and money required"},
            {"name": "Timeline Realism", "max": 5,
             "description": "Can this ship in the stated timeframe?"},
            {"name": "Risk Mitigation", "max": 5,
             "description": "Are risks identified and managed?"},
            {"name": "Dependency Management", "max": 5,
             "description": "External dependencies controlled?"},
            {"name": "Measurement Plan", "max": 5,
             "description": "Clear KPIs and success criteria?"},
        ],
    },
    {
        "id": "presentation",
        "name": "Presentation Rubric",
        "description": "Communication clarity, evidence quality, "
                       "narrative structure, and actionability",
        "max_points": 25,
        "panelists": ["Communication Board"],
        "criteria": [
            {"name": "Clarity", "max": 5,
             "description": "Is the proposal easy to understand?"},
            {"name": "Evidence Quality", "max": 5,
             "description": "Data-backed claims, traceable sources"},
            {"name": "Narrative Structure", "max": 5,
             "description": "Logical flow and compelling story"},
            {"name": "Actionability", "max": 5,
             "description": "Clear next steps and who does what"},
            {"name": "Visual Communication", "max": 5,
             "description": "Charts, tables, and formatting quality"},
        ],
    },
]

# Verify max: 25+25+30+25+25 = 130
EVALUATION_MAX_SCORE = sum(t["max_points"] for t in EVALUATION_TIERS)
IMPLEMENTATION_THRESHOLD = 110  # 85% of 130


# ---------------------------------------------------------------------------
# COMPETITION MECHANICS
# ---------------------------------------------------------------------------

TEAM_POINT_ACTIONS = [
    {"action": "proposal_submitted", "points": 10,
     "label": "Proposal enters evaluation"},
    {"action": "proposal_tier3", "points": 25,
     "label": "Proposal reaches Tier 3 review"},
    {"action": "proposal_implemented", "points": 50,
     "label": "Proposal reaches implementation"},
    {"action": "proposal_impact", "points": 100,
     "label": "Implemented proposal shows measurable impact"},
    {"action": "best_practice", "points": 200,
     "label": "Proposal becomes best practice standard"},
]

MULTIPLIERS = [
    {"code": "first_to_identify", "multiplier": 1.5,
     "label": "First team to identify a critical issue"},
    {"code": "cost_saver", "multiplier": 2.0,
     "label": "Proposal saves significant cost or time"},
    {"code": "competitive_advantage", "multiplier": 3.0,
     "label": "Proposal creates competitive advantage"},
    {"code": "transformational", "multiplier": 5.0,
     "label": "Proposal transforms business capability"},
]

ARENA_ACHIEVEMENTS = [
    {"code": "arena_evaluator", "name": "Arena Evaluator",
     "icon": "\u2696\ufe0f", "description": "Evaluated your first proposal"},
    {"code": "arena_all_tiers", "name": "Full Review",
     "icon": "\U0001f3af", "description": "Completed all 5 tiers on a proposal"},
    {"code": "arena_proposer", "name": "Idea Generator",
     "icon": "\U0001f4a1", "description": "Submitted your first proposal"},
    {"code": "arena_champion", "name": "Arena Champion",
     "icon": "\U0001f3c6", "description": "Proposal scored 110+ and reached implementation"},
]


# ---------------------------------------------------------------------------
# PRE-SEEDED PROPOSALS (10 proposals across all 5 teams)
# ---------------------------------------------------------------------------

SEED_PROPOSALS = [
    {
        "title": "Fresh Produce Dynamic Markdown Engine",
        "description": (
            "Build an automated markdown timing system for F&V that uses "
            "historical sales velocity, shelf-life remaining, and weather "
            "forecasts to recommend optimal markdown percentage and timing "
            "per SKU per store. Analysis of 383M POS transactions shows "
            "consistent patterns where markdowns applied 2 hours earlier "
            "could recover 18% more margin. Targets: reduce fresh produce "
            "waste by 15%, recover $1.2M annually in margin."
        ),
        "team_id": "alpha",
        "agent_id": "fp_demand",
        "department": "Fruit and Vegetables",
        "category": "efficiency",
        "estimated_impact_aud": 1200000,
        "estimated_effort_weeks": 12,
        "complexity": "high",
        "status": "scored",
        "total_score": 108.5,
        "tier_scores": '{"cto": 21, "clo": 18, "strategic": 27, '
                       '"implementation": 20, "presentation": 22.5}',
    },
    {
        "title": "Customer Basket Affinity Model",
        "description": (
            "Deploy association rule mining across 383M POS transactions to "
            "identify high-value product affinities and co-purchase patterns. "
            "Generate store-specific cross-sell recommendations and planogram "
            "adjacency suggestions. Initial analysis shows strong Cheese-Wine "
            "and Bakery-Coffee affinities with 3-5% basket uplift potential."
        ),
        "team_id": "epsilon",
        "agent_id": "so_basket",
        "department": "Store Management",
        "category": "revenue",
        "estimated_impact_aud": 2400000,
        "estimated_effort_weeks": 8,
        "complexity": "medium",
        "status": "implemented",
        "total_score": 118.0,
        "tier_scores": '{"cto": 23, "clo": 22, "strategic": 28, '
                       '"implementation": 23, "presentation": 22}',
    },
    {
        "title": "Strategic Store Clustering for Localised Ranging",
        "description": (
            "Apply K-means clustering using transaction patterns, demographic "
            "data, and basket composition to segment all 34 stores into 5-7 "
            "archetypes. Use clusters to develop tailored product ranges, "
            "pricing strategies, and promotional plans per cluster. McKinsey "
            "MECE framework applied to ensure mutually exclusive segments."
        ),
        "team_id": "beta",
        "agent_id": "so_performance",
        "department": "Store Management",
        "category": "revenue",
        "estimated_impact_aud": 1800000,
        "estimated_effort_weeks": 10,
        "complexity": "high",
        "status": "scored",
        "total_score": 112.0,
        "tier_scores": '{"cto": 22, "clo": 21, "strategic": 26, '
                       '"implementation": 21, "presentation": 22}',
    },
    {
        "title": "WATCHDOG v8: Autonomous Safety Monitoring",
        "description": (
            "Extend the WATCHDOG governance system to include autonomous "
            "continuous monitoring of all 16 dashboards, API endpoints, and "
            "data pipelines. Add anomaly detection for data quality, "
            "performance degradation alerting, and automated recovery "
            "procedures. Aligned with Anthropic's constitutional AI principles."
        ),
        "team_id": "gamma",
        "agent_id": "su_it",
        "department": "IT",
        "category": "innovation",
        "estimated_impact_aud": 500000,
        "estimated_effort_weeks": 6,
        "complexity": "medium",
        "status": "scored",
        "total_score": 115.5,
        "tier_scores": '{"cto": 24, "clo": 20, "strategic": 27, '
                       '"implementation": 22, "presentation": 22.5}',
    },
    {
        "title": "Labour Productivity Optimisation Engine",
        "description": (
            "Build a traffic-aware labour scheduling system that uses hourly "
            "transaction volumes by store to optimise department staffing "
            "levels. Bain Full Potential methodology applied: current labour "
            "hours analysed against revenue per labour hour benchmarks. "
            "Target: 8% improvement in labour productivity = $2.1M savings."
        ),
        "team_id": "delta",
        "agent_id": "so_staffing",
        "department": "Store Management",
        "category": "efficiency",
        "estimated_impact_aud": 2100000,
        "estimated_effort_weeks": 14,
        "complexity": "high",
        "status": "scored",
        "total_score": 105.0,
        "tier_scores": '{"cto": 20, "clo": 19, "strategic": 26, '
                       '"implementation": 18, "presentation": 22}',
    },
    {
        "title": "Intelligent Search & Discovery Platform",
        "description": (
            "Build a Google-style search interface across all Hub "
            "documentation, procedures, audit logs, and data catalog. "
            "Uses FTS5 with BM25 ranking, semantic embedding similarity, "
            "and auto-suggest. 10x improvement in information retrieval "
            "speed for all 211 roles across the organisation."
        ),
        "team_id": "epsilon",
        "agent_id": "su_it",
        "department": "IT",
        "category": "innovation",
        "estimated_impact_aud": 300000,
        "estimated_effort_weeks": 4,
        "complexity": "low",
        "status": "implemented",
        "total_score": 120.5,
        "tier_scores": '{"cto": 24, "clo": 23, "strategic": 28, '
                       '"implementation": 23, "presentation": 22.5}',
    },
    {
        "title": "Protein Category Margin Recovery Program",
        "description": (
            "Systematic analysis of protein category margins reveals "
            "consistent under-pricing on premium cuts at 12 stores. "
            "Implement dynamic pricing guardrails that maintain competitive "
            "positioning while recovering $0.80/kg on 200+ SKUs. "
            "Expected margin recovery: $890K annually."
        ),
        "team_id": "delta",
        "agent_id": "pr_pricing",
        "department": "Butcher Proteins",
        "category": "revenue",
        "estimated_impact_aud": 890000,
        "estimated_effort_weeks": 6,
        "complexity": "medium",
        "status": "scored",
        "total_score": 109.0,
        "tier_scores": '{"cto": 21, "clo": 18, "strategic": 27, '
                       '"implementation": 21, "presentation": 22}',
    },
    {
        "title": "Sustainable Sourcing Transparency Dashboard",
        "description": (
            "Create a customer-facing sustainability dashboard showing "
            "provenance, food miles, and environmental impact for key "
            "product categories. Aligns with Harris Farm's B-Corp values "
            "and premium positioning. Differentiator vs Coles/Woolworths."
        ),
        "team_id": "gamma",
        "agent_id": "bs_supplier",
        "department": "Buying Team Fresh",
        "category": "sustainability",
        "estimated_impact_aud": 600000,
        "estimated_effort_weeks": 8,
        "complexity": "medium",
        "status": "evaluating",
        "total_score": 0,
        "tier_scores": "{}",
    },
    {
        "title": "Weekend Buyer Experience Program",
        "description": (
            "Design a data-driven weekend shopping experience program "
            "targeting the premium Saturday morning shopper segment. "
            "Analysis shows Saturday 9-11am generates 34% higher basket "
            "values. Program includes curated product displays, tasting "
            "events, and personalised recommendations."
        ),
        "team_id": "beta",
        "agent_id": "so_cx",
        "department": "Service",
        "category": "customer",
        "estimated_impact_aud": 1500000,
        "estimated_effort_weeks": 10,
        "complexity": "medium",
        "status": "submitted",
        "total_score": 0,
        "tier_scores": "{}",
    },
    {
        "title": "Wholesale Digital Ordering Platform",
        "description": (
            "Build a self-service digital ordering platform for wholesale "
            "customers with real-time inventory visibility, automated "
            "pricing tiers, and predictive reorder suggestions. Reduces "
            "order processing time by 60% and improves customer satisfaction."
        ),
        "team_id": "alpha",
        "agent_id": "ws_customer",
        "department": "Wholesale Business",
        "category": "innovation",
        "estimated_impact_aud": 750000,
        "estimated_effort_weeks": 16,
        "complexity": "high",
        "status": "submitted",
        "total_score": 0,
        "tier_scores": "{}",
    },
]


# ---------------------------------------------------------------------------
# PRE-SEEDED INSIGHTS (15 across departments)
# ---------------------------------------------------------------------------

SEED_INSIGHTS = [
    {
        "agent_id": "fp_demand", "team_id": "alpha",
        "department": "Fruit and Vegetables",
        "insight_type": "opportunity",
        "title": "Stone Fruit Weekend Demand Spike Underserved",
        "description": (
            "Analysis of FY25-FY26 transaction data shows consistent 34% "
            "demand uplift for stone fruit SKUs on Saturday mornings "
            "(9-11am AEST) across top 10 stores. Current ordering patterns "
            "do not account for this, resulting in estimated $180K annual "
            "lost sales from stockouts."
        ),
        "data_source": "Transaction Data + Fiscal Calendar",
        "confidence": 0.91,
        "potential_impact_aud": 180000,
    },
    {
        "agent_id": "fp_waste", "team_id": "gamma",
        "department": "Fruit and Vegetables",
        "insight_type": "risk",
        "title": "Leafy Greens Shrinkage Exceeds Benchmark at 5 Stores",
        "description": (
            "Stores Leichhardt, Bondi, Neutral Bay, Willoughby, and "
            "Drummoyne show leafy green shrinkage rates 2.3x the network "
            "average. Root cause analysis suggests over-ordering on "
            "Mondays combined with slower midweek turnover."
        ),
        "data_source": "Transaction Data",
        "confidence": 0.87,
        "potential_impact_aud": 95000,
    },
    {
        "agent_id": "so_basket", "team_id": "epsilon",
        "department": "Store Management",
        "insight_type": "opportunity",
        "title": "Cheese-Wine Cross-Sell Generating 12% Basket Uplift",
        "description": (
            "Customers who purchase premium cheese (>$25) have a 47% "
            "probability of also purchasing wine in the same transaction. "
            "Stores with co-located displays show 12% higher combined "
            "category revenue vs stores with separate departments."
        ),
        "data_source": "Transaction Data + Product Hierarchy",
        "confidence": 0.93,
        "potential_impact_aud": 320000,
    },
    {
        "agent_id": "so_performance", "team_id": "beta",
        "department": "Store Management",
        "insight_type": "trend",
        "title": "Emerging Revenue Gap Between Metro and Suburban Stores",
        "description": (
            "Metro stores showing 8.2% YoY revenue growth vs 2.1% for "
            "suburban locations. Gap widening over last 3 quarters. "
            "Suggests differentiated strategy needed for suburban store "
            "formats including adjusted ranging and pricing."
        ),
        "data_source": "Weekly Aggregated + Fiscal Calendar",
        "confidence": 0.88,
        "potential_impact_aud": 450000,
    },
    {
        "agent_id": "pr_demand", "team_id": "alpha",
        "department": "Butcher Proteins",
        "insight_type": "opportunity",
        "title": "Premium Steak Cuts Under-Represented in 8 Stores",
        "description": (
            "Wagyu and dry-aged steak SKUs generate 3.2x average margin "
            "but are only stocked in 26 of 34 stores. Transaction analysis "
            "shows sufficient demand signals in the remaining 8 stores "
            "based on basket composition and demographic profiles."
        ),
        "data_source": "Transaction Data + Product Hierarchy",
        "confidence": 0.85,
        "potential_impact_aud": 210000,
    },
    {
        "agent_id": "gl_category", "team_id": "beta",
        "department": "Grocery",
        "insight_type": "anomaly",
        "title": "Sudden Drop in Organic Grocery Basket Penetration",
        "description": (
            "Organic product penetration in grocery baskets dropped from "
            "23% to 17% over the last 6 weeks across all stores. This "
            "coincides with competitor promotional activity. Immediate "
            "investigation and potential price response recommended."
        ),
        "data_source": "Transaction Data",
        "confidence": 0.82,
        "potential_impact_aud": 280000,
    },
    {
        "agent_id": "bk_production", "team_id": "alpha",
        "department": "Bakery",
        "insight_type": "opportunity",
        "title": "Morning Bakery Production 40 Minutes Too Early at 6 Stores",
        "description": (
            "Peak bakery purchase window is 7:30-8:30am but production "
            "completes at 6:45am at 6 stores, meaning product is 45+ "
            "minutes old at peak. Shifting production 40 minutes later "
            "could improve perceived freshness and reduce early waste."
        ),
        "data_source": "Transaction Data + Fiscal Calendar",
        "confidence": 0.89,
        "potential_impact_aud": 75000,
    },
    {
        "agent_id": "su_finance", "team_id": "beta",
        "department": "Finance",
        "insight_type": "risk",
        "title": "COGS Variance Widening in Q2 FY26",
        "description": (
            "Cost of goods sold variance vs budget has increased from "
            "1.2% to 3.8% in Q2 FY26, primarily driven by fresh produce "
            "and protein categories. Supply chain disruptions and "
            "ingredient cost inflation appear to be the primary drivers."
        ),
        "data_source": "Weekly Aggregated",
        "confidence": 0.90,
        "potential_impact_aud": 520000,
    },
    {
        "agent_id": "bs_logistics", "team_id": "alpha",
        "department": "Logistics",
        "insight_type": "opportunity",
        "title": "Route Consolidation Could Save $340K in Transport Costs",
        "description": (
            "Analysis of delivery routes shows 3 overlapping routes to "
            "Northern Beaches stores. Consolidating into 2 optimised "
            "routes would reduce total kilometres by 22% while "
            "maintaining delivery windows."
        ),
        "data_source": "Transaction Data",
        "confidence": 0.86,
        "potential_impact_aud": 340000,
    },
    {
        "agent_id": "su_it", "team_id": "gamma",
        "department": "IT",
        "insight_type": "risk",
        "title": "DuckDB Query Latency Increasing with FY26 Data Growth",
        "description": (
            "Average query response time for transaction queries has "
            "increased from 0.8s to 1.4s as FY26 data grows. At current "
            "growth rate, response times will exceed 2s threshold by "
            "April 2026. Partitioning strategy recommended."
        ),
        "data_source": "Hub Metadata",
        "confidence": 0.92,
        "potential_impact_aud": 50000,
    },
    {
        "agent_id": "gl_promo", "team_id": "alpha",
        "department": "Liquor",
        "insight_type": "opportunity",
        "title": "Craft Beer Category Showing 28% YoY Growth",
        "description": (
            "Craft beer SKUs show sustained 28% year-over-year revenue "
            "growth, outpacing all other liquor sub-categories. Current "
            "shelf space allocation (8%) is disproportionate to revenue "
            "contribution (14%). Recommend expanded range and dedicated "
            "display."
        ),
        "data_source": "Transaction Data + Product Hierarchy",
        "confidence": 0.88,
        "potential_impact_aud": 160000,
    },
    {
        "agent_id": "so_cx", "team_id": "epsilon",
        "department": "Service",
        "insight_type": "trend",
        "title": "Self-Checkout Adoption Accelerating Across Demographics",
        "description": (
            "Self-checkout transactions have grown from 18% to 31% of "
            "total transactions over the past 6 months, with the fastest "
            "adoption in the 35-50 age demographic (previously low "
            "adoption). Customer basket size at self-checkout is 15% "
            "lower than assisted checkout."
        ),
        "data_source": "Transaction Data",
        "confidence": 0.91,
        "potential_impact_aud": 200000,
    },
    {
        "agent_id": "su_people", "team_id": "beta",
        "department": "People & Culture",
        "insight_type": "risk",
        "title": "Butcher Department Turnover Rate Trending Upward",
        "description": (
            "Skilled butcher staff turnover has increased from 12% to "
            "19% annualised over the last quarter. Exit interview analysis "
            "indicates compensation competitiveness and weekend roster "
            "patterns as primary drivers."
        ),
        "data_source": "Hub Metadata",
        "confidence": 0.84,
        "potential_impact_aud": 380000,
    },
    {
        "agent_id": "ws_volume", "team_id": "alpha",
        "department": "Wholesale Business",
        "insight_type": "opportunity",
        "title": "Top 5 Wholesale Accounts Showing Cross-Sell Potential",
        "description": (
            "Analysis of top 5 wholesale accounts reveals they purchase "
            "from an average of 3.2 departments. Accounts purchasing "
            "from 5+ departments show 2.4x higher retention rates. "
            "Targeted cross-sell recommendations for each account."
        ),
        "data_source": "Transaction Data",
        "confidence": 0.83,
        "potential_impact_aud": 120000,
    },
    {
        "agent_id": "su_property", "team_id": "delta",
        "department": "Property",
        "insight_type": "opportunity",
        "title": "3 Postcodes Show Strong Expansion Potential",
        "description": (
            "Demographic analysis combined with existing store catchment "
            "modelling identifies 3 Sydney postcodes with high-income, "
            "food-interested demographics and no nearby Harris Farm store: "
            "2088 (Mosman), 2076 (Wahroonga), 2030 (Dover Heights)."
        ),
        "data_source": "Transaction Data + Weekly Aggregated",
        "confidence": 0.79,
        "potential_impact_aud": 3500000,
    },
]


# ---------------------------------------------------------------------------
# DATA INTELLIGENCE TEAM — 6 specialized sales maximization agents
# ---------------------------------------------------------------------------

DATA_INTELLIGENCE_AGENTS = [
    {
        "id": "di_lost_sales",
        "name": "Lost Sales Detective",
        "team_id": "alpha",
        "department": "Store Management",
        "business_unit": "store_ops",
        "role": "Identify and quantify missed sales opportunities",
        "capabilities": [
            "Out-of-stock detection and lost revenue calculation",
            "Demand signal detection from purchase patterns",
            "Substitution pattern analysis across categories",
            "Stockout prediction by day/time/season",
            "Customer switching behaviour modelling",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy",
                         "Fiscal Calendar"],
        "status": "active",
        "kpis": [
            "Lost sales identified per week ($)",
            "Recovery rate from recommendations",
            "Stockout prediction accuracy",
        ],
        "scoring": {
            "per_1k_lost_sales_identified": 10,
            "per_recommendation_implemented": 50,
            "per_10k_revenue_recovered": 100,
            "new_demand_pattern_discovered": 500,
        },
    },
    {
        "id": "di_overorder",
        "name": "Over-Ordering Watchdog",
        "team_id": "gamma",
        "department": "Buying Team Fresh",
        "business_unit": "buying_supply",
        "role": "Prevent waste and optimise ordering efficiency",
        "capabilities": [
            "Excess inventory detection before wastage",
            "Order vs actual sales variance tracking",
            "Buyer ordering accuracy benchmarking",
            "Waste correlation analysis by category",
            "Seasonal error pattern identification",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy",
                         "Fiscal Calendar"],
        "status": "active",
        "kpis": [
            "Waste prevented per week ($)",
            "Ordering accuracy improvement (%)",
            "Capital freed from excess inventory ($)",
        ],
        "scoring": {
            "per_1k_waste_prevented": 5,
            "per_buyer_coaching_intervention": 25,
            "per_10k_holding_cost_saved": 100,
            "major_waste_event_prevented": 250,
        },
    },
    {
        "id": "di_buying",
        "name": "Buying Strategy Optimiser",
        "team_id": "beta",
        "department": "Buying Team Gourmet",
        "business_unit": "buying_supply",
        "role": "Suggest optimal buying strategies to maximise profitability",
        "capabilities": [
            "Price elasticity analysis by product",
            "Supplier performance tracking and benchmarking",
            "Economic order quantity calculation",
            "Promotional ROI analysis",
            "Margin optimisation by category/supplier",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy",
                         "Weekly Aggregated"],
        "status": "active",
        "kpis": [
            "Margin improvement identified per month ($)",
            "Supplier cost reduction achieved (%)",
            "Promotional ROI improvement",
        ],
        "scoring": {
            "per_1k_margin_improvement": 20,
            "per_implemented_strategy": 100,
            "per_supplier_improvement": 500,
            "transformational_buying_innovation": 1000,
        },
    },
    {
        "id": "di_range",
        "name": "Range Review Analyst",
        "team_id": "delta",
        "department": "Store Management",
        "business_unit": "store_ops",
        "role": "Continuously optimise product range for maximum sales",
        "capabilities": [
            "Product performance ranking (sales, margin, velocity)",
            "Range gap identification and opportunity sizing",
            "SKU rationalisation and tail analysis",
            "Space allocation optimisation",
            "New product introduction recommendations",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy",
                         "Weekly Aggregated"],
        "status": "active",
        "kpis": [
            "Range optimisation wins per quarter",
            "Revenue from new product introductions ($)",
            "Underperformer delists actioned",
        ],
        "scoring": {
            "per_range_optimisation": 50,
            "new_product_hit_10k_month": 200,
            "category_transformation": 500,
            "range_innovation_leadership": 1000,
        },
    },
    {
        "id": "di_stocktake",
        "name": "Stocktake Intelligence Analyst",
        "team_id": "epsilon",
        "department": "Store Management",
        "business_unit": "store_ops",
        "role": "Turn stocktake data into actionable shrinkage insights",
        "capabilities": [
            "Chronic shrinkage identification by product/store",
            "Root cause investigation (theft, waste, admin error)",
            "Predictive shrinkage modelling and alerting",
            "Process improvement recommendations",
            "Industry benchmark comparison",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy"],
        "status": "active",
        "kpis": [
            "Shrinkage reduction vs prior period ($)",
            "High-risk SKU alerts actioned",
            "Process improvements implemented",
        ],
        "scoring": {
            "per_1k_shrinkage_reduction": 10,
            "per_process_improvement": 100,
            "best_in_class_shrinkage": 500,
            "transformational_loss_prevention": 1000,
        },
    },
    {
        "id": "di_transactions",
        "name": "Transaction Pattern Intelligence",
        "team_id": "epsilon",
        "department": "Store Management",
        "business_unit": "store_ops",
        "role": "Extract insights from every transaction to drive sales",
        "capabilities": [
            "Basket affinity and cross-sell identification",
            "Customer journey and conversion analysis",
            "Time-based demand pattern optimisation",
            "Micro-segment performance by store/region",
            "Traffic flow and departmental conversion",
        ],
        "data_sources": ["Transaction Data", "Product Hierarchy",
                         "Fiscal Calendar"],
        "status": "active",
        "kpis": [
            "Cross-sell opportunities identified per week",
            "Basket size improvement from insights ($)",
            "Merchandising changes implemented",
        ],
        "scoring": {
            "per_cross_sell_opportunity": 25,
            "per_merchandising_change": 100,
            "per_10k_incremental_sales": 250,
            "breakthrough_basket_insight": 500,
        },
    },
]


# Pre-seeded Data Intelligence insights
SEED_DATA_INTEL_INSIGHTS = [
    {
        "agent_id": "di_lost_sales", "team_id": "alpha",
        "department": "Fruit and Vegetables",
        "insight_type": "opportunity",
        "title": "Saturday Morning Stone Fruit Stockouts Costing $8.2K/Week",
        "description": (
            "Analysis of 383M POS transactions reveals consistent zero-sales "
            "windows for premium stone fruit SKUs (peaches, nectarines, plums) "
            "between 10-11am on Saturdays at 8 high-traffic stores. Historical "
            "demand signals show 34% uplift in this window vs weekday average. "
            "Estimated lost sales: $8,200/week across affected stores. "
            "Recommendation: increase Saturday AM delivery allocation by 25%."
        ),
        "data_source": "Transaction Data + Fiscal Calendar",
        "confidence": 0.94,
        "potential_impact_aud": 426400,
        "category": "lost_sales",
    },
    {
        "agent_id": "di_lost_sales", "team_id": "alpha",
        "department": "Bakery",
        "insight_type": "opportunity",
        "title": "Sourdough Range Gap at 6 Suburban Stores",
        "description": (
            "Customers at 6 suburban stores show strong demand signals for "
            "artisan sourdough (inferred from specialty bread purchase patterns "
            "and basket composition). These stores stock only 2 sourdough SKUs "
            "vs 8 at metro stores. Estimated missed revenue: $3,400/week."
        ),
        "data_source": "Transaction Data + Product Hierarchy",
        "confidence": 0.87,
        "potential_impact_aud": 176800,
        "category": "lost_sales",
    },
    {
        "agent_id": "di_overorder", "team_id": "gamma",
        "department": "Fruit and Vegetables",
        "insight_type": "risk",
        "title": "Leafy Greens Over-Ordered by 40% at 5 Stores",
        "description": (
            "Monday ordering patterns for leafy greens (spinach, kale, mixed "
            "leaves) at Leichhardt, Bondi, Neutral Bay, Willoughby, and "
            "Drummoyne exceed weekly sales velocity by 40%. Estimated excess "
            "inventory: $4,800/week resulting in $3,100/week waste. "
            "Recommend reducing Monday order by 30% and adding Wednesday top-up."
        ),
        "data_source": "Transaction Data",
        "confidence": 0.91,
        "potential_impact_aud": 161200,
        "category": "waste_prevention",
    },
    {
        "agent_id": "di_overorder", "team_id": "gamma",
        "department": "Bakery",
        "insight_type": "risk",
        "title": "Morning Production 40 Min Too Early at 6 Stores",
        "description": (
            "Peak bakery purchase window is 7:30-8:30am but production "
            "completes at 6:45am at 6 stores. Product is 45+ minutes old at "
            "peak trading. Late-morning sales velocity drops 22% at these "
            "stores vs network average. Shifting production 40 min later could "
            "improve freshness perception and reduce PM waste by 15%."
        ),
        "data_source": "Transaction Data + Fiscal Calendar",
        "confidence": 0.89,
        "potential_impact_aud": 95000,
        "category": "waste_prevention",
    },
    {
        "agent_id": "di_buying", "team_id": "beta",
        "department": "Butcher Proteins",
        "insight_type": "opportunity",
        "title": "Premium Steak Pricing Below Market at 12 Stores",
        "description": (
            "Wagyu and dry-aged steak SKUs are priced 8-12% below comparable "
            "premium retailers at 12 stores. Transaction data shows price "
            "insensitivity for these products (elasticity -0.3). Repricing to "
            "market level would recover $0.80/kg margin on 200+ SKUs. "
            "Estimated annual margin recovery: $890K."
        ),
        "data_source": "Transaction Data + Product Hierarchy",
        "confidence": 0.88,
        "potential_impact_aud": 890000,
        "category": "margin_improvement",
    },
    {
        "agent_id": "di_buying", "team_id": "beta",
        "department": "Grocery",
        "insight_type": "opportunity",
        "title": "Craft Beer Shelf Space vs Revenue Mismatch",
        "description": (
            "Craft beer category generates 14% of liquor revenue but occupies "
            "only 8% of shelf space. Growth rate is 28% YoY vs 4% for "
            "mainstream beer. Expanding craft range by 15 SKUs and increasing "
            "shelf allocation to 14% projects $160K incremental annual revenue."
        ),
        "data_source": "Transaction Data + Product Hierarchy",
        "confidence": 0.86,
        "potential_impact_aud": 160000,
        "category": "margin_improvement",
    },
    {
        "agent_id": "di_range", "team_id": "delta",
        "department": "Grocery",
        "insight_type": "opportunity",
        "title": "28 Underperforming SKUs Identified for Delist Review",
        "description": (
            "28 grocery SKUs show sales velocity below 2 units/week across "
            "all stores, contributing only 0.3% of category revenue while "
            "occupying 4.2% of shelf space. Replacing with top-performing "
            "alternatives from adjacent categories projects $15K/month uplift. "
            "Includes 12 duplicative gluten-free pasta variants."
        ),
        "data_source": "Transaction Data + Product Hierarchy",
        "confidence": 0.92,
        "potential_impact_aud": 180000,
        "category": "range_optimisation",
    },
    {
        "agent_id": "di_range", "team_id": "delta",
        "department": "Cheese Cutting",
        "insight_type": "opportunity",
        "title": "Premium Cheese Range Expansion Opportunity",
        "description": (
            "Basket analysis shows customers purchasing premium cheese (>$25) "
            "have 2.8x higher total basket value. Currently stocking 45 "
            "premium cheese SKUs vs 120+ at specialty competitors. Top 10 "
            "gaps identified: aged cheddar, truffle varieties, local artisan. "
            "Projected uplift: $22K/month across network."
        ),
        "data_source": "Transaction Data + Product Hierarchy",
        "confidence": 0.85,
        "potential_impact_aud": 264000,
        "category": "range_optimisation",
    },
    {
        "agent_id": "di_stocktake", "team_id": "epsilon",
        "department": "Butcher Proteins",
        "insight_type": "risk",
        "title": "Protein Shrinkage 2.3x Network Average at 4 Stores",
        "description": (
            "Stores Leichhardt, Bondi Beach, Neutral Bay, and Mosman show "
            "protein category shrinkage rates 2.3x the network average. "
            "Root cause analysis: over-cutting of premium cuts during quiet "
            "periods combined with insufficient markdown velocity. "
            "Estimated annual loss: $185K across 4 stores."
        ),
        "data_source": "Transaction Data",
        "confidence": 0.90,
        "potential_impact_aud": 185000,
        "category": "shrinkage_reduction",
    },
    {
        "agent_id": "di_stocktake", "team_id": "epsilon",
        "department": "Fruit and Vegetables",
        "insight_type": "anomaly",
        "title": "Berry Shrinkage Spike at Store 12 (3.2x Expected)",
        "description": (
            "Store 12 (Alexandria) showing berry category shrinkage 3.2x "
            "the predicted level over the last 4 weeks. Pattern does not "
            "correlate with ordering volumes or seasonal factors. "
            "Recommend immediate investigation: possible refrigeration issue "
            "or receiving process breakdown."
        ),
        "data_source": "Transaction Data",
        "confidence": 0.93,
        "potential_impact_aud": 42000,
        "category": "shrinkage_reduction",
    },
    {
        "agent_id": "di_transactions", "team_id": "epsilon",
        "department": "Store Management",
        "insight_type": "opportunity",
        "title": "Cheese-Wine Cross-Sell Generating 12% Basket Uplift",
        "description": (
            "Customers purchasing premium cheese (>$25) have 47% probability "
            "of also purchasing wine in the same basket. Stores with "
            "co-located displays show 12% higher combined category revenue. "
            "8 stores currently have separated departments. Implementing "
            "cross-merchandising at all 8: projected $320K annual uplift."
        ),
        "data_source": "Transaction Data + Product Hierarchy",
        "confidence": 0.93,
        "potential_impact_aud": 320000,
        "category": "cross_sell",
    },
    {
        "agent_id": "di_transactions", "team_id": "epsilon",
        "department": "Store Management",
        "insight_type": "trend",
        "title": "Friday 4-6pm Drives 40% of Weekly Deli Revenue",
        "description": (
            "Hourly transaction analysis reveals Friday 4-6pm AEST accounts "
            "for 40% of weekly deli/prepared foods revenue across all stores. "
            "Current staffing levels are only 15% above weekday average. "
            "Increasing deli staffing by 50% and stock by 25% during this "
            "window projects $8K/week incremental revenue."
        ),
        "data_source": "Transaction Data + Fiscal Calendar",
        "confidence": 0.91,
        "potential_impact_aud": 416000,
        "category": "cross_sell",
    },
]


# Data Intelligence scoring categories
DATA_INTEL_CATEGORIES = [
    {"id": "lost_sales", "name": "Lost Sales", "icon": "🔍",
     "description": "Missed revenue opportunities identified and recovered"},
    {"id": "waste_prevention", "name": "Waste Prevention", "icon": "♻️",
     "description": "Waste avoided through ordering optimisation"},
    {"id": "margin_improvement", "name": "Margin Improvement", "icon": "📈",
     "description": "Profitability gains from buying and pricing strategies"},
    {"id": "range_optimisation", "name": "Range Optimisation", "icon": "📦",
     "description": "Product range improvements for maximum sales"},
    {"id": "shrinkage_reduction", "name": "Shrinkage Reduction", "icon": "🔒",
     "description": "Loss prevention and stocktake intelligence"},
    {"id": "cross_sell", "name": "Cross-Sell", "icon": "🛒",
     "description": "Basket analysis and merchandising opportunities"},
]


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_team(team_id):
    """Return team dict by ID, or None."""
    for t in AGENT_TEAMS:
        if t["id"] == team_id:
            return t
    return None


def get_agent(agent_id):
    """Return agent dict by ID, or None. Searches both department and data intel agents."""
    for a in DEPARTMENT_AGENTS:
        if a["id"] == agent_id:
            return a
    for a in DATA_INTELLIGENCE_AGENTS:
        if a["id"] == agent_id:
            return a
    return None


def get_data_intel_agent(agent_id):
    """Return Data Intelligence agent dict by ID, or None."""
    for a in DATA_INTELLIGENCE_AGENTS:
        if a["id"] == agent_id:
            return a
    return None


def get_agents_by_unit(business_unit):
    """Return list of agents in a business unit."""
    return [a for a in DEPARTMENT_AGENTS
            if a["business_unit"] == business_unit]


def get_agents_by_team(team_id):
    """Return list of agents belonging to a team."""
    return [a for a in DEPARTMENT_AGENTS if a["team_id"] == team_id]


def get_business_unit(unit_id):
    """Return business unit dict by ID, or None."""
    for bu in BUSINESS_UNITS:
        if bu["id"] == unit_id:
            return bu
    return None


def calculate_proposal_score(tier_evaluations):
    """Calculate total proposal score from tier evaluations.

    Args:
        tier_evaluations: list of dicts with keys: tier, criterion, score (1-5)

    Returns:
        dict with tier_scores (per-tier totals) and total (out of 130).

    Each tier's criteria are scored 1-5. The tier score is calculated as:
        (average criterion score / 5) * tier_max_points
    """
    tier_totals = {}
    for tier in EVALUATION_TIERS:
        tier_evals = [e for e in tier_evaluations
                      if e.get("tier") == tier["id"]]
        if not tier_evals:
            tier_totals[tier["id"]] = 0.0
            continue
        avg_raw = sum(e["score"] for e in tier_evals) / len(tier_evals)
        tier_totals[tier["id"]] = round(avg_raw / 5.0 * tier["max_points"], 1)

    total = round(sum(tier_totals.values()), 1)
    return {"tier_scores": tier_totals, "total": total}
