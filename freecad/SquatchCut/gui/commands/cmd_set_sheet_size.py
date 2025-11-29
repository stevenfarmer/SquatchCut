"""FreeCAD command to open the Sheet Size configuration dialog."""

from __future__ import annotations

"""@codex
Command: Open the Sheet Size dialog for configuring sheet dimensions and spacing.
Interactions: Should use SC_SheetSizeDialog and update core preferences defaults.
Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).
"""

import os
try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
except Exception:
    App = None
    Gui = None

from SquatchCut.gui.qt_compat import QtWidgets, QtCore, QtGui

try:
    from SquatchCut.core import session, session_state  # type: ignore
    from SquatchCut.core.sheet_model import ensure_sheet_object  # type: ignore
    from SquatchCut.gui.dialogs.dlg_sheet_size import SC_SheetSizeDialog  # type: ignore
    from SquatchCut.gui.view_utils import zoom_to_objects  # type: ignore
except Exception:
    import SquatchCut.core.session_state as session_state  # type: ignore
    import SquatchCut.core.session as session  # type: ignore
    from SquatchCut.core.sheet_model import ensure_sheet_object  # type: ignore
    from SquatchCut.gui.dialogs.dlg_sheet_size import SC_SheetSizeDialog  # type: ignore
    from SquatchCut.gui.view_utils import zoom_to_objects  # type: ignore
from SquatchCut.core import logger

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

            width, height, units = dialog.get_values()

            doc = App.ActiveDocument
            if doc is None:
                doc = App.newDocument("SquatchCut")
            session_state.set_sheet_size(width, height)
            session.sync_doc_from_state(doc)
            width, height = session_state.get_sheet_size()
            sheet_obj = ensure_sheet_object(width, height, doc)

            App.Console.PrintMessage(
                f">>> [SquatchCut] SetSheetSize: updated to {width} x {height} {units}\n"
            )
            logger.info(f"Set sheet size to {width} x {height} ({units}).")
            if sheet_obj:
                zoom_to_objects([sheet_obj])

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
        return App is not None and Gui is not None


COMMAND = SC_SetSheetSizeCommand()
