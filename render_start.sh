#!/bin/bash

# ---------------------------------------------------------------------------
# Persistent disk setup (Render mounts at /data)
# Code expects data files at <project>/data/ — symlink to persistent disk
# ---------------------------------------------------------------------------
if [ -d /data ]; then
    echo "Persistent disk found at /data"

    # Ensure transactions subdirectory exists on disk
    mkdir -p /data/transactions

    # Copy ALL git-tracked reference files to disk.
    # Use cp -u (update) so newer git files overwrite stale disk copies,
    # but large downloaded files (harris_farm.db etc.) are never clobbered.
    cp -u data/*.csv /data/ 2>/dev/null || true
    cp -u data/*.parquet /data/ 2>/dev/null || true
    cp -u data/*.json /data/ 2>/dev/null || true
    cp -ru data/roles /data/ 2>/dev/null || true
    cp -ru data/census /data/ 2>/dev/null || true
    cp -ru data/outputs /data/ 2>/dev/null || true
    cp -ru data/hfm_uploads /data/ 2>/dev/null || true

    # Replace data/ with symlink to persistent disk
    rm -rf data
    ln -s /data data

    echo "Data directory linked to persistent disk"

    # Download large data files if missing (first deploy only)
    echo "Checking data files..."
    python3 data_loader.py
fi

# Also link backend/hub_data.db to persistent disk
if [ -d /data ] && [ ! -f /data/hub_data.db ]; then
    touch /data/hub_data.db
fi
if [ -d /data ]; then
    ln -sf /data/hub_data.db backend/hub_data.db
fi

# ---------------------------------------------------------------------------
# Start FastAPI backend on internal port 8000
# Run in background — Streamlit starts immediately (no blocking wait)
# ---------------------------------------------------------------------------
start_backend() {
    echo "[backend] Starting FastAPI on port 8000..."
    python3 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 2>&1 &
    BACKEND_PID=$!
    echo "[backend] PID: $BACKEND_PID"
}

start_backend

# Brief wait for backend process to stabilise (not full readiness)
sleep 3
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "[backend] Process died on first attempt. Retrying..."
    sleep 2
    start_backend
    sleep 3
fi

# Background monitor: restart backend if it crashes, log readiness
(
    # Wait for backend readiness (non-blocking — Streamlit starts in parallel)
    for i in $(seq 1 90); do
        if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
            echo "[backend] Ready after ${i}s"
            break
        fi
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo "[backend] Process died. Restarting..."
            sleep 2
            start_backend
        fi
        sleep 1
    done

    # Ongoing crash monitor
    while true; do
        sleep 30
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo "[backend] Process died. Restarting..."
            sleep 2
            start_backend
        fi
    done
) &

# ---------------------------------------------------------------------------
# Start Streamlit IMMEDIATELY — don't wait for backend
# Streamlit pages handle missing backend gracefully (show loading states).
# This ensures Render's health check sees the service port open quickly.
# ---------------------------------------------------------------------------
echo "[frontend] Starting Streamlit on port ${PORT:-10000}..."
streamlit run dashboards/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false --server.fileWatcherType none
