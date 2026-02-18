-- Harris Farm Weather Database Schema
-- Supports per-store weather tracking and demand forecasting.
-- SQLite-compatible. All timestamps stored as TEXT (ISO-8601).

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- =====================================================================
-- CORE TABLES
-- =====================================================================

CREATE TABLE IF NOT EXISTS stores (
    store_id        INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL,
    suburb          TEXT    NOT NULL,
    state           TEXT    NOT NULL DEFAULT 'NSW',
    postcode        TEXT    NOT NULL,
    latitude        REAL    NOT NULL,
    longitude       REAL    NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS weather_observations (
    observation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id        INTEGER NOT NULL REFERENCES stores(store_id),
    observed_at     TEXT    NOT NULL,                       -- ISO-8601 datetime
    temp_c          REAL,
    feels_like_c    REAL,
    humidity_pct    REAL,
    wind_kph        REAL,
    wind_dir        TEXT,
    precip_mm       REAL    DEFAULT 0,
    cloud_pct       REAL,
    uv_index        REAL,
    condition_text  TEXT,
    condition_code  INTEGER,
    is_day          INTEGER,
    source          TEXT    DEFAULT 'weatherapi',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(store_id, observed_at)
);

CREATE TABLE IF NOT EXISTS weather_forecasts (
    forecast_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id        INTEGER NOT NULL REFERENCES stores(store_id),
    forecast_date   TEXT    NOT NULL,                       -- YYYY-MM-DD
    forecast_hour   INTEGER,                                -- 0-23, NULL for daily
    max_temp_c      REAL,
    min_temp_c      REAL,
    avg_temp_c      REAL,
    max_wind_kph    REAL,
    total_precip_mm REAL    DEFAULT 0,
    avg_humidity_pct REAL,
    chance_of_rain  INTEGER DEFAULT 0,                      -- 0-100
    uv_index        REAL,
    condition_text  TEXT,
    condition_code  INTEGER,
    sunrise         TEXT,
    sunset          TEXT,
    confidence      REAL    DEFAULT 0.8,                    -- 0-1, decreases with horizon
    fetched_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    source          TEXT    DEFAULT 'weatherapi',
    UNIQUE(store_id, forecast_date, forecast_hour)
);

CREATE TABLE IF NOT EXISTS weather_impact_categories (
    category_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name   TEXT    NOT NULL UNIQUE,
    department      TEXT,
    heat_sensitivity    INTEGER NOT NULL DEFAULT 5  CHECK(heat_sensitivity BETWEEN 1 AND 10),
    cold_sensitivity    INTEGER NOT NULL DEFAULT 5  CHECK(cold_sensitivity BETWEEN 1 AND 10),
    rain_sensitivity    INTEGER NOT NULL DEFAULT 5  CHECK(rain_sensitivity BETWEEN 1 AND 10),
    wind_sensitivity    INTEGER NOT NULL DEFAULT 3  CHECK(wind_sensitivity BETWEEN 1 AND 10),
    description     TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS product_weather_profiles (
    profile_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code    TEXT    NOT NULL UNIQUE,
    product_name    TEXT    NOT NULL,
    category_id     INTEGER REFERENCES weather_impact_categories(category_id),
    hot_multiplier          REAL NOT NULL DEFAULT 1.0,      -- applied when >30 C
    cold_multiplier         REAL NOT NULL DEFAULT 1.0,      -- applied when <15 C
    rain_multiplier         REAL NOT NULL DEFAULT 1.0,      -- applied when >5 mm rain
    sunny_multiplier        REAL NOT NULL DEFAULT 1.0,      -- applied when 20-28 C, no rain
    extreme_heat_multiplier REAL NOT NULL DEFAULT 1.0,      -- applied when >38 C
    replenishment_lead_days INTEGER NOT NULL DEFAULT 1,
    min_multiplier          REAL NOT NULL DEFAULT 0.2,      -- floor
    max_multiplier          REAL NOT NULL DEFAULT 5.0,       -- ceiling
    is_active               INTEGER NOT NULL DEFAULT 1,
    notes           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS daily_weather_summary (
    summary_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id        INTEGER NOT NULL REFERENCES stores(store_id),
    summary_date    TEXT    NOT NULL,                       -- YYYY-MM-DD
    max_temp_c      REAL,
    min_temp_c      REAL,
    avg_temp_c      REAL,
    total_precip_mm REAL    DEFAULT 0,
    avg_humidity_pct REAL,
    max_wind_kph    REAL,
    avg_uv_index    REAL,
    dominant_condition TEXT,
    is_hot          INTEGER DEFAULT 0,                      -- max_temp > 30
    is_cold         INTEGER DEFAULT 0,                      -- max_temp < 15
    is_wet          INTEGER DEFAULT 0,                      -- total_precip > 5
    is_extreme_heat INTEGER DEFAULT 0,                      -- max_temp > 38
    weather_category TEXT,                                  -- HOT / COLD / WET / MILD / SUNNY
    data_source     TEXT    DEFAULT 'forecast',             -- forecast or observation
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(store_id, summary_date)
);

CREATE TABLE IF NOT EXISTS store_weather_correlations (
    correlation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id        INTEGER NOT NULL REFERENCES stores(store_id),
    category_id     INTEGER REFERENCES weather_impact_categories(category_id),
    product_code    TEXT,
    weather_variable TEXT   NOT NULL,                       -- temp, rain, humidity
    correlation_coeff REAL,
    r_squared       REAL,
    sample_size     INTEGER,
    period_start    TEXT,
    period_end      TEXT,
    calculated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(store_id, product_code, weather_variable)
);


-- =====================================================================
-- INDEXES
-- =====================================================================

CREATE INDEX IF NOT EXISTS idx_obs_store_date
    ON weather_observations(store_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_fc_store_date
    ON weather_forecasts(store_id, forecast_date);

CREATE INDEX IF NOT EXISTS idx_fc_fetched
    ON weather_forecasts(fetched_at);

CREATE INDEX IF NOT EXISTS idx_summary_store_date
    ON daily_weather_summary(store_id, summary_date);

CREATE INDEX IF NOT EXISTS idx_summary_category
    ON daily_weather_summary(weather_category);

CREATE INDEX IF NOT EXISTS idx_product_category
    ON product_weather_profiles(category_id);

CREATE INDEX IF NOT EXISTS idx_product_code
    ON product_weather_profiles(product_code);

CREATE INDEX IF NOT EXISTS idx_corr_store
    ON store_weather_correlations(store_id);


-- =====================================================================
-- VIEWS
-- =====================================================================

-- Latest forecast per store (most recently fetched daily row per date)
CREATE VIEW IF NOT EXISTS v_latest_forecast AS
SELECT f.*,
       s.name   AS store_name,
       s.suburb AS store_suburb
FROM   weather_forecasts f
JOIN   stores s ON s.store_id = f.store_id
WHERE  f.forecast_hour IS NULL
  AND  f.fetched_at = (
           SELECT MAX(f2.fetched_at)
           FROM   weather_forecasts f2
           WHERE  f2.store_id      = f.store_id
             AND  f2.forecast_date = f.forecast_date
             AND  f2.forecast_hour IS NULL
       );


-- Dashboard view: forecasts enriched with weather flags
CREATE VIEW IF NOT EXISTS v_weather_impact_dashboard AS
SELECT s.store_id,
       s.name       AS store_name,
       s.suburb,
       d.summary_date,
       d.max_temp_c,
       d.min_temp_c,
       d.total_precip_mm,
       d.avg_humidity_pct,
       d.weather_category,
       d.is_hot,
       d.is_cold,
       d.is_wet,
       d.is_extreme_heat,
       d.dominant_condition
FROM   daily_weather_summary d
JOIN   stores s ON s.store_id = d.store_id
WHERE  s.is_active = 1
ORDER  BY d.summary_date, s.store_id;


-- Rolling 7-day forecast (future dates only)
CREATE VIEW IF NOT EXISTS v_7day_forecast AS
SELECT s.store_id,
       s.name       AS store_name,
       s.suburb,
       f.forecast_date,
       f.max_temp_c,
       f.min_temp_c,
       f.avg_temp_c,
       f.total_precip_mm,
       f.chance_of_rain,
       f.avg_humidity_pct,
       f.condition_text,
       f.confidence,
       CASE
           WHEN f.max_temp_c >= 38 THEN 'EXTREME'
           WHEN f.max_temp_c >= 30 THEN 'HOT'
           WHEN f.max_temp_c <  15 THEN 'COLD'
           WHEN f.total_precip_mm > 5 THEN 'WET'
           WHEN f.max_temp_c BETWEEN 20 AND 28
                AND f.total_precip_mm < 2 THEN 'SUNNY'
           ELSE 'MILD'
       END AS weather_category
FROM   weather_forecasts f
JOIN   stores s ON s.store_id = f.store_id
WHERE  f.forecast_hour IS NULL
  AND  f.forecast_date >= date('now')
ORDER  BY f.forecast_date, s.store_id;
