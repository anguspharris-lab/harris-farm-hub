# Documentation Procedure v7
# Applies to EVERY task. Docs are built AS you build, not after.

## Auto-generated docs (Watchdog maintains these):

### 1. docs/USER_GUIDE.md — How to use The Hub
Updated after every UI-facing task. Sections:
- Getting Started (login, first steps)
- Dashboard Guide (one section per dashboard with screenshots/descriptions)
- Natural Language Queries (how to ask questions, example queries)
- Prompt Builder (how super users create custom queries)
- Troubleshooting (common issues + fixes)
Format: written for finance team users, not developers. No jargon.

### 2. docs/API_REFERENCE.md — Every endpoint documented
Updated after every backend task. Per endpoint:
- Method + URL
- What it does (plain English)
- Parameters (with types and examples)
- Response format (with example)
- Error responses
Auto-generated from docstrings where possible.

### 3. docs/ARCHITECTURE.md — How the system works
Updated after structural changes. Sections:
- System overview (what runs where, what ports)
- Data flow (where data comes from, how it's transformed, where it's displayed)
- Security model (who can access what)
- Self-improvement loop (how the system gets smarter)
- Watchdog (how safety is enforced)

### 4. docs/DECISIONS.md — Architecture Decision Records
Append-only. Every significant choice logged:
- Date
- Decision
- Options considered
- Why this option was chosen
- Rubric scores that influenced the decision

### 5. docs/CHANGELOG.md — What changed and when
Updated after every task:
- [timestamp] [task #] — What changed, why, rubric score

### 6. docs/RUNBOOK.md — Complete operational guide
Updated after deployment changes:
- How to start/stop services
- How to deploy updates
- How to connect new data sources
- How to add new dashboards
- How to recover from failures
- Emergency procedures

## Rules:
- Write docs in the SAME task as the code, not as a separate step
- If a feature changes, its docs change in the same commit
- User-facing docs use plain English (finance team audience)
- Developer docs include code examples
- Pre-commit hook warns if feature files change without docs/ update
