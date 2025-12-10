"""Helpers to synchronize SquatchCut panels into FreeCAD document geometry."""

from __future__ import annotations

from SquatchCut.core import logger, session, session_state, view_controller
from SquatchCut.core.sheet_model import ensure_sheet_object
from SquatchCut.freecad_integration import App, Gui


def sync_source_panels_to_document():
    """Create/refresh source panel geometry in the active document and update the view."""
    if App is None:
        logger.warning("sync_source_panels_to_document() skipped: FreeCAD not available.")
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

    sheet_w, sheet_h = session_state.get_sheet_size()
    sheet_obj = ensure_sheet_object(sheet_w, sheet_h, doc)

    logger.info(">>> [SquatchCut] Rebuilding source preview via view controller...")

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
        view_controller.show_source_view(doc)
    except ReferenceError:

        logger.error("ReferenceError during show_source_view()", exc_info=True)
        raise
