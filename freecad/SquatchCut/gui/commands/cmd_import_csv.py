"""FreeCAD command to import panel definitions from CSV."""

from SquatchCut.core import logger, session

# @codex
# Command: Open the CSV import dialog to load panels.
# Interactions: Should invoke SC_CSVImportDialog and hand validated rows to core csv_import.
# Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).
from SquatchCut.core.csv_import import validate_csv_file
from SquatchCut.core.geometry_sync import sync_source_panels_to_document
from SquatchCut.core.input_validation import validate_csv_file_path
from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.icons import get_icon

# Qt imports (FreeCAD standard pattern)
from SquatchCut.gui.qt_compat import QtWidgets
from SquatchCut.gui.view_helpers import fit_view_to_source, show_source_and_sheet
from SquatchCut.ui.messages import show_error

MM_PER_INCH = 25.4


def run_csv_import(doc, csv_path: str, csv_units: str = "auto"):
    """
    Core CSV import logic for SquatchCut.

    - doc: FreeCAD document into which shapes should be added.
    - csv_path: absolute path to the CSV to import.
    - csv_units: "metric", "imperial", or "auto" (auto-detect from CSV content).
    """
    from SquatchCut.core.csv_loader import detect_csv_units
    from SquatchCut.ui.progress import SimpleProgressContext

    logger.info(f"CSV selected: {csv_path}")

    with SimpleProgressContext("Importing CSV file...", "SquatchCut Import"):
        if doc is None:
            doc = App.newDocument("SquatchCut")
        session.sync_state_from_doc(doc)

        # Auto-detect units if requested
        if csv_units == "auto":
            csv_units = detect_csv_units(csv_path)
            logger.info(f"Auto-detected CSV units: {csv_units}")

            # Update measurement system to match detected units
            from SquatchCut.core import session_state

            session_state.set_measurement_system(csv_units)

        # Import session_state for use later in the function
        from SquatchCut.core import session_state

        # Normalize units
        units_val = str(csv_units or "mm").lower()
        if units_val == "metric":
            units_val = "mm"
        if units_val == "imperial":
            units_val = "in"
        csv_units = units_val

        try:
            valid_rows, errors = validate_csv_file(csv_path, csv_units=csv_units)
        except FileNotFoundError:
            show_error(f"CSV file not found:\n{csv_path}")
            logger.error(f"CSV file not found: {csv_path}")
            return
        except ValueError as exc:
            show_error(f"CSV import failed:\n{exc}")
            logger.error(f"CSV read error: {exc}")
            return

    if errors:
        show_error("CSV import failed. Check Report view for details.")
        logger.error("CSV import failed due to validation errors.")
        max_errors = 20
        for error in errors[:max_errors]:
            label = f"Row {error.row}" if error.row else "CSV"
            logger.error(f"{label}: {error.message}")
        if len(errors) > max_errors:
            logger.error(f"...and {len(errors) - max_errors} more validation error(s).")
        return

    # Store panels in pure session_state and push settings into doc if needed
    session_state.set_panels(valid_rows)
    session.sync_doc_from_state(doc)
    logger.info(f"CSV import completed. Imported {len(valid_rows)} parts.")
    # Create geometry for panels and center view
    try:
        sync_source_panels_to_document()
    except Exception as exc:
        logger.error(f"Failed to sync panels to document: {exc}")
    try:
        show_source_and_sheet(doc)
        fit_view_to_source(doc)
    except Exception:
        pass


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
            "MenuText": "Import Parts",
            "ToolTip": "Import rectangular parts from a CSV into the SquatchCut Source Parts group.",
            "Pixmap": get_icon("import_csv"),
        }

    def Activated(self):
        """
        Called when the user clicks the toolbar/menu item or when
        Gui.runCommand('SquatchCut_ImportCSV') is executed.
        """
        if App is None or Gui is None:
            try:
                logger.warning(
                    "ImportCSVCommand.Activated() called outside FreeCAD GUI environment."
                )
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
                try:
                    # Validate file path
                    validated_path = validate_csv_file_path(file_path)

                    from SquatchCut.core.csv_loader import detect_csv_units
                    from SquatchCut.core.preferences import SquatchCutPreferences

                    # Auto-detect units but allow user override
                    detected_units = detect_csv_units(validated_path)
                    prefs = SquatchCutPreferences()

                    units, ok = QtWidgets.QInputDialog.getItem(
                        None,
                        "CSV units",
                        f"Auto-detected: {detected_units}. Override if needed:",
                        ["auto (recommended)", "metric", "imperial"],
                        current=0,  # Default to auto
                        editable=False,
                    )
                    if not ok:
                        return

                    # Convert selection to actual units
                    if units == "auto (recommended)":
                        units = "auto"

                    run_csv_import(doc, validated_path, csv_units=units)

                    # Save the final detected/selected units
                    final_units = detected_units if units == "auto" else units
                    prefs.set_csv_units(final_units)
                except Exception as e:
                    from SquatchCut.ui.error_handling import handle_command_error

                    handle_command_error("Import CSV", e)
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

    # Programmatic import helper to bypass dialogs (used by GUI tests)
    def import_from_path(
        self, csv_path: str, units: str | None = None, csv_units: str | None = None
    ):
        if App is None:
            raise RuntimeError("FreeCAD App module not available for import_from_path.")
        doc = App.ActiveDocument
        if doc is None:
            doc = App.newDocument("SquatchCut")
        chosen_units = csv_units if csv_units is not None else units
        if chosen_units is None:
            try:
                from SquatchCut.core.preferences import SquatchCutPreferences

                prefs = SquatchCutPreferences()
                chosen_units = prefs.get_csv_units(prefs.get_measurement_system())
            except Exception:
                chosen_units = "mm"
        if chosen_units == "metric":
            chosen_units = "mm"
        if chosen_units == "imperial":
            chosen_units = "in"
        run_csv_import(doc, csv_path, csv_units=chosen_units)
        try:
            session.set_last_csv_path(csv_path)
        except Exception:
            pass


# Stable alias expected by tests and callers
ImportCsvCommand = ImportCSVCommand

# Export command instance used by InitGui.py:
COMMAND = ImportCsvCommand()

# Register FreeCAD command
if Gui is not None:
    Gui.addCommand("SquatchCut_ImportCSV", COMMAND)
