"""FreeCAD command to import panel definitions from CSV."""

"""@codex
Command: Open the CSV import dialog to load panels.
Interactions: Should invoke SC_CSVImportDialog and hand validated rows to core csv_loader.
Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).
"""

import csv
import os

import FreeCAD as App
import FreeCADGui as Gui

# Qt imports (FreeCAD standard pattern)
try:
    from PySide import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from SquatchCut.core import csv_loader, session_state as session
from SquatchCut.ui.messages import show_error, show_warning

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

                # Load CSV data with validation
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        headers = reader.fieldnames or []
                except FileNotFoundError:
                    show_error(f"CSV file not found:\n{file_path}")
                    App.Console.PrintError(f"[SquatchCut] CSV file not found: {file_path}\n")
                    return
                except Exception as e:
                    show_error(f"Failed to read CSV file:\n{file_path}\n\n{e}")
                    App.Console.PrintError(f"[SquatchCut] Failed to read CSV: {e}\n")
                    return

                header_cols = {h.strip().lower() for h in headers if h}
                # Required columns based on current CSV format
                required_cols = {"id", "width", "height"}
                missing = sorted(required_cols - header_cols)
                if missing:
                    msg = (
                        "The selected CSV is missing required columns:\n"
                        + ", ".join(missing)
                        + "\n\nPlease fix the CSV and try again."
                    )
                    show_error(msg)
                    App.Console.PrintError(
                        f"[SquatchCut] Missing required CSV columns: {missing}\n"
                    )
                    return

                # Map normalized header names to actual names for safe access
                name_map = {h.strip().lower(): h for h in headers if h}
                valid_rows = []
                warn_count = 0

                for idx, row in enumerate(rows, start=2):  # header is line 1
                    try:
                        data = {k.strip().lower(): v for k, v in row.items()}
                        part_id = (data.get("id") or "").strip()
                        if not part_id:
                            raise ValueError("Missing id")

                        width_val = data.get("width")
                        height_val = data.get("height")
                        width = float(width_val) if width_val not in (None, "") else None
                        height = float(height_val) if height_val not in (None, "") else None
                        if width is None or height is None:
                            raise ValueError("Missing width or height")
                        if width <= 0 or height <= 0:
                            raise ValueError("Width and height must be > 0")

                        qty_raw = data.get("qty", "")
                        try:
                            qty = int(qty_raw) if str(qty_raw).strip() else 1
                        except Exception:
                            qty = 1

                        label = (data.get("label") or part_id).strip()
                        material = (data.get("material") or "").strip()
                        raw_allow = data.get("allow_rotate", None)
                        if raw_allow is None or str(raw_allow).strip() == "":
                            allow = False
                        else:
                            allow = str(raw_allow).strip().lower() in ("1", "true", "yes", "y")

                        valid_rows.append(
                            {
                                "id": part_id,
                                "width": width,
                                "height": height,
                                "qty": qty,
                                "label": label,
                                "material": material,
                                "allow_rotate": allow,
                            }
                        )
                    except Exception as e:
                        warn_count += 1
                        App.Console.PrintError(
                            f"[SquatchCut] Skipping invalid CSV row {idx}: {e}\n"
                        )

                if not valid_rows:
                    show_error(
                        "No valid panel rows were found in the CSV.\n"
                        "Please check the data and try again."
                    )
                    return

                if warn_count > 0:
                    show_warning(
                        f"{warn_count} row(s) in the CSV were invalid and were skipped.\n"
                        "Check the Report view for details."
                    )

                try:
                    import SquatchCut.core.session as session  # type: ignore
                except Exception as exc:
                    raise RuntimeError(f"Session module unavailable: {exc}") from exc

                session.SESSION.load_csv_panels(valid_rows, csv_path=file_path)
                session.SESSION.active_csv_path = file_path
                App.Console.PrintMessage(
                    f">>> [SquatchCut] Loaded {len(valid_rows)} panels\n"
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
