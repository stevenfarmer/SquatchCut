"""FreeCAD command to export a simple CSV cutlist from the current nesting."""

from SquatchCut.core import logger
from SquatchCut.core.cutlist import export_cutops_to_csv, generate_cutops_from_session
from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.qt_compat import QtWidgets


class ExportCutlistCommand:
    """
    Export a simple CSV cutlist derived from the current nested layout.
    """

    def GetResources(self):
        return {
            "MenuText": "Export Cutlist",
            "ToolTip": "Generate a CSV cutlist from the current SquatchCut nesting.",
            "Pixmap": "",
        }

    def IsActive(self):
        return Gui is not None and App is not None and App.ActiveDocument is not None

    def Activated(self):
        if App is None or Gui is None:
            return
        try:
            from SquatchCut.ui.progress import SimpleProgressContext

            doc = App.ActiveDocument
            if doc is None:
                logger.warning("ExportCutlistCommand: no active document.")
                return

            with SimpleProgressContext("Generating cutlist...", "SquatchCut Export"):
                cut_ops = generate_cutops_from_session()
                if not cut_ops:
                    QtWidgets.QMessageBox.information(
                        Gui.getMainWindow(),
                        "SquatchCut Cutlist",
                        "No cuts to export. Make sure nesting has been run.",
                    )
                    return

            dlg = QtWidgets.QFileDialog(Gui.getMainWindow())
            dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dlg.setNameFilter("CSV files (*.csv)")
            dlg.setDefaultSuffix("csv")
            dlg.setWindowTitle("Export SquatchCut cutlist")

            if dlg.exec_() != QtWidgets.QDialog.Accepted:
                return

            filenames = dlg.selectedFiles()
            if not filenames:
                return

            out_path = filenames[0]
            with SimpleProgressContext(
                "Exporting cutlist to CSV...", "SquatchCut Export"
            ):
                export_cutops_to_csv(out_path, cut_ops)

            QtWidgets.QMessageBox.information(
                Gui.getMainWindow(),
                "SquatchCut Export",
                f"Cutlist exported successfully to:\n{out_path}",
            )

        except Exception as e:
            from SquatchCut.ui.error_handling import ErrorMessages, handle_command_error

            handle_command_error(
                "Export Cutlist",
                e,
                ErrorMessages.EXPORT_FAILED,
                ErrorMessages.EXPORT_FAILED_ACTION,
            )


if Gui:
    Gui.addCommand("SquatchCut_ExportCutlist", ExportCutlistCommand())
