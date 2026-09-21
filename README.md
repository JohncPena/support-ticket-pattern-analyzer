# Support Ticket Pattern Analyzer

A Python CLI utility that ingests CRM and service desk incident logs (CSV/JSON), extracts recurring failure signatures, calculates repeat-incident rates, and flags chronic issues for Standard Operating Procedure (SOP) runbook creation.

Built to mirror post-implementation operational reviews: identify configuration defects that cause ticket churn, isolate hardware and network trends, and turn repetitive support volume into structured documentation.

---

## Key Features

- **Multi-Format Ingestion:** Ingests structured CSV and JSON ticket exports with defensive schema and header validation.
- **Heuristic Pattern Matching:** Applies compiled regex rules across unformatted case notes to extract signatures (VLAN conflicts, DHCP lease drops, token expiration, firmware hash mismatches, serial bus drops).
- **Operational Metrics:** Calculates repeat-ticket percentages, mean time to resolution (MTTR), and failure concentration per endpoint.
- **Configurable Thresholds:** Evaluates error volumes against a customizable threshold flag (`--threshold`) to trigger automated SOP runbook recommendations.
- **JSON Pipeline Output:** Supports raw JSON output (`--json-out`) for piping directly into external dashboards, reporting tools, or log forwarders.
- **Zero External Dependencies:** Built entirely with Python standard library modules (`argparse`, `csv`, `json`, `re`, `pathlib`, `collections`).

---

## Requirements

- Python 3.9+
- Standard Library only (no external dependencies required)

---

## Usage

### 1. Analyze Standard Incident Export
Run the analyzer against a standard CSV ticket dump:

    python3 analyzer.py sample_data/tickets.csv

Expected output:

    =================================================================
           SUPPORT CASE PATTERN REPORT: tickets.csv
    =================================================================
    Total Cases Analyzed     : 10
    Repeat Incidents Flagged : 4
    Overall Repeat Rate      : 40.0%
    Mean Resolution Time     : 2.00 hrs

    --- Heuristic Signature Trends (Keyword Matching) ---
     1. VLAN / Trunking Conflict       -> 3 cases (30.0%)
     2. DHCP / IP Lease Failure        -> 2 cases (20.0%)
     3. Authentication / Token Error   -> 2 cases (20.0%)

    --- Top Root Cause Error Patterns ---
     1. VLAN tag mismatch on trunk port -> 3 occurrences (30.0%)
     2. DHCP lease allocation failure -> 2 occurrences (20.0%)
     3. Invalid API authorization token -> 2 occurrences (20.0%)

    --- Failure Distribution by Category ---
     * Network              : 5 cases
     * Authentication       : 2 cases
     * Hardware             : 1 cases

    --- Top Affected Hardware / Endpoints ---
     * Smart Switch         : 3 cases
     * Host Controller      : 2 cases
     * Cloud Gateway        : 2 cases

    --- Actionable Recommendations ---
     [!] 'VLAN tag mismatch on trunk port' accounts for 30.0% of volume.
         Action: Publish dedicated Standard Operating Procedure (SOP) runbook.
    =================================================================

### 2. Malformed or Corrupt Data Handling
Audit a file with missing required schema headers:

    python3 analyzer.py sample_data/bad_tickets.csv

Expected output:

    Validation Error: Missing required CSV column headers: ['category', 'error_message']

### 3. Custom Alert Thresholds
Trigger runbook alerts only when an issue exceeds a specific percentage of queue volume:

    python3 analyzer.py sample_data/tickets.csv --threshold 35.0

### 4. JSON Pipeline Output
Export calculated metrics directly to standard output for automation pipelines:

    python3 analyzer.py sample_data/tickets.csv --json-out

---

## Exit Codes

- `0`: Success (analysis completed cleanly).
- `1`: Validation Failure (missing file, empty record set, or invalid schema headers).
- `2`: System Error (unhandled exception or file permission failure).
