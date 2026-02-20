"""
Harris Farm Hub -- Data Loader
Downloads data files from GitHub Releases on first deploy.
Files are stored on Render's persistent disk at /data/.
"""

import os
import sys
import urllib.request

# ---------------------------------------------------------------------------
# GitHub Release configuration
# ---------------------------------------------------------------------------
REPO = "anguspharris-lab/harris-farm-hub"
RELEASE_TAG = "data-v1"
_BASE_URL = f"https://github.com/{REPO}/releases/download/{RELEASE_TAG}"

# Files to download: local path -> {url(s), size_mb, description}
# Files over 2GB are split into parts and reassembled after download.
DATA_FILES = {
    "data/harris_farm.db": {
        "urls": [f"{_BASE_URL}/harris_farm.db"],
        "size_mb": 399,
        "description": "Weekly aggregated sales, customer & market share data",
    },
    "data/transactions/FY24.parquet": {
        "urls": [
            f"{_BASE_URL}/FY24.parquet.part_aa",
            f"{_BASE_URL}/FY24.parquet.part_ab",
        ],
        "size_mb": 2336,
        "description": "POS transactions FY24 (Jul 2023 - Jun 2024, 134M rows)",
    },
    "data/transactions/FY25.parquet": {
        "urls": [
            f"{_BASE_URL}/FY25.parquet.part_aa",
            f"{_BASE_URL}/FY25.parquet.part_ab",
        ],
        "size_mb": 2675,
        "description": "POS transactions FY25 (Jul 2024 - Jun 2025, 149M rows)",
    },
    "data/transactions/FY26.parquet": {
        "urls": [f"{_BASE_URL}/FY26.parquet"],
        "size_mb": 1773,
        "description": "POS transactions FY26 YTD (Jul 2025 - Feb 2026, 99M rows)",
    },
}


def download_file(url, dest):
    """Download a file from a URL with progress reporting."""
    filename = os.path.basename(url)
    print(f"  Downloading {filename}...", flush=True)
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "HarrisFarmHub-DataLoader/1.0")
        response = urllib.request.urlopen(req)

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
                        f"\r  {filename}... {mb:.0f}MB ({pct:.0f}%)",
                        end="", flush=True,
                    )
                else:
                    print(
                        f"\r  {filename}... {mb:.0f}MB",
                        end="", flush=True,
                    )

        size_mb = os.path.getsize(dest) / (1024 * 1024)
        print(f"\n  Done: {filename} ({size_mb:.1f}MB)")
        return True

    except Exception as e:
        print(f"\n  Failed: {filename}: {e}")
        if os.path.exists(dest):
            os.remove(dest)
        return False


def download_and_assemble(dest, urls):
    """Download one or more parts and concatenate into the final file."""
    if len(urls) == 1:
        return download_file(urls[0], dest)

    # Multi-part: download parts, concatenate, clean up
    parts = []
    for i, url in enumerate(urls):
        part_path = f"{dest}.part{i}"
        if not download_file(url, part_path):
            # Clean up any downloaded parts
            for p in parts:
                if os.path.exists(p):
                    os.remove(p)
            return False
        parts.append(part_path)

    # Concatenate parts into final file
    print(f"  Assembling {os.path.basename(dest)} from {len(parts)} parts...")
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    with open(dest, "wb") as out:
        for part_path in parts:
            with open(part_path, "rb") as inp:
                while True:
                    chunk = inp.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            os.remove(part_path)

    size_mb = os.path.getsize(dest) / (1024 * 1024)
    print(f"  Assembled: {os.path.basename(dest)} ({size_mb:.1f}MB)")
    return True


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
    print(f"  Total download: ~{total_mb:.0f} MB (first deploy only)\n")

    failed = []
    for filepath, info in missing.items():
        if not download_and_assemble(filepath, info["urls"]):
            failed.append(filepath)

    if failed:
        print(f"\n{len(failed)} file(s) failed. Some dashboards may not work.")
        return False

    print(f"\nAll data files downloaded successfully")
    return True


if __name__ == "__main__":
    ensure_data()
