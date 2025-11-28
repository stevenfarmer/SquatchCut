"""FreeCAD command to import panel definitions from CSV."""

"""@codex
Command: Open the CSV import dialog to load panels.
Interactions: Should invoke SC_CSVImportDialog and hand validated rows to core csv_loader.
Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).
"""

import csv
import os

try:
    import FreeCAD as App
    import FreeCADGui as Gui
except Exception:
    App = None
    Gui = None
from SquatchCut.core import logger

# Qt imports (FreeCAD standard pattern)
from SquatchCut.gui.qt_compat import QtWidgets, QtCore, QtGui

from SquatchCut.core import session, session_state
from SquatchCut.ui.messages import show_error, show_warning
from SquatchCut.core.geometry_sync import sync_source_panels_to_document

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # .../freecad/SquatchCut
    "resources",
    "icons",
)


MM_PER_INCH = 25.4


def _convert_length(value, csv_units: str):
    """Convert a numeric length to mm based on CSV units."""
    try:
        num = float(value)
    except Exception:
        return value
    if str(csv_units).lower() == "imperial":
        return num * MM_PER_INCH
    return num


def run_csv_import(doc, csv_path: str, csv_units: str = "metric"):
    """
    Core CSV import logic for SquatchCut.

    - doc: FreeCAD document into which shapes should be added.
    - csv_path: absolute path to the CSV to import.
    - csv_units: "metric" or "imperial" (imperial converted to mm).
    """
    logger.info(f"CSV selected: {csv_path}")

    if doc is None:
        doc = App.newDocument("SquatchCut")
    session.sync_state_from_doc(doc)

    # Load CSV data with validation
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            headers = reader.fieldnames or []
    except FileNotFoundError:
        show_error(f"CSV file not found:\n{csv_path}")
        logger.error(f"CSV file not found: {csv_path}")
        return
    except Exception as e:
        show_error(f"Failed to read CSV file:\n{csv_path}\n\n{e}")
        logger.error(f"Failed to read CSV: {e}")
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
        logger.error(f"Missing required CSV columns: {missing}")
        return

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
            width = _convert_length(width, csv_units)
            height = _convert_length(height, csv_units)

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
            logger.warning(f"Skipping invalid CSV row {idx}: {e}")

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

    # Store panels in pure session_state and push settings into doc if needed
    session_state.set_panels(valid_rows)
    session.sync_doc_from_state(doc)
    logger.info(f"Loaded {len(valid_rows)} panels")
    # Create geometry for panels and center view
    try:
        sync_source_panels_to_document()
    except Exception as exc:
        logger.error(f"Failed to sync panels to document: {exc}")


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
        if App is None or Gui is None:
            try:
                logger.warning("ImportCSVCommand.Activated() called outside FreeCAD GUI environment.")
            except Exception:
                pass
            return

        logger.debug("ImportCSVCommand.Activated() entered")

        try:
            doc = App.ActiveDocument
            if doc is None:
                doc = App.newDocument("SquatchCut")
                try:
                    Gui.ActiveDocument = doc
                except Exception:
                    pass

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
                from SquatchCut.core.preferences import SquatchCutPreferences

                prefs = SquatchCutPreferences()
                default_units = prefs.get_csv_units(prefs.get_measurement_system())
                units, ok = QtWidgets.QInputDialog.getItem(
                    None,
                    "CSV units",
                    "Select units for this CSV:",
                    ["metric", "imperial"],
                    current=0 if default_units == "metric" else 1,
                    editable=False,
                )
                if not ok:
                    return
                run_csv_import(doc, file_path, csv_units=units)
                prefs.set_csv_units(units)
            else:
                # User cancelled
                logger.info("Import CSV dialog cancelled by user")

            logger.debug("ImportCSVCommand.Activated() completed")
        except Exception as e:
            logger.error(f"Error in ImportCSVCommand.Activated(): {e}")

    def IsActive(self):
        """
        Let the command be always available for now.
        Later we can restrict to when a document is open, etc.
        """
        return App is not None and Gui is not None


# Export command instance used by InitGui.py:
COMMAND = ImportCSVCommand()
