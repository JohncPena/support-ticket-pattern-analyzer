# Support Ticket Pattern Analyzer

A structured Python command-line utility designed to ingest support incident exports (CSV/JSON), aggregate error patterns, track repeat incidents, and highlight candidate issues for standard operating procedure (SOP) documentation.

This tool models the data telemetry workflows used to analyze 500+ annual support cases, identifying root-cause trends and reducing repeat ticket volume by ~20%.

## Features
- **Format Agnostic**: Accepts both `.csv` and `.json` incident feeds.
- **Root-Cause Grouping**: Aggregates recurring error codes and failure points across multi-vendor equipment.
- **Repeat Incident Calculation**: Quantifies repeat-ticket percentages across daily and monthly queues.
- **Defensive Input Handling**: Rejects malformed headers, corrupt rows, and wrong file structures with clean exit codes.

## Requirements
- Python 3.9+ (Standard Library only)

## Usage

Run with default sample data:
```bash
python3 analyzer.py
