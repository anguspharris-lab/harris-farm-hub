# Harris Farm Hub — Information Architecture Audit

**Date:** 2026-02-22
**Auditor:** Claude Code (requested by Gus Harris)
**Scope:** All 23 registered routes (Home + 22 pages) in `dashboards/app.py`

---

## Table 1: Complete Page Inventory

| Route | Page Name | Current Pillar | Primary User | Action Type | Frequency | Data Source |
|-------|-----------|---------------|--------------|-------------|-----------|-------------|
| `/` | Home | — | Everyone | Navigate | Every session | hub_data.db |
| `/greater-goodness` | Greater Goodness | P1: Greater Goodness | Execs, marketing | View data | Monthly | Static content + goals |
| `/customers` | Customers | P2: Customer | Buyers, marketing | View data | Weekly | harris_farm.db (customers, sales) |
| `/market-share` | Market Share | P2: Customer | Execs, strategy | View data | Weekly | harris_farm.db (market_share, CBAS) |
| `/learning-centre` | Learning Centre | P3: People | All staff | Learn | Weekly | Static lessons + hub_data.db |
| `/the-paddock` | The Paddock | P3: People | All staff | Learn / Practice | Weekly | Static questions + session state |
| `/hub-assistant` | Hub Assistant | P3: People | All staff | Ask questions | Daily | LLM API + harris_farm.db |
| `/ai-adoption` | AI Adoption | P3: People | Execs, L&D team | View metrics | Monthly | hub_data.db (usage stats) |
| `/academy` | Academy | P3: People | All staff | Learn / Track | Weekly | hub_data.db (progress) |
| `/sales` | Sales | P4: Operations | Store managers, buyers | View data | Daily | harris_farm.db (sales) |
| `/profitability` | Profitability | P4: Operations | Finance, buyers | View data | Weekly | harris_farm.db (sales, GP) |
| `/transport` | Transport | P4: Operations | Logistics team | View data | Weekly | Static/manual data |
| `/store-ops` | Store Ops | P4: Operations | Store managers | View data | Daily | Transaction parquets (DuckDB) |
| `/buying-hub` | Buying Hub | P4: Operations | Buyers | View data + Plan | Daily | Transaction parquets + weather API |
| `/product-intel` | Product Intel | P4: Operations | Buyers, category mgrs | View data | Weekly | Transaction parquets |
| `/plu-intel` | PLU Intelligence | P4: Operations | Store managers, buyers | View data | Weekly | harris_farm_plu.db (27M rows) |
| `/revenue-bridge` | Revenue Bridge | **P5: Digital & AI** | Finance, execs | View data | Weekly | Transaction parquets (383M rows) |
| `/prompt-builder` | Prompt Builder | **P5: Digital & AI** | All staff (super users) | Create / Build | Weekly | hub_data.db (templates) |
| `/the-rubric` | The Rubric | P5: Digital & AI | AI team, power users | Test / Compare | Monthly | LLM APIs |
| `/trending` | Trending | P5: Digital & AI | Admin, AI team | Monitor platform | Weekly | hub_data.db (usage, feedback) |
| `/mission-control` | Mission Control | P5: Digital & AI | Admin, AI team | Browse docs | Monthly | hub_data.db (docs, catalog) |
| `/agent-hub` | Agent Hub | P5: Digital & AI | Admin, AI team | Monitor agents | Weekly | hub_data.db (proposals, scores) |
| `/analytics-engine` | Analytics Engine | P5: Digital & AI | Analysts, AI team | Run analyses | Weekly | hub_data.db + harris_farm.db |
| `/agent-ops` | Agent Operations | P5: Digital & AI | Admin only | Control agents | Weekly | hub_data.db (WATCHDOG, tasks) |

---

## Table 2: Misplacement Flags

| Page | Current Location | Problem | Recommended Location | Severity |
|------|-----------------|---------|---------------------|----------|
| **Revenue Bridge** | P5: Digital & AI | Revenue decomposition dashboard using real POS transaction data (383M rows). Same data layer, same users (finance/execs), same action type (view data) as Sales and Profitability. It's a financial analytics tool, not a technology/AI page. Users looking for revenue analysis will never think to check "Tomorrow's Business, Built Better". | **P4: Operations** (next to Sales & Profitability) | **HIGH** |
| **Prompt Builder** | P5: Digital & AI | User-facing creation tool ("Super User Tool") for building analytical prompts. Primary users are store managers and analysts learning to work with AI — the same audience as Learning Centre, Academy, and The Paddock. Grouping it with admin infrastructure (Agent Ops, Mission Control) hides it from its target users. | **P3: People** (next to Learning Centre & Academy) | **HIGH** |
| **AI Adoption** | P3: People | Platform usage metrics (how many users, which features, engagement trends). This is an admin/measurement dashboard, not a learning tool. Store managers visiting "Growing Legendary Leadership" to learn AI skills don't need to see platform analytics. Its real audience is the AI team and execs tracking rollout success. | **P5: Digital & AI** (with Trending, as platform health) | **MEDIUM** |
| **The Rubric** | P5: Digital & AI | Side-by-side LLM model comparison tool. Power users and the AI team use it, but it's fundamentally a learning/evaluation tool — "which model is best for my use case?" It fits better with the AI toolkit alongside Prompt Builder. If Prompt Builder moves to People, The Rubric should follow. | **P3: People** (with Prompt Builder as AI toolkit) | **MEDIUM** |
| **Hub Assistant** | P3: People | AI chatbot that answers data questions using harris_farm.db. It's a data access tool more than a learning tool. Users asking "what were Bondi sales last week?" are doing operational work, not learning. However, it also serves as an AI onboarding tool ("try asking AI a question"). Dual purpose — acceptable in either location. | **Acceptable in P3** (keep, but could also fit P4) | **LOW** |
| **Trending** | P5: Digital & AI | System analytics about the Hub platform itself (usage patterns, LLM performance, feedback). Mixed in with 7 other pages including user-facing tools. Should be clearly grouped with other admin/governance pages, not adjacent to user tools. | **Keep in P5** but group with admin pages | **LOW** |

### Summary of P5 Overload Problem

"Tomorrow's Business, Built Better" currently has **8 pages** — the most of any pillar. It mixes three fundamentally different audiences:

1. **User-facing tools** (Prompt Builder, The Rubric) — for all staff learning AI
2. **Financial analytics** (Revenue Bridge) — for finance/ops teams viewing data
3. **Admin/governance** (Trending, Mission Control, Agent Hub, Analytics Engine, Agent Ops) — for the AI team managing the platform

No single user needs all 8. A store manager looking for Prompt Builder has to scroll past Agent Operations. An exec looking for Revenue Bridge is searching a "Digital & AI" section. This is the #1 navigation UX issue.

---

## Table 3: Proposed Navigation Structure

```
Harris Farm Hub
│
├── Home (/)
│
├── P1: For The Greater Goodness
│   └── Greater Goodness          — Purpose, sustainability, community
│
├── P2: Smashing It for the Customer
│   ├── Customers                 — Customer insights, trends, loyalty
│   └── Market Share              — Postcode share, penetration, benchmarks
│
├── P3: Growing Legendary Leadership
│   ├── Learning Centre           — AI & data skills courses
│   ├── The Paddock               — Practice AI conversations
│   ├── Academy                   — Capability journey (Seed → Legend)
│   ├── Prompt Builder            — Build analytical prompts  ← MOVED FROM P5
│   ├── The Rubric                — Compare AI models         ← MOVED FROM P5
│   └── Hub Assistant             — Ask questions, get answers
│
├── P4: Today's Business, Done Better
│   ├── Sales                     — Revenue, store performance
│   ├── Profitability             — GP analysis, margins
│   ├── Revenue Bridge            — Revenue decomposition     ← MOVED FROM P5
│   ├── Store Ops                 — Transaction intelligence
│   ├── Buying Hub                — Category buying, demand
│   ├── Product Intel             — Item & category performance
│   ├── PLU Intelligence          — PLU wastage, shrinkage
│   └── Transport                 — Route costs, fleet
│
├── P5: Tomorrow's Business, Built Better
│   ├── Analytics Engine          — Run data intelligence analyses
│   ├── Agent Hub                 — Scoreboard, Arena, Agent Network
│   ├── Agent Operations          — WATCHDOG safety & agent control
│   ├── AI Adoption               — Platform usage metrics    ← MOVED FROM P3
│   ├── Trending                  — System analytics & health
│   └── Mission Control           — Documentation & data catalog
```

### What Changed

| Move | From | To | Rationale |
|------|------|----|-----------|
| Revenue Bridge | P5 (8 pages) | P4 (8 pages) | Financial data belongs with financial dashboards |
| Prompt Builder | P5 (8 pages) | P3 (6 pages) | User creation tool belongs with learning journey |
| The Rubric | P5 (8 pages) | P3 (6 pages) | AI evaluation tool belongs with AI toolkit |
| AI Adoption | P3 (5 pages) | P5 (6 pages) | Platform metrics belong with platform admin |

### Result

| Pillar | Before | After | Change |
|--------|--------|-------|--------|
| P1: Greater Goodness | 1 | 1 | — |
| P2: Customer | 2 | 2 | — |
| P3: People | 5 | 6 | +Prompt Builder, +The Rubric, -AI Adoption |
| P4: Operations | 7 | 8 | +Revenue Bridge |
| P5: Digital & AI | **8** | **6** | -Revenue Bridge, -Prompt Builder, -The Rubric, +AI Adoption |

P5 drops from 8 → 6 pages. Every page in P5 is now genuinely about platform infrastructure and AI governance. P3 becomes the complete "AI toolkit" for Harris Farmers learning and using AI. P4 gets its missing financial analytics dashboard back alongside Sales and Profitability where users expect it.

---

## Table 4: Quick Wins (Top 5)

These are the highest-impact changes requiring the least code. Each is a configuration change in `app.py` — no dashboard code changes needed.

| # | Change | Files Modified | Lines Changed | Impact |
|---|--------|---------------|---------------|--------|
| 1 | **Move Revenue Bridge to P4** | `app.py` (move slug in `_PILLARS` and `st.navigation`), `nav.py` (move to Operations hub) | ~6 lines | Finance users find revenue analysis where they expect it — next to Sales and Profitability |
| 2 | **Move Prompt Builder to P3** | `app.py` (move slug in `_PILLARS` and `st.navigation`) | ~4 lines | Store managers discover the prompt tool alongside their learning journey, not buried in admin |
| 3 | **Move The Rubric to P3** | `app.py` (move slug in `_PILLARS` and `st.navigation`) | ~4 lines | Keeps the AI toolkit together — learn, practise, build prompts, compare models |
| 4 | **Move AI Adoption to P5** | `app.py` (move slug in `_PILLARS` and `st.navigation`) | ~4 lines | Platform metrics sit with platform monitoring (Trending), not with learning content |
| 5 | **Reorder P4 pages** — put Revenue Bridge after Profitability | `app.py` (reorder within slugs list and navigation dict) | ~2 lines | Natural flow: Sales → Profitability → Revenue Bridge (big picture → detail → decomposition) |

### Implementation Note

All 5 quick wins modify only `dashboards/app.py` — specifically the `_PILLARS` list (lines 73-84) and the `st.navigation()` dict (lines 90-99). No dashboard files need changes. No API changes. No session state changes. The `nav.py` file should also be updated for consistency, and `goals_config.py` page-to-goal mappings remain correct regardless of pillar placement.

Total estimated diff: ~20 lines changed in `app.py`, ~10 lines in `nav.py`.

---

## Appendix: Page Classification Matrix

### By Action Type
| Action | Pages |
|--------|-------|
| **View Data** (read-only dashboards) | Sales, Profitability, Revenue Bridge, Store Ops, Buying Hub, Product Intel, PLU Intel, Customers, Market Share, Transport, Greater Goodness |
| **Learn / Practice** | Learning Centre, The Paddock, Academy |
| **Create / Build** | Prompt Builder, The Rubric, Hub Assistant, Analytics Engine |
| **Monitor / Govern** | Trending, AI Adoption, Mission Control, Agent Hub, Agent Ops |

### By Audience
| Audience | Pages |
|----------|-------|
| **All staff** | Home, Hub Assistant, Learning Centre, The Paddock, Academy, Prompt Builder |
| **Store managers** | Sales, Store Ops, PLU Intel, Buying Hub |
| **Buyers / Category** | Sales, Profitability, Buying Hub, Product Intel, PLU Intel |
| **Finance / Execs** | Sales, Profitability, Revenue Bridge, Customers, Market Share, Greater Goodness |
| **AI team / Admin** | Trending, AI Adoption, Mission Control, Agent Hub, Analytics Engine, Agent Ops, The Rubric |

### By Data Layer
| Layer | Pages |
|-------|-------|
| **Layer 1 — POS/Transaction** | Sales, Profitability, Revenue Bridge, Store Ops, Buying Hub, Product Intel, PLU Intel |
| **Layer 2 — CBAS Market Share** | Market Share |
| **Layer 3 — Customer** | Customers |
| **App State — hub_data.db** | All P3 + P5 pages, Home |
| **No data / Static** | Greater Goodness, Transport, The Paddock (questions only) |
