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
