"""Helpers to synchronize SquatchCut panels into FreeCAD document geometry."""

from __future__ import annotations

try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
except Exception:  # pragma: no cover
    App = None
    Gui = None

from SquatchCut.core import logger, session, session_state
from SquatchCut.core.sheet_model import ensure_sheet_object
from SquatchCut.gui.source_view import rebuild_source_preview, SOURCE_GROUP_NAME
from SquatchCut.gui.view_utils import zoom_to_objects


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

    logger.info(">>> [SquatchCut] Rebuilding source preview...")
    group, created = rebuild_source_preview(panels)
    logger.info(f">>> [SquatchCut] Created {len(created)} preview objects")
    session.set_source_panel_objects(created)
    try:
        session_state.set_source_panel_objects(created)
    except Exception:
        pass
    try:
        doc.recompute()
    except Exception:
        pass

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
    try:
        targets = []
        if sheet_obj:
            targets.append(sheet_obj)
        targets.extend(created or [])
        if targets:
            zoom_to_objects(targets)
    except Exception:
        pass
