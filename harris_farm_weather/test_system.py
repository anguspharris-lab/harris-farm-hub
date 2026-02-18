#!/usr/bin/env python3
"""
Harris Farm Weather — System Test Suite
Verifies database, configuration, module imports, and integration.
"""

import os
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

PASS = "\033[92m\u2713\033[0m"  # green tick
FAIL = "\033[91m\u2717\033[0m"  # red cross
passed = 0
failed = 0


def check(description, condition):
    global passed, failed
    if condition:
        print(f"  {PASS}  {description}")
        passed += 1
    else:
        print(f"  {FAIL}  {description}")
        failed += 1


# =========================================================================
# 1. Database Existence & Tables
# =========================================================================

print("\n=== Database Tests ===")

db_path = Path("weather.db")
check("weather.db exists", db_path.exists())

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}

    expected_tables = [
        "stores", "weather_observations", "weather_forecasts",
        "weather_impact_categories", "product_weather_profiles",
        "daily_weather_summary", "store_weather_correlations",
    ]
    for t in expected_tables:
        check(f"Table '{t}' exists", t in tables)

    # Views
    views = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='view'"
    ).fetchall()}
    for v in ["v_latest_forecast", "v_weather_impact_dashboard", "v_7day_forecast"]:
        check(f"View '{v}' exists", v in views)

    conn.close()


# =========================================================================
# 2. Data Population
# =========================================================================

print("\n=== Data Population Tests ===")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    store_count = conn.execute("SELECT COUNT(*) AS n FROM stores").fetchone()["n"]
    check(f"Stores loaded ({store_count})", store_count >= 5)

    cat_count = conn.execute(
        "SELECT COUNT(*) AS n FROM weather_impact_categories"
    ).fetchone()["n"]
    check(f"Categories loaded ({cat_count})", cat_count >= 20)

    prod_count = conn.execute(
        "SELECT COUNT(*) AS n FROM product_weather_profiles"
    ).fetchone()["n"]
    check(f"Products loaded ({prod_count})", prod_count >= 40)

    # Spot-check a known product
    ice = conn.execute(
        "SELECT * FROM product_weather_profiles WHERE product_code = 'ICE001'"
    ).fetchone()
    check("ICE001 exists", ice is not None)
    if ice:
        check("ICE001 hot_multiplier = 2.5", abs(ice["hot_multiplier"] - 2.5) < 0.01)
        check("ICE001 cold_multiplier = 0.4", abs(ice["cold_multiplier"] - 0.4) < 0.01)

    # Check a store
    store = conn.execute(
        "SELECT * FROM stores WHERE store_id = 1"
    ).fetchone()
    check("Store 1 (Frenchs Forest) exists", store is not None)
    if store:
        check("Store 1 has valid latitude",
              -34.0 < store["latitude"] < -33.0)

    conn.close()


# =========================================================================
# 3. Module Imports
# =========================================================================

print("\n=== Module Import Tests ===")

try:
    from weather_data_loader import WeatherDataLoader
    check("weather_data_loader imports", True)
except ImportError as e:
    check(f"weather_data_loader imports — {e}", False)

try:
    from weather_demand_planner import WeatherDemandPlanner
    check("weather_demand_planner imports", True)
except ImportError as e:
    check(f"weather_demand_planner imports — {e}", False)

try:
    from weather_dashboard import WeatherDashboard
    check("weather_dashboard imports", True)
except ImportError as e:
    check(f"weather_dashboard imports — {e}", False)

try:
    from example_products import CATEGORIES, PRODUCTS, SAMPLE_STORES
    check("example_products imports", True)
    check(f"Categories defined ({len(CATEGORIES)})", len(CATEGORIES) >= 20)
    check(f"Products defined ({len(PRODUCTS)})", len(PRODUCTS) >= 40)
    check(f"Sample stores defined ({len(SAMPLE_STORES)})", len(SAMPLE_STORES) >= 5)
except ImportError as e:
    check(f"example_products imports — {e}", False)


# =========================================================================
# 4. Integration Tests (no API key required)
# =========================================================================

print("\n=== Integration Tests ===")

try:
    # Test demand calculation without live weather data
    # Insert a fake forecast row so the planner can calculate
    conn = sqlite3.connect(str(db_path))
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    conn.execute(
        """
        INSERT OR REPLACE INTO weather_forecasts
            (store_id, forecast_date, forecast_hour,
             max_temp_c, min_temp_c, avg_temp_c,
             total_precip_mm, avg_humidity_pct, chance_of_rain,
             condition_text, confidence, fetched_at)
        VALUES (1, ?, NULL, 35, 22, 28.5, 0, 45, 10,
                'Sunny', 0.9, datetime('now'))
        """,
        (tomorrow,),
    )
    conn.commit()
    conn.close()

    planner = WeatherDemandPlanner()
    result = planner.get_weather_adjusted_demand(
        store_id=1, product_code="ICE001",
        forecast_date=tomorrow, base_demand=50,
    )
    check("Demand adjustment returns result", result is not None)
    check(f"Adjusted demand = {result['adjusted_demand']} (base 50)",
          result["adjusted_demand"] > 50)
    check(f"Multiplier = {result['multiplier']}",
          result["multiplier"] > 1.0)
    check(f"Weather category = {result['weather_category']}",
          result["weather_category"] in ("HOT", "EXTREME", "SUNNY"))

    # Test high-impact products
    high_impact = planner.get_high_impact_products(1, tomorrow, min_multiplier=1.3)
    check(f"High-impact products found ({len(high_impact)})",
          len(high_impact) > 0)

    # Test weekly alerts
    alerts = planner.generate_weekly_buying_alerts(1)
    check(f"Weekly alerts generated ({len(alerts)})", isinstance(alerts, list))

    # Test store forecast summary
    summary = planner.get_store_weekly_forecast_summary(1)
    check(f"Store forecast summary ({len(summary)} days)", len(summary) >= 1)

    # Test dashboard instantiation
    dashboard = WeatherDashboard()
    check("Dashboard instantiation", dashboard is not None)

    # Test CSV export
    export_path = dashboard.export_buying_report(store_id=1)
    if export_path:
        check(f"CSV export created: {export_path}", Path(export_path).exists())
        # Clean up
        Path(export_path).unlink(missing_ok=True)
    else:
        check("CSV export (no alerts to export)", True)

except Exception as e:
    check(f"Integration test failed: {e}", False)


# =========================================================================
# 5. File Structure
# =========================================================================

print("\n=== File Structure Tests ===")

expected_files = [
    "weather_db_schema.sql",
    "weather_data_loader.py",
    "weather_demand_planner.py",
    "weather_dashboard.py",
    "example_products.py",
    "install.sh",
    "test_system.py",
    "requirements.txt",
]
for f in expected_files:
    check(f"File exists: {f}", Path(f).exists())

for d in ["logs", "backups", "exports"]:
    check(f"Directory exists: {d}/", Path(d).is_dir())


# =========================================================================
# Summary
# =========================================================================

total = passed + failed
print(f"\n{'='*50}")
print(f"  Results: {passed}/{total} passed", end="")
if failed:
    print(f", {failed} FAILED")
else:
    print(" — ALL PASSED")
print(f"{'='*50}\n")

sys.exit(0 if failed == 0 else 1)
