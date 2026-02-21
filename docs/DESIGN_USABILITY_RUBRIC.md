# Design & Usability Rubric

> Score every UI change against these 8 criteria. Below 5 on any = redesign before shipping.

---

## Scoring Scale

| Score | Meaning |
|-------|---------|
| 1-2 | Broken or unusable |
| 3-4 | Works but frustrating |
| 5-6 | Functional, acceptable |
| 7-8 | Good, intuitive |
| 9-10 | Excellent, delightful |

**Minimum threshold:** Average >= 7, no individual score below 5.

---

## The 8 Criteria

### 1. First-Use Clarity
> Can someone do the main task within 60 seconds without instructions?

| Score | Standard |
|-------|----------|
| 10 | User completes core task in <30s, zero confusion |
| 7 | User completes core task in <60s with minimal hesitation |
| 5 | User completes core task with minor trial-and-error |
| 3 | User needs to ask or read docs to do the basic thing |
| 1 | User has no idea what to do |

**Benchmark:** Uber — 3 taps to book a ride. First-time user succeeds immediately.

**Current Hub Score: 7/10**
- KPIs visible immediately on load
- Filters are clear and labelled
- Chart titles explain what you're looking at
- Minus: NL query section isn't obvious as the "ask anything" feature

### 2. Navigation
> Max 2 clicks to any feature. No dead ends.

| Score | Standard |
|-------|----------|
| 10 | Every feature reachable in 1 click, persistent nav always visible |
| 7 | 2 clicks max, clear back/home paths |
| 5 | Some features take 3+ clicks but discoverable |
| 3 | Hidden features, unclear how to get back |
| 1 | Users get lost, no consistent navigation |

**Benchmark:** Bottom nav always visible, breadcrumbs for depth.

**Current Hub Score: 5/10**
- Each dashboard is a separate Streamlit app (separate URL)
- No shared navigation bar between dashboards
- No way to jump from Sales → Profitability without knowing the URL
- Tabs within Prompt Builder work well

### 3. Visual Hierarchy
> KPIs big, charts below, details on drill-down. Most important info loudest.

| Score | Standard |
|-------|----------|
| 10 | Eye tracks naturally: headline KPIs → trends → details. Zero clutter |
| 7 | Clear hierarchy, minor competing elements |
| 5 | Hierarchy exists but some sections fight for attention |
| 3 | Flat — everything same size/weight |
| 1 | Chaotic, no visual structure |

**Benchmark:** Dashboard KPIs at top in large font, charts mid-page, tables at bottom.

**Current Hub Score: 7/10**
- st.metric cards are prominent at top of every dashboard
- Charts grouped logically (revenue trend → store breakdown → category mix)
- Tables at bottom as expected
- Minus: Some sections feel dense (product-level analytics on sales dashboard)

### 4. Consistency
> Same patterns and colours across all dashboards.

| Score | Standard |
|-------|----------|
| 10 | Identical patterns, colours, terminology across every screen |
| 7 | Consistent with minor variations |
| 5 | Generally consistent but some jarring differences |
| 3 | Each screen feels like a different app |
| 1 | No consistency at all |

**Benchmark:** Revenue = green, costs = red, everywhere. Same font, same layout grid.

**Current Hub Score: 6/10**
- All use st.metric, plotly, same basic layout
- Color scheme mostly consistent (#1e3a8a blue, #10b981 green, #ef4444 red)
- Each has NL query at bottom, footer with timestamp
- Minus: Transport uses different colour sets (Set2, Pastel). Header styles vary slightly.

### 5. Error Communication
> Tells user what happened AND what to do about it.

| Score | Standard |
|-------|----------|
| 10 | Friendly message, cause, fix, and next step |
| 7 | Clear message with suggested action |
| 5 | Error shown but no guidance |
| 3 | Generic "something went wrong" |
| 1 | Silent failure or cryptic error code |

**Benchmark:** Not "Error 500" — "We couldn't reach the database. Check your connection or try again in 30 seconds."

**Current Hub Score: 4/10**
- No error handling around API calls
- NL query silently returns mock data even when API is down
- No connection status indicator
- Streamlit will show raw Python tracebacks on crash
- Needs: try/except blocks with st.error() messages

### 6. Responsiveness
> Works desktop/tablet/phone. 44px minimum touch targets.

| Score | Standard |
|-------|----------|
| 10 | Fully responsive, touch-optimised, no horizontal scroll |
| 7 | Works on all sizes with minor layout shifts |
| 5 | Desktop-first, tablet usable, phone cramped |
| 3 | Desktop only, breaks on smaller screens |
| 1 | Doesn't work on anything but full-width desktop |

**Benchmark:** Streamlit's default is desktop-first. `layout="wide"` helps.

**Current Hub Score: 5/10**
- Streamlit handles basic responsiveness
- `layout="wide"` used consistently
- Plotly charts resize automatically
- Minus: Multi-column layouts (st.columns) compress poorly on mobile
- Minus: No explicit touch target sizing

### 7. Loading Feedback
> User always sees something happening. Spinner within 200ms.

| Score | Standard |
|-------|----------|
| 10 | Instant feedback, skeleton screens, progressive loading |
| 7 | Spinner appears immediately, data loads within 2s |
| 5 | Spinner present but sometimes delayed |
| 3 | No feedback during loading |
| 1 | Screen freezes with no indication |

**Benchmark:** Spinner within 200ms. Skeleton UI for large datasets.

**Current Hub Score: 6/10**
- `@st.cache_data` prevents repeat loads
- `st.spinner("Analyzing...")` used on NL queries
- Initial page load generates all mock data (slight delay)
- Minus: No loading indicators during chart rendering
- Minus: No skeleton screens

### 8. Accessibility
> 4.5:1 contrast, labels, keyboard navigation. WCAG 2.1 AA minimum.

| Score | Standard |
|-------|----------|
| 10 | Full WCAG 2.1 AA, screen reader tested, keyboard-only usable |
| 7 | Good contrast, all inputs labelled, logical tab order |
| 5 | Mostly accessible, some contrast issues |
| 3 | Significant accessibility gaps |
| 1 | Inaccessible to anyone with impairments |

**Benchmark:** WCAG 2.1 AA — 4.5:1 contrast ratio, all form inputs labelled.

**Current Hub Score: 5/10**
- Streamlit provides basic accessibility (labelled inputs, tab order)
- Plotly charts have hover text but no alt-text descriptions
- Custom CSS doesn't break tab order
- Minus: No explicit ARIA labels
- Minus: Chart-only insights not available in text form

---

## Current Hub Scorecard

| # | Criterion | Score | Status |
|---|-----------|-------|--------|
| 1 | First-Use Clarity | 7 | Pass |
| 2 | Navigation | 5 | Pass (borderline) |
| 3 | Visual Hierarchy | 7 | Pass |
| 4 | Consistency | 6 | Pass |
| 5 | Error Communication | 4 | **FAIL — redesign needed** |
| 6 | Responsiveness | 5 | Pass (borderline) |
| 7 | Loading Feedback | 6 | Pass |
| 8 | Accessibility | 5 | Pass (borderline) |
| | **Average** | **5.6** | **Below 7 threshold** |

### Priority Fixes

1. **Error Communication (4/10):** Add try/except around all API calls and data operations. Show `st.error()` with what happened + what to do. Add a connection status indicator.
2. **Navigation (5/10):** Add a shared sidebar or header nav linking all 23 pages + API status page. Every page should link to every other.
3. **Consistency (6/10):** Standardise colour palette across all dashboards. Create a shared `hub_theme.py` with constants.
4. **Accessibility (5/10):** Add text summaries below every chart. Ensure all interactive elements have labels.

---

## How to Use This Rubric

1. **After every UI task:** Score the affected dashboard against all 8 criteria
2. **Log scores** in CHANGELOG.md alongside the task description
3. **Any score below 5:** Stop and fix before moving to next task
4. **Weekly review:** Re-score all dashboards, track trend over time
5. **User testing:** Validate scores with actual finance team members within 2 weeks of launch
