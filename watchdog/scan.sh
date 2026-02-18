#!/bin/bash
FAIL=0
FOUND=$(grep -rn "api_key\|password\|secret\|token\|apikey\|api-key\|passwd" \
  --include="*.py" --include="*.js" --include="*.yaml" --include="*.yml" \
  --include="*.json" --include="*.toml" --include="*.cfg" --include="*.ini" \
  --include="*.sh" --include="*.html" . 2>/dev/null | \
  grep -v "node_modules" | grep -v "\.env\.template" | \
  grep -v "os\.environ\|os\.getenv\|process\.env" | \
  grep -v "^\./watchdog/" | grep -v "^\./CLAUDE\.md" | \
  grep -v "^\./orchestrator/safety\.py" | \
  grep -v "secret_patterns\|detects_secret\|review_diff" | \
  grep -v "test_orchestrator\.py" | \
  grep -v "requirements\|package-lock" | grep -v "^\.\/.git/" | \
  grep -v "config\.\|\.config\[" | \
  grep -v "max_tokens\|tokens_used\|total_tokens\|input_tokens\|usage\." | \
  grep -v "tokens INTEGER\|tokens =" | \
  grep -v "your_password\|your_.*_here\|placeholder" | \
  grep -v "Authorization.*Bearer.*self\." | \
  grep -v "api_key=.*if " | \
  grep -v "\.get(" | \
  grep -v "query_id, provider, response, tokens" | \
  grep -v 'tokens}' | \
  grep -v 'token_count\|tokens"')
if [ -n "$FOUND" ]; then echo "🚨 POTENTIAL SECRETS:"; echo "$FOUND"; FAIL=1; fi
if [ -f .env ]; then
  PERMS=$(stat -f "%A" .env 2>/dev/null || stat -c "%a" .env 2>/dev/null)
  [ "$PERMS" != "600" ] && [ "$PERMS" != "400" ] && { chmod 600 .env; echo "⚠️ .env perms fixed→600"; }
fi
[ -d .git ] && ! git check-ignore .env >/dev/null 2>&1 && { echo "🚨 .env NOT gitignored"; FAIL=1; }
[ $FAIL -eq 0 ] && echo "✅ Security scan passed" || { echo "❌ Security FAILED"; exit 1; }
