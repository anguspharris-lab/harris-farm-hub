# Harris Farm Hub — Architecture

*Last Updated: 2026-02-17 (v2.2.0)*

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                          USER (Browser)                               │
│                                                                       │
│  Financial Hub      Market Intel     Operations    Transactions       │
│  ┌──────┐┌──────┐  ┌──────┐┌──────┐ ┌──────┐  ┌──────┐┌──────┐    │
│  │Sales ││Profit│  │Cust. ││Share │ │Trans │  │StOps ││ProdIn│    │
│  │:8501 ││:8502 │  │:8507 ││:8508 │ │:8503 │  │:8511 ││:8512 │    │
│  └──┬───┘└──┬───┘  └──┬───┘└──┬───┘ └──┬───┘  └──┬───┘└──┬───┘    │
│     │       │         │       │        │         │       │          │
│  Learning Hub          ┌──────┐┌──────┐  Landing                     │
│  ┌──────┐┌──────┐      │RevBr ││Buyer │  ┌──────┐                   │
│  │Learn ││Build │      │:8513 ││:8514 │  │Home  │                   │
│  │:8510 ││:8504 │      └──┬───┘└──┬───┘  │:8500 │                   │
│  └──┬───┘└──┬───┘         │       │      └──┬───┘                   │
│     │       │    ┌──────┐┌──────┐┌──────┐   │                       │
│     │       │    │Rubric││Trend ││Asst. │   │   ┌──────┐            │
│     │       │    │:8505 ││:8506 ││:8509 │   │   │Portal│            │
│     │       │    └──┬───┘└──┬───┘└──┬───┘   │   │:8515 │            │
│     │       │       │       │       │        │   └──┬───┘            │
└─────┼───────┼───────┼───────┼───────┼────────┼──────┼────────────────┘
      └───────┴───────┴───────┴───────┴────────┴──────┘
                              │
                              v
              ┌─────────────────────────────┐
              │     FastAPI Backend :8000    │
              │     (71+ endpoints)          │
              │                             │
              │  ┌───────────────────────┐  │
              │  │ Agent Executor        │  │
              │  │ (proposals → analysis)│  │
              │  └───────────────────────┘  │
              │  ┌───────────────────────┐  │
              │  │ Data Intelligence     │  │
              │  │ (6 analysis types)    │  │
              │  └───────────────────────┘  │
              │  ┌───────────────────────┐  │
              │  │ Self-Improvement      │  │
              │  │ (score → improve)     │  │
              │  └───────────────────────┘  │
              └──────┬──────────┬───────────┘
                     │          │
          ┌──────────┘          └──────────┐
          v                                v
  ┌───────────────┐              ┌─────────────────┐
  │ SQLite        │              │ DuckDB          │
  │ hub_data.db   │              │ (in-memory)     │
  │ (35 tables)   │              │ 383.6M txns     │
  │ harris_farm.db│              │ + product hier. │
  │ (weekly agg)  │              │ + fiscal cal.   │
  └───────────────┘              └─────────────────┘
                                         │
                                    reads from
                                         │
                                 ┌───────────────┐
                                 │ Parquet Files  │
                                 │ FY24/25/26     │
                                 │ (6.6GB)        │
                                 └───────────────┘
```

---

## Components

### Frontend: Streamlit Dashboards (x16)

#### Financial Hub
| Dashboard | File | Port | Data Source |
|-----------|------|------|------------|
| Sales | `dashboards/sales_dashboard.py` | 8501 | harris_farm.db (weekly) |
| Profitability | `dashboards/profitability_dashboard.py` | 8502 | harris_farm.db (weekly) |

#### Market Intel Hub
| Dashboard | File | Port | Data Source |
|-----------|------|------|------------|
| Customers | `dashboards/customer_dashboard.py` | 8507 | harris_farm.db (weekly) |
| Market Share | `dashboards/market_share_dashboard.py` | 8508 | harris_farm.db (weekly) |

#### Operations Hub
| Dashboard | File | Port | Data Source |
|-----------|------|------|------------|
| Transport | `dashboards/transport_dashboard.py` | 8503 | harris_farm.db (weekly) |

#### Transactions Hub
| Dashboard | File | Port | Data Source |
|-----------|------|------|------------|
| Store Ops | `dashboards/store_ops_dashboard.py` | 8511 | 383.6M transactions (DuckDB) |
| Product Intel | `dashboards/product_intel_dashboard.py` | 8512 | Transactions + Product Hierarchy |
| Revenue Bridge | `dashboards/revenue_bridge_dashboard.py` | 8513 | Transactions + Fiscal Calendar |
| Buying Hub | `dashboards/buying_hub_dashboard.py` | 8514 | Transactions + Product Hierarchy |

#### Learning Hub
| Dashboard | File | Port | Data Source |
|-----------|------|------|------------|
| Learning Centre | `dashboards/learning_centre.py` | 8510 | 12 modules, 14 lessons |
| Prompt Builder | `dashboards/prompt_builder.py` | 8504 | prompt_templates |
| The Rubric | `dashboards/rubric_dashboard.py` | 8505 | Multi-LLM comparison |
| Trending | `dashboards/trending_dashboard.py` | 8506 | Usage analytics |
| Hub Assistant | `dashboards/chatbot_dashboard.py` | 8509 | Knowledge base (536 articles) |
| Hub Portal | `dashboards/hub_portal.py` | 8515 | Docs, intelligence, agents (11 tabs) |

#### Other
| Dashboard | File | Port | Data Source |
|-----------|------|------|------------|
| Landing Page | `dashboards/landing.py` | 8500 | Static + hub links |

**Tech stack:** Streamlit 1.50 + Plotly + Pandas 2.x + Python 3.9

**Navigation:** All dashboards share `dashboards/nav.py` — two-row hub navigation with 5 hub categories.

**Shared Module:** `dashboards/shared/` contains 7 reusable modules:
- `data_access.py`: Centralised query functions for SQLite weekly data
- `fiscal_selector.py`: Reusable FY/Quarter/Month/Week/Custom period selector
- `styles.py`: Shared CSS and styling
- `learning_content.py`: Learning module content
- `training_content.py`: Training curriculum
- `watchdog_safety.py`: WATCHDOG safety analysis service
- `auth_gate.py`: Authentication gate for dashboards

### Backend: FastAPI (71+ endpoints)

| Module | File | Purpose |
|--------|------|---------|
| API Server | `backend/app.py` | 71+ endpoints, 35 tables, CORS, lifecycle (~4260 lines) |
| Transaction Layer | `backend/transaction_layer.py` | DuckDB query engine for 383.6M POS rows |
| Transaction Queries | `backend/transaction_queries.py` | 41 pre-built SQL queries |
| Data Analysis | `backend/data_analysis.py` | 6 analysis types + presentation rubric |
| Agent Executor | `backend/agent_executor.py` | Polls/routes/executes approved proposals |
| Agent Router | `backend/agent_router.py` | NL query → analysis type routing |
| Self-Improvement | `backend/self_improvement.py` | Score tracking, weakest criterion, cycles |
| Product Hierarchy | `backend/product_hierarchy.py` | 72,911 product browser/search |
| PLU Lookup | `backend/plu_lookup.py` | Product lookup (72,911 items) |
| Fiscal Calendar | `backend/fiscal_calendar.py` | 5-4-4 retail calendar utilities |
| Authentication | `backend/auth.py` | Sessions, users, bcrypt hashing |
| Data Layer | `backend/data_layer.py` | Unified data access abstraction |
| Hub Database | `backend/hub_data.db` | SQLite metadata (35 tables) |

**Tech stack:** FastAPI 0.104 + Uvicorn 0.24 + SQLite3

**Data Access Pattern:** `backend/data_layer.py` provides a pluggable abstraction layer:
- `DataSource` (abstract base class): Defines standard interface for all data backends
- `MockDataSource`: Deterministic seeded mock data (RNG 42) for development/testing
- `FabricDataSource`: Stub for Microsoft Fabric integration (production)
- `get_data_source()`: Factory function reads `DB_TYPE` env var to select implementation
- All KPIs traceable to source with ±0.01 precision (data correctness law)
- Consistent data schema across mock and production backends

### Orchestrator: Multi-Agent Development System

| Component | File | Purpose |
|-----------|------|---------|
| Coordinator | `orchestrator/coordinator.py` | Manages parallel workers via git worktrees |
| Task Queue | `orchestrator/task_queue.py` | Phase-based task sequencing and dependencies |
| Worker | `orchestrator/worker.py` | Executes individual agent tasks in isolated worktrees |
| Models | `orchestrator/models.py` | Data structures (Task, Phase, WorkerResult, etc.) |
| Audit | `orchestrator/audit.py` | Logging and traceability for orchestration actions |
| Safety | `orchestrator/safety.py` | Pre-flight checks and validation |
| Config | `orchestrator/config.py` | Orchestrator configuration and settings |
| Runner | `orchestrator/run.py` | CLI entry point for orchestrated development |

**How it works:**
- Each agent (Architect, Data Engineer, Test Engineer, etc.) gets an isolated git worktree
- Agents work in parallel on separate branches from main
- Coordinator merges completed work back to main sequentially
- Full audit trail of all orchestration actions in `watchdog/audit.log`
- Enables true parallel development without merge conflicts

**Agent roles:**
- **Architect**: Structural refactoring, API design, module extraction, documentation
- **Data Engineer**: Data layer implementation, ETL, data validation
- **Test Engineer**: Test suite development, coverage, test data generation
- **Frontend Engineer**: UI/UX implementation, dashboard development
- **Backend Engineer**: API endpoints, business logic, service integration

### External Services

| Service | Purpose | Required? |
|---------|---------|-----------|
| Anthropic API (Claude) | NL queries, SQL generation, Rubric, orchestrator agents | Optional (mock data works without) |
| OpenAI API (ChatGPT) | Rubric comparison | Optional |
| xAI API (Grok) | Rubric comparison | Optional |
| Harris Farm DB (PostgreSQL) | Real transaction data | Not yet connected |

---

## Data Flow

### Natural Language Query
```
User types question in dashboard
  → Dashboard sends POST to /api/query
    → Backend stores query in SQLite
    → Backend calls Claude to generate SQL
    → (Production: execute SQL against Harris Farm DB)
    → (MVP: return mock results)
    → Backend calls Claude to explain results
    → Response returned to dashboard
    → Dashboard displays results + explanation
```

### The Rubric
```
User submits question to /api/rubric
  → Backend stores query
  → Backend fires async calls to Claude + ChatGPT + Grok
  → All responses collected (asyncio.gather)
  → Responses stored in SQLite
  → All responses returned to user
  → User picks winner via /api/decision
  → Decision stored for learning
```

---

## Key Design Decisions

1. **Streamlit over React for MVP**: Ship in a weekend. React frontend exists (`/frontend`) but unused for v1.
2. **SQLite over PostgreSQL for Hub metadata**: Zero config, embedded, sufficient for single-server MVP.
3. **Mock data in dashboards**: Dashboards work without any external dependencies. Real data integration is a separate step.
4. **Monolithic app.py**: All backend logic in one file. Will split into modules (routes, models, services) when complexity warrants it.
5. **No authentication for MVP**: Internal network only. Azure AD integration planned for production.

---

## File Structure

```
harris-farm-hub/
├── backend/
│   ├── app.py              # FastAPI server (776 lines) — primary backend
│   ├── data_layer.py       # Data access abstraction (DataSource pattern)
│   ├── main.py             # Alternate entry point (unused)
│   └── hub_data.db         # Auto-created SQLite
├── dashboards/
│   ├── shared/
│   │   ├── __init__.py     # Exports STORES, REGIONS
│   │   └── stores.py       # Canonical store network (21 locations)
│   ├── sales_dashboard.py        # Sales KPIs, charts, NL query (wired to API)
│   ├── profitability_dashboard.py # Store P&L, waterfall, insights
│   ├── transport_dashboard.py     # Delivery costs, routes, scenarios
│   ├── prompt_builder.py          # Query builder (wired to template API)
│   ├── rubric_dashboard.py        # Multi-LLM comparison + Chairman's Decision
│   └── trending_dashboard.py      # Usage analytics + self-improvement
├── orchestrator/
│   ├── __init__.py         # Package initialization
│   ├── coordinator.py      # Parallel worker coordination via git worktrees
│   ├── task_queue.py       # Phase-based task sequencing
│   ├── worker.py           # Individual agent task execution
│   ├── models.py           # Task, Phase, WorkerResult data structures
│   ├── audit.py            # Orchestration logging and traceability
│   ├── safety.py           # Pre-flight checks and validation
│   ├── config.py           # Configuration and settings
│   └── run.py              # CLI entry point
├── .worktrees/             # Isolated git worktrees for parallel agent work
├── tests/
│   ├── test_api.py               # 25 API endpoint tests
│   ├── test_rubric.py            # 10 Rubric system tests
│   ├── test_templates.py         # 8 template library tests
│   └── test_data_validation.py   # 9 data validation tests
├── docs/
│   ├── USER_GUIDE.md
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md        # This file
│   ├── DECISIONS.md
│   ├── CHANGELOG.md
│   ├── RUNBOOK.md
│   └── DESIGN_USABILITY_RUBRIC.md
├── watchdog/
│   ├── audit.log              # Full audit trail (append-only)
│   ├── health.sh              # Service health check (retry logic)
│   ├── scan.sh                # Credential/security scanner
│   ├── shutdown.sh            # Emergency shutdown with evidence
│   ├── validate_data.py       # Deep data validation
│   ├── validate_data.sh       # Validation wrapper
│   ├── rubrics/               # Scoring rubrics (code quality, UX)
│   ├── procedures/            # Standard operating procedures
│   └── learnings/             # Cross-session improvement log
├── .env                       # API keys and config (gitignored)
├── CLAUDE.md                  # Governance laws (SHA-256 verified)
├── requirements.txt           # Python deps
├── start.sh                   # Launch all services
├── stop.sh                    # Kill all services
├── setup_keys.sh              # Interactive key setup
├── docker-compose.yml         # Container orchestration
└── README.md
```

---

## Production Readmap

| Phase | What Changes |
|-------|-------------|
| MVP (now) | Mock data, SQLite, no auth, localhost |
| Week 2 | Real DB connection, Azure AD, HTTPS |
| Week 3 | Shared navigation, React frontend, scheduled reports |
| Month 2 | Predictive models, real-time alerts, mobile |
