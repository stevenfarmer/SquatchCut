"""Centralized view control helpers for SquatchCut FreeCAD views."""

from __future__ import annotations

from typing import Iterable, List

try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
except Exception:  # pragma: no cover
    App = None
    Gui = None

from SquatchCut.core import logger, session, session_state
from SquatchCut.core.sheet_model import SHEET_OBJECT_NAME
from SquatchCut.gui.view_utils import zoom_to_objects

SOURCE_GROUP_NAME = "SquatchCut_SourceParts"
NESTED_GROUP_NAME = "SquatchCut_NestedParts"
LEGACY_SHEET_GROUP_NAME = "SquatchCut_Sheets"


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


def get_source_objects(doc=None) -> list[object]:
    objs = list(session.get_source_panel_objects() or [])
    resolved_doc = _resolve_doc(doc)
    if resolved_doc is not None:
        group = resolved_doc.getObject(SOURCE_GROUP_NAME)
        objs.extend(_collect_group_objects(group))
    return _unique_objects(objs)


def get_sheet_objects(doc=None) -> list[object]:
    objs = list(session.get_sheet_objects() or [])
    resolved_doc = _resolve_doc(doc)
    if resolved_doc is not None:
        sheet_shape = resolved_doc.getObject(SHEET_OBJECT_NAME)
        if sheet_shape is not None:
            objs.append(sheet_shape)
    return _unique_objects(objs)


def get_nested_objects(doc=None) -> list[object]:
    objs = list(session.get_nested_panel_objects() or [])
    nested_group = session_state.get_nested_sheet_group()
    objs.extend(_collect_group_objects(nested_group))
    resolved_doc = _resolve_doc(doc)
    if resolved_doc is not None:
        group = resolved_doc.getObject(NESTED_GROUP_NAME)
        objs.extend(_collect_group_objects(group))
    return _unique_objects(objs)


def set_visibility(objs: Iterable[object], visible: bool) -> None:
    for obj in objs or []:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        try:
            view.Visibility = bool(visible)
        except Exception:
            continue


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

    nested_group = resolved_doc.getObject(NESTED_GROUP_NAME)
    if nested_group is not None:
        for child in list(getattr(nested_group, "Group", [])):
            _safe_remove(resolved_doc, getattr(child, "Name", None), removed)
        _safe_remove(resolved_doc, getattr(nested_group, "Name", None), removed)

    for obj in list(getattr(resolved_doc, "Objects", [])):
        name = getattr(obj, "Name", "")
        if name.startswith("SC_Nested_"):
            _safe_remove(resolved_doc, name, removed)

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

    sources = get_source_objects(resolved_doc)
    set_visibility(sources, True)
    set_visibility(get_sheet_objects(resolved_doc), False)
    set_visibility(get_nested_objects(resolved_doc), False)
    logger.info(">>> [SquatchCut] View: showing source geometry only")
    fit_view_to_objects(sources)


def show_nesting_view(
    doc=None,
    active_sheet=None,
    nested_objects=None,
) -> None:
    resolved_doc = _resolve_doc(doc)
    if resolved_doc is None:
        return

    source_objs = get_source_objects(resolved_doc)
    sheet_objs = get_sheet_objects(resolved_doc)
    nested_objs = nested_objects or get_nested_objects(resolved_doc)

    set_visibility(source_objs, False)
    set_visibility(sheet_objs, False)

    visible_sheet = active_sheet or (sheet_objs[0] if sheet_objs else None)
    if visible_sheet is not None:
        set_visibility([visible_sheet], True)
    elif sheet_objs:
        set_visibility(sheet_objs, True)

    set_visibility(nested_objs, True)

    targets = []
    if visible_sheet is not None:
        targets.append(visible_sheet)
    else:
        targets.extend(sheet_objs)
    targets.extend(nested_objs)

    sheet_label = getattr(visible_sheet, "Name", "unknown sheet")
    logger.info(f">>> [SquatchCut] View: showing nested layout on active sheet {sheet_label}")
    if targets:
        fit_view_to_objects(targets)
