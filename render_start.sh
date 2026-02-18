#!/bin/bash
# Start FastAPI backend on internal port 8000
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &

# Wait for backend
sleep 3

# Start Streamlit on Render's PORT (this is the public-facing port)
streamlit run dashboards/landing.py --server.port ${PORT:-10000} --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false
