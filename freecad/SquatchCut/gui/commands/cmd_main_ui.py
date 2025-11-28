"""Main SquatchCut command that opens the unified Task panel."""

from __future__ import annotations

import os

try:
    import FreeCAD as App
    import FreeCADGui as Gui
except Exception:
    App = None
    Gui = None

from SquatchCut.core import logger
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "resources",
    "icons",
)


class SquatchCutMainUICommand:
    """Open the consolidated SquatchCut Task panel."""

    def GetResources(self):
        return {
            "MenuText": "SquatchCut",
            "ToolTip": "Open SquatchCut sheet optimization UI",
            "Pixmap": os.path.join(ICONS_DIR, "squatchcut.svg"),
        }

    def IsActive(self):
        # Only active inside a running FreeCAD GUI session
        return App is not None and Gui is not None

    def Activated(self):
        if App is None or Gui is None:
            try:
                logger.warning("SquatchCutMainUICommand.Activated() called outside FreeCAD GUI environment.")
            except Exception:
                pass
            return

        doc = App.ActiveDocument
        if doc is None:
            doc = App.newDocument("SquatchCut")
        try:
            logger.info(">>> [SquatchCut] Opening main task panel.")
        except Exception:
            pass
        panel = SquatchCutTaskPanel(doc)
        Gui.Control.showDialog(panel)


def register():
    if Gui is not None:
        Gui.addCommand("SquatchCut_ShowTaskPanel", SquatchCutMainUICommand())
