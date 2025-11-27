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
    from PySide2 import QtWidgets, QtCore, QtGui

import os
import FreeCAD as App  # type: ignore
import FreeCADGui as Gui  # type: ignore

try:
    from SquatchCut.core import session_state  # type: ignore
    from SquatchCut.gui.dialogs.dlg_sheet_size import SC_SheetSizeDialog  # type: ignore
except Exception:
    import SquatchCut.core.session_state as session_state  # type: ignore
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

            sess = getattr(session_state, "SESSION", None)
            if not sess:
                raise RuntimeError("SESSION singleton not available in session_state")

            sess.set_sheet_size(width, height, units)

            App.Console.PrintMessage(
                f">>> [SquatchCut] SetSheetSize: updated to {sess.sheet_width} x {sess.sheet_height} {sess.sheet_units}\n"
            )

            QtWidgets.QMessageBox.information(
                None,
                "SquatchCut",
                f"Sheet size saved: {sess.sheet_width} x {sess.sheet_height} ({sess.sheet_units}).",
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
