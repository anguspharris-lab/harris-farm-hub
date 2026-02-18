# Harris Farm Markets — AI Centre of Excellence
## Documentation Index

*Last Updated: 2026-02-17 (v2.2.0)*

---

## Start Here

| Document | What you'll learn |
|----------|-------------------|
| [Best Practices Guide](BEST_PRACTICES.md) | Architecture patterns, data engineering, agent development, safety workflows, testing |
| [Feature Status Matrix](FEATURE_STATUS.md) | What's LIVE vs PARTIAL vs PLANNED — every feature audited |
| [Activation Roadmap](ACTIVATION_ROADMAP.md) | 6-phase plan from current state to fully self-improving system |

---

## System Documentation

### Architecture & Design
| Document | Purpose |
|----------|---------|
| [Architecture Overview](ARCHITECTURE.md) | System diagram, 16 dashboards, 71+ endpoints, data stack |
| [Architecture Decisions](DECISIONS.md) | 8 ADRs: why Streamlit, SQLite, monolithic backend, etc. |
| [Design & Usability Rubric](DESIGN_USABILITY_RUBRIC.md) | 8-criterion UX scoring framework |

### Operations
| Document | Purpose |
|----------|---------|
| [Runbook](RUNBOOK.md) | Start, stop, monitor, troubleshoot |
| [User Guide](USER_GUIDE.md) | Dashboard-by-dashboard guide for finance team |
| [Changelog](CHANGELOG.md) | Version history: v1.0.0 → v2.2.0 |

### Data
| Document | Purpose |
|----------|---------|
| [Data Catalog](data_catalog.md) | 383.6M transactions: schema, stores, quality, API |
| [Fiscal Calendar Profile](fiscal_calendar_profile.md) | 5-4-4 retail calendar: 4,018 daily rows, 45 columns |

---

## Governance

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](../CLAUDE.md) | 7 Laws governing all development |
| [Task Execution Procedure](../watchdog/procedures/task_execution.md) | Mandatory workflow for every task |
| [Self-Improvement Procedure](../watchdog/procedures/self_improvement.md) | MAX 3 attempts per criterion per cycle |
| [Data Correctness Procedure](../watchdog/procedures/data_correctness.md) | Validation rules for every displayed number |
| [Documentation Procedure](../watchdog/procedures/documentation.md) | Docs built AS you build, not after |

---

## Quick Reference

### Ports

| Port | Service |
|------|---------|
| 8000 | FastAPI Backend (71+ endpoints) |
| 8500 | Landing Page |
| 8501 | Sales Dashboard |
| 8502 | Profitability Dashboard |
| 8503 | Transport Dashboard |
| 8504 | Prompt Builder |
| 8505 | The Rubric |
| 8506 | Trending |
| 8507 | Customer Dashboard |
| 8508 | Market Share |
| 8509 | Hub Assistant |
| 8510 | Learning Centre |
| 8511 | Store Ops |
| 8512 | Product Intel |
| 8513 | Revenue Bridge |
| 8514 | Buying Hub |
| 8515 | Hub Portal (Documentation + Intelligence + Agents) |

### Commands

```bash
# Start everything
bash start.sh

# Run tests (1,003 tests)
python3 -m pytest tests/ -v

# Health check (all 16 services)
bash watchdog/health.sh

# Security scan
bash watchdog/scan.sh

# Execute approved agent proposals
curl -X POST http://localhost:8000/api/admin/executor/run

# Submit NL analysis query
curl -X POST http://localhost:8000/api/agent-tasks \
  -H "Content-Type: application/json" \
  -d '{"query":"find products that run out during the day","store_id":"28","days":14}'
```

### Key Metrics

| Metric | Value |
|--------|-------|
| Dashboards | 16 across 5 hubs |
| API Endpoints | 71+ |
| Database Tables | 35 (hub_data.db) |
| Tests | 1,003 across 25 files |
| Transaction Rows | 383.6M (FY24-FY26) |
| Products | 72,911 (5-level hierarchy) |
| Analysis Types | 6 (basket, stockout, intraday, price, demand, slow movers) |
| Intelligence Reports | 41 generated |
| Agent Proposals | 75 tracked |
| Knowledge Articles | 536 with full-text search |

---

## Root-Level Documents

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Project overview and quick start |
| [EXECUTIVE_SUMMARY.md](../EXECUTIVE_SUMMARY.md) | Leadership briefing |
| [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) | Full deployment instructions |
| [QUICKSTART.md](../QUICKSTART.md) | One-page onboarding |
