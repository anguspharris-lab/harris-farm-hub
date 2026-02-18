"""
Harris Farm Weather — Example Products & Categories
Pre-configured weather-impact categories and product profiles
with realistic demand multipliers for a premium grocery retailer.

Run this module directly to populate the database:
    python3 example_products.py
"""

from weather_data_loader import WeatherDataLoader

# =========================================================================
# WEATHER-IMPACT CATEGORIES
# =========================================================================
# Each tuple: (name, department, heat_sens, cold_sens, rain_sens, wind_sens, description)

CATEGORIES = [
    ("Ice Cream & Frozen Treats", "Dairy & Frozen", 10, 8, 5, 2,
     "Extreme heat sensitivity — demand spikes 2-3x on hot days"),
    ("Salads & Cold Meals", "Deli & Prepared", 9, 6, 4, 2,
     "Strong heat driver, moderate cold reduction"),
    ("Soup & Hot Meals", "Deli & Prepared", 7, 9, 8, 3,
     "Cold/rain driver — demand doubles in winter weather"),
    ("BBQ Meats & Sausages", "Meat & Seafood", 10, 7, 9, 4,
     "Highest weather sensitivity — BBQ culture drives extreme heat demand"),
    ("Fresh Berries", "Fruit & Vegetables", 7, 5, 3, 2,
     "Summer fruit, demand lifts with heat and sunny weather"),
    ("Citrus Fruit", "Fruit & Vegetables", 4, 7, 3, 2,
     "Winter seasonal, moderate cold uplift"),
    ("Tropical Fruit", "Fruit & Vegetables", 8, 4, 3, 2,
     "Heat driver — mangoes, watermelon, pineapple"),
    ("Fresh Seafood", "Meat & Seafood", 6, 5, 5, 3,
     "Moderate heat lift for seafood salads, rain dampens foot traffic"),
    ("Bakery Pies & Pastry", "Bakery", 5, 8, 7, 3,
     "Cold/rain comfort food driver"),
    ("Fresh Bread & Rolls", "Bakery", 3, 4, 3, 2,
     "Low weather sensitivity — staple product"),
    ("Cold Beverages", "Drinks", 10, 6, 4, 2,
     "Extreme heat sensitivity — water, juice, soft drinks"),
    ("Hot Beverages & Cocoa", "Drinks", 5, 8, 7, 3,
     "Cold weather driver — hot chocolate, chai"),
    ("Fresh Juice & Smoothies", "Drinks", 9, 5, 4, 2,
     "Strong heat driver, reduced in cold/rain"),
    ("Cheese & Dips", "Deli & Prepared", 7, 4, 4, 2,
     "Entertaining uplift on sunny days, reduced in cold"),
    ("Chips & Snacks", "Pantry", 6, 4, 5, 2,
     "BBQ and outdoor snacking driver"),
    ("Fresh Flowers", "Flowers & Plants", 5, 5, 7, 6,
     "Rain and wind reduce outdoor displays and foot traffic"),
    ("Sunscreen & Summer Care", "Health & Beauty", 10, 2, 3, 2,
     "Direct heat/UV correlation"),
    ("Root Vegetables", "Fruit & Vegetables", 3, 7, 5, 2,
     "Winter staple — soups and stews driver"),
    ("Leafy Greens", "Fruit & Vegetables", 6, 4, 3, 2,
     "Salad component — lifts with heat"),
    ("Condiments & Sauces", "Pantry", 6, 3, 3, 2,
     "BBQ sauce, marinades lift on hot days"),
    ("Frozen Meals", "Dairy & Frozen", 4, 6, 6, 2,
     "Convenience comfort food in cold/rain"),
    ("Wine & Beer", "Drinks", 8, 5, 5, 2,
     "Strong entertaining driver on hot/sunny days"),
    ("Stone Fruit", "Fruit & Vegetables", 8, 3, 3, 2,
     "Peak summer fruit — nectarines, peaches, plums"),
    ("Yoghurt & Dairy Desserts", "Dairy & Frozen", 7, 5, 3, 2,
     "Light dessert, heat driver"),
    ("Pasta & Rice", "Pantry", 3, 6, 5, 2,
     "Pantry staple, slight cold weather lift"),
]

# =========================================================================
# PRODUCT WEATHER PROFILES
# =========================================================================
# Each tuple: (code, name, category, hot_mult, cold_mult, rain_mult,
#              sunny_mult, extreme_heat_mult, lead_days, notes)

PRODUCTS = [
    # Ice Cream & Frozen
    ("ICE001", "Premium Vanilla Ice Cream 1L", "Ice Cream & Frozen Treats",
     2.5, 0.4, 0.6, 1.3, 3.2, 2, "Top seller in heat waves"),
    ("ICE002", "Gelato Tubs Assorted", "Ice Cream & Frozen Treats",
     2.3, 0.5, 0.6, 1.2, 3.0, 2, None),
    ("ICE003", "Ice Cream Sandwiches 4pk", "Ice Cream & Frozen Treats",
     2.8, 0.3, 0.5, 1.4, 3.5, 2, "Impulse purchase, extreme heat driver"),

    # Salads & Cold Meals
    ("SAL001", "Garden Salad Mix 200g", "Salads & Cold Meals",
     2.0, 0.7, 0.9, 1.3, 2.4, 1, None),
    ("SAL002", "Caesar Salad Kit", "Salads & Cold Meals",
     1.8, 0.7, 0.8, 1.3, 2.2, 1, None),
    ("SAL003", "Poke Bowl Fresh", "Salads & Cold Meals",
     2.2, 0.5, 0.7, 1.4, 2.6, 1, "Premium prepared meal"),

    # Soup & Hot Meals
    ("SOUP01", "Pumpkin Soup 500ml", "Soup & Hot Meals",
     0.5, 2.2, 1.9, 0.7, 0.3, 1, None),
    ("SOUP02", "Chicken Laksa Fresh", "Soup & Hot Meals",
     0.6, 2.0, 1.8, 0.8, 0.4, 1, None),
    ("SOUP03", "Minestrone Soup 500ml", "Soup & Hot Meals",
     0.5, 2.1, 1.8, 0.7, 0.3, 1, None),

    # BBQ Meats
    ("BBQ001", "Beef Sausages Premium 6pk", "BBQ Meats & Sausages",
     2.8, 0.4, 0.3, 1.5, 3.5, 2, "Highest weather-driven item"),
    ("BBQ002", "Lamb Cutlets Marinated", "BBQ Meats & Sausages",
     2.5, 0.5, 0.3, 1.4, 3.0, 2, None),
    ("BBQ003", "Chicken Skewers BBQ 6pk", "BBQ Meats & Sausages",
     2.6, 0.4, 0.3, 1.5, 3.2, 2, None),
    ("BBQ004", "Wagyu Burger Patties 4pk", "BBQ Meats & Sausages",
     2.4, 0.5, 0.4, 1.4, 3.0, 2, None),

    # Fresh Berries
    ("BER001", "Strawberries 250g Punnet", "Fresh Berries",
     1.8, 0.8, 0.9, 1.3, 2.2, 1, "Summer staple, spoilage risk in heat"),
    ("BER002", "Blueberries 125g", "Fresh Berries",
     1.6, 0.8, 0.9, 1.2, 2.0, 1, None),
    ("BER003", "Raspberries 125g", "Fresh Berries",
     1.7, 0.7, 0.8, 1.3, 2.0, 1, None),

    # Tropical Fruit
    ("TRO001", "Watermelon Half", "Tropical Fruit",
     2.5, 0.3, 0.5, 1.4, 3.0, 1, "Iconic summer fruit"),
    ("TRO002", "Mangoes Kensington Pride ea", "Tropical Fruit",
     2.2, 0.4, 0.6, 1.3, 2.8, 1, None),
    ("TRO003", "Pineapple Whole", "Tropical Fruit",
     1.8, 0.5, 0.7, 1.2, 2.2, 1, None),

    # Citrus
    ("CIT001", "Navel Oranges 1kg", "Citrus Fruit",
     0.8, 1.4, 1.1, 1.0, 0.7, 1, "Winter seasonal"),
    ("CIT002", "Lemons Net 500g", "Citrus Fruit",
     1.1, 1.2, 1.0, 1.0, 1.0, 1, "Year-round staple"),

    # Seafood
    ("SEA001", "Tiger Prawns Cooked 500g", "Fresh Seafood",
     2.0, 0.6, 0.5, 1.4, 2.5, 1, "Entertaining / BBQ driver"),
    ("SEA002", "Salmon Fillets 2pk", "Fresh Seafood",
     1.5, 0.8, 0.7, 1.2, 1.8, 1, None),

    # Bakery
    ("PIE001", "Beef & Mushroom Pie", "Bakery Pies & Pastry",
     0.5, 2.0, 1.8, 0.7, 0.3, 1, "Comfort food in cold/rain"),
    ("PIE002", "Sausage Roll 4pk", "Bakery Pies & Pastry",
     0.6, 1.8, 1.6, 0.8, 0.4, 1, None),
    ("BRD001", "Sourdough Loaf", "Fresh Bread & Rolls",
     1.0, 1.1, 1.0, 1.0, 1.0, 1, "Low weather sensitivity"),

    # Beverages
    ("DRK001", "Spring Water 1.5L", "Cold Beverages",
     2.5, 0.5, 0.6, 1.3, 3.5, 1, "Essential in heat"),
    ("DRK002", "Coconut Water 1L", "Cold Beverages",
     2.2, 0.5, 0.6, 1.3, 2.8, 1, None),
    ("DRK003", "Fresh OJ 1L", "Fresh Juice & Smoothies",
     1.8, 0.7, 0.8, 1.3, 2.2, 1, None),
    ("DRK004", "Hot Chocolate Mix", "Hot Beverages & Cocoa",
     0.4, 2.0, 1.8, 0.6, 0.3, 2, None),

    # Deli
    ("DEL001", "Hummus Classic 200g", "Cheese & Dips",
     1.6, 0.7, 0.8, 1.3, 2.0, 1, "Entertaining driver"),
    ("DEL002", "Brie Wheel 200g", "Cheese & Dips",
     1.3, 0.9, 0.9, 1.2, 1.5, 2, None),

    # Pantry
    ("SNK001", "Kettle Chips Sea Salt 175g", "Chips & Snacks",
     1.5, 0.8, 0.8, 1.2, 1.8, 3, None),
    ("CON001", "BBQ Sauce Classic 500ml", "Condiments & Sauces",
     1.8, 0.6, 0.5, 1.3, 2.2, 3, "BBQ essential"),

    # Flowers
    ("FLW001", "Mixed Bouquet Seasonal", "Fresh Flowers",
     1.1, 0.9, 0.5, 0.7, 1.3, 1, "Rain/wind kills outdoor display traffic"),

    # Root veg
    ("VEG001", "Sweet Potato 1kg", "Root Vegetables",
     0.7, 1.5, 1.3, 1.0, 0.8, 1, "Soup & roast ingredient"),
    ("VEG002", "Carrots 1kg Bag", "Root Vegetables",
     0.8, 1.3, 1.1, 1.0, 0.9, 1, None),

    # Leafy greens
    ("GRN001", "Baby Spinach 120g", "Leafy Greens",
     1.5, 0.8, 0.9, 1.2, 1.8, 1, "Salad base"),

    # Wine & Beer
    ("ALC001", "Rose Wine 750ml", "Wine & Beer",
     2.0, 0.5, 0.6, 1.4, 2.5, 2, "Summer entertaining essential"),
    ("ALC002", "Craft Beer 6pk", "Wine & Beer",
     1.8, 0.7, 0.6, 1.3, 2.2, 2, None),

    # Stone Fruit
    ("STF001", "Nectarines 500g", "Stone Fruit",
     2.0, 0.4, 0.6, 1.3, 2.4, 1, "Peak summer"),
    ("STF002", "Peaches Yellow 500g", "Stone Fruit",
     1.9, 0.4, 0.6, 1.3, 2.3, 1, None),

    # Yoghurt
    ("YOG001", "Greek Yoghurt 500g", "Yoghurt & Dairy Desserts",
     1.5, 0.8, 0.9, 1.2, 1.8, 1, None),
]


# =========================================================================
# SAMPLE STORES (Sydney metro)
# =========================================================================

SAMPLE_STORES = [
    (1,  "Frenchs Forest",  "Frenchs Forest",  "NSW", "2086", -33.7519, 151.2297),
    (28, "Mosman",          "Mosman",           "NSW", "2088", -33.8298, 151.2444),
    (3,  "Brookvale",       "Brookvale",        "NSW", "2100", -33.7619, 151.2714),
    (4,  "Neutral Bay",     "Neutral Bay",      "NSW", "2089", -33.8298, 151.2196),
    (5,  "Willoughby",      "Willoughby",       "NSW", "2068", -33.8006, 151.1944),
]


# =========================================================================
# POPULATION FUNCTIONS
# =========================================================================

def populate_categories(loader):
    """Add all weather-impact categories to the database."""
    for name, dept, heat, cold, rain, wind, desc in CATEGORIES:
        loader.add_weather_category(name, dept, heat, cold, rain, wind, desc)
    print(f"  Added {len(CATEGORIES)} weather-impact categories")


def populate_products(loader):
    """Add all product-weather profiles to the database."""
    for row in PRODUCTS:
        code, name, cat = row[0], row[1], row[2]
        hot, cold, rain, sunny = row[3], row[4], row[5], row[6]
        extreme = row[7] if len(row) > 7 else None
        lead = row[8] if len(row) > 8 else 1
        notes = row[9] if len(row) > 9 else None
        loader.add_product_profile(
            code, name, cat,
            hot=hot, cold=cold, rain=rain, sunny=sunny,
            extreme_heat=extreme, lead_days=lead, notes=notes,
        )
    print(f"  Added {len(PRODUCTS)} product-weather profiles")


def populate_stores(loader):
    """Add sample Sydney stores to the database."""
    for sid, name, suburb, state, postcode, lat, lon in SAMPLE_STORES:
        loader.add_store(sid, name, suburb, state, postcode, lat, lon)
    print(f"  Added {len(SAMPLE_STORES)} sample stores")


def populate_all(loader=None):
    """Populate the database with all example data."""
    if loader is None:
        loader = WeatherDataLoader()
        loader.initialize_database()

    populate_stores(loader)
    populate_categories(loader)
    populate_products(loader)
    loader.close()
    print("  Example data population complete.")


# =========================================================================
# CLI
# =========================================================================

if __name__ == "__main__":
    print("Populating Harris Farm Weather database with example data ...")
    populate_all()
    print("Done.")
