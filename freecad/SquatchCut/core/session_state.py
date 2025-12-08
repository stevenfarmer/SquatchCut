"""
Pure Python in-memory session state for SquatchCut.

This module intentionally does NOT import FreeCAD so that:
- Unit tests can import it without requiring FreeCAD to be installed.
- Integration with FreeCAD happens inside session.py instead.
"""

"""@codex
Pure in-memory session state for SquatchCut (no FreeCAD deps).
Tracks sheet size, kerf/gap, default rotation flag, last layout, and panel data.
"""

from copy import deepcopy

# Sheet size
_sheet_width = None
_sheet_height = None

# Cutting parameters
_kerf_mm = 0.0
_gap_mm = 0.0
_default_allow_rotate = False
_job_allow_rotate = None
_optimize_for_cut_path = False
_kerf_width_mm = 3.0
_allowed_rotations_deg = (0, 90)
_measurement_system = "metric"

# Last nesting layout: list of PlacedPart objects
_last_layout = None
_nesting_stats = {"sheets_used": None, "cut_complexity": None, "overlaps_count": None}

# Panels loaded from CSV (pure data; no FreeCAD objects)
_panels = []

# Optimization mode: "material" (default) or "cuts"
_optimization_mode = "material"
_nesting_mode = "pack"
_export_include_labels = True
_export_include_dimensions = False
_source_panel_objects = []
_nested_sheet_group = None


# --------------------------
# Sheet size accessors
# --------------------------

def set_sheet_size(width_mm: float, height_mm: float) -> None:
    """Store sheet size in millimeters in session memory."""
    global _sheet_width, _sheet_height
    _sheet_width = float(width_mm)
    _sheet_height = float(height_mm)


def clear_sheet_size() -> None:
    """Clear sheet size so UIs can show empty defaults when none are stored."""
    global _sheet_width, _sheet_height
    _sheet_width = None
    _sheet_height = None


def get_sheet_size():
    """Return current sheet size (width_mm, height_mm) or (None, None)."""
    return _sheet_width, _sheet_height


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


def set_job_allow_rotate(value: bool | None) -> None:
    """Set job-specific allow-rotate flag (used for the current nesting session)."""
    global _job_allow_rotate
    _job_allow_rotate = bool(value) if value is not None else None


def get_job_allow_rotate() -> bool | None:
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
    system = system if system in ("metric", "imperial") else "metric"
    _measurement_system = system


def get_measurement_system() -> str:
    """Return the current measurement system."""
    return _measurement_system or "metric"


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
    sheets_used: int | None = None,
    cut_complexity: float | None = None,
    overlaps_count: int | None = None,
) -> None:
    """Store summary stats from the last nesting run."""
    global _nesting_stats
    _nesting_stats = {
        "sheets_used": sheets_used,
        "cut_complexity": cut_complexity,
        "overlaps_count": overlaps_count,
    }


def get_nesting_stats() -> dict:
    """Return summary stats from the last nesting run."""
    return dict(_nesting_stats or {"sheets_used": None, "cut_complexity": None, "overlaps_count": None})


# --------------------------
# Panels storage (pure data)
# --------------------------

def set_panels(panels_list) -> None:
    """Replace panels list."""
    global _panels
    _panels = list(panels_list or [])


def add_panels(panels_list) -> None:
    """Append panels to the current list."""
    global _panels
    if not panels_list:
        return
    _panels.extend(panels_list)


def get_panels():
    """Return a copy of the current panels list."""
    return deepcopy(_panels)


def clear_panels() -> None:
    """Clear all panels."""
    global _panels
    _panels = []


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
