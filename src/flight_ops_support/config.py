from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    input_dir: Path
    fixtures_dir: Path
    processed_dir: Path
    output_dir: Path
    log_file: Path
    spreadsheet_sink_mode: str
    arrival_fuel_alert_threshold_kg: int


def load_config() -> AppConfig:
    return AppConfig(
        input_dir=Path(os.getenv("INPUT_DIR", "sample_data/incoming")),
        fixtures_dir=Path(os.getenv("FIXTURES_DIR", "sample_data/fixtures")),
        processed_dir=Path(os.getenv("PROCESSED_DIR", "sample_data/processed")),
        output_dir=Path(os.getenv("OUTPUT_DIR", "output")),
        log_file=Path(os.getenv("LOG_FILE", "logs/etl.log")),
        spreadsheet_sink_mode=os.getenv("SPREADSHEET_SINK_MODE", "local_files"),
        arrival_fuel_alert_threshold_kg=int(
            os.getenv("ARRIVAL_FUEL_ALERT_THRESHOLD_KG", "500")
        ),
    )


REPORT_COLUMNS = [
    "batch_id",
    "flight_id",
    "flight_number",
    "origin_date",
    "origin_airport",
    "destination_airport",
    "alternate_airport",
    "aircraft_registration",
    "aircraft_type",
    "scheduled_departure_utc",
    "actual_out_utc",
    "actual_off_utc",
    "actual_on_utc",
    "actual_in_utc",
    "planned_flight_level",
    "highest_flight_level",
    "planned_distance_nm",
    "planned_block_fuel_kg",
    "planned_trip_fuel_kg",
    "planned_arrival_fuel_kg",
    "actual_departure_fuel_kg",
    "actual_arrival_fuel_kg",
    "peak_fuel_on_board_kg",
    "fuel_uplift_kg",
    "arrival_fuel_variance_kg",
    "extra_fuel_reason",
    "takeoff_pilot_code",
    "landing_type",
    "flight_type",
    "dispatcher_code",
    "validation_status",
    "validation_notes",
    "source_files",
]
