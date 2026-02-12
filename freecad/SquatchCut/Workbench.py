"""SquatchCut FreeCAD workbench implementation."""
from __future__ import annotations

import os
from typing import Optional

try:
    import FreeCAD
except ImportError:  # pragma: no cover - environment may not provide FreeCAD
    FreeCAD = None

try:
    import FreeCADGui as Gui
except ImportError:  # pragma: no cover - allow headless import without FreeCAD
    Gui = None

ICON_PATH = os.path.join(os.path.dirname(__file__), "resources", "icons", "SquatchCut.svg")
COMMAND_NAME = "SquatchCut_LoadCSV"
TOOLTIP = "SquatchCut V2 (SAE)"
MENU_TEXT = "Load CSV"

_WorkbenchBase = getattr(Gui, "Workbench", object)

_command_registered = False


class LoadCSVCommand:
    """Minimal command that currently logs invocation."""

    def GetResources(self) -> dict[str, str]:
        return {
            "Pixmap": ICON_PATH,
            "MenuText": MENU_TEXT,
            "ToolTip": TOOLTIP,
        }

    def Activated(self) -> None:
        msg = "SquatchCut: Load CSV command invoked.\n"
        if FreeCAD and hasattr(FreeCAD, "Console"):
            FreeCAD.Console.PrintMessage(msg)
        else:
            print(msg, end="")

    def IsActive(self) -> bool:
        return True


def register_load_csv_command(gui: Optional[object]) -> None:
    """Register the Load CSV command with the provided GUI host."""
    global _command_registered
    if gui is None or _command_registered or not hasattr(gui, "addCommand"):
        return
    gui.addCommand(COMMAND_NAME, LoadCSVCommand())
    _command_registered = True


class SquatchCutWorkbench(_WorkbenchBase):
    """Defines the workbench metadata and toolbar/menu layout."""

    MenuText = "SquatchCut"
    ToolTip = TOOLTIP
    Icon = ICON_PATH

    def Initialize(self) -> None:  # type: ignore[override]
        if Gui is None:
            return
        register_load_csv_command(Gui)
        self.appendToolbar("SquatchCut", [COMMAND_NAME])
        self.appendMenu("SquatchCut", [COMMAND_NAME])

    def GetClassName(self) -> str:  # type: ignore[override]
        return "Gui::PythonWorkbench"
