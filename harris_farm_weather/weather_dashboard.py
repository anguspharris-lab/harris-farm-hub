"""
Harris Farm Weather — Dashboard & Reporting
Generates morning reports, urgent buying alerts, category impact summaries,
and CSV exports for integration with ordering systems.
"""

import csv
import logging
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "weather.db"
EXPORTS_DIR = BASE_DIR / "exports"

logger = logging.getLogger("weather_dashboard")


# Weather category emoji mapping
CATEGORY_EMOJI = {
    "EXTREME": "\U0001f525",   # fire
    "HOT":     "\u2600\ufe0f", # sun
    "COLD":    "\u2744\ufe0f", # snowflake
    "WET":     "\U0001f327\ufe0f", # rain
    "SUNNY":   "\U0001f31e",   # sun face
    "MILD":    "\u26c5",       # partly cloudy
    "UNKNOWN": "\u2753",       # question mark
}


class WeatherDashboard:
    """Terminal-based weather dashboard and report generator."""

    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH

    def _get_conn(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # 1. Today's Weather Overview — all stores
    # ------------------------------------------------------------------

    def today_weather_overview(self):
        """Print current weather conditions for all active stores."""
        today_str = date.today().isoformat()
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT s.store_id, s.name, s.suburb,
                       f.max_temp_c, f.min_temp_c, f.total_precip_mm,
                       f.chance_of_rain, f.condition_text, f.confidence
                FROM weather_forecasts f
                JOIN stores s ON s.store_id = f.store_id
                WHERE f.forecast_date = ? AND f.forecast_hour IS NULL
                  AND s.is_active = 1
                ORDER BY f.max_temp_c DESC
                """,
                (today_str,),
            ).fetchall()

            print(f"\n{'='*70}")
            print(f"  HARRIS FARM WEATHER OVERVIEW — {today_str}")
            print(f"{'='*70}")

            if not rows:
                print("  No forecast data for today. Run weather update first.")
                return

            for r in rows:
                max_t = r["max_temp_c"] or 0
                precip = r["total_precip_mm"] or 0

                if max_t >= 38:
                    cat = "EXTREME"
                elif max_t >= 30:
                    cat = "HOT"
                elif max_t < 15:
                    cat = "COLD"
                elif precip > 5:
                    cat = "WET"
                elif 20 <= max_t <= 28 and precip < 2:
                    cat = "SUNNY"
                else:
                    cat = "MILD"

                emoji = CATEGORY_EMOJI.get(cat, "")
                print(f"  {emoji} {r['name']:20s}  {max_t:5.1f}C  "
                      f"{precip:5.1f}mm  {cat:8s}  "
                      f"{r['condition_text'] or ''}")

            print()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 2. Urgent Buying Alerts
    # ------------------------------------------------------------------

    def urgent_buying_alerts(self, days_ahead=3):
        """Show products needing immediate orders across all stores.

        Args:
            days_ahead: how far ahead to look for impact dates.
        """
        from weather_demand_planner import WeatherDemandPlanner
        planner = WeatherDemandPlanner(self.db_path)
        conn = self._get_conn()
        today = date.today()

        try:
            stores = conn.execute(
                "SELECT store_id, name FROM stores WHERE is_active = 1"
            ).fetchall()

            print(f"\n{'='*70}")
            print(f"  URGENT BUYING ALERTS — Next {days_ahead} days")
            print(f"{'='*70}")

            any_alerts = False
            for s in stores:
                alerts = planner.generate_weekly_buying_alerts(s["store_id"])
                # filter to urgent (order_by <= today + days_ahead)
                cutoff = (today + timedelta(days=days_ahead)).isoformat()
                urgent = [a for a in alerts if a["order_by"] <= cutoff]
                if not urgent:
                    continue

                any_alerts = True
                print(f"\n  --- {s['name']} ---")
                for a in urgent:
                    arrow = "\u2191" if a["multiplier"] > 1 else "\u2193"
                    print(f"    [{a['urgency']:10s}] {a['product_name']:30s}  "
                          f"{arrow} x{a['multiplier']:.2f} ({a['pct_change']:+.0f}%)  "
                          f"order by {a['order_by']}")

            if not any_alerts:
                print("  No urgent alerts. All products within normal ranges.")
            print()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 3. High-Impact Products Today
    # ------------------------------------------------------------------

    def high_impact_products_today(self, threshold_pct=50):
        """Show products with > threshold_pct demand change today.

        Args:
            threshold_pct: minimum absolute percent change to report.
        """
        from weather_demand_planner import WeatherDemandPlanner
        planner = WeatherDemandPlanner(self.db_path)
        conn = self._get_conn()
        today_str = date.today().isoformat()
        min_mult = 1 + threshold_pct / 100

        try:
            stores = conn.execute(
                "SELECT store_id, name FROM stores WHERE is_active = 1"
            ).fetchall()

            print(f"\n{'='*70}")
            print(f"  HIGH-IMPACT PRODUCTS TODAY (>{threshold_pct}% change)")
            print(f"{'='*70}")

            any_found = False
            for s in stores:
                products = planner.get_high_impact_products(
                    s["store_id"], today_str, min_multiplier=min_mult,
                )
                if not products:
                    continue

                any_found = True
                print(f"\n  --- {s['name']} ---")
                for p in products:
                    arrow = "\u2191" if p["multiplier"] > 1 else "\u2193"
                    print(f"    {arrow} {p['product_name']:30s}  "
                          f"x{p['multiplier']:.2f} ({p['pct_change']:+.0f}%)  "
                          f"{p['weather_factors']}")

            if not any_found:
                print("  No products exceeding threshold today.")
            print()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 4. Category Impact Summary
    # ------------------------------------------------------------------

    def category_impact_summary(self, days=3):
        """Department-level weather impact forecast.

        Shows average multiplier direction per category for the next N days.

        Args:
            days: number of days to include.
        """
        from weather_demand_planner import WeatherDemandPlanner
        planner = WeatherDemandPlanner(self.db_path)
        conn = self._get_conn()

        try:
            # get forecast dates
            today = date.today()
            dates = [(today + timedelta(days=d)).isoformat() for d in range(days)]

            # use first active store as representative
            store = conn.execute(
                "SELECT store_id FROM stores WHERE is_active = 1 LIMIT 1"
            ).fetchone()
            if not store:
                print("  No active stores.")
                return

            # get categories
            categories = conn.execute(
                """
                SELECT c.category_id, c.category_name, c.department
                FROM weather_impact_categories c
                ORDER BY c.department, c.category_name
                """
            ).fetchall()

            # get products per category
            products = conn.execute(
                "SELECT * FROM product_weather_profiles WHERE is_active = 1"
            ).fetchall()

            cat_products = {}
            for p in products:
                cid = p["category_id"]
                if cid not in cat_products:
                    cat_products[cid] = []
                cat_products[cid].append(p)

            print(f"\n{'='*70}")
            print(f"  CATEGORY IMPACT SUMMARY — Next {days} days")
            print(f"{'='*70}")

            current_dept = None
            for cat in categories:
                if cat["department"] != current_dept:
                    current_dept = cat["department"]
                    print(f"\n  [{current_dept}]")

                prods = cat_products.get(cat["category_id"], [])
                if not prods:
                    continue

                # average multiplier across dates and products
                total_mult = 0
                count = 0
                for d_str in dates:
                    forecast = conn.execute(
                        """
                        SELECT max_temp_c, total_precip_mm
                        FROM weather_forecasts
                        WHERE store_id = ? AND forecast_date = ?
                          AND forecast_hour IS NULL
                        ORDER BY fetched_at DESC LIMIT 1
                        """,
                        (store["store_id"], d_str),
                    ).fetchone()

                    if not forecast:
                        continue

                    max_temp = forecast["max_temp_c"] or 20
                    precip = forecast["total_precip_mm"] or 0

                    for p in prods:
                        m, _ = planner._calculate_multiplier(max_temp, precip, p)
                        m = max(p["min_multiplier"], min(p["max_multiplier"], m))
                        total_mult += m
                        count += 1

                if count == 0:
                    continue

                avg_mult = total_mult / count
                pct = (avg_mult - 1) * 100
                arrow = "\u2191" if pct > 5 else ("\u2193" if pct < -5 else "\u2194")
                print(f"    {arrow} {cat['category_name']:35s}  "
                      f"avg x{avg_mult:.2f} ({pct:+.0f}%)")

            print()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 5. Full Dashboard (morning report)
    # ------------------------------------------------------------------

    def run_full_dashboard(self):
        """Run the complete morning weather report."""
        print("\n" + "=" * 70)
        print("  HARRIS FARM MARKETS — WEATHER INTELLIGENCE REPORT")
        print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)

        self.today_weather_overview()
        self.high_impact_products_today()
        self.urgent_buying_alerts(days_ahead=3)
        self.category_impact_summary(days=3)

        print("=" * 70)
        print("  END OF REPORT")
        print("=" * 70)

    # ------------------------------------------------------------------
    # 6. CSV Export
    # ------------------------------------------------------------------

    def export_buying_report(self, store_id=None, output_dir=None):
        """Export buying alerts as CSV for ordering systems.

        Args:
            store_id: specific store (None = all stores).
            output_dir: export directory (defaults to exports/).

        Returns:
            Path to the generated CSV file.
        """
        from weather_demand_planner import WeatherDemandPlanner
        planner = WeatherDemandPlanner(self.db_path)
        conn = self._get_conn()

        out_dir = Path(output_dir) if output_dir else EXPORTS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            if store_id:
                stores = conn.execute(
                    "SELECT store_id, name FROM stores WHERE store_id = ?",
                    (store_id,),
                ).fetchall()
            else:
                stores = conn.execute(
                    "SELECT store_id, name FROM stores WHERE is_active = 1"
                ).fetchall()

            all_alerts = []
            for s in stores:
                alerts = planner.generate_weekly_buying_alerts(s["store_id"])
                for a in alerts:
                    a["store_id"] = s["store_id"]
                    a["store_name"] = s["name"]
                all_alerts.extend(alerts)

            if not all_alerts:
                logger.info("No alerts to export")
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"buying_alerts_{timestamp}.csv"
            filepath = out_dir / filename

            fieldnames = [
                "store_id", "store_name", "product_code", "product_name",
                "impact_date", "order_by", "urgency", "multiplier",
                "pct_change", "weather_factors", "confidence", "lead_days",
            ]
            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames,
                                        extrasaction="ignore")
                writer.writeheader()
                writer.writerows(all_alerts)

            logger.info("Exported %d alerts to %s", len(all_alerts), filepath)
            print(f"  Exported {len(all_alerts)} alerts -> {filepath}")
            return filepath
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    dashboard = WeatherDashboard()
    dashboard.run_full_dashboard()
