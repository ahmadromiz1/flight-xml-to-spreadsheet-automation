# Flight XML to Spreadsheet Automation

This repository is a portfolio ETL project that demonstrates a backend automation workflow for processing three operational XML files per flight, validating cross-document consistency, and merging them into one spreadsheet-ready record.

The core engineering pattern is represented as follows:

- three XML files share the same flight or group key
- each XML file contributes a different portion of the operational data
- the three documents are reconciled into one normalized row
- the final mapped record is prepared for a spreadsheet sink

## Why This Public Version Is Simpler

This public repository is a simplified and sanitized portfolio version of a much larger real-world workflow.

In a real operational environment, multiple related XML files may be reconciled into a single spreadsheet row through a broader field-mapping layer. That full structure is not published here because real operational documents may contain sensitive flight-operational data and confidential business context.

This demo keeps the engineering pattern intact while reducing the data surface for safe publication on GitHub:

- no real company names
- no original vendor XML schema
- no credentials, endpoints, or spreadsheet IDs
- no sensitive flight-operational data
- dummy but realistic sample files
- local `CSV` and `XLSX` output instead of a live spreadsheet API connection

## What This Demo Shows

- Python batch automation
- XML parsing and field extraction
- ETL merge across `Operational Flight Plan`, `Flight Report`, and `Voyage Report`
- Cross-document identity validation
- Spreadsheet-ready output mapping
- Logging, archiving, and JSON run summary generation
- Automated test coverage through GitHub Actions

## Business Flow

```text
incoming XML inbox
  -> group files by shared flight key
  -> parse 3 document types
  -> validate cross-document identity
  -> merge into one normalized row
  -> write spreadsheet-friendly output
  -> archive processed files
```

The production-like business flow is still represented as `3 XML documents -> 1 spreadsheet row`. In a private production environment, the final sink could point to a spreadsheet API. In this public portfolio version, that sink is intentionally sanitized to local files.

The codebase also keeps a dedicated spreadsheet sink abstraction so the handoff point to a spreadsheet integration layer remains explicit, even though the public demo uses `local_files`.

## Data Model

Each flight group requires three files:

1. `*_operational_flight_plan.xml`
2. `*_flight_report.xml`
3. `*_voyage_report.xml`

All three files are merged into one output record. If one required document is missing, the group is skipped and reported in the summary output.

## Repository Layout

```text
.
|-- .github/workflows/ci.yml
|-- main.py
|-- src/flight_ops_support/
|-- sample_data/
|   |-- fixtures/
|   |-- incoming/
|   `-- processed/
|-- docs/examples/
|-- tests/
|-- README.md
`-- USER_GUIDE.md
```

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py --demo-run
```

The `--demo-run` command will:

- load dummy fixtures into `sample_data/incoming`
- process the XML batch
- archive successful inputs into `sample_data/processed/<run_timestamp>/`
- write output files to:
  - `output/flight_operations_report.csv`
  - `output/flight_operations_report.xlsx`
  - `output/last_run_summary.json`

## Run Tests

```bash
python -m unittest discover -s tests -p "test*.py" -v
```

The GitHub Actions workflow runs the same command on every `push` and `pull request`.

## Validation Rules

- all three required documents must exist for each group
- `batch_id`, `flight_id`, `flight_number`, `origin_date`, `origin_airport`, and `destination_airport` must remain consistent across the XML set
- arrival fuel variance above the configured threshold is flagged as a `warning`

## Example Outcome

The demo fixtures intentionally include:

- valid flights
- one flight with a fuel variance warning
- one incomplete document group to demonstrate skip handling

An example output report is available in [`docs/examples/flight_operations_report_example.csv`](docs/examples/flight_operations_report_example.csv).

Example terminal summary:

```json
{
  "record_count": 2,
  "warning_count": 1,
  "failed_group_count": 1,
  "csv": "output\\flight_operations_report.csv",
  "xlsx": "output\\flight_operations_report.xlsx"
}
```

## Why This Is Safe To Publish

- the XML schema is intentionally rebuilt and does not match the original production structure
- all operational entities use dummy identifiers
- no secrets, service accounts, or active endpoints are included
- the sample output is realistic enough to demonstrate ETL logic without exposing sensitive operational data

More detailed documentation is available in [`USER_GUIDE.md`](USER_GUIDE.md).
