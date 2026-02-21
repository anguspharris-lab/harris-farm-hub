# The 5 Goals of Harris Farm Hub

**Why The Hub Exists**

These five goals define the purpose of every dashboard, every agent, and every line of code in the Hub.

---

## G1: Bring Strategy to Life

**Color:** `#2d8659` | **Icon:** Pin | **Pillars:** P1, P2, P4, P5

Make Harris Farm's "Fewer, Bigger, Better" strategy visible, measurable, and actionable through live dashboards and intelligence reports.

**Key Question:** Can any Harris Farmer see how their work connects to the strategy?

**Tracked via:** Intelligence reports generated, strategic proposals implemented.

**Pages:** Greater Goodness, Customers, Market Share, Sales, Profitability, Revenue Bridge, Mission Control, Agent Hub, Agent Operations

---

## G2: Democratise Data

**Color:** `#3b82f6` | **Icon:** Chart | **Pillars:** P2, P4, P5

Put data into the hands of every Harris Farmer -- from store managers checking weekend sales to buyers optimising orders with weather forecasts.

**Key Question:** Can a store manager answer their own data question without IT help?

**Tracked via:** Unique data users, queries generated.

**Pages:** Customers, Market Share, Hub Assistant, Sales, Profitability, Store Ops, Buying Hub, Product Intel, PLU Intel, Prompt Builder, Revenue Bridge

---

## G3: Train Our Superstars

**Color:** `#a855f7` | **Icon:** Star | **Pillars:** P3, P5

Build AI capability across the business -- from Seed to Legend. Every Harris Farmer should feel confident using AI as a job partner, not a replacement.

**Key Question:** Is every team member growing their AI skills at their own pace?

**Tracked via:** Learning paths started, prompts practised.

**Pages:** Learning Centre, Hub Assistant, Academy, AI Adoption, Prompt Builder, The Rubric

---

## G4: Fast-Track Supply Chain

**Color:** `#f59e0b` | **Icon:** Truck | **Pillars:** P4

Use AI to tidy up the supply chain from pay to purchase -- reduce out-of-stocks, optimise buying, and get Grant Enders' vision into the data.

**Key Question:** Are we reducing waste and out-of-stocks measurably, week on week?

**Tracked via:** Operations agent proposals, supply chain analyses run.

**Pages:** Sales, Profitability, Transport, Store Ops, Buying Hub, Product Intel, PLU Intel

---

## G5: Always Improve

**Color:** `#ef4444` | **Icon:** Cycle | **Pillars:** P5

The Hub watches itself. WATCHDOG governance, self-improvement cycles, and continuous quality scoring ensure we get better every iteration.

**Key Question:** Is The Hub measurably better this week than last week?

**Tracked via:** Improvement findings actioned, average quality score.

**Pages:** AI Adoption, The Rubric, Trending, Mission Control, Agent Hub, Agent Operations

---

## How Goals Appear in the UI

1. **Front Page (Mission Control):** 5 goal cards with live progress bars and metrics
2. **Goal Badges:** Inline colored badges (`goal_badge_html`) on landing, academy, and content
3. **Academy:** Learning paths and arena challenges tagged to goals
4. **Activity Feed:** Each activity item shows which goals it serves

## How Goals Connect to Pillars

| Pillar | Goals Served |
|--------|-------------|
| P1: Greater Goodness | G1 |
| P2: Customer | G1, G2 |
| P3: People | G3 |
| P4: Operations | G1, G2, G4 |
| P5: Digital & AI | G1, G2, G3, G5 |

## Source Code

- `dashboards/shared/goals_config.py` -- HUB_GOALS dict, GOAL_PAGE_MAPPING, utility functions
- `dashboards/landing.py` -- Mission Control renders goals with live metrics
