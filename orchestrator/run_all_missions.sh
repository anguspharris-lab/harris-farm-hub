#!/bin/bash
# Harris Farm Hub — Run All Non-Operational Features Through Autonomous Pipeline
#
# Executes missions in dependency order. Each mission is independent but
# ordered from foundational → dependent for safety.
#
# Usage:
#   bash orchestrator/run_all_missions.sh              # Run all
#   bash orchestrator/run_all_missions.sh --dry-run    # Validate only
#   bash orchestrator/run_all_missions.sh --mission 3  # Run single mission by number

set -e
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

DRY_RUN=""
SINGLE_MISSION=""
if [ "$1" = "--dry-run" ]; then DRY_RUN="--dry-run"; fi
if [ "$1" = "--mission" ]; then SINGLE_MISSION="$2"; fi

echo "=============================================="
echo "  Harris Farm Hub — Autonomous Mission Runner"
echo "  $(date)"
echo "=============================================="

# Mission execution order (foundational → dependent)
MISSIONS=(
  "1:cleanup_hardening.json:Codebase Cleanup & Hardening"
  "2:phase3_watchdog_integration.json:Phase 3 — WATCHDOG Approval Integration"
  "3:phase4_gamification_activation.json:Phase 4 — Gamification Activation"
  "4:arena_competition_ui.json:Arena Competition UI"
  "5:rbac_enforcement.json:Role-Based Access Control"
  "6:report_export_formats.json:Report Export Formats (HTML/MD/PDF)"
  "7:task_dependencies_parallel.json:Task Dependencies & Parallel Execution"
  "8:phase5_ab_testing.json:Phase 5 — A/B Testing Framework"
  "9:weather_integration.json:Weather Module Integration"
)

PASSED=0
FAILED=0
SKIPPED=0

for entry in "${MISSIONS[@]}"; do
  IFS=':' read -r num file name <<< "$entry"

  # Skip if running single mission and this isn't it
  if [ -n "$SINGLE_MISSION" ] && [ "$num" != "$SINGLE_MISSION" ]; then
    continue
  fi

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Mission $num: $name"
  echo "  File: orchestrator/missions/$file"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  MISSION_PATH="orchestrator/missions/$file"

  if [ ! -f "$MISSION_PATH" ]; then
    echo "  SKIP — File not found"
    ((SKIPPED++))
    continue
  fi

  echo "[RUNNER] $(date -Iseconds) | Starting mission $num: $name" >> watchdog/audit.log

  if python3 orchestrator/run.py "$MISSION_PATH" $DRY_RUN --max-parallel 2 --timeout 600; then
    echo "  ✅ Mission $num PASSED"
    echo "[RUNNER] $(date -Iseconds) | Mission $num PASSED: $name" >> watchdog/audit.log
    ((PASSED++))
  else
    echo "  ❌ Mission $num FAILED"
    echo "[RUNNER] $(date -Iseconds) | Mission $num FAILED: $name" >> watchdog/audit.log
    ((FAILED++))

    # Don't abort on failure — continue with next mission
    echo "  Continuing with next mission..."
  fi

  # Brief pause between missions
  if [ -z "$DRY_RUN" ]; then
    echo "  ⏳ Cooling down 10s before next mission..."
    sleep 10
  fi
done

echo ""
echo "=============================================="
echo "  MISSION RUNNER COMPLETE"
echo "=============================================="
echo "  Passed:  $PASSED"
echo "  Failed:  $FAILED"
echo "  Skipped: $SKIPPED"
echo "  Total:   $((PASSED + FAILED + SKIPPED))"
echo "=============================================="
echo "[RUNNER] $(date -Iseconds) | All missions complete: $PASSED passed, $FAILED failed, $SKIPPED skipped" >> watchdog/audit.log
