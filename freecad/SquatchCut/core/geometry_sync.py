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

from SquatchCut.core import session_state


def sync_source_panels_to_document():
    """Create/refresh source panel geometry in the active document."""
    if App is None or Part is None:
        return

    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument("SquatchCut")
        try:
            if Gui:
                Gui.ActiveDocument = doc
        except Exception:
            pass

    panels = session_state.get_panels()
    if not panels:
        return

    group = doc.getObject("SquatchCut_SourcePanels")
    if group is None:
        group = doc.addObject("App::DocumentObjectGroup", "SquatchCut_SourcePanels")

    # Clear existing group children
    for obj in list(group.Group):
        try:
            doc.removeObject(obj.Name)
        except Exception:
            continue

    created = []
    x_cursor = 0.0
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

        obj = doc.addObject("Part::Feature", f"SC_Source_{name}")
        shape = Part.makePlane(w, h, App.Vector(x_cursor, 0, 0), App.Vector(1, 0, 0), App.Vector(0, 1, 0))
        obj.Shape = shape
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
        group.addObject(obj)
        created.append(obj)

        x_cursor += w + spacing

    session_state.set_source_panel_objects(created)

    if doc is not None:
        doc.recompute()

    # Fit view top-down
    if Gui and Gui.ActiveDocument:
        try:
            view = Gui.ActiveDocument.ActiveView
            view.viewTop()
            view.fitAll()
        except Exception:
            pass

    App.Console.PrintMessage(f"[SquatchCut] Created {len(created)} source panel shapes in document.\n")
