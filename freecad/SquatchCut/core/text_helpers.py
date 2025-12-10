"""Centralized helpers for creating FreeCAD text/label geometry."""

from __future__ import annotations

import os

from SquatchCut.core import logger
from SquatchCut.freecad_integration import App, Draft

_FONT_WARNING_EMITTED = False

def _activate_document(doc) -> bool:
    if App is None or doc is None:
        return False
    try:
        if getattr(App, "ActiveDocument", None) is not doc:
            App.ActiveDocument = doc
        return True
    except Exception:
        return False


def _vector(x: float, y: float, z: float = 0.0):
    if App is None:
        return None
    try:
        return App.Vector(float(x), float(y), float(z))
    except Exception:
        return None


def _placement(vec):
    if App is None or vec is None:
        return None
    try:
        return App.Placement(vec, App.Rotation())
    except Exception:
        return None


def create_screen_text(doc, label: str, x: float, y: float, z: float = 0.0):
    """Create a Draft text object for on-screen use, returning None on failure."""
    if Draft is None or App is None or doc is None:
        return None
    if not _activate_document(doc):
        return None
    placement = _placement(_vector(x, y, z))
    if placement is None:
        logger.warning(f"[SquatchCut] Screen text creation failed: invalid placement for '{label}'")
        return None
    strings = [str(label)]
    maker = getattr(Draft, "make_text", None)
    text_obj = None
    if callable(maker):
        try:
            text_obj = maker(strings, placement=placement)
        except Exception:
            text_obj = None
    if text_obj is None:
        legacy = getattr(Draft, "makeText", None)
        if callable(legacy):
            try:
                text_obj = legacy(strings, point=_vector(x, y, z))
            except Exception:
                text_obj = None
    if text_obj is None:
        logger.warning(f"[SquatchCut] Screen text creation failed for '{label}'")
    return text_obj


def _resolve_shape_font_file() -> str | None:
    if App is None:
        return ""
    font_candidates = []
    try:
        params = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft")
        for key in ("ShapeFontFile", "FontFile"):
            value = params.GetString(key, "")
            if value:
                font_candidates.append(value)
    except Exception:
        pass
    for candidate in font_candidates:
        if os.path.exists(candidate):
            return candidate
    try:
        resource_dir = App.getResourceDir()
    except Exception:
        resource_dir = ""
    if resource_dir:
        default_font = os.path.join(resource_dir, "Mod", "Draft", "Resources", "Fonts", "default.svg")
        if os.path.exists(default_font):
            return default_font
    return ""


def create_export_shape_text(
    doc,
    label: str,
    x: float,
    y: float,
    z: float = 0.0,
    size: float | None = None,
    tracking: float = 0.0,
):
    """Create a geometry-based ShapeString for export; return None on failure."""
    if Draft is None or App is None or doc is None:
        return None
    if not _activate_document(doc):
        return None
    font_file = _resolve_shape_font_file()
    global _FONT_WARNING_EMITTED
    if not font_file and not _FONT_WARNING_EMITTED:
        logger.warning("[SquatchCut] No Draft font configured; using FreeCAD default font for SVG text.")
        _FONT_WARNING_EMITTED = True
    size_mm = float(size) if size is not None and size > 0 else 10.0
    try:
        shape_obj = Draft.makeShapeString(
            String=str(label),
            FontFile=font_file or "",
            Size=size_mm,
            Tracking=float(tracking),
        )
    except Exception as exc:
        logger.warning(f"[SquatchCut] Export text creation failed for '{label}': {exc}")
        return None
    placement = _placement(_vector(x, y, z))
    if placement is not None:
        try:
            shape_obj.Placement = placement
        except Exception:
            pass
    return shape_obj
