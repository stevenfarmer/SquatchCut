"""Helpers to build and manage the nested layout geometry in FreeCAD."""

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

NESTED_GROUP_NAME = "SquatchCut_NestedParts"


def ensure_nested_group(doc):
    """Ensure the nested parts group exists and return it."""
    if App is None:
        logger.warning("ensure_nested_group() skipped: FreeCAD not available.")
        return None
    if doc is None:
        doc = App.newDocument("SquatchCut")
    group = doc.getObject(NESTED_GROUP_NAME)
    if group is None:
        group = doc.addObject("App::DocumentObjectGroup", NESTED_GROUP_NAME)
    return group


def rebuild_nested_geometry(doc, placements, sheet_w, sheet_h, source_objects=None):
    """
    Clear existing nested geometry and rebuild from placements.

    Returns (group, nested_objects).
    """
    if App is None or Part is None:
        logger.warning("rebuild_nested_geometry() skipped: FreeCAD/Part unavailable.")
        return None, []

    group = ensure_nested_group(doc)
    if group is None:
        return None, []

    # Remove any legacy nested containers and children
    legacy = doc.getObject("SquatchCut_Sheets")
    if legacy is not None:
        for child in list(getattr(legacy, "Group", [])):
            try:
                doc.removeObject(child.Name)
            except Exception:
                continue
        try:
            doc.removeObject(legacy.Name)
        except Exception:
            pass

    # Clear existing nested children
    for obj in list(getattr(group, "Group", [])):
        try:
            doc.removeObject(obj.Name)
        except Exception:
            continue
    # Remove stray nested objects not in group
    for obj in list(getattr(doc, "Objects", [])):
        if obj.Name.startswith("SC_Nested_") and obj not in getattr(group, "Group", []):
            try:
                doc.removeObject(obj.Name)
            except Exception:
                continue

    source_objects = source_objects or []
    source_map = {getattr(o, "Name", ""): o for o in source_objects}

    def _find_source(part_id):
        return source_map.get(part_id) or doc.getObject(part_id) or doc.getObject(f"SC_Source_{part_id}")

    nested_objs = []
    sheet_margin = float(sheet_w) * 0.25 if sheet_w else 0.0

    for idx, pp in enumerate(placements or []):
        try:
            sheet_index = int(getattr(pp, "sheet_index", 0) or 0)
            x = float(getattr(pp, "x", 0.0))
            y = float(getattr(pp, "y", 0.0))
            w = float(getattr(pp, "width", 0.0))
            h = float(getattr(pp, "height", 0.0))
        except Exception:
            continue
        if w <= 0 or h <= 0:
            continue

        name = f"SC_Nested_{pp.id}_{sheet_index}_{idx}"
        src = _find_source(getattr(pp, "id", ""))
        if src and hasattr(src, "Shape"):
            obj = doc.addObject("Part::Feature", name)
            obj.Shape = src.Shape.copy()
        else:
            obj = doc.addObject("Part::Box", name)
            obj.Width = w
            obj.Length = h
            obj.Height = 1.0

        placement = obj.Placement
        base_x = sheet_index * (float(sheet_w) + sheet_margin) + x
        base_y = y
        placement.Base = App.Vector(base_x, base_y, 0.0)
        try:
            placement.Rotation = App.Rotation(App.Vector(0, 0, 1), float(getattr(pp, "rotation_deg", 0)))
        except Exception:
            pass
        obj.Placement = placement
        try:
            obj.ViewObject.DisplayMode = "Flat Lines"
        except Exception:
            pass
        group.addObject(obj)
        nested_objs.append(obj)

    try:
        doc.recompute()
    except Exception:
        pass

    logger.info(f">>> [SquatchCut] Rebuilt nesting view with {len(nested_objs)} object(s).")
    return group, nested_objs
