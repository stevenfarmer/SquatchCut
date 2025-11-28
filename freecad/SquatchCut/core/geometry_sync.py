"""Helpers to synchronize SquatchCut panels into FreeCAD document geometry."""

from __future__ import annotations

try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
    import Part  # type: ignore
except Exception:  # pragma: no cover
    App = None
    Gui = None
    Part = None

from SquatchCut.core import logger, session, session_state
from SquatchCut.gui.view_utils import zoom_to_objects

SHEET_OBJECT_NAME = "SquatchCut_Sheet"
SOURCE_GROUP_NAME = "SquatchCut_SourcePanels"


def ensure_sheet_object(doc):
    """Create or update the single sheet outline object to match session sheet size."""
    if App is None or Part is None:
        logger.warning("ensure_sheet_object() skipped: FreeCAD/Part not available.")
        return None

    if doc is None:
        doc = App.newDocument("SquatchCut")
    try:
        if Gui:
            Gui.ActiveDocument = Gui.getDocument(doc.Name)
    except Exception:
        try:
            Gui.ActiveDocument = Gui.ActiveDocument or None
        except Exception:
            pass

    width, height = session_state.get_sheet_size()
    try:
        width = float(width)
        height = float(height)
    except Exception:
        logger.warning("ensure_sheet_object() skipped: invalid sheet size.")
        return None
    if width <= 0 or height <= 0:
        logger.warning("ensure_sheet_object() skipped: non-positive sheet size.")
        return None

    sheet_obj = doc.getObject(SHEET_OBJECT_NAME)
    if sheet_obj is None:
        sheet_obj = doc.addObject("Part::Feature", SHEET_OBJECT_NAME)

    try:
        sheet_obj.Shape = Part.makePlane(
            width,
            height,
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


def sync_source_panels_to_document():
    """Create/refresh source panel geometry in the active document and update the view."""
    if App is None or Part is None:
        logger.warning("sync_source_panels_to_document() skipped: FreeCAD/Part not available.")
        return

    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument("SquatchCut")
    try:
        if Gui:
            Gui.ActiveDocument = Gui.getDocument(doc.Name)
    except Exception:
        try:
            Gui.ActiveDocument = Gui.ActiveDocument or None
        except Exception:
            pass

    panels = session.get_panels()
    if not panels:
        logger.warning("sync_source_panels_to_document() called with no panels.")
        return

    sheet_obj = ensure_sheet_object(doc)

    group = doc.getObject(SOURCE_GROUP_NAME)
    if group is None:
        group = doc.addObject("App::DocumentObjectGroup", SOURCE_GROUP_NAME)
    try:
        if hasattr(group, "ViewObject"):
            group.ViewObject.Visibility = True
    except Exception:
        pass

    # Clear existing group children
    for obj in list(group.Group):
        try:
            doc.removeObject(obj.Name)
        except Exception:
            continue
    # Clean up any stray source objects not inside the group
    for obj in list(getattr(doc, "Objects", [])):
        if obj.Name.startswith("SC_Source_") and obj not in group.Group:
            try:
                doc.removeObject(obj.Name)
            except Exception:
                continue

    created = []
    x_cursor = 0.0
    y_offset = 0.0
    spacing = 10.0  # mm between panels

    for idx, panel in enumerate(panels):
        try:
            w = float(panel.get("width", 0))
            h = float(panel.get("height", 0))
        except Exception:
            continue
        if w <= 0 or h <= 0:
            continue
        name = panel.get("id") or panel.get("label") or f"P{idx+1}"

        # Build an explicit face in the XY plane (Z=0) to avoid edge-on rendering.
        p0 = App.Vector(x_cursor, y_offset, 0.0)
        p1 = App.Vector(x_cursor + w, y_offset, 0.0)
        p2 = App.Vector(x_cursor + w, y_offset + h, 0.0)
        p3 = App.Vector(x_cursor, y_offset + h, 0.0)
        wire = Part.makePolygon([p0, p1, p2, p3, p0])
        face = Part.Face(wire)

        obj = doc.addObject("Part::Feature", f"SC_Source_{name}")
        obj.Shape = face
        try:
            if not hasattr(obj, "SquatchCutPanel"):
                obj.addProperty(
                    "App::PropertyBool",
                    "SquatchCutPanel",
                    "SquatchCut",
                    "True if this object is a SquatchCut source panel.",
                )
            obj.SquatchCutPanel = True
        except Exception:
            pass
        try:
            if not hasattr(obj, "SquatchCutCanRotate"):
                obj.addProperty(
                    "App::PropertyBool",
                    "SquatchCutCanRotate",
                    "SquatchCut",
                    "Whether this panel may be rotated 90 degrees during nesting",
                )
            obj.SquatchCutCanRotate = bool(panel.get("allow_rotate", False))
        except Exception:
            pass
        try:
            if hasattr(obj, "ViewObject"):
                obj.ViewObject.Visibility = True
                try:
                    obj.ViewObject.DisplayMode = "Flat Lines"
                except Exception:
                    pass
        except Exception:
            pass
        group.addObject(obj)
        created.append(obj)

        x_cursor += w + spacing

    session.set_source_panel_objects(created)
    try:
        session_state.set_source_panel_objects(created)
    except Exception:
        pass

    if doc is not None:
        doc.recompute()

    # Optional debug: log the first panel's vertices to verify orientation
    if session.get_source_panel_objects():
        first = session.get_source_panel_objects()[0]
        try:
            verts = list(first.Shape.Vertexes)
            coords = ", ".join(f"({v.Point.x:.2f}, {v.Point.y:.2f}, {v.Point.z:.2f})" for v in verts)
            logger.debug(f"First source panel '{first.Name}' vertices: {coords}")
        except Exception as exc:  # pragma: no cover
            logger.warning(f"Failed to inspect source panel vertices: {exc!r}")

    try:
        targets = [o for o in [sheet_obj] + created if o is not None]
    except Exception:
        targets = created
        if sheet_obj is not None:
            targets = [sheet_obj] + created
    if targets:
        zoom_to_objects(targets)

    logger.info(f"Created {len(created)} source panel shapes in document.")
    logger.info(f"Source panel layout: {len(created)} panels, x_span={x_cursor:.1f} mm")
