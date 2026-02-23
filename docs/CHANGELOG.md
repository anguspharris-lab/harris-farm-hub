# Harris Farm Hub — Changelog

> All notable changes to the Hub are documented here.

---

## [3.7.0] - 2026-02-23

### Added
- **Usage Analytics Engine** — page-view tracking across every Hub page with adoption dashboard
  - `backend/analytics_engine.py`: Page view logging, aggregate stats, role breakdowns, user activity
  - `page_views` table with indexes on user, slug, and date
  - 4 API endpoints: `POST /api/analytics/pageview`, `GET /api/analytics/summary`, `GET /api/analytics/users`, `GET /api/analytics/by-role`
  - Fire-and-forget page-view logging in `app.py` (timeout=1, never blocks rendering)
- **Adoption Dashboard** (`dashboards/adoption_dashboard.py`) — proves value to board
  - 4 KPI cards: Unique Users, Total Page Views, Avg Pages/User, Top Page
  - Daily activity line+bar chart, Top 10 pages, Usage by role pie chart, User activity table
  - Time range selector (7/14/30/90 days), cached API calls (TTL 60s)
  - Registered under P5 Digital & AI navigation
- **Role-Based Navigation** — reduces 33 pages to 5-10 per role
  - `dashboards/shared/role_config.py`: 9 roles (admin, user, executive, store_manager, buyer, marketing, people_culture, finance, viewer)
  - Each role sees only relevant pages; admin and user see all
  - `hub_role` column added to users table (safe ALTER TABLE migration)
  - Sidebar role selector for new users with default "user" role
  - 2 API endpoints: `PUT /api/auth/role`, `GET /api/auth/roles`
  - Navigation dynamically filters pillars, sub-pages, and utility pages
- **Home Page Search Bar** — unblocks users who can't find what they need
  - Dual-source search: fuzzy page title/slug matching + Knowledge Base FTS5 via existing `/api/knowledge/search`
  - Page matches shown as `st.page_link()` buttons, KB results as expandable cards with snippets
  - Inline results below search bar, clean homepage when empty

### Changed
- Pages: 32 → 33 (added Adoption Dashboard under P5)
- API endpoints: ~147 → ~153 (4 analytics + 2 role management)
- Database tables: ~56 → ~57 (page_views table)
- `shared/auth_gate.py`: Dev bypass now returns `hub_role: "admin"`
- `backend/auth.py`: `authenticate_user()` and `verify_session()` now return `hub_role`
- Navigation header: only shows pillars and sub-pages visible to current role

### Scores
- P0 Fixes: H:9 R:9 S:9 C:8 D:8 U:9 X:8 = 8.6 (SHIP)

---

## [3.6.0] - 2026-02-22

### Added
- **Strategic Hub Rebuild** — 12 new files transforming Hub from dashboard collection to strategic platform
  - 4 Pillar intro pages: Greater Goodness, Growing Legends, Operations HQ, Digital & AI HQ
  - Way of Working page with Monday.com integration (live board embedding)
  - Marketing Assets page with 19 files across 6 categories (brand, amazon, ecomm, weekend-specials, ooh, butcher)
  - Customer Hub rebuild with customer intelligence tabs
  - AI Adoption dashboard
- **"First Day at The Hub" Simulation** — 9-document evaluation suite in `docs/simulation/`
  - 10 personas tested across all Hub pages, scored 6.4/10 overall
  - Executive summary, persona cards, journey simulations, scoring matrix, panel commentary
  - Golden paths, improvement backlog, rollout plan, marketing deep-dive

### Changed
- Navigation restructured with pillar-based grouping and two-row header
- Pages: 26 → 32 (6 new pages added)

---

## [3.5.0] - 2026-02-22

### Added
- **Academy Gamification Engine** — transforms the Growing Legends Academy from content-only to interactive XP-driven learning
  - XP system: 13 action types (login, module_complete, arena_submit, daily_challenge, prompt_score, badge_earned, quality_review, etc.)
  - 6-level progression matching maturity model: Seed (0-99) → Sprout (100-299) → Grower (300-599) → Harvester (600-999) → Cultivator (1000-1499) → Legend (1500+)
  - Streak engine: consecutive day tracking, 0.1x multiplier per day (max 2.0x), auto-awards login XP
  - Daily challenges: 60 pre-seeded challenges (prompt_writing, quiz, score_this, pattern_practice, module_complete), deterministic daily rotation
  - Badge system: 21 badges across 5 categories (achievement, streak, level, arena, learning), auto-detection and award
  - Leaderboard: period filtering (all/week/month), XP-ranked with level icons and streak counts
- **New backend module:** `backend/academy_engine.py` (380 lines) — all gamification logic centralised
- **5 new database tables:** academy_xp_log, academy_streaks, academy_daily_challenges, academy_daily_completions, academy_badges
- **10 new API endpoints:** `/api/academy/` (xp/award, xp/{user}, profile/{user}, streak/checkin, streak/{user}, leaderboard, daily-challenge, daily-challenge/complete, badges/{user}, badges/check)
- **Academy page:** 2 new tabs (My Progress, Leaderboard), "You Are Here" marker on Journey tab, XP rewards callout on Arena tab
- **Sidebar XP widget:** persistent level + XP display on every page, session-guarded streak check-in
- **Integration hooks:** module completion → +50 XP, daily login → +5 XP, quality review → +10 XP

---

## [3.4.0] - 2026-02-22

### Added
- **Prompt-to-Approval System** — the core workflow for making Harris Farm a data-first business
  - **Prompt Engine** (`prompt_builder.py` rewrite): 20 role-filtered task templates (weekly store performance, waste analysis, board paper, roster optimisation, etc.), Claude/ChatGPT/Grok AI generation, iteration loop, human annotation gate
  - **Rubric Engine** (`shared/pta_rubric.py`): 8-criteria standard rubric (Audience Fit, Storytelling, Actionability, Visual Quality, Completeness, Brevity, Data Integrity, Honesty) + 5-tier advanced rubric (CTO Panel, CLO Panel, Strategic Alignment, Implementation Readiness, Presentation Quality)
  - **Approvals Dashboard** (`approvals_dashboard.py`): New page — managers review, approve, or request changes on PtA submissions. Status filtering, rubric scorecard display, approval/reject actions
  - **10 PtA API endpoints**: generate, score, submit, list/get submissions, approve, request-changes, user-stats, leaderboard
  - **3 database tables**: `pta_submissions` (full workflow state), `pta_audit_log` (every action tracked), `pta_points_log` (gamification points)
  - **AI Ninja Gamification**: 4 levels (Prompt Apprentice → Prompt Specialist → Prompt Master → AI Ninja), points for generate/score/submit/approve actions, leaderboard
  - **Auto-save to library**: Prompts scoring 9.0+ automatically saved to `prompt_templates` with 200 bonus points
  - **Data confidence badges**: Source reliability scoring (POS=10, Competitor=4, etc.)
  - **6 PtA lessons** seeded into knowledge base (545 total articles)
- **Market Share improvements**: Store Health Scorecard refinements, trend slope visualisation enhancements
- **PLU Intelligence**: Dashboard layout and query improvements

### Changed
- Dashboards: 23 → 24 (added Approvals under P3)
- API endpoints: ~93 → ~103 (added 10 PtA endpoints)
- Database tables: 35 → 38 (3 PtA tables)
- Knowledge base: 536 → 545 articles (6 PtA lessons)
- Prompt Builder renamed to Prompt Engine (rocket icon)
- P3 (Growing Legendary Leadership): 6 → 7 pages

### Scores
- PtA System: AF:8 ST:8 AC:9 VQ:7 CO:8 BR:8 DI:7 HO:9 = 8.0 (SHIP)

---

## [3.3.0] - 2026-02-22

### Added
- **KB Chat Unification** (`shared/kb_chat.py`): Shared chat component for Hub Assistant and Learning Centre Company Knowledge tab. Key-prefixed widget namespacing prevents DuplicateWidgetID errors
- **Hub Restructure**: Broke up portal monolith — Mission Control, Agent Hub, Analytics Engine, Agent Operations now separate pages
- **"When In Doubt, Ask AI" lesson**: New Start Here lesson seeded into Learning Centre

### Fixed
- Hub Assistant "0 documents | 0 words" — self-healing cache clears on empty result
- Company Knowledge search empty text — `doc.get("content")` → `doc.get("snippet")`
- Quick Links destroying session state — HTML `<a href>` → `st.page_link()`

---

## [3.2.0] - 2026-02-21

### Added
- **Goal Alignment on All 19 Dashboards**: Every page now shows coloured goal badges (G1-G5) and a strategy context line connecting data to "Fewer, Bigger, Better". Enhanced `render_header()` in `shared/styles.py` with optional `goals` and `strategy_context` parameters (backward compatible).
- **Interactive Page Quality Scoring** (Academy Tab 7): Score any Hub page against rubric criteria, direct SQLite write, leaderboard
- **PageQualityAuditor**: Low scores generate improvement findings, closing the self-improvement loop
- **Auto-Ingest Score Pipeline**: `backfill_scores_from_audit()` runs at startup, zero overhead after first run
- **2 API endpoints**: `POST /api/page-quality/score`, `GET /api/page-quality/scores`

### Changed
- **Front Page Restructured**: Strategy pillars moved from Section 6 (bottom) to Section 2 (right after hero). "Our Strategy: Fewer, Bigger, Better" headline frames the page. System health metrics moved to collapsible expander.
- **Rubric Scoring Tightened**: `_score_audience` base 5->2, `_score_visual` base 3->1, `_score_brief` inverted (build from 0), `_score_action` graduated. Average drops from ~9.76 to realistic 6-7 range.
- **Score Regex Fixed**: Now catches all 6 audit.log score formats (was 2). D=N/A handled, stored as 0, excluded from averages.
- **PLU Intelligence**: Migrated from `st.title` to `render_header` with G2+G4 goal alignment

### Removed
- **4 stale docs deleted**: DEPLOYMENT_GUIDE.md, EXECUTIVE_SUMMARY.md, watchdog/handover.md, watchdog/INSTALL_PROMPT.md
- **510 junk DB rows deleted**: 145 test agent proposals, 129 zombie PENDING, 235 duplicate findings, 1 test template
- **Mock data removed** from Prompt Builder "Run Test Query" (replaced with honest SQL preview)
- **Port references removed** from user-facing text (3 dashboards + 1 shared module)

### Fixed
- Error messages no longer expose "port 8000" to users (3 files)
- Stale counts updated across 17 files (dashboards: 16/17->19, endpoints: 71+/80+/93+->112, analysis types: 6->11)
- 5 test expectations updated for tighter rubric scoring

### Scores
- Legacy Cleanup: H:9 R:9 S:9 C:9 D:9 U:9 X:9 = 9.0
- Goal Alignment: H:9 R:9 S:9 C:9 D:9 U:9 X:9 = 9.0

---

## [3.1.0] - 2026-02-21

### Added
- **PLU Intelligence Dashboard** (`plu_intel_dashboard.py`): 6 analytical views — Department Summary, Wastage Hotspots, Stocktake Variance, Top Revenue PLUs, Store Benchmarking, PLU Lookup with weekly trends and store breakdown
- **PLU Data Layer** (`backend/plu_layer.py`): Query engine for `harris_farm_plu.db` (27.3M rows, 3 fiscal years, 43 stores, 26K+ PLUs)
- **PLU Database** (`harris_farm_plu.db`, 3.1GB): Ingested from 3 years of weekly PLU results — tables: weekly_plu_results, dim_item (75K), dim_store (43), dim_week (156). Deployed via GitHub Releases (split into 2 parts)
- **Market Share Data Interpretation Rules** added to CLAUDE.md: 10 critical rules for CBAS data including distance tiers, Layer 1/2 separation, empirical success profiles

### Changed
- Dashboards: 17 → 18 (added PLU Intelligence under Pillar 4 Operations)
- `data_loader.py`: Added PLU database download (2 parts, 3.1GB total)
- `.gitignore`: Added `*.part_*` pattern

---

## [3.0.0] - 2026-02-21

### Added
- **Market Share Dashboard — Complete Rebuild** with 7 tabs:
  - Overview: national/state KPIs and trend charts, top/bottom 15 postcodes
  - Spatial Map: interactive Plotly mapbox with 886 postcodes + 32 store markers, colored by share/penetration/spend/distance tier
  - Store Trade Areas: select any store to see Core/Primary/Secondary/Extended postcode tiers with performance data and trend charts
  - Trends & Shifts: YoY comparison with gainers/losers, RdYlGn diverging share-change map, month-on-month anomaly detection
  - Opportunities: quadrant scatter (penetration vs share) identifying Strongholds, Growth Opportunities, Basket Opportunities, Retention Risks
  - Issues: automated flagging of Core/Primary trade area share declines with severity levels
  - Data Explorer: full filterable/sortable table with CSV download
- **Market Share Data Layer** (`backend/market_share_layer.py`): 32 geocoded store locations, 1,040 postcode coordinates, haversine distance calculations, trade area analysis, YoY comparison, shift detection, issue flagging, opportunity scoring
- **Postcode coordinates** (`data/postcode_coords.json`): 1,040 Australian postcode lat/lon via pgeocode/ABS data

---

## [2.6.0] - 2026-02-20

### Added
- **Single Multi-Page App Consolidation**: All 17 dashboards consolidated into one `st.navigation()` app via `dashboards/app.py`. Single process, native sidebar nav, shared session state.
- **Authentication System**: Site password + user accounts with login/register/password-reset. `shared/auth_gate.py` → `backend/auth.py`
- **Session-safe navigation**: All HTML `<a href>` links replaced with `st.page_link()` to preserve `st.session_state`
- **Render Deployment**: Live at https://harris-farm-hub.onrender.com with persistent disk, data files via GitHub Releases
- **Data Loader** (`data_loader.py`): Auto-downloads data files from GitHub Releases on first deploy. Handles multi-part files >2GB.
- **Password Reset**: POST `/api/auth/reset-password` endpoint — requires site access code for identity verification

### Changed
- Architecture: 17 separate Streamlit processes → 1 multi-page app
- `init_auth_db()`: Now re-syncs site password and admin credentials from env vars on every startup
- Landing page: Complete rewrite using `st.page_link()` for all navigation links
- Deployment scripts: `render_start.sh`, `start.sh`, `docker-compose.yml` updated for single-process

---

## [2.5.0] - 2026-02-18

### Added
- **Margin Erosion Analysis** (`run_margin_analysis`): Finds products with GP% significantly below department average. Compares product-level margins to dept benchmarks across stores. Actionable for buyers (cost renegotiation) and store managers (markdown review)
- **Customer Segmentation Analysis** (`run_customer_analysis`): RFM-style segmentation of loyalty customers into Champion, Big Spender, Loyal, Regular, At Risk, Occasional, Lapsed. Two evidence tables: segment summary + top 20 individual customers
- **Store Benchmark / Comparison** (`run_store_benchmark`): Network-wide store ranking across 6 KPIs (revenue, basket value, items/basket, rev/day, GP%, transaction count) with PERCENT_RANK() percentile scoring
- **3 new agents**: MarginAnalyzer, CustomerAnalyzer, StoreBenchmarkAnalyzer — full lifecycle with proposals, approval, execution, rubric scoring
- **Scheduled analysis runs**: `ANALYSIS_SCHEDULE_HOURS` env var (default 168 = weekly). Auto-creates proposals for all 11 agents via threading.Timer daemon
- **4 new training challenges**: b4 (Customer Loyalty Spotlight), i4 (Margin Erosion Investigation), i5 (Store League Table), a4 (At-Risk Customer Recovery Plan)

### Changed
- Analysis types: 8 → 11 (added margin_analysis, customer_analysis, store_benchmark)
- Agent types: 8 → 11 in AGENT_ANALYSIS_MAP
- NL router: 11 keyword groups, "margin" moved from price_dispersion to margin_analysis
- Training challenges: 9 → 13 (4 new across beginner/intermediate/advanced)
- BEST_PRACTICES.md, FEATURE_STATUS.md updated to reflect 11 analysis types and 11 agents

---

## [2.4.0] - 2026-02-18

### Added
- **Halo Effect analysis** (`run_halo_effect`): Identifies products that lift basket value when present. Compares avg basket value with vs without each product. Top finding: Lescure Butter 5.18x multiplier at Mosman
- **Specials Uplift Forecast** (`run_specials_uplift`): Detects historical price drops >15% below median, measures demand multiplier, forecasts weekly order quantities per store. Top finding: Tomato Sweet Delight 2.1x at 26% discount
- **HaloAnalyzer + SpecialsAnalyzer agents**: Full agent lifecycle — proposals, approval, execution, rubric scoring (both scored 9.9/10 Board-ready)
- **PLU check digit resolution**: `get_product_by_plu()` now handles POS check digits via progressive truncation (e.g., 502771 → 50277 = BEEF PORTERHOUSE STEAK). 100% match rate on all test PLUs
- **2 new learning lessons**: D2L2 (Using the Intelligence System — 8 analysis types, NL routing), D3L2 (Reading Intelligence Reports — interpreting halo, specials, stockout, basket reports)
- **Updated L4 templates**: Added Buyer template for specials order forecasting, Store Manager template for halo product placement

### Changed
- Analysis types: 6 → 8 (added halo_effect, specials_uplift)
- Agent types: 6 → 8 in AGENT_ANALYSIS_MAP (added HaloAnalyzer, SpecialsAnalyzer)
- NL router keywords: Added halo_effect and specials_uplift routing in agent_router.py
- Learning content: D1 lesson corrected (29 → 34 stores, 4-5-4 → 5-4-4 fiscal calendar, added transaction data overview)
- K1 lesson: Updated store count to 34
- BEST_PRACTICES.md: Updated agent table, keyword map, PLU truncation pattern, endpoint counts
- FEATURE_STATUS.md: Updated analysis types, endpoint counts, learning lesson count
- Intelligence reports now show product names instead of raw PLU numbers (100% resolution)

---

## [2.3.0] - 2026-02-18

### Added
- **Full 6-agent analysis cycle**: Expanded `POST /api/admin/trigger-analysis` to create proposals for all 6 agent types (StockoutAnalyzer, BasketAnalyzer, DemandAnalyzer, PriceAnalyzer, SlowMoverAnalyzer, ReportGenerator)
- **3 new agent types activated**: DemandAnalyzer (10.0 avg), PriceAnalyzer (9.9 avg), SlowMoverAnalyzer (9.8 avg)
- **Self-improvement auto-trigger verified**: 4 improvement proposals auto-created and executed at 5-completion intervals

### Changed
- Completed proposals: 214 → 248 (+34 new Board-ready analyses)
- Agent scores: 5 → 8 real agents with scored data
- ReportGenerator improved +0.40 points (9.00 → 9.40) — exceeds +0.3 success criteria
- Phase 2 of Activation Roadmap marked complete

---

## [2.2.1] - 2026-02-18

### Fixed
- **Rubric Dashboard (8505)**: Fixed deprecated Streamlit query params API in auth_gate.py causing intermittent failures
- **Hub Assistant (8509)**: Added knowledge base seed data for fresh installs (536 articles already present in existing DB)
- **Prompt Builder (8504)**: Added prompt template seed data (6 Harris Farm examples) for fresh installs
- **auth_gate.py**: Migrated from deprecated `st.experimental_get/set_query_params` to `st.query_params` API

### Changed
- Backfilled task scores from audit.log into task_scores table (20 entries, avg 8.86)
- Established Phase 1 monitoring baseline: 16/16 dashboards healthy, 1,117 tests, 106 endpoints, 214 completed proposals
- All 16 dashboards now reliably start and respond to health checks

---

## [2.2.0] - 2026-02-17

### Added
- **Transaction Data Layer** (`backend/transaction_layer.py`, `backend/transaction_queries.py`):
  - TransactionStore class querying 383.6M POS transactions via DuckDB
  - 41 pre-built SQL queries (7 hierarchy-aware, 10 fiscal-period-aware)
  - 8 API endpoints: summary, stores, top-items, store-trend, PLU lookup, custom query, query catalog, run named query
- **Product Hierarchy** (`backend/product_hierarchy.py`, `backend/plu_lookup.py`):
  - 72,911 products from Product Hierarchy 20260215.xlsx → `data/product_hierarchy.parquet`
  - 5-level tree: Department (9) → Major Group (30) → Minor Group (405) → HFM Item (4,465) → SKU
  - 5 API endpoints: departments, browse, search, stats
  - PLU lookup upgraded from 491 F&V to full 72,911 products
- **Fiscal Calendar** (`backend/fiscal_calendar.py`, `dashboards/shared/fiscal_selector.py`):
  - 4,018 daily rows, 45 columns, FY2016-FY2026, 5-4-4 retail calendar
  - 3 API endpoints: years, periods, current
  - Reusable Streamlit period selector (FY/Quarter/Month/Week/Custom)
  - Loaded as DuckDB table for JOIN queries
- **9 New Dashboards** (ports 8507-8515):
  - Customers (8507): Customer counts, channel mix, trends
  - Market Share (8508): Postcode share, penetration, spend
  - Hub Assistant (8509): Knowledge base Q&A (536 articles)
  - Learning Centre (8510): 12 modules, 14 lessons with progress tracking
  - Store Ops (8511): Store-level transaction intelligence
  - Product Intel (8512): Item & category performance
  - Revenue Bridge (8513): Revenue decomposition & trends
  - Buying Hub (8514): Category & buyer intelligence
  - Hub Portal (8515): Documentation, data catalog, intelligence, agents, gamification (11 tabs)
  - Landing Page (8500): Hub home with links to all 5 hub categories
- **Data Intelligence Suite** (`backend/data_analysis.py`):
  - 6 analysis types: basket, stockout, intraday_stockout, price_dispersion, demand_pattern, slow_movers
  - All query 383.6M transactions via DuckDB, return standardised result dicts
  - Presentation rubric scoring (8 dimensions, Board-ready/Exec-ready/Draft grades)
  - 41 intelligence reports generated, stored in hub_data.db
- **Agent Control Panel** (Hub Portal tab11):
  - `agent_proposals` table: 75 proposals with PENDING/APPROVED/REJECTED/COMPLETED/FAILED status
  - `agent_scores` table: 55 performance metrics across multiple agents
  - Approve/reject UI with reviewer notes
  - Agent performance cards with score history
  - Task history with execution results
- **Agent Executor** (`backend/agent_executor.py`):
  - Polls agent_proposals for APPROVED tasks
  - Routes to real analysis functions via AGENT_ANALYSIS_MAP (6 agents → 6 analysis types)
  - Scores results with presentation rubric
  - Stores in intelligence_reports, marks proposals COMPLETED
  - 44 proposals executed, all Board-ready grades (9.8-10.0/10)
  - 2 API endpoints: POST /api/admin/executor/run, GET /api/admin/executor/status
- **NL Query Router** (`backend/agent_router.py`):
  - Keyword-based routing: natural language → analysis type
  - 3 API endpoints: POST /api/agent-tasks, GET /api/agent-tasks, GET /api/agent-tasks/{id}
  - Deterministic, no LLM calls, auditable
- **Self-Improvement Engine** (`backend/self_improvement.py`):
  - Parses H/R/S/C/D/U/X scores from audit.log and task_scores table
  - Calculates per-criterion averages, identifies weakest
  - MAX 3 attempts per criterion per cycle
  - Auto-triggers every 5 agent completions
  - Dashboard tab with KPI gauges, trends, cycle history
  - 5 API endpoints: status, history, record-scores, record-cycle, backfill
- **Authentication System** (`backend/auth.py`, `dashboards/shared/auth_gate.py`):
  - Bcrypt password hashing, session tokens, expiry, revocation
  - User registration/login, admin user management
  - Site password option, auth gate for dashboards
  - 15 API endpoints for auth + admin
- **Knowledge Base**: 536 articles with full-text search (2 API endpoints)
- **Learning System**: 12 modules (L1-L4, D1-D4, K1-K4), 14 lessons, progress tracking (5 API endpoints)
- **Employee Roles**: 211 roles imported (3 Functions, 36 Departments, 140 Jobs)
- **WATCHDOG Scanner** (`scripts/watchdog.py`): AST-based Streamlit dashboard scanner — nested expander detection, component inventory, API call tracking (20 tests)
- **Hub Navigation** (`dashboards/nav.py`): Two-row hub nav with 5 hubs, renders automatically on all dashboards
- **Centre of Excellence Documentation**:
  - `docs/BEST_PRACTICES.md`: Architecture patterns, data engineering, agent development, safety workflows, testing strategy
  - `docs/FEATURE_STATUS.md`: Complete status matrix (LIVE/PARTIAL/PLANNED/CONCEPT) for all features
  - `docs/ACTIVATION_ROADMAP.md`: 6-phase roadmap from current state to fully self-improving system
  - `docs/data_catalog.md`: Transaction data profile (383.6M rows, 34 stores, 3 FYs)
  - `docs/fiscal_calendar_profile.md`: 5-4-4 retail calendar documentation (4,018 daily rows)

### Changed
- `backend/app.py`: Expanded from ~776 to ~4260 lines, 71+ endpoints, 35 database tables
- `start.sh`: Launches 16 services (API + 15 dashboards)
- `watchdog/health.sh`: Monitors all 16 services
- `dashboards/shared/`: Expanded to 7 modules (data_access, fiscal_selector, styles, learning_content, training_content, watchdog_safety, auth_gate)
- Hub navigation: 5 hubs (Financial, Market Intel, Operations, Transactions, Learning)

### Scores
- Transaction Layer: H:9 R:9 S:8 C:8 D:9 U:9 X:8 = 8.6
- Product Hierarchy: H:9 R:9 S:9 C:9 D:9 U:9 X:9 = 9.0
- Fiscal Calendar: H:9 R:9 S:9 C:9 D:9 U:9 X:9 = 9.0
- Agent Control Panel: H:9 R:9 S:9 C:8 D:9 U:9 X:8 = 8.7
- Agent Executor: H:9 R:9 S:8 C:8 D:9 U:9 X:8 = 8.6
- Self-Improvement: H:9 R:9 S:9 C:8 D:9 U:9 X:8 = 8.7
- Learning Hub: H:9 R:9 S:9 C:9 D:8 U:9 X:9 = 8.9
- CoE Documentation: H:9 R:9 S:9 C:9 D:9 U:9 X:9 = 9.0

---

## [2.1.0] - 2026-02-15

### Added
- **Learning Hub Rationalisation**: Consolidated learning dashboards, removed duplicates
- **WATCHDOG Scanner Tests**: 20 tests for AST-based dashboard scanner
- **Test Coverage Milestone**: 484 tests across 14 files

### Scores
- Average: 8.9

---

## [1.3.0] - 2026-02-14

### Added
- **Data Access Abstraction Layer** (`backend/data_layer.py`): Pluggable data source pattern with:
  - `DataSource` abstract base class defining standard interface
  - `MockDataSource` with deterministic seeded data (RNG 42)
  - `FabricDataSource` stub for Microsoft Fabric integration
  - `get_data_source()` factory function with `DB_TYPE` env var support
  - Data correctness guarantee: all KPIs traceable to source ±0.01
- **Shared Dashboard Module** (`dashboards/shared/`): Centralized constants and utilities
  - `stores.py`: Canonical 21-store network with regional mappings
  - Single source of truth for store names and regions across all dashboards
  - Eliminates duplication and reduces maintenance burden
- **Multi-Agent Orchestrator System** (`orchestrator/`): Parallel development via git worktrees
  - `coordinator.py`: Manages parallel agent execution in isolated worktrees
  - `task_queue.py`: Phase-based task sequencing with dependency tracking
  - `worker.py`: Executes individual agent tasks on separate branches
  - `models.py`: Task, Phase, WorkerResult, TaskStatus data structures
  - `audit.py`: Full logging and traceability for orchestration actions
  - `safety.py`: Pre-flight validation and safety checks
  - Enables true parallel development without merge conflicts
  - Agent roles: Architect, Data Engineer, Test Engineer, Frontend, Backend
- **Test Coverage for Data Layer**: Comprehensive tests for `DataSource` implementations
  - Mock data source validation (determinism, filtering, correctness)
  - Factory function behavior verification
  - Data schema consistency checks

### Changed
- Updated `docs/ARCHITECTURE.md` to document new components:
  - Data access abstraction layer with DataSource pattern
  - Shared dashboard module for constants
  - Orchestrator system architecture and agent roles
  - Updated file structure diagram
- Architecture now supports pluggable data backends (mock vs production)
- Dashboards can import from `dashboards.shared` for consistency

### Scores
- Phase 3 Task 1 (Data Engineer): H:9 R:9 S:9 C:9 D:9 U:8 X:9 = 8.9
- Phase 3 Task 2 (Test Engineer): H:9 R:9 S:9 C:8 D:8 U:8 X:8 = 8.4

---

## [1.2.0] - 2026-02-13

### Added
- **The Rubric Dashboard** (port 8505): Multi-LLM comparison UI with side-by-side responses, Chairman's Decision workflow, and LLM win rate history
- **Trending & Self-Improvement Dashboard** (port 8506): Weekly KPIs, LLM performance charts, top-rated queries, template usage, system health, and embedded feedback form
- **Prompt Academy**: 15 role-based templates (5 categories x 3 difficulty levels) seeded into template library
- **Test Suite**: 52 automated tests across 4 test files (API, data validation, rubric, templates)
- Prompt Builder now loads/saves templates via API with category and difficulty filters

### Fixed
- **Backend API**: Fixed KeyError in `/api/rubric` when LLM response missing timestamp field — now uses `.get()` with fallbacks
- **Sales Dashboard**: Added deterministic random seed (RNG 42) for consistent mock data across sessions
- **Sales Dashboard**: NL query box now wired to backend API instead of hardcoded response

### Changed
- `start.sh`: Now launches 7 services (API + 6 dashboards)
- `watchdog/health.sh`: Monitors all 7 services including Rubric and Trending
- `watchdog/scan.sh`: Refined false-positive filtering for token display patterns
- Updated all docs (USER_GUIDE, ARCHITECTURE, API_REFERENCE, RUNBOOK)

### Scores
- P1 Stabilise: H:8 R:8 S:9 C:8 D:7 U:8 X:8 = 8.0
- P2 Data: H:8 R:8 S:9 C:8 D:8 U:8 X:7 = 8.0
- P3 Rubric: H:9 R:8 S:9 C:8 D:8 U:8 X:8 = 8.3
- P4 Academy: H:8 R:8 S:9 C:8 D:7 U:8 X:8 = 8.0
- P5 Trending: H:8 R:8 S:9 C:8 D:8 U:8 X:8 = 8.1
- P6 Final: see below

---

## [1.1.0] - 2026-02-13

### Added
- **Watchdog v7**: Full safety, quality, design & documentation agent installed
  - `CLAUDE.md`: 7 immutable laws governing all development
  - `watchdog/health.sh`: Service health checks with retry logic
  - `watchdog/scan.sh`: Credential and security scanning
  - `watchdog/validate_data.py`: Deep data validation (checksums, range checks, null checks)
  - `watchdog/shutdown.sh`: Emergency shutdown with evidence preservation (safe — no machine shutdown)
  - Pre-commit hook: blocks secrets, CLAUDE.md tampering, test deletion
  - Code quality rubric (7 criteria: H/R/S/C/D/U/X)
  - Design & usability rubric (8 criteria, Uber-level benchmark)
  - Procedures: task execution, self-improvement, data correctness, documentation
  - Learnings directory for cross-session improvement
- Git repository initialized with `.gitignore`

---

## [1.0.1] - 2026-02-13

### Fixed
- **Sales Dashboard**: Replaced deprecated `pd.np.random` with `numpy.random` (pandas 2.x compatibility)
- **Dependencies**: Removed `pymssql` from requirements.txt (requires FreeTDS C library; not needed for PostgreSQL)

### Added
- `setup_keys.sh`: Interactive API key setup script with auto-restart and health check
- **Documentation suite**: USER_GUIDE.md, API_REFERENCE.md, ARCHITECTURE.md, DECISIONS.md, CHANGELOG.md, RUNBOOK.md
- **Design & Usability Rubric**: 8-criterion scoring framework with current Hub scores
- **QUICKSTART.md**: One-page onboarding guide for finance team

### Changed
- `.env` file populated with OpenAI API key

---

## [1.0.0] - 2026-02-13

### Added
- **Backend API** (FastAPI on port 8000)
  - Natural language → SQL query endpoint (`/api/query`)
  - The Rubric multi-LLM evaluation (`/api/rubric`)
  - Chairman's Decision recording (`/api/decision`)
  - User feedback collection (`/api/feedback`)
  - Prompt template library CRUD (`/api/templates`)
  - Performance analytics (`/api/analytics/performance`, `/api/analytics/weekly-report`)
  - SQLite metadata database (auto-created)

- **Sales Dashboard** (Streamlit on port 8501)
  - 5 KPI cards (revenue, profit, margin, transactions, avg basket)
  - Revenue trend chart (revenue + profit over time)
  - Store performance bar chart (coloured by margin)
  - Category mix pie chart
  - Product-level analytics (OOS alerts, wastage opportunities)
  - Online order metrics (miss-pick rate, substitution rate, accuracy)
  - Natural language query interface

- **Profitability Dashboard** (Streamlit on port 8502)
  - Network P&L waterfall chart
  - Store net profit comparison (horizontal bar)
  - Margin vs Revenue scatter plot (bubble = store size)
  - Store-by-store P&L table
  - Transport cost impact analysis
  - Key insights and recommendations panel

- **Transport Dashboard** (Streamlit on port 8503)
  - Cost overview KPIs (total cost, deliveries, avg cost, distance, $/km)
  - Cost component breakdown (fuel, driver, vehicle, maintenance)
  - Route efficiency analysis (bar + scatter)
  - Daily cost trend lines
  - Route consolidation opportunity analysis
  - Fleet optimisation comparison
  - Scenario modelling slider (5-30% cost reduction)

- **Prompt Builder** (Streamlit on port 8504)
  - 4-tab interface: Design, Test, Save & Share, Examples
  - Step-by-step query builder (data sources, filters, output format)
  - Auto-generated SQL preview
  - Mock test execution with AI analysis
  - 4 pre-built templates (OOS Alert, Wastage, Miss-Pick, Over-Ordering)
  - 6 example prompts from "super users"
  - Scheduling and team sharing options

- **Infrastructure**
  - `start.sh`: Launch all services with dependency install
  - `stop.sh`: Kill all services cleanly
  - `docker-compose.yml`: Container orchestration (optional)
  - `.env` template for API keys and DB config
  - `requirements.txt`: 15 Python packages
