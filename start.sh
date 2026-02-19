#!/bin/bash
# Harris Farm Hub — Start Script
# Sets up environment, downloads data, and launches API + single Streamlit app.

set -e

echo "==========================================="
echo "  Harris Farm Hub — Starting"
echo "==========================================="

# ---- Virtual environment (avoids Nix externally-managed-environment error) ----
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# ---- Install dependencies (cached after first run) ----
if [ ! -f .deps_installed ]; then
    echo ""
    echo "Installing Python dependencies..."
    pip install -q -r requirements.txt
    touch .deps_installed
    echo "Dependencies installed."
fi

# ---- Create .env from Replit secrets if not present ----
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env from environment..."
    cat > .env << EOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-your_key_here}
OPENAI_API_KEY=${OPENAI_API_KEY:-your_key_here}
AUTH_ENABLED=${AUTH_ENABLED:-false}
AUTH_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
API_URL=http://localhost:8000
EOF
    echo ".env created. Set API keys in Secrets tab."
fi

# ---- Download data files if missing ----
echo ""
echo "Checking data files..."
python3 data_loader.py

mkdir -p logs

# ---- Start Backend API ----
echo ""
echo "Starting Backend API (port 8000)..."
cd backend
python3 app.py > ../logs/api.log 2>&1 &
API_PID=$!
cd ..
sleep 2

if ps -p $API_PID > /dev/null 2>&1; then
    echo "  API running (PID $API_PID)"
else
    echo "  API failed — check logs/api.log"
fi

# ---- Start Single Multi-Page Streamlit App ----
echo ""
echo "Starting Hub (port 8500)..."
streamlit run dashboards/app.py \
    --server.port 8500 \
    --server.headless true \
    --server.address 0.0.0.0 \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --server.fileWatcherType none \
    > logs/hub.log 2>&1 &
HUB_PID=$!
sleep 2

if ps -p $HUB_PID > /dev/null 2>&1; then
    echo "  Hub running (PID $HUB_PID)"
else
    echo "  Hub failed — check logs/hub.log"
fi

echo ""
echo "==========================================="
echo "  All services started!"
echo "==========================================="
echo ""
echo "  Hub:  http://localhost:8500"
echo "  API:  http://localhost:8000"
echo ""

# Keep the script running
wait
