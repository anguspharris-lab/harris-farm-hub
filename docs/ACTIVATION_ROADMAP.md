# Activation Roadmap
**From Current State to Fully Self-Improving AI Centre of Excellence**

*Last Updated: 2026-02-18*

---

## Current State Assessment

### What's Working

| System | Status | Evidence |
|--------|--------|----------|
| 16 Streamlit dashboards | Running | 16/16 healthy (Phase 1 fixed) |
| FastAPI backend | Running | 71+ endpoints on port 8000 |
| 383.6M transaction queries | Running | 6 analysis types, Board-ready grades |
| Agent approval workflow | Running | 75 proposals tracked, approve/reject UI |
| Agent executor | Running | 44 proposals completed, all Board-ready |
| Self-improvement engine | Running | 24 task scores, 1 improvement cycle |
| WATCHDOG governance | Running | Audit trail, 4 procedures, AST scanner |
| Test suite | Passing | 1,003 tests, zero failures |
| Product hierarchy | Running | 72,911 products, 98.3% PLU match |
| Fiscal calendar | Running | 4,018 daily rows, 100% transaction coverage |

### What Needs Activation

| System | Issue | Impact |
|--------|-------|--------|
| ~~3 dashboards down~~ | ~~Rubric (8505), Assistant (8509), Prompts (8504)~~ | **FIXED in Phase 1** |
| Portal gamification | Tables exist but empty (portal_scores, achievements) | No user engagement tracking |
| WATCHDOG auto-analysis | WatchdogService built, not in approval flow | Safety relies on human judgment only |
| Arena competition | Tables + API exist, UI minimal | Agent competition not visible |
| A/B testing | Designed but not implemented | Improvements deployed blind |

### What's Blocked on Nothing (Ready to Activate)

These features are fully built and just need a switch flip or first use:

1. **Portal gamification** — POST /api/portal/score and /achievements endpoints work, just need dashboard integration
2. **Arena leaderboard** — GET /api/arena/leaderboard returns data, needs prominent UI placement
3. **WATCHDOG auto-analysis** — WatchdogService.analyze_proposal() works, needs to be called during task creation

---

## Phase 1: Stabilise & Harden — COMPLETED 2026-02-18

**Goal:** Ensure all 16 dashboards are reliably running, fix the 3 intermittent services, and establish baseline metrics.

### 1.1 Fix Intermittent Dashboards — DONE

| Dashboard | Port | Root Cause | Fix Applied |
|-----------|------|------------|-------------|
| Rubric | 8505 | Deprecated `st.experimental_get_query_params` in auth_gate.py | Migrated to `st.query_params` API |
| Hub Assistant | 8509 | Empty knowledge_base table on fresh DB | Added `seed_knowledge_base()` (20 articles, idempotent) |
| Prompt Builder | 8504 | Empty prompt_templates table on fresh DB | Added `seed_prompt_templates()` (6 templates, idempotent) |

**Verification:** `watchdog/health.sh` shows 16/16 up.

### 1.2 Backfill Missing Data — DONE

- Ran `/api/self-improvement/backfill` — 20 task scores in DB
- All 7 criteria above threshold: H=9.0, R=9.0, S=8.6, C=8.65, D=9.0, U=9.0, X=8.75 (avg 8.86)
- Weakest criterion: Safe (S) at 8.6 — still well above 7.0 threshold

### 1.3 Monitoring Baseline — ESTABLISHED

| Metric | Baseline (2026-02-18) | Target |
|--------|----------------------|--------|
| Dashboards healthy | 16/16 | 16/16 |
| Tests | 1,117 across 29 files | No regressions |
| API endpoints | 106 | Maintain |
| Executor completed | 214 | Continuous |
| Self-improvement avg | 8.86/10 | Maintain >=7.0 |
| Backend modules | 18 | Maintain |
| Total lines of code | 24,982 | N/A |

### 1.4 Documentation Verification — DONE

- FEATURE_STATUS.md updated: Rubric and Hub Assistant marked LIVE
- CHANGELOG.md updated: v2.2.1 entry added
- ACTIVATION_ROADMAP.md updated: Phase 1 marked complete

---

## Phase 2: Activate Self-Improvement Loop — COMPLETED 2026-02-18

**Goal:** Get the self-improvement loop producing measurable agent improvements.

### 2.1 Generate Improvement Data — DONE

- Expanded `POST /api/admin/trigger-analysis` to create proposals for all 6 agent types (was only StockoutAnalyzer + BasketAnalyzer)
- Created 30 proposals, approved all, executor processed them against 383M transactions
- 3 new agent types activated: DemandAnalyzer, PriceAnalyzer, SlowMoverAnalyzer

### 2.2 Trigger First Full Improvement Cycle — DONE

Auto-triggered improvement proposals fired as designed:
- SelfImprovementEngine after 20 completions
- ContinuousImprovement after 5 completions
- BasketAnalyzer after 15 completions
- SelfImprovementEngine after 25 completions
- All approved and executed successfully

### 2.3 Apply Improvements — DONE

- Trigger-analysis endpoint expanded to cover all 6 agent types (code change in app.py)
- All agents now producing scored intelligence reports

### 2.4 Measure Impact — DONE

| Agent | Before | After | Change |
|-------|--------|-------|--------|
| ReportGenerator | 9.00 | 9.40 | **+0.40** |
| BasketAnalyzer | 9.63 | 9.71 | +0.08 |
| StockoutAnalyzer | 9.75 | 9.79 | +0.04 |
| DemandAnalyzer | NEW | 10.00 | NEW |
| PriceAnalyzer | NEW | 9.90 | NEW |
| SlowMoverAnalyzer | NEW | 9.80 | NEW |

**Success criteria MET:** ReportGenerator improved +0.40 points (threshold was +0.3).

### Phase 2 Final State

| Metric | Before | After |
|--------|--------|-------|
| Completed proposals | 214 | 248 |
| Agents with scores | 5 real | 8 real |
| Auto-triggered improvements | 1 | 5 |
| Overall avg score | 8.86/10 | 8.86/10 |
| All criteria above threshold | Yes | Yes |

---

## Phase 3: Integrate WATCHDOG into Approval Flow (Week 3)

**Goal:** Automated safety analysis before human review.

### 3.1 Wire WATCHDOG into Task Creation

`dashboards/shared/watchdog_safety.py` already contains `WatchdogService` with an `analyze_proposal()` method. Integration points:

1. When POST /api/agent-tasks creates a task, call `WatchdogService.analyze_proposal()`
2. Store WATCHDOG report in `watchdog_report_json` field (already exists on agent_tasks table)
3. Set `watchdog_status` field (already exists) to SAFE/LOW/MEDIUM/HIGH/BLOCKED
4. Display WATCHDOG badge in approval UI (Agent Control tab)

### 3.2 Add WATCHDOG to Agent Proposals

1. When new agent_proposal is created (any source), run WATCHDOG analysis
2. Store risk assessment alongside the proposal
3. Show risk badge in Pending Approval sub-tab
4. Block HIGH/BLOCKED proposals from approval (require operator override)

### 3.3 Test Safety Boundaries

Create test proposals that should trigger different risk levels:
- Low risk: "Analyse demand patterns at Mosman for last 14 days"
- Medium risk: "Run stockout analysis across ALL stores for 90 days"
- High risk: "Delete all historical data and rebuild from scratch"

**Success criteria:** WATCHDOG correctly assigns risk levels to 90%+ of test cases.

**Estimated effort:** 4-6 hours

---

## Phase 4: Activate Gamification & Competition (Week 4)

**Goal:** Make agent performance visible and competitive.

### 4.1 Populate Gamification Tables

Wire existing endpoints into the dashboard flow:

1. After each task completion, POST to /api/portal/score
2. Define achievement criteria and award via POST /api/portal/achievements
3. Display leaderboard prominently in Hub Portal

### 4.2 Build Agent Leaderboard

Add a dedicated leaderboard view to the Hub Portal:

```
Rank | Agent | Avg Score | Tasks | Best Grade | Trend
#1   | StockoutAnalyzer | 9.9 | 12 | Board-ready | ↑
#2   | BasketAnalyzer   | 9.8 | 8  | Board-ready | →
#3   | DemandAnalyzer   | 9.7 | 6  | Board-ready | ↑
```

### 4.3 Define Achievement Badges

| Achievement | Criteria | Points |
|-------------|----------|--------|
| First Analysis | Complete 1 task | 10 |
| Consistent Performer | 5 consecutive scores > 9.0 | 50 |
| Board-Ready Streak | 10 Board-ready grades | 100 |
| Speed Runner | Complete analysis in < 30 seconds | 75 |
| Self-Improver | Score increase of 1.0+ points | 150 |

### 4.4 Launch Competition Mode

- Set 30-day window for improvement competition
- Track baseline scores at start
- Award winner based on largest improvement (not highest absolute score)
- Display competition standings in Hub Portal

**Estimated effort:** 6-8 hours

---

## Phase 5: A/B Testing Framework (Month 2)

**Goal:** Deploy improvements scientifically.

### 5.1 Build Version Manager

```python
class AgentVersionManager:
    def deploy_test(self, agent_name, new_config, test_ratio=0.2):
        """Route 20% of tasks to new config, 80% to production."""
        ...

    def evaluate(self, agent_name):
        """Compare test vs production scores after 20+ samples."""
        ...

    def promote(self, agent_name):
        """Deploy test version to production."""
        ...
```

### 5.2 Store Version History

```sql
CREATE TABLE agent_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    version TEXT NOT NULL,
    config_json TEXT NOT NULL,
    deployed_at TEXT DEFAULT (datetime('now')),
    retired_at TEXT,
    avg_score REAL,
    task_count INTEGER DEFAULT 0
);
```

### 5.3 First A/B Test

1. Take an improvement recommendation from Phase 2
2. Deploy as test version (20% of tasks)
3. Run 20+ tasks through both versions
4. Compare scores with statistical significance
5. Promote if improvement confirmed

**Success criteria:** First A/B test completed with clear winner deployed.

**Estimated effort:** 8-12 hours

---

## Phase 6: Scale & Optimise (Month 2-3)

**Goal:** Handle growth and optimise for speed.

### 6.1 Performance Targets

| Metric | Current | Target |
|--------|---------|--------|
| Analysis query time | 2-15 sec | < 5 sec (P95) |
| Executor throughput | ~50 tasks/day | 200 tasks/day |
| Dashboard load time | 2-4 sec | < 2 sec |
| Test suite runtime | ~5 min | < 3 min |

### 6.2 Optimisation Priorities

1. **Cache hot queries** — DuckDB materialized views for common store/period combos
2. **Parallel execution** — Run independent analyses concurrently in executor
3. **Query optimisation** — Profile slow queries, add DuckDB indexes
4. **Dashboard caching** — Increase TTL for stable data, decrease for real-time

### 6.3 Infrastructure Evolution

When to make each change:

| Trigger | Action |
|---------|--------|
| > 200 tasks/day | Add parallel executor (ThreadPoolExecutor) |
| > 500 tasks/day | Migrate hub_data.db to PostgreSQL |
| > 1000 tasks/day | Add Redis queue, multiple executor instances |
| Multiple users | Implement RBAC on endpoints |
| External access | Add HTTPS, authentication enforcement |

---

## Success Metrics by Phase

| Phase | Key Metric | Target |
|-------|-----------|--------|
| 1: Stabilise | Dashboard uptime | 16/16 healthy | **DONE** |
| 2: Self-Improve | Measurable improvement | +0.3 points on 1+ agent | **DONE** (+0.40 ReportGenerator) |
| 3: WATCHDOG | Risk assessment accuracy | 90%+ correct |
| 4: Gamification | Agent engagement | All 6 agents scored + ranked |
| 5: A/B Testing | Scientific deployment | 1+ improvement promoted |
| 6: Scale | Throughput | 200+ tasks/day |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Executor crashes | Supervisor process or systemd service; `--once` mode for testing |
| Poor analysis quality | Rubric scoring catches issues; min 7/10 threshold |
| Self-improvement loops | MAX 3 attempts per criterion per cycle; human approval gate |
| Data corruption | WATCHDOG data correctness procedure; validate_data.sh |
| Runaway agent task creation | Per-agent daily limit (50 proposals); human approval required |
| Dashboard regressions | 1,003 tests; WATCHDOG AST scanner; health.sh monitoring |

---

## Quick Reference: How to Run Things

```bash
# Start everything
bash start.sh

# Run executor once (process approved proposals)
curl -X POST http://localhost:8000/api/admin/executor/run

# Check executor status
curl http://localhost:8000/api/agent-tasks

# Submit NL query
curl -X POST http://localhost:8000/api/agent-tasks \
  -H "Content-Type: application/json" \
  -d '{"query":"find products that run out during the day","store_id":"28","days":14}'

# Run tests
python3 -m pytest tests/ -v

# Health check
bash watchdog/health.sh

# Security scan
bash watchdog/scan.sh
```
