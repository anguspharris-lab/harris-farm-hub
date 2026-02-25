# First Day at The Hub — Rollout Plan

*Phased rollout recommendations based on 20-persona simulation*
*Generated 2026-02-22*

---

## Rollout Principle

**Pull, don't push.** Let early successes create demand. Mandate kills adoption; demonstration drives it. Start with personas who had breakthrough moments, let them become advocates, then expand.

---

## Phase 0: Pre-Pilot Fixes (1 week)

Before any users touch The Hub, fix the 5 P0 issues:

1. Add search bar on Home page
2. Add role-based navigation (role selector at first login)
3. Fix mobile responsiveness (hamburger nav on phone)
4. Add usage analytics (page view logging)
5. Distribute credentials via existing channels (intranet, store notice boards, new-starter packs)

**Owner:** Phil (CTO)
**Verify:** All 5 P0 items pass testing before pilot starts

---

## Phase 1: Pilot Group A — "The Believers" (2 weeks)

### Who: 10 users, two cohorts

**Cohort 1: Procurement Team (5 users)**
- James (Procurement Buyer) + 4 peers
- Why: James scored 8.3/10. PLU Intelligence replaced 3 Excel reports. His team will see immediate value.
- Entry point: Direct link to Buying Hub + PLU Intelligence
- Success metric: 3+ weekly active users, 1 quantified time saving ("PLU Intelligence saves X hours/week")

**Cohort 2: Graduate Program (5 users)**
- Kai + 4 fellow graduates
- Why: Kai scored 8.4/10. Digitally native, competitive, will use gamification. Best organic advocates in the org.
- Entry point: Guided "Welcome to Harris Farm" journey > Academy > Prompt Engine
- Success metric: All 5 earn 100+ XP in 2 weeks, at least 2 submit Prompt Engine outputs

### Onboarding for Phase 1
- **15-minute walkthrough** per cohort (not a training session — a "let me show you the 3 things you'll love")
- **Direct links** to their relevant pages (not "go explore")
- **Slack channel** `#hub-pilot` for feedback and questions
- **Daily check-in** from Phil for first 3 days, then weekly

### Measures
| Metric | Target | How |
|--------|--------|-----|
| Weekly active users | 8/10 | Usage analytics |
| Pages visited per user | 5+ | Usage analytics |
| Prompt Engine submissions | 5+ total | PtA submissions table |
| Academy XP earned | 500+ total | Academy leaderboard |
| User satisfaction | 7+/10 | Quick survey at day 7 |
| Time saved (procurement) | Quantified | James interview |

---

## Phase 2: Expand to Champions (2 weeks, after Pilot A succeeds)

### Who: 15 additional users

**Cohort 3: Store Managers — Select Stores (5 users)**
- Karen (Bondi Junction) + 4 store managers from large-format stores
- Why: Karen scored 7.0/10. With store pinning and role-based nav (Phase 0 fixes), she'll get value in 2 minutes.
- Entry point: Direct link to "My Store" sales view (pre-filtered)
- Must have: Store pinning working, mobile nav fixed

**Cohort 4: Head of Ops + Finance (3 users)**
- Sean (Head of Ops) + Rebecca (Finance Analyst) + 1 peer
- Why: Sean scored 8.0 (PLU Intel), Rebecca scored 7.3 (Revenue Bridge)
- Entry point: Operations dashboard, Revenue Bridge
- Must have: CSV export buttons on Sales, Profitability, Revenue Bridge

**Cohort 5: People & Culture (2 users)**
- Laura (Head of People) + 1 HR peer
- Entry point: People intro page > Learning Centre > Academy
- Must have: Academy has 5 starter modules with real content

**Cohort 6: Marketing — Analyst Only (2 users)**
- Liam (Marketing Analyst) + 1 peer
- Why: Liam scored 7.9. Market share data and Analytics Engine are genuinely useful for him.
- Entry point: Customer Hub > Market Share, Analytics Engine
- NOT including broader marketing team yet (no ROAS data = no CMO value)

**Cohort 7: Weekend Buyer + Content Creator (3 users)**
- Zara (Weekend Buyer) + Tilly (Content Creator) + 1 peer
- Why: Both found unexpected value (Zara: AI for buying, Tilly: data-driven content). They're innovators.
- Entry point: Prompt Engine, Trending, Marketing Assets

### Onboarding for Phase 2
- **5-minute peer demo** from Phase 1 pilot users (James shows procurement, Kai shows grads)
- **"Hub Quick Start" one-pager** per role: 3 features, 3 links, 1 expected benefit
- **Weekly feedback collection** via 3-question survey

### Measures
| Metric | Target | How |
|--------|--------|-----|
| Weekly active users | 20/25 | Usage analytics |
| Cross-pillar usage | 3+ pillars visited per user | Usage analytics |
| Prompt Engine quality | Avg Rubric score > 7.0 | PtA leaderboard |
| Store manager return rate | 4/5 return in week 2 | Usage analytics |
| Advocacy question: "Would you recommend?" | 60%+ Yes | Survey |

---

## Phase 3: Broader Rollout (4 weeks, after Phase 2 succeeds)

### Who: All remaining desk-based knowledge workers (~50 users)

- All store managers (remaining ~35)
- All procurement/buying team
- Finance team
- Full People & Culture team
- Marketing team (with caveats — see below)
- Digital & AI team

### Marketing Rollout Conditions
Do NOT include the full marketing team until:
1. Brand voice is configured in Prompt Engine
2. Marketing-specific templates exist (Social Caption, Email Campaign, Campaign Brief)
3. At minimum, manual ROAS input is available
4. Sophie (CMO) has been briefed on what exists vs what's coming

### Onboarding for Phase 3
- **Self-service** — guided first-login experience with role selector
- **2-minute video** per role showing "Your first 5 minutes on The Hub"
- **"Hub Champions" network** — 1 trained user per team who can help colleagues
- **Monthly "Hub Wins" email** — showcasing real value delivered (time saved, insights found, quality scores)

---

## Phase 4: Frontline Staff (8 weeks, after Phase 3 succeeds)

### Who: Store floor staff, warehouse operators, transport (~500+ users)

### Prerequisites (MUST be done first):
1. Mobile-first simplified interface or PWA
2. Task-based Home: "I need to..." (lookup PLU, find policy, complete training)
3. Quick lookup tool (one input, one answer, 10 seconds)
4. SSO or QR-code login (passwords don't work for shared terminals)
5. At least 5 real Academy modules with completion tracking

### Strategy
- **Don't mandate "use The Hub"** — mandate specific tasks that happen to be on The Hub
- Example: "Complete your quarterly food safety refresher on The Hub" (not "explore The Hub")
- Example: "Look up the PLU for new products on The Hub" (not "check out PLU Intelligence")
- **Measure completion of tasks, not logins**

---

## Rollout Timeline

```
Week 0:     Fix P0 issues (search, nav, mobile, analytics, creds)
Week 1-2:   Phase 1 — 10 pilot users (procurement + grads)
Week 3:     Review pilot data, fix issues, collect testimonials
Week 4-5:   Phase 2 — 15 additional users (store mgrs, ops, finance, analyst)
Week 6:     Review, iterate, prepare marketing rollout conditions
Week 7-10:  Phase 3 — All knowledge workers (~50 users)
Week 11+:   Phase 4 — Frontline staff (requires mobile-first redesign)
```

---

## Communication Strategy by Tier

### Executives
- **Message:** "The Hub gives you real-time visibility into all 5 pillars — initiatives, performance, and AI adoption — in one place."
- **Channel:** 1:1 demo from Phil or Angus
- **Cadence:** Monthly exec summary email with 5 key metrics

### Store Managers
- **Message:** "Your store's sales, right now, in 3 clicks. Plus AI tools to write your weekly briefing."
- **Channel:** Peer demo from Karen (after Phase 2), regional manager endorsement
- **Cadence:** Monday morning "Your Week at a Glance" notification

### Supply Chain
- **Message:** "PLU Intelligence shows you product performance across 43 stores. The data you've been building manually is now automated."
- **Channel:** James presents at next procurement meeting
- **Cadence:** Weekly "Top Movers" automated insight

### Marketing
- **Message:** "Brand assets, AI-powered content drafts, and product trends for data-driven storytelling. More marketing data feeds coming Q2."
- **Channel:** Sophie briefing first, then team walkthrough
- **Cadence:** Weekly "What's Trending" content inspiration push
- **WARNING:** Set expectations clearly. Do not oversell. The gap between promise and reality will create active detractors.

### Frontline Staff
- **Message:** "Need a PLU? Need a policy? Need to complete training? It's all in one place now."
- **Channel:** Store manager introduces in team meeting, QR code poster in break room
- **Cadence:** Only when they need it — don't spam

### New Starters
- **Message:** "Welcome to Harris Farm. The Hub is your guide to understanding the company, completing your training, and getting started with AI."
- **Channel:** Part of HR onboarding pack (Day 1)
- **Cadence:** Automated "Week 1 / Week 2 / Week 4" journey nudges

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|:-:|:-:|---|
| CFO becomes active detractor | High | High | Brief Damien separately. Show Revenue Bridge value. Add CSV export. Don't claim to replace FloQast. |
| CMO tells marketing team "it's not for us" | High | Med | Brief Sophie before any marketing rollout. Set clear expectations. Show Liam's positive experience. |
| Store managers ignore after first visit | Med | High | Store pinning, Monday morning notification, peer advocacy from Karen. |
| Warehouse staff refuse to engage | High | Low (for now) | Don't force it. Fix mobile UX and task-based navigation first. Phase 4 timing. |
| Pilot users frustrated by bugs | Med | High | Daily check-ins in week 1. Dedicated #hub-pilot Slack channel. Fast fix turnaround. |
| Privacy concerns about usage analytics | Low | Med | Transparent: "We track page views to improve The Hub, not to monitor individuals." Anonymise by default, aggregate by role. |
