#!/usr/bin/env python3
"""
Support Ticket Pattern Analyzer
Parses enterprise support case logs to identify recurring root causes,
repeat-incident rates, and candidates for SOP runbooks.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path


def load_tickets(filepath: str) -> list[dict]:
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
                    missing = required_cols - actual_cols
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


def analyze_tickets(tickets: list[dict]) -> dict:
    total_tickets = len(tickets)
    categories = Counter()
    errors = Counter()
    device_types = Counter()
    repeat_count = 0
    total_resolution_time = 0.0
    resolution_time_tracked_count = 0

    for ticket in tickets:
        cat = ticket.get("category", "Uncategorized").strip() or "Uncategorized"
        err = ticket.get("error_message", "Unknown Error").strip() or "Unknown Error"
        dev = ticket.get("device_type", "Unknown Device").strip() or "Unknown Device"

        categories[cat] += 1
        errors[err] += 1
        device_types[dev] += 1

        repeat_val = str(ticket.get("repeat_incident", "")).lower()
        if repeat_val in {"true", "1", "yes"}:
            repeat_count += 1

        time_str = ticket.get("resolution_time_hrs")
        if time_str is not None:
            try:
                total_resolution_time += float(time_str)
                resolution_time_tracked_count += 1
            except ValueError:
                pass

    repeat_rate = (repeat_count / total_tickets) * 100
    avg_resolution_time = (
        (total_resolution_time / resolution_time_tracked_count)
        if resolution_time_tracked_count > 0
        else None
    )

    return {
        "total_tickets": total_tickets,
        "repeat_incident_count": repeat_count,
        "repeat_incident_rate": repeat_rate,
        "avg_resolution_time_hrs": avg_resolution_time,
        "top_categories": categories.most_common(3),
        "top_errors": errors.most_common(3),
        "top_devices": device_types.most_common(3),
    }


def print_report(metrics: dict) -> None:
    print("=" * 60)
    print("       SUPPORT CASE PATTERN ANALYSIS REPORT")
    print("=" * 60)
    print(f"Total Cases Analyzed     : {metrics['total_tickets']}")
    print(f"Repeat Incidents Flagged : {metrics['repeat_incident_count']}")
    print(f"Overall Repeat Rate      : {metrics['repeat_incident_rate']:.1f}%")

    if metrics["avg_resolution_time_hrs"] is not None:
        print(f"Mean Resolution Time     : {metrics['avg_resolution_time_hrs']:.2f} hrs")

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
    top_err, top_count = metrics["top_errors"][0]
    top_pct = (top_count / metrics["total_tickets"]) * 100
    if top_pct >= 20.0:
        print(f" [!] '{top_err}' accounts for {top_pct:.1f}% of volume.")
        print("     Action: Publish dedicated Standard Operating Procedure (SOP) runbook.")
    else:
        print(" [i] Issue spread is balanced across categories. Continue baseline monitoring.")
    print("=" * 60)


def main() -> None:
    target_file = sys.argv[1] if len(sys.argv) > 1 else "sample_data/tickets.csv"

    try:
        ticket_data = load_tickets(target_file)
        results = analyze_tickets(ticket_data)
        print_report(results)
    except (FileNotFoundError, ValueError) as err:
        print(f"Validation Error: {err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"Unexpected Execution Failure ({type(err).__name__}): {err}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
