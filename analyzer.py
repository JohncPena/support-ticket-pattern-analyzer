#!/usr/bin/env python3
"""
Support Ticket Pattern Analyzer
Parses enterprise support case logs (CSV/JSON) to identify recurring root causes,
repeat-incident rates, keyword signatures, and candidates for SOP runbooks.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

KEYWORD_RULES = {
    "VLAN / Trunking Conflict": re.compile(r"\b(vlan|trunk|tagged|untagged|native vlan)\b", re.IGNORECASE),
    "DHCP / IP Lease Failure": re.compile(r"\b(dhcp|lease|ip allocation|exhaustion)\b", re.IGNORECASE),
    "Authentication / Token Error": re.compile(r"\b(token|auth(entication)?|unauthorized|api key|credential)\b", re.IGNORECASE),
    "Firmware / Hash Mismatch": re.compile(r"\b(firmware|hash|ota|checksum|corrupt image)\b", re.IGNORECASE),
    "Serial / Hardware Drop": re.compile(r"\b(rs-?232|serial|unresponsive|baud|uart)\b", re.IGNORECASE),
}


def load_tickets(filepath: str) -> list[dict]:
    """Load and validate ticket records from a CSV or JSON file."""
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Target file not found: {filepath}")

    if path.stat().st_size == 0:
        raise ValueError(f"Target file is empty: {filepath}")

    ext = path.suffix.lower()
    if ext not in {".csv", ".json"}:
        raise ValueError(f"Unsupported file format '{ext}'. Expected .csv or .json")

    try:
        if ext == ".csv":
            with open(path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                required_cols = {"ticket_id", "category", "error_message"}
                actual_cols = set(reader.fieldnames or [])

                if not required_cols.issubset(actual_cols):
                    missing = sorted(list(required_cols - actual_cols))
                    raise ValueError(f"Missing required CSV column headers: {missing}")

                records = [row for row in reader if any(row.values())]
        else:
            with open(path, mode="r", encoding="utf-8") as f:
                records = json.load(f)
                if not isinstance(records, list):
                    raise ValueError("JSON root element must be a list of ticket objects")

    except UnicodeDecodeError:
        raise ValueError(f"File encoding error. Please ensure {filepath} is UTF-8 encoded.")
    except json.JSONDecodeError as err:
        raise ValueError(f"Malformed JSON syntax: {err}")

    if not records:
        raise ValueError(f"No records found in {filepath}")

    return records


def extract_keywords(text: str) -> list[str]:
    """Match free-text fields against keyword signatures."""
    matched_tags = []
    for tag_name, pattern in KEYWORD_RULES.items():
        if pattern.search(text):
            matched_tags.append(tag_name)
    return matched_tags or ["Unclassified Signature"]


def analyze_tickets(tickets: list[dict], threshold_pct: float = 20.0) -> dict:
    """Analyze ticket metrics, root causes, repeat patterns, and keyword tags."""
    total_tickets = len(tickets)
    categories = Counter()
    errors = Counter()
    device_types = Counter()
    keyword_signatures = Counter()
    repeat_count = 0
    total_resolution_time = 0.0
    resolution_time_tracked_count = 0

    for ticket in tickets:
        cat = str(ticket.get("category", "")).strip() or "Uncategorized"
        err = str(ticket.get("error_message", "")).strip() or "Unknown Error"
        dev = str(ticket.get("device_type", "")).strip() or "Unknown Device"

        categories[cat] += 1
        errors[err] += 1
        device_types[dev] += 1

        tags = extract_keywords(err)
        for tag in tags:
            keyword_signatures[tag] += 1

        repeat_val = str(ticket.get("repeat_incident", "")).strip().lower()
        if repeat_val in {"true", "1", "yes"}:
            repeat_count += 1

        time_str = ticket.get("resolution_time_hrs")
        if time_str is not None and str(time_str).strip():
            try:
                total_resolution_time += float(time_str)
                resolution_time_tracked_count += 1
            except ValueError:
                pass

    repeat_rate = (repeat_count / total_tickets) * 100.0 if total_tickets else 0.0
    avg_resolution_time = (
        (total_resolution_time / resolution_time_tracked_count)
        if resolution_time_tracked_count > 0
        else None
    )

    return {
        "total_tickets": total_tickets,
        "repeat_incident_count": repeat_count,
        "repeat_incident_rate": round(repeat_rate, 2),
        "avg_resolution_time_hrs": round(avg_resolution_time, 2) if avg_resolution_time else None,
        "top_categories": categories.most_common(3),
        "top_errors": errors.most_common(3),
        "top_devices": device_types.most_common(3),
        "top_signatures": keyword_signatures.most_common(3),
        "threshold_pct": threshold_pct,
    }


def print_report(metrics: dict, target_file: str) -> None:
    """Print formatted terminal report."""
    print("=" * 65)
    print(f"       SUPPORT CASE PATTERN REPORT: {Path(target_file).name}")
    print("=" * 65)
    print(f"Total Cases Analyzed     : {metrics['total_tickets']}")
    print(f"Repeat Incidents Flagged : {metrics['repeat_incident_count']}")
    print(f"Overall Repeat Rate      : {metrics['repeat_incident_rate']:.1f}%")

    if metrics["avg_resolution_time_hrs"] is not None:
        print(f"Mean Resolution Time     : {metrics['avg_resolution_time_hrs']:.2f} hrs")

    print("\n--- Heuristic Signature Trends (Keyword Matching) ---")
    for rank, (sig, count) in enumerate(metrics["top_signatures"], 1):
        pct = (count / metrics["total_tickets"]) * 100
        print(f" {rank}. {sig:<30} -> {count} cases ({pct:.1f}%)")

    print("\n--- Top Root Cause Error Patterns ---")
    for rank, (err, count) in enumerate(metrics["top_errors"], 1):
        pct = (count / metrics["total_tickets"]) * 100
        print(f" {rank}. {err} -> {count} occurrences ({pct:.1f}%)")

    print("\n--- Failure Distribution by Category ---")
    for cat, count in metrics["top_categories"]:
        print(f" * {cat:<20} : {count} cases")

    print("\n--- Top Affected Hardware / Endpoints ---")
    for dev, count in metrics["top_devices"]:
        print(f" * {dev:<20} : {count} cases")

    print("\n--- Actionable Recommendations ---")
    if metrics["top_errors"]:
        top_err, top_count = metrics["top_errors"][0]
        top_pct = (top_count / metrics["total_tickets"]) * 100
        if top_pct >= metrics["threshold_pct"]:
            print(f" [!] '{top_err}' accounts for {top_pct:.1f}% of volume.")
            print("     Action: Publish dedicated Standard Operating Procedure (SOP) runbook.")
        else:
            print(" [i] Issue spread is balanced across categories. Continue baseline monitoring.")
    print("=" * 65)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze support ticket exports (CSV/JSON) for recurring defects and SOP candidates."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="sample_data/tickets.csv",
        help="Path to CSV or JSON ticket export file (default: sample_data/tickets.csv)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=20.0,
        help="Volume threshold percentage to trigger an SOP recommendation (default: 20.0)",
    )
    parser.add_argument(
        "--json-out",
        action="store_true",
        help="Output metrics as formatted JSON instead of terminal report",
    )

    args = parser.parse_args()

    try:
        ticket_data = load_tickets(args.file)
        results = analyze_tickets(ticket_data, threshold_pct=args.threshold)

        if args.json_out:
            print(json.dumps(results, indent=2))
        else:
            print_report(results, args.file)

        sys.exit(0)

    except (FileNotFoundError, ValueError) as err:
        print(f"Validation Error: {err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"Unexpected Execution Failure ({type(err).__name__}): {err}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
