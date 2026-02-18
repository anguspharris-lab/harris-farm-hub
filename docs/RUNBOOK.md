# Harris Farm Hub — Runbook

> Operations guide for starting, stopping, monitoring, and troubleshooting the Hub.

---

## Quick Commands

```bash
# Start everything
cd /Users/angusharris/Downloads/harris-farm-hub
bash start.sh

# Stop everything
bash stop.sh

# Setup/change API keys (interactive)
bash setup_keys.sh

# Check if services are running
curl -s http://localhost:8000 && echo " API OK"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501  # Sales
curl -s -o /dev/null -w "%{http_code}" http://localhost:8502  # Profitability
curl -s -o /dev/null -w "%{http_code}" http://localhost:8503  # Transport
curl -s -o /dev/null -w "%{http_code}" http://localhost:8504  # Prompt Builder
```

---

## Service Details

| Service | Process | Port | Log File |
|---------|---------|------|----------|
| Backend API | `python3 app.py` | 8000 | `logs/api.log` |
| Sales Dashboard | `streamlit run sales_dashboard.py` | 8501 | `logs/sales.log` |
| Profitability | `streamlit run profitability_dashboard.py` | 8502 | `logs/profit.log` |
| Transport | `streamlit run transport_dashboard.py` | 8503 | `logs/transport.log` |
| Prompt Builder | `streamlit run prompt_builder.py` | 8504 | `logs/builder.log` |

---

## Starting Services Manually

If `start.sh` fails, start each service individually:

```bash
export PATH="/Users/angusharris/Library/Python/3.9/bin:$PATH"
cd /Users/angusharris/Downloads/harris-farm-hub

# API
cd backend && python3 app.py &
cd ..

# Dashboards (each in background)
cd dashboards
streamlit run sales_dashboard.py --server.port 8501 --server.headless true &
streamlit run profitability_dashboard.py --server.port 8502 --server.headless true &
streamlit run transport_dashboard.py --server.port 8503 --server.headless true &
streamlit run prompt_builder.py --server.port 8504 --server.headless true &
cd ..
```

---

## Stopping Services Manually

```bash
# Graceful
pkill -f "streamlit run"
pkill -f "app.py"

# Nuclear (if above doesn't work)
lsof -i :8000 -i :8501 -i :8502 -i :8503 -i :8504 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

---

## Checking Logs

```bash
# Live tail all logs
tail -f logs/*.log

# Check specific service
tail -50 logs/api.log
tail -50 logs/sales.log

# Search for errors
grep -i error logs/*.log
grep -i traceback logs/*.log
```

---

## Port Conflicts

If a port is already in use:

```bash
# Find what's using the port
lsof -i :8501

# Kill it
kill <PID>

# Or use a different port
streamlit run sales_dashboard.py --server.port 8511 --server.headless true
```

---

## Environment Variables

Located in `.env` at the project root. Services read these on startup — restart required after changes.

| Variable | Purpose | Required? |
|----------|---------|-----------|
| ANTHROPIC_API_KEY | Claude API (NL queries, Rubric) | Optional for MVP |
| OPENAI_API_KEY | ChatGPT (Rubric) | Optional for MVP |
| GROK_API_KEY | Grok (Rubric) | Optional |
| DB_TYPE | Database type | No (default: postgresql) |
| DB_HOST | Database host | No (not connected in MVP) |
| DB_PORT | Database port | No |
| DB_NAME | Database name | No |
| DB_USER | Database user | No |
| DB_PASSWORD | Database password | No |
| API_URL | Backend URL | No (default: http://localhost:8000) |

---

## Database

### Hub Metadata (SQLite)
- Location: `backend/hub_data.db`
- Auto-created on API startup
- Contains: queries, llm_responses, evaluations, feedback, prompt_templates, generated_queries

### Backup
```bash
cp backend/hub_data.db backend/hub_data_backup_$(date +%Y%m%d).db
```

### Reset (delete all Hub data)
```bash
rm backend/hub_data.db
# Restart API — it will recreate the database
```

---

## Common Issues

### "streamlit: command not found"
```bash
export PATH="/Users/angusharris/Library/Python/3.9/bin:$PATH"
```
Or use the full path: `/Users/angusharris/Library/Python/3.9/bin/streamlit`

### "ModuleNotFoundError"
```bash
pip3 install -r requirements.txt
```

### Dashboard shows but charts are empty
Mock data generates on first load. Try refreshing (Cmd+R). If persistent, check `logs/sales.log` for errors.

### API returns "API key not configured"
The AI features need keys in `.env`. Run `bash setup_keys.sh` and restart.

### "Address already in use"
Another process is on that port. Find and kill it:
```bash
lsof -i :8501 | grep LISTEN
kill <PID>
```

---

## Health Check Script

Save this as `healthcheck.sh`:

```bash
#!/bin/bash
echo "Harris Farm Hub Health Check"
echo "============================"
for port in 8000 8501 8502 8503 8504; do
    code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port)
    case $port in
        8000) name="API" ;;
        8501) name="Sales" ;;
        8502) name="Profit" ;;
        8503) name="Transport" ;;
        8504) name="Prompt Builder" ;;
    esac
    if [ "$code" = "200" ]; then
        echo "  OK   $name (:$port)"
    else
        echo "  FAIL $name (:$port) - HTTP $code"
    fi
done
```
