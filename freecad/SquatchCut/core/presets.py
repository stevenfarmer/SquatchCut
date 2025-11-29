"""Preset sheet definitions and helpers."""

from __future__ import annotations

PRESET_SHEETS = [
    {
        "id": "4x8",
        "width_mm": 1220.0,
        "height_mm": 2440.0,
        "nickname": "4x8 ft",
    },
    {
        "id": "5x10",
        "width_mm": 1525.0,
        "height_mm": 3050.0,
        "nickname": "5x10 ft",
    },
]


def find_matching_preset(width_mm: float, height_mm: float, tol_mm: float = 1.0):
    """Return the preset whose dimensions are within tolerance of the provided values."""
    if width_mm is None or height_mm is None:
        return None
    for preset in PRESET_SHEETS:
        if abs(width_mm - preset["width_mm"]) <= tol_mm and abs(
            height_mm - preset["height_mm"]
        ) <= tol_mm:
            return preset
    return None
