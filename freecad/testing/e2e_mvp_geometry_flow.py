"""E2E smoke test: geometry extraction -> nesting -> report."""

import FreeCAD as App  # type: ignore

from SquatchCut.core.shape_extractor import ShapeExtractor  # type: ignore
from SquatchCut.core.multi_sheet_optimizer import MultiSheetOptimizer  # type: ignore
from SquatchCut.core.report_generator import ReportGenerator  # type: ignore
from .helpers.generate_test_documents import create_basic_rectangles_doc


def run_e2e_on_generated_doc():
    """
    Generate a test document, extract shapes as panels, run nesting, and verify the result.
    """
    doc = create_basic_rectangles_doc()
    extractor = ShapeExtractor()
    panels = extractor.extract_from_document(doc)
    assert panels, "No panels extracted from generated document."

    optimizer = MultiSheetOptimizer()
    sheets = optimizer.optimize(panels, {"width": 2440.0, "height": 1220.0})
    assert sheets, "No sheets produced by optimizer."

    report = ReportGenerator()
    report_data = report.build_report_data(sheets)
    assert report_data["summary"]["total_panels"] == len(panels)
    return report_data


def main():
    print("Running SquatchCut geometry E2E smoke test...")
    data = run_e2e_on_generated_doc()
    print("Geometry E2E test passed. Sheets:", data["summary"]["total_sheets"])


if __name__ == "__main__":
    main()
