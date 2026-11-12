"""Synthetic JSON -> CSV: stable ID dedup and spreadsheet formula safety.

Usage: python clean_csv.py < example_input.json > output.csv
Standard library only; no network or real customer data.
"""
import csv
import io
import json
import sys

FIELDS = ("id", "name", "note")

def safe_cell(value):
    text = str(value if value is not None else "").strip()
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text

def convert(rows):
    if not isinstance(rows, list):
        raise ValueError("Expected a JSON array")
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Expected JSON object rows")
        key = str(row.get("id", "")).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        writer.writerow({key: safe_cell(row.get(key, "")) for key in FIELDS})
    return buf.getvalue()

if __name__ == "__main__":
    sys.stdout.write(convert(json.load(sys.stdin)))
