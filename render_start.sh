#!/bin/bash
# Start FastAPI backend in background
cd /opt/render/project/src
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to start
sleep 3

# Start Streamlit frontend
streamlit run dashboards/landing.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
