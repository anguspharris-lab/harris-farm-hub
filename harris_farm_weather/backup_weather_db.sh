#!/usr/bin/env bash
# Backup weather.db with timestamped filename and 30-day retention.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB="$SCRIPT_DIR/weather.db"
BACKUP_DIR="$SCRIPT_DIR/backups"

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEST="$BACKUP_DIR/weather_${TIMESTAMP}.db"

cp "$DB" "$DEST"
echo "Backup: $DEST ($(du -h "$DEST" | cut -f1))"

# Prune backups older than 30 days
find "$BACKUP_DIR" -name "weather_*.db" -mtime +30 -delete 2>/dev/null || true
echo "Pruned backups older than 30 days"
