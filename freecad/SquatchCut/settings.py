"""Centralized settings hydration for SquatchCut."""

from __future__ import annotations

from SquatchCut.core import session_state
from SquatchCut.core import sheet_presets as sc_sheet_presets
from SquatchCut.core import units as sc_units
from SquatchCut.core.preferences import SquatchCutPreferences


def hydrate_from_params(measurement_override: str | None = None) -> None:
    """
    Load persisted preferences from FreeCAD ParamGet into in-memory session_state.

    Safe to call multiple times and does not require any UI context.
    """
    prefs = SquatchCutPreferences()

    if measurement_override in ("metric", "imperial"):
        measurement_system = measurement_override
    else:
        measurement_system = prefs.get_measurement_system()
    units = "in" if measurement_system == "imperial" else "mm"

    # Ensure global units preference matches the measurement system
    sc_units.set_units(units)
    session_state.set_measurement_system(measurement_system)

    # Core defaults (per measurement system)
    if prefs.has_default_sheet_size(measurement_system):
        default_width_mm, default_height_mm = prefs.get_default_sheet_size_mm(measurement_system)
    else:
        default_width_mm, default_height_mm = sc_sheet_presets.get_factory_default_sheet_size(measurement_system)
    session_state.set_sheet_size(default_width_mm, default_height_mm)
    session_state.set_kerf_mm(prefs.get_default_kerf_mm())
    session_state.set_gap_mm(prefs.get_default_spacing_mm())
    session_state.set_kerf_width_mm(prefs.get_default_kerf_mm())
    session_state.set_optimize_for_cut_path(prefs.get_default_optimize_for_cut_path())
    session_state.set_default_allow_rotate(prefs.get_default_allow_rotate())

    # Export defaults
    session_state.set_export_include_labels(prefs.get_export_include_labels())
    session_state.set_export_include_dimensions(prefs.get_export_include_dimensions())
