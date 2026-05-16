from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.flight_ops_support.config import AppConfig
from src.flight_ops_support.pipeline import build_record, group_input_files
from src.flight_ops_support.sinks import build_spreadsheet_sink


def make_config(temp_root: Path, threshold: int = 500) -> AppConfig:
    return AppConfig(
        input_dir=temp_root / "incoming",
        fixtures_dir=temp_root / "fixtures",
        processed_dir=temp_root / "processed",
        output_dir=temp_root / "output",
        log_file=temp_root / "logs" / "etl.log",
        spreadsheet_sink_mode="local_files",
        arrival_fuel_alert_threshold_kg=threshold,
    )


class GroupingTest(unittest.TestCase):
    def test_group_input_files_maps_document_suffixes_to_triplets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            incoming_dir = Path(temp_dir)
            expected_files = {
                "demo_flight_aur101_20260514_operational_flight_plan.xml": "ofp",
                "demo_flight_aur101_20260514_flight_report.xml": "flight",
                "demo_flight_aur101_20260514_voyage_report.xml": "voyage",
            }

            for file_name in expected_files:
                (incoming_dir / file_name).write_text("<root />", encoding="utf-8")

            grouped = group_input_files(incoming_dir)

            self.assertIn("demo_flight_aur101_20260514", grouped)
            self.assertEqual(set(grouped["demo_flight_aur101_20260514"]), {"ofp", "flight", "voyage"})


class RecordBuilderTest(unittest.TestCase):
    def test_build_record_marks_warning_when_arrival_fuel_variance_exceeds_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = make_config(Path(temp_dir), threshold=500)
            files = {
                "ofp": Path("demo_flight_aur205_20260514_operational_flight_plan.xml"),
                "flight": Path("demo_flight_aur205_20260514_flight_report.xml"),
                "voyage": Path("demo_flight_aur205_20260514_voyage_report.xml"),
            }
            ofp = {
                "batch_id": "BATCH-1",
                "flight_id": "FLT-1",
                "flight_number": "AUR205",
                "origin_date": "2026-05-14",
                "origin_airport": "WIII",
                "destination_airport": "WARR",
                "planned_arrival_fuel_kg": 2100,
                "alternate_airport": "WADD",
                "aircraft_registration": "REG-BX7",
                "aircraft_type": "B738",
                "scheduled_departure_utc": "2026-05-14T05:40:00Z",
                "planned_flight_level": 330,
                "planned_distance_nm": 1060,
                "planned_block_fuel_kg": 9700,
                "planned_trip_fuel_kg": 6400,
                "dispatcher_code": "DSP-02",
            }
            flight = {
                "batch_id": "BATCH-1",
                "flight_id": "FLT-1",
                "flight_number": "AUR205",
                "origin_date": "2026-05-14",
                "origin_airport": "WIII",
                "destination_airport": "WARR",
                "highest_flight_level": 340,
                "peak_fuel_on_board_kg": 9750,
                "extra_fuel_reason": "ATC reroute reserve",
            }
            voyage = {
                "batch_id": "BATCH-1",
                "flight_id": "FLT-1",
                "flight_number": "AUR205",
                "origin_date": "2026-05-14",
                "origin_airport": "WIII",
                "destination_airport": "WARR",
                "actual_out_utc": "2026-05-14T05:48:00Z",
                "actual_off_utc": "2026-05-14T06:02:00Z",
                "actual_on_utc": "2026-05-14T07:57:00Z",
                "actual_in_utc": "2026-05-14T08:03:00Z",
                "actual_departure_fuel_kg": 9680,
                "actual_arrival_fuel_kg": 1400,
                "fuel_uplift_kg": 1150,
                "takeoff_pilot_code": "PILOT-27",
                "landing_type": "Autoland",
                "flight_type": "Scheduled",
            }

            record, issues, status = build_record(config, files, ofp, flight, voyage)

            self.assertIsNotNone(record)
            self.assertEqual(status, "warning")
            self.assertEqual(record["arrival_fuel_variance_kg"], -700)
            self.assertTrue(any("arrival fuel variance exceeds threshold" in issue for issue in issues))

    def test_build_record_fails_when_required_document_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = make_config(Path(temp_dir))
            files = {
                "ofp": Path("demo_flight_aur330_20260514_operational_flight_plan.xml"),
                "flight": Path("demo_flight_aur330_20260514_flight_report.xml"),
            }
            shared_fields = {
                "batch_id": "BATCH-3",
                "flight_id": "FLT-3",
                "flight_number": "AUR330",
                "origin_date": "2026-05-14",
                "origin_airport": "WAAA",
                "destination_airport": "WSSS",
            }

            record, issues, status = build_record(config, files, shared_fields, shared_fields, shared_fields)

            self.assertIsNone(record)
            self.assertEqual(status, "failed")
            self.assertTrue(any("missing required XML documents" in issue for issue in issues))


class SpreadsheetSinkTest(unittest.TestCase):
    def test_build_spreadsheet_sink_rejects_unknown_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                build_spreadsheet_sink("google_sheets_api", Path(temp_dir))


if __name__ == "__main__":
    unittest.main()
