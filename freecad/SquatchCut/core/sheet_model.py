"""Sheet object helpers for SquatchCut."""

from __future__ import annotations

from SquatchCut.core import logger, session
from SquatchCut.freecad_integration import App, Gui, Part

SHEET_OBJECT_NAME = "SquatchCut_Sheet"
SHEET_BOUNDARY_PREFIX = "SquatchCut_Sheet_"


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
        logger.info("[SquatchCut] Sheet object created.")
    else:
        logger.info("[SquatchCut] Sheet object updated to "
                    f"{w:.1f} x {h:.1f} mm.")

    try:
        sheet_obj.Shape = Part.makePlane(
            w,
            h,
            App.Vector(0.0, 0.0, 0.0),
            App.Vector(0, 0, 1),
            App.Vector(1, 0, 0),
        )
    except Exception as exc:
        logger.warning(f"Failed to update sheet outline shape: {exc!r}")
    try:
        if hasattr(sheet_obj, "ViewObject") and sheet_obj.ViewObject:
            sheet_obj.ViewObject.DisplayMode = "Flat Lines"
            sheet_obj.ViewObject.ShapeColor = (0.5, 0.5, 0.5)
    except Exception:
        pass

    session.set_sheet_objects([sheet_obj])
    try:
        doc.recompute()
    except Exception:
        pass

    return sheet_obj


def get_or_create_group(doc, name):
    if doc is None:
        return None
    group = doc.getObject(name)
    if group is None:
        group = doc.addObject("App::DocumentObjectGroup", name)
        group.Label = name
    return group


def clear_group_children(group):
    """
    Remove all children from the given FreeCAD group without deleting the group.
    """
    removed = 0
    if group is None:
        return 0
    doc = getattr(group, "Document", None)
    children = list(getattr(group, "Group", []) or [])
    for child in children:
        if child is None:
            continue
        try:
            name = getattr(child, "Name", None)
        except ReferenceError:
            name = None
        if not name:
            continue
        try:
            if doc:
                doc.removeObject(name)
            removed += 1
        except Exception:
            continue
    return removed


def clear_group(group):
    """
    Backwards-compatible alias for clear_group_children().
    """
    return clear_group_children(group)


def clear_sheet_boundaries(doc):
    """Remove any sheet boundary objects created for multi-sheet layouts."""
    if doc is None:
        return
    removed = []
    for obj in list(getattr(doc, "Objects", []) or []):
        name = getattr(obj, "Name", "") or ""
        if name.startswith(SHEET_BOUNDARY_PREFIX) and name != SHEET_OBJECT_NAME:
            try:
                doc.removeObject(name)
                removed.append(name)
            except Exception:
                continue
    return removed


def _create_sheet_feature(doc, width_mm, height_mm, name, label, offset_x):
    """Create a single sheet boundary plane at the requested offset."""
    try:
        obj = doc.addObject("Part::Feature", name)
    except Exception:
        return None
    try:
        obj.Label = label
    except Exception:
        pass
    try:
        obj.Shape = Part.makePlane(
            float(width_mm),
            float(height_mm),
            App.Vector(offset_x, 0.0, 0.0),
            App.Vector(0, 0, 1),
            App.Vector(1, 0, 0),
        )
    except Exception:
        try:
            obj.Shape = Part.makePlane(
                float(width_mm),
                float(height_mm),
                App.Vector(0.0, 0.0, 0.0),
                App.Vector(0, 0, 1),
                App.Vector(1, 0, 0),
            )
        except Exception:
            pass
    try:
        if hasattr(obj, "ViewObject") and obj.ViewObject:
            obj.ViewObject.DisplayMode = "Flat Lines"
            obj.ViewObject.ShapeColor = (0.5, 0.5, 0.5)
    except Exception:
        pass
    try:
        if hasattr(obj, "Placement"):
            placement = obj.Placement
            placement.Base = App.Vector(offset_x, 0.0, 0.0)
            obj.Placement = placement
    except Exception:
        pass
    return obj


def build_sheet_boundaries(doc, sheet_sizes, spacing):
    """
    Create sheet boundary planes for each configured sheet size and return the objects plus offsets.
    """
    if doc is None:
        return [], []
    boundaries = []
    offsets = []
    current_x = 0.0
    for idx, (width, height) in enumerate(sheet_sizes or []):
        if width <= 0 or height <= 0:
            offsets.append(current_x)
            current_x += spacing
            continue
        offsets.append(current_x)
        if idx == 0:
            sheet_obj = ensure_sheet_object(width, height, doc)
            if sheet_obj:
                try:
                    sheet_obj.Label = f"Sheet_{idx + 1}"
                except Exception:
                    pass
                try:
                    placement = sheet_obj.Placement
                    placement.Base = App.Vector(current_x, 0.0, 0.0)
                    sheet_obj.Placement = placement
                except Exception:
                    pass
                boundaries.append(sheet_obj)
        else:
            name = f"{SHEET_BOUNDARY_PREFIX}{idx + 1}"
            label = f"Sheet_{idx + 1}"
            obj = _create_sheet_feature(doc, width, height, name, label, current_x)
            if obj:
                boundaries.append(obj)
        current_x += width + spacing
    return boundaries, offsets


def compute_sheet_spacing(sheet_sizes, gap_mm: float | None):
    """Determine spacing between sheets based on gap or a proportion of the widest sheet."""
    max_width = 0.0
    for width, _ in sheet_sizes:
        if width and width > max_width:
            max_width = width
    margin_by_width = max_width * 0.25 if max_width > 0 else 0.0
    gap = float(gap_mm or 0.0)
    return max(margin_by_width, gap)
