"""@codex
Module: Report generation utilities for SquatchCut nesting results.
Boundaries: Do not generate geometry or perform nesting; only summarize sheets and write PDF/CSV outputs.
Primary methods: build_pdf, build_csv, _summarize, _write_pdf, _write_csv.
Note: Update incrementally; do not overwrite this module when adding logic.
"""

from __future__ import annotations


class ReportGenerator:
    """Builds PDF and CSV summaries for nesting results."""

    def build_pdf(self, sheets: list[dict], output_path: str):
        """Generate a PDF summary report."""
        data = self.build_report_data(sheets)
        self.generate_pdf(data, output_path)

    def build_csv(self, sheets: list[dict], output_path: str):
        """Generate a CSV summary report."""
        data = self.build_report_data(sheets)
        self.generate_csv(data, output_path)

    def _summarize(self, sheets: list[dict]) -> dict:
        """Produce a summary data structure (sheet count, efficiency, waste)."""
        return self.build_report_data(sheets).get("summary", {})

    def _write_pdf(self, summary: dict, sheets: list[dict], output_path: str):
        """Write the PDF document to disk."""
        data = {"summary": summary, "sheets": sheets}
        self.generate_pdf(data, output_path)

    def _write_csv(self, summary: dict, sheets: list[dict], output_path: str):
        """Write the CSV report to disk."""
        data = {"summary": summary, "sheets": sheets}
        self.generate_csv(data, output_path)

    # New MVP implementations
    def build_report_data(self, sheets: list[dict]) -> dict:
        """Aggregate sheet and placement data into a summary structure."""
        total_sheets = len(sheets)
        total_panels = 0
        total_area_used = 0.0
        total_sheet_area = 0.0

        for sheet in sheets:
            sw = float(sheet.get("width", 0))
            sh = float(sheet.get("height", 0))
            total_sheet_area += sw * sh
            placements = sheet.get("placements", [])
            total_panels += len(placements)
            for placement in placements:
                pw = float(placement.get("width", 0))
                ph = float(placement.get("height", 0))
                total_area_used += pw * ph

        efficiency_percent = (
            (total_area_used / total_sheet_area) * 100 if total_sheet_area else 0.0
        )
        waste_percent = max(0.0, 100.0 - efficiency_percent)

        return {
            "sheets": sheets,
            "summary": {
                "total_sheets": total_sheets,
                "total_panels": total_panels,
                "total_area_used": total_area_used,
                "total_sheet_area": total_sheet_area,
                "efficiency_percent": efficiency_percent,
                "waste_percent": waste_percent,
            },
        }

    def generate_pdf(self, data: dict, output_path: str):
        """Generate a PDF (or text fallback) report."""
        summary = data.get("summary", {})
        sheets = data.get("sheets", [])
        try:
            from reportlab.lib.pagesizes import A4  # type: ignore
            from reportlab.pdfgen import canvas  # type: ignore
        except Exception:
            # Fallback to plain text with .pdf extension
            with open(output_path, "w", encoding="utf-8") as fh:
                fh.write("SquatchCut Report (text fallback)\n")
                fh.write(f"Total sheets: {summary.get('total_sheets', 0)}\n")
                fh.write(f"Total panels: {summary.get('total_panels', 0)}\n")
                fh.write(
                    f"Efficiency: {summary.get('efficiency_percent', 0):.2f}%\n"
                )
                fh.write(f"Waste: {summary.get('waste_percent', 0):.2f}%\n\n")
                for sheet in sheets:
                    fh.write(f"Sheet {sheet.get('sheet_id')}\n")
                    for placement in sheet.get("placements", []):
                        fh.write(
                            f"  Panel {placement.get('panel_id')} at ({placement.get('x')}, {placement.get('y')}) rot {placement.get('rotation')}\n"
                        )
            return

        c = canvas.Canvas(output_path, pagesize=A4)
        text = c.beginText(40, A4[1] - 40)
        text.textLine("SquatchCut Nesting Report")
        text.textLine(f"Total sheets: {summary.get('total_sheets', 0)}")
        text.textLine(f"Total panels: {summary.get('total_panels', 0)}")
        text.textLine(
            f"Efficiency: {summary.get('efficiency_percent', 0):.2f}% | Waste: {summary.get('waste_percent', 0):.2f}%"
        )
        text.textLine("")
        for sheet in sheets:
            text.textLine(f"Sheet {sheet.get('sheet_id')}")
            for placement in sheet.get("placements", []):
                line = (
                    f"  Panel {placement.get('panel_id')} "
                    f"({placement.get('width', '')}x{placement.get('height', '')}) "
                    f"at ({placement.get('x')}, {placement.get('y')}), rot {placement.get('rotation')}"
                )
                text.textLine(line)
            text.textLine("")
        c.drawText(text)
        c.showPage()
        c.save()

    def generate_csv(self, data: dict, output_path: str):
        """Write placement data to CSV."""
        import csv

        sheets = data.get("sheets", [])
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                ["sheet_id", "panel_id", "x", "y", "rotation", "width", "height"]
            )
            for sheet in sheets:
                sid = sheet.get("sheet_id")
                for placement in sheet.get("placements", []):
                    writer.writerow(
                        [
                            sid,
                            placement.get("panel_id"),
                            placement.get("x"),
                            placement.get("y"),
                            placement.get("rotation"),
                            placement.get("width"),
                            placement.get("height"),
                        ]
                    )
