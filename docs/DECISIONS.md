# Harris Farm Hub — Architecture Decision Records

> Append-only log. Every significant technical or design choice is recorded here with context, options considered, and rationale.

---

## ADR-001: Streamlit for Dashboard Framework

**Date:** 13 Feb 2026
**Status:** Accepted
**Context:** Need interactive dashboards that the finance team can use immediately. Budget: one weekend.

**Options Considered:**
1. **Streamlit** — Python-native, rapid prototyping, built-in widgets
2. **React + Recharts** — More polished UI, but requires JS expertise and longer build time
3. **Dash (Plotly)** — Python-based like Streamlit, more customisable but steeper learning curve
4. **Power BI / Tableau** — Enterprise tools, but licensing cost and less AI integration

**Decision:** Streamlit. Ship speed trumps polish for MVP. React frontend is scaffolded (`/frontend`) for future migration.

**Consequences:** Limited customisation (no shared nav between apps), desktop-first responsive design, each dashboard is a separate process.

---

## ADR-002: SQLite for Hub Metadata

**Date:** 13 Feb 2026
**Status:** Accepted
**Context:** Need to store query history, LLM responses, feedback, and prompt templates.

**Options:** PostgreSQL, SQLite, Redis, DynamoDB
**Decision:** SQLite. Zero configuration, embedded in the app, sufficient for single-server deployment.

**Consequences:** Not suitable for multi-server deployment. Will migrate to PostgreSQL when scaling beyond single machine.

---

## ADR-003: Mock Data for MVP Dashboards

**Date:** 13 Feb 2026
**Status:** Accepted
**Context:** Real database connection requires credentials, VPN, and data governance approval.

**Decision:** Generate realistic mock data using numpy random distributions on every dashboard load, cached with `@st.cache_data`. Dashboards are fully functional without any external dependencies.

**Consequences:** Data is not real — user must understand this. Random seed not fixed, so data changes per session. Real DB integration is a separate deployment step.

---

## ADR-004: Monolithic Backend (Single app.py)

**Date:** 13 Feb 2026
**Status:** Accepted
**Context:** All backend logic (API routes, Rubric evaluator, Query generator, DB init) in one 776-line file.

**Decision:** Keep monolithic for MVP. Split into modules when any single concern exceeds ~300 lines or when a second developer joins.

**Consequences:** Easy to understand and deploy. Will need refactoring before adding auth, scheduled tasks, or webhooks.

---

## ADR-005: No Authentication for MVP

**Date:** 13 Feb 2026
**Status:** Accepted (temporary)
**Context:** MVP runs on localhost/internal network only.

**Decision:** Skip auth for v1. CORS allows all origins. Plan Azure AD integration for production.

**Consequences:** Not suitable for public deployment. Anyone on the network can access all endpoints.

---

## ADR-006: Multi-LLM via Direct API Calls

**Date:** 13 Feb 2026
**Status:** Accepted
**Context:** The Rubric needs to query Claude, ChatGPT, and Grok simultaneously.

**Options:** LangChain orchestration, direct API calls, custom abstraction
**Decision:** Direct API calls with asyncio.gather for parallel execution. Simple, no framework dependency.

**Consequences:** Each provider needs its own client code. Adding a new LLM means writing a new `query_*` method.

---

## ADR-007: Remove pymssql from Dependencies

**Date:** 13 Feb 2026
**Status:** Accepted
**Context:** pymssql requires FreeTDS C library compilation, which fails on macOS without brew install.

**Decision:** Comment out pymssql from requirements.txt. Only needed if connecting to SQL Server (Harris Farm uses PostgreSQL).

**Consequences:** SQL Server connections not available out of the box. Re-add if needed with `brew install freetds` first.

---

## ADR-008: Fix pd.np Deprecation in Sales Dashboard

**Date:** 13 Feb 2026
**Status:** Accepted
**Context:** `pd.np.random` removed in pandas 2.x. Sales dashboard crashed on load.

**Decision:** Replace `pd.np.random` with direct `import numpy as np` and `np.random` calls.

**Consequences:** Dashboard loads correctly on pandas 2.1.3+.
