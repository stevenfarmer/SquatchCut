"""FreeCAD command to open the Sheet Size configuration dialog."""

from __future__ import annotations

"""@codex
Command: Open the Sheet Size dialog for configuring sheet dimensions and spacing.
Interactions: Should use SC_SheetSizeDialog and update core preferences defaults.
Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).
"""

# Qt bindings (FreeCAD ships PySide / PySide2, not PySide6)
try:
    from PySide import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets

import os
import FreeCAD as App  # type: ignore

try:
    from SquatchCut.core import session, session_state  # type: ignore
    from SquatchCut.gui.dialogs.dlg_sheet_size import SC_SheetSizeDialog  # type: ignore
except Exception:
    import SquatchCut.core.session_state as session_state  # type: ignore
    import SquatchCut.core.session as session  # type: ignore
    from SquatchCut.gui.dialogs.dlg_sheet_size import SC_SheetSizeDialog  # type: ignore

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # .../freecad/SquatchCut
    "resources",
    "icons",
)


class SC_SetSheetSizeCommand:
    """Open the Sheet Size dialog to configure sheet dimensions and spacing."""

    COMMAND_NAME = "SC_SetSheetSize"

    def GetResources(self):  # noqa: N802  (FreeCAD API)
        return {
            "Pixmap": ":/icons/Draft_Rectangle.svg",
            "MenuText": "Set Sheet Size",
            "ToolTip": "Set the sheet width and height for nesting",
        }

    def Activated(self):  # noqa: N802  (FreeCAD API)
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

            width, height, units = dialog.get_values()

            doc = App.ActiveDocument
            if doc is None:
                doc = App.newDocument("SquatchCut")
            session_state.set_sheet_size(width, height)
            session.sync_doc_from_state(doc)

            App.Console.PrintMessage(
                f">>> [SquatchCut] SetSheetSize: updated to {width} x {height} {units}\n"
            )

            QtWidgets.QMessageBox.information(
                None,
                "SquatchCut",
                f"Sheet size saved: {width} x {height} ({units}).",
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
        return True


COMMAND = SC_SetSheetSizeCommand()
