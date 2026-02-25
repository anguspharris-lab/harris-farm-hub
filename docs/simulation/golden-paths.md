# First Day at The Hub — Golden Paths
*Optimised first-visit journeys by role tier*
*Generated 2026-02-22*

---

## What Is a Golden Path?

A golden path is the **ideal first-visit journey** for a specific role. Instead of "explore the platform," each user gets a curated 3-5 step sequence that delivers their highest-value moment in the minimum time.

The simulation showed that personas who found their golden path scored 7+ (Karen, Rebecca, Liam). Personas who were left to explore freely scored below 5 (Trevor, Marco, Darren).

**Rule: Nobody should ever see the full 33-page nav on their first visit.**

---

## Path 1: Executive (Co-CEO, CFO, CTO, Department Heads)

**For:** Angus, Luke, Damien, Sean, Laura, Phil, Sophie
**Time to value:** 2 minutes
**Entry point:** Direct link to Landing page

### Journey
1. **Landing Page** (30s) — See the 5-pillar strategy overview, System Health metrics, Quick Launch buttons
2. **Way of Working** (60s) — See all Monday.com initiatives across 5 pillars: how many done, in progress, stuck. Board-ready status view.
3. **Their Pillar Intro Page** (30s) — e.g., Phil → Digital & AI HQ, Sean → Operations HQ. See strategic question, hero metrics, initiative summary.
4. **One Data Deep-Dive** (optional) — e.g., Sean → Sales Dashboard, Phil → Mission Control

### Expected Value
- "I can see the entire strategy's progress in one place"
- "I know which pillar is behind and where to focus"
- Board-paper-ready data in 2 minutes

### What Must Work
- Landing page loads fast with real metrics
- Way of Working shows Monday.com data (or graceful Coming Soon)
- Pillar intro pages show live hero metrics where available

---

## Path 2: Store Manager (Large and Small Format)

**For:** Karen, Trevor, and all ~40 store managers
**Time to value:** 90 seconds
**Entry point:** Direct link "Your Store"

### Journey
1. **Sales Dashboard — Pre-filtered to their store** (30s) — This week vs last week, YoY comparison, top/bottom departments
2. **Store Ops** (30s) — Their store's operational metrics, staffing context
3. **Prompt Engine** (30s) — "Write my weekly team briefing" using store data as context
4. **Hub Assistant** (optional) — "What's the policy on..." for quick policy lookups

### Expected Value
- "My store's sales right now, in 3 clicks"
- "I can write my Monday briefing in 60 seconds with AI"
- Monday morning utility: open The Hub → see my numbers → write my briefing → done

### What Must Work
- Store pinning: after first selection, always default to their store
- Sales dashboard loads their store without navigating 43-store dropdown
- Prompt Engine "Store Weekly Briefing" template exists and works

### Critical Fix Required
- Add store pinning (P1 backlog #7)
- Pre-filter URL: `?store=Bondi+Junction` parameter support
- Mobile-responsive Sales page (P0 backlog #2)

---

## Path 3: Supply Chain (Procurement, Buying, Weekend Buyer)

**For:** James, Zara, and procurement/buying teams
**Time to value:** 60 seconds
**Entry point:** Direct link to Buying Hub

### Journey
1. **Buying Hub** (30s) — Category performance, supplier insights, margin analysis
2. **PLU Intelligence** (60s) — Search specific PLU across 43 stores, see network-wide performance. The breakthrough moment: "This replaced my Excel report."
3. **Product Intel** (30s) — Price benchmarking, competitor product data
4. **Prompt Engine** (optional) — "Analyse category X performance" or "Draft supplier negotiation brief"

### Expected Value
- "I can see product performance across all 43 stores in 15 seconds"
- "PLU Intelligence replaced 3 of my weekly Excel reports"
- Data-driven buying decisions without manual spreadsheet work

### What Must Work
- PLU Intelligence loads fast with the full 27.3M row dataset
- PLU Quick Lookup tab exists for instant product search (P1 backlog #6)
- Buying Hub shows real category/supplier data

---

## Path 4: Marketing Team

**For:** Sophie, Megan, Josh, Liam, Tilly
**Time to value:** 2-3 minutes (longer due to expectation management)
**Entry point:** Depends on sub-role

### Sub-Path 4A: Marketing Analyst (Liam)
1. **Customer Hub** (60s) — Customer count trends, demographic patterns
2. **Market Share** (60s) — Postcode-level competitive intelligence for campaign targeting
3. **Analytics Engine** (60s) — Cross-sell analysis on 383M transactions (basket analysis)
4. **Trending** (30s) — What's selling now, content inspiration

### Sub-Path 4B: Brand Manager / Content Creator (Megan, Tilly)
1. **Marketing Assets** (60s) — Brand guidelines, campaign creatives, download what you need
2. **Prompt Engine** (60s) — AI-generated content drafts (with brand voice caveat)
3. **Trending** (30s) — Data-driven content inspiration
4. **Market Share** (optional) — Competitive context for campaign planning

### Sub-Path 4C: CMO (Sophie)
1. **Customer Hub** (60s) — Headline customer metrics
2. **Market Share** (60s) — Competitive position by postcode
3. **Marketing Assets** (30s) — Asset library overview
4. **HONEST CONVERSATION** — "ROAS, email metrics, and brand health tracking are not yet connected. Here's the roadmap."

### Expected Value
- Liam: "Market share data is genuinely useful for targeting and competitive analysis"
- Megan/Tilly: "Asset centralisation is useful; AI drafts need brand voice training"
- Sophie: "Good competitive intel, but not a marketing intelligence platform yet"

### What Must Work
- Marketing Assets page loads with all 19 assets
- Market Share provides postcode-level intelligence
- Prompt Engine works (with honest caveat about generic output)

### Critical Warning
**Do NOT position The Hub as a marketing intelligence platform.** It is a competitive intelligence + content creation tool for marketing. The board reporting capability gap (0.5/8 on marketing rubric) must be communicated clearly to Sophie before any marketing team rollout.

---

## Path 5: People & Culture

**For:** Laura, HR team
**Time to value:** 2 minutes
**Entry point:** Direct link to People intro page

### Journey
1. **People Intro Page — "Growing Legends"** (30s) — Strategic question, Academy adoption metrics, PtA submission count
2. **Academy** (60s) — Leaderboard, XP tracking, daily challenges. See gamification system in action.
3. **Learning Centre** (30s) — Training modules (needs 5 starter modules — P2 backlog #15)
4. **Prompt Engine** (30s) — "Draft onboarding welcome email" or "Create training summary"

### Expected Value
- "I can see Academy adoption and AI engagement across the org"
- "The gamification system will drive training completion"
- "Prompt Engine helps standardise people comms"

### What Must Work
- Academy leaderboard shows data (even if only pilot users)
- People intro page shows live PtA submissions and Academy XP
- Learning Centre has at least placeholder module structure

---

## Path 6: New Starter / Graduate

**For:** Kai, Bella, all new hires
**Time to value:** 5 minutes (discovery is the value)
**Entry point:** "New to Harris Farm? Start here" card on Home page

### Journey
1. **Home — "New Starter" Card** (10s) — Click "Start here" to begin guided journey
2. **Greater Goodness Intro Page** (60s) — Learn the company values, sustainability commitment
3. **Pillar Intro Pages** (2 min) — Quick tour of all 5 strategic pillars and what they mean
4. **Academy** (60s) — Create profile, earn first XP, see daily challenge
5. **Hub Assistant** (60s) — Ask "What's the dress code?" or "How do I apply for leave?" — get instant answer from 543-article knowledge base

### Expected Value
- "I understand the company strategy in 5 minutes"
- "The Academy makes learning feel like a game"
- "I can ask the Hub Assistant anything about company policy"

### What Must Work
- "New Starter" card exists on Home page (P1 backlog #9)
- Pillar intro pages load with strategic context
- Hub Assistant responds with accurate KB answers
- Academy allows immediate profile creation and XP earning

---

## Path 7: Frontline / Warehouse (Future — Not Ready)

**For:** Darren, Marco, transport operators, store floor staff
**Time to value:** TARGET 30 seconds (currently fails)
**Entry point:** Task-based mobile interface (DOES NOT YET EXIST)

### Intended Journey (Post Mobile Redesign)
1. **"I need to..."** screen (5s) — Large buttons: "Look up a PLU", "Find a policy", "Do training", "Report an issue"
2. **Quick Lookup** (10s) — Type product name → get PLU code, price, margin instantly
3. **Hub Assistant** (15s) — "What's the food safety temperature for chicken?" → instant answer
4. **Training Module** (if time) — Complete daily module, earn XP

### Current Status: NOT READY
- No mobile-first interface
- No quick lookup tool
- No task-based navigation
- Shared terminal sessions not isolated
- **Do NOT roll out to frontline staff until Phase 4 prerequisites are met (see rollout-plan.md)**

---

## Implementation Notes

### How to Deploy Golden Paths

1. **Role selector at first login** — User selects their role (Store Manager, Procurement, Marketing, etc.)
2. **Role determines default nav** — Show only 5-8 pages relevant to that role
3. **Direct links in comms** — Don't send people to harris-farm-hub.onrender.com. Send them to harris-farm-hub.onrender.com/sales?store=Bondi+Junction
4. **Peer demos, not training sessions** — James shows procurement team. Karen shows store managers. Kai shows graduates.
5. **Measure golden path completion** — Track: did the user complete their 3-5 step journey? Where did they drop off?

### Golden Path Success Metrics

| Path | Target | Metric |
|------|--------|--------|
| Executive | 90% reach Way of Working within 2 min | Page sequence tracking |
| Store Manager | 80% view their store's sales within 90s | Store-filtered page view |
| Supply Chain | 80% use PLU Intelligence in first session | PLU Intel page view |
| Marketing | 70% download at least 1 asset | Download tracking |
| People | 70% view Academy leaderboard | Academy page view |
| New Starter | 90% complete 3+ pillar intros | Intro page sequence |
| Frontline | Not measured until Phase 4 | N/A |

---

*For The Greater Goodness — Harris Farm Markets*
