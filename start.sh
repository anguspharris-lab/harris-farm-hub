#!/bin/bash
# Harris Farm Hub — Replit Start Script
# Sets up environment, downloads data, and launches all 16 services.

set -e

echo "==========================================="
echo "  Harris Farm Hub — Starting on Replit"
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
    echo "Creating .env from Replit environment..."
    cat > .env << EOF
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-your_key_here}
OPENAI_API_KEY=${OPENAI_API_KEY:-your_key_here}
AUTH_ENABLED=${AUTH_ENABLED:-false}
AUTH_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
API_URL=http://localhost:8000
EOF
    echo ".env created. Set API keys in Replit Secrets tab."
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

# ---- Start Dashboards ----
echo ""
echo "Starting Dashboards..."

DASHBOARDS=(
    "landing.py:8500:Landing"
    "sales_dashboard.py:8501:Sales"
    "profitability_dashboard.py:8502:Profitability"
    "transport_dashboard.py:8503:Transport"
    "prompt_builder.py:8504:Prompt Builder"
    "rubric_dashboard.py:8505:Rubric"
    "trending_dashboard.py:8506:Trending"
    "customer_dashboard.py:8507:Customers"
    "market_share_dashboard.py:8508:Market Share"
    "chatbot_dashboard.py:8509:Hub Assistant"
    "learning_centre.py:8510:Learning Centre"
    "store_ops_dashboard.py:8511:Store Ops"
    "product_intel_dashboard.py:8512:Product Intel"
    "revenue_bridge_dashboard.py:8513:Revenue Bridge"
    "buying_hub_dashboard.py:8514:Buying Hub"
    "hub_portal.py:8515:Hub Portal"
    "greater_goodness.py:8516:Greater Goodness"
)

for entry in "${DASHBOARDS[@]}"; do
    IFS=':' read -r file port name <<< "$entry"
    echo "  Starting $name (port $port)..."
    streamlit run "dashboards/$file" \
        --server.port "$port" \
        --server.headless true \
        --server.address 0.0.0.0 \
        --server.enableCORS false \
        --server.enableXsrfProtection false \
        --server.fileWatcherType none \
        > "logs/${file%.py}.log" 2>&1 &
    sleep 1
done

echo ""
echo "==========================================="
echo "  All services started!"
echo "==========================================="
echo ""
echo "  Hub Home:  port 8500 (primary webview)"
echo "  API:       port 8000"
echo ""
echo "  Set API keys in the Replit Secrets tab:"
echo "    ANTHROPIC_API_KEY"
echo "    OPENAI_API_KEY"
echo ""

# Keep the script running so Replit doesn't stop
wait
