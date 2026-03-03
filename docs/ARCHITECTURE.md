# Harris Farm Hub — Architecture

*Last Updated: 2026-02-27 (v3.8 — MDHE + Property Intelligence + Role-Based Access)*

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
         │  │ Role-Based Page Filtering   │    │
         │  │ hub_role → allowed_slugs    │    │
         │  └─────────────────────────────┘    │
         │                                     │
         │  ┌─────────────────────────────┐    │
         │  │ st.navigation() router      │    │
         │  │ 43 pages across 6 sections  │    │
         │  └─────────────────────────────┘    │
         │                                     │
         │  Shared: styles, fiscal selector,   │
         │  hierarchy filter, ask_question     │
         └──────────────┬──────────────────────┘
                        │ HTTP (localhost:8000)
                        v
         ┌─────────────────────────────────────┐
         │     FastAPI Backend                 │
         │     backend/app.py (~264 endpoints) │
         │                                     │
         │  Auth    NL Query   Multi-LLM       │
         │  Agent Executor   Self-Improvement  │
         │  MDHE   Property Intel   Roles      │
         └──────┬──────────────┬───────────────┘
                │              │
       ┌────────┘              └────────┐
       v                                v
┌──────────────────┐           ┌─────────────────┐
│ SQLite            │           │ DuckDB          │
│                   │           │ (in-process)    │
│ harris_farm.db    │           │ 383M txns       │
│ (418MB)           │           │ via parquet     │
│                   │           │ FY24/25/26      │
│ harris_farm_plu   │           └─────────────────┘
│ .db (3.1GB)       │
│                   │           ┌─────────────────┐
│ hub_data.db       │           │ Census Data     │
│ (~105 tables)     │           │ ABS demographic │
│                   │           │ SA1→postcode    │
└──────────────────┘           └─────────────────┘
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

## Pages by Section

### Strategy (6 pages)
| Page | File | Data Source |
|------|------|------------|
| Strategy Overview | `strategy_overview.py` | Static content |
| Greater Goodness | `greater_goodness.py` | Static content |
| Growing Legends (intro) | `intro_p3_people.py` | Static content |
| Operations HQ (intro) | `intro_p4_operations.py` | Static content |
| Digital & AI HQ (intro) | `intro_p5_digital.py` | Static content |
| Way of Working | `way_of_working/dashboard.py` | Monday.com API |

### Growing Legends (4 pages)
| Page | File | Data Source |
|------|------|------------|
| Skills Academy | `skills_academy.py` | XP system, gamification (hub_data.db) |
| The Paddock | `the_paddock.py` | AI practice conversations |
| Prompt Engine | `prompt_builder.py` | 20 task templates, PtA workflow (hub_data.db) |
| Hub Assistant | `chatbot_dashboard.py` | Knowledge base (545 articles) |

### Operations (10 pages)
| Page | File | Data Source |
|------|------|------------|
| Customer Hub | `customer_hub/dashboard.py` | Transactions (DuckDB) |
| Sales | `sales_dashboard.py` | harris_farm.db |
| Profitability | `profitability_dashboard.py` | harris_farm.db |
| Revenue Bridge | `revenue_bridge_dashboard.py` | Transactions (DuckDB) |
| Store Ops | `store_ops_dashboard.py` | Transactions (DuckDB) |
| Buying Hub | `buying_hub_dashboard.py` | Transactions + Hierarchy |
| Product Intel | `product_intel_dashboard.py` | Transactions + Hierarchy |
| PLU Intelligence | `plu_intel_dashboard.py` | harris_farm_plu.db |
| Transport | `transport_dashboard.py` | harris_farm.db |
| Analytics Engine | `analytics_engine.py` | hub_data.db + harris_farm.db |

### Property (7 pages)
| Page | File | Data Source |
|------|------|------------|
| Store Network | `store_network_page.py` | Census + CBAS data |
| Market Share | `market_share_page.py` | harris_farm.db |
| Demographics | `demographics_page.py` | Census data |
| Whitespace Analysis | `whitespace_analysis.py` | Census + CBAS data |
| Competitor Map | `competitor_map_page.py` | Placeholder |
| ROCE Analysis | `roce_dashboard.py` | harris_farm.db |
| Cannibalisation | `cannibalisation_dashboard.py` | CBAS data |

### MDHE (4 pages)
| Page | File | Data Source |
|------|------|------------|
| MDHE Dashboard | `mdhe/dashboard.py` | hub_data.db (MDHE tables) |
| MDHE Upload | `mdhe/upload.py` | hub_data.db + file uploads |
| MDHE Issues | `mdhe/issues.py` | hub_data.db |
| MDHE Guide | `mdhe/guide.py` | docs/MDHE_GUIDE.md |

### Back of House (11 pages)
| Page | File | Data Source |
|------|------|------------|
| The Rubric | `rubric_dashboard.py` | Multi-LLM comparison |
| Approvals | `approvals_dashboard.py` | PtA submissions (hub_data.db) |
| Workflow Engine | `workflow_engine.py` | 4P state machine (hub_data.db) |
| Agent Operations | `agent_operations.py` | WATCHDOG safety (hub_data.db) |
| Mission Control | `hub_portal.py` | Docs, catalog, self-improvement |
| AI Adoption | `ai_adoption/dashboard.py` | Usage metrics |
| Adoption | `adoption_dashboard.py` | Page views |
| Trending | `trending_dashboard.py` | System analytics |
| Agent Hub | `agent_hub.py` | Scoreboard, Arena |
| Marketing Assets | `marketing_assets.py` | Brand files |
| User Management | `mdhe/user_management.py` | Admin user/role mgmt |

---

## Data Layer

### harris_farm.db (SQLite, 418MB)

Weekly aggregated data — sales, customers, market share.

`sales` table uses a MEASURE-DIMENSION pattern:

| measure | What `value` means |
|---------|-------------------|
| Sales - Val | Revenue ($) |
| Final Gross Prod - Val | Gross profit ($) |
| Bgt Sales - Val | Budget revenue ($) |
| Bgt Final GP - Val | Budget gross profit ($) |
| Total Shrinkage - Val | Shrinkage ($) |

Also contains: `customers` (17K rows), `market_share` (77K rows).

### harris_farm_plu.db (SQLite, 3.1GB)

27.3M PLU weekly results across 3 fiscal years and 43 stores.

### Transaction Parquets (DuckDB, 383M rows)

| File | Period | Rows |
|------|--------|------|
| FY24.parquet | Jul 2023 - Jun 2024 | 134M |
| FY25.parquet | Jul 2024 - Jun 2025 | 149M |
| FY26.parquet | Jul 2025 - Feb 2026 | 99M |

Accessed via `backend/transaction_layer.py` using DuckDB's zero-copy parquet reader.

### hub_data.db (SQLite, ~105 tables)

Application state, auth, MDHE, gamification, agents, KB, PtA workflow, chat history, adoption metrics, and more. Persists all user accounts, learning progress, and MDHE data across deploys.

### Census Data (data/census/processed/)

ABS SA1-to-postcode demographic data. Four processed files (parquet/csv, 2.8MB total). Used by Property Intelligence pages for demographic profiling and whitespace analysis.

### CBAS Network (data/cbas_network.json)

31 stores with coordinates, trade areas, and 16 whitespace opportunities. Source data for Store Network, Whitespace Analysis, and Cannibalisation pages.

---

## Authentication Flow

```
User visits site
  -> app.py calls require_login()
    -> Check st.session_state for auth_token + auth_user
      -> Found? Return immediately (no API call)
      -> Not found? Show login page, call st.stop()

User submits login form
  -> POST /api/auth/login (email + password)
    -> bcrypt verify
    -> Generate session token
    -> Store in st.session_state (including hub_role)
    -> st.rerun() -> require_login() finds token -> returns user

After login, role-based filtering:
  -> hub_role determines visible pages
  -> shared/role_config.py defines 10 roles with allowed_slugs
  -> _RESTRICTED_SLUGS filtered from navigation for non-privileged roles
  -> Financial/property data restricted to admin + executive
  -> SLT auto-promotion via AUTH_SLT_EMAILS env var

User navigates between pages
  -> st.page_link() triggers rerun (no page reload)
  -> require_login() finds token in session_state
  -> Returns cached user immediately
  -> Page renders with user context
```

---

## Role-Based Access Control

10 roles defined in `shared/role_config.py`. Each role specifies `allowed_slugs` controlling which pages appear in navigation. Enforced in `app.py` during `st.navigation()` page registration.

**Restricted slugs** (`_RESTRICTED_SLUGS`):
`sales`, `profitability`, `revenue-bridge`, `store-network`, `market-share`, `demographics`, `whitespace`, `competitor-map`, `roce`, `cannibalisation`

Only **admin** and **executive** roles see restricted pages. All other roles see the full set of non-restricted pages appropriate to their access level.

**SLT auto-promotion:** The `AUTH_SLT_EMAILS` environment variable lists email addresses that are automatically promoted to admin on login, ensuring key leadership always has full access.

---

## Deployment Architecture (Render)

```
Render Web Service (Starter plan)
  |-- Build: pip install -r requirements.txt
  |-- Start: bash render_start.sh (NON-BLOCKING)
  |     |-- Symlink /data -> data/
  |     |-- python data_loader.py (downloads from GitHub Releases)
  |     |-- streamlit run dashboards/app.py --server.port $PORT
  |     |     (starts IMMEDIATELY — serves pages while backend initializes)
  |     |-- uvicorn backend.app:app --host 127.0.0.1 --port 8000 &
  |     |     (backend readiness poll runs in background)
  |
  |-- Health check path: / (Streamlit serves this immediately)
  |-- /health endpoint on backend for internal readiness
  |
  +-- Persistent Disk (10GB at /data)
        |-- harris_farm.db (418MB)
        |-- harris_farm_plu.db (3.1GB)
        |-- transactions/FY24.parquet (2.3GB)
        |-- transactions/FY25.parquet (2.7GB)
        |-- transactions/FY26.parquet (1.7GB)
        |-- hub_data.db (~105 tables — persists across deploys)
        |-- mdhe_uploads/ (MDHE file uploads)
        +-- *.csv (reference files)
```

Data persists across deploys. Only downloaded on first deploy (~10 min). hub_data.db persists all user accounts, learning progress, and MDHE data across deploys.

---

## External Services

| Service | Used By | Required |
|---------|---------|----------|
| Anthropic (Claude) | NL queries, Hub Assistant, Rubric | Yes (for AI features) |
| OpenAI (GPT) | Rubric comparison | Optional |
| xAI (Grok) | Rubric comparison | Optional |
| Monday.com | Way of Working | Optional |

---

## Key Design Decisions

1. **Single `st.navigation()` app** — one process, shared session, one port. Replaced 17 separate processes.
2. **Auth gate in app.py only** — `require_login()` runs once before any page. Pages read from `st.session_state`.
3. **Session trust** — once logged in, token is trusted from session_state without re-verifying against API on every page load.
4. **Light theme login** — works WITH Streamlit's default theme instead of fighting it with dark CSS overrides.
5. **GitHub Releases for data** — large files stored as release assets, auto-downloaded by `data_loader.py`. Split files >2GB into parts.
6. **DuckDB for transactions** — zero-copy parquet reader, no ETL needed, queries 383M rows in seconds.
7. **5-4-4 fiscal calendar** — all date logic uses Harris Farm's fiscal calendar (Jul-Jun, 5-4-4 week pattern).
8. **Role-based page filtering** — hub_role controls which pages appear in navigation, enforced in app.py.
9. **Non-blocking startup** — Streamlit serves pages immediately while backend initializes in the background.
10. **MDHE as separate nav section** — dedicated Master Data Health section with its own colour in navigation.
11. **SLT auto-promotion** — AUTH_SLT_EMAILS env var ensures key people always have admin access.
