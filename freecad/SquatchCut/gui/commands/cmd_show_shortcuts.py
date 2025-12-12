"""FreeCAD command to show keyboard shortcuts help."""

from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.icons import get_icon
from SquatchCut.gui.keyboard_shortcuts import show_shortcuts_help


class ShowShortcutsCommand:
    """Show available keyboard shortcuts for SquatchCut."""

    def GetResources(self):
        return {
            "MenuText": "Keyboard Shortcuts",
            "ToolTip": "Show available keyboard shortcuts for SquatchCut operations.",
            "Pixmap": get_icon("help"),
        }

    def IsActive(self):
        return App is not None and Gui is not None

    def Activated(self):
        show_shortcuts_help()


# Register command
if Gui is not None:
    Gui.addCommand("SquatchCut_ShowShortcuts", ShowShortcutsCommand())

COMMAND = ShowShortcutsCommand()
