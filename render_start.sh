#!/bin/bash

# ---------------------------------------------------------------------------
# Persistent disk setup (Render mounts at /data)
# Code expects data files at <project>/data/ — symlink to persistent disk
# ---------------------------------------------------------------------------
if [ -d /data ]; then
    echo "Persistent disk found at /data"

    # Ensure transactions subdirectory exists on disk
    mkdir -p /data/transactions

    # Copy git-tracked reference files to disk (first deploy only)
    cp -n data/*.csv /data/ 2>/dev/null || true
    cp -n data/*.parquet /data/ 2>/dev/null || true
    cp -rn data/roles /data/ 2>/dev/null || true

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
# Run in background with output captured; restart if it crashes
# ---------------------------------------------------------------------------
start_backend() {
    echo "[backend] Starting FastAPI on port 8000..."
    python3 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 2>&1 &
    BACKEND_PID=$!
    echo "[backend] PID: $BACKEND_PID"
}

start_backend

# Wait for backend to be ready (up to 60 seconds)
echo "Waiting for backend API..."
BACKEND_READY=false
for i in $(seq 1 60); do
    # Check if process is still alive
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "[backend] Process died (exit). Restarting..."
        sleep 2
        start_backend
    fi
    if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
        echo "[backend] Ready after ${i}s"
        BACKEND_READY=true
        break
    fi
    sleep 1
done

if [ "$BACKEND_READY" = false ]; then
    echo "[backend] WARNING: Backend not ready after 60s. Streamlit will start anyway."
fi

# Background monitor: restart backend if it crashes
(
    while true; do
        sleep 30
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo "[backend] Process died. Restarting..."
            sleep 2
            start_backend
        fi
    done
) &

# Start single multi-page Streamlit app on Render's PORT
streamlit run dashboards/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false --server.fileWatcherType none
