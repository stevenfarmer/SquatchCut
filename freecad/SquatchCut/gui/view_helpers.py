"""Lightweight FreeCAD helpers to keep SquatchCut objects visible and framed."""

from __future__ import annotations

from typing import Iterable, List, Optional
import logging

try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
except Exception:  # pragma: no cover
    App = None
    Gui = None

logger = logging.getLogger("SquatchCut.view_helpers")
from SquatchCut.gui.view_utils import zoom_to_objects

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


def _collect_group_members(group) -> List[App.DocumentObject if App else object]:
    if group is None:
        return []
    members = getattr(group, "Group", []) or []
    return [obj for obj in members if obj is not None]


def _collect_objects_by_prefix(doc, prefix: str) -> List[App.DocumentObject if App else object]:
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


def _set_visibility(objs: Iterable[object], visible: bool) -> None:
    for obj in objs or []:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            continue
        try:
            view.Visibility = bool(visible)
        except Exception:
            continue


def get_sheet_object(doc=None):
    """Return the sheet object if it exists in the document."""
    resolved = _resolve_doc(doc)
    if resolved is None:
        return None
    return resolved.getObject(SHEET_OBJECT_NAME)


def get_source_group(doc=None):
    """Return the source parts group if present."""
    resolved = _resolve_doc(doc)
    if resolved is None:
        return None
    return resolved.getObject(SOURCE_GROUP_NAME)


def get_nested_group(doc=None):
    """Return the nested parts group if present."""
    resolved = _resolve_doc(doc)
    if resolved is None:
        return None
    return resolved.getObject(NESTED_GROUP_NAME)


def show_only_sheet_and_nested(doc=None) -> None:
    """
    Show only the sheet object and nested parts while hiding source parts.
    """
    resolved = _resolve_doc(doc)
    if resolved is None:
        return

    sheet = get_sheet_object(resolved)
    nested_group = get_nested_group(resolved)
    source_group = get_source_group(resolved)

    if source_group is not None:
        _set_visibility([source_group], False)
        _set_visibility(_collect_group_members(source_group), False)
    _set_visibility(_collect_objects_by_prefix(resolved, SOURCE_PREFIX), False)

    if sheet is not None:
        _set_visibility([sheet], True)
    if nested_group is not None:
        nested_members = _collect_group_members(nested_group)
        _set_visibility([nested_group], True)
        _set_visibility(nested_members, True)
    _set_visibility(_collect_objects_by_prefix(resolved, NESTED_PREFIX), True)

    logger.info("[SquatchCut] View helper: focusing sheet and nested parts.")


def fit_view_to_sheet(doc=None) -> None:
    """Frame the current view around the sheet object, if available."""
    resolved = _resolve_doc(doc)
    if resolved is None:
        return

    sheet = get_sheet_object(resolved)
    if sheet is None:
        logger.debug("[SquatchCut] fit_view_to_sheet() skipped: no sheet object.")
        return

    if Gui is not None:
        try:
            gui_doc = Gui.getDocument(resolved.Name)
            if gui_doc is not None:
                Gui.ActiveDocument = gui_doc
        except Exception:
            pass

    zoom_to_objects([sheet])
