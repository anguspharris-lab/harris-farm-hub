# Harris Farm Hub — Runbook

> Operations guide for the Hub. Covers local dev, Render deployment, monitoring, and troubleshooting.

---

## Service Map

| Service | Port | Process | What it does |
|---------|------|---------|-------------|
| Hub (Streamlit) | 8500 (local) / $PORT (Render) | `streamlit run dashboards/app.py` | All 17 dashboards, single process |
| API (FastAPI) | 8000 | `uvicorn backend.app:app` | 80+ endpoints, auth, NL queries, LLM |

---

## Local Operations

### Start

```bash
cd /Users/angusharris/Downloads/harris-farm-hub
bash start.sh
# Hub: http://localhost:8500
# API: http://localhost:8000
```

### Stop

```bash
pkill -f "streamlit run"
pkill -f "uvicorn"
```

### Restart just the Hub (keep API running)

```bash
pkill -f "streamlit run"
streamlit run dashboards/app.py --server.port 8500 --server.headless true --server.fileWatcherType none &
```

### Check health

```bash
bash watchdog/health.sh
```

### View logs

```bash
tail -f logs/api.log    # Backend
tail -f logs/hub.log    # Streamlit
```

### Change API keys

```bash
bash setup_keys.sh
```

---

## Render Operations

### Deployment

Deploys trigger automatically on push to `main`. To manually deploy:

```bash
# Via Render API
curl -X POST -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache": "do_not_clear"}' \
  https://api.render.com/v1/services/srv-d6b3lqur433s73aq0u2g/deploys
```

Or use the dashboard: https://dashboard.render.com/web/srv-d6b3lqur433s73aq0u2g

### View logs

Dashboard -> harris-farm-hub -> Logs

### SSH into the service

```bash
ssh srv-d6b3lqur433s73aq0u2g@ssh.oregon.render.com
```

### Check data on disk

```bash
# Via SSH
ls -lh /data/
ls -lh /data/transactions/
du -sh /data/*
```

### Force re-download data

```bash
# Via SSH — delete the file, then redeploy
rm /data/harris_farm.db
rm /data/transactions/FY26.parquet
# Then trigger a deploy (data_loader.py runs on start)
```

### Environment variables

Set via dashboard: https://dashboard.render.com/web/srv-d6b3lqur433s73aq0u2g/env

| Variable | Purpose | Required |
|----------|---------|----------|
| `PYTHON_VERSION` | Python runtime | Yes |
| `ANTHROPIC_API_KEY` | Claude API | Yes |
| `OPENAI_API_KEY` | GPT API | Yes |
| `AUTH_ENABLED` | Enable login (`true`/`false`) | Yes |
| `AUTH_SECRET_KEY` | Token signing key | Yes |
| `AUTH_SITE_PASSWORD` | Shared team access code | Yes |
| `AUTH_ADMIN_EMAIL` | Admin account email | Yes (first deploy) |
| `AUTH_ADMIN_PASSWORD` | Admin account password | Yes (first deploy) |

### Render API key

Stored locally: used for CLI operations. Generate at:
https://dashboard.render.com/u/settings#api-keys

Service ID: `srv-d6b3lqur433s73aq0u2g`

---

## Data Management

### Data sources

| File | Location | Size | Updates |
|------|----------|------|---------|
| `harris_farm.db` | `/data/harris_farm.db` | 399MB | Weekly (manual upload) |
| `FY24.parquet` | `/data/transactions/FY24.parquet` | 2.3GB | Static (closed FY) |
| `FY25.parquet` | `/data/transactions/FY25.parquet` | 2.7GB | Static (closed FY) |
| `FY26.parquet` | `/data/transactions/FY26.parquet` | 1.7GB | Periodic (current FY) |
| `hub_data.db` | `/data/hub_data.db` | <1MB | Auto (app state) |

### Updating harris_farm.db

1. Get the updated `.db` file
2. Upload to GitHub Release:
   ```bash
   gh release upload data-v1 harris_farm.db --clobber
   ```
3. SSH into Render and delete the old file:
   ```bash
   ssh srv-d6b3lqur433s73aq0u2g@ssh.oregon.render.com
   rm /data/harris_farm.db
   ```
4. Trigger a redeploy — `data_loader.py` will download the new file

### Updating transaction parquets

Same process. For files >2GB, split first:
```bash
split -b 1900m path/to/FY26.parquet /tmp/FY26.parquet.part_
gh release upload data-v1 /tmp/FY26.parquet.part_* --clobber
```

### Backup

```bash
# Via SSH
cp /data/harris_farm.db /data/harris_farm.db.bak
cp /data/hub_data.db /data/hub_data.db.bak
```

---

## Troubleshooting

### Login page appears but fields are invisible / white-on-white

The login page uses Streamlit's default light theme. If custom CSS from `shared/styles.py` is loading before the auth gate, check that `app.py` calls `require_login()` BEFORE `apply_styles()`.

### "Cannot connect to the Hub API" on login

The backend hasn't started yet. On Render, it takes ~10s to boot. Refresh after 30 seconds.

### Login doesn't persist between pages

Ensure `dashboards/app.py` uses `st.page_link()` for navigation (not HTML `<a href>` links). HTML links cause full page reloads which destroy `st.session_state`.

### Data dashboards show empty / errors

Data files aren't on disk. Check via SSH:
```bash
ls -lh /data/harris_farm.db
ls -lh /data/transactions/
```
If missing, trigger a redeploy — `data_loader.py` will download them.

### Deploy fails at build step

Check `requirements.txt` — all packages must be installable on Python 3.11. Common issues:
- `pydantic<2` constraint (needed for FastAPI compatibility)
- Missing system packages (shouldn't happen on Render Python runtime)

### "ModuleNotFoundError: No module named 'auth'"

The backend needs `backend/` on `sys.path`. This is handled by `backend/app.py` line 25-29. If running manually, use:
```bash
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```
NOT `cd backend && python3 app.py`.

### Streamlit "watchdog" error

The project has a `watchdog/` directory that shadows the pip `watchdog` package. Always run with:
```bash
--server.fileWatcherType none
```

---

## Key Files

| File | What it does | When to edit |
|------|-------------|-------------|
| `dashboards/app.py` | Entry point, navigation, auth gate | Adding/removing pages |
| `dashboards/shared/auth_gate.py` | Login UI + session management | Changing login flow |
| `dashboards/shared/styles.py` | Shared CSS, header, footer | Changing look and feel |
| `backend/app.py` | All API endpoints | Adding backend features |
| `backend/auth.py` | Auth logic, token management | Changing auth rules |
| `data_loader.py` | Data download from GitHub | Adding new data files |
| `render_start.sh` | Render startup sequence | Changing deploy behavior |
| `render.yaml` | Render service config | Changing infra settings |
| `requirements.txt` | Python dependencies | Adding packages |
