"""Lightweight FreeCAD helpers to keep SquatchCut objects visible and framed."""

from __future__ import annotations

import logging

try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
except Exception:  # pragma: no cover
    App = None
    Gui = None

from SquatchCut.gui.view_utils import zoom_to_objects

logger = logging.getLogger("SquatchCut.view_helpers")

SHEET_OBJECT_NAME = "SquatchCut_Sheet"
SOURCE_GROUP_NAME = "SquatchCut_SourceParts"
NESTED_GROUP_NAME = "SquatchCut_NestedParts"
SOURCE_PREFIX = "SC_Source_"
NESTED_PREFIX = "SC_Nested_"


def _resolve_doc(doc=None):
    if doc is not None:
        return doc
    if App is None:
        return None
    return App.ActiveDocument


def _collect_group_members(group):
    if group is None:
        return []
    members = getattr(group, "Group", []) or []
    return [obj for obj in members if obj is not None]


def _collect_objects_by_prefix(doc, prefix: str):
    if doc is None:
        return []
    result = []
    for obj in getattr(doc, "Objects", []) or []:
        if obj is None:
            continue
        name = getattr(obj, "Name", "") or ""
        if name.startswith(prefix):
            result.append(obj)
    return result


def _set_visibility(objs, visible: bool) -> None:
    for obj in objs or []:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        try:
            view.Visibility = bool(visible)
        except Exception:
            continue


def get_sheet_object(doc=None):
    resolved = _resolve_doc(doc)
    if resolved is None:
        return None
    return resolved.getObject(SHEET_OBJECT_NAME)


def get_source_group(doc=None):
    resolved = _resolve_doc(doc)
    if resolved is None:
        return None
    return resolved.getObject(SOURCE_GROUP_NAME)


def get_nested_group(doc=None):
    resolved = _resolve_doc(doc)
    if resolved is None:
        return None
    return resolved.getObject(NESTED_GROUP_NAME)


def _hide_source(doc):
    group = get_source_group(doc)
    _set_visibility([group], False)
    _set_visibility(_collect_group_members(group), False)
    _set_visibility(_collect_objects_by_prefix(doc, SOURCE_PREFIX), False)


def _show_source(doc):
    group = get_source_group(doc)
    _set_visibility([group], True)
    _set_visibility(_collect_group_members(group), True)
    _set_visibility(_collect_objects_by_prefix(doc, SOURCE_PREFIX), True)


def _hide_nested(doc):
    group = get_nested_group(doc)
    _set_visibility([group], False)
    _set_visibility(_collect_group_members(group), False)
    _set_visibility(_collect_objects_by_prefix(doc, NESTED_PREFIX), False)


def _show_nested(doc):
    group = get_nested_group(doc)
    _set_visibility([group], True)
    _set_visibility(_collect_group_members(group), True)
    _set_visibility(_collect_objects_by_prefix(doc, NESTED_PREFIX), True)


def _ensure_sheet_visible(doc):
    sheet = get_sheet_object(doc)
    if sheet is not None:
        _set_visibility([sheet], True)
    return sheet


def _hide_sheet(doc):
    sheet = get_sheet_object(doc)
    if sheet is not None:
        _set_visibility([sheet], False)


def show_sheet_only(doc=None) -> None:
    resolved = _resolve_doc(doc)
    if resolved is None:
        return
    _ensure_sheet_visible(resolved)
    _hide_source(resolved)
    _hide_nested(resolved)
    logger.info("[SquatchCut] View: sheet only.")


def show_source_only(doc=None) -> None:
    resolved = _resolve_doc(doc)
    if resolved is None:
        return
    _hide_sheet(resolved)
    _show_source(resolved)
    _hide_nested(resolved)
    logger.info("[SquatchCut] View: source only.")


def show_source_and_sheet(doc=None) -> None:
    resolved = _resolve_doc(doc)
    if resolved is None:
        return
    _ensure_sheet_visible(resolved)
    _show_source(resolved)
    _hide_nested(resolved)
    logger.info("[SquatchCut] View: source + sheet.")


def show_nested_only(doc=None) -> None:
    resolved = _resolve_doc(doc)
    if resolved is None:
        return
    _ensure_sheet_visible(resolved)
    _show_nested(resolved)
    _hide_source(resolved)
    logger.info("[SquatchCut] View: nested only.")


def show_only_sheet_and_nested(doc=None) -> None:
    resolved = _resolve_doc(doc)
    if resolved is None:
        return
    _ensure_sheet_visible(resolved)
    _show_nested(resolved)
    _hide_source(resolved)
    logger.info("[SquatchCut] View helper: focusing sheet and nested parts.")


def fit_view_to_sheet_and_nested(doc=None) -> None:
    resolved = _resolve_doc(doc)
    if resolved is None:
        return
    targets = []
    sheet = get_sheet_object(resolved)
    if sheet is not None:
        targets.append(sheet)
    nested_group = get_nested_group(resolved)
    if nested_group is not None:
        targets.extend(_collect_group_members(nested_group))
    if not targets:
        logger.debug("[SquatchCut] fit_view_to_sheet_and_nested(): nothing to fit.")
        return
    zoom_to_objects(targets)


def fit_view_to_source(doc=None) -> None:
    resolved = _resolve_doc(doc)
    if resolved is None:
        return
    targets = []
    source_group = get_source_group(resolved)
    if source_group is not None:
        targets.extend(_collect_group_members(source_group))
    targets.extend(_collect_objects_by_prefix(resolved, SOURCE_PREFIX))
    if not targets:
        logger.debug("[SquatchCut] fit_view_to_source(): nothing to fit.")
        return
    zoom_to_objects(targets)
