# Support Ticket Pattern Analyzer

A Python CLI utility that ingests CRM/support incident exports (CSV/JSON), groups recurring error signatures, and calculates repeat-incident rates after customer go-live.
Built to model the post-implementation review workflow used on 500+ annual cases: find which configuration and integration defects create ticket churn, then turn those patterns into runbooks.
Features

Accepts CSV and JSON incident exports
Groups recurring error codes and failure points
Calculates repeat-ticket rates across daily and monthly queues
Rejects malformed headers, corrupt rows, and bad file structures with clean exit codes

## Requirements
- Python 3.9+ (Standard Library only)

## Usage

Run with default sample data:
```bash
python3 analyzer.py
