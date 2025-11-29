"""Command to reset the SquatchCut view to the sheet and nested layout."""

from __future__ import annotations

import os

try:
    import FreeCAD as App
    import FreeCADGui as Gui
except Exception:  # pragma: no cover
    App = None
    Gui = None

from SquatchCut.core import logger
from SquatchCut.gui.view_helpers import (
    fit_view_to_sheet,
    get_nested_group,
    get_sheet_object,
    show_only_sheet_and_nested,
)

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # .../SquatchCut/gui
    "resources",
    "icons",
)


class ResetViewCommand:
    """
    SquatchCut command that focuses the view on the sheet and nested parts.
    """

    def GetResources(self):
        return {
            "MenuText": "Reset View",
            "ToolTip": "Show the sheet and nested layout, hide source parts, and fit the view.",
            "Pixmap": os.path.join(ICONS_DIR, "squatchcut.svg"),
        }

    def Activated(self):
        if App is None:
            logger.warning("ResetViewCommand.Activated() called outside FreeCAD.")
            return

        doc = App.ActiveDocument
        if doc is None:
            logger.info("[SquatchCut] Reset view skipped: no active document.")
            return

        sheet = get_sheet_object(doc)
        nested_group = get_nested_group(doc)
        if sheet is None and nested_group is None:
            logger.info("[SquatchCut] Reset view skipped: no sheet or nested layout.")
            return

        logger.info("[SquatchCut] Reset view: showing sheet and nested parts.")
        show_only_sheet_and_nested(doc)
        fit_view_to_sheet(doc)

    def IsActive(self):
        if App is None:
            return False
        doc = App.ActiveDocument
        if doc is None:
            return False
        return get_sheet_object(doc) is not None or get_nested_group(doc) is not None
