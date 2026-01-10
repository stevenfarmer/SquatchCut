from __future__ import annotations

import re
from typing import Optional

from SquatchCut.freecad_integration import App  # Centralized FreeCAD import

# FreeCAD ParamGroup for SquatchCut prefs
PREF_PATH = "User parameter:BaseApp/Preferences/Mod/SquatchCut"
UNITS_KEY = "Units"  # "mm" or "in"
_fallback_units = "mm"


def _get_param_group():
    if App is None:
        return None
    return App.ParamGet(PREF_PATH)


# -----------------------
# Unit preference helpers
# -----------------------

def get_units():
    """
    Return the current units preference as a string:

    - "mm" for Metric (millimeters)
    - "in" for Imperial (inches)

    Default is "mm" if not set.
    """
    group = _get_param_group()
    if group is None:
        return _fallback_units
    value = group.GetString(UNITS_KEY, _fallback_units)
    if value not in ("mm", "in"):
        value = "mm"
    return value


def set_units(units: str):
    """
    Set the units preference. Must be "mm" or "in".
    Any other value is ignored.
    """
    global _fallback_units
    if units not in ("mm", "in"):
        return
    group = _get_param_group()
    if group is None:
        _fallback_units = units
        return
    group.SetString(UNITS_KEY, units)


# --------------
# Conversions
# --------------

MM_PER_INCH = 25.4


def mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches."""
    return float(mm) / MM_PER_INCH


def inches_to_mm(inches: float) -> float:
    """Convert inches to millimeters."""
    return float(inches) * MM_PER_INCH


# ------------------------------
# Imperial fraction formatting
# ------------------------------

def inches_to_fraction_str(value_in_inches: float, max_denominator: int = 16) -> str:
    """
    Format inches as a mixed fraction string (e.g., "24", "3/4", "24 3/8").

    - Uses Fraction to reduce terms.
    - max_denominator controls rounding (default 1/16").
    """
    from fractions import Fraction

    # Normalize tiny negatives to zero
    val = float(value_in_inches)
    if abs(val) < 1e-9:
        val = 0.0

    whole = int(val)
    frac_part = val - whole
    # Handle rounding to whole when fraction is effectively zero
    frac = Fraction(frac_part).limit_denominator(max_denominator)
    if abs(frac.numerator) < 1e-9:
        return str(whole)

    # If rounding pushes fraction to a whole
    if frac.numerator == frac.denominator:
        whole += 1
        frac = Fraction(0, 1)
        return str(whole)

    frac_str = f"{frac.numerator}/{frac.denominator}"
    if whole == 0:
        return frac_str
    return f"{whole} {frac_str}"


def parse_imperial_inches(text: str) -> float:
    """
    Parse imperial strings like "48", "48.5", "3/4", "48 3/4", "48-3/4" into inches (float).

    Raises ValueError on invalid input.
    """
    raw = str(text or "").strip()
    if not raw:
        raise ValueError("Invalid imperial length format: empty input")

    # Regex strict pattern:
    # 1. Whole number (optional decimal) followed optionally by a fraction (mixed number)
    # 2. Or just a fraction
    # The mixed number part allows separator of space or dash (with optional surrounding spaces)
    pattern = re.compile(r"""
        ^
        (?:
            (?P<whole>(?:\d+(?:\.\d*)?|\.\d+)) # Whole number (int or float, e.g. 5, 5., .5, 5.5)
            (?:
                \s*[- ]\s*                    # Separator: dash or space
                (?P<frac_mixed>\d+\s*/\s*\d+) # Fraction part of mixed number
            )?
        |
            (?P<frac_only>\d+\s*/\s*\d+)      # Fraction only
        )
        $
    """, re.VERBOSE)

    match = pattern.match(raw)
    if not match:
        raise ValueError(f"Invalid imperial length format: '{text}'")

    whole_str = match.group("whole")
    frac_mixed_str = match.group("frac_mixed")
    frac_only_str = match.group("frac_only")

    val = 0.0

    if whole_str:
        val += float(whole_str)

    frac_str = frac_mixed_str or frac_only_str
    if frac_str:
        # Normalize fraction slash spacing for splitting
        frac_clean = frac_str.replace(" ", "")
        num_str, den_str = frac_clean.split("/")
        den = float(den_str)
        if den == 0:
            raise ValueError(f"Invalid imperial length format: '{text}' (division by zero)")
        val += float(num_str) / den

    return val


def mm_to_display(value_mm: float) -> float:
    """Convert an internal mm value to the current display units."""
    units = get_units()
    if units == "in":
        return value_mm / MM_PER_INCH
    return value_mm


def display_to_mm(value_display: float) -> float:
    """Convert a user-entered value in current display units to mm."""
    units = get_units()
    if units == "in":
        return value_display * MM_PER_INCH
    return value_display


def get_unit_label() -> str:
    """Return the short label for the current units, e.g. 'mm' or 'in'."""
    return get_units()


# ------------------------------
# Measurement-system formatting
# ------------------------------

def _normalize_measurement_system(system: str) -> str:
    """Return a safe measurement system string ('metric' or 'imperial')."""
    return "imperial" if system == "imperial" else "metric"


def unit_label_for_system(system: str) -> str:
    """Return 'mm' or 'in' for the provided measurement system."""
    return "in" if _normalize_measurement_system(system) == "imperial" else "mm"


def format_metric_length(value_mm: float, decimals: int = 3) -> str:
    """Format a metric length with trimmed trailing zeros."""
    formatted = f"{float(value_mm):.{decimals}f}"
    formatted = formatted.rstrip("0").rstrip(".")
    return formatted or "0"


def format_length(value_mm: float, measurement_system: str, max_denominator: int = 16, decimals: int = 3) -> str:
    """
    Format a millimeter value for display in the requested measurement system.

    - Metric: trimmed decimal string.
    - Imperial: mixed fraction string (using inches_to_fraction_str).
    """
    system = _normalize_measurement_system(measurement_system)
    if system == "imperial":
        return format_imperial_length(value_mm, max_denominator=max_denominator)
    return format_metric_length(value_mm, decimals=decimals)


def format_imperial_length(value_mm: float, max_denominator: int = 16) -> str:
    """
    Format mm as an imperial string using mixed fractions.
    """
    inches = mm_to_inches(value_mm)
    return inches_to_fraction_str(inches, max_denominator=max_denominator)


def format_preset_label(
    width_mm: float,
    height_mm: float,
    measurement_system: str,
    nickname: Optional[str] = None,
    max_denominator: int = 16,
    decimals: int = 3,
) -> str:
    """
    Return a preset label contained within a single measurement system.

    - Metric: "1220 x 2440 mm" (pure metric).
    - Imperial: nickname (if provided) or "W x H in".
    """
    system = _normalize_measurement_system(measurement_system)
    if system == "imperial":
        if nickname:
            return nickname
        width_in = format_length(width_mm, "imperial", max_denominator)
        height_in = format_length(height_mm, "imperial", max_denominator)
        return f"{width_in} x {height_in} in"
    # Metric path
    metric_pair = f"{format_metric_length(width_mm, decimals)} x {format_metric_length(height_mm, decimals)} mm"
    return metric_pair


def parse_length(text: str, measurement_system: str) -> float:
    """
    Parse a user-entered length string into millimeters based on measurement_system.

    Raises ValueError with a helpful message on failure.
    """
    system = _normalize_measurement_system(measurement_system)
    raw = str(text or "").strip()
    if not raw:
        raise ValueError("Length value is empty.")

    if system == "imperial":
        inches = parse_imperial_inches(raw)
        return inches_to_mm(inches)

    try:
        return float(raw)
    except Exception as exc:  # pragma: no cover - simple conversion
        raise ValueError(f"Invalid metric length: '{text}'") from exc
