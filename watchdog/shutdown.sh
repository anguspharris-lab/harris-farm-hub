#!/bin/bash
TRIGGER="${1:-MANUAL}"
echo "🚨 SHUTDOWN $(date -Iseconds) | TRIGGER: $TRIGGER" >> watchdog/audit.log
cp watchdog/audit.log watchdog/audit.log.bak 2>/dev/null
pkill -f "uvicorn|streamlit|node|python.*app" 2>/dev/null
cp -r watchdog/ "../WD_EVIDENCE_$(date +%s)/" 2>/dev/null
echo ""
echo "🚨🚨🚨 WATCHDOG EMERGENCY SHUTDOWN 🚨🚨🚨"
echo "Trigger: $TRIGGER"
echo "Evidence preserved. All services killed."
echo "Review watchdog/audit.log before restart."
echo ""
echo "⚠️ Services stopped. Machine NOT shut down (safety override)."
echo "If you need to power off, do so manually."
