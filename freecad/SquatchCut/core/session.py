# @codex
# File: freecad/SquatchCut/core/session.py
# Summary: FreeCAD-aware adapter syncing document properties into session_state.
# Details:
#   - Ensures sheet size, kerf/gap, and default rotation flags mirror doc properties.
#   - Provides helpers to sync state to/from the active FreeCAD document.
from __future__ import annotations

from collections.abc import Mapping

from SquatchCut.freecad_integration import App, Gui  # noqa: F401
from SquatchCut.core import session_state
from SquatchCut.core import sheet_presets
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core.sheet_model import clear_sheet_boundaries

SHEET_OBJECT_NAME = "SquatchCut_Sheet"
SOURCE_GROUP_NAME = "SquatchCut_SourceParts"
NESTED_GROUP_NAME = "SquatchCut_NestedParts"
SOURCE_PREFIX = "SC_Source_"
NESTED_PREFIX = "SC_Nested_"

# Default measurement if detection fails
DEFAULT_MEASUREMENT_SYSTEM = "metric"

# Additional SquatchCut session-related state
_source_panel_objects = []
_sheet_objects = []
_nested_panel_objects = []
_last_csv_path = None


def _normalize_measurement_value(value):
    """Normalize metadata/unit hints into 'metric' or 'imperial'."""
    if value is None:
        return DEFAULT_MEASUREMENT_SYSTEM
    if isinstance(value, (list, tuple, set)):
        for item in value:
            normalized = _normalize_measurement_value(item)
            if normalized:
                return normalized
        return DEFAULT_MEASUREMENT_SYSTEM
    text = str(value).strip().lower()
    if not text:
        return DEFAULT_MEASUREMENT_SYSTEM
    if any(token in text for token in ("imperial", "inch", "us customary", "in/lb", "ft/in", "ft-in", "us-in")):
        return "imperial"
    if any(token in text for token in ("metric", "millimeter", "mm", "si", "mks")):
        return "metric"
    if text in ("in", "inch", "inches"):
        return "imperial"
    if text in ("mm", "millimeters"):
        return "metric"
    return DEFAULT_MEASUREMENT_SYSTEM


def _extract_units_from_metadata(meta):
    """Inspect metadata containers for unit hints."""
    if meta is None:
        return DEFAULT_MEASUREMENT_SYSTEM
    if isinstance(meta, Mapping):
        items = meta.items()
    elif isinstance(meta, (list, tuple, set)):
        items = meta
    else:
        if isinstance(meta, str):
            return _normalize_measurement_value(meta)
        return DEFAULT_MEASUREMENT_SYSTEM
    value = None
    for entry in items:
        if isinstance(entry, (list, tuple)) and len(entry) == 2:
            key, value = entry
        else:
            continue
        if "unit" not in str(key).lower():
            value = None
            continue
        break
    if value is None:
        return DEFAULT_MEASUREMENT_SYSTEM
    return _normalize_measurement_value(value)


def _resolve_doc(doc):
    """Resolve to an existing FreeCAD document if available."""
    if doc is not None:
        return doc
    if App is None:
        return None
    return App.ActiveDocument


def _safe_remove(doc, name, removed=None):
    if doc is None or not name:
        return False
    try:
        doc.removeObject(name)
        if removed is not None:
            removed.append(name)
        return True
    except Exception:
        return False


def _remove_objects_by_prefix(doc, prefix, removed=None):
    if doc is None:
        return
    for obj in list(getattr(doc, "Objects", []) or []):
        name = getattr(obj, "Name", "") or ""
        if name.startswith(prefix):
            _safe_remove(doc, name, removed)


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


def clear_sheet_object(doc=None):
    resolved = _resolve_doc(doc)
    if resolved is None:
        return 0
    return 1 if _safe_remove(resolved, SHEET_OBJECT_NAME) else 0


def clear_source_group(doc=None):
    resolved = _resolve_doc(doc)
    if resolved is None:
        return []
    removed = []
    group = get_source_group(resolved)
    if group is not None:
        for member in list(getattr(group, "Group", []) or []):
            _safe_remove(resolved, getattr(member, "Name", None), removed)
        _safe_remove(resolved, getattr(group, "Name", None), removed)
    _remove_objects_by_prefix(resolved, SOURCE_PREFIX, removed)
    return removed


def clear_nested_group(doc=None):
    resolved = _resolve_doc(doc)
    if resolved is None:
        return
    group = get_nested_group(resolved)
    removed = []
    if group is not None:
        for member in list(getattr(group, "Group", []) or []):
            _safe_remove(resolved, getattr(member, "Name", None), removed)
        _safe_remove(resolved, getattr(group, "Name", None), removed)
    _remove_objects_by_prefix(resolved, NESTED_PREFIX, removed)
    return removed


def clear_all_squatchcut_geometry(doc=None):
    resolved = _resolve_doc(doc)
    if resolved is None:
        return
    clear_nested_group(resolved)
    clear_source_group(resolved)
    clear_sheet_object(resolved)
    clear_sheet_boundaries(resolved)
    clear_sheets()
    set_source_panel_objects([])
    set_nested_panel_objects([])
    try:
        session_state.set_nested_sheet_group(None)
    except Exception:
        pass


def clear_nested_layout(doc=None):
    """Clear only the nested layout artifacts (sheet outlines and nested group) while keeping source panels."""
    resolved = _resolve_doc(doc)
    if resolved is None:
        return
    clear_nested_group(resolved)
    clear_sheet_object(resolved)
    clear_sheet_boundaries(resolved)
    set_nested_panel_objects([])
    set_sheet_objects([])
    try:
        session_state.set_nested_sheet_group(None)
    except Exception:
        pass


def detect_document_measurement_system(doc) -> str | None:
    """Best-effort detection of a FreeCAD document's measurement system."""
    if doc is None:
        prefs = SquatchCutPreferences()
        return prefs.get_measurement_system() or DEFAULT_MEASUREMENT_SYSTEM

    for attr_name in ("Metadata", "Meta", "DocumentMetadata"):
        meta = getattr(doc, attr_name, None)
        normalized = _extract_units_from_metadata(meta)
        if normalized:
            return normalized

    getter = getattr(doc, "getMetadata", None)
    if callable(getter):
        for key in ("UnitSystem", "UnitSchema", "Units", "MeasurementSystem"):
            try:
                normalized = _normalize_measurement_value(getter(key))
            except Exception:
                normalized = None
            if normalized:
                return normalized

    attr_candidates = [
        getattr(doc, "SquatchCutSheetUnits", None),
        getattr(doc, "UnitSystem", None),
        getattr(doc, "unit_system", None),
    ]
    for candidate in attr_candidates:
        normalized = _normalize_measurement_value(candidate)
        if normalized:
            return normalized

    prefs = SquatchCutPreferences()
    return prefs.get_measurement_system() or DEFAULT_MEASUREMENT_SYSTEM


def update_sheet_size_from_doc(doc):
    """Read sheet size from document properties into session_state."""
    try:
        w = float(getattr(doc, "SquatchCutSheetWidth"))
        h = float(getattr(doc, "SquatchCutSheetHeight"))
        session_state.set_sheet_size(w, h)
    except Exception:
        pass


def update_kerf_gap_from_doc(doc):
    """Read kerf/gap from document properties into session_state."""
    try:
        session_state.set_kerf_mm(float(getattr(doc, "SquatchCutKerfMM")))
    except Exception:
        pass
    try:
        session_state.set_gap_mm(float(getattr(doc, "SquatchCutGapMM")))
    except Exception:
        pass
    try:
        session_state.set_default_allow_rotate(bool(getattr(doc, "SquatchCutDefaultAllowRotate")))
    except Exception:
        pass


def push_last_layout_to_state(layout):
    """Push last layout into session_state."""
    session_state.set_last_layout(layout)


def set_sheet_properties(doc, width, height, units="mm"):
    """Helper to set sheet size on doc and mirror into session_state."""
    try:
        doc.SquatchCutSheetWidth = float(width)
        doc.SquatchCutSheetHeight = float(height)
        session_state.set_sheet_size(float(width), float(height))
    except Exception:
        pass
    try:
        doc.SquatchCutSheetUnits = units or "mm"
    except Exception:
        pass
    # Also mirror current kerf/gap/default rotate into doc
    try:
        doc.SquatchCutKerfMM = float(session_state.get_kerf_mm())
    except Exception:
        pass
    try:
        doc.SquatchCutGapMM = float(session_state.get_gap_mm())
    except Exception:
        pass
    try:
        doc.SquatchCutDefaultAllowRotate = bool(session_state.get_default_allow_rotate())
    except Exception:
        pass


def ensure_doc_settings(
    doc,
    measurement_system: str | None = None,
    default_sheet_mm: tuple[float | None, float | None] | None = None,
):
    """
    Ensure the active document has the SquatchCut settings properties.
    """
    normalized_system = measurement_system if measurement_system in ("metric", "imperial") else None
    if normalized_system is None:
        normalized_system = detect_document_measurement_system(doc) or "metric"
    fallback_width, fallback_height = sheet_presets.get_factory_default_sheet_size(normalized_system)
    if default_sheet_mm:
        default_width = float(default_sheet_mm[0]) if default_sheet_mm[0] is not None else fallback_width
        default_height = float(default_sheet_mm[1]) if default_sheet_mm[1] is not None else fallback_height
    else:
        default_width, default_height = fallback_width, fallback_height

    if not hasattr(doc, "SquatchCutSheetWidth"):
        try:
            doc.addProperty(
                "App::PropertyFloat",
                "SquatchCutSheetWidth",
                "SquatchCut",
                "Sheet width (mm)",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutSheetWidth = float(default_width)
        except Exception:
            pass
    if not hasattr(doc, "SquatchCutSheetHeight"):
        try:
            doc.addProperty(
                "App::PropertyFloat",
                "SquatchCutSheetHeight",
                "SquatchCut",
                "Sheet height (mm)",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutSheetHeight = float(default_height)
        except Exception:
            pass

    if not hasattr(doc, "SquatchCutKerfMM"):
        try:
            doc.addProperty(
                "App::PropertyFloat",
                "SquatchCutKerfMM",
                "SquatchCut",
                "Kerf spacing between adjacent parts (mm)",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutKerfMM = 3.0
        except Exception:
            pass
    if not hasattr(doc, "SquatchCutGapMM"):
        try:
            doc.addProperty(
                "App::PropertyFloat",
                "SquatchCutGapMM",
                "SquatchCut",
                "Gap/halo spacing around parts (mm)",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutGapMM = 0.0
        except Exception:
            pass

    if not hasattr(doc, "SquatchCutDefaultAllowRotate"):
        try:
            doc.addProperty(
                "App::PropertyBool",
                "SquatchCutDefaultAllowRotate",
                "SquatchCut",
                "Allow rotation by default when CSV does not specify allow_rotate.",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutDefaultAllowRotate = False
        except Exception:
            pass

    if not hasattr(doc, "SquatchCutSheetUnits"):
        try:
            doc.addProperty(
                "App::PropertyString",
                "SquatchCutSheetUnits",
                "SquatchCut",
                "Measurement system used for SquatchCut sheet defaults.",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutSheetUnits = "in" if normalized_system == "imperial" else "mm"
        except Exception:
            pass


def sync_state_from_doc(
    doc,
    measurement_system: str | None = None,
    default_sheet_mm: tuple[float | None, float | None] | None = None,
):
    """
    Read settings from the FreeCAD document and push them into session_state.
    """
    ensure_doc_settings(doc, measurement_system, default_sheet_mm)

    session_state.set_sheet_size(
        float(doc.SquatchCutSheetWidth),
        float(doc.SquatchCutSheetHeight),
    )
    session_state.set_kerf_mm(float(doc.SquatchCutKerfMM))
    session_state.set_gap_mm(float(doc.SquatchCutGapMM))

    default_allow = bool(doc.SquatchCutDefaultAllowRotate)
    session_state.set_default_allow_rotate(default_allow)

    doc_units = getattr(doc, "SquatchCutSheetUnits", None)
    normalized = _normalize_measurement_value(doc_units)
    if normalized in ("metric", "imperial"):
        session_state.set_measurement_system(normalized)


def sync_doc_from_state(doc, measurement_system: str | None = None):
    """
    Write current session_state values back into the document properties.
    Useful if state was changed directly.
    """
    normalized_system = measurement_system if measurement_system in ("metric", "imperial") else session_state.get_measurement_system()
    ensure_doc_settings(doc, normalized_system)

    w, h = session_state.get_sheet_size()
    if w is not None:
        doc.SquatchCutSheetWidth = float(w)
    if h is not None:
        doc.SquatchCutSheetHeight = float(h)

    doc.SquatchCutKerfMM = float(session_state.get_kerf_mm())
    doc.SquatchCutGapMM = float(session_state.get_gap_mm())
    doc.SquatchCutDefaultAllowRotate = bool(session_state.get_default_allow_rotate())
    try:
        doc.SquatchCutSheetUnits = "in" if normalized_system == "imperial" else "mm"
    except Exception:
        pass


# Convenience wrappers to mirror session_state panel storage -------------------

def get_panels():
    return session_state.get_panels()


def set_panels(panels):
    session_state.set_panels(panels)


def get_job_sheets():
    return session_state.get_job_sheets()


def set_job_sheets(sheets):
    session_state.set_job_sheets(sheets)


# Source panel objects ---------------------------------------------------------

def get_source_panel_objects():
    return _source_panel_objects


def set_source_panel_objects(objs):
    global _source_panel_objects
    _source_panel_objects = list(objs) if objs is not None else []


def clear_source_panel_objects():
    global _source_panel_objects
    _source_panel_objects = []


# Sheet and nested objects -----------------------------------------------------

def get_sheet_objects():
    return _sheet_objects


def set_sheet_objects(objs):
    global _sheet_objects
    _sheet_objects = list(objs) if objs is not None else []


def get_nested_panel_objects():
    return _nested_panel_objects


def set_nested_panel_objects(objs):
    global _nested_panel_objects
    _nested_panel_objects = list(objs) if objs is not None else []


def clear_sheets():
    global _sheet_objects, _nested_panel_objects
    _sheet_objects = []
    _nested_panel_objects = []


# CSV path tracking ------------------------------------------------------------

def get_last_csv_path():
    return _last_csv_path


def set_last_csv_path(path):
    global _last_csv_path
    _last_csv_path = path


# General clear ---------------------------------------------------------------

def clear_all_geometry():
    clear_source_panel_objects()
    clear_sheets()
