#!/usr/bin/env python3
"""
build-data.py
Processes the PERC Hold Tags CSV export into clean JSON for the Hold Melt Dashboard.

Usage:
    python scripts/build-data.py

Input:  data/*.csv  (most recent CSV matching the expected format)
Output: src/data/holds.json

The output JSON contains individual hold records with raw dates.
All melt-curve computation happens at dashboard runtime so that
settings like hold-release delay can be adjusted live.

Designed to be forward-compatible with wildcard PERC exports:
  - Currently filters to INS-prefixed restrictions only
  - All class standings are included (SR, ALUM, etc.) for accurate melt curves
  - Class-level breakdown (FY/SO/JR) is only used for the current cohort at dashboard runtime
"""

import csv
import json
import glob
import hashlib
import os
import sys
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────

# Where to look for the CSV (relative to project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "src", "data", "holds.json")
SALT_PATH = os.path.join(PROJECT_ROOT, ".salt")

# Filters (adjust these when switching to wildcard exports)
RESTRICTION_PREFIX = "INS"          # Only include restrictions starting with this
EXCLUDED_CLASSES = set()  # No class exclusions - all records included for melt curves
                          # Class breakdown (FY/SO/JR) is handled at dashboard runtime
                          # and only applies to the current cohort where data is accurate

# Academic year mapping: restriction code -> display label
# Add new codes here as new cycles begin
YEAR_LABELS = {
    "INS21": "20-21",
    "INS23": "22-23",
    "INS24": "23-24",
    "INS25": "24-25",
    "INS26": "25-26",
}


def load_salt():
    """Load the salt for hashing student IDs from .salt file."""
    if not os.path.exists(SALT_PATH):
        print(f"ERROR: Salt file not found at {SALT_PATH}")
        print("Create a .salt file in the project root containing your secret phrase.")
        print("This file is git-ignored and stays on your machine only.")
        sys.exit(1)
    with open(SALT_PATH, "r") as f:
        salt = f.read().strip()
    if not salt:
        print("ERROR: .salt file is empty. Add a secret phrase.")
        sys.exit(1)
    return salt


def hash_id(student_id, salt):
    """Hash a student ID with the salt. Returns an 8-character hex string.
    8 hex chars = 4 billion possible values, more than enough for ~1700 students."""
    return hashlib.sha256((salt + student_id).encode()).hexdigest()[:8]


def find_csv(data_dir):
    """Find the most recently modified CSV in the data directory."""
    csvs = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csvs:
        print(f"ERROR: No CSV files found in {data_dir}/")
        print("Place your PERC Hold Tags export CSV in the data/ folder and re-run.")
        sys.exit(1)
    # Use most recently modified
    csvs.sort(key=os.path.getmtime, reverse=True)
    chosen = csvs[0]
    print(f"Using: {os.path.basename(chosen)}")
    return chosen


def parse_csv(filepath, salt):
    """Parse the CSV and return cleaned hold records with hashed student IDs."""
    records = []
    skipped = {"class_filter": 0, "restriction_filter": 0, "parse_error": 0}

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Validate expected columns exist
        expected = {"Str Student", "Restriction", "Start Date", "End Date", "Class"}
        if not expected.issubset(set(reader.fieldnames or [])):
            missing = expected - set(reader.fieldnames or [])
            print(f"ERROR: CSV missing expected columns: {missing}")
            print(f"Found columns: {reader.fieldnames}")
            sys.exit(1)

        for row in reader:
            student_id = row["Str Student"].strip().strip('"')
            restriction = row["Restriction"].strip().strip('"')
            class_standing = row["Class"].strip().strip('"')
            start_date = row["Start Date"].strip().strip('"')
            end_date = row["End Date"].strip().strip('"')

            # ── Filters (modify these for wildcard support) ──
            if not restriction.startswith(RESTRICTION_PREFIX):
                skipped["restriction_filter"] += 1
                continue

            # Handle comma-separated class values (e.g., "ALUM, ALGR")
            class_parts = {p.strip() for p in class_standing.split(",")}
            if class_parts & EXCLUDED_CLASSES:
                skipped["class_filter"] += 1
                continue

            # Validate dates
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                if end_date:
                    datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError as e:
                skipped["parse_error"] += 1
                continue

            records.append({
                "r": restriction,       # restriction code
                "s": start_date,        # start date (hold placed)
                "e": end_date or "",    # end date (hold lifted), empty = still active
                "c": class_standing,    # class standing: FY, SO, JR, SR, ALUM
                "i": hash_id(student_id, salt),  # salted hash of student ID
            })

    return records, skipped


def summarize(records):
    """Print a summary of the processed data."""
    from collections import Counter

    by_code = Counter(r["r"] for r in records)
    by_class = Counter(r["c"] for r in records)
    active = sum(1 for r in records if not r["e"])

    print(f"\n{'='*50}")
    print(f"  Processed: {len(records)} hold records")
    print(f"  Active (no end date): {active}")
    print(f"{'='*50}")

    print("\n  By restriction code:")
    for code in sorted(by_code.keys()):
        label = YEAR_LABELS.get(code, "?")
        active_ct = sum(1 for r in records if r["r"] == code and not r["e"])
        print(f"    {code} ({label}): {by_code[code]} total, {active_ct} active")

    print("\n  By class standing:")
    for cls in sorted(by_class.keys()):
        print(f"    {cls}: {by_class[cls]}")

    # Detect start dates per restriction
    print("\n  Placement dates:")
    codes = set(r["r"] for r in records)
    for code in sorted(codes):
        starts = set(r["s"] for r in records if r["r"] == code)
        for s in sorted(starts):
            ct = sum(1 for r in records if r["r"] == code and r["s"] == s)
            print(f"    {code}: {s} ({ct} holds)")

    # Recurrence analysis: how many holds per student?
    from collections import defaultdict
    student_codes = defaultdict(set)
    for r in records:
        student_codes[r["i"]].add(r["r"])
    hold_counts = Counter(len(v) for v in student_codes.values())
    print(f"\n  Hold recurrence ({len(student_codes)} unique students):")
    for n in sorted(hold_counts.keys()):
        label = "hold" if n == 1 else "holds"
        print(f"    {n} {label}: {hold_counts[n]} students ({hold_counts[n]/len(student_codes)*100:.1f}%)")


def build_output(records, source_file):
    """Build the output JSON structure."""
    return {
        "holds": records,
        "meta": {
            "generated": datetime.now().isoformat(),
            "source": os.path.basename(source_file),
            "recordCount": len(records),
            "filters": {
                "restrictionPrefix": RESTRICTION_PREFIX,
                "excludedClasses": sorted(EXCLUDED_CLASSES),
            },
            "yearLabels": YEAR_LABELS,
        },
    }


def main():
    print("InSight Hold Melt - Data Pipeline")
    print("-" * 40)

    salt = load_salt()
    csv_path = find_csv(DATA_DIR)
    records, skipped = parse_csv(csv_path, salt)

    if skipped["restriction_filter"] or skipped["class_filter"] or skipped["parse_error"]:
        print(f"\n  Skipped rows:")
        if skipped["restriction_filter"]:
            print(f"    Non-{RESTRICTION_PREFIX} restrictions: {skipped['restriction_filter']}")
        if skipped["class_filter"]:
            print(f"    Excluded classes (SR/ALUM): {skipped['class_filter']}")
        if skipped["parse_error"]:
            print(f"    Parse errors: {skipped['parse_error']}")

    summarize(records)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Write JSON
    output = build_output(records, csv_path)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"\n  Output: {OUTPUT_PATH}")
    print(f"  Size: {size_kb:.1f} KB")
    print(f"\nDone. Vite will hot-reload the dashboard automatically.")


if __name__ == "__main__":
    main()