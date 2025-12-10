"""FreeCAD command to export nesting reports after a run completes."""

from __future__ import annotations

import os

from SquatchCut.core import session_state
from SquatchCut.core.report_generator import ReportGenerator
from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.dialogs.dlg_export_report import SC_ExportReportDialog
from SquatchCut.gui.icons import get_icon
from SquatchCut.gui.qt_compat import QtWidgets

# @codex
# Command: Export PDF/CSV nesting reports.
# Interactions: Should use SC_ExportReportDialog and call core report_generator outputs.
# Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).


class SC_ExportReportCommand:
    """Export PDF/CSV reports after nesting."""

    COMMAND_NAME = "SC_ExportReport"

    def GetResources(self):  # noqa: N802  (FreeCAD API)
        return {
            "MenuText": "Export Report",
            "ToolTip": "Export nesting results to PDF and CSV.",
            "Pixmap": get_icon("export_report"),
        }

    def Activated(self):  # noqa: N802  (FreeCAD API)
        if App is None or Gui is None:
            try:
                from SquatchCut.core import logger

                logger.warning("SC_ExportReportCommand.Activated() called outside FreeCAD GUI environment.")
            except Exception:
                pass
            return

        report_data = session_state.get_last_report_data()
        if not report_data:
            QtWidgets.QMessageBox.information(
                None, "SquatchCut", "No nesting results available. Run nesting first."
            )
            return

        dialog = SC_ExportReportDialog()
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return
        data = dialog.get_data()
        directory = data.get("directory") or ""
        if not directory:
            QtWidgets.QMessageBox.information(
                None, "SquatchCut", "Please select an export directory."
            )
            return

        pdf_path = os.path.join(directory, "squatchcut_nesting_report.pdf")
        csv_path = os.path.join(directory, "squatchcut_nesting_report.csv")

        generator = ReportGenerator()
        try:
            generator.generate_pdf(report_data, pdf_path)
            if data.get("generate_csv") or data.get("include_csv"):
                generator.generate_csv(report_data, csv_path)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                None, "SquatchCut", f"Export failed:\n{exc}"
            )
            return

        QtWidgets.QMessageBox.information(
            None, "SquatchCut", f"Report exported to:\n{pdf_path}"
        )

    def IsActive(self):  # noqa: N802  (FreeCAD API)
        return App is not None and Gui is not None and App.ActiveDocument is not None


COMMAND = SC_ExportReportCommand()
