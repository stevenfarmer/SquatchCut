"""FreeCAD command to open SquatchCut preferences."""

from __future__ import annotations

"""@codex
Command: Open SquatchCut preferences.
Interactions: Should display preferences UI and read/write via core preferences.
Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).
"""

import os

from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.qt_compat import QtWidgets
from SquatchCut.gui.dialog_preferences import SquatchCutPreferencesDialog

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # .../freecad/SquatchCut
    "resources",
    "icons",
)


class SC_PreferencesCommand:
    """Open the preferences window or panel."""

    COMMAND_NAME = "SC_Preferences"

    def GetResources(self):  # noqa: N802  (FreeCAD API)
        return {
            "MenuText": "Preferences",
            "ToolTip": "Open the SquatchCut preferences dialog.",
            "Pixmap": os.path.join(ICONS_DIR, "preferences.svg"),
        }

    def Activated(self):  # noqa: N802  (FreeCAD API)
        if App is None or Gui is None:
            try:
                from SquatchCut.core import logger

                logger.warning("SC_PreferencesCommand.Activated() called outside FreeCAD GUI environment.")
            except Exception:
                pass
            return

        dlg = SquatchCutPreferencesDialog()
        dlg.exec_()

    def IsActive(self):  # noqa: N802  (FreeCAD API)
        return App is not None and Gui is not None


COMMAND = SC_PreferencesCommand()
