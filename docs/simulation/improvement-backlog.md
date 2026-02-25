# First Day at The Hub — Improvement Backlog
*Prioritised fixes from 20-persona simulation*
*Generated 2026-02-22*

## Prioritisation Rules
- P0 (Do Now): Blocks 5+ personas OR prevents any store-tier persona from getting value
- P1 (This Sprint): Reduces scores below 8 for 3+ personas
- P2 (Next Sprint): Affects 1-2 personas or polish items
- P3 (Backlog): Nice-to-haves that elevate 8 to 9-10

## P0 — Do Now (Pre-Pilot)

| # | Issue | Personas Affected | Impact | Effort | Recommendation |
|---|-------|-------------------|--------|--------|----------------|
| 1 | No search bar on Home page | Trevor, Marco, Darren, Bella, Damien (5+) | High | S | Add prominent search bar on Home: "What are you looking for?" Natural language search across pages, KB articles, and features. |
| 2 | Mobile layout broken — top nav illegible on phone | Marco, Priya, Tilly, Zara, Bella (5+) | High | M | Responsive redesign of top nav: collapse to hamburger menu on mobile. Or create a mobile-first landing page with 5 large buttons (My Store, Training, AI Tools, Policies, Help). |
| 3 | No role-based navigation | ALL 20 personas | High | M | Add a role selector at first login. Show 5-8 pages relevant to role. Store Manager sees: My Store Sales, Staff Training, Prompt Engine, Hub Assistant. Warehouse Operator sees: Training Modules, Safety, SOPs. Marketing sees: Assets, Prompt Engine, Customer Data, Trending. |
| 4 | Password distribution problem — no SSO | Trevor, Darren (can't get started) | High | L | Short-term: include Hub URL and password in every new-starter pack, store notice board, intranet link. Medium-term: SSO via Dayforce or Microsoft Entra. |
| 5 | No usage analytics | Phil, Angus (can't prove value to board) | High | M | Add page-view tracking (log to hub_data.db on every page load): user_id, page, timestamp. Build an Adoption Dashboard showing: unique users/week, pages/session, top pages, usage by role/department. |

## P1 — This Sprint (Week 1-2 of Pilot)

| # | Issue | Personas Affected | Impact | Effort | Recommendation |
|---|-------|-------------------|--------|--------|----------------|
| 6 | PLU lookup for 2-minute users (not analytics) | Marco, Zara | Med | S | Add a "Quick Lookup" tab to PLU Intelligence: type a product name or PLU code, get instant result. No filters needed. One input, one answer. |
| 7 | Store default pinning | Karen, Trevor, Marco (all store tier) | Med | S | After first store selection, save to session_state and persist via user profile. "Always show my store first." |
| 8 | CSV export on key dashboards | Damien, Rebecca, Liam | Med | S | Add explicit "Export to CSV" button on Sales, Profitability, Market Share pages. (The hidden dataframe download icon isn't discoverable.) |
| 9 | "New Starter? Start Here" path | Bella, Kai | Med | S | Add a prominent card on the Home page: "New to Harris Farm? Start here" linking to a curated journey: Company Values > Learning Centre > Academy > Hub Assistant. |
| 10 | Brand voice configuration for Prompt Engine | Megan, Tilly, Josh | Med | M | Add a system prompt prefix to the Prompt Engine that includes Harris Farm's tone of voice guidelines: warm, community-focused, family-owned, "For The Greater Goodness." Pull from brand_guidelines.pdf or create a brand voice config file. |
| 11 | eNPS integration (People intro page) | Laura | Med | M | Connect to Dayforce engagement survey or add a manual input field for eNPS score on the People intro page. Replace "Coming Soon" card with live data. |

## P2 — Next Sprint (Week 3-4)

| # | Issue | Personas Affected | Impact | Effort | Recommendation |
|---|-------|-------------------|--------|--------|----------------|
| 12 | Marketing-specific data connections | Sophie, Liam, Josh | Med | L | Phase 1: Add manual ROAS/CPA input fields (marketing team updates weekly). Phase 2: Meta Ads API integration for live ROAS. Phase 3: Klaviyo integration for email metrics. |
| 13 | Marketing Assets version control | Megan | Low | M | Add "status" field to index.json (current/archived/draft). Add upload date, approved_by, and version fields. Show "Current" badge on approved assets. |
| 14 | Prompt Engine creative content scoring | Tilly, Josh | Low | M | Add a "Creative Content" rubric variant in pta_rubric.py: score brand voice, emotional resonance, platform-appropriateness instead of data citations and analytical rigour. |
| 15 | Academy pilot content — 5 starter modules | Laura, Kai, Bella | Med | M | Create 5 real Learning Centre modules: (1) Welcome to Harris Farm, (2) The 5 Pillars Explained, (3) AI at Harris Farm — Getting Started, (4) Using the Prompt Engine, (5) Understanding Our Customers. Each awards 50-100 XP. |
| 16 | Transport real-time tracking | Priya | Low | L | Integrate with TMS (if available) or add manual delivery status updates. Show "In Transit / Delivered / Delayed" per store per day. |
| 17 | Revenue Bridge CSV export | Rebecca | Low | S | Add export button on Revenue Bridge — she'd stop building the manual Excel version. |

## P3 — Backlog (Future Sprints)

| # | Issue | Personas Affected | Impact | Effort | Recommendation |
|---|-------|-------------------|--------|--------|----------------|
| 18 | SSO integration (Microsoft Entra / Dayforce) | All | Med | L | Eliminate password distribution. Auto-assign roles based on job title from Dayforce. |
| 19 | Power BI connector / read-only SQL API | Liam | Low | L | Expose a read-only API or SQL endpoint so analysts can connect Power BI to Hub data without duplicating queries. |
| 20 | Marketing dashboard (ROAS, CPA, email metrics) | Sophie, Liam, Josh | High | L | Full marketing intelligence dashboard: ROAS by channel, CPA tracking, email open/click rates, loyalty active members, LTV cohorts. Requires Meta Ads, Google Ads, and Klaviyo API integrations. |
| 21 | Shared terminal session isolation | Darren | Low | M | Auto-logout after 15 minutes of inactivity on shared terminals. Clear session state on new login to prevent cross-user data leakage. |
| 22 | Image editing / template tools in Marketing Assets | Megan, Tilly | Low | L | Add simple image overlay capability (add text to campaign template) or integrate with Canva API for asset customisation. |
| 23 | FloQast reconciliation notes | Damien, Rebecca | Low | M | Add a "Data Source Notes" section on Sales/Profitability pages explaining: "These figures are POS-derived and may differ from reconciled P&L by ±2% due to timing and adjustment differences." |
| 24 | Dayforce HCM integration for People metrics | Laura | Med | L | Pull turnover rate, headcount, training completion from Dayforce API. Replace "Coming Soon" cards on People intro page with live data. |

---

## Cross-Persona Pattern Analysis

### Systemic Issues (Hit 5+ Personas)
1. **Navigation overload** — 33 pages, no role filtering, no search (ALL 20)
2. **Mobile UX broken** — top nav, table layouts, filter controls (10+ store/SC/marketing)
3. **No adoption metrics** — can't prove value (Phil, Angus, Laura + all execs)
4. **Missing Excel/CSV export** — data users can't action the insights (5+)

### Tier-Specific Gaps
| Tier | Primary Gap | Secondary Gap |
|------|-------------|---------------|
| Executive | No adoption metrics | No exec dashboard (5 numbers, 1 page) |
| Store | Mobile UX + navigation | No store pinning, no quick lookup |
| Supply Chain | Not designed for them at all | No integration with operational tools |
| Marketing | No marketing data (ROAS, CRM) | AI content lacks brand voice |
| Support | Hidden export buttons | No reconciliation notes |
| New Starter | No guided first-week journey | Empty leaderboard (needs pilot data) |

### The 2-Minute Test
| Persona | Value in 2 min? | Why / Why Not |
|---------|:-:|---|
| Marco (Produce DM) | NO | Needed a PLU lookup, got a dashboard |
| Darren (Warehouse) | NO | Couldn't find the training module |
| Trevor (Store Mgr) | NO | Couldn't find his store in the filter |
| Karen (Store Mgr) | YES | Found her store's sales data in 3 min (close) |
| Priya (Transport) | YES | Found transport cost data in 2 min |

### The Advocacy Test — "Would you recommend The Hub to a colleague?"
| Would Advocate | Name | Why |
|:-:|---|---|
| YES | Kai (Grad) | "It's like Duolingo for understanding the company" |
| YES | James (Procurement) | "Replaced 3 Excel reports" |
| YES | Zara (Weekend Buyer) | "AI that knows about our products" |
| YES | Sean (Head of Ops) | "PLU Intelligence across 43 stores" |
| MAYBE | Rebecca (Finance) | "Revenue Bridge is good but I need export" |
| MAYBE | Tilly (Content) | "Trending data is great for content ideas" |
| NO | Sophie (CMO) | "No ROAS, no campaign data. It's not for marketing." |
| NO | Damien (CFO) | "Doesn't match FloQast. Can't use it for reporting." |
| NO | Trevor (Store Mgr) | "Couldn't even find my store" |
| NO | Darren (Warehouse) | "Not for people like me" |

---

## Quick Wins (High Impact, Low Effort)

1. **Search bar on Home page** — S effort, unblocks 5+ personas
2. **PLU Quick Lookup tab** — S effort, serves produce department managers
3. **Store pinning** — S effort, saves every store persona 60s per visit
4. **CSV export buttons** — S effort, unblocks finance and analyst personas
5. **"New Starter" card on Home** — S effort, guided onboarding path
