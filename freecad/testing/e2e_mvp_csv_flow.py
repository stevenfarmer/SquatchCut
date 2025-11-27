"""E2E smoke test for SquatchCut MVP: CSV -> nesting -> report."""

import os

import FreeCAD as App  # type: ignore

from SquatchCut.core.csv_loader import CsvLoader  # type: ignore
from SquatchCut.core.preferences import PreferencesManager  # type: ignore
from SquatchCut.core.nesting_engine import NestingEngine  # type: ignore
from SquatchCut.core.multi_sheet_optimizer import MultiSheetOptimizer  # type: ignore
from SquatchCut.core.report_generator import ReportGenerator  # type: ignore


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "csv")
SMALL_CSV = os.path.join(FIXTURE_DIR, "valid_panels_small.csv")
MULTI_SHEET_CSV = os.path.join(FIXTURE_DIR, "valid_panels_multi_sheet.csv")


def run_e2e_on_csv(csv_path: str, sheet_width: float = 2440.0, sheet_height: float = 1220.0) -> dict:
    """
    Load panels from CSV, run nesting end-to-end, and return the report data.
    Raise AssertionError if something critical fails.
    """
    loader = CsvLoader()
    panels = loader.load_csv(csv_path)
    assert panels, f"No panels loaded from {csv_path}"

    optimizer = MultiSheetOptimizer()
    sheets = optimizer.optimize(panels, {"width": sheet_width, "height": sheet_height})
    assert sheets, "No sheets produced by optimizer."

    report = ReportGenerator()
    report_data = report.build_report_data(sheets)
    summary = report_data.get("summary", {})
    assert "total_sheets" in summary and "total_panels" in summary, "Summary missing expected fields."
    return report_data


def main():
    print("Running SquatchCut CSV E2E smoke tests...")
    data_small = run_e2e_on_csv(SMALL_CSV)
    print("Small CSV test passed. Sheets:", data_small["summary"]["total_sheets"])

    data_multi = run_e2e_on_csv(MULTI_SHEET_CSV)
    print("Multi-sheet CSV test passed. Sheets:", data_multi["summary"]["total_sheets"])

    print("All CSV E2E smoke tests completed successfully.")


if __name__ == "__main__":
    main()
