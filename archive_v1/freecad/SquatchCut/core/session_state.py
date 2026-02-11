"""
Pure Python in-memory session state for SquatchCut.

This module intentionally does NOT import FreeCAD so that:
- Unit tests can import it without requiring FreeCAD to be installed.
- Integration with FreeCAD happens inside session.py instead.
"""

from copy import deepcopy
from typing import Any, Optional

# @codex
# Pure in-memory session state for SquatchCut (no FreeCAD deps).
# Tracks sheet size, kerf/gap, default rotation flag, last layout, and panel data.

# Sheet size
_sheet_width: Optional[float] = None
_sheet_height: Optional[float] = None
_job_sheets: list[dict[str, Any]] = []

SHEET_MODE_SIMPLE = "simple"
SHEET_MODE_JOB_SHEETS = "job_sheets"
_sheet_mode: str = SHEET_MODE_SIMPLE

# Cutting parameters
_kerf_mm: float = 0.0
_gap_mm: float = 0.0
_default_allow_rotate: bool = False
_job_allow_rotate: Optional[bool] = None
_optimize_for_cut_path: bool = False
_kerf_width_mm: float = 3.0
_allowed_rotations_deg: tuple[int, ...] = (0, 90)
_measurement_system: str = "imperial"

# Last nesting layout: list of PlacedPart objects
_last_layout: Optional[list[Any]] = None
_nesting_stats: dict[str, Any] = {
    "sheets_used": None,
    "cut_complexity": None,
    "overlaps_count": None,
    "per_sheet_stats": [],
}

# Panels loaded from CSV (pure data; no FreeCAD objects)
_panels: list[dict[str, Any]] = []
_shape_panel_objects: dict[str, Any] = {}

# Optimization mode: "material" (default) or "cuts"
_optimization_mode: str = "material"
_nesting_mode: str = "pack"
_export_include_labels: bool = True
_export_include_dimensions: bool = False
_source_panel_objects: list[Any] = []
_nested_sheet_group: Optional[Any] = None


def set_shape_panel_objects(mapping) -> None:
    """Store FreeCAD objects associated with shape-based panels."""
    global _shape_panel_objects
    if mapping is None:
        _shape_panel_objects = {}
        return
    try:
        _shape_panel_objects = dict(mapping)
    except Exception:
        _shape_panel_objects = {}


def get_shape_panel_object(panel_id):
    """Return the FreeCAD object tied to the requested panel id."""
    if not panel_id:
        return None
    return _shape_panel_objects.get(panel_id)


def clear_shape_panel_objects() -> None:
    """Clear shape-driven object registry."""
    global _shape_panel_objects
    _shape_panel_objects = {}


# --------------------------
# Sheet size accessors
# --------------------------


def set_sheet_size(width_mm: float, height_mm: float) -> None:
    """Store sheet size in millimeters in session memory."""
    global _sheet_width, _sheet_height
    _sheet_width = None if width_mm is None else float(width_mm)
    _sheet_height = None if height_mm is None else float(height_mm)


def clear_sheet_size() -> None:
    """Clear sheet size so UIs can show empty defaults when none are stored."""
    global _sheet_width, _sheet_height
    _sheet_width = None
    _sheet_height = None
    clear_job_sheets()


def get_sheet_size():
    """Return current sheet size (width_mm, height_mm) or (None, None)."""
    return _sheet_width, _sheet_height


def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def _safe_int(value):
    try:
        return int(value)
    except Exception:
        return 1


def _normalize_sheet_entry(entry):
    if entry is None:
        entry = {}
    if isinstance(entry, dict):
        width = _safe_float(entry.get("width_mm") or entry.get("width"))
        height = _safe_float(entry.get("height_mm") or entry.get("height"))
        quantity = _safe_int(entry.get("quantity"))
        label = entry.get("label") or entry.get("name")
    else:
        width = _safe_float(getattr(entry, "width_mm", None))
        height = _safe_float(getattr(entry, "height_mm", None))
        quantity = _safe_int(getattr(entry, "quantity", None))
        label = getattr(entry, "label", None) or getattr(entry, "name", None)
    return {
        "width_mm": width,
        "height_mm": height,
        "quantity": max(quantity, 1),
        "label": str(label) if label is not None else None,
    }


def set_job_sheets(sheet_definitions):
    """Replace the current job sheet list with the provided definitions."""
    global _job_sheets
    if sheet_definitions is None:
        _job_sheets = []
        return
    normalized = []
    for entry in sheet_definitions:
        normalized.append(_normalize_sheet_entry(entry))
    _job_sheets = normalized


def get_job_sheets():
    """Return a copy of the current job sheet definitions."""
    return deepcopy(_job_sheets)


def add_job_sheet(
    width_mm: float,
    height_mm: float,
    quantity: int = 1,
    label: Optional[str] = None,
):
    """Append a new sheet definition."""
    global _job_sheets
    entry = _normalize_sheet_entry(
        {
            "width_mm": width_mm,
            "height_mm": height_mm,
            "quantity": quantity,
            "label": label,
        }
    )
    _job_sheets.append(entry)
    return entry


def remove_job_sheet(index: int) -> bool:
    """Remove a sheet definition by index; returns True if removed."""
    global _job_sheets
    if 0 <= index < len(_job_sheets):
        _job_sheets.pop(index)
        return True
    return False


def update_job_sheet(index: int, **updates) -> bool:
    """Update fields for a job sheet; returns True if updated."""
    if 0 <= index < len(_job_sheets):
        sheet = _job_sheets[index]
        if "width_mm" in updates:
            sheet["width_mm"] = _safe_float(updates["width_mm"])
        if "height_mm" in updates:
            sheet["height_mm"] = _safe_float(updates["height_mm"])
        if "quantity" in updates:
            sheet["quantity"] = max(_safe_int(updates["quantity"]), 1)
        if "label" in updates:
            label = updates["label"]
            sheet["label"] = str(label) if label is not None else None
        return True
    return False


def clear_job_sheets():
    """Remove all job sheet definitions."""
    global _job_sheets
    _job_sheets = []


# --------------------------
# Sheet mode helpers
# --------------------------


def set_sheet_mode(mode: Optional[str]) -> None:
    """Set how sheets are provided: 'simple' (default) or 'job_sheets'."""
    global _sheet_mode
    if mode == SHEET_MODE_JOB_SHEETS:
        _sheet_mode = SHEET_MODE_JOB_SHEETS
    else:
        _sheet_mode = SHEET_MODE_SIMPLE


def get_sheet_mode() -> str:
    """Return the current sheet mode."""
    return _sheet_mode or SHEET_MODE_SIMPLE


def is_simple_sheet_mode() -> bool:
    """Return True when repeated default sheets are active."""
    return get_sheet_mode() == SHEET_MODE_SIMPLE


def is_job_sheets_mode() -> bool:
    """Return True when explicit job sheets should be used."""
    return get_sheet_mode() == SHEET_MODE_JOB_SHEETS


# --------------------------
# Kerf / gap accessors
# --------------------------


def set_kerf_mm(value: float) -> None:
    """Store kerf width (mm) used between adjacent parts."""
    global _kerf_mm
    _kerf_mm = float(value)


def get_kerf_mm() -> float:
    """Return kerf width (mm)."""
    return float(_kerf_mm)


def set_gap_mm(value: float) -> None:
    """Store edge gap/margin (mm) around parts/sheets."""
    global _gap_mm
    _gap_mm = float(value)


def get_gap_mm() -> float:
    """Return edge gap/margin (mm)."""
    return float(_gap_mm)


def set_default_allow_rotate(value: bool) -> None:
    """Set default allow-rotate flag for panels without explicit rotation setting."""
    global _default_allow_rotate
    _default_allow_rotate = bool(value)


def get_default_allow_rotate() -> bool:
    """Return default allow-rotate flag."""
    return bool(_default_allow_rotate)


def set_job_allow_rotate(value: Optional[bool]) -> None:
    """Set job-specific allow-rotate flag (used for the current nesting session)."""
    global _job_allow_rotate
    _job_allow_rotate = bool(value) if value is not None else None


def get_job_allow_rotate() -> Optional[bool]:
    """Return job-specific allow-rotate preference, or None if unset."""
    return _job_allow_rotate


def clear_job_allow_rotate() -> None:
    """Reset job-specific allow-rotate flag so it re-aligns with defaults."""
    global _job_allow_rotate
    _job_allow_rotate = None


def set_optimize_for_cut_path(value: bool) -> None:
    """Enable/disable guillotine-style cut optimization."""
    global _optimize_for_cut_path
    _optimize_for_cut_path = bool(value)


def get_optimize_for_cut_path() -> bool:
    """Return cut optimization flag."""
    return bool(_optimize_for_cut_path)


def set_kerf_width_mm(value: float) -> None:
    """Set kerf width (mm) for cut-path optimization."""
    global _kerf_width_mm
    _kerf_width_mm = float(value)


def get_kerf_width_mm() -> float:
    """Return kerf width (mm) for cut-path optimization."""
    return float(_kerf_width_mm)


def set_allowed_rotations_deg(values) -> None:
    """Set allowed rotation angles as a tuple of ints."""
    global _allowed_rotations_deg
    try:
        vals = tuple(int(v) for v in (values or ()))
        if not vals:
            vals = (0,)
    except Exception:
        vals = (0,)
    _allowed_rotations_deg = vals


def get_allowed_rotations_deg():
    """Return allowed rotation angles tuple."""
    return tuple(_allowed_rotations_deg or (0,))


# --------------------------
# Measurement system
# --------------------------


def set_measurement_system(system: str) -> None:
    """Store measurement system preference ('metric' or 'imperial')."""
    global _measurement_system
    system = system if system in ("metric", "imperial") else "imperial"
    _measurement_system = system


def get_measurement_system() -> str:
    """Return the current measurement system."""
    return _measurement_system or "imperial"


# --------------------------
# Last layout storage
# --------------------------


def set_last_layout(layout_list) -> None:
    """Store a copy of the last nesting layout (list of PlacedPart)."""
    global _last_layout
    # Make a deep copy to avoid external mutation
    _last_layout = deepcopy(layout_list)


def get_last_layout():
    """Retrieve a copy of the last nesting layout, or None."""
    if _last_layout is None:
        return None
    return deepcopy(_last_layout)


def set_nesting_stats(
    sheets_used: Optional[int] = None,
    cut_complexity: Optional[float] = None,
    overlaps_count: Optional[int] = None,
    per_sheet_stats: Optional[list[dict[str, Any]]] = None,
) -> None:
    """Store summary stats from the last nesting run."""
    global _nesting_stats
    _nesting_stats = {
        "sheets_used": sheets_used,
        "cut_complexity": cut_complexity,
        "overlaps_count": overlaps_count,
        "per_sheet_stats": list(per_sheet_stats or []),
    }


def get_nesting_stats() -> dict[str, Any]:
    """Return summary stats from the last nesting run."""
    return dict(
        _nesting_stats
        or {
            "sheets_used": None,
            "cut_complexity": None,
            "overlaps_count": None,
            "per_sheet_stats": [],
        }
    )


# --------------------------
# Panels storage (pure data)
# --------------------------


def set_panels(panels_list) -> None:
    """Replace panels list."""
    global _panels
    _panels = list(panels_list or [])
    clear_shape_panel_objects()


def add_panels(panels_list) -> None:
    """Append panels to the current list."""
    global _panels
    if not panels_list:
        return
    _panels.extend(panels_list)


def get_panels():
    """Return a copy of the current panels list."""
    sanitized = []
    for panel in _panels:
        copied = None
        if hasattr(panel, "copy") and callable(panel.copy):
            try:
                copied = panel.copy()
            except Exception:
                copied = None
        if copied is None:
            try:
                copied = dict(panel)
            except Exception:
                copied = panel
        sanitized.append(copied)
    return sanitized


def clear_panels() -> None:
    """Clear all panels."""
    global _panels
    _panels = []
    clear_shape_panel_objects()


# --------------------------
# Optimization mode
# --------------------------


def set_optimization_mode(mode: str) -> None:
    """Set nesting optimization mode (material or cuts)."""
    global _optimization_mode
    if mode not in ("material", "cuts"):
        mode = "material"
    _optimization_mode = mode


def get_optimization_mode() -> str:
    """Get the current nesting optimization mode."""
    return _optimization_mode or "material"


def set_nesting_mode(mode: str) -> None:
    """Set layout style: pack (default) or cut_friendly."""
    global _nesting_mode
    if mode not in ("pack", "cut_friendly"):
        mode = "pack"
    _nesting_mode = mode


def get_nesting_mode() -> str:
    """Return layout style."""
    return _nesting_mode or "pack"


# --------------------------
# Export flags
# --------------------------


def set_export_include_labels(value: bool) -> None:
    """Set whether exports include part labels."""
    global _export_include_labels
    _export_include_labels = bool(value)


def get_export_include_labels() -> bool:
    """Return whether exports include part labels."""
    return bool(_export_include_labels)


def set_export_include_dimensions(value: bool) -> None:
    """Set whether exports include simple dimensions."""
    global _export_include_dimensions
    _export_include_dimensions = bool(value)


def get_export_include_dimensions() -> bool:
    """Return whether exports include simple dimensions."""
    return bool(_export_include_dimensions)


# --------------------------
# Document object tracking
# --------------------------


def set_source_panel_objects(objs) -> None:
    """Track source panel FreeCAD objects used for nesting."""
    global _source_panel_objects
    _source_panel_objects = list(objs or [])


def get_source_panel_objects():
    """Return tracked source panel FreeCAD objects."""
    return list(_source_panel_objects or [])


def set_nested_sheet_group(group) -> None:
    """Track the nested sheet group object."""
    global _nested_sheet_group
    _nested_sheet_group = group


def get_nested_sheet_group():
    """Return the nested sheet group object."""
    return _nested_sheet_group


# --------------------------
# Genetic Algorithm Settings
# --------------------------


# Genetic algorithm functions removed - feature was unused


# --------------------------
# Cut Sequence Settings
# --------------------------

_generate_cut_sequence: bool = False
_cut_sequences: list[Any] = []


def set_generate_cut_sequence(enabled: bool) -> None:
    """Enable or disable cut sequence generation."""
    global _generate_cut_sequence
    _generate_cut_sequence = bool(enabled)


def get_generate_cut_sequence() -> bool:
    """Return whether cut sequence generation is enabled."""
    return _generate_cut_sequence


def set_cut_sequences(sequences) -> None:
    """Store generated cut sequences."""
    global _cut_sequences
    _cut_sequences = sequences or []


def get_cut_sequences():
    """Return stored cut sequences."""
    return _cut_sequences or []
