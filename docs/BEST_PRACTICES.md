# Centre of Excellence — Best Practices Guide
**Harris Farm Markets AI Hub**

*Last Updated: 2026-02-18*
*Status: Living Document — Updated with each major learning*

---

## Table of Contents
1. [Architecture Patterns](#1-architecture-patterns)
2. [Data Engineering](#2-data-engineering)
3. [Agent Development](#3-agent-development)
4. [Safety & Approval Workflows](#4-safety--approval-workflows)
5. [Testing Strategy](#5-testing-strategy)
6. [Dashboard Development](#6-dashboard-development)
7. [Performance Optimisation](#7-performance-optimisation)
8. [Self-Improvement Mechanisms](#8-self-improvement-mechanisms)

---

## 1. Architecture Patterns

### 1.1 FastAPI Backend + Streamlit Frontends

The Hub uses a single FastAPI backend (`backend/app.py`, ~5000 lines, ~103 endpoints) serving 24 Streamlit dashboards via a single `st.navigation()` app. This is deliberate — not a monolith problem.

**Why one backend file works (for now):**
- Single source of truth for database init, config, and all endpoints
- Easy to search and cross-reference
- No circular import issues between modules
- When it gets unwieldy, split by domain (auth, transactions, intelligence, admin)

**Pattern: Streamlit dashboards call the API, never import backend directly.**

```python
# dashboards/sales_dashboard.py — CORRECT
resp = requests.get("{}/api/transactions/summary".format(API_URL), params={...})
data = resp.json()

# WRONG — don't import backend modules into dashboards
# from backend.data_analysis import run_demand_pattern
```

**Exception:** Shared dashboard utilities (`dashboards/shared/`) are fine to import across dashboards.

### 1.2 Hub Navigation Pattern

All 24 pages share navigation via `dashboards/app.py` (`st.navigation()`):

```python
HUBS = {
    "Financial":    {"color": "#1e3a8a", "icon": "...", "dashboards": {8501: "Sales", 8502: "Profitability"}},
    "Market Intel":  {"color": "#7c3aed", "icon": "...", "dashboards": {8507: "Customers", 8508: "Market Share"}},
    ...
}
```

**To add a new dashboard:** Add an entry to the appropriate hub in `HUBS`, create the dashboard file, add its port to `start.sh`. The nav renders automatically.

### 1.3 Database Strategy: SQLite + DuckDB

| Database | Purpose | Location | Size |
|----------|---------|----------|------|
| hub_data.db | Metadata, agents, learning, knowledge | `backend/hub_data.db` | 3.2MB |
| harris_farm.db | Weekly aggregated sales/customers/share | `data/harris_farm.db` | 399MB |
| DuckDB (in-memory) | 383.6M POS transactions from Parquet | `~/Desktop/.../raw/*.parquet` | 6.6GB |

**Key learning:** hub_data.db lives in `backend/`, not `data/`. The `data/` directory has a stale 0-byte copy. Always reference `config.HUB_DB`.

**DuckDB pattern:** Load Parquet + reference tables into an in-memory DuckDB connection, then run analytical SQL. This avoids importing 6.6GB into SQLite.

```python
# backend/transaction_layer.py
conn = duckdb.connect()
conn.execute("CREATE TABLE product_hierarchy AS SELECT * FROM read_parquet(?)", [parquet_path])
conn.execute("CREATE TABLE fiscal_calendar AS SELECT * FROM read_parquet(?)", [fc_path])
# Then JOIN transaction parquet files against these reference tables
```

---

## 2. Data Engineering

### 2.1 Parquet as Source of Truth

Three data assets are stored as Parquet files and loaded into DuckDB at query time:

| Asset | File | Rows | Columns |
|-------|------|------|---------|
| Transactions | `~/Desktop/.../raw/FY2{4,5,6}*.parquet` | 383.6M | 9 |
| Product Hierarchy | `data/product_hierarchy.parquet` | 72,911 | 19 |
| Fiscal Calendar | `data/fiscal_calendar_daily.parquet` | 4,018 | 45 |

**Why Parquet:** Columnar format, compressed, fast DuckDB reads, no import step needed. Excel originals are preserved but never queried directly.

### 2.2 JOIN Strategy

The three datasets connect via:

```sql
-- Transaction → Product: PLU match (98.3% coverage)
t.PLUItem_ID = ph.ProductNumber

-- Transaction → Fiscal Calendar: Date match (100% coverage)
CAST(t.SaleDate AS DATE) = fc.TheDate
```

**Critical:** SaleDate is UTC. All hourly analysis must add AEST offset:
```sql
EXTRACT(HOUR FROM t.SaleDate + INTERVAL '11' HOUR) AS hour_aest
```

### 2.3 Fiscal Calendar: 5-4-4 Pattern

Harris Farm uses a **5-4-4 retail calendar** (NOT 4-5-4):
- Each quarter = 13 weeks = 5 + 4 + 4 weeks
- Weeks run Monday-Sunday
- FY starts on the Monday nearest July 1
- 53-week years: FY2016 and FY2022 only

**Financial months are NOT calendar months.** "Financial July 2026" = 2025-06-30 to 2025-08-03. Always use the fiscal calendar table for period boundaries.

### 2.4 Query Library Pattern

`backend/transaction_queries.py` provides 41 pre-built SQL queries with metadata:

```python
QUERIES = {
    "hourly_sales": {
        "name": "Hourly Sales Pattern",
        "sql": "SELECT ... FROM read_parquet(...) ...",
        "params": ["store_id", "days"],
        "description": "Hourly revenue pattern for a store",
    },
    ...
}
```

**Benefits:** Queries are version-controlled, documented, reusable. Dashboards call them by name rather than embedding SQL.

### 2.5 Data Correctness Rules

From `watchdog/procedures/data_correctness.md`:

1. Log source query + row count before displaying any number
2. Cross-validate against control totals
3. Range check: no negative revenue, no future dates, quantity < 100K
4. Null check: flag nulls, never silently drop
5. Float tolerance: ±0.01 for financial figures
6. Validation fail → do NOT display → show reason → alert operator

---

## 3. Agent Development

### 3.1 Agent Naming Convention

**Pattern:** `{Function}{Type}` — the name describes what the agent does.

| Agent | Analyses | Description |
|-------|----------|-------------|
| StockoutAnalyzer | intraday_stockout, stockout_detection | Identifies products that ran out |
| BasketAnalyzer | basket_analysis | Cross-sell and market basket |
| DemandAnalyzer | demand_pattern | Peak/trough demand periods |
| PriceAnalyzer | price_dispersion | Price variation across stores |
| SlowMoverAnalyzer | slow_movers | Underperforming products |
| ReportGenerator | demand_pattern | Synthesises findings |
| HaloAnalyzer | halo_effect | Products that lift basket value when present |
| SpecialsAnalyzer | specials_uplift | Forecast demand uplift for price-drop specials |
| MarginAnalyzer | margin_analysis | Products with GP% below department average |
| CustomerAnalyzer | customer_analysis | RFM segmentation of loyalty customers |
| StoreBenchmarkAnalyzer | store_benchmark | All-store KPI ranking with percentiles |

### 3.2 Agent Routing: Deterministic, Not LLM

The Hub routes tasks to agents using keyword matching, not LLM calls. This is fast, predictable, and auditable.

**`backend/agent_router.py`** — NL query routing:
```python
KEYWORD_MAP = {
    "basket_analysis": {"keywords": ["basket", "cross-sell", "bought together", "pair", "bundle"], "weight": 1.0},
    "intraday_stockout": {"keywords": ["intra-day", "hourly", "run out", "during the day", "abnormal"], "weight": 1.2},
    "halo_effect": {"keywords": ["halo", "basket grow", "basket value", "basket lift", "basket builder"], "weight": 1.0},
    "specials_uplift": {"keywords": ["special", "price drop", "uplift", "forecast demand", "promo", "on special"], "weight": 1.0},
    "margin_analysis": {"keywords": ["margin", "wastage", "gp%", "gross profit", "erosion", "cogs"], "weight": 1.0},
    "customer_analysis": {"keywords": ["customer", "segment", "rfm", "loyalty", "retention", "lapsed"], "weight": 1.0},
    "store_benchmark": {"keywords": ["benchmark", "store compar", "store rank", "league table", "kpi"], "weight": 1.0},
    ...
}
```

**`backend/agent_executor.py`** — Proposal routing:
```python
AGENT_ANALYSIS_MAP = {
    "StockoutAnalyzer": ["intraday_stockout", "stockout_detection"],
    "BasketAnalyzer": ["basket_analysis"],
    "HaloAnalyzer": ["halo_effect"],
    "SpecialsAnalyzer": ["specials_uplift"],
    "MarginAnalyzer": ["margin_analysis"],
    "CustomerAnalyzer": ["customer_analysis"],
    "StoreBenchmarkAnalyzer": ["store_benchmark"],
    ...
}
```

**Fallback:** Unknown queries/proposals default to `demand_pattern` (safe, always produces results).

### 3.3 Analysis Function Pattern

Every analysis in `backend/data_analysis.py` follows the same structure:

```python
def run_basket_analysis(store_id=None, days=14, limit=50):
    """Run basket analysis against real transaction data."""
    conn = _get_connection()  # DuckDB with parquet + reference tables

    # 1. Build SQL with CTEs
    sql = """
        WITH baskets AS (...),
        pairs AS (...),
        lift AS (...)
        SELECT ... FROM lift ORDER BY lift_score DESC LIMIT ?
    """

    # 2. Execute and collect results
    results = conn.execute(sql, [store_id, days, limit]).fetchall()

    # 3. Return standardised result dict via _build_result()
    return _build_result(
        analysis_type="basket_analysis",
        title="Cross-sell Opportunities — {} ({} days)".format(store_name, days),
        executive_summary="Found {} product pairs...".format(len(results)),
        findings=[...],
        evidence_tables=[{"headers": [...], "rows": [...]}],
        financial_impact={"estimated_revenue_uplift": ...},
        recommendations=[{"action": "...", "priority": "HIGH"}],
        methodology={"approach": "Market basket analysis with lift scoring"},
        confidence_level=0.85,
    )
```

**`_build_result()`** ensures every analysis returns a consistent dict that the presentation rubric can score.

### 3.4 PLU Resolution & Check Digit Handling

POS systems append a check digit to weighed/priced items — a 5-digit PLU in the product hierarchy appears as a 6-digit PLU in transaction data (e.g., `502771` in POS = `50277` in hierarchy = "BEEF PORTERHOUSE STEAK").

`product_hierarchy.py:get_product_by_plu()` handles this with progressive truncation:

```python
# Exact match first
match = df[df["ProductNumber"] == plu]
# Fallback: truncate trailing digits (check digit / price suffix)
if match.empty and len(plu) >= 5:
    for trim in range(1, 3):  # try removing 1 then 2 digits
        truncated = plu[: len(plu) - trim]
        match = df[df["ProductNumber"] == truncated]
        if not match.empty:
            break
```

**When to use this pattern:** Any code resolving PLU numbers from POS data to product names should call `get_product_by_plu()` rather than doing a direct exact match.

### 3.5 Execution Pipeline

```
Approved Proposal → route_proposal() → execute_analysis() → score_result() → store_report() → mark_completed()
```

Each step is a separate function. If any step fails, `mark_failed()` records the error. The rubric scores every result on 8 dimensions.

---

## 4. Safety & Approval Workflows

### 4.1 WATCHDOG Governance (7 Laws)

Every session and task is governed by `CLAUDE.md`:

1. **Honest code** — behaviour matches names
2. **Full audit trail** — watchdog/audit.log, no gaps
3. **Test before ship** — min 1 success + 1 failure per function
4. **Zero secrets in code** — .env only
5. **Operator authority** — Gus Harris only
6. **Data correctness** — every number traceable to source ±0.01
7. **Document everything** — no undocumented features

### 4.2 Human-in-the-Loop Task Flow

```
Agent creates proposal (status=PENDING)
    ↓
Human reviews in Agent Control tab
    ↓
Approve (status=APPROVED) or Reject (status=REJECTED, notes required)
    ↓
Executor picks up APPROVED proposals
    ↓
Routes to real analysis functions (383M POS transactions)
    ↓
Scores with presentation rubric
    ↓
Stores in intelligence_reports
    ↓
Marks COMPLETED with execution_result summary
```

**Never bypass this flow.** Even read-only analysis goes through approval.

### 4.3 Task Status State Machine

```
PENDING → APPROVED → COMPLETED
   ↓                     ↓
REJECTED              FAILED
```

Valid statuses enforced by CHECK constraint in SQLite.

### 4.4 7-Criteria Scoring (H/R/S/C/D/U/X)

Every task is scored on 7 dimensions, each 0-10:

| Code | Criterion | What it measures |
|------|-----------|-----------------|
| H | Honest | Behaviour matches names, no deception |
| R | Reliable | Tests pass, consistent results |
| S | Safe | No secrets, sandboxed operations |
| C | Clean | Code quality, no dead code |
| D | Data Correct | Numbers traceable to source |
| U | Usable | User can accomplish their goal |
| X | Documented | Features have docs |

**Threshold:** Average ≥ 7, none below 5. Tasks scoring below threshold trigger self-improvement.

### 4.5 Audit Logging

Every action logs to `watchdog/audit.log`:
```
[2026-02-17 01:35] TASK: Agent Executor | STATUS: COMPLETE | DETAILS: ... | SCORES: H=9 R=9 S=8 C=8 D=9 U=9 X=8 avg=8.6
```

Also logged to `task_scores` table for structured querying:
```sql
SELECT criterion, AVG(score) FROM task_scores GROUP BY criterion
```

---

## 5. Testing Strategy

### 5.1 Test Requirements

From CLAUDE.md Law 3: **min 1 success + 1 failure per function**.

Current: **1,003 tests** across 25 files. Run with:
```bash
python3 -m pytest tests/ -v
```

### 5.2 Test Organisation

| Test File | What it covers |
|-----------|---------------|
| test_agent_executor.py | Routing, DB helpers, API endpoints, improvement triggers |
| test_agent_control.py | Proposals table, seeding, approve/reject API |
| test_agent_tasks.py | NL router, intraday stockout, agent task API |
| test_transactions.py | 383M row queries, DuckDB layer |
| test_data_analysis.py | 8 analysis types, registry, result structure |
| test_self_improvement.py | Score parsing, averages, weakest criterion, cycles |
| test_watchdog_scanner.py | AST-based Streamlit scanner (20 tests) |
| test_auth.py | Password hashing, sessions, RBAC |

### 5.3 Testing Pattern

```python
class TestRouteProposal:
    """Test the route_proposal() function."""

    def test_route_stockout_analyzer(self):
        """Success: known agent maps correctly."""
        from agent_executor import route_proposal
        result = route_proposal({"agent_name": "StockoutAnalyzer"})
        assert "intraday_stockout" in result

    def test_route_empty_proposal(self):
        """Failure case: empty input still returns a valid list."""
        from agent_executor import route_proposal
        result = route_proposal({})
        assert isinstance(result, list)
        assert len(result) >= 1
```

### 5.4 Python 3.9 Compatibility

The system runs on Python 3.9. Key constraints:
- No `dict | None` type unions — use `Optional[dict]` or omit annotation
- No `match` statements — use if/elif chains
- Use `.format()` strings, not f-strings in some contexts
- Streamlit not on PATH — use full path: `/Users/angusharris/Library/Python/3.9/bin/streamlit`

---

## 6. Dashboard Development

### 6.1 Streamlit Cache Pattern

Every dashboard caches API calls with TTL:

```python
@st.cache_data(ttl=60)
def _fetch_sales_summary(store_id, days):
    resp = requests.get(
        "{}/api/transactions/summary".format(API_URL),
        params={"store_id": store_id, "days": days},
        timeout=10,
    )
    return resp.json() if resp.ok else {}
```

**TTL guidelines:**
- 30s for rapidly changing data (executor status, task queue)
- 60s for standard dashboards
- 300s for reference data (product hierarchy, fiscal calendar)

### 6.2 Shared Components

`dashboards/shared/` contains reusable components:

| Module | Purpose |
|--------|---------|
| `data_access.py` | Centralised query functions for SQLite data |
| `fiscal_selector.py` | Reusable FY/Quarter/Month/Week/Custom selector |
| `styles.py` | Shared CSS and styling |
| `learning_content.py` | Learning module content |
| `training_content.py` | Training curriculum |
| `watchdog_safety.py` | WATCHDOG safety analysis |
| `auth_gate.py` | Authentication gate for dashboards |

### 6.3 WATCHDOG Scanner

`scripts/watchdog.py` is an AST-based scanner that checks all Streamlit dashboards:

```bash
python3 scripts/watchdog.py --report   # Full scan of all dashboards
python3 scripts/watchdog.py --check dashboards/sales_dashboard.py  # Single file
```

Detects: nested expanders (including cross-function), component inventory, API call patterns. 23 pages scanned, 134 components inventoried.

---

## 7. Performance Optimisation

### 7.1 DuckDB Query Performance

DuckDB queries against 383.6M rows typically complete in 2-15 seconds. Key optimisations:

- **Filter early:** Push WHERE clauses into CTEs, don't filter in Python
- **Limit results:** Always use `LIMIT` for evidence tables (typically 50)
- **Single store:** Most analyses scope to one store at a time
- **Time windows:** Default to 14-30 days, not full history

### 7.2 Database Indexing

hub_data.db indexes:
```sql
CREATE INDEX idx_at_status ON agent_tasks(status);
CREATE INDEX idx_proposals_status ON agent_proposals(status);
CREATE INDEX idx_scores_agent_time ON agent_scores(agent_name, timestamp DESC);
```

### 7.3 Executor Polling

The agent executor polls every 30 seconds (configurable via `EXECUTOR_POLL_INTERVAL` env var). For current volume (~100 tasks/day), polling is sufficient.

**When to switch to event-driven:** Task volume > 1000/day or latency requirements < 5 seconds.

---

## 8. Self-Improvement Mechanisms

### 8.1 The Self-Improvement Loop

```
Agent completes task
    ↓
Log performance score (H/R/S/C/D/U/X)
    ↓
Every 5 completions → SelfImprovementEngine triggers
    ↓
Analyses recent performance, identifies weakest criterion
    ↓
Proposes improvement (status=PENDING)
    ↓
Human approves → improvement applied
    ↓
MAX 3 ATTEMPTS per criterion per cycle
```

**Implementation:** `backend/self_improvement.py` parses scores from both audit.log and the task_scores table, calculates averages, and identifies the weakest criterion.

### 8.2 Score Tracking

Raw scores stored in `task_scores` table (never aggregated, always queryable):

```sql
-- Find weakest criterion across recent tasks
SELECT 'H' as criterion, AVG(h) as avg FROM task_scores
UNION ALL SELECT 'R', AVG(r) FROM task_scores
...
ORDER BY avg ASC LIMIT 1
```

### 8.3 Improvement Triggers

`agent_executor.py` checks after every proposal completion:

```python
def check_improvement_trigger(agent_name):
    count = get_completed_count(agent_name)
    if count > 0 and count % 5 == 0 and no_pending_improvement(agent_name):
        create_improvement_proposal(agent_name, count)
```

This creates a PENDING proposal for SelfImprovementEngine, which goes through the normal approval flow.

---

## Appendix: Key File Paths

| File | Purpose |
|------|---------|
| `backend/app.py` | Primary backend (~4600 lines, 112 endpoints) |
| `backend/agent_executor.py` | Executes approved proposals |
| `backend/agent_router.py` | NL query → analysis type routing |
| `backend/data_analysis.py` | 11 analysis types against 383M transactions |
| `backend/self_improvement.py` | Score tracking and improvement engine |
| `backend/transaction_layer.py` | DuckDB query engine |
| `backend/transaction_queries.py` | 41 pre-built SQL queries |
| `backend/product_hierarchy.py` | 72,911 product browser |
| `backend/fiscal_calendar.py` | 5-4-4 retail calendar utilities |
| `dashboards/nav.py` | Hub navigation (5 pillars, 23 pages) |
| `dashboards/shared/` | Shared components (data access, fiscal selector, styles) |
| `CLAUDE.md` | 7 Laws governing all development |
| `watchdog/procedures/` | 4 core operational procedures |
| `watchdog/audit.log` | Full audit trail |
