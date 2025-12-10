"""FreeCAD command to open the Sheet Size configuration dialog."""

from __future__ import annotations

"""@codex
Command: Open the Sheet Size dialog for configuring sheet dimensions and spacing.
Interactions: Should use SC_SheetSizeDialog and update core preferences defaults.
Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).
"""

from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.icons import get_icon
from SquatchCut.gui.qt_compat import QtWidgets
from SquatchCut.gui.view_helpers import fit_view_to_sheet_and_nested, show_sheet_only

try:
    from SquatchCut.core import session, session_state  # type: ignore
    from SquatchCut.core.sheet_model import ensure_sheet_object  # type: ignore
    from SquatchCut.gui.dialogs.dlg_sheet_size import SC_SheetSizeDialog  # type: ignore
except Exception:
    import SquatchCut.core.session as session  # type: ignore
    import SquatchCut.core.session_state as session_state  # type: ignore
    from SquatchCut.core.sheet_model import ensure_sheet_object  # type: ignore
    from SquatchCut.gui.dialogs.dlg_sheet_size import SC_SheetSizeDialog  # type: ignore
from SquatchCut.core import units as sc_units
from SquatchCut.ui.messages import show_error


class SC_SetSheetSizeCommand:
    """Open the Sheet Size dialog to configure sheet dimensions and spacing."""

    COMMAND_NAME = "SC_SetSheetSize"

    def GetResources(self):  # noqa: N802  (FreeCAD API)
        return {
            "Pixmap": get_icon("set_sheet_size"),
            "MenuText": "Set Sheet",
            "ToolTip": "Set the sheet dimensions used for SquatchCut nesting.",
        }

    def Activated(self):  # noqa: N802  (FreeCAD API)
        if App is None or Gui is None:
            try:
                from SquatchCut.core import logger

                logger.warning("SC_SetSheetSizeCommand.Activated() called outside FreeCAD GUI environment.")
            except Exception:
                pass
            return

        App.Console.PrintMessage(
            ">>> [SquatchCut] SetSheetSizeCommand.Activated() entered\n"
        )
        try:
            dialog = SC_SheetSizeDialog()
            result = dialog.exec()
            if result != QtWidgets.QDialog.Accepted:
                App.Console.PrintMessage(
                    ">>> [SquatchCut] SetSheetSize: dialog cancelled by user\n"
                )
                return

            try:
                width, height, _ = dialog.get_values()
            except ValueError as exc:
                show_error(
                    "Invalid imperial value. Use formats like 48, 48.5, 48 1/2, or 48-1/2."
                    if dialog.measurement_system == "imperial"
                    else str(exc),
                    title="SquatchCut",
                )
                return

            doc = App.ActiveDocument
            if doc is None:
                doc = App.newDocument("SquatchCut")
            session_state.set_sheet_size(width, height)
            session.sync_doc_from_state(doc)
            width, height = session_state.get_sheet_size()
            sheet_obj = ensure_sheet_object(width, height, doc)

            unit_label = sc_units.unit_label_for_system(dialog.measurement_system)
            primary_width = sc_units.format_length(width, dialog.measurement_system)
            primary_height = sc_units.format_length(height, dialog.measurement_system)
            secondary_label = "mm" if unit_label == "in" else "in"
            secondary_width = sc_units.format_length(
                width, "metric" if unit_label == "in" else "imperial"
            )
            secondary_height = sc_units.format_length(
                height, "metric" if unit_label == "in" else "imperial"
            )

            App.Console.PrintMessage(
                f">>> [SquatchCut] SetSheetSize: updated to {primary_width} x {primary_height} {unit_label} "
                f"({secondary_width} x {secondary_height} {secondary_label})\n"
            )
            logger.info(
                f"Set sheet size to {width} x {height} mm "
                f"(displayed as {primary_width} x {primary_height} {unit_label})."
            )
            if sheet_obj:
                try:
                    show_sheet_only(doc)
                    fit_view_to_sheet_and_nested(doc)
                except Exception:
                    pass

            QtWidgets.QMessageBox.information(
                None,
                "SquatchCut",
                f"Sheet size saved: {primary_width} x {primary_height} {unit_label} "
                f"({secondary_width} x {secondary_height} {secondary_label}).",
            )
        except Exception as exc:
            App.Console.PrintError(
                f">>> [SquatchCut] Error in SetSheetSizeCommand.Activated(): {exc}\n"
            )
        finally:
            App.Console.PrintMessage(
                ">>> [SquatchCut] SetSheetSizeCommand.Activated() completed\n"
            )

    def IsActive(self):  # noqa: N802  (FreeCAD API)
        return App is not None and Gui is not None


COMMAND = SC_SetSheetSizeCommand()
