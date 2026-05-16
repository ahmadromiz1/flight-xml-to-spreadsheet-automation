from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from src.flight_ops_support.config import AppConfig
from src.flight_ops_support.pipeline import ensure_directories, process_groups, refresh_demo_data


class PipelineIntegrationTest(unittest.TestCase):
    def test_demo_fixtures_produce_expected_summary(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        fixture_source = repo_root / "sample_data" / "fixtures"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            fixtures_dir = temp_root / "fixtures"
            incoming_dir = temp_root / "incoming"
            processed_dir = temp_root / "processed"
            output_dir = temp_root / "output"
            log_file = temp_root / "logs" / "etl.log"

            shutil.copytree(fixture_source, fixtures_dir)

            config = AppConfig(
                input_dir=incoming_dir,
                fixtures_dir=fixtures_dir,
                processed_dir=processed_dir,
                output_dir=output_dir,
                log_file=log_file,
                spreadsheet_sink_mode="local_files",
                arrival_fuel_alert_threshold_kg=500,
            )

            ensure_directories(config)
            refresh_demo_data(config)
            summary = process_groups(config)

            self.assertEqual(summary["record_count"], 2)
            self.assertEqual(summary["warning_count"], 1)
            self.assertEqual(summary["failed_group_count"], 1)
            self.assertTrue((output_dir / "flight_operations_report.csv").exists())
            self.assertTrue((output_dir / "flight_operations_report.xlsx").exists())


if __name__ == "__main__":
    unittest.main()
