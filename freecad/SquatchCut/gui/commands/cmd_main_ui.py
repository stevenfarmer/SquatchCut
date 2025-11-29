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

_main_panel_instance: SquatchCutTaskPanel | None = None

def _clear_main_panel():
    global _main_panel_instance
    _main_panel_instance = None


def _current_main_panel():
    return _main_panel_instance


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

        global _main_panel_instance
        if _main_panel_instance is not None:
            try:
                Gui.Control.showDialog(_main_panel_instance)
                logger.info("[SquatchCut] Reusing existing main task panel.")
            except Exception:
                pass
            return

        doc = App.ActiveDocument
        if doc is None:
            doc = App.newDocument("SquatchCut")
        panel = SquatchCutTaskPanel(doc)
        panel.set_close_callback(_clear_main_panel)
        _main_panel_instance = panel
        try:
            logger.info("[SquatchCut] Opening main task panel.")
        except Exception:
            pass
        Gui.Control.showDialog(panel)
        try:
            logger.info("[SquatchCut] Task panel opened.")
        except Exception:
            pass


def register():
    if Gui is not None:
        Gui.addCommand("SquatchCut_ShowTaskPanel", SquatchCutMainUICommand())
