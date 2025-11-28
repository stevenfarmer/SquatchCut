try:
    import FreeCAD as App
    import FreeCADGui as Gui
except Exception:
    App = None
    Gui = None

from SquatchCut.ui.control_panel import SquatchCutControlPanel


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
            "Pixmap": ":/icons/Preferences-General.svg",
            "MenuText": "SquatchCut Settings",
            "ToolTip": "Edit sheet size, kerf, gap, and default rotation settings for SquatchCut",
        }

    def IsActive(self):
        return App is not None and Gui is not None

    def Activated(self):
        if App is None or Gui is None:
            try:
                from SquatchCut.core import logger

                logger.warning("SquatchCutSettingsCommand.Activated() called outside FreeCAD GUI environment.")
            except Exception:
                pass
            return

        doc = App.ActiveDocument
        if doc is None:
            App.Console.PrintError("[SquatchCut] No active document for settings.\n")
            return

        panel = SquatchCutControlPanel(doc)
        Gui.Control.showDialog(panel)


# Register the command
if Gui is not None:
    Gui.addCommand("SquatchCut_Settings", SquatchCutSettingsCommand())
