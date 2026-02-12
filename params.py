"""Centralized SAE defaults and conversion helpers."""
from __future__ import annotations

from dataclasses import dataclass

INCH_TO_MM = 25.4
DEFAULT_UNITS = "imperial"


def inches_to_mm(value: float) -> float:
    """Convert inches to millimeters."""
    return value * INCH_TO_MM


def mm_to_inches(value: float) -> float:
    """Convert millimeters to inches."""
    return value / INCH_TO_MM


@dataclass(frozen=True)
class SheetSize:
    width_in: float
    height_in: float

    @property
    def width_mm(self) -> float:
        return inches_to_mm(self.width_in)

    @property
    def height_mm(self) -> float:
        return inches_to_mm(self.height_in)

    def dimensions_mm(self) -> tuple[float, float]:
        return (self.width_mm, self.height_mm)


SAE_SHEET_SIZE = SheetSize(width_in=48.0, height_in=96.0)
SAE_SHEET_SIZE_MM = SAE_SHEET_SIZE.dimensions_mm()
DEFAULT_SHEET_SIZE = SAE_SHEET_SIZE
