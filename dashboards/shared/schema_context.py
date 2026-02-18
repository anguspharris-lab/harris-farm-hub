"""
Harris Farm Hub — Shared Schema Context for Natural Language Query Generation.
Single source of truth for database tables, columns, and query routing.
Used by the /api/query backend endpoint to generate correct SQL.
"""

import re
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# SQLITE SCHEMA  (harris_farm.db — weekly aggregated business data)
# ---------------------------------------------------------------------------

SQLITE_SCHEMA = """
DATABASE: harris_farm.db (SQLite)
Weekly aggregated business data for Harris Farm Markets (FY2017-FY2024).

TABLE: sales  (1.6M rows — weekly sales by store/department/major group)
  IMPORTANT: This table uses a MEASURE-DIMENSION pattern.
  The 'measure' column determines what 'value' means.
  Columns:
    store           TEXT  — Store name, format "10 - HFM Pennant Hills"
    channel         TEXT  — "Retail" or "Online"
    department      TEXT  — Format "10 - Fruit & Vegetables", "20 - Grocery", "30 - Perishable", "40 - Flowers", "50 - Proteins", "60 - Bakery", "70 - Liquor", "80 - Service/Counter"
    major_group     TEXT  — Format "01 - Vegetables"
    is_promotion    TEXT  — "N" or "Y"
    measure         TEXT  — One of EXACTLY these values:
                            "Sales - Val"              → Revenue dollars
                            "Initial Gross Profit - Val" → Initial GP dollars
                            "Final Gross Prod - Val"   → Final GP (after shrinkage) dollars
                            "Bgt Sales - Val"          → Budget sales dollars
                            "Bgt Final GP - Val"       → Budget GP dollars
                            "Total Shrinkage - Val"    → Shrinkage dollars
    fy_lol          INT   — Financial year like-on-like flag (1 = comparable store)
    rolling_13wk_lol INT  — Rolling 13-week like-on-like flag
    fv_store        INT   — Fruit & Vegetables store flag (1 = FV store)
    week_ending     TEXT  — Week ending date YYYY-MM-DD
    value           REAL  — Dollar value for the selected measure

  QUERY RULES for 'sales' table:
    - To get revenue: WHERE measure = 'Sales - Val'
    - To get gross profit: WHERE measure = 'Final Gross Prod - Val'
    - To get shrinkage: WHERE measure = 'Total Shrinkage - Val'
    - To get budget: WHERE measure = 'Bgt Sales - Val'
    - GP% = SUM(value WHERE measure='Final Gross Prod - Val') / SUM(value WHERE measure='Sales - Val') * 100
    - Budget variance = (SUM(actual) - SUM(budget)) / SUM(budget) * 100
    - For like-on-like comparisons: AND fy_lol = 1
    - Date range: 2016-07-10 to 2024-06-30

  LIMITATION: This table has NO item-level product data. The finest granularity is
  department + major_group. For specific product queries (e.g. "bananas", "avocados"),
  the DuckDB transaction database must be used instead — this is handled automatically.

TABLE: customers  (17K rows — weekly customer counts by store)
  Columns:
    store           TEXT  — Store name (same format as sales.store)
    channel         TEXT  — "Retail" or "Online"
    measure         TEXT  — "Customer Count" or "Budget Customers"
    week_ending     TEXT  — Week ending date YYYY-MM-DD
    value           REAL  — Count value

TABLE: market_share  (77K rows — market share by region and period)
  Columns:
    period                    INT   — Period code YYYYMM (e.g. 202312)
    region_code               TEXT  — Region code (e.g. "2150")
    region_name               TEXT  — Region name (e.g. "Parramatta")
    industry_name             TEXT  — Always "Harris Farm Markets"
    channel                   TEXT  — "Instore", "Online", or "Total"
    market_size_dollars       REAL  — Total market size in dollars
    market_share_pct          REAL  — Harris Farm market share %
    customer_penetration_pct  REAL  — Customer penetration %
    spend_per_customer        REAL  — Average spend per customer ($)
    spend_per_transaction     REAL  — Average spend per transaction ($)
    transactions_per_customer REAL  — Average transactions per customer

TABLE: stores  (30 rows — store reference master)
  Columns:
    store_number    TEXT  — Store ID (e.g. "10")
    store_name      TEXT  — Store name (e.g. "HFM Pennant Hills")
    store_company   TEXT  — "Harris Farm Markets"
    state           TEXT  — "NSW"
    store_type      TEXT  — "Retail"
    fv_store        INT   — 1=FV store, 0=not
    like_for_like   INT   — 1=comparable, 0=not

TABLE: departments  (28 rows — department and major group hierarchy)
  Columns:
    department_code     TEXT
    department_name     TEXT  — e.g. "Fruit & Vegetables"
    major_group_code    TEXT
    major_group_name    TEXT  — e.g. "Vegetables"

TABLE: fiscal_calendar  (626 rows — weekly fiscal calendar FY2015-FY2027)
  Columns:
    sequence              INT   — Sequential week number
    week_ending_date      TEXT  — Week ending date YYYY-MM-DD
    financial_year        INT   — e.g. 2025
    fin_week_of_month     INT   — 1-5
    fin_week_of_year      INT   — 1-53
    prior_year_week_ending TEXT — Prior year equivalent week

TABLE: product_lines  (491 rows — product hierarchy reference)
  Columns:
    department_code     INT
    department_name     TEXT
    major_group_code    INT
    major_group_name    TEXT
    minor_group_code    TEXT
    minor_group_name    TEXT
    item_family_code    TEXT
    item_family_name    TEXT

KEY JOINS:
  - sales.store links to stores by composite key (e.g. "10 - HFM Pennant Hills" contains store_number "10")
  - sales.department links to departments (e.g. "10 - Fruit & Vegetables" contains department_code "10")
  - sales.week_ending = fiscal_calendar.week_ending_date
"""

# ---------------------------------------------------------------------------
# DUCKDB SCHEMA  (transaction parquets — 383M line-item POS records)
# ---------------------------------------------------------------------------

DUCKDB_SCHEMA = """
DATABASE: DuckDB in-memory (transaction parquets — 383M POS line-item records)
Individual point-of-sale transactions from FY24-FY26 (Jul 2023 - Feb 2026).

TABLE/VIEW: transactions  (383M rows — individual POS line items)
  Columns:
    Reference2      TEXT      — Transaction reference ID
    SaleDate        TIMESTAMP — Sale datetime (UTC)
    Store_ID        TEXT      — Store number (e.g. "10", "48", "57")
    PLUItem_ID      TEXT      — Product PLU code
    Quantity        DOUBLE    — Units sold (can be fractional for weighed items)
    SalesIncGST     DOUBLE    — Revenue including GST ($)
    GST             DOUBLE    — GST component ($)
    EstimatedCOGS   DOUBLE    — Estimated cost of goods ($, typically negative)
    CustomerCode    TEXT      — Customer ID or "NULL" (88% null)
    fiscal_year     TEXT      — "FY24", "FY25", or "FY26"

TABLE: product_hierarchy  (72,911 rows — product master with full hierarchy)
  Columns:
    ProductNumber           TEXT  — PLU code (join key to transactions.PLUItem_ID)
    ProductName             TEXT  — Product description
    DepartmentCode          TEXT  — Department code (e.g. "10", "20")
    DepartmentDesc          TEXT  — Format "10 - FRUIT & VEGETABLES"
    MajorGroupCode          TEXT  — Major group code
    MajorGroupDesc          TEXT  — Format "01 - VEGETABLES"
    MinorGroupCode          TEXT  — Minor group code
    MinorGroupDesc          TEXT  — Format "05 - BABY"
    HFMItem                 TEXT  — HFM item code
    HFMItemDesc             TEXT  — HFM item description (e.g. "WIPES")
    BuyerId                 TEXT  — Buyer code (e.g. "TWHITE")
    ProductLifecycleStateId TEXT  — "Active", "Deleted", "New/Inactive", or NULL

TABLE: fiscal_calendar  (4,018 rows — daily fiscal calendar)
  Columns:
    TheDate             TIMESTAMP — Calendar date
    DayOfWeekNo         INT       — 1=Monday through 7=Sunday
    DayOfWeekName       TEXT      — "Monday" through "Sunday"
    BusinessDay         TEXT      — "Y" or "N"
    Weekend             TEXT      — "Y" or "N"
    WeekEndingDate      TIMESTAMP — Week ending date
    SeasonName          TEXT      — "Summer", "Autumn", "Winter", "Spring"
    FinYear             INT       — Financial year (e.g. 2025)
    FinMonthOfYearNo    INT       — Fiscal month 1-12
    FinWeekOfYearNo     INT       — Fiscal week 1-53
    FinQuarterOfYearNo  INT       — Fiscal quarter 1-4

KEY JOINS:
  - transactions.PLUItem_ID = product_hierarchy.ProductNumber
  - CAST(transactions.SaleDate AS DATE) = fiscal_calendar.TheDate
  - transactions.Store_ID maps to store names (10=Pennant Hills, 24=St Ives, 28=Mosman, 32=Willoughby, 37=Broadway, 40=Erina, 44=Orange, 48=Manly, 49=Mona Vale, 51=Bowral, 52=Cammeray, 54=Potts Point, 56=Boronia Park, 57=Bondi Beach, 58=Drummoyne, 59=Bathurst, 63=Randwick, 64=Leichhardt, 65=Bondi Westfield, 66=Newcastle, 67=Lindfield, 68=Albury, 69=Rose Bay, 70=West End QLD, 74=Isle of Capri QLD, 75=Clayfield QLD, 76=Lane Cove, 77=Dural, 80=Majura Park ACT, 84=Redfern, 85=Marrickville, 86=Miranda, 87=Maroubra)

PRODUCT HIERARCHY (6 levels — broadest to most specific):
  Store → Department → Major Group → Minor Group → Item Family → PLU
  Examples:
    Department:   "10 - FRUIT & VEGETABLES"
    Major Group:  "01 - VEGETABLES"
    Minor Group:  "05 - BABY"
    Item (ProductName): "BANANA CAVENDISH", "AVOCADO HASS LARGE", "SOURDOUGH LOAF"

PRODUCT SEARCH RULES (CRITICAL — follow these exactly):
  1. When the user asks about a SPECIFIC PRODUCT (e.g. "bananas", "avocados", "sourdough bread", "lamb cutlets"):
     - ALWAYS search at the ProductName level using ILIKE pattern matching
     - NEVER assume the product name appears in MajorGroupDesc or DepartmentDesc
     - Use: WHERE LOWER(ph.ProductName) LIKE LOWER('%banana%')
     - The ProductName column contains item-level descriptions like "BANANA CAVENDISH", "BANANA LADY FINGER"

  2. When the user asks about a CATEGORY (e.g. "fruit sales", "grocery department", "vegetables"):
     - Search at DepartmentDesc or MajorGroupDesc level
     - Use: WHERE LOWER(ph.DepartmentDesc) LIKE LOWER('%fruit%')
     - Or:  WHERE LOWER(ph.MajorGroupDesc) LIKE LOWER('%vegetable%')

  3. CASCADING SEARCH APPROACH (for ambiguous terms):
     - First try ProductName (most specific)
     - Then MinorGroupDesc
     - Then MajorGroupDesc
     - Then DepartmentDesc (broadest)
     In practice: use LOWER(ph.ProductName) LIKE LOWER('%term%') for specific products,
     and LOWER(ph.MajorGroupDesc) LIKE LOWER('%term%') or LOWER(ph.DepartmentDesc) LIKE LOWER('%term%') for categories.

  4. COMMON PRODUCT MAPPINGS (search term → what to use):
     "bananas"      → WHERE LOWER(ph.ProductName) LIKE '%banana%'
     "avocados"     → WHERE LOWER(ph.ProductName) LIKE '%avocado%'
     "strawberries" → WHERE LOWER(ph.ProductName) LIKE '%strawberr%'
     "milk"         → WHERE LOWER(ph.ProductName) LIKE '%milk%'
     "bread"        → WHERE LOWER(ph.ProductName) LIKE '%bread%' OR LOWER(ph.ProductName) LIKE '%loaf%'
     "chicken"      → WHERE LOWER(ph.ProductName) LIKE '%chicken%'
     "lamb"         → WHERE LOWER(ph.ProductName) LIKE '%lamb%'
     "beef"         → WHERE LOWER(ph.ProductName) LIKE '%beef%'
     "salmon"       → WHERE LOWER(ph.ProductName) LIKE '%salmon%'
     "cheese"       → WHERE LOWER(ph.ProductName) LIKE '%cheese%'
     "wine"         → WHERE LOWER(ph.ProductName) LIKE '%wine%'
     "pasta"        → WHERE LOWER(ph.MinorGroupDesc) LIKE '%pasta%' (category-level)
     "fruit"        → WHERE LOWER(ph.DepartmentDesc) LIKE '%fruit%' (department-level)
     "vegetables"   → WHERE LOWER(ph.MajorGroupDesc) LIKE '%vegetable%' (major group)
     "grocery"      → WHERE LOWER(ph.DepartmentDesc) LIKE '%grocery%' (department-level)
     "bakery"       → WHERE LOWER(ph.DepartmentDesc) LIKE '%bakery%' (department-level)
     "flowers"      → WHERE LOWER(ph.DepartmentDesc) LIKE '%flower%' (department-level)
     "liquor"       → WHERE LOWER(ph.DepartmentDesc) LIKE '%liquor%' (department-level)
     "proteins"     → WHERE LOWER(ph.DepartmentDesc) LIKE '%protein%' (department-level)

DATE HANDLING RULES:
  - "last week" = the most recent COMPLETE Monday-to-Sunday week (not the current partial week)
  - "this week" = current partial week starting Monday
  - "last month" = previous calendar month
  - "this month" = current calendar month so far
  - "this financial year" = starts 1 July. If current date is before July, FY = current year. If after July, FY = current year + 1.
  - Use fiscal_calendar table for fiscal period lookups: JOIN fiscal_calendar fc ON CAST(t.SaleDate AS DATE) = fc.TheDate
  - For DuckDB date arithmetic: SaleDate >= CURRENT_DATE - INTERVAL '7 days'

SALES COLUMN RULES:
  - Revenue (inc GST): SUM(t.SalesIncGST)
  - Revenue (ex GST): SUM(t.SalesIncGST - t.GST)
  - Cost of goods: SUM(t.EstimatedCOGS) — note: COGS values are typically negative
  - Gross margin: SUM(t.SalesIncGST + t.EstimatedCOGS)
  - Quantity sold: SUM(t.Quantity)
  - For "how many sold" questions, use SUM(t.Quantity)
  - For "revenue" or "sales value", use SUM(t.SalesIncGST)

STANDARD QUERY PATTERN for product queries:
  SELECT
      ph.ProductName,
      SUM(t.Quantity) AS "Units Sold",
      ROUND(SUM(t.SalesIncGST), 2) AS "Revenue"
  FROM transactions t
  JOIN product_hierarchy ph ON t.PLUItem_ID = ph.ProductNumber
  WHERE LOWER(ph.ProductName) LIKE LOWER('%search_term%')
    AND t.SaleDate >= <date_filter>
  GROUP BY ph.ProductName
  ORDER BY SUM(t.SalesIncGST) DESC
  LIMIT 20
"""

# ---------------------------------------------------------------------------
# PAGE CONTEXT → DATABASE ROUTING
# ---------------------------------------------------------------------------

# Which database each page context should query
PAGE_DATABASE = {
    # SQLite pages (weekly aggregated data)
    "sales": "sqlite",
    "profitability": "sqlite",
    "customers": "sqlite",
    "market_share": "sqlite",
    "trending": "sqlite",
    "general": "sqlite",
    # DuckDB pages (transaction-level data)
    "store_ops": "duckdb",
    "product_intel": "duckdb",
    "revenue_bridge": "duckdb",
    "buying_hub": "duckdb",
}

# ---------------------------------------------------------------------------
# PAGE-SPECIFIC GUIDANCE
# ---------------------------------------------------------------------------

PAGE_GUIDANCE = {
    "sales": (
        "The user is on the SALES dashboard. "
        "Default to the 'sales' table with measure='Sales - Val' for revenue questions. "
        "Use measure='Final Gross Prod - Val' for gross profit. "
        "Use measure='Total Shrinkage - Val' for shrinkage. "
        "Join to fiscal_calendar on week_ending = week_ending_date for fiscal period analysis."
    ),
    "profitability": (
        "The user is on the PROFITABILITY dashboard. "
        "Use the 'sales' table with different measures: "
        "'Sales - Val' for revenue, 'Final Gross Prod - Val' for GP, "
        "'Bgt Final GP - Val' for budget GP, 'Total Shrinkage - Val' for shrinkage. "
        "GP% = SUM(GP value) / SUM(Sales value) * 100."
    ),
    "customers": (
        "The user is on the CUSTOMERS dashboard. "
        "Default to the 'customers' table. "
        "Use measure='Customer Count' for actual counts, 'Budget Customers' for budget. "
        "Can cross-reference with 'sales' table for revenue-per-customer analysis."
    ),
    "market_share": (
        "The user is on the MARKET SHARE dashboard. "
        "Default to the 'market_share' table. "
        "Period is in YYYYMM format. Channel can be 'Instore', 'Online', or 'Total'. "
        "For trends, use GROUP BY period ORDER BY period."
    ),
    "trending": (
        "The user is on the TRENDING dashboard. "
        "Use the 'sales' table for trend analysis. "
        "Group by week_ending or join to fiscal_calendar for period-level trends."
    ),
    "store_ops": (
        "The user is on the STORE OPERATIONS dashboard (transaction-level data). "
        "Default to the 'transactions' table (383M rows). "
        "Join to product_hierarchy ON PLUItem_ID = ProductNumber for product details. "
        "Join to fiscal_calendar ON CAST(SaleDate AS DATE) = TheDate for fiscal periods. "
        "Always include reasonable filters (date range, store) to keep queries performant."
    ),
    "product_intel": (
        "The user is on the PRODUCT INTELLIGENCE dashboard (transaction-level data). "
        "Focus on product performance using transactions joined to product_hierarchy. "
        "Group by DepartmentDesc, MajorGroupDesc, MinorGroupDesc, or ProductName for hierarchy analysis."
    ),
    "revenue_bridge": (
        "The user is on the REVENUE BRIDGE dashboard (transaction-level data). "
        "Focus on revenue analysis: SalesIncGST for revenue, EstimatedCOGS for cost, "
        "SalesIncGST + EstimatedCOGS for margin (COGS is negative). "
        "Compare periods using fiscal_calendar."
    ),
    "buying_hub": (
        "The user is on the BUYING HUB dashboard (transaction-level data). "
        "Focus on buyer-level analysis. Join to product_hierarchy for BuyerId. "
        "Useful metrics: revenue per buyer, product count per buyer, margins by buyer."
    ),
    "general": (
        "General query context. Choose the most relevant table based on the question. "
        "Use 'sales' for revenue/performance, 'customers' for traffic, "
        "'market_share' for competitive analysis."
    ),
}

# ---------------------------------------------------------------------------
# SUGGESTED QUESTIONS PER PAGE
# ---------------------------------------------------------------------------

SUGGESTED_QUESTIONS = {
    "sales": [
        "Which store had the highest sales this financial year?",
        "What are the top 5 departments by revenue?",
        "Show me weekly sales trends for the last 12 weeks",
        "Which store has the worst budget variance?",
        "Compare Fruit & Vegetables sales across all stores",
    ],
    "profitability": [
        "Which store has the best gross profit percentage?",
        "Where is shrinkage highest as a percentage of sales?",
        "Compare GP% across all departments",
        "Which stores are under budget for gross profit?",
        "Show me the top 10 most profitable major groups",
    ],
    "customers": [
        "Which store has the most customers?",
        "Show me customer count trends over the last 12 weeks",
        "Which stores are below budget for customer counts?",
        "Compare retail vs online customer counts",
        "What is the average customer count per store per week?",
    ],
    "market_share": [
        "Which region has our highest market share?",
        "How has our market share changed over the last 6 months?",
        "Where is customer penetration lowest?",
        "What is our average spend per customer by region?",
        "Compare instore vs online market share",
    ],
    "trending": [
        "What are the fastest growing departments?",
        "Show me week-over-week sales trends",
        "Which stores are trending up vs down?",
        "Compare this year's sales to last year",
        "What is the seasonal sales pattern for Fruit & Vegetables?",
    ],
    "store_ops": [
        "What time of day has the highest transaction volume?",
        "Which products have the most transactions today?",
        "Show me average basket size by store",
        "What is the busiest day of the week?",
        "Top 10 products by revenue this month",
    ],
    "product_intel": [
        "What are the top selling products this month?",
        "Which products have declining sales?",
        "Show me revenue by department for this fiscal year",
        "What is the average selling price by major group?",
        "Which products have the highest margin?",
    ],
    "revenue_bridge": [
        "Compare revenue this month vs last month",
        "What is the revenue split by department?",
        "Show me daily revenue trends for the last 2 weeks",
        "Which store has the highest revenue per transaction?",
        "Compare weekday vs weekend revenue",
    ],
    "buying_hub": [
        "Which buyer handles the most revenue?",
        "Show me product count by buyer",
        "What is the margin by buyer?",
        "Which buyer's products are growing fastest?",
        "Top 10 products by quantity sold this week",
    ],
    "general": [
        "Give me a summary of last week's performance",
        "Which store is performing best overall?",
        "What should I be looking at right now?",
    ],
}


# ---------------------------------------------------------------------------
# PRODUCT QUERY DETECTION
# ---------------------------------------------------------------------------

# Specific product names that should trigger item-level search (DuckDB)
_PRODUCT_TERMS = {
    # Fruit
    "banana", "apple", "orange", "mango", "avocado", "strawberry", "strawberries",
    "blueberry", "blueberries", "raspberry", "raspberries", "grape", "grapes",
    "watermelon", "rockmelon", "pineapple", "pear", "peach", "plum", "cherry",
    "cherries", "kiwi", "lemon", "lime", "grapefruit", "mandarin", "nectarine",
    "fig", "pomegranate", "passionfruit", "lychee", "papaya", "dragonfruit",
    # Vegetables
    "tomato", "potato", "onion", "carrot", "broccoli", "capsicum", "zucchini",
    "cucumber", "lettuce", "spinach", "kale", "mushroom", "corn", "celery",
    "beetroot", "pumpkin", "sweet potato", "asparagus", "cauliflower", "eggplant",
    "garlic", "ginger", "chilli", "bean", "pea",
    # Proteins
    "chicken", "beef", "lamb", "pork", "salmon", "prawn", "prawns", "steak",
    "mince", "sausage", "bacon", "ham", "turkey", "duck", "veal", "barramundi",
    "tuna", "snapper", "fish",
    # Dairy
    "milk", "cheese", "yoghurt", "yogurt", "butter", "cream", "egg", "eggs",
    # Bakery
    "bread", "sourdough", "croissant", "muffin", "cake", "pie", "roll", "baguette",
    "loaf",
    # Grocery
    "pasta", "rice", "cereal", "coffee", "tea", "chocolate", "chips", "sauce",
    "oil", "olive oil", "vinegar", "flour", "sugar", "honey", "jam", "nuts",
    # Drinks
    "wine", "beer", "juice", "water", "kombucha", "cider",
    # Flowers
    "roses", "tulips", "bouquet", "flowers",
}

# Category terms that map to department/major group level
_CATEGORY_TERMS = {
    "fruit": "department",
    "vegetables": "major_group",
    "grocery": "department",
    "bakery": "department",
    "liquor": "department",
    "proteins": "department",
    "flowers": "department",
    "perishable": "department",
    "service": "department",
    "deli": "department",
}

# Pattern: "how many X did we sell", "X sales", "top X products", etc.
_PRODUCT_QUERY_PATTERNS = [
    r"how many (\w+)",
    r"(\w+) (?:sales|revenue|sold|selling)",
    r"(?:sell|sold|selling) (?:the most |any )?(\w+)",
    r"top \d+ (?:selling )?(\w+)",
    r"best selling (\w+)",
    r"worst selling (\w+)",
    r"price of (\w+)",
]


def detect_product_query(question: str) -> dict:
    """Detect if a question is about specific products or categories.

    Returns:
        dict with keys:
            is_product_query: bool — True if specific product detected
            is_category_query: bool — True if category-level detected
            search_terms: list[str] — product/category terms found
            search_level: str — "product", "category", or None
            needs_duckdb: bool — True if query must route to DuckDB
    """
    q = question.lower()
    result = {
        "is_product_query": False,
        "is_category_query": False,
        "search_terms": [],
        "search_level": None,
        "needs_duckdb": False,
    }

    # Check for specific product terms
    found_products = []
    for term in _PRODUCT_TERMS:
        # Match whole word or with common suffixes (s, es)
        if re.search(rf"\b{re.escape(term)}s?\b", q):
            found_products.append(term)

    if found_products:
        result["is_product_query"] = True
        result["search_terms"] = found_products
        result["search_level"] = "product"
        result["needs_duckdb"] = True
        return result

    # Check for category terms
    found_categories = []
    for term, level in _CATEGORY_TERMS.items():
        if re.search(rf"\b{re.escape(term)}\b", q):
            found_categories.append(term)

    if found_categories:
        result["is_category_query"] = True
        result["search_terms"] = found_categories
        result["search_level"] = "category"
        # Category queries can work in DuckDB too for richer results
        result["needs_duckdb"] = True
        return result

    # Check patterns that imply product-level queries
    for pattern in _PRODUCT_QUERY_PATTERNS:
        match = re.search(pattern, q)
        if match:
            extracted = match.group(1)
            # Only flag if the extracted term looks like a product
            if extracted in _PRODUCT_TERMS or len(extracted) > 3:
                # Check it's not a generic business term
                generic = {"store", "stores", "week", "month", "year", "department",
                           "revenue", "sales", "profit", "budget", "customer", "customers",
                           "market", "share", "total", "average", "daily", "weekly"}
                if extracted not in generic:
                    result["is_product_query"] = True
                    result["search_terms"] = [extracted]
                    result["search_level"] = "product"
                    result["needs_duckdb"] = True

    return result


# ---------------------------------------------------------------------------
# SCHEMA PROMPT BUILDER
# ---------------------------------------------------------------------------

def get_schema_for_page(page_context: str, question: str = None) -> tuple:
    """Return a complete schema prompt tailored to a specific dashboard page.

    If a question is provided, detects product-level queries and auto-routes
    to DuckDB even if the page normally uses SQLite.

    Returns:
        tuple of (prompt: str, effective_db: str)
            effective_db is "sqlite" or "duckdb" — the actual DB to execute against
    """
    db_type = PAGE_DATABASE.get(page_context, "sqlite")
    product_info = None

    # Auto-route product queries to DuckDB
    if question and db_type == "sqlite":
        product_info = detect_product_query(question)
        if product_info["needs_duckdb"]:
            db_type = "duckdb"  # Override to DuckDB for product-level queries

    schema = DUCKDB_SCHEMA if db_type == "duckdb" else SQLITE_SCHEMA
    guidance = PAGE_GUIDANCE.get(page_context, PAGE_GUIDANCE["general"])

    # If we auto-routed, add extra guidance
    if product_info and product_info["needs_duckdb"]:
        terms = ", ".join(product_info["search_terms"])
        if product_info["is_product_query"]:
            guidance += (
                f"\n\nAUTO-ROUTED: This query mentions specific product(s): {terms}. "
                "The SQLite database does NOT have item-level data, so this query has been "
                "routed to the DuckDB transaction database. "
                "Use product_hierarchy.ProductName with LIKE patterns to find matching products. "
                "Join transactions to product_hierarchy ON PLUItem_ID = ProductNumber."
            )
        elif product_info["is_category_query"]:
            guidance += (
                f"\n\nAUTO-ROUTED: This query mentions product category: {terms}. "
                "Routed to DuckDB for richer product-level detail. "
                "Use DepartmentDesc or MajorGroupDesc to filter by category."
            )

    prompt = f"""You are a SQL expert for Harris Farm Markets, an Australian premium fresh-food grocery retailer with 30+ stores across NSW, QLD, and ACT.

Today's date: {datetime.now().strftime('%Y-%m-%d')}

{schema}

PAGE CONTEXT: {guidance}

CRITICAL RULES:
- Return ONLY the SQL query. No explanation, no markdown backticks, no comments.
- Use {"SQLite" if db_type == "sqlite" else "DuckDB"} syntax.
- Always include ORDER BY and LIMIT (max 1000 rows).
- Use clear column aliases in the SELECT clause.
- For monetary values, round to 2 decimal places.
- For percentages, round to 1 decimal place.
- Use Australian English in column aliases (e.g. "Gross Profit" not "Gross Margin").
- NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or any write operations.
"""
    return prompt, db_type


# ---------------------------------------------------------------------------
# INTENT CLASSIFICATION
# ---------------------------------------------------------------------------

def classify_query_intent(question: str) -> str:
    """Pre-classify question intent to help route to correct tables."""
    q = question.lower()

    # Check for specific product queries first (highest priority)
    product_info = detect_product_query(question)
    if product_info["is_product_query"]:
        return "product_specific"
    if product_info["is_category_query"]:
        return "product_category"

    if any(t in q for t in [
        "out of stock", "oos", "stock out", "availability",
        "missing", "empty shelf",
    ]):
        return "inventory"
    if any(t in q for t in [
        "transport", "delivery", "route", "truck",
        "logistics", "freight", "cost per km",
    ]):
        return "transport"
    if any(t in q for t in [
        "p&l", "profit and loss", "labour", "labor",
        "rent", "net profit", "net margin", "opex",
    ]):
        return "profitability"
    if any(t in q for t in [
        "market share", "penetration", "market size",
        "spend per customer", "competitive",
    ]):
        return "market_share"
    if any(t in q for t in [
        "customer", "traffic", "footfall", "visitor",
        "customer count",
    ]):
        return "customers"
    if any(t in q for t in [
        "when", "time of day", "day of week", "hour",
        "peak", "busiest", "quietest", "morning", "evening",
    ]):
        return "temporal"
    if any(t in q for t in [
        "product", "plu", "sku", "item",
        "category", "department", "hierarchy",
        "buyer", "buying",
    ]):
        return "product"
    if any(t in q for t in [
        "sales", "revenue", "gp", "gross profit",
        "margin", "budget", "shrinkage", "top selling",
    ]):
        return "sales"
    return "general"


# ---------------------------------------------------------------------------
# SQL VALIDATION
# ---------------------------------------------------------------------------

_BLOCKED = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
    "ATTACH", "DETACH", "COPY", "IMPORT", "LOAD", "PRAGMA",
}


def validate_sql(sql: str, intent: str) -> tuple:
    """Validate generated SQL is safe and matches intent.

    Returns (is_valid: bool, message: str).
    """
    sql_upper = sql.upper()

    # Safety: read-only
    for kw in _BLOCKED:
        # Match whole words only
        if f" {kw} " in f" {sql_upper} " or sql_upper.startswith(f"{kw} "):
            return False, f"Only SELECT queries are allowed (found {kw})."

    if not sql_upper.lstrip().startswith("SELECT"):
        return False, "Query must start with SELECT."

    return True, "OK"
