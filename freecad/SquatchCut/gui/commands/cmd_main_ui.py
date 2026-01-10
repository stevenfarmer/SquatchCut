"""Main SquatchCut command that opens the unified Task panel."""

from __future__ import annotations

from typing import Optional

from SquatchCut.core import logger
from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.icons import get_icon
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel

_main_panel_instance: Optional[SquatchCutTaskPanel] = None

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
            "Pixmap": get_icon("main"),
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
                # Close any other active TaskPanel before reusing this one
                try:
                    active_dialog = getattr(Gui.Control, "activeDialog", lambda: None)()
                    if active_dialog and active_dialog is not _main_panel_instance:
                        close_fn = getattr(Gui.Control, "closeDialog", None)
                        if callable(close_fn):
                            close_fn()
                except Exception:
                    pass
                Gui.Control.showDialog(_main_panel_instance)
                logger.info("Reusing existing main task panel.")
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
            logger.info("Opening main task panel.")
        except Exception:
            pass
        # Close any existing TaskPanel to avoid FreeCAD "Active task dialog" errors
        try:
            active_dialog = getattr(Gui.Control, "activeDialog", lambda: None)()
            if active_dialog and active_dialog is not panel:
                close_fn = getattr(Gui.Control, "closeDialog", None)
                if callable(close_fn):
                    close_fn()
        except Exception:
            pass
        Gui.Control.showDialog(panel)
        try:
            logger.info("Task panel opened.")
        except Exception:
            pass


def register():
    if Gui is not None:
        Gui.addCommand("SquatchCut_ShowTaskPanel", SquatchCutMainUICommand())
