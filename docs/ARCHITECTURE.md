# Harris Farm Hub — Architecture

*Last Updated: 2026-02-22 (v3.1 — IA Restructure)*

---

## System Overview

```
                    Browser (any device)
                           |
                           v
         ┌─────────────────────────────────────┐
         │     Streamlit Multi-Page App        │
         │     dashboards/app.py               │
         │     (single process, one port)      │
         │                                     │
         │  ┌─────────────────────────────┐    │
         │  │ Auth Gate (require_login)   │    │
         │  │ Session persists across all │    │
         │  │ pages via st.session_state  │    │
         │  └─────────────────────────────┘    │
         │                                     │
         │  ┌─────────────────────────────┐    │
         │  │ st.navigation() router      │    │
         │  │ 23 pages across 5 pillars   │    │
         │  └─────────────────────────────┘    │
         │                                     │
         │  Shared: styles, fiscal selector,   │
         │  hierarchy filter, ask_question     │
         └──────────────┬──────────────────────┘
                        │ HTTP (localhost:8000)
                        v
         ┌─────────────────────────────────────┐
         │     FastAPI Backend                 │
         │     backend/app.py (112 endpoints)   │
         │                                     │
         │  Auth    NL Query   Multi-LLM       │
         │  Agent Executor   Self-Improvement  │
         └──────┬──────────────┬───────────────┘
                │              │
       ┌────────┘              └────────┐
       v                                v
┌──────────────┐              ┌─────────────────┐
│ SQLite       │              │ DuckDB          │
│              │              │ (in-process)    │
│ harris_farm  │              │ 383M txns       │
│ .db (399MB)  │              │ via parquet     │
│ hub_data.db  │              │ FY24/25/26      │
└──────────────┘              └─────────────────┘
```

---

## Key Change: Single App Architecture

**Before (v2):** 17 separate Streamlit processes on ports 8500-8516, connected by HTML links. Each process ~50MB RAM, navigation caused full page reloads, session state lost between dashboards.

**After (v3):** One `st.navigation()` app on a single port. One process, shared session state, native sidebar navigation. Login once, navigate everywhere.

### What this means

- **One process** instead of 17 (~85% memory reduction)
- **One port** (8500 local, $PORT on Render)
- **Shared session state** — login persists across all pages
- **`st.page_link()`** for navigation (no page reloads)
- **`app.py`** is the only file that calls `set_page_config()`, `require_login()`, and `apply_styles()`

---

## Pages by Pillar

### For The Greater Goodness
| Page | File | Data Source |
|------|------|------------|
| Greater Goodness | `greater_goodness.py` | Static content |

### Smashing It for the Customer
| Page | File | Data Source |
|------|------|------------|
| Customers | `customer_dashboard.py` | Transactions (DuckDB) |
| Market Share | `market_share_dashboard.py` | harris_farm.db |

### Growing Legendary Leadership
| Page | File | Data Source |
|------|------|------------|
| Learning Centre | `learning_centre.py` | 12 modules, API |
| The Paddock | `the_paddock.py` | Practice AI conversations |
| Academy | `growing_legends_academy.py` | Capability journey (hub_data.db) |
| Prompt Builder | `prompt_builder.py` | API (templates) |
| The Rubric | `rubric_dashboard.py` | API (multi-LLM) |
| Hub Assistant | `chatbot_dashboard.py` | Knowledge base (API) |

### Today's Business, Done Better
| Page | File | Data Source |
|------|------|------------|
| Sales | `sales_dashboard.py` | harris_farm.db |
| Profitability | `profitability_dashboard.py` | harris_farm.db |
| Revenue Bridge | `revenue_bridge_dashboard.py` | Transactions (DuckDB) |
| Store Ops | `store_ops_dashboard.py` | Transactions (DuckDB) |
| Buying Hub | `buying_hub_dashboard.py` | Transactions (DuckDB) |
| Product Intel | `product_intel_dashboard.py` | Transactions (DuckDB) |
| PLU Intelligence | `plu_intel_dashboard.py` | harris_farm_plu.db |
| Transport | `transport_dashboard.py` | harris_farm.db |

### Tomorrow's Business, Built Better
| Page | File | Data Source |
|------|------|------------|
| Analytics Engine | `analytics_engine.py` | Data Intelligence (hub_data.db + harris_farm.db) |
| Agent Hub | `agent_hub.py` | Scoreboard, Arena, Agent Network (hub_data.db) |
| Agent Operations | `agent_operations.py` | WATCHDOG safety & agent control (hub_data.db) |
| AI Adoption | `ai_adoption/dashboard.py` | Platform usage metrics (hub_data.db) |
| Trending | `trending_dashboard.py` | API (analytics) |
| Mission Control | `hub_portal.py` | Docs, data catalog, showcase, self-improvement |

---

## Data Layer

### harris_farm.db (SQLite, 399MB)

Weekly aggregated data. `sales` table uses a MEASURE-DIMENSION pattern:

| measure | What `value` means |
|---------|-------------------|
| Sales - Val | Revenue ($) |
| Final Gross Prod - Val | Gross profit ($) |
| Bgt Sales - Val | Budget revenue ($) |
| Bgt Final GP - Val | Budget gross profit ($) |
| Total Shrinkage - Val | Shrinkage ($) |

Also contains: `customers` (17K rows), `market_share` (77K rows).

### Transaction Parquets (DuckDB, 383M rows)

| File | Period | Rows |
|------|--------|------|
| FY24.parquet | Jul 2023 - Jun 2024 | 134M |
| FY25.parquet | Jul 2024 - Jun 2025 | 149M |
| FY26.parquet | Jul 2025 - Feb 2026 | 99M |

Accessed via `backend/transaction_layer.py` using DuckDB's zero-copy parquet reader.

### hub_data.db (SQLite, app state)

Queries, responses, evaluations, prompt templates, knowledge base, agent data, auth sessions.

---

## Authentication Flow

```
User visits site
  → app.py calls require_login()
    → Check st.session_state for auth_token + auth_user
      → Found? Return immediately (no API call)
      → Not found? Show login page, call st.stop()

User submits login form
  → POST /api/auth/login (email + password)
    → bcrypt verify
    → Generate session token
    → Store in st.session_state
    → st.rerun() → require_login() finds token → returns user

User navigates between pages
  → st.page_link() triggers rerun (no page reload)
  → require_login() finds token in session_state
  → Returns cached user immediately
  → Page renders with user context
```

---

## Deployment Architecture (Render)

```
Render Web Service (Starter plan)
  ├── Build: pip install -r requirements.txt
  ├── Start: bash render_start.sh
  │     ├── Symlink /data → data/
  │     ├── python data_loader.py (downloads from GitHub Releases)
  │     ├── uvicorn backend.app:app --host 127.0.0.1 --port 8000 &
  │     ├── Wait for backend ready (30s timeout)
  │     └── streamlit run dashboards/app.py --server.port $PORT
  │
  └── Persistent Disk (10GB at /data)
        ├── harris_farm.db (399MB)
        ├── transactions/FY24.parquet (2.3GB)
        ├── transactions/FY25.parquet (2.7GB)
        ├── transactions/FY26.parquet (1.7GB)
        ├── hub_data.db (app state)
        └── *.csv (reference files)
```

Data persists across deploys. Only downloaded on first deploy (~10 min).

---

## External Services

| Service | Used By | Required |
|---------|---------|----------|
| Anthropic (Claude) | NL queries, Hub Assistant, Rubric | Yes (for AI features) |
| OpenAI (GPT) | Rubric comparison | Optional |
| xAI (Grok) | Rubric comparison | Optional |

---

## Key Design Decisions

1. **Single `st.navigation()` app** — one process, shared session, one port. Replaced 17 separate processes.
2. **Auth gate in app.py only** — `require_login()` runs once before any page. Pages read from `st.session_state`.
3. **Session trust** — once logged in, token is trusted from session_state without re-verifying against API on every page load.
4. **Light theme login** — works WITH Streamlit's default theme instead of fighting it with dark CSS overrides.
5. **GitHub Releases for data** — large files stored as release assets, auto-downloaded by `data_loader.py`. Split files >2GB into parts.
6. **DuckDB for transactions** — zero-copy parquet reader, no ETL needed, queries 383M rows in seconds.
7. **5-4-4 fiscal calendar** — all date logic uses Harris Farm's fiscal calendar (Jul-Jun, 5-4-4 week pattern).
