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
