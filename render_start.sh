#!/bin/bash

# ---------------------------------------------------------------------------
# Persistent disk setup (Render mounts at /data)
# Code expects data files at <project>/data/ — symlink to persistent disk
# ---------------------------------------------------------------------------
if [ -d /data ]; then
    echo "Persistent disk found at /data"

    # Copy git-tracked reference files to disk (first deploy only)
    cp -n data/*.csv /data/ 2>/dev/null || true
    cp -n data/*.parquet /data/ 2>/dev/null || true
    cp -rn data/roles /data/ 2>/dev/null || true

    # Replace data/ with symlink to persistent disk
    rm -rf data
    ln -s /data data

    echo "Data directory linked to persistent disk"
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

# Wait for backend
sleep 3

# Start single multi-page Streamlit app on Render's PORT
streamlit run dashboards/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false --server.fileWatcherType none
