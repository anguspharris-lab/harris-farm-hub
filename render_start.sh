#!/bin/bash
# Start FastAPI backend on internal port 8000
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 &

# Wait for backend
sleep 3

# Start single multi-page Streamlit app on Render's PORT
streamlit run dashboards/app.py --server.port ${PORT:-10000} --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false --server.fileWatcherType none
