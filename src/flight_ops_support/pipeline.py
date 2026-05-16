from __future__ import annotations

import argparse
import json
import logging
import shutil
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import REPORT_COLUMNS, AppConfig, load_config
from .sinks import build_spreadsheet_sink

LOGGER = logging.getLogger("flight_ops_support")
DOCUMENT_SUFFIXES = {
    "operational_flight_plan": "ofp",
    "flight_report": "flight",
    "voyage_report": "voyage",
}


def configure_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    if LOGGER.handlers:
        return

    LOGGER.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(stream_handler)


def ensure_directories(config: AppConfig) -> None:
    config.input_dir.mkdir(parents=True, exist_ok=True)
    config.fixtures_dir.mkdir(parents=True, exist_ok=True)
    config.processed_dir.mkdir(parents=True, exist_ok=True)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.log_file.parent.mkdir(parents=True, exist_ok=True)


def refresh_demo_data(config: AppConfig) -> int:
    ensure_directories(config)

    for xml_file in config.input_dir.glob("*.xml"):
        xml_file.unlink()

    copied = 0
    for fixture in sorted(config.fixtures_dir.glob("*.xml")):
        shutil.copy2(fixture, config.input_dir / fixture.name)
        copied += 1

    LOGGER.info("Loaded %s demo XML files into %s", copied, config.input_dir)
    return copied


def read_xml(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def text_or_empty(element: ET.Element, path: str) -> str:
    node = element.find(path)
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def attr_or_empty(element: ET.Element, path: str, attr: str) -> str:
    node = element.find(path)
    if node is None:
        return ""
    return (node.attrib.get(attr) or "").strip()


def parse_int(value: str) -> int | None:
    if value == "":
        return None
    return int(value)


def parse_float(value: str) -> float | None:
    if value == "":
        return None
    return float(value)


def parse_ofp(path: Path) -> dict[str, object]:
    root = read_xml(path)
    return {
        "batch_id": root.attrib.get("batchId", ""),
        "flight_id": attr_or_empty(root, "./Flight", "flightId"),
        "flight_number": attr_or_empty(root, "./Flight", "flightNumber"),
        "origin_date": attr_or_empty(root, "./Flight", "originDate"),
        "origin_airport": attr_or_empty(root, "./Flight/Route", "origin"),
        "destination_airport": attr_or_empty(root, "./Flight/Route", "destination"),
        "alternate_airport": attr_or_empty(root, "./Flight/Route", "alternate"),
        "scheduled_departure_utc": attr_or_empty(
            root, "./Flight", "scheduledDepartureUtc"
        ),
        "aircraft_registration": attr_or_empty(root, "./Aircraft", "registration"),
        "aircraft_type": attr_or_empty(root, "./Aircraft", "type"),
        "planned_flight_level": parse_int(text_or_empty(root, "./Dispatch/PlannedFlightLevel")),
        "planned_distance_nm": parse_int(text_or_empty(root, "./Dispatch/PlannedDistanceNm")),
        "planned_block_fuel_kg": parse_int(
            text_or_empty(root, "./Dispatch/PlannedBlockFuelKg")
        ),
        "planned_trip_fuel_kg": parse_int(
            text_or_empty(root, "./Dispatch/PlannedTripFuelKg")
        ),
        "planned_arrival_fuel_kg": parse_int(
            text_or_empty(root, "./Dispatch/PlannedArrivalFuelKg")
        ),
        "dispatcher_code": text_or_empty(root, "./Dispatch/DispatcherCode"),
    }


def parse_flight_report(path: Path) -> dict[str, object]:
    root = read_xml(path)
    return {
        "batch_id": root.attrib.get("batchId", ""),
        "flight_id": attr_or_empty(root, "./Flight", "flightId"),
        "flight_number": attr_or_empty(root, "./Flight", "flightNumber"),
        "origin_date": attr_or_empty(root, "./Flight", "originDate"),
        "origin_airport": attr_or_empty(root, "./Flight", "origin"),
        "destination_airport": attr_or_empty(root, "./Flight", "destination"),
        "highest_flight_level": parse_int(
            text_or_empty(root, "./WaypointSummary/HighestFlightLevel")
        ),
        "peak_fuel_on_board_kg": parse_int(
            text_or_empty(root, "./WaypointSummary/PeakFuelOnBoardKg")
        ),
        "extra_fuel_reason": text_or_empty(root, "./FuelNotes/ExtraFuelReason"),
    }


def parse_voyage_report(path: Path) -> dict[str, object]:
    root = read_xml(path)
    return {
        "batch_id": root.attrib.get("batchId", ""),
        "flight_id": attr_or_empty(root, "./Flight", "flightId"),
        "flight_number": attr_or_empty(root, "./Flight", "flightNumber"),
        "origin_date": attr_or_empty(root, "./Flight", "originDate"),
        "origin_airport": attr_or_empty(root, "./Flight", "origin"),
        "destination_airport": attr_or_empty(root, "./Flight", "destination"),
        "actual_out_utc": attr_or_empty(root, "./ActualTimes", "outUtc"),
        "actual_off_utc": attr_or_empty(root, "./ActualTimes", "offUtc"),
        "actual_on_utc": attr_or_empty(root, "./ActualTimes", "onUtc"),
        "actual_in_utc": attr_or_empty(root, "./ActualTimes", "inUtc"),
        "actual_departure_fuel_kg": parse_int(
            attr_or_empty(root, "./Fuel", "actualDepartureFuelKg")
        ),
        "actual_arrival_fuel_kg": parse_int(
            attr_or_empty(root, "./Fuel", "actualArrivalFuelKg")
        ),
        "fuel_uplift_kg": parse_int(attr_or_empty(root, "./Fuel", "upliftKg")),
        "fuel_density_kg_per_l": parse_float(
            attr_or_empty(root, "./Fuel", "densityKgPerL")
        ),
        "takeoff_pilot_code": attr_or_empty(root, "./Crew", "takeoffPilotCode"),
        "landing_type": attr_or_empty(root, "./Operation", "landingType"),
        "flight_type": attr_or_empty(root, "./Operation", "flightType"),
    }


def group_input_files(input_dir: Path) -> dict[str, dict[str, Path]]:
    groups: dict[str, dict[str, Path]] = defaultdict(dict)

    for path in sorted(input_dir.glob("*.xml")):
        for suffix, doc_type in DOCUMENT_SUFFIXES.items():
            marker = f"_{suffix}.xml"
            if path.name.endswith(marker):
                group_key = path.name[: -len(marker)]
                groups[group_key][doc_type] = path
                break

    return groups


def validate_identity(ofp: dict[str, object], flight: dict[str, object], voyage: dict[str, object]) -> list[str]:
    issues: list[str] = []
    identity_fields = [
        "batch_id",
        "flight_id",
        "flight_number",
        "origin_date",
        "origin_airport",
        "destination_airport",
    ]
    documents = {"ofp": ofp, "flight": flight, "voyage": voyage}

    for field in identity_fields:
        values = {name: str(payload.get(field, "")).strip() for name, payload in documents.items()}
        distinct_values = {value for value in values.values() if value}
        if len(distinct_values) > 1:
            issues.append(f"identity mismatch on {field}: {values}")

    return issues


def build_record(
    config: AppConfig,
    files: dict[str, Path],
    ofp: dict[str, object],
    flight: dict[str, object],
    voyage: dict[str, object],
) -> tuple[dict[str, object] | None, list[str], str]:
    missing = [doc_type for doc_type in ("ofp", "flight", "voyage") if doc_type not in files]
    if missing:
        return None, [f"missing required XML documents: {', '.join(missing)}"], "failed"

    issues = validate_identity(ofp, flight, voyage)

    planned_arrival = ofp.get("planned_arrival_fuel_kg")
    actual_arrival = voyage.get("actual_arrival_fuel_kg")
    arrival_variance = None
    if isinstance(planned_arrival, int) and isinstance(actual_arrival, int):
        arrival_variance = actual_arrival - planned_arrival
        if abs(arrival_variance) > config.arrival_fuel_alert_threshold_kg:
            issues.append(
                "arrival fuel variance exceeds threshold "
                f"({arrival_variance} kg vs limit {config.arrival_fuel_alert_threshold_kg} kg)"
            )

    status = "warning" if issues else "passed"

    record = {
        "batch_id": ofp.get("batch_id", ""),
        "flight_id": ofp.get("flight_id", ""),
        "flight_number": ofp.get("flight_number", ""),
        "origin_date": ofp.get("origin_date", ""),
        "origin_airport": ofp.get("origin_airport", ""),
        "destination_airport": ofp.get("destination_airport", ""),
        "alternate_airport": ofp.get("alternate_airport", ""),
        "aircraft_registration": ofp.get("aircraft_registration", ""),
        "aircraft_type": ofp.get("aircraft_type", ""),
        "scheduled_departure_utc": ofp.get("scheduled_departure_utc", ""),
        "actual_out_utc": voyage.get("actual_out_utc", ""),
        "actual_off_utc": voyage.get("actual_off_utc", ""),
        "actual_on_utc": voyage.get("actual_on_utc", ""),
        "actual_in_utc": voyage.get("actual_in_utc", ""),
        "planned_flight_level": ofp.get("planned_flight_level"),
        "highest_flight_level": flight.get("highest_flight_level"),
        "planned_distance_nm": ofp.get("planned_distance_nm"),
        "planned_block_fuel_kg": ofp.get("planned_block_fuel_kg"),
        "planned_trip_fuel_kg": ofp.get("planned_trip_fuel_kg"),
        "planned_arrival_fuel_kg": ofp.get("planned_arrival_fuel_kg"),
        "actual_departure_fuel_kg": voyage.get("actual_departure_fuel_kg"),
        "actual_arrival_fuel_kg": voyage.get("actual_arrival_fuel_kg"),
        "peak_fuel_on_board_kg": flight.get("peak_fuel_on_board_kg"),
        "fuel_uplift_kg": voyage.get("fuel_uplift_kg"),
        "arrival_fuel_variance_kg": arrival_variance,
        "extra_fuel_reason": flight.get("extra_fuel_reason", ""),
        "takeoff_pilot_code": voyage.get("takeoff_pilot_code", ""),
        "landing_type": voyage.get("landing_type", ""),
        "flight_type": voyage.get("flight_type", ""),
        "dispatcher_code": ofp.get("dispatcher_code", ""),
        "validation_status": status,
        "validation_notes": " | ".join(issues) if issues else "ok",
        "source_files": ", ".join(path.name for path in sorted(files.values())),
    }

    return record, issues, status


def archive_files(config: AppConfig, files: dict[str, Path], run_stamp: str) -> None:
    destination = config.processed_dir / run_stamp
    destination.mkdir(parents=True, exist_ok=True)

    for path in files.values():
        shutil.move(str(path), destination / path.name)


def write_outputs(config: AppConfig, records: list[dict[str, object]]) -> tuple[Path, Path]:
    dataframe = pd.DataFrame(records, columns=REPORT_COLUMNS)
    sink = build_spreadsheet_sink(config.spreadsheet_sink_mode, config.output_dir)
    artifacts = sink.write(dataframe)
    return artifacts.csv_path, artifacts.xlsx_path


def write_summary(config: AppConfig, payload: dict[str, object]) -> Path:
    summary_path = config.output_dir / "last_run_summary.json"
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return summary_path


def process_groups(config: AppConfig) -> dict[str, object]:
    groups = group_input_files(config.input_dir)
    LOGGER.info("Discovered %s candidate flight groups", len(groups))

    records: list[dict[str, object]] = []
    skipped_groups: list[dict[str, object]] = []
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for group_key, files in sorted(groups.items()):
        LOGGER.info("Processing group %s", group_key)

        if any(doc not in files for doc in ("ofp", "flight", "voyage")):
            missing = [doc for doc in ("ofp", "flight", "voyage") if doc not in files]
            skipped_groups.append(
                {"group_key": group_key, "status": "failed", "notes": [f"missing documents: {', '.join(missing)}"]}
            )
            LOGGER.warning("Skipping %s because documents are missing: %s", group_key, missing)
            continue

        try:
            ofp = parse_ofp(files["ofp"])
            flight = parse_flight_report(files["flight"])
            voyage = parse_voyage_report(files["voyage"])
            record, issues, status = build_record(config, files, ofp, flight, voyage)
            if record is None:
                skipped_groups.append({"group_key": group_key, "status": status, "notes": issues})
                LOGGER.warning("Skipping %s: %s", group_key, issues)
                continue

            records.append(record)
            LOGGER.info("Built output row for %s with status %s", group_key, status)
            archive_files(config, files, run_stamp)
        except Exception as exc:
            skipped_groups.append(
                {
                    "group_key": group_key,
                    "status": "failed",
                    "notes": [f"unexpected processing error: {exc}"],
                }
            )
            LOGGER.exception("Unexpected processing error for %s", group_key)

    csv_path = None
    xlsx_path = None
    if records:
        csv_path, xlsx_path = write_outputs(config, records)
        LOGGER.info("Wrote %s records to %s and %s", len(records), csv_path, xlsx_path)

    summary = {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "input_directory": str(config.input_dir),
        "processed_directory": str(config.processed_dir),
        "record_count": len(records),
        "warning_count": sum(1 for row in records if row["validation_status"] == "warning"),
        "failed_group_count": len(skipped_groups),
        "records": records,
        "skipped_groups": skipped_groups,
        "output_files": {
            "csv": str(csv_path) if csv_path else "",
            "xlsx": str(xlsx_path) if xlsx_path else "",
        },
    }
    summary_path = write_summary(config, summary)
    LOGGER.info("Wrote run summary to %s", summary_path)
    summary["summary_path"] = str(summary_path)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch ETL for dummy flight operations XML triplets."
    )
    parser.add_argument(
        "--demo-run",
        action="store_true",
        help="Reload sanitized XML fixtures into the inbox before processing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()

    ensure_directories(config)
    configure_logging(config.log_file)

    if args.demo_run:
        refresh_demo_data(config)

    summary = process_groups(config)

    print(
        json.dumps(
            {
                "record_count": summary["record_count"],
                "warning_count": summary["warning_count"],
                "failed_group_count": summary["failed_group_count"],
                "csv": summary["output_files"]["csv"],
                "xlsx": summary["output_files"]["xlsx"],
            },
            indent=2,
        )
    )
    return 0
