"""Main SquatchCut command that opens the unified Task panel."""

from __future__ import annotations

import os

import FreeCAD as App
import FreeCADGui as Gui

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
        return True

    def Activated(self):
        doc = App.ActiveDocument
        if doc is None:
            doc = App.newDocument("SquatchCut")
        panel = SquatchCutTaskPanel(doc)
        Gui.Control.showDialog(panel)


def register():
    Gui.addCommand("SquatchCut_MainUI", SquatchCutMainUICommand())
