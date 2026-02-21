# Harris Farm Hub -- Comprehensive Python Runtime Error Audit

**Date:** 2026-02-21
**Scope:** All `.py` files in `dashboards/`, `dashboards/shared/`, `dashboards/ai_adoption/`, selected backend files, and top-level entry points.
**Auditor:** Claude (research only -- no files modified)

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 7 |
| Warning  | 19 |
| Info     | 12 |
| **Total** | **38** |

---

## Critical Issues

### C-01. SQL Injection via f-string interpolation
**Files:**
- `/Users/angusharris/Downloads/harris-farm-hub/dashboards/product_intel_dashboard.py` line 66
- `/Users/angusharris/Downloads/harris-farm-hub/dashboards/revenue_bridge_dashboard.py` lines 65, 74

**Category:** 10 (Column/query safety)
**Severity:** Critical

Both dashboards construct SQL queries using f-string interpolation of user-selected `store_id`:

```python
store_filter = f"AND Store_ID = '{store_id}'" if store_id else ""
sql = f"""
    SELECT ...
    FROM transactions
    WHERE SaleDate >= CAST(? AS TIMESTAMP)
      AND SaleDate < CAST(? AS TIMESTAMP)
      {store_filter}
"""
```

The `store_id` comes from a Streamlit selectbox (which limits input to known values), but this pattern is dangerous because:
1. If the selectbox source data is corrupted or manipulated, arbitrary SQL can be injected.
2. The `TransactionStore.query()` method uses parameterised queries for `?` placeholders but the `store_filter` bypasses this.

**Suggested Fix:** Pass `store_id` as a parameterised value:
```python
store_clause = "AND Store_ID = ?" if store_id else ""
params = [start, end]
if store_id:
    params.append(store_id)
return ts.query(sql_with_placeholder, params)
```

---

### C-02. Unguarded division by zero in `plu_intel_dashboard.py`
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/plu_intel_dashboard.py` lines 71-72
**Category:** 7 (Division by zero)
**Severity:** Critical

```python
total_sales = df["sales"].sum()
total_gm = df["gm"].sum()
total_waste = df["wastage"].sum()

k2.metric("Gross Margin", f"${total_gm / 1e6:,.1f}M", f"{total_gm / total_sales * 100:.1f}%")
k3.metric("Wastage", f"${total_waste / 1e6:,.1f}M", f"{total_waste / total_sales * 100:.1f}%")
```

If `total_sales` is 0 (empty data after filtering `df = df[df["sales"] > 0]` returns all zeros or empty), both `total_gm / total_sales` and `total_waste / total_sales` will raise `ZeroDivisionError`.

**Note:** The filter on line 61 (`df = df[df["sales"] > 0]`) should prevent this, but if the PLU database has no data or the filter returns an empty dataframe, `total_sales` will be 0 and the code will crash before reaching the `if not df.empty` check (there is no such check).

**Suggested Fix:**
```python
gm_pct = (total_gm / total_sales * 100) if total_sales > 0 else 0
waste_pct = (total_waste / total_sales * 100) if total_sales > 0 else 0
```

---

### C-03. Unguarded division by zero in `customer_dashboard.py`
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/customer_dashboard.py` line 403
**Category:** 7 (Division by zero)
**Severity:** Critical

```python
total_identified = len(df_rfm)
multi_store = (df_rfm["stores_visited"] >= 2).sum()
multi_store_pct = multi_store / total_identified * 100
```

If `df_rfm` is empty (which can happen if the API returns an empty list for `rfm_data`), `total_identified` is 0 and this line raises `ZeroDivisionError`. The code checks `if not rfm_data:` above but the API could return a non-empty list that produces an empty DataFrame.

**Suggested Fix:**
```python
multi_store_pct = (multi_store / total_identified * 100) if total_identified > 0 else 0
```

---

### C-04. `int(pc)` on postcode strings may raise ValueError
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/market_share_dashboard.py` lines 137-139, 219-221, 863-865, 1000-1002, 1086-1088, 1199-1201
**Category:** 6 (pd.to_numeric / type conversion)
**Severity:** Critical

Postcodes are filtered by state using lambdas that call `int(pc)`:

```python
state_ranges = {
    "NSW": lambda pc: 2000 <= int(pc) <= 2999,
    "QLD": lambda pc: 4000 <= int(pc) <= 4999,
    "ACT": lambda pc: 2600 <= int(pc) <= 2618 or int(pc) in (2900, ...),
}
fn = state_ranges.get(state_filter)
if fn:
    mdf = mdf[mdf["postcode"].apply(lambda x: fn(x))]
```

If any postcode string is non-numeric (e.g., "NSW", empty string, or contains letters), `int(pc)` will raise `ValueError` and crash the entire dashboard.

The `market_share_layer.py` already filters by `length(region_code) = 4`, but the `market_share` table also contains state-level rows like "NSW", "QLD", "ACT", "AUS" which have non-numeric `region_code` values. If these leak into the DataFrame, the lambda will crash.

**Suggested Fix:**
```python
def safe_int(pc):
    try:
        return int(pc)
    except (ValueError, TypeError):
        return 0

state_ranges = {
    "NSW": lambda pc: 2000 <= safe_int(pc) <= 2999,
    ...
}
```

---

### C-05. `set()` in session state is not JSON-serializable
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/rubric_dashboard.py` lines 64, 66
**Category:** 9 (st.metric/session state)
**Severity:** Critical

```python
if "progress" not in st.session_state:
    st.session_state.progress = {
        "challenges_done": 0,
        "evaluations_done": 0,
        "providers_used": set(),   # <-- set()
        "best_scores": {},
        "badges": set(),           # <-- set()
    }
```

Streamlit serialises session state to JSON for persistence. Python `set()` objects are not JSON-serialisable. This will cause errors when Streamlit attempts to cache or persist session state.

**Suggested Fix:** Use lists instead:
```python
"providers_used": [],
"badges": [],
```

---

### C-06. `config.yaml` read at module import time -- crash if missing
**Files:**
- `/Users/angusharris/Downloads/harris-farm-hub/dashboards/ai_adoption/cache.py` line 15
- `/Users/angusharris/Downloads/harris-farm-hub/dashboards/ai_adoption/data_fetcher.py` line 17

**Category:** 4 (File path references)
**Severity:** Critical

```python
_CFG = yaml.safe_load((_DIR / "config.yaml").read_text())
```

Both files read `config.yaml` at import time (module-level). If the file is missing (deleted, deployment issue, wrong working directory), the import will raise `FileNotFoundError` and crash the entire AI Adoption Tracker dashboard, and potentially `hub_portal.py` which may import from these modules.

**Suggested Fix:** Wrap in try/except with a sensible default:
```python
try:
    _CFG = yaml.safe_load((_DIR / "config.yaml").read_text())
except FileNotFoundError:
    _CFG = {"platforms": {}, "refresh_interval_hours": 6, "cache_db": "data/ai_adoption_cache.db"}
```

---

### C-07. Hardcoded password in `streamlit_app.py`
**File:** `/Users/angusharris/Downloads/harris-farm-hub/streamlit_app.py` line 42
**Category:** 4 (Security / file references)
**Severity:** Critical

```python
if pw == "HFM2026!1":
```

Password is hardcoded in source code, violating WATCHDOG Law 4 ("Zero secrets in code -- .env only"). This file is in the git repository and the password is visible to anyone with repo access.

**Suggested Fix:** Move to environment variable:
```python
if pw == os.environ.get("HUB_PASSWORD", ""):
```

---

## Warning Issues

### W-01. `st.page_link()` fallback to "/" may fail
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/landing.py` lines 186-189
**Category:** 3 (st.page_link targets)
**Severity:** Warning

```python
page = _port_to_page(port)
if page:
    st.page_link(page, label=f"{d_icon} {label}", use_container_width=True)
```

The `_port_to_page()` function returns `None` if no matching page is found. When `page` is `None`, the link is simply not rendered, which is safe. However, if the nav registry and the actual page files get out of sync, users will see missing links with no error message or feedback.

**Suggested Fix:** Add an `else` clause displaying a disabled button or info message.

---

### W-02. `locals()` check for cross-tab variable
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/prompt_builder.py` line 435
**Category:** 10 (Column references after filtering)
**Severity:** Warning

```python
data=generated_sql if 'generated_sql' in locals() else "-- Run test first",
```

The variable `generated_sql` is defined in a different Streamlit tab scope. When the user clicks the "Export as SQL" button in tab 3, `generated_sql` may not exist in `locals()` because Streamlit re-runs the entire script on each interaction and the variable is only assigned inside a `if st.button(...)` block in another tab.

This will not crash (the fallback string is used), but the button will always show "-- Run test first" because `generated_sql` is never in scope when this button is clicked.

**Suggested Fix:** Store `generated_sql` in `st.session_state` when generated:
```python
st.session_state.generated_sql = sql_result
```

---

### W-03. `next()` without default may raise StopIteration
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/shared/fiscal_selector.py` lines 150, 168, 186
**Category:** 10 (Column references / iterator safety)
**Severity:** Warning

```python
q = next(q for q in quarters if q["quarter_no"] == selected_q)
m = next(m for m in months if m["month_no"] == selected_m)
w = next(w for w in weeks if w["week_no"] == selected_w)
```

If the generator finds no matching element, `next()` raises `StopIteration`. This is unlikely because `selected_q` comes from a selectbox populated from the same `quarters` list, but if data changes between the selectbox render and the `next()` call (e.g., Streamlit caching race condition), it will crash.

**Suggested Fix:** Use `next(..., None)` with a None check:
```python
q = next((q for q in quarters if q["quarter_no"] == selected_q), None)
if not q:
    st.error("Selected quarter not found")
    return _empty_result()
```

---

### W-04. `Path(__file__).parent` without `.resolve()` in data_access.py
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/shared/data_access.py` lines 27-28
**Category:** 4 (File path references)
**Severity:** Warning

```python
shared_dir = Path(__file__).parent
project_root = shared_dir.parent.parent
```

The project convention documented in MEMORY.md requires `Path(__file__).resolve().parent` because "Streamlit's script runner breaks relative paths without it." Without `.resolve()`, the path may be incorrect when Streamlit runs the script from a different working directory or via a symlink.

**Suggested Fix:**
```python
shared_dir = Path(__file__).resolve().parent
project_root = shared_dir.parent.parent
```

---

### W-05. `.iloc[0]` on potentially empty DataFrame in macro view
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/market_share_dashboard.py` lines 710, 715
**Category:** 8 (.iloc/.loc on potentially empty DataFrames)
**Severity:** Warning

```python
macro_df = pd.DataFrame(macro)
best = macro_df.iloc[0]
worst = macro_df.iloc[-1]
```

The code checks `if not macro:` but not `if macro_df.empty:`. If `macro` is a non-empty list but contains data that results in an empty DataFrame (unlikely but possible), `iloc[0]` raises `IndexError`.

**Suggested Fix:** Add `if not macro_df.empty:` guard.

---

### W-06. `.iloc[0]` on potentially empty DataFrame in PLU intel
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/plu_intel_dashboard.py` line 207
**Category:** 8 (.iloc/.loc on potentially empty DataFrames)
**Severity:** Warning

```python
item = df[df["plu_code"] == selected].iloc[0]
```

If no row matches the selected PLU code, `iloc[0]` will raise `IndexError`.

**Suggested Fix:**
```python
match = df[df["plu_code"] == selected]
if match.empty:
    st.warning("PLU not found in data.")
else:
    item = match.iloc[0]
```

---

### W-07. `.loc` with `.idxmin()`/`.idxmax()` on potentially empty result
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/transport_dashboard.py` line 482
**Category:** 8 (.iloc/.loc on potentially empty DataFrames)
**Severity:** Warning

```python
best_vehicle = vehicle_analysis.loc[vehicle_analysis['cost_per_pallet'].idxmin(), 'vehicle_type']
```

If `vehicle_analysis` is empty, `idxmin()` raises `ValueError`. The code should guard with an emptiness check.

**Suggested Fix:** Check `if not vehicle_analysis.empty:` before accessing.

---

### W-08. `scatter_mapbox` with potential NaN in size/color columns
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/market_share_dashboard.py` lines 273, 284, 295, 312, 475, 803, 922
**Category:** 5 (scatter_mapbox NaN guarding)
**Severity:** Warning

Multiple `scatter_mapbox` calls use columns like `bubble_size`, `trend_slope_annual`, `yoy_change_pp`, `share_change` for size and color. While line 247 does `mdf["market_share_pct"] = pd.to_numeric(...).fillna(0)` for the main bubble size, other columns like `trend_slope_annual` (line 243: `.fillna(0)`) are handled.

However, the `scatter_mapbox` at line 475 uses `size="size"` and `color="market_share_pct"` where the `size` column is computed as:
```python
map_df["size"] = map_df["market_share_pct"].clip(lower=0.5) * 2
```

If `market_share_pct` contains NaN values that weren't cleaned, `clip()` propagates NaN and `scatter_mapbox` may fail or display incorrectly.

The main map on lines 273-282 is properly guarded. The trade area map on line 475 and the cluster map on line 803 have less thorough NaN handling.

**Suggested Fix:** Add `.fillna(0)` before computing size columns in all scatter_mapbox calls.

---

### W-09. `json.loads()` on potentially malformed data
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/hub_portal.py` lines 1044-1048
**Category:** 9 (Receiving None or malformed data)
**Severity:** Warning

```python
try:
    tier_scores = json.loads(p.get("tier_scores", "{}"))
except Exception:
    tier_scores = {}
```

This is actually properly handled with a try/except. However, the same pattern should be checked elsewhere. The `learning_centre.py` file has `json.loads()` calls on API responses that may not be properly guarded.

**Note:** After review, this specific instance is safe. Marking as informational.

---

### W-10. `tuple[bool, str]` type hint requires Python 3.10+
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/ai_adoption/dashboard.py` line 39
**Category:** 1 (Syntax/compatibility)
**Severity:** Warning

```python
def _sync_platform(platform_key: str) -> tuple[bool, str]:
```

The project uses Python 3.9 (per MEMORY.md: "Streamlit binary: `/Users/angusharris/Library/Python/3.9/bin/streamlit`"). The `tuple[bool, str]` type hint (lowercase `tuple`) is only valid in Python 3.10+. In Python 3.9, this raises `TypeError` at function definition time.

Same issue in:
- `ai_adoption/data_fetcher.py` line 42: `-> tuple[bool, str]`
- `ai_adoption/data_fetcher.py` lines 35, 39: `-> list[dict]`
- `ai_adoption/cache.py` lines 100, 116, etc.: `list[dict]`

**Suggested Fix:** Either:
1. Add `from __future__ import annotations` at the top of each file, OR
2. Use `typing.Tuple[bool, str]` and `typing.List[dict]`

---

### W-11. `list[dict]` type hints require Python 3.9+
**Files:**
- `/Users/angusharris/Downloads/harris-farm-hub/backend/product_hierarchy.py` line 47: `-> list[dict]`
- `/Users/angusharris/Downloads/harris-farm-hub/backend/product_hierarchy.py` line 184: `-> list[dict]`
- `/Users/angusharris/Downloads/harris-farm-hub/backend/transaction_layer.py` line 180: `-> list[dict]`

**Category:** 1 (Syntax/compatibility)
**Severity:** Warning

These use `list[dict]` which works in Python 3.9+ but would fail in Python 3.8. Since the project targets Python 3.9, this is OK for now, but the `tuple[bool, str]` in ai_adoption (see W-10) is NOT OK on Python 3.9.

---

### W-12. `plu_layer.py` SQL f-string interpolation with `int()` cast
**File:** `/Users/angusharris/Downloads/harris-farm-hub/backend/plu_layer.py` lines 52, 75, 101, 130, 201
**Category:** 10 (SQL safety)
**Severity:** Warning

```python
fy_clause = f"AND f.fiscal_year = {int(fiscal_year)}" if fiscal_year else ""
```

The `int()` cast provides some protection against SQL injection, but this pattern is repeated 5 times and is fragile. If `fiscal_year` is a value that `int()` can parse but produces unexpected SQL (unlikely with `int()` but still a code smell), it could cause issues.

**Suggested Fix:** Use parameterised queries consistently:
```python
if fiscal_year:
    clauses.append("f.fiscal_year = ?")
    params.append(int(fiscal_year))
```

---

### W-13. Division by zero in `rubric_dashboard.py` score calculations
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/rubric_dashboard.py` lines 520, 554, 611
**Category:** 7 (Division by zero)
**Severity:** Warning

```python
avg = sum(scores.values()) / len(scores)                    # line 520
averages = {p: sum(s.values()) / len(s) for p, s in all_scores.items()}  # line 554
avg_score = sum(progress["best_scores"].values()) / len(progress["best_scores"])  # line 611
```

If `scores`, `s`, or `progress["best_scores"]` is an empty dict, `len()` returns 0 and division raises `ZeroDivisionError`.

**Suggested Fix:** Guard each with `if scores:` or use `len(scores) or 1`.

---

### W-14. `customer_dashboard.py` unguarded division at line 247
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/customer_dashboard.py` line 247
**Category:** 7 (Division by zero)
**Severity:** Warning

```python
online_pct = (
    online_customers / total_customers * 100
) if total_customers > 0 else 0
```

This one IS guarded (has `if total_customers > 0`), but line 695 is NOT:
```python
online_pct_ch = online_ct / total_ct * 100 if total_ct > 0 else 0
```

Line 695 is actually guarded too. After careful review, the customer_dashboard guards its divisions properly in most places EXCEPT line 403 (covered in C-03).

---

### W-15. `landing.py` column indexing could go out of range
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/landing.py` lines 148-150
**Category:** 8 (Index access on potentially wrong-sized containers)
**Severity:** Warning

```python
if _n_hubs > 3:
    row2 = st.columns(min(3, _n_hubs - 3))
    all_cols = all_cols[:3] + row2
col_idx = i if i < 3 else i
with all_cols[col_idx]:
```

If `_n_hubs > 6`, `col_idx` (which equals `i`) could exceed `len(all_cols)` (which is at most 6). Currently `_n_hubs` is 5, so `col_idx` maxes at 4 and `all_cols` has 5 elements (3 + 2). This is safe with current data, but fragile if more hubs are added.

**Suggested Fix:** Use modular indexing or iterate directly:
```python
col_idx = min(i, len(all_cols) - 1)
```

---

### W-16. `voice_realtime.py` API key in client-side JavaScript
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/shared/voice_realtime.py` line 18
**Category:** 4 (Security)
**Severity:** Warning

```python
REALTIME_KEY = os.getenv("OPENAI_REALTIME_API_KEY", "")
```

This key is subsequently embedded into JavaScript rendered via `components.html()`. While it reads from an environment variable (compliant with Law 4), the key ends up in the browser DOM and is visible via "View Source" or DevTools. Any user of the dashboard can extract the API key.

**Suggested Fix:** Proxy WebSocket connections through the backend API instead of exposing the key to the client.

---

### W-17. `hub_portal.py` API-dependent tabs may silently fail
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/hub_portal.py` (throughout)
**Category:** 9 (Receiving None)
**Severity:** Warning

The hub_portal.py makes extensive API calls with `try/except` blocks and fallback to `{}` or `[]`. However, some metric displays assume specific keys exist in the API response without checking:

```python
p.get("estimated_impact_aud", 0)
p.get("complexity", "?")
```

These use `.get()` with defaults, which is safe. However, when the API is down, many sections will show "No data" or fallback values silently without any error banner indicating the backend is unreachable.

**Suggested Fix:** Add a single top-of-page health check for the backend API with a visible warning banner if unreachable.

---

### W-18. `transaction_queries.py` `{store_filter}` in SQL templates
**File:** `/Users/angusharris/Downloads/harris-farm-hub/backend/transaction_queries.py` lines 38, 58
**Category:** 10 (SQL safety)
**Severity:** Warning

```python
"sql": """
    SELECT ...
    FROM transactions
    WHERE SaleDate >= CAST(? AS TIMESTAMP)
      AND SaleDate < CAST(? AS TIMESTAMP)
      {store_filter}
    ...
""",
```

The `{store_filter}` placeholder is resolved in the `run_query()` function. If `run_query()` properly parameterises the store filter, this is safe. The pattern is that `run_query()` replaces `{store_filter}` with `AND Store_ID = ?` and adds the parameter, which is correct. However, the templates themselves contain raw `{store_filter}` placeholders that could be misused.

**Suggested Fix:** Document the pattern clearly or use a query builder pattern that enforces parameterisation.

---

### W-19. `data_analysis.py` file too large to fully audit
**File:** `/Users/angusharris/Downloads/harris-farm-hub/backend/data_analysis.py`
**Category:** N/A
**Severity:** Warning

This file exceeds 25,000 tokens and could not be fully read. It should be audited separately for the same 10 categories.

---

## Info Issues

### I-01. Operator precedence in `data_fetcher.py`
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/ai_adoption/data_fetcher.py` lines 124-126
**Category:** 7 (Division/arithmetic)
**Severity:** Info

```python
"tokens": (result.get("num_tokens", 0)
           or result.get("input_tokens", 0)
           + result.get("output_tokens", 0)),
```

Due to Python operator precedence, `+` binds tighter than `or`, so this evaluates as:
```python
result.get("num_tokens", 0) or (result.get("input_tokens", 0) + result.get("output_tokens", 0))
```

This is actually correct behavior (if `num_tokens` is 0/falsy, fall back to `input_tokens + output_tokens`), but the lack of explicit parentheses makes intent unclear.

**Suggested Fix:** Add parentheses for clarity:
```python
"tokens": result.get("num_tokens", 0) or (result.get("input_tokens", 0) + result.get("output_tokens", 0)),
```

---

### I-02. Duplicate fiscal calendar logic across files
**Files:**
- `/Users/angusharris/Downloads/harris-farm-hub/dashboards/sales_dashboard.py` (contains inline 5-4-4 calendar)
- `/Users/angusharris/Downloads/harris-farm-hub/dashboards/profitability_dashboard.py` (contains inline 5-4-4 calendar)
- `/Users/angusharris/Downloads/harris-farm-hub/dashboards/shared/fiscal_selector.py` (imports from backend)
- `/Users/angusharris/Downloads/harris-farm-hub/backend/fiscal_calendar.py` (canonical source)

**Category:** 2 (Import validation)
**Severity:** Info

The 5-4-4 retail fiscal calendar is defined in at least 3 different places. The `shared/fiscal_selector.py` correctly imports from `backend/fiscal_calendar.py`, but `sales_dashboard.py` and `profitability_dashboard.py` maintain their own inline versions. If the calendar definitions diverge, dashboards could show inconsistent period boundaries.

**Suggested Fix:** Migrate all fiscal calendar usage to `shared/fiscal_selector.py` / `backend/fiscal_calendar.py`.

---

### I-03. `Path(__file__).parent` without `.resolve()` in backend files
**Files:**
- `/Users/angusharris/Downloads/harris-farm-hub/backend/transaction_layer.py` line 19: `Path(__file__).parent.parent`
- `/Users/angusharris/Downloads/harris-farm-hub/backend/plu_lookup.py` lines 12-13: `Path(__file__).parent.parent`

**Category:** 4 (File path references)
**Severity:** Info

These backend files use `Path(__file__).parent` without `.resolve()`. This is less critical for backend files (which are typically run via `uvicorn` from a known directory) than for Streamlit dashboards, but is inconsistent with the project convention.

**Suggested Fix:** Use `Path(__file__).resolve().parent` for consistency.

---

### I-04. `rubric_evaluator.py` uses blocking API in async functions
**File:** `/Users/angusharris/Downloads/harris-farm-hub/rubric_evaluator.py` lines 39, 72
**Category:** 2 (Import/runtime pattern)
**Severity:** Info

```python
async def query_claude(self, prompt: str, context: str = ""):
    message = self.claude_client.messages.create(...)  # synchronous call in async function
```

The `anthropic.Anthropic()` and `openai.OpenAI()` clients are synchronous. Calling them inside `async def` functions blocks the event loop. Only `query_grok()` uses a truly async `httpx.AsyncClient`. The `asyncio.gather()` on line 166 will not achieve true parallelism for Claude and ChatGPT calls.

**Suggested Fix:** Use `anthropic.AsyncAnthropic()` and `openai.AsyncOpenAI()`.

---

### I-05. `transport_dashboard.py` uses mock data
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/transport_dashboard.py` (entire file)
**Category:** N/A
**Severity:** Info

The transport dashboard generates all data using `np.random.RandomState(42)`. This is not a bug, but users may not realise the data is simulated. The dashboard does not display any warning about mock data.

---

### I-06. `data_layer.py` `MockDataSource` is the only working implementation
**File:** `/Users/angusharris/Downloads/harris-farm-hub/backend/data_layer.py` line 278
**Category:** N/A
**Severity:** Info

`FabricDataSource` raises `NotImplementedError`. The factory defaults to `"mock"` via environment variable `DB_TYPE`. This is by design but worth noting for production readiness.

---

### I-07. `configure_urls.py` and `setup_gdrive_urls.py` reference outdated data_loader.py format
**Files:**
- `/Users/angusharris/Downloads/harris-farm-hub/configure_urls.py`
- `/Users/angusharris/Downloads/harris-farm-hub/setup_gdrive_urls.py`

**Category:** 4 (File path references)
**Severity:** Info

These scripts expect a specific format in `data_loader.py` (Google Drive URL pattern with `REPLACE_WITH_FILE_ID`). The current `data_loader.py` uses GitHub Releases URLs instead. These scripts are obsolete and will not work with the current `data_loader.py`.

---

### I-08. `store_ops_dashboard.py` uses `pd.to_numeric(errors="coerce")` properly
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/store_ops_dashboard.py`
**Category:** 6 (pd.to_numeric usage)
**Severity:** Info

All `pd.to_numeric` calls in the codebase use `errors="coerce"` which converts failures to NaN rather than raising exceptions. This is the correct pattern. No issues found with this category.

---

### I-09. `hourly_charts.py` depends on column names from query results
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/shared/hourly_charts.py` (various lines)
**Category:** 10 (Column references)
**Severity:** Info

The hourly charts component accesses columns like `df_dow["DayOfWeekName"]` and `df_raw["DayOfWeekName"]`. These columns must be present in the query results passed to the rendering functions. The functions are wrapped in try/except blocks, so missing columns produce a warning rather than a crash.

---

### I-10. `streamlit_app.py` is a standalone legacy app
**File:** `/Users/angusharris/Downloads/harris-farm-hub/streamlit_app.py`
**Category:** N/A
**Severity:** Info

This file appears to be an older, standalone version of the Hub (before the multi-page architecture in `dashboards/app.py`). It uses `st.set_page_config()` which means it cannot be used as a page in the multi-page app. It is likely unused in the current deployment.

---

### I-11. `learning_centre.py` API calls without timeout
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/learning_centre.py` (various)
**Category:** 9 (Receiving None)
**Severity:** Info

API calls via `requests.get()` / `requests.post()` throughout `learning_centre.py` do not specify timeouts. If the backend is slow or unresponsive, these calls will block indefinitely, making the dashboard appear frozen.

**Suggested Fix:** Add `timeout=10` to all `requests` calls.

---

### I-12. `buying_hub_dashboard.py` uses guarded division
**File:** `/Users/angusharris/Downloads/harris-farm-hub/dashboards/buying_hub_dashboard.py` line 178
**Category:** 7 (Division by zero)
**Severity:** Info

```python
gp_pct = (gp_total / total_rev * 100) if total_rev > 0 else 0
```

Properly guarded. No issue.

---

## Files Audited

### Dashboards (19 files)
| File | Lines | Issues |
|------|-------|--------|
| `dashboards/app.py` | 152 | None |
| `dashboards/nav.py` | 134 | None |
| `dashboards/landing.py` | 247 | W-01, W-15 |
| `dashboards/sales_dashboard.py` | 751 | I-02 |
| `dashboards/customer_dashboard.py` | 1150 | C-03, W-14 |
| `dashboards/market_share_dashboard.py` | 1263 | C-04, W-05, W-08 |
| `dashboards/profitability_dashboard.py` | 788 | I-02 |
| `dashboards/transport_dashboard.py` | 591 | W-07, I-05 |
| `dashboards/store_ops_dashboard.py` | 955 | I-08 |
| `dashboards/buying_hub_dashboard.py` | 495 | I-12 |
| `dashboards/product_intel_dashboard.py` | 528 | C-01 |
| `dashboards/plu_intel_dashboard.py` | 235 | C-02, W-06 |
| `dashboards/chatbot_dashboard.py` | 163 | None |
| `dashboards/greater_goodness.py` | 524 | None |
| `dashboards/learning_centre.py` | 691 | I-11 |
| `dashboards/prompt_builder.py` | 576 | W-02 |
| `dashboards/rubric_dashboard.py` | 661 | C-05, W-13 |
| `dashboards/trending_dashboard.py` | 305 | None |
| `dashboards/revenue_bridge_dashboard.py` | 504 | C-01 |
| `dashboards/hub_portal.py` | 2199 | W-09, W-17 |

### Shared modules (17 files)
| File | Lines | Issues |
|------|-------|--------|
| `shared/auth_gate.py` | 416 | None |
| `shared/styles.py` | 122 | None |
| `shared/stores.py` | 42 | None |
| `shared/data_access.py` | 346 | W-04 |
| `shared/fiscal_selector.py` | 313 | W-03 |
| `shared/hierarchy_filter.py` | 299 | None |
| `shared/hourly_charts.py` | 205 | I-09 |
| `shared/time_filter.py` | 312 | None |
| `shared/learning_content.py` | 1165 | None |
| `shared/portal_content.py` | 467 | None |
| `shared/schema_context.py` | 698 | None |
| `shared/training_content.py` | 552 | None |
| `shared/voice_realtime.py` | 780 | W-16 |
| `shared/watchdog_safety.py` | 817 | None |
| `shared/agent_teams.py` | 1795 | None |
| `shared/ask_question.py` | 400 | None |
| `shared/__init__.py` | 0 | None |

### AI Adoption (4 files)
| File | Lines | Issues |
|------|-------|--------|
| `ai_adoption/dashboard.py` | 273 | W-10 |
| `ai_adoption/cache.py` | 210 | C-06, W-10 |
| `ai_adoption/data_fetcher.py` | 241 | C-06, W-10, I-01 |
| `ai_adoption/__init__.py` | 0 | None |
| `ai_adoption/config.yaml` | 15 | None |

### Backend (10 files)
| File | Lines | Issues |
|------|-------|--------|
| `backend/app.py` | 200+ | None (partially read) |
| `backend/transaction_layer.py` | 421 | I-03 |
| `backend/transaction_queries.py` | 700+ | W-18 |
| `backend/market_share_layer.py` | 1033 | None |
| `backend/plu_layer.py` | 252 | W-12 |
| `backend/plu_lookup.py` | 137 | I-03 |
| `backend/product_hierarchy.py` | 377 | W-11 |
| `backend/fiscal_calendar.py` | 341 | None |
| `backend/data_layer.py` | 365 | I-06 |
| `backend/data_analysis.py` | 25000+ | W-19 |

### Top-level (5 files)
| File | Lines | Issues |
|------|-------|--------|
| `streamlit_app.py` | 464 | C-07, I-10 |
| `data_loader.py` | 168 | None |
| `rubric_evaluator.py` | 289 | I-04 |
| `configure_urls.py` | 159 | I-07 |
| `setup_gdrive_urls.py` | 198 | I-07 |

---

## Priority Fix Order

1. **C-01** (SQL injection) -- Highest priority. Convert all f-string SQL to parameterised queries.
2. **C-07** (Hardcoded password) -- Move to environment variable immediately.
3. **C-02, C-03** (Division by zero) -- Simple guard clauses, quick fix.
4. **C-04** (int(pc) ValueError) -- Wrap in try/except, affects 6 locations.
5. **C-05** (set in session state) -- Replace with lists.
6. **C-06** (config.yaml crash) -- Add try/except at module level.
7. **W-10** (Python 3.9 type hints) -- Add `from __future__ import annotations`.
8. **W-16** (API key in browser) -- Requires architectural change to proxy via backend.

---

*End of audit report.*
