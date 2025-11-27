import FreeCAD
import FreeCADGui

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
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if doc is None:
            FreeCAD.Console.PrintError("[SquatchCut] No active document for settings.\n")
            return

        panel = SquatchCutControlPanel(doc)
        FreeCADGui.Control.showDialog(panel)


# Register the command
FreeCADGui.addCommand("SquatchCut_Settings", SquatchCutSettingsCommand())
