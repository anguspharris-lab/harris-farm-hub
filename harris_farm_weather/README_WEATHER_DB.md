# Harris Farm Weather Database — Technical Reference

## Architecture

```
                 WeatherAPI.com (free tier)
                        |
                        v
               weather_data_loader.py
                   |           |
                   v           v
             weather.db    daily_weather_summary
                   |
          +--------+---------+
          |                  |
  weather_demand_planner.py  weather_dashboard.py
          |                  |
          v                  v
    Adjusted demand     Morning reports
    Buying alerts       CSV exports
```

### Components

| File | Purpose |
|------|---------|
| `weather_db_schema.sql` | Database DDL (tables, indexes, views) |
| `weather_data_loader.py` | API integration, data ingestion, store management |
| `weather_demand_planner.py` | Demand adjustment engine, buying alerts |
| `weather_dashboard.py` | Terminal reports, CSV exports |
| `example_products.py` | 25 categories, 42 products, 5 sample stores |

---

## Database Schema

### Tables

**`stores`** — Harris Farm locations with GPS coordinates.

| Column | Type | Description |
|--------|------|-------------|
| store_id | INTEGER PK | Matches POS system |
| name | TEXT | Store name |
| latitude, longitude | REAL | GPS for weather lookups |
| is_active | INTEGER | 1 = active, 0 = closed |

**`weather_forecasts`** — Forecast data from WeatherAPI.

| Column | Type | Description |
|--------|------|-------------|
| store_id | INTEGER FK | Store reference |
| forecast_date | TEXT | YYYY-MM-DD |
| forecast_hour | INTEGER | 0-23 (NULL = daily summary) |
| max_temp_c, min_temp_c, avg_temp_c | REAL | Temperature range |
| total_precip_mm | REAL | Expected rainfall |
| chance_of_rain | INTEGER | 0-100% |
| confidence | REAL | 0-1, decreases with horizon |

**`weather_observations`** — Actual weather readings.

| Column | Type | Description |
|--------|------|-------------|
| store_id | INTEGER FK | Store reference |
| observed_at | TEXT | ISO-8601 datetime |
| temp_c, feels_like_c | REAL | Current temperature |
| precip_mm | REAL | Current precipitation |

**`weather_impact_categories`** — Product group sensitivity scores.

| Column | Type | Description |
|--------|------|-------------|
| category_name | TEXT UNIQUE | e.g. "BBQ Meats & Sausages" |
| department | TEXT | Parent department |
| heat/cold/rain/wind_sensitivity | INTEGER | 1-10 scale |

**`product_weather_profiles`** — Per-product demand multipliers.

| Column | Type | Description |
|--------|------|-------------|
| product_code | TEXT UNIQUE | SKU / internal code |
| hot_multiplier | REAL | Applied when max temp > 30C |
| cold_multiplier | REAL | Applied when max temp < 15C |
| rain_multiplier | REAL | Applied when precip > 5mm |
| sunny_multiplier | REAL | Applied when 20-28C + dry |
| extreme_heat_multiplier | REAL | Applied when max temp > 38C |
| replenishment_lead_days | INTEGER | Order lead time |
| min_multiplier, max_multiplier | REAL | Clamp range |

**`daily_weather_summary`** — Aggregated daily metrics with categories.

| Column | Type | Description |
|--------|------|-------------|
| weather_category | TEXT | EXTREME / HOT / COLD / WET / SUNNY / MILD |
| is_hot, is_cold, is_wet, is_extreme_heat | INTEGER | Boolean flags |

**`store_weather_correlations`** — Statistical relationships (for ML).

| Column | Type | Description |
|--------|------|-------------|
| weather_variable | TEXT | temp / rain / humidity |
| correlation_coeff | REAL | Pearson r |
| r_squared | REAL | Coefficient of determination |

### Views

- **`v_latest_forecast`** — Most recent daily forecast per store/date
- **`v_weather_impact_dashboard`** — Forecasts with weather flags for dashboards
- **`v_7day_forecast`** — Forward-looking 7-day outlook with categories

---

## API Integration

### WeatherAPI.com

- **Free tier**: 1,000,000 calls/month, 3-day forecast, current conditions
- **Endpoint**: `https://api.weatherapi.com/v1/forecast.json`
- **Rate limiting**: Built-in 1-second pause between store calls + 60s retry on 429
- **Data stored**: Daily summaries + hourly breakdowns

### Configuration

```bash
# Set API key as environment variable
export WEATHERAPI_KEY="your_key_here"

# Or pass directly
python3 weather_data_loader.py --fetch your_key_here
```

---

## Usage Examples

### Calculate Weather-Adjusted Demand

```python
from weather_demand_planner import WeatherDemandPlanner

planner = WeatherDemandPlanner()

result = planner.get_weather_adjusted_demand(
    store_id=1,
    product_code="ICE001",
    forecast_date="2026-02-17",
    base_demand=50,
)

print(f"Adjusted: {result['adjusted_demand']} units")
print(f"Multiplier: x{result['multiplier']}")
print(f"Reason: {result['weather_factors']}")
print(f"Category: {result['weather_category']}")
# Output:
# Adjusted: 125 units
# Multiplier: x2.5
# Reason: Hot day 35C (x2.5)
# Category: HOT
```

### Get High-Impact Products

```python
products = planner.get_high_impact_products(
    store_id=1,
    forecast_date="2026-02-17",
    min_multiplier=1.5,
)

for p in products:
    print(f"{p['product_name']}: x{p['multiplier']} ({p['pct_change']:+.0f}%)")
```

### Generate Buying Alerts

```python
alerts = planner.generate_weekly_buying_alerts(store_id=1)

for a in alerts:
    print(f"[{a['urgency']}] {a['product_name']} "
          f"x{a['multiplier']} — order by {a['order_by']} "
          f"for {a['impact_date']}")
```

### Export to CSV

```python
from weather_dashboard import WeatherDashboard

dashboard = WeatherDashboard()
filepath = dashboard.export_buying_report(store_id=1)
# Creates: exports/buying_alerts_20260217_0700.csv
```

---

## SQL Query Reference

### Current forecasts for all stores

```sql
SELECT * FROM v_7day_forecast
WHERE forecast_date = date('now');
```

### Products that need ordering today

```sql
SELECT p.product_code, p.product_name, p.hot_multiplier,
       p.replenishment_lead_days,
       f.max_temp_c, f.total_precip_mm
FROM product_weather_profiles p
CROSS JOIN v_latest_forecast f
WHERE f.max_temp_c > 30
  AND p.hot_multiplier > 1.5
ORDER BY p.hot_multiplier DESC;
```

### Weather history for analysis

```sql
SELECT summary_date, weather_category,
       max_temp_c, total_precip_mm
FROM daily_weather_summary
WHERE store_id = 1
ORDER BY summary_date DESC
LIMIT 30;
```

### Category sensitivity overview

```sql
SELECT category_name, department,
       heat_sensitivity, cold_sensitivity, rain_sensitivity
FROM weather_impact_categories
ORDER BY heat_sensitivity DESC;
```

---

## Integration Options

### Excel / Google Sheets

Import the CSV exports from `exports/` directory. Columns:
`store_id, store_name, product_code, product_name, impact_date, order_by, urgency, multiplier, pct_change, weather_factors, confidence, lead_days`

### REST API

The weather database can be queried from the main Harris Farm Hub backend. Add endpoints to `backend/app.py` that read from `weather.db`.

### Direct SQL

```bash
sqlite3 harris_farm_weather/weather.db
```

---

## Advanced Features

### Correlation Analysis

Once you have sales data paired with weather observations, calculate correlations:

```python
# Future: auto-tune multipliers from historical data
conn.execute("""
    INSERT INTO store_weather_correlations
        (store_id, product_code, weather_variable,
         correlation_coeff, r_squared, sample_size,
         period_start, period_end)
    VALUES (?, ?, 'temp', ?, ?, ?, ?, ?)
""", params)
```

### Confidence Scoring

Forecast confidence decreases with horizon:
- Today: 1.0
- Tomorrow: 0.9
- Day 2: 0.8
- Day 3+: 0.7-0.5

The demand planner includes confidence in all results so downstream systems can weight decisions.

---

## Maintenance

### Daily Operations

| Time | Task | Command |
|------|------|---------|
| 6:00 AM | Fetch forecasts | `python3 daily_weather_update.py` |
| 7:00 AM | Generate report | `python3 generate_daily_dashboard.py` |
| 11:00 PM | Backup database | `bash backup_weather_db.sh` |

### Database Size

With 5 stores and daily updates:
- ~15 forecast rows/day (5 stores x 3 days)
- ~5 observation rows/day
- ~15 hourly rows/day per store
- Estimated: ~5 MB/year

### Pruning Old Data

```sql
-- Remove forecasts older than 90 days
DELETE FROM weather_forecasts
WHERE fetched_at < datetime('now', '-90 days');

-- Remove observations older than 1 year
DELETE FROM weather_observations
WHERE observed_at < datetime('now', '-365 days');
```
