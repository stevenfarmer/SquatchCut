"""Centralized settings hydration for SquatchCut."""

from __future__ import annotations

from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core import session_state
from SquatchCut.core import units as sc_units


def hydrate_from_params() -> None:
    """
    Load persisted preferences from FreeCAD ParamGet into in-memory session_state.

    Safe to call multiple times and does not require any UI context.
    """
    prefs = SquatchCutPreferences()

    measurement_system = prefs.get_measurement_system()
    units = "in" if measurement_system == "imperial" else "mm"

    # Ensure global units preference matches the measurement system
    sc_units.set_units(units)
    session_state.set_measurement_system(measurement_system)

    # Core defaults (stored in mm)
    session_state.set_sheet_size(
        prefs.get_default_sheet_width_mm(),
        prefs.get_default_sheet_height_mm(),
    )
    session_state.set_kerf_mm(prefs.get_default_kerf_mm())
    session_state.set_gap_mm(prefs.get_default_spacing_mm())
    session_state.set_kerf_width_mm(prefs.get_default_kerf_mm())
    session_state.set_optimize_for_cut_path(prefs.get_default_optimize_for_cut_path())

    # Export defaults
    session_state.set_export_include_labels(prefs.get_export_include_labels())
    session_state.set_export_include_dimensions(prefs.get_export_include_dimensions())
