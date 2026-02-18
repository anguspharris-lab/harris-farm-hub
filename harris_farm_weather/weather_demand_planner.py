"""
Harris Farm Weather — Demand Planner
Calculates weather-adjusted demand, identifies high-impact products,
and generates weekly buying alerts with lead-time awareness.
"""

import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "weather.db"

logger = logging.getLogger("weather_planner")


class WeatherDemandPlanner:
    """Weather-driven demand adjustment engine."""

    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH

    def _get_conn(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Core: calculate adjusted demand for a single product on a date
    # ------------------------------------------------------------------

    def get_weather_adjusted_demand(self, store_id, product_code,
                                    forecast_date, base_demand):
        """Return demand adjusted by weather conditions.

        Args:
            store_id: integer store identifier.
            product_code: product code from product_weather_profiles.
            forecast_date: date string (YYYY-MM-DD) or datetime.date.
            base_demand: baseline daily demand quantity.

        Returns:
            dict with keys: adjusted_demand, multiplier, weather_factors,
            confidence, weather_category, max_temp_c, total_precip_mm.
        """
        if isinstance(forecast_date, date):
            forecast_date = forecast_date.isoformat()

        conn = self._get_conn()
        try:
            # product profile
            profile = conn.execute(
                "SELECT * FROM product_weather_profiles WHERE product_code = ?",
                (product_code,),
            ).fetchone()
            if not profile:
                return {
                    "adjusted_demand": base_demand,
                    "multiplier": 1.0,
                    "weather_factors": "Product not configured",
                    "confidence": 0.0,
                    "weather_category": "UNKNOWN",
                    "max_temp_c": None,
                    "total_precip_mm": None,
                }

            # forecast for the store/date
            forecast = conn.execute(
                """
                SELECT max_temp_c, min_temp_c, avg_temp_c,
                       total_precip_mm, avg_humidity_pct, condition_text,
                       confidence
                FROM weather_forecasts
                WHERE store_id = ? AND forecast_date = ? AND forecast_hour IS NULL
                ORDER BY fetched_at DESC LIMIT 1
                """,
                (store_id, forecast_date),
            ).fetchone()

            if not forecast:
                return {
                    "adjusted_demand": base_demand,
                    "multiplier": 1.0,
                    "weather_factors": f"No forecast for store {store_id} on {forecast_date}",
                    "confidence": 0.0,
                    "weather_category": "UNKNOWN",
                    "max_temp_c": None,
                    "total_precip_mm": None,
                }

            max_temp = forecast["max_temp_c"] or 20
            precip = forecast["total_precip_mm"] or 0
            confidence = forecast["confidence"] or 0.8

            multiplier, factors = self._calculate_multiplier(
                max_temp, precip, profile,
            )

            # clamp
            multiplier = max(profile["min_multiplier"],
                             min(profile["max_multiplier"], multiplier))

            adjusted = round(base_demand * multiplier)

            # determine weather category
            if max_temp >= 38:
                category = "EXTREME"
            elif max_temp >= 30:
                category = "HOT"
            elif max_temp < 15:
                category = "COLD"
            elif precip > 5:
                category = "WET"
            elif 20 <= max_temp <= 28 and precip < 2:
                category = "SUNNY"
            else:
                category = "MILD"

            return {
                "adjusted_demand": adjusted,
                "multiplier": round(multiplier, 2),
                "weather_factors": factors,
                "confidence": round(confidence, 2),
                "weather_category": category,
                "max_temp_c": max_temp,
                "total_precip_mm": precip,
            }
        finally:
            conn.close()

    @staticmethod
    def _calculate_multiplier(max_temp, precip, profile):
        """Apply multiplier rules and return (multiplier, description).

        Rules (compound):
            >38 C → extreme_heat_multiplier
            >30 C → hot_multiplier
            <15 C → cold_multiplier
            >5 mm rain → rain_multiplier
            20-28 C + <2 mm rain → sunny_multiplier
        """
        multiplier = 1.0
        parts = []

        if max_temp >= 38:
            multiplier *= profile["extreme_heat_multiplier"]
            parts.append(f"Extreme heat {max_temp:.0f}C (x{profile['extreme_heat_multiplier']})")
        elif max_temp >= 30:
            multiplier *= profile["hot_multiplier"]
            parts.append(f"Hot day {max_temp:.0f}C (x{profile['hot_multiplier']})")
        elif max_temp < 15:
            multiplier *= profile["cold_multiplier"]
            parts.append(f"Cold day {max_temp:.0f}C (x{profile['cold_multiplier']})")
        elif 20 <= max_temp <= 28 and precip < 2:
            multiplier *= profile["sunny_multiplier"]
            parts.append(f"Sunny day {max_temp:.0f}C (x{profile['sunny_multiplier']})")

        if precip > 5:
            multiplier *= profile["rain_multiplier"]
            parts.append(f"Rain {precip:.1f}mm (x{profile['rain_multiplier']})")

        if not parts:
            parts.append(f"Mild conditions {max_temp:.0f}C, {precip:.1f}mm rain")

        return multiplier, "; ".join(parts)

    # ------------------------------------------------------------------
    # High-impact products for a given store/date
    # ------------------------------------------------------------------

    def get_high_impact_products(self, store_id, forecast_date,
                                 min_multiplier=1.3):
        """List products whose weather multiplier exceeds a threshold.

        Args:
            store_id: store identifier.
            forecast_date: YYYY-MM-DD string or date.
            min_multiplier: minimum multiplier to include (default 1.3 = +30%).

        Returns:
            list of dicts sorted by abs(multiplier − 1) descending.
        """
        if isinstance(forecast_date, date):
            forecast_date = forecast_date.isoformat()

        conn = self._get_conn()
        try:
            products = conn.execute(
                "SELECT * FROM product_weather_profiles WHERE is_active = 1"
            ).fetchall()

            forecast = conn.execute(
                """
                SELECT max_temp_c, total_precip_mm, confidence, condition_text
                FROM weather_forecasts
                WHERE store_id = ? AND forecast_date = ? AND forecast_hour IS NULL
                ORDER BY fetched_at DESC LIMIT 1
                """,
                (store_id, forecast_date),
            ).fetchone()

            if not forecast:
                return []

            max_temp = forecast["max_temp_c"] or 20
            precip = forecast["total_precip_mm"] or 0

            results = []
            for p in products:
                mult, factors = self._calculate_multiplier(max_temp, precip, p)
                mult = max(p["min_multiplier"], min(p["max_multiplier"], mult))

                if mult >= min_multiplier or mult <= (1.0 / min_multiplier):
                    results.append({
                        "product_code": p["product_code"],
                        "product_name": p["product_name"],
                        "multiplier": round(mult, 2),
                        "pct_change": round((mult - 1) * 100, 1),
                        "weather_factors": factors,
                        "lead_days": p["replenishment_lead_days"],
                    })

            results.sort(key=lambda x: abs(x["multiplier"] - 1), reverse=True)
            return results
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Weekly buying alerts with lead-time awareness
    # ------------------------------------------------------------------

    def generate_weekly_buying_alerts(self, store_id):
        """Generate actionable buying alerts for the forecast window.

        For each product with significant weather impact, calculates:
        - the demand-impacted date
        - the latest order date (accounting for lead time)
        - whether the order date has already passed

        Returns:
            list of alert dicts sorted by order_by date.
        """
        conn = self._get_conn()
        try:
            forecasts = conn.execute(
                """
                SELECT forecast_date, max_temp_c, total_precip_mm, confidence
                FROM weather_forecasts
                WHERE store_id = ? AND forecast_hour IS NULL
                  AND forecast_date >= date('now')
                ORDER BY forecast_date
                """,
                (store_id,),
            ).fetchall()

            products = conn.execute(
                "SELECT * FROM product_weather_profiles WHERE is_active = 1"
            ).fetchall()

            if not forecasts or not products:
                return []

            today = date.today()
            alerts = []

            for fc in forecasts:
                fc_date_str = fc["forecast_date"]
                fc_date = datetime.strptime(fc_date_str, "%Y-%m-%d").date()
                max_temp = fc["max_temp_c"] or 20
                precip = fc["total_precip_mm"] or 0
                confidence = fc["confidence"] or 0.8

                for p in products:
                    mult, factors = self._calculate_multiplier(max_temp, precip, p)
                    mult = max(p["min_multiplier"], min(p["max_multiplier"], mult))

                    if mult < 1.3 and mult > 0.7:
                        continue  # no significant impact

                    lead = p["replenishment_lead_days"]
                    order_by = fc_date - timedelta(days=lead)
                    urgency = "PAST DUE" if order_by < today else (
                        "TODAY" if order_by == today else (
                            "TOMORROW" if order_by == today + timedelta(days=1) else
                            f"in {(order_by - today).days}d"
                        )
                    )

                    alerts.append({
                        "product_code": p["product_code"],
                        "product_name": p["product_name"],
                        "impact_date": fc_date_str,
                        "order_by": order_by.isoformat(),
                        "urgency": urgency,
                        "multiplier": round(mult, 2),
                        "pct_change": round((mult - 1) * 100, 1),
                        "weather_factors": factors,
                        "confidence": round(confidence, 2),
                        "lead_days": lead,
                    })

            alerts.sort(key=lambda a: a["order_by"])
            return alerts
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Store weekly forecast summary
    # ------------------------------------------------------------------

    def get_store_weekly_forecast_summary(self, store_id):
        """Return a 7-day weather outlook for a store.

        Returns:
            list of dicts with date, temps, rain, category, condition.
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT forecast_date, max_temp_c, min_temp_c, avg_temp_c,
                       total_precip_mm, chance_of_rain, avg_humidity_pct,
                       condition_text, confidence
                FROM weather_forecasts
                WHERE store_id = ? AND forecast_hour IS NULL
                  AND forecast_date >= date('now')
                ORDER BY forecast_date
                LIMIT 7
                """,
                (store_id,),
            ).fetchall()

            result = []
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

                fc_date = datetime.strptime(r["forecast_date"], "%Y-%m-%d")
                result.append({
                    "date": r["forecast_date"],
                    "day_name": fc_date.strftime("%A"),
                    "max_temp_c": r["max_temp_c"],
                    "min_temp_c": r["min_temp_c"],
                    "total_precip_mm": r["total_precip_mm"],
                    "chance_of_rain": r["chance_of_rain"],
                    "condition": r["condition_text"],
                    "confidence": r["confidence"],
                    "weather_category": cat,
                })
            return result
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    planner = WeatherDemandPlanner()

    print("=== Weekly Forecast — Store 1 ===")
    for day in planner.get_store_weekly_forecast_summary(1):
        print(f"  {day['day_name']:10s} {day['date']}  "
              f"{day['max_temp_c']:.0f}C  {day['total_precip_mm']:.1f}mm  "
              f"{day['weather_category']}")

    print("\n=== High-Impact Products — Store 1, Tomorrow ===")
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    for p in planner.get_high_impact_products(1, tomorrow):
        print(f"  {p['product_name']:30s}  x{p['multiplier']:.2f}  "
              f"({p['pct_change']:+.0f}%)  {p['weather_factors']}")

    print("\n=== Buying Alerts — Store 1 ===")
    for a in planner.generate_weekly_buying_alerts(1):
        print(f"  [{a['urgency']:10s}] {a['product_name']:30s}  "
              f"x{a['multiplier']:.2f}  order by {a['order_by']}  "
              f"for {a['impact_date']}")
