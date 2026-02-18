#!/usr/bin/env python3
"""
Harris Farm Hub -- Google Drive URL Setup (Interactive)

Opens the HarrisFarmHub folder in Google Drive, then prompts you
to share each file and paste the link. Auto-updates data_loader.py.

Usage:
  python3 setup_gdrive_urls.py
"""

import os
import re
import subprocess
import sys
import webbrowser
import time

LOADER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_loader.py")

FILES = [
    {
        "name": "harris_farm.db",
        "local_path": "data/harris_farm.db",
        "size": "399 MB",
    },
    {
        "name": "FY24.parquet",
        "local_path": "data/transactions/FY24.parquet",
        "size": "2.3 GB",
    },
    {
        "name": "FY25.parquet",
        "local_path": "data/transactions/FY25.parquet",
        "size": "2.6 GB",
    },
    {
        "name": "FY26.parquet",
        "local_path": "data/transactions/FY26.parquet",
        "size": "1.7 GB",
    },
]


def extract_file_id(url_or_id):
    """Extract Google Drive file ID from a share URL or raw ID."""
    url_or_id = url_or_id.strip()
    # Full URL: https://drive.google.com/file/d/XXXXX/view?usp=sharing
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    # Open URL: https://drive.google.com/open?id=XXXXX
    match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    # Raw file ID (no slashes, no spaces, reasonable length)
    if re.match(r"^[a-zA-Z0-9_-]{10,}$", url_or_id):
        return url_or_id
    return None


def update_data_loader(file_ids):
    """Replace placeholder URLs in data_loader.py with real file IDs."""
    with open(LOADER_FILE) as f:
        content = f.read()

    updated = 0
    for local_path, file_id in file_ids.items():
        # Replace placeholder for this specific file
        old = f'"{local_path}": {{\n        "url": "https://drive.google.com/uc?export=download&id=REPLACE_WITH_FILE_ID"'
        new = f'"{local_path}": {{\n        "url": "https://drive.google.com/uc?export=download&id={file_id}"'
        if old in content:
            content = content.replace(old, new)
            updated += 1
        else:
            # Already has a different ID — replace it
            pattern = (
                re.escape(f'"{local_path}": {{')
                + r'\n\s+"url": "https://drive\.google\.com/uc\?export=download&id=[^"]+"'
            )
            replacement = (
                f'"{local_path}": {{\n'
                f'        "url": "https://drive.google.com/uc?export=download&id={file_id}"'
            )
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                updated += 1

    with open(LOADER_FILE, "w") as f:
        f.write(content)

    return updated


def main():
    print()
    print("=" * 56)
    print("  Harris Farm Hub -- Google Drive URL Setup")
    print("=" * 56)
    print()
    print("  Files are in: My Drive/HarrisFarmHub/")
    print("  Google Drive will sync them automatically.")
    print()
    print("  Opening the folder in your browser now...")
    print()

    # Open Google Drive web — search for the folder
    webbrowser.open("https://drive.google.com/drive/my-drive")
    time.sleep(2)

    print("-" * 56)
    print("  FOR EACH FILE:")
    print("  1. Right-click the file in Google Drive")
    print("  2. Share > General access > 'Anyone with the link'")
    print("  3. Click 'Copy link'")
    print("  4. Paste below")
    print("-" * 56)
    print()

    file_ids = {}
    for f in FILES:
        while True:
            link = input(
                f"  Paste link for {f['name']} ({f['size']})\n"
                f"  (or 'skip' to skip): "
            ).strip()

            if link.lower() == "skip":
                print(f"  -- Skipped {f['name']}\n")
                break

            file_id = extract_file_id(link)
            if file_id:
                file_ids[f["local_path"]] = file_id
                print(f"  -- Got ID: {file_id[:25]}...\n")
                break
            else:
                print("  -- Could not extract file ID. Try pasting the full share URL.\n")

    if not file_ids:
        print("No URLs provided. Exiting.")
        sys.exit(1)

    print()
    print(f"Updating data_loader.py with {len(file_ids)} URL(s)...")
    updated = update_data_loader(file_ids)
    print(f"Updated {updated} URL(s) in data_loader.py")

    # Check for remaining placeholders
    with open(LOADER_FILE) as f:
        remaining = f.read().count("REPLACE_WITH_FILE_ID")
    # Subtract 1 for the comment on line 15
    config_remaining = max(0, remaining - 1)
    if config_remaining:
        print(f"\nNote: {config_remaining} file(s) still have placeholder URLs.")
        print("Re-run this script to add them later.")
    else:
        print("\nAll 4 files configured!")

    # Rebuild zip
    print()
    rebuild = input("Rebuild harris-farm-hub-replit.zip now? (y/n): ").strip().lower()
    if rebuild == "y":
        print("\nBuilding zip...")
        os.system(
            'cd "' + os.path.dirname(os.path.abspath(__file__)) + '" && '
            "rm -f harris-farm-hub-replit.zip && "
            "zip -r harris-farm-hub-replit.zip . "
            '-x ".git/*" -x "venv/*" -x "__pycache__/*" -x "*.pyc" '
            '-x ".DS_Store" -x ".claude/*" -x "logs/*" '
            '-x "data/harris_farm.db" -x "data/transactions/*" '
            '-x "*.db-wal" -x "*.db-shm" -x ".env" '
            '-x "gdrive_urls.txt" -x "token.pickle" '
            '-x "harris-farm-hub-replit.zip" -x ".hub_pids" '
            '-x ".deps_installed" -x ".cache/*" -x ".pytest_cache/*" '
            "> /dev/null 2>&1"
        )
        size = os.path.getsize(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "harris-farm-hub-replit.zip")
        )
        print(f"  harris-farm-hub-replit.zip ({size / 1024 / 1024:.1f} MB)")
        print()
        print("=" * 56)
        print("  DONE! Upload the zip to Replit and click Run.")
        print("  Data files will download automatically (~7 GB).")
        print("=" * 56)
    else:
        print("\nSkipped zip rebuild. Run manually when ready:")
        print("  python3 configure_urls.py && bash -c 'zip -r ...'")

    print()


if __name__ == "__main__":
    main()
