# Harris Farm Hub -- Current State

**Last Updated:** 2026-02-22

---

## Architecture

- **Frontend:** Streamlit (single multi-page app via `st.navigation()`)
- **Backend:** FastAPI on port 8000 (`backend/app.py`, 112 endpoints)
- **Entry Point:** `dashboards/app.py` -- runs all 23 pages in one process
- **Auth:** `shared/auth_gate.py` -- bcrypt + session tokens, site password option
- **Deployment:** Render (persistent disk, GitHub Releases data loader)
- **Governance:** WATCHDOG 7 Laws, CLAUDE.md SHA-256 verified, `watchdog/audit.log`

---

## Navigation Structure

```
Home (landing.py)
|
+-- For The Greater Goodness (1 page)
|   +-- Greater Goodness
|
+-- Smashing It for the Customer (2 pages)
|   +-- Customers
|   +-- Market Share
|
+-- Growing Legendary Leadership (6 pages)
|   +-- Learning Centre
|   +-- The Paddock
|   +-- Academy
|   +-- Prompt Builder
|   +-- The Rubric
|   +-- Hub Assistant
|
+-- Today's Business, Done Better (8 pages)
|   +-- Sales
|   +-- Profitability
|   +-- Revenue Bridge
|   +-- Store Ops
|   +-- Buying Hub
|   +-- Product Intel
|   +-- PLU Intelligence
|   +-- Transport
|
+-- Tomorrow's Business, Built Better (6 pages)
    +-- Analytics Engine
    +-- Agent Hub
    +-- Agent Operations
    +-- AI Adoption
    +-- Trending
    +-- Mission Control
```

---

## Page Inventory

| Page | File | Goals | Status |
|------|------|-------|--------|
| Home | `landing.py` | All | LIVE |
| Greater Goodness | `greater_goodness.py` | G1 | LIVE |
| Customers | `customer_dashboard.py` | G1, G2 | LIVE |
| Market Share | `market_share_dashboard.py` | G1, G2 | LIVE |
| Learning Centre | `learning_centre.py` | G3 | LIVE |
| The Paddock | `the_paddock.py` | G3 | LIVE |
| Academy | `growing_legends_academy.py` | G3 | LIVE |
| Prompt Builder | `prompt_builder.py` | G2, G3 | LIVE |
| The Rubric | `rubric_dashboard.py` | G3, G5 | LIVE |
| Hub Assistant | `chatbot_dashboard.py` | G2, G3 | LIVE |
| Sales | `sales_dashboard.py` | G1, G2, G4 | LIVE |
| Profitability | `profitability_dashboard.py` | G1, G2, G4 | LIVE |
| Revenue Bridge | `revenue_bridge_dashboard.py` | G1, G2 | LIVE |
| Store Ops | `store_ops_dashboard.py` | G2, G4 | LIVE |
| Buying Hub | `buying_hub_dashboard.py` | G2, G4 | LIVE |
| Product Intel | `product_intel_dashboard.py` | G2, G4 | LIVE |
| PLU Intelligence | `plu_intel_dashboard.py` | G2, G4 | LIVE |
| Transport | `transport_dashboard.py` | G4 | LIVE |
| Analytics Engine | `analytics_engine.py` | G2, G4 | LIVE |
| Agent Hub | `agent_hub.py` | G1, G5 | LIVE |
| Agent Operations | `agent_operations.py` | G1, G5 | LIVE |
| AI Adoption | `ai_adoption/dashboard.py` | G3, G5 | LIVE |
| Trending | `trending_dashboard.py` | G5 | LIVE |
| Mission Control | `hub_portal.py` | G1, G5 | LIVE |

---

## Data Assets

| Asset | Location | Rows | Format |
|-------|----------|------|--------|
| Transactions | Parquet files | 383.6M | DuckDB via `transaction_layer.py` |
| Product Hierarchy | Parquet | 72,911 | DuckDB |
| Fiscal Calendar | Parquet | 4,018 | DuckDB |
| Weekly Sales | `harris_farm.db` | 1.6M+ | SQLite |
| Market Share | `harris_farm.db` | 77K | SQLite |
| Customers | `harris_farm.db` | 17K | SQLite |
| PLU Results | `harris_farm_plu.db` | 27.3M | SQLite |
| Hub State | `hub_data.db` | 35 tables | SQLite |

---

## Front Page (Mission Control)

The landing page (`dashboards/landing.py`) serves as Mission Control with 7 sections:

1. **Mission Statement** -- Green gradient hero banner with personalised greeting
2. **Strategy Pillars** -- "Fewer, Bigger, Better" framing + 5 pillar cards with status (prominent, Section 2)
3. **5 Goals** -- Live progress cards (G1-G5) with metrics from `hub_data.db`
4. **Quick Launch** -- 6 cards linking to key entry points
5. **Activity Feed** -- Recent reports, proposals, findings, WATCHDOG audits
6. **WATCHDOG Trust** -- 7 Laws + radar chart of H/R/S/C/D/U/X quality scores
7. **System Health** -- Collapsible expander with dashboard/endpoint/test counts

## Goal Alignment

Every dashboard shows its goal alignment in the header via `render_header(goals=, strategy_context=)`:
- Coloured goal badges (G1 green, G2 blue, G3 purple, G4 amber, G5 red)
- One-line strategy context connecting the data to "Fewer, Bigger, Better"
- 23 pages tagged with relevant goals
- Function in `shared/styles.py`, backward compatible (goals param optional)

---

## Learning Features

- **Learning Centre** (`learning_centre.py`): 12 modules (L1-L4, D1-D4, K1-K4), 5 tabs
- **Academy** (`growing_legends_academy.py`): 6 maturity levels (Seed to Legend), 7 prompt patterns, 6 learning paths, 5 arena challenges, 8 tabs, site quality rubrics
- **Prompt Builder** (`prompt_builder.py`): 17 templates, structured prompt design
- **Hub Assistant** (`chatbot_dashboard.py`): 545 knowledge base articles, full-text search

---

## Rubric System

- **The Rubric** (`rubric_dashboard.py`): Multi-LLM comparison, 5-building-block scoring
- **5-Tier Evaluation** (`shared/agent_teams.py`): CTO (25) + CLO (25) + Strategic (30) + Implementation (25) + Presentation (25) = 130 max, 110 threshold
- **WATCHDOG Scoring**: H/R/S/C/D/U/X criteria, 7+ average required
- **Site Quality Rubrics** (Academy): Dashboard Quality (7 criteria/35pts), Page Content (5 criteria/25pts)

---

## Supply Chain (Pillar 4)

Seven dashboards serve operations and supply chain:
- Sales, Profitability, Transport -- weekly aggregated data
- Store Ops, Buying Hub, Product Intel -- 383M transaction-level intelligence
- PLU Intelligence -- 27.3M PLU-level wastage, shrinkage, margins

Grant Enders engaged for supply chain transformation. OOS reduction target 20% by Jun 2026.

Agent system runs 11 analysis types including basket, stockout, demand, slow_movers, halo_effect, specials_uplift, margin_analysis.

---

## Self-Improvement System

- Mission Control Tab 4 (Self-Improvement): Score tracking, cycle history, KPI gauges
- `self_improvement.py`: Parses H/R/S/C/D/U/X from audit, stores in `task_scores`
- Auto-triggers improvement proposal every 5 task completions
- MAX 3 attempts per criterion enforced
- 121 improvement findings logged (deduplicated), 29 quality scores recorded

---

## Agent System

- 224 agent proposals tracked in `hub_data.db` (test/zombie rows cleaned)
- 237 agent scores across 18 agents
- 180 intelligence reports with rubric grades
- NL query router with 11 analysis types
- Sequential execution via `agent_executor.py`
- WATCHDOG safety analysis (partial integration)

---

## Known Issues

- WATCHDOG Safety LLM analysis built but not integrated into approval flow
- Risk level auto-assessment field exists but not auto-populated
- Role-Based Access Control designed but not enforced on endpoints
- Arena UI is minimal (tables + API exist, 12 proposals)
- Gamification tables exist but limited data (no user scores logged yet)
