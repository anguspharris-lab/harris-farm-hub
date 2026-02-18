#!/usr/bin/env python3
"""
Extract text from Harris Farm policy documents into hub_data.db knowledge_base table.

Sources:
  1. OneDrive_1_14-02-2026 — operational procedures (NUTS), department guides, golden rules
  2. Current Policies — HR policies (POL), safety systems (SYS)

Features:
  - Skips archived/outdated folders
  - Prefers .docx over .pdf when both exist (better text extraction)
  - Maps 31 raw folder names into 11 meaningful categories
  - Chunks long documents (>2000 words) into ~1000-word segments
  - Deduplicates via SHA-256 content hash
  - Rebuilds FTS5 search index after extraction

Usage:
  python3 scripts/extract_knowledge.py            # incremental (add new docs)
  python3 scripts/extract_knowledge.py --rebuild   # wipe and rebuild from scratch
"""

import argparse
import hashlib
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import PyPDF2
import docx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SOURCES = [
    {
        "name": "OneDrive Procedures",
        "path": Path("/Users/angusharris/Downloads/OneDrive_1_14-02-2026"),
        "recursive": True,
        "category_mode": "folder",
    },
    {
        "name": "Current Policies",
        "path": Path("/Users/angusharris/Downloads/Current Policies"),
        "recursive": False,   # root-level files only
        "category_mode": "policy",
    },
]

HUB_DB = Path(__file__).parent.parent / "backend" / "hub_data.db"

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
CHUNK_THRESHOLD = 2000  # words — chunk if longer
CHUNK_TARGET = 1000     # words per chunk
CHUNK_OVERLAP = 100     # word overlap between chunks

# Folders to skip (matched case-insensitively against any path component)
SKIP_PATTERNS = {"archive", "archived", "archieved", "outdated", "250516"}

# Map raw folder names to consolidated categories
CATEGORY_MAP = {
    "fruit and veg": "Fresh Produce",
    "flowers": "Fresh Produce",
    "bakery": "Perishables",
    "cheese": "Perishables",
    "deli": "Perishables",
    "proteins": "Perishables",
    "perishables": "Perishables",
    "production": "Perishables",
    "service": "Store Operations",
    "ccr": "Store Operations",
    "back dock": "Store Operations",
    "grocery": "Store Operations",
    "cellar door": "Store Operations",
    "barcelona bar": "Store Operations",
    "coffee cart": "Store Operations",
    "the juggler": "Store Operations",
    "upcycle": "Store Operations",
    "online": "Online & Delivery",
    "warehouse": "Warehouse & Logistics",
    "people & culture": "People & Culture",
    "succession planning": "People & Culture",
    "dayforce": "Systems & Technology",
    "d365": "Systems & Technology",
    "donesafe": "Systems & Technology",
    "it": "Systems & Technology",
    "livehire": "Systems & Technology",
    "safety": "Safety & Compliance",
    "finance": "Finance & Marketing",
    "marketing": "Finance & Marketing",
    "2025 - golden rules": "Golden Rules",
}


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_pdf(filepath):
    """Extract text from a PDF file."""
    try:
        reader = PyPDF2.PdfReader(str(filepath))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as e:
        print(f"  WARN: PDF extraction failed for {filepath.name}: {e}")
        return ""


def extract_docx(filepath):
    """Extract text from a DOCX file."""
    try:
        doc = docx.Document(str(filepath))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        print(f"  WARN: DOCX extraction failed for {filepath.name}: {e}")
        return ""


def clean_text(text):
    """Normalise whitespace and remove control characters."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text, filename):
    """Split text into chunks if it exceeds CHUNK_THRESHOLD words."""
    words = text.split()
    word_count = len(words)

    if word_count <= CHUNK_THRESHOLD:
        return [{
            "content": text,
            "word_count": word_count,
            "chunk_index": 0,
            "chunk_total": 1,
        }]

    chunks = []
    start = 0
    chunk_idx = 0

    while start < word_count:
        end = min(start + CHUNK_TARGET, word_count)
        chunk_words = words[start:end]

        chunks.append({
            "content": " ".join(chunk_words),
            "word_count": len(chunk_words),
            "chunk_index": chunk_idx,
            "chunk_total": -1,
        })

        start = end - CHUNK_OVERLAP if end < word_count else word_count
        chunk_idx += 1

    for c in chunks:
        c["chunk_total"] = len(chunks)

    return chunks


def content_hash(text):
    """SHA-256 hash for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# File collection and filtering
# ---------------------------------------------------------------------------

def should_skip_path(filepath, base_dir):
    """Return True if any path component matches a skip pattern."""
    rel = filepath.relative_to(base_dir)
    for part in rel.parts:
        part_lower = part.lower().strip()
        if part_lower in SKIP_PATTERNS:
            return True
        if any(pat in part_lower for pat in SKIP_PATTERNS):
            return True
    return False


def get_category(filepath, base_dir, category_mode="folder"):
    """Map a filepath to a consolidated category."""
    if category_mode == "policy":
        return "Company Policy"
    rel = filepath.relative_to(base_dir)
    parts = rel.parts
    folder = parts[0] if len(parts) > 1 else "Uncategorised"
    return CATEGORY_MAP.get(folder.lower(), folder)


def collect_files(source_dir, recursive=True):
    """Collect supported files, preferring .docx when both .docx and .pdf exist."""
    all_files = []
    for ext in SUPPORTED_EXTENSIONS:
        if recursive:
            all_files.extend(source_dir.rglob(f"*{ext}"))
        else:
            all_files.extend(source_dir.glob(f"*{ext}"))

    # Filter out archived/outdated folders
    all_files = [f for f in all_files if not should_skip_path(f, source_dir)]

    # Build set of (parent, stem) pairs that have a .docx version
    docx_stems = set()
    for f in all_files:
        if f.suffix.lower() == ".docx":
            docx_stems.add((f.parent, f.stem))

    # Skip .pdf files when a .docx with the same stem exists
    result = []
    pdf_skipped = 0
    for f in all_files:
        if f.suffix.lower() == ".pdf" and (f.parent, f.stem) in docx_stems:
            pdf_skipped += 1
            continue
        result.append(f)

    return sorted(result), pdf_skipped


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def init_knowledge_table(conn):
    """Create knowledge_base table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            category TEXT,
            doc_type TEXT,
            content TEXT NOT NULL,
            content_hash TEXT UNIQUE,
            word_count INTEGER,
            chunk_index INTEGER DEFAULT 0,
            chunk_total INTEGER DEFAULT 1,
            extracted_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_kb_hash ON knowledge_base(content_hash)")
    conn.commit()


def rebuild_fts_index(conn):
    """Rebuild the FTS5 search index from knowledge_base data."""
    try:
        conn.execute("DELETE FROM knowledge_fts")
        conn.execute("""
            INSERT INTO knowledge_fts(rowid, filename, category, content)
            SELECT id, filename, category, content FROM knowledge_base
        """)
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM knowledge_fts").fetchone()[0]
        print(f"  FTS5 index rebuilt: {count} rows indexed")
    except Exception as e:
        print(f"  WARN: FTS5 rebuild skipped ({e})")
        print("  Run the backend once to create the FTS5 table, then re-run extraction.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(rebuild=False):
    print("=" * 60)
    print("Harris Farm Hub — Knowledge Base Extraction")
    print("=" * 60)

    conn = sqlite3.connect(str(HUB_DB))
    init_knowledge_table(conn)

    if rebuild:
        conn.execute("DELETE FROM knowledge_base")
        conn.commit()
        print("  Cleared existing knowledge_base (rebuild mode)")

    existing_hashes = set(
        r[0] for r in conn.execute("SELECT content_hash FROM knowledge_base").fetchall()
    )
    print(f"  Existing documents in KB: {len(existing_hashes)}")

    now = datetime.utcnow().isoformat() + "Z"
    grand_extracted = 0
    grand_skipped = 0
    grand_failed = 0
    grand_chunks = 0

    for source in SOURCES:
        source_dir = source["path"]
        source_name = source["name"]
        category_mode = source["category_mode"]
        recursive = source.get("recursive", True)

        print(f"\n--- Source: {source_name} ---")
        print(f"  Path: {source_dir}")

        if not source_dir.exists():
            print(f"  WARN: Directory not found, skipping")
            continue

        files, pdf_skipped = collect_files(source_dir, recursive=recursive)
        pdf_count = sum(1 for f in files if f.suffix.lower() == ".pdf")
        docx_count = sum(1 for f in files if f.suffix.lower() == ".docx")
        print(f"  Files to process: {len(files)} (DOCX: {docx_count}, PDF: {pdf_count})")
        print(f"  PDFs skipped (docx exists): {pdf_skipped}")

        extracted = 0
        skipped = 0
        failed = 0

        for i, filepath in enumerate(files):
            ext = filepath.suffix.lower()

            if ext == ".pdf":
                text = extract_pdf(filepath)
            elif ext == ".docx":
                text = extract_docx(filepath)
            else:
                continue

            text = clean_text(text)

            if not text or len(text) < 20:
                skipped += 1
                continue

            category = get_category(filepath, source_dir, category_mode)
            chunks = chunk_text(text, filepath.name)

            doc_inserted = False
            for chunk in chunks:
                h = content_hash(chunk["content"])
                if h in existing_hashes:
                    continue

                try:
                    conn.execute(
                        """INSERT INTO knowledge_base
                           (source_path, filename, category, doc_type, content,
                            content_hash, word_count, chunk_index, chunk_total, extracted_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            str(filepath.relative_to(source_dir)),
                            filepath.name,
                            category,
                            ext.lstrip("."),
                            chunk["content"],
                            h,
                            chunk["word_count"],
                            chunk["chunk_index"],
                            chunk["chunk_total"],
                            now,
                        ),
                    )
                    existing_hashes.add(h)
                    grand_chunks += 1
                    doc_inserted = True
                except sqlite3.IntegrityError:
                    pass  # duplicate hash

            if doc_inserted:
                extracted += 1
            else:
                skipped += 1

            if (i + 1) % 50 == 0:
                conn.commit()
                print(f"  Processed {i + 1}/{len(files)} files...")

        conn.commit()
        print(f"  Extracted: {extracted}, Skipped: {skipped}, Failed: {failed}")
        grand_extracted += extracted
        grand_skipped += skipped
        grand_failed += failed

    # Rebuild FTS5 index
    print("\nRebuilding FTS5 search index...")
    rebuild_fts_index(conn)

    # Summary
    total_rows = conn.execute("SELECT COUNT(*) FROM knowledge_base").fetchone()[0]
    total_words = conn.execute(
        "SELECT COALESCE(SUM(word_count), 0) FROM knowledge_base"
    ).fetchone()[0]
    cat_stats = conn.execute(
        "SELECT category, COUNT(*) as n, SUM(word_count) as w "
        "FROM knowledge_base GROUP BY category ORDER BY n DESC"
    ).fetchall()

    conn.close()

    print(f"\n{'=' * 60}")
    print("EXTRACTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Documents extracted: {grand_extracted}")
    print(f"Skipped (empty/duplicate): {grand_skipped}")
    print(f"Failed: {grand_failed}")
    print(f"Total chunks in KB: {total_rows} ({grand_chunks} new)")
    print(f"Total words: {total_words:,}")
    print(f"\nCategory breakdown:")
    for cat, n, w in cat_stats:
        print(f"  {cat:25s}  {n:4d} chunks  {w:>8,} words")
    print(f"\nDatabase: {HUB_DB}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract policy docs into knowledge base")
    parser.add_argument("--rebuild", action="store_true",
                        help="Wipe and rebuild KB from scratch")
    args = parser.parse_args()
    main(rebuild=args.rebuild)
