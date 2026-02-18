"""
Harris Farm Weather — Data Loader
Initialises the weather database, manages stores, fetches forecasts from
WeatherAPI.com, records observations, and generates daily summaries.
"""

import json
import logging
import os
import sqlite3
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "weather.db"
SCHEMA_PATH = BASE_DIR / "weather_db_schema.sql"
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
API_PAUSE_SECONDS = 1  # be nice to the free tier

logger = logging.getLogger("weather_loader")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ---------------------------------------------------------------------------
# WeatherDataLoader
# ---------------------------------------------------------------------------

class WeatherDataLoader:
    """Manages the weather SQLite database and populates it from WeatherAPI."""

    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._conn = None

    # -- connection helpers ------------------------------------------------

    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), timeout=30)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # -- database bootstrap ------------------------------------------------

    def initialize_database(self):
        """Create all tables, indexes and views from the schema file."""
        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
        sql = SCHEMA_PATH.read_text()
        conn = self._get_conn()
        conn.executescript(sql)
        conn.commit()
        logger.info("Database initialised at %s", self.db_path)

    # -- store management --------------------------------------------------

    def add_store(self, store_id, name, suburb, state, postcode, lat, lon):
        """Insert or update a store record.

        Args:
            store_id: integer store identifier (matches POS system).
            name: human-readable store name.
            suburb: suburb / locality.
            state: Australian state code (e.g. 'NSW').
            postcode: 4-digit postcode.
            lat: latitude (negative for Southern Hemisphere).
            lon: longitude.
        """
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO stores (store_id, name, suburb, state, postcode, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(store_id) DO UPDATE SET
                name      = excluded.name,
                suburb    = excluded.suburb,
                state     = excluded.state,
                postcode  = excluded.postcode,
                latitude  = excluded.latitude,
                longitude = excluded.longitude,
                updated_at = datetime('now')
            """,
            (store_id, name, suburb, state, postcode, lat, lon),
        )
        conn.commit()
        logger.info("Store %s (%s) added/updated", store_id, name)

    def get_active_stores(self):
        """Return list of dicts for all active stores."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM stores WHERE is_active = 1 ORDER BY store_id"
        ).fetchall()
        return [dict(r) for r in rows]

    # -- weather API -------------------------------------------------------

    def _api_get(self, endpoint, params, api_key):
        """Make a rate-limited GET to WeatherAPI.com."""
        params["key"] = api_key
        url = f"{WEATHERAPI_BASE}/{endpoint}"
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as exc:
            if resp.status_code == 403:
                logger.error("API key rejected (403). Check your WeatherAPI key.")
            elif resp.status_code == 429:
                logger.warning("Rate limited. Waiting 60 s before retry ...")
                time.sleep(60)
                return self._api_get(endpoint, params, api_key)
            else:
                logger.error("HTTP %s: %s", resp.status_code, exc)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("Request failed: %s", exc)
            return None

    # -- fetch & store forecasts -------------------------------------------

    def fetch_forecast(self, store_id, lat, lon, api_key, days=3):
        """Fetch forecast from WeatherAPI and persist to database.

        Args:
            store_id: store identifier.
            lat, lon: GPS coordinates.
            api_key: WeatherAPI.com key.
            days: forecast days (free tier supports up to 3).

        Returns:
            Number of forecast rows inserted.
        """
        data = self._api_get(
            "forecast.json",
            {"q": f"{lat},{lon}", "days": days, "aqi": "no", "alerts": "no"},
            api_key,
        )
        if not data:
            return 0

        conn = self._get_conn()
        inserted = 0
        fetched_at = datetime.utcnow().isoformat(timespec="seconds")

        for day in data.get("forecast", {}).get("forecastday", []):
            fc_date = day["date"]
            d = day["day"]
            astro = day.get("astro", {})

            # confidence decreases with horizon
            horizon = (datetime.strptime(fc_date, "%Y-%m-%d").date() - date.today()).days
            confidence = max(0.5, 1.0 - horizon * 0.1)

            # daily summary row (forecast_hour = NULL)
            conn.execute(
                """
                INSERT INTO weather_forecasts
                    (store_id, forecast_date, forecast_hour,
                     max_temp_c, min_temp_c, avg_temp_c,
                     max_wind_kph, total_precip_mm, avg_humidity_pct,
                     chance_of_rain, uv_index,
                     condition_text, condition_code,
                     sunrise, sunset, confidence, fetched_at)
                VALUES (?,?,NULL, ?,?,?, ?,?,?, ?,?, ?,?, ?,?, ?,?)
                ON CONFLICT(store_id, forecast_date, forecast_hour) DO UPDATE SET
                    max_temp_c      = excluded.max_temp_c,
                    min_temp_c      = excluded.min_temp_c,
                    avg_temp_c      = excluded.avg_temp_c,
                    max_wind_kph    = excluded.max_wind_kph,
                    total_precip_mm = excluded.total_precip_mm,
                    avg_humidity_pct= excluded.avg_humidity_pct,
                    chance_of_rain  = excluded.chance_of_rain,
                    uv_index        = excluded.uv_index,
                    condition_text  = excluded.condition_text,
                    condition_code  = excluded.condition_code,
                    sunrise         = excluded.sunrise,
                    sunset          = excluded.sunset,
                    confidence      = excluded.confidence,
                    fetched_at      = excluded.fetched_at
                """,
                (
                    store_id, fc_date,
                    d.get("maxtemp_c"), d.get("mintemp_c"), d.get("avgtemp_c"),
                    d.get("maxwind_kph"), d.get("totalprecip_mm"),
                    d.get("avghumidity"),
                    d.get("daily_chance_of_rain", 0),
                    d.get("uv"),
                    d.get("condition", {}).get("text"),
                    d.get("condition", {}).get("code"),
                    astro.get("sunrise"), astro.get("sunset"),
                    confidence, fetched_at,
                ),
            )
            inserted += 1

            # hourly rows
            for hour in day.get("hour", []):
                h = int(hour["time"].split(" ")[1].split(":")[0])
                conn.execute(
                    """
                    INSERT INTO weather_forecasts
                        (store_id, forecast_date, forecast_hour,
                         max_temp_c, min_temp_c, avg_temp_c,
                         max_wind_kph, total_precip_mm, avg_humidity_pct,
                         chance_of_rain, uv_index,
                         condition_text, condition_code,
                         confidence, fetched_at)
                    VALUES (?,?,?, ?,?,?, ?,?,?, ?,?, ?,?, ?,?)
                    ON CONFLICT(store_id, forecast_date, forecast_hour) DO UPDATE SET
                        max_temp_c      = excluded.max_temp_c,
                        avg_temp_c      = excluded.avg_temp_c,
                        max_wind_kph    = excluded.max_wind_kph,
                        total_precip_mm = excluded.total_precip_mm,
                        avg_humidity_pct= excluded.avg_humidity_pct,
                        chance_of_rain  = excluded.chance_of_rain,
                        uv_index        = excluded.uv_index,
                        condition_text  = excluded.condition_text,
                        condition_code  = excluded.condition_code,
                        confidence      = excluded.confidence,
                        fetched_at      = excluded.fetched_at
                    """,
                    (
                        store_id, fc_date, h,
                        hour.get("temp_c"), hour.get("temp_c"), hour.get("temp_c"),
                        hour.get("wind_kph"), hour.get("precip_mm"),
                        hour.get("humidity"),
                        hour.get("chance_of_rain", 0),
                        hour.get("uv"),
                        hour.get("condition", {}).get("text"),
                        hour.get("condition", {}).get("code"),
                        confidence, fetched_at,
                    ),
                )
                inserted += 1

        conn.commit()
        logger.info("Store %s: %d forecast rows upserted", store_id, inserted)
        return inserted

    # -- record actual observation -----------------------------------------

    def record_observation(self, store_id, lat, lon, api_key):
        """Fetch current conditions and store as an observation.

        Returns True on success, False on failure.
        """
        data = self._api_get(
            "current.json", {"q": f"{lat},{lon}", "aqi": "no"}, api_key,
        )
        if not data or "current" not in data:
            return False

        c = data["current"]
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO weather_observations
                (store_id, observed_at, temp_c, feels_like_c, humidity_pct,
                 wind_kph, wind_dir, precip_mm, cloud_pct, uv_index,
                 condition_text, condition_code, is_day)
            VALUES (?,?,?,?,?, ?,?,?,?,?, ?,?,?)
            ON CONFLICT(store_id, observed_at) DO NOTHING
            """,
            (
                store_id,
                c.get("last_updated", datetime.utcnow().isoformat()),
                c.get("temp_c"), c.get("feelslike_c"), c.get("humidity"),
                c.get("wind_kph"), c.get("wind_dir"), c.get("precip_mm"),
                c.get("cloud"), c.get("uv"),
                c.get("condition", {}).get("text"),
                c.get("condition", {}).get("code"),
                c.get("is_day"),
            ),
        )
        conn.commit()
        logger.info("Store %s: observation recorded", store_id)
        return True

    # -- daily summary generation ------------------------------------------

    def generate_daily_summary(self, store_id, summary_date=None):
        """Build a daily_weather_summary row from forecast data.

        Args:
            store_id: store identifier.
            summary_date: YYYY-MM-DD string (defaults to today).
        """
        if summary_date is None:
            summary_date = date.today().isoformat()

        conn = self._get_conn()
        row = conn.execute(
            """
            SELECT max_temp_c, min_temp_c, avg_temp_c,
                   total_precip_mm, avg_humidity_pct, max_wind_kph,
                   uv_index, condition_text
            FROM weather_forecasts
            WHERE store_id = ? AND forecast_date = ? AND forecast_hour IS NULL
            ORDER BY fetched_at DESC LIMIT 1
            """,
            (store_id, summary_date),
        ).fetchone()

        if not row:
            logger.warning("No forecast data for store %s on %s", store_id, summary_date)
            return

        max_t = row["max_temp_c"] or 0
        min_t = row["min_temp_c"] or 0
        precip = row["total_precip_mm"] or 0

        is_hot = int(max_t >= 30)
        is_cold = int(max_t < 15)
        is_wet = int(precip > 5)
        is_extreme = int(max_t >= 38)

        if is_extreme:
            category = "EXTREME"
        elif is_hot:
            category = "HOT"
        elif is_cold:
            category = "COLD"
        elif is_wet:
            category = "WET"
        elif 20 <= max_t <= 28 and precip < 2:
            category = "SUNNY"
        else:
            category = "MILD"

        conn.execute(
            """
            INSERT INTO daily_weather_summary
                (store_id, summary_date, max_temp_c, min_temp_c, avg_temp_c,
                 total_precip_mm, avg_humidity_pct, max_wind_kph, avg_uv_index,
                 dominant_condition, is_hot, is_cold, is_wet, is_extreme_heat,
                 weather_category, data_source)
            VALUES (?,?,?,?,?, ?,?,?,?, ?,?,?,?,?, ?,'forecast')
            ON CONFLICT(store_id, summary_date) DO UPDATE SET
                max_temp_c        = excluded.max_temp_c,
                min_temp_c        = excluded.min_temp_c,
                avg_temp_c        = excluded.avg_temp_c,
                total_precip_mm   = excluded.total_precip_mm,
                avg_humidity_pct  = excluded.avg_humidity_pct,
                max_wind_kph      = excluded.max_wind_kph,
                avg_uv_index      = excluded.avg_uv_index,
                dominant_condition= excluded.dominant_condition,
                is_hot            = excluded.is_hot,
                is_cold           = excluded.is_cold,
                is_wet            = excluded.is_wet,
                is_extreme_heat   = excluded.is_extreme_heat,
                weather_category  = excluded.weather_category,
                data_source       = excluded.data_source
            """,
            (
                store_id, summary_date,
                max_t, min_t, row["avg_temp_c"],
                precip, row["avg_humidity_pct"], row["max_wind_kph"],
                row["uv_index"], row["condition_text"],
                is_hot, is_cold, is_wet, is_extreme,
                category,
            ),
        )
        conn.commit()
        logger.info("Store %s: daily summary for %s → %s", store_id, summary_date, category)

    # -- category / profile management -------------------------------------

    def add_weather_category(self, name, department, heat, cold, rain, wind=3,
                             description=None):
        """Insert or update a weather-impact category.

        Args:
            name: category name (e.g. 'Ice Cream & Frozen Treats').
            department: parent department.
            heat/cold/rain/wind: sensitivity scores 1-10.
            description: optional notes.
        """
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO weather_impact_categories
                (category_name, department, heat_sensitivity, cold_sensitivity,
                 rain_sensitivity, wind_sensitivity, description)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(category_name) DO UPDATE SET
                department       = excluded.department,
                heat_sensitivity = excluded.heat_sensitivity,
                cold_sensitivity = excluded.cold_sensitivity,
                rain_sensitivity = excluded.rain_sensitivity,
                wind_sensitivity = excluded.wind_sensitivity,
                description      = excluded.description
            """,
            (name, department, heat, cold, rain, wind, description),
        )
        conn.commit()

    def add_product_profile(self, product_code, product_name, category_name,
                            hot=1.0, cold=1.0, rain=1.0, sunny=1.0,
                            extreme_heat=None, lead_days=1, notes=None):
        """Insert or update a product-weather profile.

        Args:
            product_code: unique SKU / internal code.
            product_name: display name.
            category_name: must exist in weather_impact_categories.
            hot/cold/rain/sunny: demand multipliers.
            extreme_heat: override for >38 C (defaults to hot * 1.2).
            lead_days: replenishment lead time in days.
            notes: optional notes.
        """
        if extreme_heat is None:
            extreme_heat = round(hot * 1.2, 2)

        conn = self._get_conn()
        cat_row = conn.execute(
            "SELECT category_id FROM weather_impact_categories WHERE category_name = ?",
            (category_name,),
        ).fetchone()
        cat_id = cat_row["category_id"] if cat_row else None

        conn.execute(
            """
            INSERT INTO product_weather_profiles
                (product_code, product_name, category_id,
                 hot_multiplier, cold_multiplier, rain_multiplier,
                 sunny_multiplier, extreme_heat_multiplier,
                 replenishment_lead_days, notes)
            VALUES (?,?,?, ?,?,?, ?,?, ?,?)
            ON CONFLICT(product_code) DO UPDATE SET
                product_name            = excluded.product_name,
                category_id             = excluded.category_id,
                hot_multiplier          = excluded.hot_multiplier,
                cold_multiplier         = excluded.cold_multiplier,
                rain_multiplier         = excluded.rain_multiplier,
                sunny_multiplier        = excluded.sunny_multiplier,
                extreme_heat_multiplier = excluded.extreme_heat_multiplier,
                replenishment_lead_days = excluded.replenishment_lead_days,
                notes                   = excluded.notes,
                updated_at              = datetime('now')
            """,
            (
                product_code, product_name, cat_id,
                hot, cold, rain, sunny, extreme_heat,
                lead_days, notes,
            ),
        )
        conn.commit()

    # -- bulk operations ---------------------------------------------------

    def update_all_store_forecasts(self, api_key, days=3):
        """Fetch forecasts + observations for every active store.

        Args:
            api_key: WeatherAPI.com API key.
            days: number of forecast days (free tier = 3).

        Returns:
            Total forecast rows inserted across all stores.
        """
        stores = self.get_active_stores()
        if not stores:
            logger.warning("No active stores found")
            return 0

        total = 0
        for s in stores:
            sid = s["store_id"]
            lat, lon = s["latitude"], s["longitude"]
            logger.info("Fetching weather for %s (%s) ...", s["name"], s["suburb"])

            rows = self.fetch_forecast(sid, lat, lon, api_key, days=days)
            total += rows

            self.record_observation(sid, lat, lon, api_key)

            # generate summaries for each forecast day
            for offset in range(days):
                d = (date.today() + timedelta(days=offset)).isoformat()
                self.generate_daily_summary(sid, d)

            time.sleep(API_PAUSE_SECONDS)

        logger.info("All stores updated: %d total forecast rows", total)
        return total


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Harris Farm Weather — Data Loader")
    parser.add_argument("--init", action="store_true", help="Initialise database")
    parser.add_argument("--fetch", metavar="API_KEY",
                        help="Fetch forecasts for all stores using the given API key")
    parser.add_argument("--days", type=int, default=3,
                        help="Forecast days (free tier = 3)")
    args = parser.parse_args()

    loader = WeatherDataLoader()

    if args.init:
        loader.initialize_database()
        print("Database initialised.")

    if args.fetch:
        n = loader.update_all_store_forecasts(args.fetch, days=args.days)
        print(f"Done — {n} forecast rows stored.")

    loader.close()
