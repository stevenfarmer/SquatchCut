from __future__ import annotations

import traceback

from typing import Optional

from SquatchCut.core import logger
from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.icons import get_icon
from SquatchCut.gui.taskpanel_settings import TaskPanel_Settings

_settings_panel_instance: Optional[TaskPanel_Settings] = None


def _clear_settings_panel() -> None:
    global _settings_panel_instance
    _settings_panel_instance = None


def _current_settings_panel() -> Optional[TaskPanel_Settings]:
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
            "Pixmap": get_icon("tool_settings"),
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
            reuse = _settings_panel_instance is not None
            if reuse:
                try:
                    if hasattr(_settings_panel_instance, "sheet_width_edit"):
                        _ = _settings_panel_instance.sheet_width_edit.text()
                    # If no attribute, assume it is a test double and reuse.
                except Exception:
                    _clear_settings_panel()
                    reuse = False
            if not reuse:
                panel = TaskPanel_Settings()
                panel.set_close_callback(_clear_settings_panel)
                _settings_panel_instance = panel
                logger.info("[SquatchCut] >>> Opening new settings panel.")
            else:
                panel = _settings_panel_instance
                logger.info("[SquatchCut] >>> Reusing existing settings panel.")

            # FreeCAD only allows one active TaskPanel; close any existing dialog first.
            try:
                active_dialog = getattr(Gui.Control, "activeDialog", lambda: None)()
                if active_dialog and active_dialog is not panel:
                    close_fn = getattr(Gui.Control, "closeDialog", None)
                    if callable(close_fn):
                        close_fn()
            except Exception:
                pass

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
