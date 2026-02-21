# Hub Portal Architecture Audit

**Date:** 2026-02-22 | **Scope:** Full platform inventory, redundancy analysis, dead code, restructure recommendations

---

## Section 1: Complete Inventory

### 1.1 Main Navigation (20 pages)

| Slug | Title | Icon | Pillar | URL |
|------|-------|------|--------|-----|
| (home) | Home | Apple | -- | / |
| greater-goodness | Greater Goodness | Seedling | P1: Greater Goodness | /greater-goodness |
| customers | Customers | People | P2: Customer | /customers |
| market-share | Market Share | Map | P2: Customer | /market-share |
| learning-centre | Learning Centre | Grad Cap | P3: People | /learning-centre |
| the-paddock | The Paddock | Seedling | P3: People | /the-paddock |
| hub-assistant | Hub Assistant | Speech | P3: People | /hub-assistant |
| ai-adoption | AI Adoption | Chart | P3: People | /ai-adoption |
| academy | Academy | Star | P3: People | /academy |
| sales | Sales | Chart | P4: Operations | /sales |
| profitability | Profitability | Money | P4: Operations | /profitability |
| transport | Transport | Truck | P4: Operations | /transport |
| store-ops | Store Ops | Store | P4: Operations | /store-ops |
| buying-hub | Buying Hub | Cart | P4: Operations | /buying-hub |
| product-intel | Product Intel | Search | P4: Operations | /product-intel |
| plu-intel | PLU Intelligence | Chart | P4: Operations | /plu-intel |
| prompt-builder | Prompt Builder | Wrench | P5: Digital & AI | /prompt-builder |
| the-rubric | The Rubric | Scales | P5: Digital & AI | /the-rubric |
| trending | Trending | Chart Up | P5: Digital & AI | /trending |
| revenue-bridge | Revenue Bridge | Chart Down | P5: Digital & AI | /revenue-bridge |
| hub-portal | Hub Portal | Globe | P5: Digital & AI | /hub-portal |

### 1.2 Hub Portal Internal Tabs (11)

| # | Tab | Purpose | Data | Audience | Frequency |
|---|-----|---------|------|----------|-----------|
| 1 | Documentation | Browse system docs, procedures, learnings | /docs/, /watchdog/ files | Developers | Weekly |
| 2 | Data Catalog | Schema inventory, joins, data relationships | All 4 DBs metadata | Analysts | Monthly |
| 3 | Showcase | AI Centre of Excellence metrics, demo stats | task_scores, tests | Leadership | Monthly/demos |
| 4 | Prompt Library | Browse/submit/history of prompt templates | prompt_templates, prompt_history | All users | Weekly |
| 5 | Scoreboard | Gamified points, leaderboard, AI agent competition | portal_scores, game_agents | All users | Daily |
| 6 | The Arena | 5 agent teams competing with proposals | arena_proposals, arena_evaluations | Admin/analysts | Weekly |
| 7 | Agent Network | Registry of 41 department analyst agents | arena agents, insights | Admin | Monthly |
| 8 | Data Intelligence | Run analysis (basket, stockout, price, demand, slow movers) | 383M transaction rows | Analysts | Weekly |
| 9 | WATCHDOG Safety | Safety review queue, risk assessment, audit trail | watchdog_proposals, watchdog_audit | Admin | As needed |
| 10 | Self-Improvement | Score tracking (HRSCDU), codebase audit, findings | task_scores, improvement_cycles | Developers | Weekly |
| 11 | Agent Control | Approve/reject agent proposals, performance, executor | agent_proposals, agent_scores | Admin | As needed |

### 1.3 Dashboard Tab Structures

| Dashboard | Tabs | Tab Names |
|-----------|------|-----------|
| Market Share | 8 | Overview, Spatial Map, Store Trade Areas, Store Health, Trends & Shifts, Opportunities, Issues, Data Explorer |
| Customer | 4 | Overview, Known Customers, Channel Analysis, Lifetime Value |
| Buying Hub | 5 | Department Overview, Category Drill-Down, Buyer Dashboard, Range Review, Trading Patterns |
| Product Intel | 5 | Top Items, PLU Deep Dive, Basket Analysis, Slow Movers, Trading Patterns |
| Store Ops | 5 | Daily Trend, Trading Patterns, Category Mix, Anomaly Detection, Out of Stock |
| Revenue Bridge | 6 | Monthly Revenue, Revenue Decomposition, Department Breakdown, Store Rankings, Year-over-Year, Trading Patterns |
| Learning Centre | 5 | My Dashboard, AI Prompting Skills, Data Prompting, Knowledge Base, Lab |
| Academy | 7 | Journey, Patterns, Rubric, Resources, Leaderboard, Challenges, Progress |
| The Paddock | 5 screens | Welcome, Register, Assessment (5 modules), Results, Admin/Greenhouse |
| The Rubric | 5 | Learn, Practice, Compare, Scorecard, My Progress |
| Prompt Builder | 4 | Design, Test, Save & Share, Examples |

### 1.4 API Endpoints (112 total)

| Category | Count | Prefix |
|----------|-------|--------|
| Authentication | 16 | /api/auth/* |
| Transactions | 9 | /api/transactions/* |
| Arena | 12 | /api/arena/* |
| WATCHDOG | 10 | /api/watchdog/* |
| Portal | 6 | /api/portal/* |
| Intelligence | 5 | /api/intelligence/* |
| Learning | 8 | /api/learning/* |
| Product Hierarchy | 5 | /api/hierarchy/* |
| Core Query/Rubric | 5 | /api/query, /api/rubric, etc. |
| Game | 5 | /api/game/* |
| Admin/Agent Control | 8 | /api/admin/* |
| Self-Improvement | 5 | /api/self-improvement/* |
| Continuous Improvement | 4 | /api/continuous-improvement/* |
| Agent Tasks | 3 | /api/agent-tasks/* |
| Other (sustainability, fiscal, chat, etc.) | 11 | various |

---

## Section 2: Redundancy Analysis

### CRITICAL: Agent Proposal Systems (3 overlapping systems)

| System | Location | Purpose | API |
|--------|----------|---------|-----|
| The Arena (Tab 6) | Hub Portal | Competitive evaluation for business value | /api/arena/* |
| WATCHDOG Safety (Tab 9) | Hub Portal | Safety review and risk assessment | /api/watchdog/* |
| Agent Control Panel (Tab 11) | Hub Portal | Operational approval and execution | /api/admin/agent-proposals/* |

**Verdict:** Different stages of ONE pipeline, but fragmented across 3 separate tabs. Approvers have to navigate 3 tabs to complete one approval process.

### Prompt Systems (2 overlapping)

| System | Location | Overlap |
|--------|----------|---------|
| Prompt Builder | Standalone page | Design, test, save prompts |
| Prompt Library (Tab 4) | Hub Portal | Browse, submit, history |

**Verdict:** "Submit Prompt" in Hub Portal duplicates Prompt Builder's save functionality.

### Learning Platforms (3 overlapping)

| System | Location | Focus |
|--------|----------|-------|
| Learning Centre | Standalone page | Structured modules (L1-L4, D1-D4, K1-K4) |
| Growing Legends Academy | Standalone page | Gamified 6-level journey |
| The Paddock | Standalone page | AI skills assessment + learning paths |

**Verdict:** Different purposes but progress tracking could be unified.

### Product Analytics (2 overlapping)

| System | Data Source | Overlap |
|--------|-----------|---------|
| Product Intel | 383M transaction rows (DuckDB) | Top items, basket analysis, slow movers |
| PLU Intelligence | 27.3M weekly PLU rows (SQLite) | Weekly aggregates, store comparisons |

**Verdict:** Different data sources, but names are confusing and some analyses overlap.

---

## Section 3: Dead Code & Cleanup

### Potentially Unused Files

| File | Status | Action |
|------|--------|--------|
| `streamlit_app.py` (root) | Legacy entry point, replaced by `dashboards/app.py` | Verify and delete |
| `configure_urls.py` (root) | Google Drive URL config | Likely legacy (GitHub Releases replaced GDrive) |
| `setup_gdrive_urls.py` (root) | Google Drive setup | Same as above |
| `rubric_evaluator.py` (root) | Standalone rubric evaluator | Check if replaced by /api/rubric |
| `dashboards/nav.py` | Legacy nav system | Only used in landing.py, could inline |

### Potentially Orphaned API Endpoints

| Endpoint | Issue |
|----------|-------|
| POST `/api/sustainability/kpis/{kpi_id}` | No edit UI visible in Greater Goodness dashboard |
| POST `/api/roles/import` | No UI — dev/admin tool only |
| POST `/api/page-quality/score` | No UI — background/automated only |
| 6x `/api/auth/admin/*` endpoints | No unified admin panel UI |

### Incomplete Features

| Feature | Issue |
|---------|-------|
| Continuous Improvement findings | Has API to update status but no UI buttons |
| WATCHDOG Scheduler | API exists but no scheduler UI in WATCHDOG tab |
| Admin user management | API endpoints exist but no admin panel page |

---

## Section 4: Proposed Restructure

### 4.1 Hub Portal is Overloaded

The Hub Portal (2,876 lines) has 11 tabs that are each sub-applications. This is the #1 usability issue.

**Proposed split:**

**KEEP in Hub Portal (rename to "Mission Control"):**
- Documentation
- Data Catalog
- Showcase
- Self-Improvement

**PROMOTE to standalone pages:**
- Scoreboard + The Arena + Agent Network → **"Agent Hub"** (new page)
- Data Intelligence → **"Analytics Engine"** (new page)
- WATCHDOG Safety + Agent Control Panel → **"Agent Operations"** (merge into single page with 3-stage pipeline)
- Prompt Library → merge into Prompt Builder

### 4.2 Migration Plan

| Current Item | Current Location | Proposed Location | Action |
|-------------|-----------------|-------------------|--------|
| Documentation | Hub Portal Tab 1 | Mission Control Tab 1 | Keep (rename parent) |
| Data Catalog | Hub Portal Tab 2 | Mission Control Tab 2 | Keep |
| Showcase | Hub Portal Tab 3 | Mission Control Tab 3 | Keep |
| Prompt Library | Hub Portal Tab 4 | Merge into Prompt Builder | Remove tab, add browse to Prompt Builder |
| Scoreboard | Hub Portal Tab 5 | New "Agent Hub" page | Promote |
| The Arena | Hub Portal Tab 6 | New "Agent Hub" page | Promote |
| Agent Network | Hub Portal Tab 7 | New "Agent Hub" page | Promote |
| Data Intelligence | Hub Portal Tab 8 | New "Analytics Engine" page | Promote |
| WATCHDOG Safety | Hub Portal Tab 9 | New "Agent Operations" page | Promote + merge |
| Self-Improvement | Hub Portal Tab 10 | Mission Control Tab 4 | Keep |
| Agent Control Panel | Hub Portal Tab 11 | New "Agent Operations" page | Promote + merge |
| Product Intel | Operations pillar | Merge with PLU Intel | Merge → "Product Analytics" |
| PLU Intelligence | Operations pillar | Merge with Product Intel | Merge → "Product Analytics" |
| Hub Portal | Digital & AI pillar | Rename | Rename → "Mission Control" |

### 4.3 Naming Clarity

| Current | Proposed |
|---------|----------|
| Hub Portal | Mission Control |
| Product Intel | Product Analytics (Transactions) |
| PLU Intelligence | Product Analytics (Weekly) — or merge |
| Hub Assistant | Ask Harris Farm |
| The Paddock | The Paddock: AI Skills Assessment |

### 4.4 Priority Actions

| Priority | Action | Effort |
|----------|--------|--------|
| HIGH | Restructure Hub Portal — promote 4-5 tabs to standalone pages | 1 week |
| HIGH | Create unified Agent Operations page (Arena eval → WATCHDOG review → Approval) | 3-4 days |
| MEDIUM | Build admin panel UI for user management | 2-3 days |
| MEDIUM | Add role-based "Recommended for You" on landing page | 1-2 days |
| LOW | Rename pages for clarity | 1 day |
| LOW | Merge Product Intel + PLU Intel | 2-3 days |
| LOW | Clean up dead code files | 1 day |

---

## Summary Stats

| Metric | Count |
|--------|-------|
| Main navigation pages | 20 |
| Hub Portal tabs | 11 |
| Hub Portal sub-tabs | 14 |
| Other dashboard tab structures | 11 |
| Total unique views | 60+ |
| API endpoints | 112 |
| Database tables | 35+ |
| Data rows | 383M+ |
| Backend Python files | 21 |
| Dashboard Python files | 22 |
| hub_portal.py | 2,876 lines |
| backend/app.py | 5,198 lines |

**Overall Platform Health: 4/5** — comprehensive and production-ready, but Hub Portal overload and agent workflow fragmentation are the main usability issues.
