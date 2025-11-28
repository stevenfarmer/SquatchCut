"""Small FreeCAD GUI helpers for view control."""

from __future__ import annotations

try:
    import FreeCADGui as Gui  # type: ignore
except Exception:  # pragma: no cover
    Gui = None

from SquatchCut.core import logger


def zoom_to_objects(objects):
    """
    Center and zoom the active view to fit the given objects.

    Uses Gui.Selection to temporarily select objects, calls fitAll(),
    and clears the selection afterwards.
    """
    if Gui is None:
        logger.warning("zoom_to_objects() skipped: FreeCADGui unavailable.")
        return

    try:
        doc = Gui.ActiveDocument
        view = doc.ActiveView if doc else None
    except Exception:
        view = None

    if view is None:
        logger.warning("zoom_to_objects() skipped: no active view.")
        return

    sel = Gui.Selection
    try:
        sel.clearSelection()
        for obj in objects or []:
            if obj is None:
                continue
            try:
                sel.addSelection(obj)
            except Exception:
                continue
        try:
            view.viewTop()
        except Exception:
            pass
        try:
            view.setCameraType("Orthographic")
        except Exception:
            pass
        view.fitAll()
        logger.debug(f"zoom_to_objects() fit {len(objects or [])} object(s).")
    except Exception as exc:
        logger.warning(f"zoom_to_objects() failed: {exc!r}")
    finally:
        try:
            sel.clearSelection()
        except Exception:
            pass
