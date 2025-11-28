try:
    import FreeCAD as App  # type: ignore
except Exception:  # pragma: no cover
    App = None

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
