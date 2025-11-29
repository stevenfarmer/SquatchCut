"""Sheet object helpers for SquatchCut."""

from __future__ import annotations

try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
    import Part  # type: ignore
except Exception:  # pragma: no cover
    App = None
    Gui = None
    Part = None

from SquatchCut.core import logger, session

SHEET_OBJECT_NAME = "SquatchCut_Sheet"


def ensure_sheet_object(width_mm: float, height_mm: float, doc=None):
    """
    Create or update the single sheet outline object.

    - Uses name SquatchCut_Sheet.
    - Updates dimensions in place if it exists.
    - Places lower-left at (0, 0).
    """
    if App is None or Part is None:
        logger.warning("ensure_sheet_object() skipped: FreeCAD/Part not available.")
        return None

    if doc is None:
        doc = App.ActiveDocument or App.newDocument("SquatchCut")
    try:
        if Gui:
            Gui.ActiveDocument = Gui.getDocument(doc.Name)
    except Exception:
        pass

    try:
        w = float(width_mm)
        h = float(height_mm)
    except Exception:
        logger.warning("ensure_sheet_object() skipped: invalid sheet size.")
        return None
    if w <= 0 or h <= 0:
        logger.warning("ensure_sheet_object() skipped: non-positive sheet size.")
        return None

    sheet_obj = doc.getObject(SHEET_OBJECT_NAME)
    if sheet_obj is None:
        sheet_obj = doc.addObject("Part::Feature", SHEET_OBJECT_NAME)

    try:
        sheet_obj.Shape = Part.makePlane(
            w,
            h,
            App.Vector(0.0, 0.0, 0.0),
            App.Vector(1, 0, 0),
            App.Vector(0, 1, 0),
        )
    except Exception as exc:
        logger.warning(f"Failed to update sheet outline shape: {exc!r}")
    try:
        if hasattr(sheet_obj, "ViewObject"):
            sheet_obj.ViewObject.DisplayMode = "Flat Lines"
    except Exception:
        pass

    session.set_sheet_objects([sheet_obj])
    try:
        doc.recompute()
    except Exception:
        pass

    return sheet_obj
