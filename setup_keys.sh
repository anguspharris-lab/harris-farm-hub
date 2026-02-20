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
pkill -f "uvicorn" 2>/dev/null
sleep 2

export PATH="/Users/angusharris/Library/Python/3.9/bin:$PATH"
cd "$HUB_DIR"
mkdir -p logs

# Start API
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
sleep 3

# Start single Hub app
streamlit run dashboards/app.py \
    --server.port 8500 \
    --server.headless true \
    --server.address 0.0.0.0 \
    --server.fileWatcherType none \
    > logs/hub.log 2>&1 &
sleep 4

echo ""
echo "═══════════════════════════════════════════════════"
echo "  🍎 HARRIS FARM HUB — SERVICES RUNNING"
echo "═══════════════════════════════════════════════════"
echo ""

for port in 8000 8500; do
    code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port)
    if [ "$code" = "200" ] || [ "$code" = "302" ]; then
        status="✅"
    else
        status="❌"
    fi
    case $port in
        8000) name="API Backend  " ;;
        8500) name="Hub          " ;;
    esac
    echo "  $status $name http://localhost:$port"
done

echo ""
echo "  Opening Hub..."
open http://localhost:8500

echo ""
echo "═══════════════════════════════════════════════════"
echo ""
