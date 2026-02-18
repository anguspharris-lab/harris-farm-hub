#!/usr/bin/env bash
# Harris Farm Weather — Automation Setup
# Creates cron-ready scripts for daily weather updates, dashboard reports,
# and database backups.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  Harris Farm Weather — Automation Setup"
echo "============================================"
echo

# -------------------------------------------------------
# 1. Daily Weather Update Script
# -------------------------------------------------------

cat > daily_weather_update.py << 'PYEOF'
#!/usr/bin/env python3
"""Daily weather update — designed for cron execution.

Usage:
    python3 daily_weather_update.py

Reads API key from WEATHERAPI_KEY environment variable.
"""
import logging
import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    handlers=[
        logging.FileHandler("logs/weather_update.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("daily_update")

api_key = os.environ.get("WEATHERAPI_KEY")
if not api_key:
    logger.error("WEATHERAPI_KEY environment variable not set")
    sys.exit(1)

try:
    from weather_data_loader import WeatherDataLoader
    loader = WeatherDataLoader()
    total = loader.update_all_store_forecasts(api_key)
    loader.close()
    logger.info("Daily update complete: %d forecast rows", total)
except Exception as e:
    logger.error("Daily update failed: %s", e, exc_info=True)
    sys.exit(1)
PYEOF

chmod +x daily_weather_update.py
echo "  Created: daily_weather_update.py"


# -------------------------------------------------------
# 2. Daily Dashboard Report Script
# -------------------------------------------------------

cat > generate_daily_dashboard.py << 'PYEOF'
#!/usr/bin/env python3
"""Generate daily weather dashboard report — designed for cron execution.

Usage:
    python3 generate_daily_dashboard.py
"""
import logging
import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    handlers=[
        logging.FileHandler("logs/dashboard_report.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("dashboard_report")

try:
    from weather_dashboard import WeatherDashboard
    dashboard = WeatherDashboard()
    dashboard.run_full_dashboard()
    dashboard.export_buying_report()
    logger.info("Dashboard report complete")
except Exception as e:
    logger.error("Dashboard report failed: %s", e, exc_info=True)
    sys.exit(1)
PYEOF

chmod +x generate_daily_dashboard.py
echo "  Created: generate_daily_dashboard.py"


# -------------------------------------------------------
# 3. Database Backup Script
# -------------------------------------------------------

cat > backup_weather_db.sh << 'SHEOF'
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
SHEOF

chmod +x backup_weather_db.sh
echo "  Created: backup_weather_db.sh"


# -------------------------------------------------------
# 4. Print crontab suggestions
# -------------------------------------------------------

echo
echo "============================================"
echo "  Suggested crontab entries"
echo "============================================"
echo
echo "# Harris Farm Weather — Automation"
echo "# Edit with: crontab -e"
echo
echo "# 6:00 AM — Fetch fresh forecasts"
echo "0 6 * * * cd $SCRIPT_DIR && WEATHERAPI_KEY=YOUR_KEY_HERE python3 daily_weather_update.py >> logs/cron.log 2>&1"
echo
echo "# 7:00 AM — Generate morning report + CSV export"
echo "0 7 * * * cd $SCRIPT_DIR && python3 generate_daily_dashboard.py >> logs/cron.log 2>&1"
echo
echo "# 11:00 PM — Database backup"
echo "0 23 * * * cd $SCRIPT_DIR && bash backup_weather_db.sh >> logs/cron.log 2>&1"
echo
echo "Replace YOUR_KEY_HERE with your WeatherAPI.com key."
echo
