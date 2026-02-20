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
    python data_loader.py
fi

# Also link backend/hub_data.db to persistent disk
if [ -d /data ] && [ ! -f /data/hub_data.db ]; then
    touch /data/hub_data.db
fi
if [ -d /data ]; then
    ln -sf /data/hub_data.db backend/hub_data.db
fi

# Start FastAPI backend on internal port 8000
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 &

# Wait for backend to be ready (up to 30 seconds)
echo "Waiting for backend API..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
        echo "Backend ready after ${i}s"
        break
    fi
    sleep 1
done

# Start single multi-page Streamlit app on Render's PORT
streamlit run dashboards/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false --server.fileWatcherType none
