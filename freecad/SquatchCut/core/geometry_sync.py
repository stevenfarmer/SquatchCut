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

from SquatchCut.core import logger, session


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

    group = doc.getObject("SquatchCut_SourcePanels")
    if group is None:
        group = doc.addObject("App::DocumentObjectGroup", "SquatchCut_SourcePanels")
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

    # 5) Force top-down, fit-all view in the active document
    try:
        if Gui.ActiveDocument is not None:
            view = Gui.ActiveDocument.ActiveView
            view.viewTop()
            view.setCameraType("Orthographic")
            view.fitAll()
            logger.debug("Updated view: Top + FitAll for source panels.")
        else:
            logger.warning("Gui.ActiveDocument is None; cannot update view.")
    except Exception as exc:
        logger.warning(f"Failed to update view after CSV import: {exc!r}")

    logger.info(f"Created {len(created)} source panel shapes in document.")
    logger.info(f"Source panel layout: {len(created)} panels, x_span={x_cursor:.1f} mm")
