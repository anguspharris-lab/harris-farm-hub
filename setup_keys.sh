#!/bin/bash
# Harris Farm Hub - API Key Setup (paste-friendly)

ENV_FILE="$(dirname "$0")/.env"
HUB_DIR="$(dirname "$0")"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  🍎 Harris Farm Hub — API Key Setup"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  Paste each key and press Enter."
echo "  Press Enter with no input to skip."
echo ""

# Anthropic
echo "Anthropic (Claude) API key:"
echo -n "  > "
read CLAUDE_KEY
if [ -n "$CLAUDE_KEY" ]; then
    sed -i '' "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$CLAUDE_KEY|" "$ENV_FILE"
    echo "  ✅ Saved"
else
    echo "  ⏭  Skipped"
fi
echo ""

# OpenAI
echo "OpenAI API key (Enter to keep existing):"
echo -n "  > "
read OPENAI_KEY
if [ -n "$OPENAI_KEY" ]; then
    sed -i '' "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_KEY|" "$ENV_FILE"
    echo "  ✅ Saved"
else
    echo "  ⏭  Kept existing"
fi
echo ""

# Grok
echo "Grok (xAI) API key (Enter to skip):"
echo -n "  > "
read GROK_KEY
if [ -n "$GROK_KEY" ]; then
    sed -i '' "s|^GROK_API_KEY=.*|GROK_API_KEY=$GROK_KEY|" "$ENV_FILE"
    echo "  ✅ Saved"
else
    echo "  ⏭  Skipped"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Restarting Hub..."
echo "═══════════════════════════════════════════════════"
echo ""

# Stop everything
pkill -f "streamlit run" 2>/dev/null
pkill -f "app.py" 2>/dev/null
sleep 2

export PATH="/Users/angusharris/Library/Python/3.9/bin:$PATH"
cd "$HUB_DIR"
mkdir -p logs

# Start API
cd backend
python3 app.py > ../logs/api.log 2>&1 &
cd ..
sleep 3

# Start dashboards
cd dashboards
streamlit run sales_dashboard.py --server.port 8501 --server.headless true > ../logs/sales.log 2>&1 &
sleep 2
streamlit run profitability_dashboard.py --server.port 8502 --server.headless true > ../logs/profit.log 2>&1 &
sleep 2
streamlit run transport_dashboard.py --server.port 8503 --server.headless true > ../logs/transport.log 2>&1 &
sleep 2
streamlit run prompt_builder.py --server.port 8504 --server.headless true > ../logs/builder.log 2>&1 &
cd ..

sleep 8

echo ""
echo "═══════════════════════════════════════════════════"
echo "  🍎 HARRIS FARM HUB — ALL SERVICES RUNNING"
echo "═══════════════════════════════════════════════════"
echo ""

for port in 8000 8501 8502 8503 8504; do
    code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port)
    if [ "$code" = "200" ]; then
        status="✅"
    else
        status="❌"
    fi
    case $port in
        8000) name="API Backend        " ;;
        8501) name="Sales Dashboard    " ;;
        8502) name="Profitability      " ;;
        8503) name="Transport          " ;;
        8504) name="Prompt Builder     " ;;
    esac
    echo "  $status $name http://localhost:$port"
done

echo ""
echo "  Opening Sales Dashboard..."
open http://localhost:8501

echo ""
echo "═══════════════════════════════════════════════════"
echo ""
