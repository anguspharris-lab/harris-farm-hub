# Harris Farm Hub — Centre of Excellence Redesign
## Board Presentation | February 2026

**Prepared for:** Angus Harris, Luke Harris, Darren Weir, Laura Durkan, Phil Cribb
**Prepared by:** AI Centre of Excellence Team
**Status:** For Board Approval

---

## 1. EXECUTIVE SUMMARY

The Hub is Harris Farm's flagship AI Centre of Excellence — a CRITICAL Pillar 5 initiative. This redesign transforms it from a technical analytics platform into a **strategy-aligned, purpose-led, people-first** tool that serves every pillar of "Fewer, Bigger, Better."

**What changes:**
- Navigation reorganised around our 5 strategic pillars (not technical categories)
- Harris Farm brand identity throughout (green #4ba021, "For The Greater Goodness")
- Prosci ADKAR change management woven into the Learning Centre
- Supply chain tools directly supporting Pillar 4 buying and waste targets
- Clear "LIVE / FUTURE DEVELOPMENT" markers on every feature
- Self-improving system with human-in-the-loop governance

**What stays:**
- All 16 existing dashboards and their functionality
- 93+ API endpoints, 383.6M transaction data engine
- WATCHDOG safety governance (7 Laws)
- 1,003 automated tests
- Autonomous development pipeline

**Core philosophy:** *Enablement, not replacement. Augmentation, not automation.*

---

## 2. STAKEHOLDER CONSULTATION

### Laura Durkan — Head of People (Pillars 3 & 5)

**Key requirements:**
- Learning Centre must follow Prosci ADKAR progression (Awareness → Desire → Knowledge → Ability → Reinforcement)
- AI training must feel safe — every screen communicates "AI is your job partner"
- Clear pathways: Beginner → Intermediate → Advanced → Citizen Developer
- Support for Top 100 Development Day (Mar 12 2026) preparation
- Legendary Leadership content integrated — leaders model AI adoption
- "Every Harris Farm Job Is a Customer Job" — AI helps people do their best work

**Design response:**
- Learning Centre restructured around ADKAR stages
- Every dashboard includes a "How AI helps your role" contextual guide
- Citizen Developer pathway with badges and progression tracking
- Change management messaging embedded in onboarding flow
- Safe, encouraging tone throughout: "Try it — we'll help you get better"

### Supply Chain & Buying Team (Pillar 4)

**Key requirements:**
- Buying automation with demand forecasting (active initiative)
- OOS reduction by 20% target (by Jun 2026)
- Weather-driven ordering adjustments
- Transport cost optimisation and Greystanes DC efficiency
- Supplier relationship visibility
- Process mapping: Procure → Pay → Sell visibility

**Design response:**
- Buying Hub dashboard enhanced with weather impact forecasts
- OOS tracking with target progress (20% reduction gauge)
- Transport dashboard linked to supply chain KPIs
- Product intel showing range refresh progress and category performance
- Wastage dashboard aligned to sustainability targets

### Angus Harris — Co-CEO (Pillar 5 Lead)

**Key requirements:**
- The Hub IS the AI Centre of Excellence (Pillar 5, Outcome 2)
- Must demonstrate progress to the Board and Top 100
- Self-improving autonomous system with safety guardrails
- Data Insights Hub — democratised data access for all departments
- Citizen Developer Program platform
- Integration pathway to Microsoft Fabric

**Design response:**
- Strategy alignment dashboard showing Hub impact across all 5 pillars
- Self-improvement metrics visible in Hub Portal
- Fabric migration readiness indicators
- Autonomous agent pipeline with WATCHDOG governance
- Pillar 5 progress tracker built into landing page

### Luke Harris — Co-CEO (Pillars 2 & 5)

**Key requirements:**
- Customer experience and loyalty program readiness
- Brand integrity in all outputs — "For The Greater Goodness"
- Growth analytics supporting path to 50 stores
- Amazon Fresh partnership analytics integration
- Voice of Customer data infrastructure

**Design response:**
- Customer dashboard enhanced with loyalty-ready analytics
- Market share dashboard supporting store network expansion planning
- Brand-consistent design across every screen
- Customer identification rate tracking (currently 12.5%)
- VoC data collection framework in analytics pipeline

---

## 3. REDESIGN ARCHITECTURE

### 3.1 Brand Identity

| Element | Current | Redesigned |
|---------|---------|------------|
| Primary colour | #1e3a8a (dark blue) | #4ba021 (Harris Farm green) |
| Secondary colour | #10b981 (teal) | #a2d3f1 (light blue) |
| Accent | #ef4444 (red) | #d97706 (warm amber) |
| Alert/negative | #ef4444 | #ef4444 (unchanged) |
| Background | #f0f2f6 (grey) | #f5f5f5 (warm white) |
| Text | Various | #171819 (consistent dark) |
| Font feel | Technical | Warm, approachable (DM Sans-inspired) |
| Tagline | "AI Centre of Excellence" | "For The Greater Goodness — AI Centre of Excellence" |
| Tone | Technical/analytical | Friendly, purpose-led, encouraging |

### 3.2 Navigation — Pillar-Aligned

**Current structure (technical):**
```
Financial Hub → Market Intel → Operations → Transactions → Learning
```

**Redesigned structure (strategy-aligned):**

```
HOME — Harris Farm Hub
  |
  |— GREATER GOODNESS (Pillar 1)
  |     Sustainability metrics, B-Corp progress, wastage reduction
  |
  |— CUSTOMER INTELLIGENCE (Pillar 2)
  |     Customer Dashboard, Market Share, Loyalty readiness
  |
  |— PEOPLE & LEADERSHIP (Pillar 3)
  |     Learning Centre, Prompt Academy, ADKAR Progress, Hub Assistant
  |
  |— OPERATIONS EXCELLENCE (Pillar 4)
  |     Sales, Profitability, Transport, Store Ops, Buying Hub, Product Intel
  |
  |— DIGITAL & AI (Pillar 5)
  |     Prompt Builder, The Rubric, Trending, Hub Portal, Revenue Bridge, Agent Network
  |
  |— STRATEGY TRACKER
        Pillar progress, initiative status, KPI scorecards
```

### 3.3 Dashboard-to-Pillar Mapping

| Dashboard | Port | Primary Pillar | Secondary |
|-----------|------|---------------|-----------|
| Landing (Home) | 8500 | All | — |
| Sales | 8501 | P4 Operations | P2 Customer |
| Profitability | 8502 | P4 Operations | P1 Sustainability |
| Transport | 8503 | P4 Operations | P1 Supply Chain |
| Prompt Builder | 8504 | P5 Digital & AI | P3 Learning |
| Rubric | 8505 | P5 Digital & AI | — |
| Trending | 8506 | P5 Digital & AI | — |
| Customer | 8507 | P2 Customer | — |
| Market Share | 8508 | P2 Customer | P4 Growth |
| Hub Assistant | 8509 | P3 People | P5 AI |
| Learning Centre | 8510 | P3 People | P5 AI |
| Store Ops | 8511 | P4 Operations | — |
| Product Intel | 8512 | P4 Operations | P4 Buying |
| Revenue Bridge | 8513 | P5 Digital & AI | P4 Finance |
| Buying Hub | 8514 | P4 Operations | P4 Supply Chain |
| Hub Portal | 8515 | P5 Digital & AI | All |

---

## 4. LEARNING CENTRE — PROSCI ADKAR REDESIGN

### Current State
5 tabs: My Dashboard, AI Prompting Skills, Data Prompting, Company Knowledge, Practice Lab

### Redesigned — ADKAR Journey

**Stage 1: AWARENESS** (Why AI matters at Harris Farm)
- Harris Farm's AI vision — "AI as a Job Partner" (Pillar 5.3)
- What the Hub does and how it helps YOUR role
- Greater Goodness connection — AI helps us serve customers better
- "This is about enablement, not taking people's jobs"
- Video/text from Angus & Luke on the AI vision

**Stage 2: DESIRE** (I want to learn this)
- Success stories from early adopters
- Role-specific benefits (buyer saves 2hrs/week, store manager catches OOS faster)
- The Prompt Academy pathway — clear progression with badges
- "Every Harris Farm job is a customer job — AI helps you do it better"

**Stage 3: KNOWLEDGE** (How to use AI tools)
- Core AI Skills (L1-L4) — existing content, reframed
- 5 Building Blocks: Role, Context, Task, Format, Constraints
- Harris Farm data skills (D1-D4) — existing content
- Company knowledge (K1-K4) — existing content
- Practice Lab with coaching

**Stage 4: ABILITY** (I can do it myself)
- Citizen Developer challenges
- Real-world scenarios by department
- The Rubric — compare AI responses, develop judgment
- Build your own prompts with Prompt Builder
- Department-specific templates

**Stage 5: REINFORCEMENT** (Keep improving)
- Progress tracking dashboard
- Badges and achievements
- Leaderboard (optional, gamified)
- Self-improvement suggestions
- Peer learning — share prompts that worked
- Monthly AI tips from the CoE

### 5-Level Prompt Academy Curriculum

| Level | Name | Audience | Content |
|-------|------|----------|---------|
| 1 | AI Explorer | Everyone | What is AI, basic prompting, 5 building blocks |
| 2 | Prompt Practitioner | Regular users | Advanced techniques, chain-of-thought, few-shot |
| 3 | Data Navigator | Analysts/buyers | HFM data queries, dashboard interpretation, intelligence system |
| 4 | AI Champion | Power users | Multi-LLM comparison, template creation, department workflows |
| 5 | Citizen Developer | Innovators | Build automations, create agents, vibe coding basics |

---

## 5. SECURITY ROADMAP

**For: Swechchha Boki Shrestha (Head of IT) & Phil Cribb (CTO)**

### Current State
- No authentication (ADR-005, MVP decision)
- CORS allows all origins
- Internal network access only
- WATCHDOG governance for AI safety
- Pre-commit hooks block credential leaks

### Phase 1 — Immediate (Feb-Mar 2026)
- [ ] RBAC enforcement (admin/operator/analyst/viewer roles)
- [ ] Session-based authentication with secure tokens
- [ ] API rate limiting
- [ ] Input validation on all 93+ endpoints
- [ ] HTTPS enforcement

### Phase 2 — Q3 FY26 (Apr-Jun 2026)
- [ ] Azure AD / SSO integration
- [ ] Role-based dashboard access (department-specific views)
- [ ] Audit trail for data access (who queried what, when)
- [ ] Encrypted data at rest (SQLite → encrypted SQLite)
- [ ] Network segmentation (Hub on dedicated VLAN)

### Phase 3 — FY27 (Jul 2026+)
- [ ] SOC 2 Type I readiness
- [ ] Penetration testing
- [ ] Data classification (PII handling for loyalty data)
- [ ] Multi-factor authentication
- [ ] Automated vulnerability scanning in CI/CD

---

## 6. MICROSOFT FABRIC INTEGRATION STRATEGY

**For: Leonard Rawat (IT/Data), Phil Cribb (CTO)**

### Current Architecture
```
Parquet files (6.6GB) → DuckDB (in-memory) → FastAPI → Dashboards
```

### Target Architecture (Fabric)
```
Source Systems → Fabric Lakehouse → Fabric Warehouse → Power BI / Hub Dashboards
```

### Migration Path
1. **Phase 1 (Current):** Hub reads Parquet files directly via DuckDB — works today
2. **Phase 2 (Fabric Ready):** Hub gains API adapter layer — can switch data source without dashboard changes
3. **Phase 3 (Fabric Live):** Hub reads from Fabric Warehouse/Lakehouse endpoints — same dashboards, enterprise data
4. **Phase 4 (Hybrid):** Hub + Power BI coexist — Hub for AI/NL queries, Power BI for standard reporting

### Hub Preparation
- Abstract data access layer already exists (`dashboards/shared/data_access.py`)
- Add Fabric connector module (swap DuckDB for Fabric SQL endpoint)
- Maintain backward compatibility (Parquet fallback if Fabric unavailable)
- Zero dashboard code changes required

---

## 7. SELF-IMPROVING AUTONOMOUS SYSTEM

### Architecture
```
Human Question → AI Agent Proposes Analysis → WATCHDOG Safety Check
→ Human Approves → Execute Against 383.6M Transactions
→ Score (H/R/S/C/D/U/X) → Store Report → Learn
→ Every 5 tasks → Self-Improvement Engine → Propose Enhancement
→ Max 3 Attempts per Criterion → Escalate if stuck
```

### Guardrails
- **7 WATCHDOG Laws** — immutable, verified by SHA-256 checksum every session
- **Operator Authority** — Gus Harris sole approver for system changes
- **Data Correctness** — every number traceable to source ±0.01
- **Full Audit Trail** — append-only log, no deletions
- **Emergency Shutdown** — kills all services, preserves evidence

### Human-in-the-Loop
- AI proposes, never acts autonomously on real data
- Every analysis requires human review before publishing
- Chairman's Decision system for multi-LLM outputs
- Self-improvement proposals require operator approval before deployment

---

## 8. FEATURE STATUS — LIVE vs FUTURE DEVELOPMENT

### LIVE (Built and Working)
- 16 Streamlit dashboards with data visualisation
- FastAPI backend (93+ endpoints)
- Natural language → SQL query engine
- The Rubric (multi-LLM comparison)
- Prompt Builder with template library
- Learning Centre (12 modules, 15 practice challenges)
- WATCHDOG governance framework
- Agent routing and proposal system
- Self-improvement scoring engine
- 1,003 automated tests
- Weather demand forecasting system

### FUTURE DEVELOPMENT (Planned, Not Yet Operational)
- Real database connection (currently using intelligently-seeded mock data)
- Azure AD authentication
- Autonomous agent execution (requires operator approval flow)
- Advanced ML models (demand forecasting, dynamic pricing)
- Real-time alerts (OOS, wastage anomalies)
- Voice interface for buyers
- Mobile-optimised views
- Supplier portal integration
- Loyalty program analytics (awaiting program launch)
- Power BI / Fabric integration
- A/B testing framework for agents
- PDF/HTML report export

---

## 9. IMPLEMENTATION APPROACH

### What We're Implementing Now
1. **Brand overhaul** — Harris Farm green, "Greater Goodness" messaging, warm tone
2. **Navigation restructure** — 5-pillar organisation
3. **Landing page redesign** — Strategy-aligned home with pillar navigation
4. **Learning Centre ADKAR framing** — Prosci stages in the learning journey
5. **Consistent "LIVE / Future" labelling** — Clear on every feature
6. **Harris Farm history and values** — Woven into Company Knowledge section
7. **Change management messaging** — Safe, encouraging AI adoption language

### What We Preserve
- All 16 dashboard codebases
- All 93+ API endpoints
- WATCHDOG governance
- Agent and self-improvement systems
- Test suite (1,003 tests)
- Autonomous development pipeline

---

## 10. BOARD RECOMMENDATION

**Motion:** Approve the Hub redesign to align with our "Fewer, Bigger, Better" strategy, incorporating:
1. Harris Farm brand identity throughout
2. 5-pillar navigation structure
3. Prosci ADKAR learning journey
4. Clear LIVE vs Future Development labelling
5. Security and Fabric integration roadmaps

**Investment:** Engineering effort only (no additional spend required — built with existing AI tools)

**Timeline:** Immediate implementation, iterative refinement through Jun 2026

**Success Metrics:**
- Top 100 AI training participation rate (target: 80% by Jun 2026)
- Hub usage: queries/day, active users/week
- OOS reduction progress toward 20% target
- Prompt Academy completion rates by level
- User satisfaction scores (target: 7+/10)

---

*For The Greater Goodness — Harris Farm Hub, Centre of Excellence*
*Family owned since '71. AI-powered since '26.*
