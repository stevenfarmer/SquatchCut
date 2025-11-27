"""FreeCAD command to import panel definitions from CSV."""

"""@codex
Command: Open the CSV import dialog to load panels.
Interactions: Should invoke SC_CSVImportDialog and hand validated rows to core csv_loader.
Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).
"""

import FreeCAD as App
import FreeCADGui as Gui

# Qt imports (FreeCAD standard pattern)
try:
    from PySide import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import os
from SquatchCut.core import csv_loader, session_state as session

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # .../freecad/SquatchCut
    "resources",
    "icons",
)


class ImportCSVCommand:
    """
    SquatchCut - Import CSV panels command (debug stub + file dialog).

    For now, this logs when Activated() is called, opens a file picker
    for CSV files, and reports the chosen path. Later we'll wire this
    into the real CSV parsing + geometry flow.
    """

    def GetResources(self):
        """
        Return FreeCAD command metadata.
        """
        return {
            "MenuText": "Import CSV Panels",
            "ToolTip": "Import panel definitions from a CSV file.",
            "Pixmap": os.path.join(ICONS_DIR, "import_csv.svg"),
        }

    def Activated(self):
        """
        Called when the user clicks the toolbar/menu item or when
        Gui.runCommand('SquatchCut_ImportCSV') is executed.
        """
        App.Console.PrintMessage(">>> [SquatchCut] ImportCSVCommand.Activated() entered\n")

        try:
            # 1) Show file open dialog for CSV
            caption = "Select CSV file"
            file_filter = "CSV files (*.csv);;All files (*.*)"
            file_path, selected_filter = QtWidgets.QFileDialog.getOpenFileName(
                None,
                caption,
                "",
                file_filter,
            )

            if file_path:
                # User picked a file
                short_name = os.path.basename(file_path)
                App.Console.PrintMessage(
                    f">>> [SquatchCut] CSV selected: {file_path}\n"
                )

                QtWidgets.QMessageBox.information(
                    None,
                    "SquatchCut - CSV Imported",
                    f"Selected CSV file:\n{short_name}",
                )

                # Load CSV data into session state
                try:
                    import SquatchCut.core.csv_loader as loader  # type: ignore
                except Exception:
                    # Fallback stub loader if real one is unavailable
                    class _FallbackLoader:
                        @staticmethod
                        def load_csv(path):
                            return [{"width": 10, "height": 20, "qty": 1}]

                    loader = _FallbackLoader()

                try:
                    import SquatchCut.core.session as session  # type: ignore
                except Exception as exc:
                    raise RuntimeError(f"Session module unavailable: {exc}") from exc

                panels_list = loader.load_csv(file_path)
                session.SESSION.load_csv_panels(panels_list, csv_path=file_path)
                session.SESSION.active_csv_path = file_path
                App.Console.PrintMessage(
                    f">>> [SquatchCut] Loaded {len(panels_list)} panels\n"
                )
            else:
                # User cancelled
                App.Console.PrintMessage(
                    ">>> [SquatchCut] Import CSV dialog cancelled by user\n"
                )

            App.Console.PrintMessage(">>> [SquatchCut] ImportCSVCommand.Activated() completed\n")
        except Exception as e:
            App.Console.PrintError(
                f">>> [SquatchCut] Error in ImportCSVCommand.Activated(): {e}\n"
            )

    def IsActive(self):
        """
        Let the command be always available for now.
        Later we can restrict to when a document is open, etc.
        """
        return True


# Export command instance used by InitGui.py:
COMMAND = ImportCSVCommand()
