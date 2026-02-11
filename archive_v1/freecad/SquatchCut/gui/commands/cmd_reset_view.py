"""Command to reset the SquatchCut view to the sheet and nested layout."""

from __future__ import annotations

from SquatchCut.core import logger
from SquatchCut.freecad_integration import App
from SquatchCut.gui.icons import get_icon
from SquatchCut.gui.view_helpers import (
    fit_view_to_sheet_and_nested,
    fit_view_to_source,
    get_nested_group,
    get_sheet_object,
    show_nested_only,
    show_source_and_sheet,
)


class ResetViewCommand:
    """
    SquatchCut command that focuses the view on the sheet and nested parts.
    """

    def GetResources(self):
        return {
            "MenuText": "Reset View",
            "ToolTip": "Show the sheet and nested layout, hide source parts, and fit the view.",
            "Pixmap": get_icon("reset_view"),
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

        has_nested = nested_group is not None and bool(
            getattr(nested_group, "Group", [])
        )
        if has_nested:
            show_nested_only(doc)
            fit_view_to_sheet_and_nested(doc)
        else:
            show_source_and_sheet(doc)
            fit_view_to_source(doc)

    def IsActive(self):
        if App is None:
            return False
        doc = App.ActiveDocument
        if doc is None:
            return False
        return get_sheet_object(doc) is not None or get_nested_group(doc) is not None
