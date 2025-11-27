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

# Last nesting layout: list of PlacedPart objects
_last_layout = None

# Panels loaded from CSV (pure data; no FreeCAD objects)
_panels = []


# --------------------------
# Sheet size accessors
# --------------------------

def set_sheet_size(width_mm: float, height_mm: float) -> None:
    global _sheet_width, _sheet_height
    _sheet_width = float(width_mm)
    _sheet_height = float(height_mm)


def get_sheet_size():
    return _sheet_width, _sheet_height


# --------------------------
# Kerf / gap accessors
# --------------------------

def set_kerf_mm(value: float) -> None:
    global _kerf_mm
    _kerf_mm = float(value)


def get_kerf_mm() -> float:
    return float(_kerf_mm)


def set_gap_mm(value: float) -> None:
    global _gap_mm
    _gap_mm = float(value)


def get_gap_mm() -> float:
    return float(_gap_mm)


def set_default_allow_rotate(value: bool) -> None:
    global _default_allow_rotate
    _default_allow_rotate = bool(value)


def get_default_allow_rotate() -> bool:
    return bool(_default_allow_rotate)


# --------------------------
# Last layout storage
# --------------------------

def set_last_layout(layout_list) -> None:
    global _last_layout
    # Make a deep copy to avoid external mutation
    _last_layout = deepcopy(layout_list)


def get_last_layout():
    if _last_layout is None:
        return None
    return deepcopy(_last_layout)


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
