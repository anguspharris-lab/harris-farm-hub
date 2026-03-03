# Feature Status Matrix
**Harris Farm Markets AI Hub — Centre of Excellence**

*Last Updated: 2026-02-27*

Legend:
- **LIVE** — Fully operational, tested, data flowing
- **PARTIAL** — Built but not fully activated or missing components
- **PLANNED** — Designed in documentation, not yet implemented
- **CONCEPT** — Idea stage, no implementation

---

## Core Infrastructure

| Feature | Status | Evidence |
|---------|--------|----------|
| FastAPI Backend | **LIVE** | `backend/app.py` — ~264 endpoints, port 8000 |
| Hub Navigation (6 sections) | **LIVE** | Single multi-page app via `st.navigation()` in `dashboards/app.py` — 43 pages |
| SQLite Metadata Database | **LIVE** | `backend/hub_data.db` — ~105 tables |
| SQLite Aggregated Data | **LIVE** | `data/harris_farm.db` — 1.6M+ rows (weekly grain) |
| DuckDB Transaction Engine | **LIVE** | `backend/transaction_layer.py` — 383.6M POS rows |
| Census Data Processing | **LIVE** | `scripts/process_census.py` — ABS SA1-to-postcode, occupation/income/age profiles |
| CBAS Network Data | **LIVE** | `data/cbas_network.json` — 31 stores, 16 whitespace opportunities |
| Render Deployment | **LIVE** | https://harris-farm-hub.onrender.com — persistent disk, GitHub Releases data |
| Data Loader | **LIVE** | `data_loader.py` — auto-downloads data from GitHub Releases on deploy |
| Start/Stop Scripts | **LIVE** | `start.sh` / `render_start.sh` — single Streamlit process, non-blocking backend startup |
| WATCHDOG Governance (CLAUDE.md) | **LIVE** | 7 Laws, audit.log, 4 procedures |
| Test Suite | **LIVE** | 1,003 tests across 25 files |

---

## Dashboards (43 pages — single multi-page app)

### Strategy (6 pages)

| Dashboard | Status | Data Source |
|-----------|--------|-------------|
| Home (Landing) | **LIVE** | hub_data.db (live metrics), harris_farm.db — strategy pillars, goals, quick launch, activity feed, WATCHDOG, system health |
| Strategy Overview | **LIVE** | Static content + strategy framework |
| Greater Goodness | **LIVE** | Static content + goals |
| Growing Legends (Intro) | **LIVE** | Pillar intro page |
| Operations HQ (Intro) | **LIVE** | Pillar intro page |
| Digital & AI HQ (Intro) | **LIVE** | Pillar intro page |

### Growing Legends (4 pages)

| Dashboard | Status | Data Source |
|-----------|--------|-------------|
| Skills Academy | **LIVE** | Growing Legends Academy — 6-level maturity model, 7 prompt patterns, 6 learning paths, site quality rubrics, **Gamification Engine:** XP system (13 action types), streak tracking (1.0-2.0x multiplier), 60 daily challenges, 21 badges, leaderboard, 10 tabs |
| The Paddock | **LIVE** | AI practice conversations (session state) |
| Prompt Engine | **LIVE** | 20 task templates, PtA workflow — generate, score, iterate, annotate, submit (hub_data.db) |
| Hub Assistant | **LIVE** | Knowledge base (545 articles), full-text search chat |

### Operations (10 pages)

| Dashboard | Status | Data Source |
|-----------|--------|-------------|
| Customer Hub | **LIVE** | harris_farm.db (weekly) |
| Sales | **LIVE** | harris_farm.db (weekly) |
| Profitability | **LIVE** | harris_farm.db (weekly) |
| Revenue Bridge | **LIVE** | 383.6M transactions (Parquet/DuckDB) + Fiscal Calendar |
| Store Ops | **LIVE** | 383.6M transactions (Parquet/DuckDB) |
| Buying Hub | **LIVE** | Transactions + Product Hierarchy |
| Product Intel | **LIVE** | Transactions + Product Hierarchy |
| PLU Intelligence | **LIVE** | harris_farm_plu.db (27.3M rows) — 6 views: Dept Summary, Wastage Hotspots, Stocktake Variance, Top Revenue PLUs, Store Benchmarking, PLU Lookup |
| Transport | **LIVE** | harris_farm.db (weekly) |
| Analytics Engine | **LIVE** | Data Intelligence — run analyses, reports, agent tasks (hub_data.db + harris_farm.db) |

### Property (7 pages)

| Dashboard | Status | Data Source |
|-----------|--------|-------------|
| Store Network | **LIVE** | 8 tabs — overview, performance, geography, trade areas, competition, demographics, trends, data quality. Census integration, trade area analysis |
| Whitespace Analysis | **LIVE** | 6 tabs — opportunity map, scoring, demographics, cannibalisation risk, financial model, summary. 16 opportunities scored |
| Demographics | **LIVE** | 6 tabs — overview, income, occupation, age, household, comparison. ABS census data |
| Market Share | **LIVE** | Placeholder — enhanced version. harris_farm.db (77K rows) |
| Competitor Map | **LIVE** | Placeholder — competitive landscape mapping |
| ROCE Analysis | **LIVE** | Return on capital employed dashboard |
| Cannibalisation | **LIVE** | Distance-based cannibalisation analysis |

### MDHE (4 pages)

| Dashboard | Status | Data Source |
|-----------|--------|-------------|
| MDHE Dashboard | **LIVE** | 5-tab health scores, domain scoring, trend charts |
| MDHE Upload | **LIVE** | CSV/Excel upload, preview, auto-validation |
| MDHE Issues | **LIVE** | Issue tracker, status workflow (Open/In Progress/Resolved) |
| MDHE Guide | **LIVE** | Renders `docs/MDHE_GUIDE.md` in-app |

### Back of House (11 pages)

| Dashboard | Status | Data Source |
|-----------|--------|-------------|
| The Rubric | **LIVE** | AI training, prompt skills, multi-LLM comparison |
| Approvals | **LIVE** | Managers review/approve/reject PtA submissions, rubric scorecard display (hub_data.db) |
| Workflow Engine | **LIVE** | 4P state machine (Prompt-Prove-Propose-Progress), multi-project tracking, talent radar, velocity metrics (hub_data.db) |
| Agent Operations | **LIVE** | WATCHDOG safety & agent control pipeline (hub_data.db) |
| Mission Control | **LIVE** | Documentation, data catalog, showcase, self-improvement (hub_data.db) |
| AI Adoption | **LIVE** | Organisation-wide platform usage metrics (hub_data.db) |
| Trending | **LIVE** | System analytics & usage (hub_data.db) |
| Agent Hub | **LIVE** | Scoreboard, Arena, Agent Network (hub_data.db) |
| Marketing Assets | **LIVE** | Marketing content and asset management |
| Way of Working | **LIVE** | Culture and ways of working content |
| User Management | **LIVE** | Admin page for user CRUD, role assignment, session management |

### Cross-cutting

| Feature | Status | Data Source |
|---------|--------|-------------|
| Goal Alignment (all pages) | **LIVE** | `render_header(goals=, strategy_context=)` — coloured G1-G5 badges + strategy context |

---

## Data Assets

| Asset | Status | Details |
|-------|--------|---------|
| Transaction Data (Parquet) | **LIVE** | 383.6M rows, 3 FYs (FY24-FY26), 34 stores, 6.6GB |
| Product Hierarchy (Parquet) | **LIVE** | 72,911 products, 5-level tree (Dept-MajGrp-MinGrp-HFM-SKU) |
| Fiscal Calendar (Parquet) | **LIVE** | 4,018 daily rows, 45 columns, FY2016-FY2026, 5-4-4 pattern |
| Weekly Aggregated (SQLite) | **LIVE** | 1.6M+ rows: sales, customers, market share (FY2017-FY2024) |
| PLU Weekly Results (SQLite) | **LIVE** | harris_farm_plu.db — 27.3M rows, 3 FYs, 43 stores, 26K+ PLUs, 3.1GB |
| Census Data (Processed) | **LIVE** | `data/census/processed/` — 4 parquet/csv files, 2.8MB. ABS SA1-to-postcode aggregation |
| CBAS Network Data | **LIVE** | `data/cbas_network.json` — 31 stores, 16 whitespace opportunities |
| Postcode Coordinates (JSON) | **LIVE** | 1,040 Australian postcode lat/lon coordinates |
| Store Coordinates | **LIVE** | 32 retail store lat/lon in `backend/market_share_layer.py` |
| Employee Roles | **LIVE** | 211 roles: 3 Functions, 36 Departments, 140 Jobs |
| Knowledge Base | **LIVE** | 536 articles with full-text search |
| Learning Modules | **LIVE** | 12 modules (L1-L4, D1-D4, K1-K4), 16 lessons |
| PLU-Product Join | **LIVE** | 98.3% match rate by PLU, 98.4% by revenue |
| Transaction-Fiscal Join | **LIVE** | 100% coverage (all 959 transaction dates matched) |
| ROC Analysis Outputs | **LIVE** | `data/outputs/roc/` — Ring of Confidence trade area scoring |
| Market Share Outputs | **LIVE** | `data/outputs/market_share/` — postcode-level market share |
| Demographics Outputs | **LIVE** | `data/outputs/demographics/` — demographic scoring and profiles |

---

## Master Data Health Engine (MDHE)

| Feature | Status | Details |
|---------|--------|---------|
| 4-Layer Validation Engine | **LIVE** | Rules (35%), Standards (30%), AI (20%), Recon (15%) |
| Domain Scoring (5 domains) | **LIVE** | PLU, Barcode, Pricing, Hierarchy, Supplier — 0-100 |
| EAN-13 Barcode Validation | **LIVE** | Check digit algorithm |
| Data Upload & Ingestion | **LIVE** | CSV/Excel upload, column preview, auto-validation |
| Issue Tracker | **LIVE** | Open/In Progress/Resolved workflow |
| Demo Data Seeding | **LIVE** | 10 PLUs with deliberate quality issues, is_dummy cleanup |
| MDHE API (10 endpoints) | **LIVE** | /api/mdhe/ — scores, validations, issues, scan-results, plu-records |
| MDHE Guide (in-app) | **LIVE** | Renders team documentation within the Hub |
| Vision Scan Integration | **PLANNED** | Needs warehouse scan data upload |
| POS Scan Integration | **PLANNED** | Needs POS scan report upload |
| AI Layer (Claude) | **PLANNED** | Batch anomaly detection, fuzzy duplicate matching |
| Signup Approval Workflow | **PLANNED** | New users default to viewer, admin approves |

---

## Property Intelligence

| Feature | Status | Details |
|---------|--------|---------|
| Census Data Processing | **LIVE** | ABS SA1-to-postcode, occupation/income/age profiles |
| ROC Analysis | **LIVE** | Ring of Confidence trade area scoring |
| Store Network Dashboard | **LIVE** | 8 tabs — overview, performance, geography, trade areas, competition, demographics, trends, data quality |
| Whitespace Analysis | **LIVE** | 6 tabs — opportunity map, scoring, demographics, cannibalisation risk, financial model, summary |
| Demographics Dashboard | **LIVE** | 6 tabs — overview, income, occupation, age, household, comparison |
| Cannibalisation Risk | **LIVE** | Distance-based cannibalisation analysis |
| ROCE Analysis | **LIVE** | Return on capital employed dashboard |
| CBAS Network Data | **LIVE** | 31 stores, 16 whitespace opportunities |

---

## Agent System

| Feature | Status | Details |
|---------|--------|---------|
| Agent Proposals Table | **LIVE** | 272+ proposals (hub_data.db), full status tracking |
| Agent Scores Table | **LIVE** | 192+ score records across 18 agents |
| Agent Control Panel (UI) | **LIVE** | Agent Operations — approve/reject/view scores |
| Task Approval Workflow | **LIVE** | PENDING - APPROVED - COMPLETED/FAILED/REJECTED |
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
| WATCHDOG AST Scanner | **LIVE** | `scripts/watchdog.py` — 23 pages, 134 components, 20 tests |
| Health Check Script | **LIVE** | `watchdog/health.sh` — checks all 23 pages |
| Scan Script | **LIVE** | `watchdog/scan.sh` — security + code quality scan |
| 7-Criteria Scoring (H/R/S/C/D/U/X) | **LIVE** | Logged per task, avg >=7 threshold |
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
| Self-Improvement Dashboard | **LIVE** | Mission Control tab 4 — KPI gauges, trends, cycles |
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
| Password Reset | **LIVE** | POST /api/auth/reset-password — requires site access code |
| Credential Sync | **LIVE** | `init_auth_db()` re-syncs from env vars on every startup |
| Admin User Management | **LIVE** | CRUD users, view sessions, audit log |
| Role-Based Access Control | **LIVE** | 10 roles defined, enforced on navigation |
| SLT Auto-Promotion | **LIVE** | AUTH_SLT_EMAILS env var — automatic SLT role assignment |
| User Management UI | **LIVE** | Admin page for role assignment and user administration |
| Hub Role Filtering | **LIVE** | `shared/role_config.py` — 10 roles, _RESTRICTED_SLUGS, page-level access control |

---

## Prompt-to-Approval System

| Feature | Status | Details |
|---------|--------|---------|
| Prompt Engine (20 templates) | **LIVE** | Role-filtered task templates, Claude/ChatGPT/Grok generation |
| 8-Criteria Standard Rubric | **LIVE** | `shared/pta_rubric.py` — AF, ST, AC, VQ, CO, BR, DI, HO (1-10 each) |
| 5-Tier Advanced Rubric | **LIVE** | CTO Panel, CLO Panel, Strategic, Implementation, Presentation |
| Human Annotation Gate | **LIVE** | Must add >=1 annotation before submission |
| Approval Workflow (4 levels) | **LIVE** | L1 Team - L2 Department - L3 Executive - L4 Board |
| Approvals Dashboard | **LIVE** | `approvals_dashboard.py` — review, approve, request changes |
| AI Ninja Gamification | **LIVE** | 4 levels (Apprentice - Specialist - Master - Ninja), points, leaderboard |
| Auto-Save to Library | **LIVE** | Prompts scoring 9.0+ auto-saved to prompt_templates, 200 pts |
| Data Confidence Badges | **LIVE** | Source reliability scoring (POS=10, Competitor=4, etc.) |
| PtA Audit Log | **LIVE** | Every action tracked in `pta_audit_log` table |
| PtA Points System | **LIVE** | `pta_points_log` table — generate, score, submit, approve actions |
| PtA Leaderboard | **LIVE** | GET /api/pta/leaderboard — top users by points |
| Similar Prompts Hint | **LIVE** | Shows matching library prompts when creating new ones |
| Iteration Loop | **LIVE** | Challenge AI, add context, refine — max 5 iterations |

---

## Portal & Gamification

| Feature | Status | Details |
|---------|--------|---------|
| Mission Control (4 tabs) | **LIVE** | Documentation, data catalog, showcase, self-improvement |
| Agent Hub (3 tabs) | **LIVE** | Scoreboard, Arena, Agent Network |
| Analytics Engine (4 tabs) | **LIVE** | Run Analysis, Reports, Agent Tasks, Demo Insights |
| Agent Operations (4 tabs) | **LIVE** | Safety Review, Approval Queue, Execution, Audit Trail |
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
| Prompt-to-Approval | 10 | **LIVE** |
| Roles | 3 | **LIVE** |
| Role Management | 5 | **LIVE** |
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
| Academy Gamification | 10 | **LIVE** |
| MDHE | 10 | **LIVE** |
| Page Analytics | 4 | **LIVE** |
| Property Intelligence | 8 | **LIVE** |
| Market Share | 6 | **LIVE** |
| Demographics | 4 | **LIVE** |
| Store Network | 5 | **LIVE** |
| **Total** | **~264** | |

---

## Summary Counts

| Metric | Count |
|--------|-------|
| API Endpoints | ~264 |
| Pages | 43 |
| Database Tables | ~105 |
| Nav Sections | 6 |
| Roles | 10 |
| Test Files | 25 |
| Tests | 1,003 |
| Backend Modules | 16 |
| Analysis Types | 11 |
| Transaction Rows | 383.6M |
| Products | 72,911 |
| Knowledge Articles | 545 |
| Intelligence Reports | 140+ |
| Agent Proposals | 272+ |
| Agent Scores | 192+ |
| Watchdog Procedures | 4 |

---

## What's Next

See **[ACTIVATION_ROADMAP.md](ACTIVATION_ROADMAP.md)** for the phased plan to move PARTIAL features to LIVE and implement PLANNED features.
