"""Helpers for building source preview geometry."""

from __future__ import annotations

try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
    import Part  # type: ignore
except Exception:  # pragma: no cover
    App = None
    Gui = None
    Part = None

from SquatchCut.core import logger
from SquatchCut.core.sheet_model import ensure_sheet_object, get_or_create_group, clear_group


SOURCE_GROUP_NAME = "SquatchCut_SourceParts"


def _ensure_group(doc):
    group = get_or_create_group(doc, SOURCE_GROUP_NAME)
    try:
        if hasattr(group, "ViewObject"):
            group.ViewObject.Visibility = True
    except Exception:
        pass
    return group


def rebuild_source_preview(parts):
    """
    Clear and rebuild source preview rectangles under SquatchCut_SourceParts.

    Returns (group, created_objects).
    """
    if App is None or Part is None:
        logger.warning("rebuild_source_preview() skipped: FreeCAD/Part not available.")
        return None, []

    doc = App.ActiveDocument or App.newDocument("SquatchCut")
    try:
        if Gui:
            Gui.ActiveDocument = Gui.getDocument(doc.Name)
    except Exception:
        pass

    group = _ensure_group(doc)
    removed = clear_group(group)
    logger.info(f">>> [SquatchCut] Source group cleared and rebuilt with {removed} parts")

    created = []
    x_cursor = 0.0
    y_offset = 0.0
    spacing = 10.0

    for idx, panel in enumerate(parts or []):
        try:
            w = float(panel.get("width", 0))
            h = float(panel.get("height", 0))
        except Exception:
            continue
        if w <= 0 or h <= 0:
            continue
        name = panel.get("id") or panel.get("label") or f"P{idx+1}"

        p0 = App.Vector(x_cursor, y_offset, 0.0)
        p1 = App.Vector(x_cursor + w, y_offset, 0.0)
        p2 = App.Vector(x_cursor + w, y_offset + h, 0.0)
        p3 = App.Vector(x_cursor, y_offset + h, 0.0)
        wire = Part.makePolygon([p0, p1, p2, p3, p0])
        face = Part.Face(wire)

        obj = doc.addObject("Part::Feature", f"SC_Source_{name}")
        obj.Shape = face
        try:
            if hasattr(obj, "ViewObject"):
                obj.ViewObject.DisplayMode = "Flat Lines"
                obj.ViewObject.Visibility = True
        except Exception:
            pass
        group.addObject(obj)
        created.append(obj)
        x_cursor += w + spacing

    try:
        doc.recompute()
    except Exception:
        pass

    return group, created
