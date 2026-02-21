# Harris Farm Hub — Self-Improvement Plan
**Date:** 21 February 2026
**Baseline:** v3.1.0 — 18 dashboards, 53 API endpoints, 4 databases

---

## Current Maturity: 73% Functional

| Layer | Status | Score |
|-------|--------|-------|
| **Core Operational Dashboards** (Sales, Profitability, Customers, Store Ops, Buying Hub, Product Intel, Revenue Bridge) | Production-ready with real data | 9/10 |
| **Strategic Intelligence** (Market Share, PLU Intelligence) | Production-ready, rich features | 9/10 |
| **Backend API** (53 endpoints, auth, DuckDB, SQLite) | All implemented, real data | 9/10 |
| **Data Assets** (383M transactions, 27.3M PLU, 77K market share) | Complete, verified | 10/10 |
| **Learning & Training** (Learning Centre, Rubric, Prompt Builder) | Framework exists, persistence gaps | 4/10 |
| **AI Tools** (Chatbot, Analytics, Agents) | Partially wired | 5/10 |
| **Supply Chain** (Transport) | 100% mock data | 1/10 |
| **Brand & Culture** (Greater Goodness) | Static content only | 3/10 |
| **Gamification** (Leaderboard, Achievements, Portal) | Tables exist, logic not persistent | 3/10 |
| **Deployment & DevOps** (Render, GitHub Releases, data_loader) | Working in production | 8/10 |

**Overall: 73/100**

---

## Phase 1: Fix What's Broken (Week 1)
*Impact: Prevent user-facing failures*

### 1.1 Verify Learning Progress Persistence
- **Problem:** `/api/learning/progress/{user_id}` POST exists but no confirmed test that progress saves and reloads across sessions
- **Fix:** Test the round-trip. If broken, ensure `user_progress` table in hub_data.db is written on completion
- **Effort:** 2 hours
- **Impact:** Learning Centre becomes usable for Prompt Academy rollout

### 1.2 Wire Rubric Challenge Execution
- **Problem:** CHALLENGES list exists in rubric_dashboard.py but clicking "Start Challenge" doesn't actually send prompts to AI providers for comparison
- **Fix:** Connect challenge submission → `/api/rubric` endpoint → display scored results
- **Effort:** 4 hours
- **Impact:** Rubric becomes a real training tool, not just UI

### 1.3 Fix test_six_analysis_types — DONE
- **Problem:** Test expects 6 analysis types but 11 now exist. CI/CD may fail.
- **Fix:** Updated assertion to `== 11` in `tests/test_data_analysis.py`
- **Effort:** 15 minutes
- **Impact:** Clean test suite

### 1.4 Verify Chatbot Knowledge Base Depth
- **Problem:** hub_data.db has knowledge_base table with FTS5, but unclear how many real docs are indexed
- **Fix:** Audit content. If <50 articles, seed with Hub documentation, procedures, Harris Farm strategy docs
- **Effort:** 2 hours
- **Impact:** Hub Assistant becomes genuinely useful

---

## Phase 2: Complete the Platform (Weeks 2-3)
*Impact: Move from 73% → 90%*

### 2.1 Wire Analytics Backend (Replace MockDataSource)
- **Problem:** `/api/analytics/performance` and `/api/analytics/weekly-report` use MockDataSource (seeded random data). Trending dashboard shows fake metrics.
- **Fix:** Aggregate real data from hub_data.db tables (queries, llm_responses, evaluations, feedback) into analytics views. Replace MockDataSource with SQLiteAnalyticsSource.
- **Effort:** 1 day
- **Impact:** Trending dashboard shows real system usage. Self-improvement loop feeds on real data.

### 2.2 Wire Leaderboard & Achievement Persistence
- **Problem:** Hub Portal shows gamification UI but POINT_ACTIONS, EVALUATION_TIERS are hardcoded dicts. No backend updates scores when users complete challenges or submit prompts.
- **Fix:**
  - Trigger `game_points` insert on rubric submission, learning completion, feedback
  - Implement `game_achievements` unlock logic (e.g., "First Query", "10 Prompts", "All Modules")
  - Connect leaderboard API to real game_points table
- **Effort:** 1 day
- **Impact:** Gamification becomes motivating, not decorative

### 2.3 Populate Greater Goodness with Real Data
- **Problem:** 100% hardcoded HTML. Achievement cards show static numbers.
- **Fix:**
  - Pull sustainability KPIs from data source (or define as admin-editable in hub_data.db)
  - Add "Latest Community Impact" section from real store data
  - Timeline of milestones pulled from a simple table
- **Effort:** 4 hours
- **Impact:** Pillar 1 page reflects real progress, not static content

### 2.4 Strengthen Prompt Builder Persistence
- **Problem:** Templates may not save across sessions. Only default "Out of Stock Alert" template hardcoded.
- **Fix:**
  - Verify `/api/templates` POST actually writes to hub_data.db (prompt_templates table)
  - Seed 10-15 templates for common Harris Farm use cases (buyer order planning, store manager weekly review, dept head margin check, marketing campaign)
  - Add "My Templates" section that loads user-saved prompts
- **Effort:** 4 hours
- **Impact:** Prompt Builder becomes the entry point for Prompt Academy

---

## Phase 3: Real Data Integration (Weeks 3-5)
*Impact: Eliminate all mock data*

### 3.1 Transport Dashboard — Real Data
- **Problem:** Only dashboard with 100% mock data. Uses `np.random.RandomState(42)`.
- **Options:**
  - **Option A:** Source delivery/route data from WMS/ERP export (CSV/Excel)
  - **Option B:** Build from POS data — derive delivery cost proxies from store-level volume patterns
  - **Option C:** If no transport data exists, redesign as "Supply Chain Intelligence" using existing store replenishment patterns from PLU data
- **Effort:** 1-3 days depending on data availability
- **Impact:** Eliminates last mock dashboard. Pillar 4 fully data-driven.

### 3.2 Integrate PLU Intelligence into Main Workflow
- **Problem:** PLU dashboard uses isolated 3.1GB database. Not connected to other dashboards.
- **Fix:**
  - Add PLU wastage insights to Profitability dashboard (top wastage items by store)
  - Add PLU stocktake alerts to Store Ops dashboard
  - Link Product Intel top items to PLU weekly trends
  - Consider "View PLU Detail" links from other dashboards
- **Effort:** 1 day
- **Impact:** PLU data enriches existing dashboards, not siloed

### 3.3 Cross-Dashboard Linking
- **Problem:** Dashboards are independent views. A store manager seeing poor margin in Profitability can't click through to see which PLUs are causing it.
- **Fix:** Add contextual `st.page_link()` buttons:
  - Profitability → PLU Intelligence (wastage drill-down)
  - Store Ops → PLU Intelligence (item detail)
  - Market Share → Customer dashboard (same postcode analysis)
  - Sales → Profitability (margin deep-dive)
- **Effort:** 4 hours
- **Impact:** Hub feels like an integrated platform, not separate tools

---

## Phase 4: Intelligence Layer (Weeks 5-8)
*Impact: Move from reporting to recommendations*

### 4.1 Automated Alerts System
- **Problem:** Issues exist (market share declines, PLU wastage spikes) but users must manually check dashboards
- **Fix:**
  - Build `backend/alert_engine.py` — scheduled scan of key metrics
  - Alerts: Share decline >2pp in Core trade area, wastage spike >20% MoM, stocktake variance anomaly
  - Display on Landing Page as notification cards
  - Optional email digest (weekly)
- **Effort:** 2 days
- **Impact:** Proactive intelligence — the Hub tells you what needs attention

### 4.2 Natural Language Query for All Data
- **Problem:** `/api/query` NL→SQL engine exists but only routes to DuckDB transactions and harris_farm.db. PLU database and market share spatial queries not accessible.
- **Fix:** Extend QueryGenerator to route PLU and market share questions
- **Effort:** 1 day
- **Impact:** Hub Assistant can answer "What's the worst wastage PLU in Bondi?" or "Which postcodes are we losing share in?"

### 4.3 Executive Weekly Brief
- **Problem:** No automated executive summary
- **Fix:**
  - Generate weekly brief from: sales vs budget, share movements, PLU wastage alerts, customer retention shifts
  - Render as a single-page view on Landing Page or dedicated tab
  - Option to email to leadership team
- **Effort:** 1 day
- **Impact:** Angus & Luke get a one-page weekly pulse without opening multiple dashboards

---

## Phase 5: Polish & Scale (Ongoing)
*Impact: Production hardening*

### 5.1 Per-Dashboard Tests
- **Problem:** No dedicated tests for sales_dashboard, profitability, market_share rendering
- **Fix:** Integration tests that verify SQL queries execute without error and return expected column shapes
- **Effort:** 2 days
- **Impact:** Confidence in deployments

### 5.2 Standardise Store/Department Names
- **Problem:** Multiple dashboards parse "10 - HFM Pennant Hills" manually. Brittle.
- **Fix:** Create `shared/constants.py` with STORES dict and DEPARTMENTS dict. Refactor all dashboards.
- **Effort:** 4 hours
- **Impact:** Reduces future bugs when store names change

### 5.3 Rate Limiting & Error Handling
- **Problem:** 53 API endpoints with no rate limiting. Some dashboard errors silently swallowed.
- **Fix:** Add FastAPI rate limiting middleware. Standardise error display in dashboards.
- **Effort:** 4 hours
- **Impact:** Production resilience

### 5.4 Mobile Responsiveness
- **Problem:** Streamlit wide layout doesn't render well on mobile
- **Fix:** Add responsive CSS overrides in shared/styles.py for key dashboards (Landing, Sales, Market Share)
- **Effort:** 4 hours
- **Impact:** Store managers can check KPIs on phone

---

## Scoring Target

| Phase | Current | Target | Timeline |
|-------|---------|--------|----------|
| Phase 1 (Fix broken) | 73% | 80% | Week 1 |
| Phase 2 (Complete platform) | 80% | 90% | Weeks 2-3 |
| Phase 3 (Real data) | 90% | 95% | Weeks 3-5 |
| Phase 4 (Intelligence) | 95% | 98% | Weeks 5-8 |
| Phase 5 (Polish) | 98% | 100% | Ongoing |

---

## Success Metrics

1. **Zero mock data dashboards** — all 18 use real or admin-editable data
2. **Gamification engagement** — >50% of users earn first achievement within 2 weeks
3. **Alert coverage** — automated detection for share decline, wastage spike, stocktake anomaly
4. **Cross-dashboard navigation** — any insight is 1 click from related detail
5. **Executive brief** — weekly auto-generated summary delivered without manual effort
6. **Test coverage** — every dashboard has at least 3 integration tests
7. **Knowledge base** — >100 indexed articles, chatbot answers 80%+ of common questions

---

*"Fewer, Bigger, Better" — this plan focuses on completing what exists rather than adding new features.*
*Every phase makes existing dashboards more useful, not more numerous.*
