"""Preset sheet definitions and helpers."""

from __future__ import annotations

from SquatchCut.core.units import inches_to_mm

PRESET_SHEETS = [
    {
        "id": "4x8",
        "label": "4' x 8'",
        "width_mm": inches_to_mm(48.0),
        "height_mm": inches_to_mm(96.0),
        "nickname": "4x8 ft",
    },
    {
        "id": "2x4",
        "label": "2' x 4'",
        "width_mm": inches_to_mm(24.0),
        "height_mm": inches_to_mm(48.0),
        "nickname": "2x4 ft",
    },
    {
        "id": "5x10",
        "label": "5' x 10'",
        "width_mm": inches_to_mm(60.0),
        "height_mm": inches_to_mm(120.0),
        "nickname": "5x10 ft",
    },
]


def find_matching_preset(width_mm: float, height_mm: float, tol_mm: float = 1.0):
    """Return the preset whose dimensions are within tolerance of the provided values."""
    if width_mm is None or height_mm is None:
        return None
    for preset in PRESET_SHEETS:
        if (
            abs(width_mm - preset["width_mm"]) <= tol_mm
            and abs(height_mm - preset["height_mm"]) <= tol_mm
        ):
            return preset
    return None
