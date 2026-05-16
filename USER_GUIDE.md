# User Guide

## Purpose

This guide exists to provide a more detailed walkthrough than the main `README.md`.

Use `README.md` for the quick portfolio overview.
Use `USER_GUIDE.md` when someone wants the operational flow, file model, runtime behavior, and extension points in more detail.

If you prefer a leaner public repository, you can keep only `README.md` and remove this file. It is optional, not required by the code.

## Overview

`Flight XML to Spreadsheet Automation` simulates an ETL workflow with the following shape:

1. collect XML files from an inbox
2. group files by the same flight key
3. parse three distinct document types
4. validate shared identity fields across documents
5. merge the extracted values into one report record
6. write the normalized output to a spreadsheet-friendly sink
7. archive successfully processed files

This represents a realistic engineering pattern where one flight is distributed across three XML files and must be mapped into a single spreadsheet row.

## Public Demo vs Original Workflow

This repository is intentionally smaller than the original implementation.

In a real operational environment, the three XML files may feed a much larger mapping layer before the result is inserted into a spreadsheet-oriented reporting destination. That complete structure is not published because the source XML may contain sensitive flight-operational information and confidential business context.

This public demo keeps the important engineering pattern intact:

```text
3 XML files with the same flight/group key
  -> extract fields from each document
  -> validate identity consistency
  -> map into one normalized spreadsheet row
  -> hand off to a spreadsheet sink
```

For safety, the public repository replaces the live spreadsheet integration with local `CSV` and `XLSX` outputs.

## XML Triplet Model

Each output row is derived from three sources:

- `Operational Flight Plan`
  Contains planned route, aircraft, dispatch, and planned fuel data.
- `Flight Report`
  Contains en-route summary data and additional fuel notes.
- `Voyage Report`
  Contains actual timestamps, actual fuel values, and operation markers.

The purpose of this design is to demonstrate a realistic ETL pattern where operational information is distributed across multiple documents and must be reconciled before reporting.

## Spreadsheet Sink Abstraction

The codebase keeps a spreadsheet sink abstraction so the integration boundary remains explicit.

Current public mode:

- `local_files`
  Writes normalized output to local `CSV` and `XLSX` files.

This makes it clear where a private spreadsheet API integration would sit without exposing confidential integration details in the public repository.

## File Naming Convention

The demo naming format is:

```text
<group_key>_operational_flight_plan.xml
<group_key>_flight_report.xml
<group_key>_voyage_report.xml
```

Example:

```text
demo_flight_aur101_20260514_operational_flight_plan.xml
demo_flight_aur101_20260514_flight_report.xml
demo_flight_aur101_20260514_voyage_report.xml
```

All files with the same `group_key` are merged into one output row.

## Output Columns

The normalized output currently includes:

- batch and flight identity
- origin, destination, and alternate airports
- aircraft registration and type
- scheduled and actual timestamps
- planned and actual fuel metrics
- en-route summary values
- flight type, landing type, and dispatcher code
- validation status and notes
- source file references

The public version exposes only a reduced subset of the original field model, while preserving the same reconciliation pattern.

## Running The Demo

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a local environment file:

```bash
copy .env.example .env
```

3. Run the demo pipeline:

```bash
python main.py --demo-run
```

4. Run the tests:

```bash
python -m unittest discover -s tests -p "test*.py" -v
```

## Runtime Behavior

During execution:

- dummy XML fixtures are copied into `sample_data/incoming`
- the pipeline scans for `*.xml`
- files are grouped by the prefix before the document suffix
- incomplete groups are skipped
- identity inconsistencies become warnings
- successfully processed files are moved to `sample_data/processed/<timestamp>/`
- the run summary is written to JSON for auditability

## Validation Semantics

`validation_status` uses three outcomes:

- `passed`
  All identity fields are consistent and no alerts are present.
- `warning`
  A row is still produced, but issues exist, such as fuel variance above threshold or identity mismatches across documents.
- `failed`
  A row is not produced because required documents are missing or an unexpected processing error occurs.

## Portfolio Review Checklist

When someone reviews this repository, the important points should be immediately visible:

- the problem statement is clear: three XML documents must be reconciled into one row
- the data is safe: names, codes, and files are dummy and sanitized
- the engineering hygiene is visible: tests, CI, logs, and structured project layout
- the output is easy to verify through report files and run summaries

## Public Portfolio Safety

This repository is safe to publish because:

- the XML schema is intentionally reconstructed and does not replicate the original production documents
- all aircraft, dispatcher, and pilot identifiers are dummy values
- no spreadsheet ID, service account, domain, endpoint, or API key is included
- output is written only to local files

## Extension Ideas

Reasonable next steps for a private or expanded implementation:

- add more parser and validator unit tests
- implement a real spreadsheet API sink behind the existing abstraction
- add a scheduled ingestion layer
- add a BI or dashboard handoff layer
- add business-rule validation by airport or fleet type
- add a DuckDB or Parquet sink for larger-scale batch analysis
