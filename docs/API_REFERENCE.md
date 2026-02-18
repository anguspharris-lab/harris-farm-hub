# Harris Farm Hub — API Reference

> Backend API running on `http://localhost:8000`

---

## Base URL

```
http://localhost:8000
```

## Authentication

None (MVP). Production will require Azure AD / SSO tokens.

---

## Endpoints

### GET /
Health check and endpoint listing.

**Response:**
```json
{
  "service": "Harris Farm Hub API",
  "version": "1.0.0",
  "status": "operational",
  "endpoints": {
    "natural_language_query": "/api/query",
    "rubric_evaluation": "/api/rubric",
    "chairman_decision": "/api/decision",
    "user_feedback": "/api/feedback",
    "prompt_templates": "/api/templates",
    "analytics": "/api/analytics"
  }
}
```

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

**Note:** Currently returns mock results. Requires ANTHROPIC_API_KEY for SQL generation.

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

**Requires:** ANTHROPIC_API_KEY and/or OPENAI_API_KEY in `.env`

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

---

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

## Data Storage

| Store | Technology | Location |
|-------|-----------|----------|
| Hub metadata | SQLite | `backend/hub_data.db` |
| Query history | SQLite table `queries` | Auto-created on startup |
| LLM responses | SQLite table `llm_responses` | Linked to queries |
| Chairman decisions | SQLite table `evaluations` | Append-only |
| User feedback | SQLite table `feedback` | 1-5 star ratings |
| Prompt templates | SQLite table `prompt_templates` | CRUD via API |
| Generated SQL | SQLite table `generated_queries` | For learning/improvement |

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
| 422 | Validation error (bad request body) |
| 500 | Server error (check API logs) |
