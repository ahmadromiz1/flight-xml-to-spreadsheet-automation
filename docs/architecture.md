# Architecture Notes

## High-Level Pipeline

```text
XML Files
   ↓
Parser
   ↓
Validation Layer
   ↓
Merge Engine
   ↓
Spreadsheet Export
   ↓
Archive and Logs
```

## Component Responsibilities

- `sample_data/fixtures/`
  Provides sanitized dummy XML fixtures used for repeatable demo runs.
- `src/flight_ops_support/pipeline.py`
  Orchestrates grouping, parsing, validation, record building, output writing, and archiving.
- `src/flight_ops_support/config.py`
  Centralizes runtime paths and threshold configuration.
- `src/flight_ops_support/sinks.py`
  Defines the spreadsheet sink abstraction and the current public-demo local file sink.
- `tests/`
  Covers integration flow and domain-level record-building behavior.

## Data Flow

1. XML files are loaded from the incoming directory.
2. Files are grouped by shared flight or batch key.
3. Each document type is parsed into a partial payload.
4. Shared identity fields are validated across the three payloads.
5. A normalized output record is assembled.
6. The record is written to spreadsheet-friendly output files.
7. Successfully processed inputs are archived and summarized.

## Public Demo Boundary

In a private production environment, the export step could write to a spreadsheet API or reporting platform. In this public portfolio version, the sink is intentionally limited to local files so the architecture remains visible without exposing confidential operational integrations.
