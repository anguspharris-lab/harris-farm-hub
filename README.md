# Harris Farm Hub — AI Centre of Excellence

> **17 dashboards. One platform. Zero complexity.**

The Hub is Harris Farm Markets' centralized AI platform — Sales, Profitability, Customer Analytics, Market Share, Transport, Store Ops, Product Intel, and more — all powered by 383M POS transactions, wrapped in a single Streamlit app with shared authentication.

**Live:** https://harris-farm-hub.onrender.com

---

## Quick Start (Local)

```bash
# Install dependencies
pip install -r requirements.txt

# Start everything (API + Hub)
bash start.sh

# Open in browser
open http://localhost:8500
```

That's it. The Hub runs on port 8500, the API on port 8000.

---

## Architecture

```
Browser (any device)
    |
    v
Streamlit Multi-Page App (port 8500)
    dashboards/app.py
    |-- Auth gate (shared login)
    |-- 17 page modules (sales, profitability, customers, etc.)
    |-- Shared styles, filters, components
    |
    v
FastAPI Backend (port 8000)
    backend/app.py
    |-- 80+ API endpoints
    |-- Auth (bcrypt, session tokens)
    |-- Natural language query engine
    |-- Multi-LLM orchestration (Claude, GPT, Grok)
    |
    v
Data Layer
    |-- harris_farm.db (SQLite, 399MB) — weekly sales, customers, market share
    |-- FY24/25/26.parquet (DuckDB) — 383M POS transactions
    |-- hub_data.db (SQLite) — app state, knowledge base, chat history
```

### Dashboards (17 pages, 5 pillars)

| Pillar | Pages |
|--------|-------|
| For The Greater Goodness | Greater Goodness |
| Smashing It for the Customer | Customers, Market Share |
| Growing Legendary Leadership | Learning Centre, Hub Assistant |
| Today's Business, Done Better | Sales, Profitability, Transport, Store Ops, Buying Hub, Product Intel |
| Tomorrow's Business, Built Better | Prompt Builder, The Rubric, Trending, Revenue Bridge, Hub Portal |

---

## Deployment (Render)

The Hub is deployed to Render at https://harris-farm-hub.onrender.com. Everything is automated — push to `main` triggers a deploy.

### How it works

1. **Build step:** `pip install -r requirements.txt`
2. **Start step:** `bash render_start.sh` which:
   - Links persistent disk at `/data`
   - Downloads data files from GitHub Releases (first deploy only, ~7.2GB)
   - Starts FastAPI backend on port 8000
   - Starts Streamlit on Render's PORT

### Render service config

| Setting | Value |
|---------|-------|
| Service | Web Service (Python) |
| Plan | Starter ($7/mo) |
| Region | Oregon |
| Branch | main |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `bash render_start.sh` |
| Disk | 10GB at `/data` |

### Environment variables (set on Render dashboard)

| Variable | Purpose |
|----------|---------|
| `PYTHON_VERSION` | `3.11.6` |
| `ANTHROPIC_API_KEY` | Claude API key for NL queries and Rubric |
| `OPENAI_API_KEY` | ChatGPT API key for Rubric |
| `AUTH_ENABLED` | `true` |
| `AUTH_SECRET_KEY` | Random hex string for token signing |
| `AUTH_SITE_PASSWORD` | Shared access code for the team |
| `AUTH_ADMIN_EMAIL` | Admin user email |
| `AUTH_ADMIN_PASSWORD` | Admin user password |

### Data files

Data is stored in a GitHub Release (`data-v1`) and auto-downloaded on first deploy:

| File | Size | Contents |
|------|------|----------|
| `harris_farm.db` | 399MB | Weekly sales, customers, market share |
| `FY24.parquet` | 2.3GB | POS transactions Jul 2023 - Jun 2024 (134M rows) |
| `FY25.parquet` | 2.7GB | POS transactions Jul 2024 - Jun 2025 (149M rows) |
| `FY26.parquet` | 1.7GB | POS transactions Jul 2025 - Feb 2026 (99M rows) |

Files >2GB are split into parts for GitHub (2GB upload limit) and reassembled automatically by `data_loader.py`.

### Updating data files

To update data files (e.g., new FY26 data):

```bash
# Install gh CLI if needed
brew install gh

# Upload new file (splits automatically if >2GB)
gh release upload data-v1 path/to/new_file.parquet --clobber

# For files >2GB, split first:
split -b 1900m path/to/big_file.parquet /tmp/FY26.parquet.part_
gh release upload data-v1 /tmp/FY26.parquet.part_* --clobber

# Delete old data on Render to force re-download:
# Render Dashboard -> harris-farm-hub -> Shell -> rm /data/transactions/FY26.parquet
# Then trigger a manual deploy
```

### Fresh deploy from scratch

If deploying to a new Render service:

1. Create a Web Service pointing to this repo
2. Set all environment variables listed above
3. Add a 10GB disk mounted at `/data`
4. Deploy — data downloads automatically on first start

---

## Local Development

### Prerequisites

- Python 3.9+
- pip

### Running locally

```bash
# Install deps
pip install -r requirements.txt

# Option A: Use start.sh (starts API + Hub)
bash start.sh

# Option B: Manual
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 &
streamlit run dashboards/app.py --server.port 8500 --server.fileWatcherType none
```

### Environment

Copy `.env.template` to `.env` or create one:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
AUTH_ENABLED=false          # Set to true to require login locally
```

With `AUTH_ENABLED=false`, the auth gate is bypassed and you go straight to the Hub.

### Data files

The following must be in `data/` for data-dependent dashboards:

- `harris_farm.db` — required for Sales, Profitability, Market Share, Landing
- `data/transactions/FY*.parquet` — required for Customer, Store Ops, Product Intel, Buying Hub, Revenue Bridge

AI dashboards (Prompt Builder, Rubric, Hub Assistant, Learning Centre) work without data files.

---

## Project Structure

```
harris-farm-hub/
  dashboards/
    app.py                      # Single entry point (st.navigation)
    landing.py                  # Home page with pillar cards
    sales_dashboard.py          # Sales performance
    profitability_dashboard.py  # Store P&L
    customer_dashboard.py       # Customer analytics
    market_share_dashboard.py   # Market share by postcode
    transport_dashboard.py      # Transport costs
    store_ops_dashboard.py      # Store operations
    product_intel_dashboard.py  # Product-level analytics
    buying_hub_dashboard.py     # Buying analysis
    revenue_bridge_dashboard.py # Revenue bridge
    chatbot_dashboard.py        # Hub Assistant (RAG chatbot)
    learning_centre.py          # Training content
    prompt_builder.py           # Custom prompt designer
    rubric_dashboard.py         # Multi-LLM evaluation
    trending_dashboard.py       # Usage analytics
    hub_portal.py               # Documentation portal
    greater_goodness.py         # Sustainability
    nav.py                      # Legacy nav data (used by landing)
    shared/
      auth_gate.py              # Login/register UI + session management
      styles.py                 # Shared CSS + header/footer
      fiscal_selector.py        # 5-4-4 fiscal calendar picker
      hierarchy_filter.py       # Product hierarchy drill-down
      time_filter.py            # Time/hour range filter
      ask_question.py           # NL query component
      stores.py                 # Store list constants
      data_access.py            # SQLite helpers
  backend/
    app.py                      # FastAPI server (80+ endpoints)
    auth.py                     # Authentication (bcrypt, sessions)
    fiscal_calendar.py          # 5-4-4 fiscal calendar logic
    transaction_layer.py        # DuckDB parquet query engine
    transaction_queries.py      # Pre-built transaction queries
    product_hierarchy.py        # Product hierarchy lookups
    hub_data.db                 # App state database
  data/
    harris_farm.db              # Main analytics database
    transactions/               # POS transaction parquets
    *.csv                       # Reference data files
  data_loader.py                # Downloads data from GitHub Releases
  render_start.sh               # Render startup script
  render.yaml                   # Render service config
  start.sh                      # Local startup script
  requirements.txt              # Python dependencies
```

---

## Authentication

The Hub uses a two-layer auth system:

1. **Site access code** — shared password you give the team (set via `AUTH_SITE_PASSWORD`)
2. **Individual accounts** — email + password per user

On first deploy, an admin account is created from `AUTH_ADMIN_EMAIL` / `AUTH_ADMIN_PASSWORD` env vars.

Users can create their own accounts (requires the site access code).

Set `AUTH_ENABLED=false` to bypass all auth (local dev).

---

## Health Check

```bash
# Local
bash watchdog/health.sh

# Render — check via logs
# Dashboard -> harris-farm-hub -> Logs
```

---

## License

Proprietary — Harris Farm Markets Internal Use Only
