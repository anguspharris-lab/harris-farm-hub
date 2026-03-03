# Harris Farm Hub — Complete Technical Documentation

> **Last Updated:** 2026-03-03 | **Version:** v4.0 | **Status:** Production (Render)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [All 43 Pages by Section](#3-all-43-pages-by-section)
4. [Backend API (254 Endpoints)](#4-backend-api-254-endpoints)
5. [Data Layer](#5-data-layer)
6. [Authentication & Roles](#6-authentication--roles)
7. [Design System](#7-design-system)
8. [Shared Modules (40 Components)](#8-shared-modules-40-components)
9. [Backend Modules (38 Files)](#9-backend-modules-38-files)
10. [Gamification & XP System](#10-gamification--xp-system)
11. [WATCHDOG Safety System](#11-watchdog-safety-system)
12. [Deployment (Render)](#12-deployment-render)
13. [Local Development](#13-local-development)
14. [External Services](#14-external-services)
15. [Critical Technical Patterns](#15-critical-technical-patterns)
16. [Key Statistics](#16-key-statistics)
17. [File Inventory](#17-file-inventory)

---

## 1. Overview

The Harris Farm Hub is an **AI Centre of Excellence** — a single multi-page Streamlit application backed by a FastAPI server, serving 43 pages across 6 strategic sections. It powers trading intelligence, property analytics, learning & development, data quality governance, and AI adoption across Harris Farm Markets' 21-store network.

| Attribute | Value |
|-----------|-------|
| **Live URL** | https://harris-farm-hub.onrender.com |
| **Strategy** | "Fewer, Bigger, Better" — 5 pillars, Vision 2030 |
| **Brand** | Dark green-black theme, "For The Greater Goodness" |
| **GitHub** | anguspharris-lab/harris-farm-hub (main branch) |
| **Stack** | Streamlit + FastAPI + SQLite + DuckDB + Parquet |
| **Data Scale** | 383M POS transactions, 27.3M PLU records, 17K customers |
| **Store Network** | 21 stores across 9 Sydney regions |

---

## 2. Architecture

```
Browser (any device)
    │
    ▼
Streamlit Multi-Page App (port 8500 local / $PORT on Render)
    dashboards/app.py
    ├── Auth Gate (shared/auth_gate.py → require_login())
    ├── Role-Based Page Filtering (shared/role_config.py)
    ├── st.navigation() → 43 pages across 6 sections
    ├── Dark Navy Styling (shared/styles.py)
    └── Sidebar: Role selector + Academy XP widget
    │
    ▼ HTTP (localhost:8000)
FastAPI Backend (port 8000)
    backend/app.py
    ├── ~254 API endpoints
    ├── Auth (bcrypt, session tokens, role management)
    ├── Natural language query engine (Claude/GPT)
    ├── Multi-LLM orchestration (Claude, GPT, Grok)
    ├── MDHE validation engine
    ├── Skills Academy v4 engine
    ├── Transaction query engine (DuckDB)
    └── WATCHDOG scheduler
    │
    ▼
Data Layer
    ├── harris_farm.db      (SQLite, 418MB)  — weekly sales, customers, market share
    ├── harris_farm_plu.db  (SQLite, 3.1GB)  — PLU weekly results (27.3M rows)
    ├── FY24/25/26.parquet  (DuckDB)         — 383M POS transactions
    ├── hub_data.db         (SQLite, ~105 tables) — app state, gamification, KB, MDHE
    ├── auth.db             (SQLite)         — user accounts & sessions
    └── census/             (parquet/csv)    — ABS demographic data
```

### Key Design Decisions

1. **Single `st.navigation()` app** — one process, shared session, one port (replaced 17 separate processes)
2. **Auth gate in app.py only** — `require_login()` runs once before any page renders
3. **Session trust** — token trusted from `st.session_state` without re-verifying on every page
4. **DuckDB for transactions** — zero-copy parquet reader, queries 383M rows in seconds
5. **Non-blocking startup** — Streamlit serves pages immediately while backend initialises
6. **GitHub Releases for data** — large files stored as release assets, auto-downloaded on first deploy
7. **5-4-4 fiscal calendar** — all date logic uses Harris Farm's fiscal calendar (Jul-Jun)

---

## 3. All 43 Pages by Section

### Strategy (6 pages)

| Page | File | Purpose | Data Source |
|------|------|---------|-------------|
| Home | `landing.py` | "Harris Farming It" philosophy, 4 doors, AI-First Method | Static |
| Strategy Overview | `strategy_overview.py` | 5 pillars, initiatives, 5 goals | Static |
| Greater Goodness | `greater_goodness.py` | Pillar 1 — Purpose & Sustainability | Static |
| Growing Legends | `intro_p3_people.py` | Pillar 3 intro — People development | Static |
| Operations HQ | `intro_p4_operations.py` | Pillar 4 intro — Supply chain & ops | Static |
| Digital & AI HQ | `intro_p5_digital.py` | Pillar 5 intro — AI & digital systems | Static |

*Way of Working (`way_of_working/dashboard.py`) may also appear here — initiative tracker via Monday.com API.*

### Growing Legends (4 pages)

| Page | File | Purpose | Data Source |
|------|------|---------|-------------|
| Skills Academy | `skills_academy.py` | 6-level gamification (Seed → Legend), L-Series + D-Series | hub_data.db, XP API |
| The Paddock | `the_paddock.py` | Progressive AI challenges — one wrong = game over | Paddock API |
| Hub Assistant | `chatbot_dashboard.py` | RAG knowledge base chat (545+ articles) | hub_data.db KB |
| Prompt Builder | `prompt_builder.py` | Prompt Engine + PtA workflow, 20 task templates | hub_data.db |

### Operations (10 pages)

| Page | File | Purpose | Data Source |
|------|------|---------|-------------|
| Customer Hub | `customer_hub/dashboard.py` | 5-tab customer insights (Overview, Known, Channel, Cohort, By Store) | Transactions (DuckDB) |
| Sales | `sales_dashboard.py` | Revenue, store performance, trends | harris_farm.db |
| Profitability | `profitability_dashboard.py` | GP analysis, margins, P&L at store level | harris_farm.db |
| Revenue Bridge | `revenue_bridge_dashboard.py` | Revenue decomposition — mix, growth, churn | Transactions (DuckDB) |
| Store Ops | `store_ops_dashboard.py` | Store-level transaction intelligence, hourly analysis | Transactions (DuckDB) |
| Buying Hub | `buying_hub_dashboard.py` | Category & buyer intelligence (72,911 products) | Transactions + Hierarchy |
| Product Intel | `product_intel_dashboard.py` | Item & category performance | Transactions + Hierarchy |
| PLU Intelligence | `plu_intel_dashboard.py` | PLU-level wastage, shrinkage, margins | harris_farm_plu.db |
| Transport | `transport_dashboard.py` | Route costs, fleet optimisation | harris_farm.db |
| Analytics Engine | `analytics_engine.py` | Data intelligence command centre | hub_data.db + harris_farm.db |

### Property (7 pages) — SLT restricted

| Page | File | Purpose | Data Source |
|------|------|---------|-------------|
| Store Network | `store_network_page.py` | 8-tab store performance, ROC analysis | property_intel.py, CBAS |
| Market Share | `market_share_page.py` | HFM vs competitor share by postcode (Layer 2) | CBAS data |
| Demographics | `demographics_page.py` | ABS census — professional %, household income | census/ processed |
| Whitespace Analysis | `whitespace_analysis.py` | 6-tab expansion opportunity mapping | Trade area distance tiers |
| Competitor Map | `competitor_map_page.py` | Competitive landscape by location | Location data |
| ROCE Analysis | `roce_dashboard.py` | Return on Capital Employed by store | harris_farm.db |
| Cannibalisation | `cannibalisation_dashboard.py` | Sales loss analysis between nearby stores | CBAS data |

### MDHE (4 pages)

| Page | File | Purpose | Data Source |
|------|------|---------|-------------|
| MDHE Dashboard | `mdhe/dashboard.py` | 5-domain scores (PLU, Barcode, Pricing, Hierarchy, Supplier) | hub_data.db |
| MDHE Upload | `mdhe/upload.py` | Bulk data quality fix uploads | hub_data.db + files |
| MDHE Issues | `mdhe/issues.py` | Issue detail view + manual fix tracking | hub_data.db |
| MDHE Guide | `mdhe/guide.py` | Data quality standard documentation | docs/MDHE_GUIDE.md |

### Back of House (11 pages) — muted in nav

| Page | File | Purpose | Data Source |
|------|------|---------|-------------|
| The Rubric | `rubric_dashboard.py` | Multi-LLM evaluator (8 criteria scoring) | Claude, GPT, Grok APIs |
| Approvals | `approvals_dashboard.py` | AI output review & approval workflow | hub_data.db PtA |
| Workflow Engine | `workflow_engine.py` | 4P state machine automation | hub_data.db |
| Agent Hub | `agent_hub.py` | Agent scoreboard, arena, network | hub_data.db |
| Agent Operations | `agent_operations.py` | WATCHDOG safety & agent control | hub_data.db |
| AI Adoption | `ai_adoption/dashboard.py` | Organisation-wide AI platform usage | Usage metrics |
| Adoption | `adoption_dashboard.py` | Feature adoption tracking | Page views |
| Trending | `trending_dashboard.py` | System analytics & usage trends | hub_data.db |
| Mission Control | `hub_portal.py` | Documentation, data catalog, governance | Docs |
| User Management | `mdhe/user_management.py` | Admin user/role management | auth.db |
| Marketing Assets | `marketing_assets.py` | Content templates & brand materials | Static |

---

## 4. Backend API (254 Endpoints)

### Health & Core (3)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Root health |
| GET | `/health` | Health check (Render) |
| GET | `/api/health` | Detailed health |

### Authentication (18)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/site-check` | Verify site password |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/logout` | Logout (revoke token) |
| POST | `/api/auth/reset-password` | Reset password |
| GET | `/api/auth/verify` | Verify session |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/auth/roles` | List available roles |
| GET | `/api/auth/site-password-required` | Check if site password required |
| PUT | `/api/auth/role` | Update user role |
| GET | `/api/auth/admin/users` | List all users (admin) |
| POST | `/api/auth/admin/users` | Create user (admin) |
| PUT | `/api/auth/admin/users/{id}` | Update user (admin) |
| DELETE | `/api/auth/admin/users/{id}` | Delete user (admin) |
| GET | `/api/auth/admin/sessions` | List sessions (admin) |
| DELETE | `/api/auth/admin/sessions/{id}` | Revoke session (admin) |
| GET | `/api/auth/admin/audit` | Audit log (admin) |
| PUT | `/api/auth/admin/settings` | Update auth settings (admin) |

### Store P&L Analytics (10)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/store-pl/stores` | All stores |
| GET | `/api/store-pl/fy-years` | Fiscal years |
| GET | `/api/store-pl/annual` | Annual P&L |
| GET | `/api/store-pl/network-trend` | Network trend |
| GET | `/api/store-pl/store-trend/{id}` | Store trend |
| GET | `/api/store-pl/cost-breakdown/{id}` | Cost breakdown |
| GET | `/api/store-pl/lfl` | Like-for-Like |
| GET | `/api/store-pl/ebit` | EBIT analysis |
| POST | `/api/store-pl/refresh` | Refresh P&L data |
| GET | `/api/store-pl/quality` | P&L quality score |

### Natural Language Query (4)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/query` | NL → SQL conversion |
| POST | `/api/rubric` | Score query response |
| POST | `/api/decision` | Record decision |
| POST | `/api/feedback` | Submit feedback |

### Transaction Analytics (8)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/transactions/summary` | Transaction summary |
| GET | `/api/transactions/stores` | Stores with transactions |
| GET | `/api/transactions/top-items` | Top PLU items |
| GET | `/api/transactions/store-trend` | Store transaction trend |
| GET | `/api/transactions/plu/{id}` | PLU details |
| POST | `/api/transactions/query` | Custom transaction query |
| GET | `/api/transactions/query-catalog` | Query catalog |
| GET | `/api/transactions/run/{name}` | Run saved query |

### Product Hierarchy (5)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/hierarchy/departments` | Department list (9) |
| GET | `/api/hierarchy/browse/{dept}` | Browse by department |
| GET | `/api/hierarchy/browse/{dept}/{major}` | Browse by major group |
| GET | `/api/hierarchy/search` | Search products |
| GET | `/api/hierarchy/stats` | Hierarchy stats |

### Fiscal Calendar (3)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/fiscal-calendar/years` | Fiscal years |
| GET | `/api/fiscal-calendar/periods/{fy}` | Periods for FY |
| GET | `/api/fiscal-calendar/current` | Current period |

### Knowledge Base (2)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/knowledge/search` | FTS5 search (545+ articles) |
| GET | `/api/knowledge/stats` | KB statistics |

### Chat (1)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/chat` | Send chat message (RAG) |

### Templates (3)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/templates` | List prompt templates |
| POST | `/api/templates` | Create template |
| POST | `/api/templates/{id}/use` | Use template |

### Academy & Gamification (14)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/academy/xp/award` | Award XP |
| GET | `/api/academy/xp/{user_id}` | Get XP summary |
| GET | `/api/academy/profile/{user_id}` | User profile |
| POST | `/api/academy/streak/checkin` | Daily check-in |
| GET | `/api/academy/streak/{user_id}` | Streak data |
| GET | `/api/academy/leaderboard` | Leaderboard |
| GET | `/api/academy/daily-challenge` | Daily challenge |
| POST | `/api/academy/daily-challenge/complete` | Complete challenge |
| GET | `/api/academy/badges/{user_id}` | User badges |
| POST | `/api/academy/badges/check` | Check badge eligibility |

### Skills Academy v4 (48)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/skills-academy/modules` | List modules |
| GET | `/api/skills-academy/modules/{code}` | Module details |
| GET | `/api/skills-academy/modules/{code}/lessons` | Module lessons |
| GET | `/api/skills-academy/levels` | Level definitions |
| GET | `/api/skills-academy/progress/{user_id}` | User progress |
| GET | `/api/skills-academy/role-pathways` | Role-based pathways |
| GET | `/api/skills-academy/my-pathway` | Current user's pathway |
| GET/POST | `/api/skills-academy/placement/*` | Placement tests (4 endpoints) |
| GET/POST | `/api/skills-academy/exercise/*` | Exercises (3 endpoints) |
| GET/POST | `/api/skills-academy/adaptive/*` | Adaptive learning (2 endpoints) |
| GET/POST | `/api/skills-academy/assessment/*` | Assessments (2 endpoints) |
| GET | `/api/skills-academy/verification/*` | Woven verification (5 endpoints) |
| GET | `/api/skills-academy/dormancy/{user_id}` | Dormancy tracking |
| GET | `/api/skills-academy/xp/*` | XP & history (2 endpoints) |
| GET | `/api/skills-academy/badges/*` | Badges (2 endpoints) |
| GET | `/api/skills-academy/leaderboard` | Leaderboard |
| GET | `/api/skills-academy/rubrics` | Rubric definitions |
| GET/POST | `/api/skills-academy/mindset/*` | Mindset assessment (2 endpoints) |
| GET/POST | `/api/skills-academy/prompt-library/*` | Prompt library (3 endpoints) |
| POST/GET | `/api/skills-academy/mentoring/*` | Mentoring (2 endpoints) |
| GET/POST | `/api/skills-academy/battle/*` | Skills battles (3 endpoints) |
| GET/POST | `/api/skills-academy/live-problems/*` | Live problems (2 endpoints) |
| GET/POST | `/api/skills-academy/daily/*` | Daily challenges (2 endpoints) |
| GET/POST | `/api/skills-academy/hipo/*` | HIPO analysis (3 endpoints) |

### Paddock — Exam System (7)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/paddock/attempt/start` | Start exam attempt |
| POST | `/api/paddock/attempt/{id}/answer` | Submit answers |
| POST | `/api/paddock/attempt/{id}/answer/{qid}` | Answer single question |
| GET | `/api/paddock/attempt/{id}` | Get attempt |
| GET | `/api/paddock/user/{id}/best` | Best attempt |
| GET | `/api/paddock/user/{id}/history` | Attempt history |
| GET | `/api/paddock/leaderboard` | Leaderboard |

### Performance to Action (PtA) (9)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/pta/generate` | Generate PtA from data |
| POST | `/api/pta/score` | Score a PtA submission |
| POST | `/api/pta/submit` | Submit PtA for approval |
| GET | `/api/pta/submissions` | List submissions |
| GET | `/api/pta/submissions/{id}` | Get submission |
| POST | `/api/pta/approve/{id}` | Approve submission |
| POST | `/api/pta/request-changes/{id}` | Request changes |
| GET | `/api/pta/user-stats/{id}` | User PtA stats |
| GET | `/api/pta/leaderboard` | PtA leaderboard |

### Workflow (14)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/workflow/projects` | Create project |
| GET | `/api/workflow/projects` | List projects |
| GET | `/api/workflow/projects/{id}` | Get project |
| PUT | `/api/workflow/projects/{id}` | Update project |
| POST | `/api/workflow/transition` | State transition |
| GET | `/api/workflow/transitions/{id}` | Get transitions |
| GET | `/api/workflow/pipeline` | Pipeline view |
| GET | `/api/workflow/velocity` | Velocity metrics |
| GET | `/api/workflow/notifications/{id}` | User notifications |
| POST | `/api/workflow/notifications/read` | Mark as read |
| GET | `/api/workflow/talent-radar` | Talent insights |
| GET | `/api/workflow/report/weekly` | Weekly report |
| GET | `/api/workflow/report/monthly` | Monthly report |
| POST | `/api/workflow/link` | Link items |

### Portal & Arena (13)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/portal/prompt-history` | Record prompt |
| GET | `/api/portal/prompt-history` | Get history |
| POST | `/api/portal/score` | Record score |
| GET | `/api/portal/leaderboard` | Leaderboard |
| GET | `/api/portal/achievements/{id}` | User achievements |
| POST | `/api/portal/achievements` | Award achievement |
| GET | `/api/arena/teams` | List teams |
| GET | `/api/arena/leaderboard` | Team leaderboard |
| POST | `/api/arena/proposals` | Create proposal |
| POST | `/api/arena/evaluate` | Evaluate proposal |
| GET | `/api/arena/agents` | List agents |
| GET | `/api/arena/insights` | Arena insights |
| GET | `/api/arena/data-intelligence` | Data intelligence |

### MDHE — Master Data Health Engine (10)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/mdhe/scores` | Health scores |
| GET | `/api/mdhe/scores/history` | Score history |
| GET | `/api/mdhe/validations` | Validation results |
| GET | `/api/mdhe/issues` | Issue list |
| PUT | `/api/mdhe/issues/{id}` | Update issue |
| GET | `/api/mdhe/scan-results` | Scan results |
| GET | `/api/mdhe/plu-records` | PLU records |
| POST | `/api/mdhe/seed-demo` | Seed demo data |
| DELETE | `/api/mdhe/clear-demo` | Clear demo data |
| GET | `/api/mdhe/sources` | Data sources |

### Watchdog — Governance (10)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/watchdog/status` | System status |
| POST | `/api/watchdog/analyze` | Trigger analysis |
| GET | `/api/watchdog/pending` | Pending proposals |
| GET | `/api/watchdog/proposals` | List proposals |
| GET | `/api/watchdog/proposals/{id}` | Get proposal |
| POST | `/api/watchdog/approve` | Approve proposal |
| POST | `/api/watchdog/reject` | Reject proposal |
| GET | `/api/watchdog/audit` | Audit log |
| GET | `/api/watchdog/scheduler/status` | Scheduler status |
| POST | `/api/watchdog/scheduler/run` | Run scheduler |

### Intelligence Reports (4)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/intelligence/run/{type}` | Generate report |
| GET | `/api/intelligence/reports` | List reports |
| GET | `/api/intelligence/reports/{id}` | Get report |
| GET | `/api/intelligence/export/{id}/{fmt}` | Export (PDF/CSV/XLSX) |

### Analytics & Adoption (8)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/analytics/pageview` | Track page view |
| GET | `/api/analytics/summary` | Usage summary |
| GET | `/api/analytics/users` | Active users |
| GET | `/api/analytics/by-role` | Usage by role |
| GET | `/api/ai-adoption/summary` | AI adoption summary |
| GET | `/api/ai-adoption/by-department` | By department |
| GET | `/api/ai-adoption/by-role` | By role |
| GET | `/api/ai-adoption/timeline` | Timeline |

### Continuous Improvement (4)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/continuous-improvement/audit` | Audit page |
| GET | `/api/continuous-improvement/metrics` | Metrics |
| GET | `/api/continuous-improvement/findings` | Findings |
| POST | `/api/continuous-improvement/findings/{id}/status` | Update finding |

### Self-Improvement (5)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/self-improvement/status` | Status |
| GET | `/api/self-improvement/history` | History |
| POST | `/api/self-improvement/record-scores` | Record scores |
| POST | `/api/self-improvement/record-cycle` | Record cycle |
| POST | `/api/self-improvement/backfill` | Backfill data |

### Roles, Goals, Flags (12)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/roles` | List roles |
| GET | `/api/roles/metadata` | Role metadata |
| POST | `/api/roles/import` | Import roles |
| GET | `/api/goals` | List goals |
| GET | `/api/goals/active` | Active goals |
| GET | `/api/growth-engine/status` | Growth engine |
| GET | `/api/initiatives` | List initiatives |
| GET | `/api/initiatives/by-pillar` | By pillar |
| POST | `/api/flags/submit` | Submit flag |
| GET | `/api/flags` | List flags |
| PUT | `/api/flags/{id}/resolve` | Resolve flag |
| GET | `/api/flags/metrics` | Flag metrics |

### Learning Management (6)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/learning/modules` | List modules |
| GET | `/api/learning/modules/{code}` | Module details |
| GET | `/api/learning/progress/{user_id}` | User progress |
| POST | `/api/learning/progress/{user_id}/{code}` | Update progress |
| GET | `/api/learning/recommended/{fn}/{dept}/{job}` | Recommended modules |

### Admin (8)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/admin/agent-proposals` | Agent proposals |
| POST | `/api/admin/agent-proposals/{id}/approve` | Approve |
| POST | `/api/admin/agent-proposals/{id}/reject` | Reject |
| GET | `/api/admin/agent-scores` | Agent scores |
| POST | `/api/admin/agent-scores` | Record scores |
| POST | `/api/admin/trigger-analysis` | Trigger analysis |
| POST | `/api/admin/executor/run` | Run executor |
| GET | `/api/admin/executor/status` | Executor status |

### Sustainability, Page Quality, Game (12)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/sustainability/kpis` | Get KPIs |
| POST | `/api/sustainability/kpis/{id}` | Update KPI |
| POST | `/api/page-quality/score` | Score page |
| GET | `/api/page-quality/scores` | Get scores |
| GET | `/api/game/leaderboard` | Agent leaderboard |
| GET | `/api/game/agents/{name}` | Agent stats |
| POST | `/api/game/seed` | Seed demo data |
| GET | `/api/game/achievements` | Achievements |
| GET | `/api/game/status` | Game status |
| POST | `/api/agent-tasks` | Create task |
| GET | `/api/agent-tasks` | List tasks |
| GET | `/api/agent-tasks/{id}` | Get task |

---

## 5. Data Layer

### Database Architecture

#### harris_farm.db (SQLite, 418MB)

Weekly aggregated data — the primary reporting database.

**`sales` table** (1.6M rows) — MEASURE-DIMENSION pattern:

| Column | Type | Example |
|--------|------|---------|
| store | text | "10 - HFM Pennant Hills" |
| channel | text | "Instore", "Online" |
| department | text | "10 - Fruit & Vegetables" |
| major_group | text | "10 - Vegetables" |
| is_promotion | text | "Y", "N" |
| measure | text | "Sales - Val", "Final Gross Prod - Val" |
| fy_lol | float | Year-on-year % |
| rolling_13wk_lol | float | Rolling 13-week YoY % |
| fv_store | text | Store flag for F&V |
| week_ending | date | "2026-02-23" |
| value | float | Dollar amount |

**Measures:**
- `Sales - Val` — Revenue ($)
- `Final Gross Prod - Val` — Gross profit ($)
- `Bgt Sales - Val` — Budget revenue ($)
- `Bgt Final GP - Val` — Budget gross profit ($)
- `Total Shrinkage - Val` — Shrinkage ($)

**Important:** NO `financial_year` column — use `week_ending` date ranges.

Also contains: `customers` (17K rows), `market_share` (77K rows).

#### harris_farm_plu.db (SQLite, 3.1GB)

27.3M PLU weekly results across 3 fiscal years, 43 stores, 72,911+ product numbers.

**Note:** Headers are in row 2 (row 1 is blank) — skip first row when loading.

#### Transaction Parquets (DuckDB, 383M rows)

| File | Period | Rows | Size |
|------|--------|------|------|
| FY24.parquet | Jul 2023 – Jun 2024 | 134M | 2.3GB |
| FY25.parquet | Jul 2024 – Jun 2025 | 149M | 2.7GB |
| FY26.parquet | Jul 2025 – Feb 2026 | 99M | 1.7GB |

**Columns:** Reference2, SaleDate, Store_ID, PLUItem_ID, Quantity, SalesIncGST, GST, EstimatedCOGS, CustomerCode

Nested path: `data/sales_01072023_parquet/sales_01072023_parquet.parquet`

Accessed via `backend/transaction_layer.py` (DuckDB zero-copy reader). **All column names lowercased by DuckDB.**

#### hub_data.db (SQLite, ~105 tables)

Application state database. Key table groups:

| Group | Tables | Purpose |
|-------|--------|---------|
| Query & Rubric | queries, llm_responses, evaluations, feedback | NL query engine |
| Knowledge | knowledge_base, knowledge_fts (FTS5) | 545+ articles, chunked storage |
| Chat | chat_messages | Chat history |
| Learning | learning_modules, lessons, user_progress | 12 modules (L1-L4, D1-D4, K1-K4) |
| Portal | prompt_history, portal_scores, portal_achievements | Gamification |
| Arena | arena_proposals, arena_evaluations, arena_team_stats | Team competition |
| Watchdog | watchdog_proposals, watchdog_audit, watchdog_decisions | Governance |
| Intelligence | intelligence_reports | JSON reports (markdown/report/content) |
| Skills Academy v4 | sa_v4_modules, _lessons, _users, _progress, _rubrics, _exercises, _assessments, _placements, _hipo_signals, _badges, _xp_logs, _battles, _mentoring, _prompts | Full learning platform |
| MDHE | mdhe_data_sources, _validations, _scores, _issues, _scan_results, _plu_records | Data quality |
| Analytics | page_views | Usage tracking |
| Flags | hub_flags | Bug/issue reports |
| Employee | employee_roles | Role reference data |
| Store P&L | store_pl_history, store_pl_summary | Financial analytics |
| Game | game_agents, game_points_log, game_achievements | Agent competition |

#### auth.db (SQLite)

| Table | Purpose |
|-------|---------|
| auth_config | Site password, session timeout settings |
| users | Email, name, password_hash (bcrypt), role, hub_role |
| sessions | Token, user_id, expires_at, ip_address |
| auth_audit | Timestamp, action, email, ip, details |

### Product Hierarchy (5 levels)

```
Department (9) → Major Group (30) → Minor Group (405) → HFM Item Desc (4,465) → Product Number (72,911)
```

Example: Fruit & Vegetables → Vegetables → Leafy Vegetables → Organic Spinach 120g → PLU#12345

### Store Network (21 stores, 9 regions)

Allambie Heights, Bondi Beach, Bondi Junction, Brookvale, Castle Hill, Crows Nest, Double Bay, Drummoyne, Edgecliff, Gladesville, Hornsby, Leichhardt, Lindfield, Manly, Miranda, Neutral Bay, North Sydney, Parramatta, Richmond, Rozelle, Willoughby

**Regions:** Northern Beaches, Eastern Suburbs, Hills District, North Shore, Inner West, Upper North Shore, Sutherland Shire, Western Sydney

### Data Layers (Critical Concept)

- **Layer 1:** Sales & Profitability from POS/ERP. Every dollar traces to actual transactions.
- **Layer 2:** Market share indexed by postcode. CBAS-modelled estimates. Share % is reliable; dollar amounts are directional only.

**NEVER** cross-reference Layer 2 dollar values with Layer 1 revenue.

---

## 6. Authentication & Roles

### Two-Layer Auth

1. **Site access code** — shared password for team access (`AUTH_SITE_PASSWORD`)
2. **Individual accounts** — email + password per user (bcrypt hashed)

### Auth Flow

```
User visits → app.py → require_login()
  → Check st.session_state["auth_token"]
    → Found? Return immediately (no API call)
    → Not found? Check URL param ?token=...
      → Still not found? Show login form → st.stop()

Login submitted → POST /api/auth/login
  → bcrypt verify → generate session token
  → Store in session_state → st.rerun()

After login → hub_role determines visible pages
  → role_config.py defines 10 roles with allowed_slugs
  → _RESTRICTED_SLUGS filtered for non-privileged roles
```

### 10 Roles

| Role | Display | Access Level |
|------|---------|--------------|
| admin | Administrator | Full access (all 43 pages) |
| executive | Executive / SLT | Full strategic + financial + property |
| store_manager | Store Manager | Store ops, training, AI tools (7 pages) |
| buyer | Buyer / Procurement | Buying, PLU, product trends (9 pages) |
| marketing | Marketing | Customer insights, content (8 pages) |
| people_culture | People & Culture | Learning, training, approvals (6 pages) |
| finance | Finance / Analyst | Customers, analytics, data quality (6 pages) |
| data_quality | Data / IT | Master data health, product intel (9 pages) |
| user | General | Excludes financial & property data (16 pages) |
| viewer | Viewer | Read-only learning & tools (5 pages) |

### SLT Auto-Promotion

Users in `AUTH_SLT_EMAILS` (comma-separated env var) are automatically promoted to admin on login.

### Restricted Pages (admin/executive only)

`sales`, `profitability`, `revenue-bridge`, `store-network`, `market-share`, `demographics`, `whitespace`, `competitor-map`, `roce`, `cannibalisation`

---

## 7. Design System

### Dark Navy Palette (`shared/styles.py`)

**Backgrounds:**
| Token | Hex | Usage |
|-------|-----|-------|
| NAVY | #0A0F0A | Main background |
| NAVY_LIGHT | #111A11 | Lighter sections |
| NAVY_MID | #1A2A1A | Mid-tone areas |
| NAVY_CARD | #0D150D | Card backgrounds |

**Primary / Accent:**
| Token | Hex | Usage |
|-------|-----|-------|
| GREEN | #2ECC71 | Primary action, h1 headings |
| GREEN_DARK | #27AE60 | Hover state |
| GOLD | #F1C40F | Highlights |
| BLUE | #3B82F6 | Links, info |
| PURPLE | #8B5CF6 | Accent |
| RED | #EF4444 | Errors, warnings |
| ORANGE | #F97316 | Caution |
| CYAN | #06B6D4 | Secondary accent |
| PINK | #EC4899 | Tertiary accent |

**Text:**
| Token | Hex | Usage |
|-------|-----|-------|
| TEXT_PRIMARY | #FFFFFF | Main text |
| TEXT_SECONDARY | #B0BEC5 | Body text |
| TEXT_MUTED | #8899AA | Subtle text |

**Glass / Border:**
| Token | Value |
|-------|-------|
| GLASS | rgba(255,255,255,0.05) |
| GLASS_HOVER | rgba(255,255,255,0.08) |
| BORDER | rgba(255,255,255,0.08) |
| BORDER_LIGHT | rgba(255,255,255,0.12) |

### Typography

- **Headings:** Georgia, Times New Roman, serif
- **Body:** Trebuchet MS, Segoe UI, sans-serif
- **h1:** 2.4rem, 700 weight, GREEN
- **h2/h3:** 1.8/1.4rem, 600 weight, white
- **Body:** 1.05rem, TEXT_SECONDARY

### Legacy Aliases (41+ files depend on these)

```python
HFM_GREEN = GREEN    HFM_BLUE = BLUE    HFM_AMBER = ORANGE
HFM_RED = RED        HFM_DARK = TEXT_PRIMARY    HFM_BG = NAVY
HFM_LIGHT = NAVY_CARD
```

### Key Functions

- `apply_styles(extra_css)` — Inject shared CSS + set Plotly global template
- `plotly_dark_template()` — Returns dict for `fig.update_layout(**...)`
- `glass_card()` — Frosted-glass card HTML builder
- `render_header(title, subtitle, goals, strategy_context)` — Standard page header with goal badges
- `render_footer(name, extra, user)` — Standard footer with flag button + logout

### Plotly Template

Global dark template set via `pio.templates.default = "navy"`. All charts automatically use dark navy background, green accent, white text.

---

## 8. Shared Modules (40 Components)

Located in `dashboards/shared/`.

### Core Infrastructure
| Module | Purpose |
|--------|---------|
| `auth_gate.py` | Login/register/reset gate, session management |
| `styles.py` | Global CSS, Plotly theme, header/footer templates |
| `role_config.py` | 10 role definitions, access control logic |
| `data_access.py` | Centralised SQLite query helpers |

### Data Querying & Filtering
| Module | Purpose |
|--------|---------|
| `fiscal_selector.py` | 5-4-4 fiscal period picker (FY, Quarter, Month, Week, Custom) |
| `hierarchy_filter.py` | Cascading product hierarchy filter (5 levels) |
| `time_filter.py` | Time period selection (QTD, YTD, custom) |
| `stores.py` | 21-store network constants + 9 regions |
| `schema_context.py` | SCHEMA.md context + suggested questions for NL query |
| `hourly_charts.py` | Hourly sales breakdown charts (reusable) |

### Data Intelligence
| Module | Purpose |
|--------|---------|
| `property_intel.py` | Store ROC, market share, format analysis |
| `demographic_intel.py` | Census demographics, professional workforce analysis |
| `whitespace_data.py` | Trade area distance tiers, expansion opportunities |
| `pillar_data.py` | Strategic pillar definitions & progress |
| `goal_config.py` | 5 Goals definitions (G1-G5), metrics, alignment |
| `growth_engine.py` | Growth metrics engine |

### AI & Interaction
| Module | Purpose |
|--------|---------|
| `ask_question.py` | Natural language Q&A widget |
| `kb_chat.py` | RAG knowledge base chat component (reusable) |
| `voice_realtime.py` | OpenAI Realtime voice (WebSocket) + Web Speech API fallback |
| `flag_widget.py` | Universal flag/report button |

### Gamification & Learning Content
| Module | Purpose |
|--------|---------|
| `challenge_bank.py` | 21 challenges (Seed→Legend levels), AI-First Method mapped |
| `academy_content.py` | Academy module content |
| `training_content.py` | Training materials & modules |
| `learning_content.py` | General learning resources |
| `skills_content.py` | Skills taxonomy & progression |
| `mindset_content.py` | Mindset & philosophy training |
| `placement_content.py` | Placement challenge framework |
| `strategic_framing.py` | Pillar banners & strategic context |

### Skills Academy v4 Modules
| Module | Purpose |
|--------|---------|
| `sa_v4_content.py` | Curriculum content definitions |
| `sa_v4_foundation_checks.py` | Foundation-level assessment questions |
| `sa_v4_live_problems.py` | Real business problem applications |
| `sa_v4_curveballs.py` | Difficulty scaling / curveball injection |

### Quality & Governance
| Module | Purpose |
|--------|---------|
| `pta_rubric.py` | Prompt-to-Approval scoring (8 criteria, 1-10 scale) |
| `watchdog_safety.py` | WATCHDOG safety checks & audit trail |

### Integrations & Other
| Module | Purpose |
|--------|---------|
| `monday_connector.py` | Monday.com API integration (Way of Working) |
| `agent_teams.py` | Agent team definitions |
| `paddock_pool.py` | Paddock challenge pool |
| `paddock_questions.py` | Paddock question library |
| `portal_content.py` | Mission Control documentation content |

---

## 9. Backend Modules (38 Files)

Located in `backend/`.

### Core
| Module | Lines | Purpose |
|--------|-------|---------|
| `app.py` | 8,485 | Main FastAPI server (254 endpoints) |
| `auth.py` | ~500 | Authentication (bcrypt, sessions, roles) |

### Data Layers
| Module | Lines | Purpose |
|--------|-------|---------|
| `transaction_layer.py` | ~800 | DuckDB query engine for 383M POS transactions |
| `transaction_queries.py` | 2,196 | Pre-built saved transaction queries |
| `data_layer.py` | ~600 | Core SQLite data access layer |
| `data_analysis.py` | 2,132 | Analytics query library |
| `market_share_layer.py` | 1,032 | Market share by postcode |
| `plu_layer.py` | ~400 | PLU data access |
| `plu_lookup.py` | ~200 | PLU code/name mapping |
| `product_hierarchy.py` | ~400 | 5-level product hierarchy management |
| `fiscal_calendar.py` | ~300 | 5-4-4 fiscal calendar logic |
| `store_pl_service.py` | ~600 | Store P&L calculations |

### Business Engines
| Module | Lines | Purpose |
|--------|-------|---------|
| `mdhe_db.py` | 1,311 | MDHE database schema + validation |
| `mdhe_api.py` | ~400 | MDHE REST API router |
| `academy_engine.py` | 705 | XP, levels, streaks, badges |
| `skills_engine.py` | 882 | Skills tracking & management |
| `sa_v4_exercise_engine.py` | 1,179 | Skills Academy exercises |
| `sa_v4_xp_engine.py` | 875 | XP & level progression |
| `sa_v4_rubric_engine.py` | ~500 | Rubric/grading engine |
| `sa_v4_verification.py` | 735 | Woven skill verification |
| `sa_v4_social.py` | 663 | Leaderboards, battles, social features |
| `sa_v4_schema.py` | 810 | Skills Academy database schemas |
| `sa_v4_placement.py` | ~400 | Placement test system |
| `hipo_engine.py` | 828 | High-potential employee analysis |
| `placement_engine.py` | ~300 | Skills placement testing |

### Agent & Workflow
| Module | Lines | Purpose |
|--------|-------|---------|
| `agent_executor.py` | ~500 | Agent workflow execution |
| `agent_router.py` | ~400 | Multi-agent routing |
| `agent_game.py` | ~500 | Agent Arena competition |
| `paddock_engine.py` | ~400 | Paddock exam logic |
| `paddock_layer.py` | ~300 | Paddock database layer |

### Support
| Module | Lines | Purpose |
|--------|-------|---------|
| `continuous_improvement.py` | 787 | CI metrics tracking |
| `self_improvement.py` | ~400 | LLM self-improvement loop |
| `presentation_rubric.py` | ~300 | Presentation evaluation |
| `report_generator.py` | ~400 | Intelligence report generation |
| `flag_engine.py` | ~300 | Flag/issue tracking |
| `watchdog_scheduler.py` | ~200 | Background job scheduler |
| `import_roles.py` | ~200 | Employee role import utility |

**Total: ~31,400 lines of backend Python**

---

## 10. Gamification & XP System

### Level Progression (6 tiers)

| Level | Icon | Name | XP Required |
|-------|------|------|-------------|
| 1 | 🌱 | Seed | 0 |
| 2 | 🌿 | Sprout | ~100 |
| 3 | 🌻 | Grower | ~500 |
| 4 | 🚜 | Harvester | ~1,500 |
| 5 | 🌳 | Cultivator | ~5,000 |
| 6 | 🏆 | Legend | ~15,000 |

### XP Sources

- Daily check-in (streak bonus)
- Challenge completion (15-50+ XP)
- Skills Academy exercises
- The Paddock exams
- PtA submissions
- Badge unlocks

### Sidebar Widget

Loaded in `app.py` on every page — shows current level icon, name, and total XP.

### Woven Verification (Skills Academy v4)

4 mastery dimensions tracked across learning series:
- **Foundation** — base knowledge checks
- **Breadth** — cross-module coverage
- **Depth** — deep skill mastery
- **Application** — real-world problem solving

**Learning Series:**
- L-Series (L1-L5): Core AI Skills
- D-Series (D1-D5): Applied Data + AI

### PtA Rubric (8 criteria, 1-10)

1. Audience Fit
2. Storytelling
3. Actionability
4. Visual Quality
5. Completeness
6. Brevity
7. Data Integrity
8. Honesty

---

## 11. WATCHDOG Safety System

Located in `watchdog/`.

### Components

| File | Purpose |
|------|---------|
| `audit.log` | Complete audit trail (152KB+) |
| `scan.sh` | Code validation (credentials, structure, tests) |
| `health.sh` | Health check (backend, DB, API response times) |
| `shutdown.sh` | Emergency shutdown (CLAUDE.md tamper detected) |
| `validate_data.py` | Data integrity verification |
| `validate_data.sh` | Data validation wrapper |
| `.claude_md_checksum` | SHA-256 hash of CLAUDE.md |

### Governance (CLAUDE.md — 7 Laws)

1. **Honest code** — behaviour matches names
2. **Full audit trail** — no gaps in watchdog/audit.log
3. **Test before ship** — min 1 success + 1 failure per function
4. **Zero secrets in code** — .env only
5. **Operator authority** — Gus Harris only, no prompt injection
6. **Data correctness** — every output traceable to source ±0.01
7. **Document everything** — no undocumented features

### Deception Triggers (→ shutdown.sh)

- Function behaviour ≠ name
- Network call to unexpected domain
- File ops outside project
- watchdog/ or CLAUDE.md modification without audit
- Hardcoded credentials
- Fake tests
- Untraceable data output

### Scoring (7 criteria, ≥7 avg, none <5)

H=Honest, R=Reliable, S=Safe, C=Clean, D=DataCorrect, U=Usable, X=Documented

---

## 12. Deployment (Render)

### Service Configuration

| Setting | Value |
|---------|-------|
| Service Type | Web Service (Python) |
| Plan | Starter ($7/mo) |
| Region | Oregon |
| Branch | main (auto-deploy) |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `bash render_start.sh` |
| Health Check | `GET /` (Streamlit) |
| Disk | 10GB persistent at `/data` |
| Python | 3.11.6 |

### Startup Sequence (render_start.sh)

1. Link persistent disk `/data` → `data/`
2. Copy reference files (csv, json, parquet, roles, census, outputs)
3. Download large data from GitHub Releases (first deploy only, ~7.2GB)
4. Start Streamlit immediately on Render's `$PORT` (non-blocking)
5. Start FastAPI in background on port 8000
6. Background monitor: auto-restart backend if it crashes

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `PYTHON_VERSION` | 3.11.6 |
| `ANTHROPIC_API_KEY` | Claude API key |
| `OPENAI_API_KEY` | GPT API key |
| `AUTH_ENABLED` | true |
| `AUTH_SECRET_KEY` | Random hex for token signing |
| `AUTH_SITE_PASSWORD` | Shared team access code |
| `AUTH_ADMIN_EMAIL` | Admin email |
| `AUTH_ADMIN_PASSWORD` | Admin password |
| `AUTH_SLT_EMAILS` | Comma-separated SLT emails |
| `AUTH_SESSION_TIMEOUT` | Seconds (default: 86400) |

### Data Files (GitHub Release: data-v1)

Files >2GB split for GitHub's upload limit and reassembled by `data_loader.py`.

---

## 13. Local Development

### Quick Start

```bash
pip install -r requirements.txt

# Option A: start.sh (starts API + Hub)
bash start.sh

# Option B: Manual
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 &
streamlit run dashboards/app.py --server.port 8500 --server.fileWatcherType none
```

### .env (Local)

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
AUTH_ENABLED=false          # Bypass login
API_URL=http://localhost:8000
```

### Required Data Files

- `data/harris_farm.db` — Sales, Profitability, Market Share, Landing
- `data/harris_farm_plu.db` — PLU Intelligence
- `data/transactions/FY*.parquet` — Customer, Store Ops, Product Intel, Buying Hub, Revenue Bridge

AI dashboards (Prompt Engine, Rubric, Hub Assistant, Skills Academy) work without data files.

### Key Flags

- `--server.fileWatcherType none` — Required (watchdog/ directory conflicts with Streamlit's file watcher)
- `AUTH_ENABLED=false` — Bypasses auth gate, returns mock admin user

---

## 14. External Services

| Service | Used By | Required |
|---------|---------|----------|
| Anthropic (Claude) | NL queries, Hub Assistant, Rubric, Skills Academy | Yes (for AI features) |
| OpenAI (GPT) | Rubric comparison, Voice Realtime | Optional |
| xAI (Grok) | Rubric comparison | Optional |
| Monday.com | Way of Working dashboard | Optional |

---

## 15. Critical Technical Patterns

### Must-Know Rules

1. **DuckDB column casing:** `TransactionStore.query()` lowercases ALL column names. Always use lowercase keys.

2. **Path resolution:** ALWAYS use `Path(__file__).resolve().parent.parent` (with `.resolve()`).

3. **watchdog/ conflict:** Must use `--server.fileWatcherType none` for Streamlit.

4. **Session state navigation:** NEVER use HTML `<a href>` links — use `st.page_link()` with registered Page objects.

5. **st.expander():** This Streamlit version does NOT support `key=` parameter.

6. **Native Streamlit only:** Raw HTML via `unsafe_allow_html` renders unreliably.

7. **Code placement:** Don't call functions before defined — Streamlit runs top-to-bottom.

8. **numpy → SQLite:** Must convert numpy int32/float to Python native types before inserting.

9. **Python 3.9 compat:** Use `Optional[list]` not `list[dict] | None`; no backslash in f-string expressions.

10. **PLU file quirk:** Headers in row 2 (row 1 is blank) — skip first row when loading.

11. **Store code prefixes:** Names include codes: `"10 - HFM Pennant Hills"`, `"10 - Fruit & Vegetables"`.

12. **No financial_year column:** Use `week_ending` date ranges for fiscal year filtering.

13. **Knowledge base chunking:** Uses `chunk_index`/`chunk_total` columns for large articles.

14. **Intelligence reports:** Stored as JSON dict with markdown/report/content keys in `report_json` column.

### Standard Page Template

```python
from shared.styles import render_header, render_footer
from shared.ask_question import render_ask_question
from shared.fiscal_selector import render_fiscal_selector

user = st.session_state.get("auth_user")

render_header(
    title="Page Title",
    subtitle="Subtitle",
    goals=["G1", "G2"],
    strategy_context="Why this matters"
)

# Main content (tabs, filters, charts)
# ...

render_ask_question("page_context")
render_footer("Page Name", "Layer 1 data", user=user)
```

### Database Caching Pattern

```python
@st.cache_data(ttl=300)  # 5-minute cache
def load_data():
    db = Path(__file__).resolve().parent.parent / "data" / "harris_farm.db"
    with sqlite3.connect(db) as conn:
        return pd.read_sql("SELECT ...", conn)
```

---

## 16. Key Statistics

| Metric | Value |
|--------|-------|
| Total Project Size | 8.6GB |
| Python Files | 183+ (104 dashboards + 37 backend + others) |
| Lines of Python | ~59,000 (dashboards ~27K, backend ~31K) |
| API Endpoints | 254 |
| Database Tables | ~105 (hub_data.db) + sales/PLU/auth |
| Streamlit Pages | 43 across 6 sections |
| Shared Components | 40 modules |
| User Roles | 10 |
| Store Network | 21 stores, 9 regions |
| Transaction Records | 383M+ |
| PLU Records | 27.3M |
| Customers | 17K+ |
| Market Share Records | 77K+ |
| Product Numbers | 72,911+ |
| Knowledge Articles | 545+ |
| Dependencies | 22 packages |
| Documentation Files | 38+ markdown + 1 PDF |

---

## 17. File Inventory

### Project Root

```
harris-farm-hub/
├── dashboards/                    # Streamlit frontend (104 files)
│   ├── app.py                     # Entry point: st.navigation()
│   ├── landing.py                 # Home page
│   ├── nav.py                     # Navigation registry
│   ├── strategy_overview.py
│   ├── greater_goodness.py
│   ├── intro_p3_people.py
│   ├── intro_p4_operations.py
│   ├── intro_p5_digital.py
│   ├── sales_dashboard.py
│   ├── profitability_dashboard.py
│   ├── revenue_bridge_dashboard.py
│   ├── customer_dashboard.py
│   ├── store_ops_dashboard.py
│   ├── buying_hub_dashboard.py
│   ├── product_intel_dashboard.py
│   ├── plu_intel_dashboard.py
│   ├── transport_dashboard.py
│   ├── analytics_engine.py
│   ├── store_network_page.py
│   ├── market_share_page.py
│   ├── demographics_page.py
│   ├── whitespace_analysis.py
│   ├── competitor_map_page.py
│   ├── roce_dashboard.py
│   ├── cannibalisation_dashboard.py
│   ├── skills_academy.py
│   ├── skills_academy_v3.py
│   ├── the_paddock.py
│   ├── chatbot_dashboard.py
│   ├── prompt_builder.py
│   ├── rubric_dashboard.py
│   ├── approvals_dashboard.py
│   ├── workflow_engine.py
│   ├── agent_hub.py
│   ├── agent_operations.py
│   ├── adoption_dashboard.py
│   ├── trending_dashboard.py
│   ├── hub_portal.py
│   ├── marketing_assets.py
│   ├── growing_legends_academy.py
│   ├── learning_centre.py
│   ├── customer_hub/              # Customer Hub sub-dashboard (9 files)
│   ├── mdhe/                      # MDHE sub-dashboard (6 files)
│   ├── way_of_working/            # Way of Working (4 files)
│   ├── ai_adoption/               # AI Adoption (4 files)
│   └── shared/                    # 40 reusable modules
│       ├── auth_gate.py
│       ├── styles.py
│       ├── role_config.py
│       ├── data_access.py
│       ├── fiscal_selector.py
│       ├── hierarchy_filter.py
│       ├── time_filter.py
│       ├── stores.py
│       ├── ask_question.py
│       ├── kb_chat.py
│       ├── voice_realtime.py
│       ├── flag_widget.py
│       ├── hourly_charts.py
│       ├── property_intel.py
│       ├── demographic_intel.py
│       ├── whitespace_data.py
│       ├── pillar_data.py
│       ├── goal_config.py
│       ├── growth_engine.py
│       ├── schema_context.py
│       ├── challenge_bank.py
│       ├── academy_content.py
│       ├── training_content.py
│       ├── learning_content.py
│       ├── skills_content.py
│       ├── mindset_content.py
│       ├── placement_content.py
│       ├── strategic_framing.py
│       ├── portal_content.py
│       ├── pta_rubric.py
│       ├── watchdog_safety.py
│       ├── monday_connector.py
│       ├── agent_teams.py
│       ├── paddock_pool.py
│       ├── paddock_questions.py
│       ├── sa_v4_content.py
│       ├── sa_v4_foundation_checks.py
│       ├── sa_v4_live_problems.py
│       └── sa_v4_curveballs.py
├── backend/                       # FastAPI server (38 files, 31K lines)
│   ├── app.py                     # Main server (8,485 lines, 254 endpoints)
│   ├── auth.py
│   ├── transaction_layer.py
│   ├── transaction_queries.py
│   ├── data_layer.py
│   ├── data_analysis.py
│   ├── market_share_layer.py
│   ├── plu_layer.py
│   ├── plu_lookup.py
│   ├── product_hierarchy.py
│   ├── fiscal_calendar.py
│   ├── store_pl_service.py
│   ├── mdhe_db.py
│   ├── mdhe_api.py
│   ├── academy_engine.py
│   ├── skills_engine.py
│   ├── sa_v4_exercise_engine.py
│   ├── sa_v4_xp_engine.py
│   ├── sa_v4_rubric_engine.py
│   ├── sa_v4_verification.py
│   ├── sa_v4_social.py
│   ├── sa_v4_schema.py
│   ├── sa_v4_placement.py
│   ├── hipo_engine.py
│   ├── placement_engine.py
│   ├── paddock_engine.py
│   ├── paddock_layer.py
│   ├── agent_executor.py
│   ├── agent_router.py
│   ├── agent_game.py
│   ├── continuous_improvement.py
│   ├── self_improvement.py
│   ├── presentation_rubric.py
│   ├── report_generator.py
│   ├── flag_engine.py
│   ├── watchdog_scheduler.py
│   ├── import_roles.py
│   └── hub_data.db                # App state database (~105 tables)
├── data/                          # Analytics data (8.6GB)
│   ├── harris_farm.db             # Weekly sales (418MB)
│   ├── harris_farm_plu.db         # PLU results (3.1GB)
│   ├── transactions/              # POS parquets (383M rows)
│   ├── census/processed/          # ABS demographics
│   ├── cbas_network.json          # Store network data
│   ├── auth.db                    # User authentication
│   ├── outputs/                   # Generated outputs
│   └── roles/                     # Employee role data
├── watchdog/                      # Safety & governance
│   ├── audit.log
│   ├── scan.sh
│   ├── health.sh
│   ├── shutdown.sh
│   ├── validate_data.py
│   ├── procedures/                # 6 documented procedures
│   ├── learnings/                 # 7 learning documents
│   ├── rubrics/
│   └── data_checksums/
├── docs/                          # 25 documentation files
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── USER_GUIDE.md
│   ├── RUNBOOK.md
│   ├── CHANGELOG.md
│   ├── FEATURE_STATUS.md
│   ├── BEST_PRACTICES.md
│   ├── MDHE_GUIDE.md
│   ├── DIMENSION_MAPPING.md
│   ├── data_catalog.md
│   └── ...
├── orchestrator/                  # Agent orchestration (9 files)
├── paddock/                       # Paddock training app
├── the-paddock/                   # Paddock v2
├── harris_farm_weather/           # Weather intelligence
├── marketing-assets/              # Brand materials
├── scripts/                       # Utility scripts (8 files)
├── logs/                          # 38 timestamped log dirs
├── assets/                        # Images (logo.png etc.)
├── .streamlit/config.toml         # Streamlit theme config
├── CLAUDE.md                      # 7 Laws governance
├── README.md                      # Primary documentation
├── render.yaml                    # Render deployment config
├── render_start.sh                # Production startup
├── start.sh                       # Local startup
├── requirements.txt               # 22 Python packages
└── data_loader.py                 # GitHub Release downloader
```

### Dependencies (requirements.txt)

```
streamlit>=1.36    pandas         plotly          numpy
pyarrow            Pillow         requests        httpx
uvicorn[standard]  fastapi        python-multipart pydantic<2
python-dotenv      anthropic      openai          bcrypt
duckdb             openpyxl       pyyaml          folium
streamlit-folium
```

---

*Generated 2026-03-03 — Harris Farm Hub AI Centre of Excellence*
