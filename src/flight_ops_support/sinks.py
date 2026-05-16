from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd


@dataclass(frozen=True)
class SpreadsheetArtifacts:
    csv_path: Path
    xlsx_path: Path


class SpreadsheetSink(Protocol):
    def write(self, dataframe: pd.DataFrame) -> SpreadsheetArtifacts:
        """Persist a normalized report into a spreadsheet-compatible destination."""


class LocalSpreadsheetFilesSink:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def write(self, dataframe: pd.DataFrame) -> SpreadsheetArtifacts:
        csv_path = self.output_dir / "flight_operations_report.csv"
        xlsx_path = self.output_dir / "flight_operations_report.xlsx"

        dataframe.to_csv(csv_path, index=False)
        dataframe.to_excel(xlsx_path, index=False)

        return SpreadsheetArtifacts(csv_path=csv_path, xlsx_path=xlsx_path)


def build_spreadsheet_sink(sink_mode: str, output_dir: Path) -> SpreadsheetSink:
    if sink_mode == "local_files":
        return LocalSpreadsheetFilesSink(output_dir)

    raise ValueError(
        "Unsupported spreadsheet sink mode. "
        "Use 'local_files' for the sanitized public demo."
    )
