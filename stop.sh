#!/bin/bash

# Harris Farm Hub - Stop Script

echo "🛑 Stopping Harris Farm Hub services..."

if [ -f .hub_pids ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping process $pid..."
            kill $pid 2>/dev/null
        fi
    done < .hub_pids
    
    rm .hub_pids
    echo "✅ All services stopped"
else
    echo "⚠️  No running services found"
    
    # Try to find and kill any remaining processes
    echo "Checking for orphaned processes..."
    pkill -f "streamlit run" 2>/dev/null
    pkill -f "uvicorn" 2>/dev/null
    pkill -f "app.py" 2>/dev/null
    echo "✅ Cleanup complete"
fi

echo ""
echo "Hub services have been stopped."
