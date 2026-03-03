# Harris Farm Hub -- Current State

**Last Updated:** 2026-02-27

---

## Architecture

- **Frontend:** Streamlit (single multi-page app via `st.navigation()`)
- **Backend:** FastAPI on port 8000 (`backend/app.py`, ~264 endpoints)
- **Entry Point:** `dashboards/app.py` -- runs all 43 pages (including Home) in one process
- **Auth:** `shared/auth_gate.py` → `backend/auth.py` -- bcrypt + session tokens, site password, role-based access
- **Deployment:** Render (persistent disk, GitHub Releases data loader, non-blocking startup)
- **Governance:** WATCHDOG 7 Laws, CLAUDE.md SHA-256 verified, `watchdog/audit.log`
- **Database Tables:** ~105 in `hub_data.db`

---

## Navigation Structure -- 6 Purpose-Based Sections (43 pages)

```
Home (landing.py)
|
+-- Strategy (6 pages)
|   +-- Strategy Overview, Greater Goodness, Growing Legends (intro),
|   +-- Operations HQ (intro), Digital & AI HQ (intro), Way of Working
|
+-- Growing Legends (4 pages)
|   +-- Skills Academy, The Paddock, Prompt Engine, Hub Assistant
|
+-- Operations (10 pages)
|   +-- Customer Hub, Sales, Profitability, Revenue Bridge,
|   +-- Store Ops, Buying Hub, Product Intel, PLU Intelligence,
|   +-- Transport, Analytics Engine
|
+-- Property (7 pages)
|   +-- Store Network, Market Share, Demographics,
|   +-- Whitespace Analysis, Competitor Map, ROCE Analysis, Cannibalisation
|
+-- MDHE (4 pages)
|   +-- MDHE Dashboard, MDHE Upload, MDHE Issues, MDHE Guide
|
+-- Back of House (11 pages)
    +-- The Rubric, Approvals, Workflow Engine, Agent Ops,
    +-- Mission Control, AI Adoption, Adoption, Trending,
    +-- Agent Hub, Marketing Assets, User Management
```

---

## Page Inventory

| Page | File | Section | Status |
|------|------|---------|--------|
| Home | `landing.py` | -- | LIVE |
| Strategy Overview | `strategy_overview.py` | Strategy | LIVE |
| Greater Goodness | `greater_goodness.py` | Strategy | LIVE |
| Growing Legends (intro) | `intro_p3_people.py` | Strategy | LIVE |
| Operations HQ (intro) | `intro_p4_operations.py` | Strategy | LIVE |
| Digital & AI HQ (intro) | `intro_p5_digital.py` | Strategy | LIVE |
| Way of Working | `way_of_working/dashboard.py` | Strategy | LIVE |
| Skills Academy | `skills_academy.py` | Growing Legends | LIVE |
| The Paddock | `the_paddock.py` | Growing Legends | LIVE |
| Prompt Engine | `prompt_builder.py` | Growing Legends | LIVE |
| Hub Assistant | `chatbot_dashboard.py` | Growing Legends | LIVE |
| Customer Hub | `customer_hub/dashboard.py` | Operations | LIVE |
| Sales | `sales_dashboard.py` | Operations | LIVE |
| Profitability | `profitability_dashboard.py` | Operations | LIVE |
| Revenue Bridge | `revenue_bridge_dashboard.py` | Operations | LIVE |
| Store Ops | `store_ops_dashboard.py` | Operations | LIVE |
| Buying Hub | `buying_hub_dashboard.py` | Operations | LIVE |
| Product Intel | `product_intel_dashboard.py` | Operations | LIVE |
| PLU Intelligence | `plu_intel_dashboard.py` | Operations | LIVE |
| Transport | `transport_dashboard.py` | Operations | LIVE |
| Analytics Engine | `analytics_engine.py` | Operations | LIVE |
| Store Network | `store_network_page.py` | Property | LIVE |
| Market Share | `market_share_dashboard.py` | Property | LIVE |
| Demographics | `demographics_page.py` | Property | LIVE |
| Whitespace Analysis | `whitespace_analysis.py` | Property | LIVE |
| Competitor Map | `competitor_map_page.py` | Property | PLACEHOLDER |
| ROCE Analysis | `roce_dashboard.py` | Property | LIVE |
| Cannibalisation | `cannibalisation_dashboard.py` | Property | LIVE |
| MDHE Dashboard | `mdhe/dashboard.py` | MDHE | LIVE |
| MDHE Upload | `mdhe/upload.py` | MDHE | LIVE |
| MDHE Issues | `mdhe/issues.py` | MDHE | LIVE |
| MDHE Guide | `mdhe/guide.py` | MDHE | LIVE |
| The Rubric | `rubric_dashboard.py` | Back of House | LIVE |
| Approvals | `approvals_dashboard.py` | Back of House | LIVE |
| Workflow Engine | `workflow_engine.py` | Back of House | LIVE |
| Agent Ops | `agent_operations.py` | Back of House | LIVE |
| Mission Control | `hub_portal.py` | Back of House | LIVE |
| AI Adoption | `ai_adoption/dashboard.py` | Back of House | LIVE |
| Adoption | `adoption_dashboard.py` | Back of House | LIVE |
| Trending | `trending_dashboard.py` | Back of House | LIVE |
| Agent Hub | `agent_hub.py` | Back of House | LIVE |
| Marketing Assets | `marketing_assets.py` | Back of House | LIVE |
| User Management | `mdhe/user_management.py` | Back of House | LIVE |

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
| Hub State | `hub_data.db` | ~105 tables | SQLite |
| Census | `data/census/processed/` | -- | ABS SA1-to-postcode demographic data |
| CBAS Network | `data/cbas_network.json` | 31 stores, 16 whitespace | JSON |
| Property Intel | `data/outputs/roc/`, `market_share/`, `demographics/` | -- | CSV/Parquet |

---

## Role-Based Access Control

- **10 roles:** admin, user, executive, store_manager, buyer, marketing, people_culture, finance, data_quality, viewer
- **Defined in:** `dashboards/shared/role_config.py`
- **SLT auto-promotion:** Members listed in `AUTH_SLT_EMAILS` env var are auto-promoted to admin on login
- **Enforcement:** Role checks applied at navigation level -- pages are shown/hidden based on user role

### Access Matrix

| Section | admin | executive | user | store_manager | buyer | finance | data_quality | viewer |
|---------|-------|-----------|------|---------------|-------|---------|--------------|--------|
| Strategy | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Growing Legends | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Operations (general) | Yes | Yes | Yes | Yes | Yes | Partial | Partial | Partial |
| Operations (financial) | Yes | Yes | No | No | No | No | No | No |
| Property | Yes | Yes | No | No | No | No | No | No |
| MDHE | Yes | Yes | Yes | Partial | Partial | Partial | Yes | No |
| Back of House | Yes | Yes | Partial | Partial | Partial | Partial | Partial | No |
| User Management | Yes | No | No | No | No | No | No | No |

Financial data (Sales, Profitability, Revenue Bridge) and Property data (Store Network, Market Share, Demographics, Whitespace, ROCE, Cannibalisation) are restricted to admin and executive roles only.

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
- 43 pages tagged with relevant goals
- Function in `shared/styles.py`, backward compatible (goals param optional)

---

## MDHE -- Master Data Health Engine

The MDHE is a 4-page data quality system with a backend validation engine.

### Pages

- **MDHE Dashboard** (`mdhe/dashboard.py`): 5-tab health score overview across all data domains
- **MDHE Upload** (`mdhe/upload.py`): Data upload and ingestion pipeline
- **MDHE Issues** (`mdhe/issues.py`): Issue tracker for data quality problems
- **MDHE Guide** (`mdhe/guide.py`): Team documentation and onboarding

### Architecture

- **4-layer validation:** Rules (35%), Standards (30%), AI (20%), Reconciliation (15%)
- **5 domains scored:** PLU, Barcode, Pricing, Hierarchy, Supplier
- **Frontend:** `dashboards/mdhe/` (dashboard.py, upload.py, issues.py, guide.py, engine.py, user_management.py)
- **Backend:** `backend/mdhe_db.py`, `backend/mdhe_api.py`
- **Database:** 6 tables in `hub_data.db` (mdhe_data_sources, mdhe_validations, mdhe_scores, mdhe_issues, mdhe_scan_results, mdhe_plu_master)

---

## Property Intelligence Engine

The Property Intelligence Engine provides location analytics, demographic profiling, and expansion planning across 7 pages.

### Pages

- **Store Network** (`store_network_page.py`): 8 tabs -- network overview, individual store profiles, trade area analysis
- **Market Share** (`market_share_dashboard.py`): Postcode-level CBAS market share analysis
- **Demographics** (`demographics_page.py`): 6 tabs -- ABS census demographic profiling by postcode
- **Whitespace Analysis** (`whitespace_analysis.py`): 6 tabs -- expansion opportunity identification
- **Competitor Map** (`competitor_map_page.py`): Placeholder -- competitive landscape mapping
- **ROCE Analysis** (`roce_dashboard.py`): Return on capital employed by store
- **Cannibalisation** (`cannibalisation_dashboard.py`): Store overlap and cannibalisation risk

### Data Pipeline

- **Data modules:** `shared/property_intel.py`, `shared/demographic_intel.py`, `shared/whitespace_data.py`
- **Census processing:** `scripts/process_census.py` (ABS SA1 to postcode), `scripts/demographic_scoring.py`
- **Data outputs:** `data/outputs/roc/`, `data/outputs/market_share/`, `data/outputs/demographics/`
- **Census data:** `data/census/processed/` (4 parquet/csv files, 2.8MB) -- raw zips in gitignore
- **CBAS network:** `data/cbas_network.json` (31 stores, 16 whitespace opportunities)
- **ROC analysis:** Ring of Confidence scoring for store trade areas

---

## Learning Features

- **Skills Academy** (`skills_academy.py`): 6 maturity levels (Seed to Legend), 7 prompt patterns, 6 learning paths, 5 arena challenges, 10 tabs, site quality rubrics. **Gamification Engine:** XP system (13 action types, 6 levels), streak tracking (1.0-2.0x multiplier), 60 daily challenges, 21 badges, leaderboard. Backend: `academy_engine.py`, 5 tables, 10 `/api/academy/` endpoints.
- **The Paddock** (`the_paddock.py`): AI practice conversations -- structured prompt practice environment
- **Prompt Engine** (`prompt_builder.py`): 20 role-filtered task templates, PtA workflow (generate, score, iterate, annotate, submit, approve)
- **Approvals** (`approvals_dashboard.py`): Managers review, approve, or request changes on PtA submissions
- **Hub Assistant** (`chatbot_dashboard.py`): 545 knowledge base articles, full-text search + RAG chat

---

## Rubric System

- **The Rubric** (`rubric_dashboard.py`): Multi-LLM comparison, 5-building-block scoring
- **PtA Rubric Engine** (`shared/pta_rubric.py`): 8-criteria standard (AF, ST, AC, VQ, CO, BR, DI, HO) + 5-tier advanced. Verdicts: SHIP (8.0+), REVISE (5.0-7.9), REJECT (<5.0)
- **5-Tier Evaluation** (`shared/agent_teams.py`): CTO (25) + CLO (25) + Strategic (30) + Implementation (25) + Presentation (25) = 130 max, 110 threshold
- **WATCHDOG Scoring**: H/R/S/C/D/U/X criteria, 7+ average required
- **Site Quality Rubrics** (Academy): Dashboard Quality (7 criteria/35pts), Page Content (5 criteria/25pts)

---

## Supply Chain (Operations)

Ten dashboards serve operations and supply chain:
- Customer Hub, Sales, Profitability, Revenue Bridge -- customer and financial intelligence
- Store Ops, Buying Hub, Product Intel -- 383M transaction-level intelligence
- PLU Intelligence -- 27.3M PLU-level wastage, shrinkage, margins
- Transport -- logistics and delivery operations
- Analytics Engine -- natural language query interface

Grant Enders engaged for supply chain transformation. OOS reduction target 20% by Jun 2026.

Agent system runs 11 analysis types including basket, stockout, demand, slow_movers, halo_effect, specials_uplift, margin_analysis.

---

## Workflow Engine

- **Workflow Engine** (`workflow_engine.py`): 4P state machine for proposal lifecycle management
- Supports multi-stage approval workflows with role-based routing
- Integrates with PtA system and agent proposals

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

## Prompt-to-Approval System

The PtA system is the core workflow for making Harris Farm a data-first business. Every person starts with the Prompt Engine, generates AI output, scores it against the 8-criteria rubric, iterates with human context, and submits for approval.

- **20 task templates** across 11 roles (store performance, waste analysis, board paper, category review, etc.)
- **8-criteria rubric**: Audience Fit, Storytelling, Actionability, Visual Quality, Completeness, Brevity, Data Integrity, Honesty
- **5-tier advanced rubric**: CTO Panel, CLO Panel, Strategic Alignment, Implementation Readiness, Presentation Quality
- **Approval routing**: L1 Team, L2 Department, L3 Executive, L4 Board (mapped by role)
- **AI Ninja gamification**: Prompt Apprentice (0-100pts), Specialist (101-500), Master (501-2000), AI Ninja (2001+)
- **10 API endpoints**: generate, score, submit, list/get submissions, approve, request-changes, user-stats, leaderboard
- **3 database tables**: pta_submissions, pta_audit_log, pta_points_log
- **Auto-save**: Prompts scoring 9.0+ auto-saved to library with 200 bonus points

---

## Known Issues

- WATCHDOG Safety LLM analysis built but not integrated into approval flow
- Risk level auto-assessment field exists but not auto-populated
- Competitor Map page is placeholder only -- no data integration yet
- Arena UI is minimal (tables + API exist, 12 proposals)
- PtA data validation layer is directional (confidence badges) -- not yet cross-source validated
- PtA email notifications on approval not yet implemented
- PtA escalation workflow placeholder only ("Coming soon")
- Market Share page uses CBAS modelled estimates -- dollar values are directional, not actual revenue
