#!/usr/bin/env bash
# Harris Farm Weather — Installation Script
# Sets up database, dependencies, sample data, and directory structure.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  Harris Farm Weather — Installation"
echo "============================================"
echo

# 1. Python version check
echo "[1/6] Checking Python version ..."
PYTHON="python3"
if ! command -v "$PYTHON" &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.8+ first."
    exit 1
fi

PY_VER=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$($PYTHON -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$($PYTHON -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]; }; then
    echo "ERROR: Python 3.8+ required (found $PY_VER)"
    exit 1
fi
echo "  Python $PY_VER — OK"

# 2. Install dependencies
echo "[2/6] Installing Python dependencies ..."
$PYTHON -m pip install --quiet --user -r requirements.txt
echo "  Dependencies installed"

# 3. Create directories
echo "[3/6] Creating directories ..."
mkdir -p logs backups exports
echo "  logs/ backups/ exports/ — created"

# 4. Initialise database
echo "[4/6] Initialising database ..."
$PYTHON -c "
from weather_data_loader import WeatherDataLoader
loader = WeatherDataLoader()
loader.initialize_database()
loader.close()
print('  Database created at weather.db')
"

# 5. Populate sample data
echo "[5/6] Populating sample stores, categories, and products ..."
$PYTHON -c "
from example_products import populate_all
populate_all()
"

# 6. Verify
echo "[6/6] Verifying installation ..."
$PYTHON -c "
import sqlite3
conn = sqlite3.connect('weather.db')
stores = conn.execute('SELECT COUNT(*) FROM stores').fetchone()[0]
cats   = conn.execute('SELECT COUNT(*) FROM weather_impact_categories').fetchone()[0]
prods  = conn.execute('SELECT COUNT(*) FROM product_weather_profiles').fetchone()[0]
conn.close()
print(f'  Stores:     {stores}')
print(f'  Categories: {cats}')
print(f'  Products:   {prods}')
"

echo
echo "============================================"
echo "  Installation Complete"
echo "============================================"
echo
echo "Next steps:"
echo "  1. Sign up for a free API key at https://www.weatherapi.com/"
echo "  2. Fetch your first forecast:"
echo "     python3 weather_data_loader.py --fetch YOUR_API_KEY"
echo "  3. Run the dashboard:"
echo "     python3 weather_dashboard.py"
echo "  4. Run tests:"
echo "     python3 test_system.py"
echo
