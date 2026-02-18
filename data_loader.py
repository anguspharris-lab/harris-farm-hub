"""
Harris Farm Hub -- External Data Loader
Downloads large data files from Google Drive on first run (Replit deployment).
"""

import os
import re
import sys
import http.cookiejar
import urllib.request

# ---------------------------------------------------------------------------
# DATA FILE REGISTRY
# Map of local file paths to Google Drive download URLs.
# After uploading to Drive, replace REPLACE_WITH_FILE_ID with the real ID.
# ---------------------------------------------------------------------------

DATA_FILES = {
    "data/harris_farm.db": {
        "url": "https://drive.google.com/uc?export=download&id=REPLACE_WITH_FILE_ID",
        "size_mb": 399,
        "description": "Weekly aggregated sales, customer & market share data",
    },
    "data/transactions/FY24.parquet": {
        "url": "https://drive.google.com/uc?export=download&id=REPLACE_WITH_FILE_ID",
        "size_mb": 2355,
        "description": "POS transactions FY24 (Jul 2023 - Jun 2024, 134M rows)",
    },
    "data/transactions/FY25.parquet": {
        "url": "https://drive.google.com/uc?export=download&id=REPLACE_WITH_FILE_ID",
        "size_mb": 2663,
        "description": "POS transactions FY25 (Jul 2024 - Jun 2025, 149M rows)",
    },
    "data/transactions/FY26.parquet": {
        "url": "https://drive.google.com/uc?export=download&id=REPLACE_WITH_FILE_ID",
        "size_mb": 1741,
        "description": "POS transactions FY26 YTD (Jul 2025 - Feb 2026, 99M rows)",
    },
}


def download_from_gdrive(url, dest):
    """Download a file from Google Drive, handling the large-file
    virus-scan confirmation page that appears for files >100MB."""
    print(f"  Downloading {os.path.basename(dest)}...", flush=True)
    try:
        cookiejar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookiejar)
        )

        # First request -- may return a confirmation page for large files
        response = opener.open(url)
        content_type = response.headers.get("Content-Type", "")

        if "text/html" in content_type:
            html = response.read().decode("utf-8")
            # Extract confirm token from the warning page
            match = re.search(r"confirm=([0-9A-Za-z_-]+)", html)
            if match:
                confirm_url = f"{url}&confirm={match.group(1)}"
                response = opener.open(confirm_url)
            else:
                # Fallback: uuid-based confirmation
                match = re.search(r"uuid=([0-9A-Za-z_-]+)", html)
                if match:
                    confirm_url = f"{url}&confirm=t&uuid={match.group(1)}"
                    response = opener.open(confirm_url)

        # Stream to disk with progress
        total = response.headers.get("Content-Length")
        downloaded = 0
        block_size = 1024 * 1024  # 1 MB chunks

        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        with open(dest, "wb") as f:
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                mb = downloaded / (1024 * 1024)
                if total:
                    pct = (downloaded / int(total)) * 100
                    print(
                        f"\r  Downloading {os.path.basename(dest)}... "
                        f"{mb:.0f}MB ({pct:.0f}%)",
                        end="",
                        flush=True,
                    )
                else:
                    print(
                        f"\r  Downloading {os.path.basename(dest)}... {mb:.0f}MB",
                        end="",
                        flush=True,
                    )

        size_mb = os.path.getsize(dest) / (1024 * 1024)
        print(f"\n  Downloaded {os.path.basename(dest)} ({size_mb:.1f}MB)")
        return True

    except Exception as e:
        print(f"\n  Failed to download {os.path.basename(dest)}: {e}")
        if os.path.exists(dest):
            os.remove(dest)  # Clean up partial download
        return False


def ensure_data():
    """Check all required data files exist; download any missing ones."""
    missing = {}
    for filepath, info in DATA_FILES.items():
        if not os.path.exists(filepath):
            missing[filepath] = info

    if not missing:
        print("All data files present")
        return True

    print(f"Need to download {len(missing)} data file(s)...")
    total_mb = sum(info["size_mb"] for info in missing.values())
    print(f"  Total download: ~{total_mb:.0f} MB (first run only)\n")

    failed = []
    for filepath, info in missing.items():
        url = info["url"]
        if "REPLACE_WITH_FILE_ID" in url:
            print(f"  {filepath}: No download URL configured yet!")
            print(
                "    Edit data_loader.py and replace "
                "REPLACE_WITH_FILE_ID with your Google Drive file ID"
            )
            failed.append(filepath)
            continue
        if not download_from_gdrive(url, filepath):
            failed.append(filepath)

    if failed:
        print(f"\n{len(failed)} file(s) missing. Some dashboards may not work.")
        return False

    print(f"\nAll data files downloaded successfully")
    return True


if __name__ == "__main__":
    ensure_data()
