# Feature Status Matrix
**Harris Farm Markets AI Hub — Centre of Excellence**

*Last Updated: 2026-02-18*

Legend:
- **LIVE** — Fully operational, tested, data flowing
- **PARTIAL** — Built but not fully activated or missing components
- **PLANNED** — Designed in documentation, not yet implemented
- **CONCEPT** — Idea stage, no implementation

---

## Core Infrastructure

| Feature | Status | Evidence |
|---------|--------|----------|
| FastAPI Backend | **LIVE** | `backend/app.py` — 93+ endpoints, port 8000 |
| Hub Portal (Documentation + Intelligence) | **LIVE** | `dashboards/hub_portal.py` — port 8515, 11 tabs |
| SQLite Metadata Database | **LIVE** | `backend/hub_data.db` — 35 tables, 1,009 rows |
| SQLite Aggregated Data | **LIVE** | `data/harris_farm.db` — 1.6M+ rows (weekly grain) |
| DuckDB Transaction Engine | **LIVE** | `backend/transaction_layer.py` — 383.6M POS rows |
| Hub Navigation (5 hubs) | **LIVE** | `dashboards/nav.py` — 16 dashboards across 5 hubs |
| Start/Stop Scripts | **LIVE** | `start.sh` / stop via port kill |
| WATCHDOG Governance (CLAUDE.md) | **LIVE** | 7 Laws, audit.log, 4 procedures |
| Test Suite | **LIVE** | 1,003 tests across 25 files |

---

## Dashboards (16 total)

### Financial Hub

| Dashboard | Port | Status | Data Source |
|-----------|------|--------|-------------|
| Sales | 8501 | **LIVE** | harris_farm.db (weekly) |
| Profitability | 8502 | **LIVE** | harris_farm.db (weekly) |

### Market Intel Hub

| Dashboard | Port | Status | Data Source |
|-----------|------|--------|-------------|
| Customers | 8507 | **LIVE** | harris_farm.db (weekly) |
| Market Share | 8508 | **LIVE** | harris_farm.db (weekly) |

### Operations Hub

| Dashboard | Port | Status | Data Source |
|-----------|------|--------|-------------|
| Transport | 8503 | **LIVE** | harris_farm.db (weekly) |

### Transactions Hub

| Dashboard | Port | Status | Data Source |
|-----------|------|--------|-------------|
| Store Ops | 8511 | **LIVE** | 383.6M transactions (Parquet/DuckDB) |
| Product Intel | 8512 | **LIVE** | Transactions + Product Hierarchy |
| Revenue Bridge | 8513 | **LIVE** | Transactions + Fiscal Calendar |
| Buying Hub | 8514 | **LIVE** | Transactions + Product Hierarchy |

### Learning Hub

| Dashboard | Port | Status | Data Source |
|-----------|------|--------|-------------|
| Learning Centre | 8510 | **LIVE** | 12 modules, 14 lessons (hub_data.db) |
| Prompt Builder | 8504 | **LIVE** | prompt_templates (hub_data.db) |
| The Rubric | 8505 | **LIVE** | AI training, prompt skills, multi-LLM comparison |
| Trending | 8506 | **LIVE** | Usage analytics (hub_data.db) |
| Hub Assistant | 8509 | **LIVE** | Knowledge base (536 articles), full-text search chat |
| Hub Portal | 8515 | **LIVE** | Documentation, intelligence, agents, gamification |

### Other

| Dashboard | Port | Status | Data Source |
|-----------|------|--------|-------------|
| Landing Page | 8500 | **LIVE** | Static + links to all hubs |

---

## Data Assets

| Asset | Status | Details |
|-------|--------|---------|
| Transaction Data (Parquet) | **LIVE** | 383.6M rows, 3 FYs (FY24-FY26), 34 stores, 6.6GB |
| Product Hierarchy (Parquet) | **LIVE** | 72,911 products, 5-level tree (Dept→MajGrp→MinGrp→HFM→SKU) |
| Fiscal Calendar (Parquet) | **LIVE** | 4,018 daily rows, 45 columns, FY2016-FY2026, 5-4-4 pattern |
| Weekly Aggregated (SQLite) | **LIVE** | 1.6M+ rows: sales, customers, market share (FY2017-FY2024) |
| Employee Roles | **LIVE** | 211 roles: 3 Functions, 36 Departments, 140 Jobs |
| Knowledge Base | **LIVE** | 536 articles with full-text search |
| Learning Modules | **LIVE** | 12 modules (L1-L4, D1-D4, K1-K4), 16 lessons |
| PLU → Product Join | **LIVE** | 98.3% match rate by PLU, 98.4% by revenue |
| Transaction → Fiscal Join | **LIVE** | 100% coverage (all 959 transaction dates matched) |

---

## Agent System

| Feature | Status | Details |
|---------|--------|---------|
| Agent Proposals Table | **LIVE** | 272+ proposals (hub_data.db), full status tracking |
| Agent Scores Table | **LIVE** | 192+ score records across 18 agents |
| Agent Control Panel (UI) | **LIVE** | Hub Portal tab11 — approve/reject/view scores |
| Task Approval Workflow | **LIVE** | PENDING → APPROVED → COMPLETED/FAILED/REJECTED |
| Agent Executor | **LIVE** | `backend/agent_executor.py` — polls, routes, executes, scores |
| Executor API | **LIVE** | POST /api/admin/executor/run, GET /api/admin/executor/status |
| NL Query Router | **LIVE** | `backend/agent_router.py` — keyword-based, 11 analysis types |
| Agent Task Submission (NL) | **LIVE** | POST /api/agent-tasks — accepts natural language queries |
| 11 Analysis Types | **LIVE** | basket, stockout, intraday_stockout, price, demand, slow_movers, halo_effect, specials_uplift, margin_analysis, customer_analysis, store_benchmark |
| PLU Check Digit Resolution | **LIVE** | `product_hierarchy.py` — progressive truncation for POS check digits |
| Presentation Rubric Scoring | **LIVE** | 8-dimension scoring, Board-ready/Exec-ready/Draft grades |
| Intelligence Reports Storage | **LIVE** | 41 reports generated, stored in hub_data.db |
| Self-Improvement Trigger | **LIVE** | Auto-creates improvement proposal every 5 completions |

---

## Safety & Governance

| Feature | Status | Details |
|---------|--------|---------|
| CLAUDE.md 7 Laws | **LIVE** | Checksum verified each session |
| Audit Log (watchdog/audit.log) | **LIVE** | Full trail, no gaps |
| 4 Watchdog Procedures | **LIVE** | Task execution, self-improvement, data correctness, documentation |
| WATCHDOG AST Scanner | **LIVE** | `scripts/watchdog.py` — 16 dashboards, 134 components, 20 tests |
| Health Check Script | **LIVE** | `watchdog/health.sh` — checks all 16 services |
| Scan Script | **LIVE** | `watchdog/scan.sh` — security + code quality scan |
| 7-Criteria Scoring (H/R/S/C/D/U/X) | **LIVE** | Logged per task, avg ≥7 threshold |
| WATCHDOG Safety Analysis (LLM) | **PARTIAL** | `dashboards/shared/watchdog_safety.py` exists, WatchdogService class built, not integrated into approval flow |
| Risk Level Auto-Assessment | **PARTIAL** | risk_level field exists on proposals, not auto-populated |
| SHA-256 CLAUDE.md Verification | **LIVE** | Checked at session start |

---

## Self-Improvement Loop

| Feature | Status | Details |
|---------|--------|---------|
| Score Parsing from Audit Log | **LIVE** | `self_improvement.py` parses H/R/S/C/D/U/X scores |
| Structured Score Storage | **LIVE** | `task_scores` table — 29+ records |
| Average Calculation | **LIVE** | Per-criterion averages across all tasks |
| Weakest Criterion Detection | **LIVE** | Identifies lowest-scoring dimension |
| Improvement Cycle Tracking | **LIVE** | `improvement_cycles` table — 5+ cycles recorded |
| Auto-Trigger (every 5 completions) | **LIVE** | `check_improvement_trigger()` in agent_executor.py |
| Self-Improvement Dashboard | **LIVE** | Hub Portal tab10 — KPI gauges, trends, cycles |
| Backfill from Audit History | **LIVE** | POST /api/self-improvement/backfill |
| MAX 3 Attempts per Criterion | **LIVE** | Enforced in procedure, tracked in improvement_cycles |
| A/B Testing Framework | **PLANNED** | Designed in best practices, not implemented |
| Automated Prompt Optimisation | **PLANNED** | Requires A/B framework first |

---

## Authentication & Users

| Feature | Status | Details |
|---------|--------|---------|
| User Registration/Login | **LIVE** | `backend/auth.py` — bcrypt hashing, session tokens |
| Session Management | **LIVE** | Token-based, expiry, revocation |
| Auth Gate for Dashboards | **LIVE** | `dashboards/shared/auth_gate.py` |
| Site Password | **LIVE** | Optional site-wide access code |
| Admin User Management | **LIVE** | CRUD users, view sessions, audit log |
| Role-Based Access Control | **PLANNED** | User roles exist but not enforced on endpoints |

---

## Portal & Gamification

| Feature | Status | Details |
|---------|--------|---------|
| Hub Portal (11 tabs) | **LIVE** | Documentation, data catalog, intelligence, agents, learning |
| Prompt History | **LIVE** | Tracks all prompts submitted |
| Portal Scores | **PARTIAL** | Table exists, no scores logged yet |
| Achievements | **PARTIAL** | Table exists, no achievements awarded yet |
| User Progress Tracking | **PARTIAL** | Table exists, not populated |
| Leaderboard UI | **PARTIAL** | GET /api/portal/leaderboard endpoint exists, UI minimal |

---

## Intelligence & Reporting

| Feature | Status | Details |
|---------|--------|---------|
| 11 Data Analysis Types | **LIVE** | All 11 query 383M transactions via DuckDB |
| Run Analysis API | **LIVE** | POST /api/intelligence/run/{type} |
| Report Storage | **LIVE** | 41 intelligence_reports with rubric scores |
| Report Export (JSON/CSV) | **LIVE** | GET /api/intelligence/export/{id}/{fmt} |
| Report Export (HTML/MD/PDF) | **PLANNED** | Only JSON and CSV implemented |
| Presentation Rubric | **LIVE** | 8-dimension scoring, auto-grading |
| Arena Competition | **PARTIAL** | Tables + API exist (12 proposals, 5 team stats), UI minimal |

---

## Multi-Agent Coordination

| Feature | Status | Details |
|---------|--------|---------|
| Agent-to-Analysis Routing | **LIVE** | `AGENT_ANALYSIS_MAP` in agent_executor.py |
| Sequential Proposal Execution | **LIVE** | Executor processes one at a time |
| Task Dependencies | **PLANNED** | No dependency tracking between proposals |
| Agent Swarms | **CONCEPT** | Multiple agents on one goal |
| Agent-to-Agent Task Creation | **CONCEPT** | Agents creating proposals for other agents |
| Parallel Execution | **PLANNED** | Currently sequential |

---

## API Coverage Summary

| Domain | Endpoints | Status |
|--------|-----------|--------|
| Core (query, rubric, decision, feedback) | 4 | **LIVE** |
| Templates | 2 | **LIVE** |
| Analytics | 2 | **LIVE** |
| Knowledge Base | 2 | **LIVE** |
| Chat | 1 | **LIVE** |
| Roles | 3 | **LIVE** |
| Learning | 5 | **LIVE** |
| Transactions | 8 | **LIVE** |
| Product Hierarchy | 5 | **LIVE** |
| Fiscal Calendar | 3 | **LIVE** |
| Authentication | 7 | **LIVE** |
| Admin Auth | 8 | **LIVE** |
| Portal/Gamification | 6 | **LIVE** |
| Arena | 10 | **PARTIAL** |
| Watchdog | 7 | **LIVE** |
| Intelligence | 4 | **LIVE** |
| Agent Tasks (NL) | 3 | **LIVE** |
| Self-Improvement | 5 | **LIVE** |
| Admin Agent Control | 6 | **LIVE** |
| Admin Executor | 2 | **LIVE** |
| **Total** | **~93** | |

---

## Summary Counts

| Metric | Count |
|--------|-------|
| API Endpoints | ~93 |
| Dashboards | 16 |
| Database Tables | 35 |
| Test Files | 25 |
| Tests | 1,003 |
| Backend Modules | 16 |
| Analysis Types | 11 |
| Transaction Rows | 383.6M |
| Products | 72,911 |
| Knowledge Articles | 536 |
| Intelligence Reports | 140+ |
| Agent Proposals | 272+ |
| Agent Scores | 192+ |
| Watchdog Procedures | 4 |

---

## What's Next

See **[ACTIVATION_ROADMAP.md](ACTIVATION_ROADMAP.md)** for the phased plan to move PARTIAL features to LIVE and implement PLANNED features.
