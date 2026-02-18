"""
Harris Farm Hub -- Configure Google Drive Download URLs

Reads gdrive_urls.txt and updates data_loader.py with real file IDs.

Usage:
  1. Upload files to Google Drive (Share > Anyone with the link > Viewer)
  2. Create gdrive_urls.txt with one entry per line:
       filename=FILE_ID
     Example:
       harris_farm.db=1aBcDeFgHiJkLmNoPqRsTuVwXyZ
       FY24.parquet=2aBcDeFgHiJkLmNoPqRsTuVwXyZ
       FY25.parquet=3aBcDeFgHiJkLmNoPqRsTuVwXyZ
       FY26.parquet=4aBcDeFgHiJkLmNoPqRsTuVwXyZ
  3. Run: python3 configure_urls.py
"""

import os
import re
import sys

URL_FILE = "gdrive_urls.txt"
LOADER_FILE = "data_loader.py"

# Map short names to the local paths used in data_loader.py
NAME_TO_PATH = {
    "harris_farm.db": "data/harris_farm.db",
    "FY24.parquet": "data/transactions/FY24.parquet",
    "FY25.parquet": "data/transactions/FY25.parquet",
    "FY26.parquet": "data/transactions/FY26.parquet",
}


def parse_urls():
    """Parse gdrive_urls.txt — accepts FILE_ID or full Drive URLs."""
    if not os.path.exists(URL_FILE):
        print(f"ERROR: {URL_FILE} not found.")
        print(f"Create it with one entry per line: filename=FILE_ID_OR_URL")
        print(f"\nExample:")
        for name in NAME_TO_PATH:
            print(f"  {name}=1aBcDeFgHiJkLmNoPqRsTuVwXyZ")
        sys.exit(1)

    mapping = {}
    with open(URL_FILE) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                print(f"WARNING: Skipping line {line_num} (no '=' found): {line}")
                continue

            name, value = line.split("=", 1)
            name = name.strip()
            value = value.strip()

            # Extract file ID from full URL if needed
            # e.g. https://drive.google.com/file/d/XXXXX/view?usp=sharing
            url_match = re.search(r"/d/([a-zA-Z0-9_-]+)", value)
            if url_match:
                file_id = url_match.group(1)
            else:
                # Assume it's a raw file ID
                file_id = value

            if name not in NAME_TO_PATH:
                print(f"WARNING: Unknown file '{name}' on line {line_num}. "
                      f"Expected one of: {', '.join(NAME_TO_PATH.keys())}")
                continue

            mapping[name] = file_id

    return mapping


def update_data_loader(mapping):
    """Replace REPLACE_WITH_FILE_ID placeholders in data_loader.py."""
    with open(LOADER_FILE) as f:
        content = f.read()

    updated_count = 0
    for name, file_id in mapping.items():
        local_path = NAME_TO_PATH[name]
        # Find the entry for this file and replace its FILE_ID
        old_pattern = (
            f'"{local_path}": {{\n'
            f'        "url": "https://drive.google.com/uc?export=download&id=REPLACE_WITH_FILE_ID"'
        )
        new_value = (
            f'"{local_path}": {{\n'
            f'        "url": "https://drive.google.com/uc?export=download&id={file_id}"'
        )
        if old_pattern in content:
            content = content.replace(old_pattern, new_value)
            updated_count += 1
        elif f"id={file_id}" in content:
            print(f"  {name}: already configured (skipped)")
        else:
            # Try replacing any existing ID for this path
            pattern = re.escape(f'"{local_path}"') + r'.*?id=([a-zA-Z0-9_-]+)"'
            if re.search(pattern, content, re.DOTALL):
                print(f"  {name}: updating existing ID")
                old = re.search(
                    re.escape(f'"{local_path}": {{') + r'\n\s+"url": "https://drive\.google\.com/uc\?export=download&id=[^"]+"',
                    content
                )
                if old:
                    content = content.replace(
                        old.group(0),
                        f'"{local_path}": {{\n        "url": "https://drive.google.com/uc?export=download&id={file_id}"'
                    )
                    updated_count += 1

    with open(LOADER_FILE, "w") as f:
        f.write(content)

    return updated_count


def main():
    print("Harris Farm Hub -- Configure Google Drive URLs")
    print("=" * 50)
    print()

    mapping = parse_urls()

    if not mapping:
        print("ERROR: No valid entries found in gdrive_urls.txt")
        sys.exit(1)

    print(f"Found {len(mapping)} file ID(s) in {URL_FILE}:")
    for name, file_id in mapping.items():
        print(f"  {name} -> {file_id[:20]}...")
    print()

    updated = update_data_loader(mapping)
    print(f"\nUpdated {updated} URL(s) in {LOADER_FILE}")

    # Check for any remaining placeholders
    with open(LOADER_FILE) as f:
        content = f.read()
    remaining = content.count("REPLACE_WITH_FILE_ID")
    if remaining:
        missing = []
        for name, path in NAME_TO_PATH.items():
            if name not in mapping:
                missing.append(name)
        print(f"\nWARNING: {remaining} file(s) still need URLs:")
        for name in missing:
            print(f"  - {name}")
    else:
        print("\nAll files configured! data_loader.py is ready.")
        print("Rebuild the Replit zip to include the updated URLs.")


if __name__ == "__main__":
    main()
