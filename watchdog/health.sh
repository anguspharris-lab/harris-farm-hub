#!/bin/bash
P=0;F=0;SERVICES=("api:8000" "hub:8500")
for S in "${SERVICES[@]}"; do
  NAME="${S%%:*}"; PORT="${S##*:}"
  CODE=$(curl -so/dev/null -w"%{http_code}" --max-time 3 http://localhost:$PORT 2>/dev/null)
  if echo "$CODE"|grep -q "200\|302"; then echo "✅ $NAME:$PORT"; ((P++))
  else
    sleep 2
    CODE=$(curl -so/dev/null -w"%{http_code}" --max-time 3 http://localhost:$PORT 2>/dev/null)
    if echo "$CODE"|grep -q "200\|302"; then echo "✅ $NAME:$PORT (retry)"; ((P++))
    else echo "❌ $NAME:$PORT (code:$CODE)"; ((F++)); fi
  fi
done
echo "---"; echo "$P up $F down"
if [ $F -eq 0 ]; then echo "🟢 ALL HEALTHY"
elif [ $P -eq 0 ]; then
  echo "⚠️ ALL DOWN — possible restart. Waiting 30s..."
  sleep 30; P2=0;F2=0
  for S in "${SERVICES[@]}"; do PORT="${S##*:}"
    CODE=$(curl -so/dev/null -w"%{http_code}" --max-time 3 http://localhost:$PORT 2>/dev/null)
    echo "$CODE"|grep -q "200\|302" && ((P2++)) || ((F2++))
  done
  [ $F2 -eq 0 ] && echo "🟢 ALL HEALTHY (after restart)" || echo "🔴 $F2 STILL DOWN"
else echo "🔴 $F SERVICE(S) DOWN"; fi
