from __future__ import annotations

import os
import traceback

try:
    import FreeCAD as App
    import FreeCADGui as Gui
except Exception:
    App = None
    Gui = None

from SquatchCut.core import logger
from SquatchCut.gui.taskpanel_settings import TaskPanel_Settings

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "resources",
    "icons",
)

_settings_panel_instance: TaskPanel_Settings | None = None


def _clear_settings_panel() -> None:
    global _settings_panel_instance
    _settings_panel_instance = None


def _current_settings_panel() -> TaskPanel_Settings | None:
    return _settings_panel_instance


class SquatchCutSettingsCommand:
    """
    Opens the SquatchCut Settings TaskPanel for editing:
    - sheet width/height
    - kerf (mm)
    - gap (mm)
    - default allow-rotation flag
    """

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONS_DIR, "squatchcut-settings.svg"),
            "MenuText": "Settings",
            "ToolTip": "Open SquatchCut settings for sheet size, logging, and developer tools.",
        }

    def IsActive(self):
        if App is None or Gui is None:
            return False
        wb = Gui.activeWorkbench()
        if wb is None:
            return False
        return wb.__class__.__name__ == "SquatchCutWorkbench"

    def Activated(self):
        if App is None or Gui is None:
            logger.warning("[SquatchCut] SquatchCut_Settings invoked outside FreeCAD GUI.")
            return

        logger.info("[SquatchCut] >>> Activated SquatchCut_Settings.")
        try:
            global _settings_panel_instance
            if _settings_panel_instance is None:
                panel = TaskPanel_Settings()
                panel.set_close_callback(_clear_settings_panel)
                _settings_panel_instance = panel
                logger.info("[SquatchCut] >>> Opening new settings panel.")
            else:
                panel = _settings_panel_instance
                logger.info("[SquatchCut] >>> Reusing existing settings panel.")

            Gui.Control.showDialog(panel)
            logger.info("[SquatchCut] >>> Settings panel opened.")
        except Exception as exc:
            error_msg = f"[SquatchCut][ERROR] Failed to open settings panel: {exc}"
            logger.error(error_msg)
            try:
                App.Console.PrintError(f"{error_msg}\n{traceback.format_exc()}")
            except Exception:
                pass


# Register the command
if Gui is not None:
    Gui.addCommand("SquatchCut_Settings", SquatchCutSettingsCommand())
