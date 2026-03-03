# Harris Farm Hub — API Reference

> Backend API powering the Hub. ~264 endpoints across 22 groups.

---

## Base URL

```
http://localhost:8000        # Local development
```

On Render, the API runs on port 8000 behind the Streamlit frontend. All API calls from the Hub go through the internal network — the API is not directly exposed to the internet.

---

## Authentication

Most endpoints require an `X-Auth-Token` header containing a session token obtained from the `/api/auth/login` endpoint.

```
X-Auth-Token: <session_token>
```

Admin endpoints additionally require the authenticated user to have `role='admin'`.

---

## Endpoint Groups

| Group | Prefix | Endpoints | Description |
|-------|--------|-----------|-------------|
| Health | `GET /` and `GET /health` | 2 | Service status |
| Auth | `/api/auth/*` | 7 | Login, register, reset-password, verify session |
| Admin Auth | `/api/auth/admin/*` | 8 | List/update/delete users, list sessions, audit log |
| Roles | `/api/auth/role`, `/api/auth/roles` | 2 | Role management |
| Transactions | `/api/transactions/*` | 8 | Transaction queries via DuckDB |
| Product Hierarchy | `/api/products/*` | 5 | Department browse, search, PLU lookup |
| Fiscal Calendar | `/api/fiscal/*` | 3 | Years, periods, current period |
| Knowledge Base | `/api/knowledge/*` | 2 | Search, seed |
| Chat | `/api/chat` | 1 | Hub Assistant chat |
| PtA (Prompt-to-Approval) | `/api/pta/*` | 10 | Generate, score, submit, approve |
| Learning | `/api/learning/*` | 5 | Modules, progress tracking |
| Templates | `/api/templates` | 2 | Prompt template CRUD |
| Rubric | `/api/rubric` | 1 | Multi-LLM evaluation |
| Analytics | `/api/analytics/*` | 4 | Page view tracking, usage stats |
| Academy | `/api/academy/*` | 10 | XP, streaks, badges, leaderboard |
| Intelligence | `/api/intelligence/*` | 4 | Run analysis, reports, export |
| Agent Tasks | `/api/agent-tasks` | 3 | NL query submission |
| Self-Improvement | `/api/self-improvement/*` | 5 | Score tracking, cycles |
| Admin Agents | `/api/admin/*` | 8 | Agent control, executor |
| Portal | `/api/portal/*` | 6 | Gamification |
| Watchdog | `/api/watchdog/*` | 7 | Safety, audit |
| MDHE | `/api/mdhe/*` | 10 | Scores, validations, issues, scan results, PLU records, sources, demo data |
| **Total** | | **~264** | |

---

## Core Endpoints (Detailed)

### GET /

Health check and endpoint listing.

**Response:**
```json
{
  "service": "Harris Farm Hub API",
  "version": "1.0.0",
  "status": "operational",
  "endpoints": { ... }
}
```

### GET /health

Lightweight health check (instant 200 response). Used by Render for health monitoring.

---

### POST /api/query

Convert natural language question to SQL and return results.

**Request Body:**
```json
{
  "question": "Which stores had margin below 5% last month?",
  "dataset": "sales",
  "user_id": "finance_team"
}
```

| Field | Type | Required | Options |
|-------|------|----------|---------|
| question | string | Yes | Any natural language question |
| dataset | string | No | `sales`, `profitability`, `transport`, `inventory` (default: `sales`) |
| user_id | string | No | User identifier (default: `finance_team`) |

**Response:**
```json
{
  "query_id": 1,
  "question": "Which stores had margin below 5% last month?",
  "generated_sql": "SELECT ...",
  "results": [...],
  "result_count": 3,
  "explanation": "Based on the data...",
  "dataset": "sales"
}
```

**Requires:** `ANTHROPIC_API_KEY` for SQL generation.

---

### POST /api/rubric

The Rubric: Query multiple LLMs simultaneously and compare responses.

**Request Body:**
```json
{
  "prompt": "What is the best pricing strategy for premium fresh produce?",
  "context": "Harris Farm Markets operates 34 stores in NSW/QLD/ACT...",
  "providers": ["claude", "chatgpt"],
  "user_id": "chairman"
}
```

| Field | Type | Required | Options |
|-------|------|----------|---------|
| prompt | string | Yes | The question to evaluate |
| context | string | No | Background information |
| providers | array | No | `claude`, `chatgpt`, `grok` (default: `["claude", "chatgpt"]`) |
| user_id | string | No | default: `chairman` |

**Response:**
```json
{
  "query_id": 1,
  "prompt": "...",
  "context": "...",
  "timestamp": "2026-02-13T...",
  "responses": [
    {
      "provider": "Claude Sonnet 4.5",
      "response": "...",
      "tokens": 1234,
      "latency_ms": 2345.67,
      "timestamp": "...",
      "status": "success"
    },
    {
      "provider": "ChatGPT-4 Turbo",
      "response": "...",
      "tokens": 987,
      "latency_ms": 1876.43,
      "timestamp": "...",
      "status": "success"
    }
  ],
  "awaiting_chairman_decision": true
}
```

**Requires:** `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY` in `.env`

---

### POST /api/decision

Record the Chairman's Decision on which LLM response was best.

**Request Body:**
```json
{
  "query_id": 1,
  "winner": "Claude Sonnet 4.5",
  "feedback": "More specific to Harris Farm context",
  "user_id": "chairman"
}
```

---

### POST /api/feedback

Submit user feedback on query quality (1-5 stars).

**Request Body:**
```json
{
  "query_id": 1,
  "rating": 4,
  "comment": "Good answer but missed seasonal context",
  "user_id": "finance_team"
}
```

---

### GET /api/templates

Retrieve prompt templates from the library.

**Query Parameters:**

| Param | Type | Options |
|-------|------|---------|
| category | string | `retail_ops`, `buying`, `merchandising`, `finance`, `general` |
| difficulty | string | `beginner`, `intermediate`, `advanced` |

### POST /api/templates

Add a new prompt template.

**Request Body:**
```json
{
  "title": "Weekly Wastage Report",
  "description": "Shows wastage by category and store for the past week",
  "template": "Show all products with wastage above {{threshold}}% ...",
  "category": "retail_ops",
  "difficulty": "beginner"
}
```

---

### GET /api/analytics/performance

Self-improvement analytics: top queries, LLM win rates, popular templates.

### GET /api/analytics/weekly-report

Weekly summary: total queries, average rating, SQL success rate.

---

## MDHE Endpoints

### GET /api/mdhe/scores

Returns domain health scores (product, supplier, pricing, store).

**Response:**
```json
{
  "scores": [
    { "domain": "product", "score": 87.3, "trend": "up", "issues": 12 },
    { "domain": "supplier", "score": 92.1, "trend": "stable", "issues": 4 },
    { "domain": "pricing", "score": 78.9, "trend": "down", "issues": 23 },
    { "domain": "store", "score": 95.0, "trend": "up", "issues": 2 }
  ]
}
```

### GET /api/mdhe/validations

Returns validation failures with optional filters.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| domain | string | Filter by domain (product, supplier, pricing, store) |
| severity | string | Filter by severity (critical, warning, info) |
| limit | int | Max results (default: 100) |

### GET /api/mdhe/issues

Returns issue tracker items for data quality remediation.

### PUT /api/mdhe/issues/{id}

Update issue status (e.g., open, in_progress, resolved).

**Request Body:**
```json
{
  "status": "resolved",
  "resolution_note": "Fixed supplier code mapping"
}
```

### POST /api/mdhe/seed-demo

Seed demo data for testing and demonstration purposes.

### DELETE /api/mdhe/clear-demo

Clear all demo data from the MDHE tables.

---

## Data Storage

| Store | Technology | Size | Contents |
|-------|-----------|------|----------|
| `harris_farm.db` | SQLite | 418MB | Weekly sales, customers, market share |
| `harris_farm_plu.db` | SQLite | 3.1GB | PLU weekly results (27.3M rows) |
| `hub_data.db` | SQLite | ~105 tables | App state, auth, MDHE, gamification, agents |
| Transaction parquets | DuckDB | 383M rows | POS transactions (FY24-FY26) |

---

## Error Responses

```json
{
  "detail": "Error message describing what went wrong"
}
```

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 401 | Unauthorized — missing or invalid auth token |
| 403 | Forbidden — insufficient role permissions |
| 404 | Not found |
| 422 | Validation error (bad request body) |
| 500 | Server error (check API logs) |
