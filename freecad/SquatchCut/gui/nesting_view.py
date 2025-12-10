"""Helpers to build and manage the nested layout geometry in FreeCAD."""

from __future__ import annotations

from SquatchCut.core import logger
from SquatchCut.core.sheet_model import clear_group_children, get_or_create_group
from SquatchCut.freecad_integration import App, Part

NESTED_GROUP_NAME = "SquatchCut_NestedParts"


def ensure_nested_group(doc):
    """Ensure the nested parts group exists and return it."""
    if App is None:
        logger.warning("ensure_nested_group() skipped: FreeCAD not available.")
        return None
    if doc is None:
        doc = App.newDocument("SquatchCut")
    return get_or_create_group(doc, NESTED_GROUP_NAME)


def rebuild_nested_geometry(
    doc,
    placements,
    sheet_w=None,
    sheet_h=None,
    sheet_sizes=None,
    spacing=None,
    source_objects=None,
):
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
    removed = clear_group_children(group)
    logger.info(f">>> [SquatchCut] Nested group cleared and rebuilt with {removed} parts")

    source_objects = source_objects or []
    source_map = _build_source_map(source_objects, doc)
    if not source_map and placements:
        logger.warning("[SquatchCut][WARN] No valid source objects found for nesting; using fallback boxes.")

    def _find_source(part_id):
        return source_map.get(part_id) or doc.getObject(part_id) or doc.getObject(f"SC_Source_{part_id}")

    nested_objs = []
    size_list = sheet_sizes or []
    if not size_list and sheet_w and sheet_h:
        size_list = [(sheet_w, sheet_h)]
    if not size_list:
        if sheet_w and sheet_h:
            size_list = [(sheet_w, sheet_h)]
        else:
            size_list = [(0.0, 0.0)]
    sheet_spacing = float(spacing) if spacing is not None else (float(size_list[0][0]) * 0.25 if size_list and size_list[0][0] else 0.0)
    sheet_offsets = []
    current_offset = 0.0
    for width, _ in size_list:
        sheet_offsets.append(current_offset)
        current_offset += width + sheet_spacing

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
        idx = min(sheet_index, len(sheet_offsets) - 1 if sheet_offsets else 0)
        if idx < 0:
            idx = 0
        base_x = sheet_offsets[idx] + x
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


def _safe_object_name(obj):
    if obj is None:
        return ""
    try:
        return getattr(obj, "Name", "") or ""
    except ReferenceError:
        return ""


def _build_source_map(source_objects, doc):
    valid = {}
    for obj in source_objects or []:
        name = _safe_object_name(obj)
        if name:
            valid[name] = obj
    if doc is not None:
        source_group = doc.getObject("SquatchCut_SourceParts")
        if source_group is not None:
            for member in getattr(source_group, "Group", []) or []:
                name = _safe_object_name(member)
                if name:
                    valid[name] = member
        for obj in getattr(doc, "Objects", []) or []:
            try:
                name = getattr(obj, "Name", "") or ""
            except ReferenceError:
                continue
            if not name or not name.startswith("SC_Source_"):
                continue
            key = name.replace("SC_Source_", "", 1) or name
            if key not in valid:
                valid[key] = obj
    return valid
