# Getting Started — Harris Farm Weather System

## 5-Minute Quick Start

```bash
# 1. Install everything
bash install.sh

# 2. Get a free API key from https://www.weatherapi.com/ (1M calls/month free)

# 3. Fetch your first forecast
python3 weather_data_loader.py --fetch YOUR_API_KEY

# 4. Run the dashboard
python3 weather_dashboard.py

# 5. Run tests
python3 test_system.py
```

That's it. You now have weather-adjusted demand forecasts for 5 Sydney stores and 42 products.

---

## How Multipliers Work

Every product has four demand multipliers:

| Condition | Trigger | Example: Ice Cream | Example: Soup |
|-----------|---------|-------------------|---------------|
| **Hot** | Max temp > 30C | x2.5 (demand +150%) | x0.5 (demand -50%) |
| **Cold** | Max temp < 15C | x0.4 (demand -60%) | x2.2 (demand +120%) |
| **Rain** | Precip > 5mm | x0.6 (demand -40%) | x1.9 (demand +90%) |
| **Sunny** | 20-28C, dry | x1.3 (demand +30%) | x0.7 (demand -30%) |
| **Extreme Heat** | Max temp > 38C | x3.2 (demand +220%) | x0.3 (demand -70%) |

**Multipliers compound.** A hot + rainy day for BBQ sausages:
- Hot multiplier: x2.8
- Rain multiplier: x0.3
- Combined: 2.8 x 0.3 = **x0.84** (BBQ is rained out despite heat)

### Example Calculation

```
Base demand:     50 units/day (ice cream)
Tomorrow:        36C, sunny
Hot multiplier:  x2.5
Adjusted demand: 50 x 2.5 = 125 units
Order today:     Lead time is 2 days, so order 2 days before impact
```

---

## Daily Workflow

### Morning (7 AM)

```bash
# Run the full dashboard
python3 weather_dashboard.py
```

This shows:
1. **Weather Overview** — conditions at each store with emoji indicators
2. **High-Impact Products** — items with >50% demand change today
3. **Urgent Buying Alerts** — what to order now (accounts for lead times)
4. **Category Summary** — department-level demand direction

### Export for Ordering

```bash
# Generate CSV for your ordering system
python3 -c "
from weather_dashboard import WeatherDashboard
d = WeatherDashboard()
d.export_buying_report()
"
```

Output: `exports/buying_alerts_YYYYMMDD_HHMM.csv`

### Automate It

```bash
# Set up cron jobs for daily automation
bash setup_automation.sh
```

---

## Adjusting for Your Products

### Add a New Product

```python
from weather_data_loader import WeatherDataLoader

loader = WeatherDataLoader()
loader.add_product_profile(
    product_code="PASTA01",
    product_name="Fresh Pasta 400g",
    category_name="Pasta & Rice",
    hot=0.7,      # less demand in heat
    cold=1.5,     # more demand in cold
    rain=1.3,     # comfort food
    sunny=0.9,    # slightly less
    lead_days=1,
    notes="Fresh pasta — comfort food driver",
)
loader.close()
```

### Add a New Category

```python
loader.add_weather_category(
    name="Frozen Desserts",
    department="Dairy & Frozen",
    heat=9, cold=7, rain=4, wind=2,
    description="Frozen cakes, tarts, and novelties",
)
```

### Add a New Store

```python
loader.add_store(
    store_id=42,
    name="Bondi Junction",
    suburb="Bondi Junction",
    state="NSW",
    postcode="2022",
    lat=-33.8912,
    lon=151.2472,
)
```

---

## Common Questions

**Q: How accurate are the multipliers?**
A: The default multipliers are based on grocery retail patterns. You should refine them over time by comparing weather-adjusted forecasts against actual sales. The `store_weather_correlations` table is designed for this — future versions will auto-tune multipliers from historical data.

**Q: What if the API is down?**
A: The system stores all fetched data locally. If a fetch fails, the last successful forecast is used. Error handling is built in with retries for rate limiting.

**Q: Can I use a different weather API?**
A: Yes. The `WeatherDataLoader` class has a clean `_api_get` method. Override `fetch_forecast` and `record_observation` to parse a different API's response format.

**Q: What about store-specific microclimates?**
A: Each store uses its own GPS coordinates, so forecasts are location-specific. Coastal stores (Mosman) may differ significantly from inland stores.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: pandas` | Run `pip install -r requirements.txt` |
| `403 Forbidden` from API | Check your API key at weatherapi.com |
| `No forecast data` | Run `python3 weather_data_loader.py --fetch KEY` first |
| Empty dashboard | Ensure `weather.db` has forecast data: `sqlite3 weather.db "SELECT COUNT(*) FROM weather_forecasts"` |
| Stale forecasts | The cron job fetches fresh data daily at 6 AM |
