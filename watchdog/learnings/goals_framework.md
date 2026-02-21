# Goals Framework Learnings — 2026-02-21

## Architecture Decision: Single File for Goals
All goal data lives in `dashboards/shared/goals_config.py`:
- HUB_GOALS dict (G1-G5 with metadata)
- GOAL_PAGE_MAPPING (dashboard slug → goal IDs)
- _ANALYSIS_GOAL_MAP (analysis type → goal IDs for activity feed)
- _SUPPLY_CHAIN_TYPES (tuple of G4-relevant analysis types)
- Utility functions + DB query functions

Rationale: `dashboards/shared/` is the established pattern for content constants.
A separate `goals/` directory would break conventions and need sys.path changes.

## Bug: None Timestamps from SQLite
SQLite `created_at` columns can be NULL. If `row[3]` returns None, then
`item["timestamp"][:16]` crashes with `TypeError: 'NoneType' is not subscriptable`.
**Fix:** Always `or ""` on timestamp assignment:
```python
"timestamp": row[3] or "",
```

## Bug: SQL String Interpolation
Never f-string inject values into SQL — even from internal tuples.
**Fix:** Use parameterized queries with `?` placeholders:
```python
placeholders = ", ".join("?" for _ in _SUPPLY_CHAIN_TYPES)
conn.execute(f"SELECT COUNT(*) FROM table WHERE col IN ({placeholders})", _SUPPLY_CHAIN_TYPES)
```

## Performance: Single DB Connection for Goals
The front page loads all 5 goals. Opening 5 separate SQLite connections is wasteful.
**Fix:** `fetch_all_goal_metrics()` does all G1-G5 queries in one connection.
Similarly, `fetch_watchdog_scores()` pulls all 7 H/R/S/C/D/U/X averages in one connection.

## Pattern: Activity Feed Color-Coding
Status strings from different tables have different formats:
- Proposals: "COMPLETED", "PENDING", "FAILED"
- Reports: "Grade: Draft", "Grade: Board-ready"
- Improvements: "warning — data_quality"
- WATCHDOG: "Risk: HIGH, Findings: 3"

**Fix:** Use keyword-based matching (`.upper()` + `in` checks) instead of exact dict lookup.

## Pattern: Word-Boundary Description Truncation
`desc[:90]` can cut "sales" to "sal".
**Fix:** `desc[:90].rsplit(" ", 1)[0] + "..."` — splits on last space before limit.

## Nav Registry Must Match app.py
`nav.py` HUBS list and `_PORT_TO_SLUG` must include ALL pages registered in `app.py`.
AI Adoption was missing — added port 8519 and slug `ai-adoption` to both.
**Rule:** When adding a new page to app.py, also add to:
1. `nav.py` HUBS (under correct pillar)
2. `nav.py` _PORT_TO_SLUG
3. `shared/goals_config.py` GOAL_PAGE_MAPPING

## Pattern: Session-Safe _pages Lookup
Fetch `st.session_state.get("_pages", {})` ONCE at module scope, not per-tab.
Streamlit reruns the entire file on each interaction — redundant fetches are wasteful
and error-prone if the dict changes mid-run.

## Goal Badge HTML
Use 8-digit hex for opacity: `{color}20` for background, `{color}50` for border.
Inline `<span>` with `display:inline-block`, `border-radius:12px`, `font-size:0.75em`.
Function: `goal_badge_html(goal_id)` in goals_config.py.

## Rubric Iteration Loop (2026-02-21)

### Score Regex Must Be Universal
Audit log scores appear in 6+ formats — no prefix, `SCORE:`, `SCORES:`, `Score:`,
with `=` or `:` or no delimiter, and D may be `N/A`. Use:
```python
r"(?:SCORES?:\s*)?"       # prefix optional
r"H[=:]?(\d+)\s+"        # delimiter optional
r"D[=:]?(\d+|N/?A)\s+"   # D handles N/A
```
With `re.IGNORECASE`. Store D=N/A as 0, exclude from averages.

### Presentation Rubric: Build Up, Not Down
`_score_brief` starting at 10 and deducting means empty reports get 10/10.
Always build from 0. Same for `_score_audience` (base was 5 for any summary).

### Auto-Ingest: Call Backfill at Startup
`backfill_scores_from_audit()` is idempotent. Call it in `lifespan()` after
`init_hub_database()`. Zero overhead when no new scores. Every Render restart
picks up new audit entries automatically.

### Page Quality Scoring: Direct SQLite Write
Academy Tab 7 writes directly to `page_quality_scores` table in hub_data.db.
No backend dependency — same pattern as landing page. Creates table if missing
(defensive `CREATE TABLE IF NOT EXISTS` before insert).

### PageQualityAuditor Closes the Loop
Low page quality scores → `improvement_findings` → can be promoted to agent
proposals → executed → re-scored. This is the full closed loop:
Score → Finding → Proposal → Fix → Re-score.

## Legacy Cleanup Learnings (2026-02-21)

### Port References Are Toxic After Migration
When migrating from multi-process (ports 8500-8519) to single `st.navigation()`,
port numbers in user-facing text become confusing. They leak implementation details.
**Rule:** Search for `port 85\d\d` and `port 8000` after any architecture migration.
Replace with page names.

### Mock Data Must Be Labelled
`prompt_builder.py` had fake "Run Test Query" with hardcoded data pretending to execute SQL.
This violates Law 1 (honest code). If a feature is aspirational, label it honestly.
**Rule:** Never use `st.spinner("Running...")` + fake results. Either wire up real execution
or use `st.info()` explaining it's a preview.

### Database Test Pollution Prevention
Tests writing to production `hub_data.db` creates zombie rows (145 test agent entries,
129 PENDING proposals never processed). Tests should use temp DBs or clean up after.
**Rule:** Check `agent_proposals` and `improvement_findings` periodically for test pollution.

### Stale Counts Multiply Across Docs
When the Hub grew from 6→16→17→19 dashboards, counts in 15+ files went stale.
Each new dashboard should trigger a search for the old count across ALL docs.
**Rule:** After adding a page, run `grep -r "N dashboards\|N pages\|N Streamlit"` across the repo.

### CHANGELOG Is Historical — Don't Rewrite
CHANGELOG entries describe what existed at the time of that release. Don't update
"16/16 dashboards healthy" in a Feb 18 entry just because there are now 19.
Only update files that describe the *current* state.

## Goal Alignment Pattern (2026-02-21)

### render_header() Is the Single Point for Goal Context
`shared/styles.py:render_header(title, subtitle, goals=None, strategy_context=None)`
- `goals`: list of goal IDs (e.g. `["G1", "G2", "G4"]`) — renders coloured badges
- `strategy_context`: one-liner connecting data to strategy — renders in italic grey
- Backward compatible — existing calls without goals still work
- Uses `goal_badge_html()` from `goals_config.py` for consistent badge styling
**Rule:** When adding a new dashboard, always set `goals=` and `strategy_context=` in the
`render_header()` call. Reference `GOAL_PAGE_MAPPING` in `goals_config.py` for the mapping.

### Strategy Context Should Be Specific, Not Generic
Each dashboard's `strategy_context` connects its specific data to the strategy:
- Sales: "validates 'Bigger'" (revenue growth)
- Profitability: "drives 'Better'" (margin visibility)
- Customers: "focus on customers who love us most" (Fewer, Bigger, Better)
- Supply chain pages: reference Pillar 4 language ("pay to purchase")
Never use generic text like "supports the strategy" — say *which part* and *how*.
