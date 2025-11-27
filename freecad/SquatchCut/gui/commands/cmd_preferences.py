"""FreeCAD command to open SquatchCut preferences."""

from __future__ import annotations

"""@codex
Command: Open SquatchCut preferences.
Interactions: Should display preferences UI and read/write via core preferences.
Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).
"""

# Qt bindings (FreeCAD ships PySide / PySide2, not PySide6)
try:
    from PySide import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import os
import FreeCAD as App  # type: ignore

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
            "ToolTip": "Open SquatchCut preferences.",
            "Pixmap": os.path.join(ICONS_DIR, "preferences.svg"),
        }

    def Activated(self):  # noqa: N802  (FreeCAD API)
        QtWidgets.QMessageBox.information(
            None,
            "SquatchCut Preferences",
            "Use the Sheet Size dialog for sheet defaults; additional preferences may be managed via FreeCAD preferences.",
        )

    def IsActive(self):  # noqa: N802  (FreeCAD API)
        return True


COMMAND = SC_PreferencesCommand()
