"""Centralized view control helpers for SquatchCut FreeCAD views."""

from __future__ import annotations

from typing import Iterable, List

from SquatchCut.freecad_integration import App, Gui

from SquatchCut.core import logger, session, session_state
from SquatchCut.core.nesting import derive_sheet_sizes_for_layout
from SquatchCut.core.sheet_model import (
    SHEET_OBJECT_NAME,
    ensure_sheet_object,
    get_or_create_group,
    clear_group_children,
    compute_sheet_spacing,
)
from SquatchCut.gui.nesting_view import rebuild_nested_geometry
from SquatchCut.gui.source_view import rebuild_source_preview
from SquatchCut.gui.view_utils import zoom_to_objects

SOURCE_GROUP_NAME = "SquatchCut_SourceParts"
NESTED_GROUP_NAME = "SquatchCut_NestedParts"
LEGACY_SHEET_GROUP_NAME = "SquatchCut_Sheets"
SQUATCHCUT_GROUP_NAMES = (SHEET_OBJECT_NAME, SOURCE_GROUP_NAME, NESTED_GROUP_NAME)


def _resolve_doc(doc=None):
    if doc is not None:
        return doc
    if App is None:
        return None
    doc = App.ActiveDocument
    if doc is None:
        try:
            doc = App.newDocument("SquatchCut")
        except Exception:
            return None
    try:
        if Gui:
            Gui.ActiveDocument = Gui.getDocument(doc.Name)
    except Exception:
        pass
    return doc


def _resolve_view():
    if Gui is None:
        return None
    try:
        gui_doc = Gui.ActiveDocument
        if gui_doc is None:
            return None
        return gui_doc.ActiveView
    except Exception:
        return None


def _collect_group_objects(group):
    if group is None:
        return []
    try:
        iterable = getattr(group, "Group", [])
    except ReferenceError:
        return []
    return [obj for obj in iterable if obj is not None]


def _unique_objects(objs: Iterable[object]) -> List[object]:
    seen = set()
    unique = []
    for obj in objs:
        if obj is None:
            continue
        try:
            name = getattr(obj, "Name", None)
        except ReferenceError:
            continue
        key = (name, obj)
        if key in seen:
            continue
        seen.add(key)
        unique.append(obj)
    return unique


def _set_object_visibility(obj, visible: bool) -> None:
    if obj is None:
        return
    view = getattr(obj, "ViewObject", None)
    if view is None:
        return
    try:
        view.Visibility = bool(visible)
    except Exception:
        pass


def set_squatchcut_group_visibility(doc, active_group_name: str) -> None:
    if doc is None:
        return
    for name in SQUATCHCUT_GROUP_NAMES:
        obj = doc.getObject(name)
        is_active = name == active_group_name
        _set_object_visibility(obj, is_active)
        if obj is None or name == SHEET_OBJECT_NAME:
            continue
        for child in list(getattr(obj, "Group", []) or []):
            _set_object_visibility(child, is_active)


def auto_zoom_to_group(view, group):
    if group is None:
        return
    members = [obj for obj in _collect_group_objects(group) if obj is not None]
    targets = list(members)
    if not targets and hasattr(group, "Shape"):
        targets.append(group)
    if not targets:
        return
    if view is not None:
        try:
            view.viewTop()
        except Exception:
            pass
        try:
            view.setCameraType("Orthographic")
        except Exception:
            pass
    fit_view_to_objects(targets)


def _redraw_sheet_object(doc):
    if doc is None:
        return None
    sheet_w, sheet_h = session_state.get_sheet_size()
    if not sheet_w or not sheet_h:
        return doc.getObject(SHEET_OBJECT_NAME)
    sheet_obj = ensure_sheet_object(sheet_w, sheet_h, doc)
    session.set_sheet_objects([sheet_obj] if sheet_obj else [])
    return sheet_obj


def _redraw_source_group(doc):
    if doc is None:
        return None, []
    parts = session.get_panels() or session_state.get_panels() or []
    group = get_or_create_group(doc, SOURCE_GROUP_NAME)
    if not parts:
        clear_group_children(group)
        session.set_source_panel_objects([])
        try:
            session_state.set_source_panel_objects([])
        except Exception:
            pass
        return group, []
    group, created = rebuild_source_preview(parts, doc=doc)
    session.set_source_panel_objects(created)
    try:
        session_state.set_source_panel_objects(created)
    except Exception:
        pass
    return group, created


def _redraw_nested_group(doc):
    if doc is None:
        return None, []
    placements = session_state.get_last_layout() or []
    group = get_or_create_group(doc, NESTED_GROUP_NAME)
    if not placements:
        clear_group_children(group)
        session.set_nested_panel_objects([])
        try:
            session_state.set_nested_sheet_group(group)
        except Exception:
            pass
        return group, []
    sheet_w, sheet_h = session_state.get_sheet_size()
    if not sheet_w or not sheet_h:
        clear_group_children(group)
        session.set_nested_panel_objects([])
        try:
            session_state.set_nested_sheet_group(group)
        except Exception:
            pass
        return group, []
    sheet_defs = session_state.get_job_sheets() or []
    sheet_mode = session_state.get_sheet_mode()
    sheet_sizes = derive_sheet_sizes_for_layout(
        sheet_mode,
        sheet_defs,
        sheet_w,
        sheet_h,
        placements,
    )
    if not sheet_sizes and sheet_w and sheet_h:
        sheet_sizes = [(sheet_w, sheet_h)]
    sheet_spacing = compute_sheet_spacing(sheet_sizes, session_state.get_gap_mm())
    source_objs = session.get_source_panel_objects()
    group, nested_objs = rebuild_nested_geometry(
        doc,
        placements,
        sheet_sizes=sheet_sizes,
        spacing=sheet_spacing,
        source_objects=source_objs,
    )
    session.set_nested_panel_objects(nested_objs or [])
    try:
        session_state.set_nested_sheet_group(group)
    except Exception:
        pass
    return group, nested_objs or []


def fit_view_to_objects(objects: Iterable[object]) -> None:
    targets = _unique_objects(objects or [])
    if not targets:
        logger.debug("fit_view_to_objects() skipped: no targets to fit.")
        return
    try:
        zoom_to_objects(targets)
    except Exception as exc:
        logger.warning(f"fit_view_to_objects() failed: {exc!r}")


def cleanup_nested_layout(doc=None) -> None:
    resolved_doc = _resolve_doc(doc)
    if resolved_doc is None:
        return

    removed = []
    legacy = resolved_doc.getObject(LEGACY_SHEET_GROUP_NAME)
    if legacy is not None:
        for child in list(getattr(legacy, "Group", [])):
            _safe_remove(resolved_doc, getattr(child, "Name", None), removed)
        _safe_remove(resolved_doc, getattr(legacy, "Name", None), removed)

    nested_removed = session.clear_nested_group(resolved_doc) or []
    removed.extend(nested_removed)

    session.clear_sheets()
    try:
        session_state.set_nested_sheet_group(None)
    except Exception:
        pass

    if removed:
        logger.info(f">>> [SquatchCut] Removed {len(removed)} stale nested object(s).")


def _safe_remove(doc, name, removed):
    if doc is None or not name:
        return
    try:
        doc.removeObject(name)
        removed.append(name)
    except Exception:
        pass


def show_source_view(doc=None) -> None:
    resolved_doc = _resolve_doc(doc)
    if resolved_doc is None:
        return

    group, created = _redraw_source_group(resolved_doc)
    set_squatchcut_group_visibility(resolved_doc, SOURCE_GROUP_NAME)
    count = len(created or getattr(group, "Group", []))
    logger.info(f">>> [SquatchCut] View: showing source geometry only ({count} objects).")
    view = _resolve_view()
    auto_zoom_to_group(view, group)


def show_sheet_view(doc=None) -> None:
    resolved_doc = _resolve_doc(doc)
    if resolved_doc is None:
        return

    sheet_obj = _redraw_sheet_object(resolved_doc)
    set_squatchcut_group_visibility(resolved_doc, SHEET_OBJECT_NAME)
    logger.info(">>> [SquatchCut] View: showing sheet only.")
    view = _resolve_view()
    auto_zoom_to_group(view, sheet_obj)


def show_nesting_view(
    doc=None,
    active_sheet=None,
    nested_objects=None,
) -> None:
    resolved_doc = _resolve_doc(doc)
    if resolved_doc is None:
        return

    group, nested_objs = _redraw_nested_group(resolved_doc)
    set_squatchcut_group_visibility(resolved_doc, NESTED_GROUP_NAME)
    count = len(nested_objs or getattr(group, "Group", []))
    logger.info(f">>> [SquatchCut] View: showing nested layout only ({count} objects).")
    view = _resolve_view()
    auto_zoom_to_group(view, group)
