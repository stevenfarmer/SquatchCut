import math

from SquatchCut import settings
from SquatchCut.core import session_state
from SquatchCut.core import units as sc_units
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core import sheet_presets as sc_sheet_presets
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel


def _snapshot_prefs(prefs: SquatchCutPreferences) -> dict:
    return {
        "measurement_system": prefs.get_measurement_system(),
        "width_mm": prefs.get_default_sheet_width_mm(),
        "height_mm": prefs.get_default_sheet_height_mm(),
        "width_in": prefs.get_default_sheet_width_in(),
        "height_in": prefs.get_default_sheet_height_in(),
        "spacing_mm": prefs.get_default_spacing_mm(),
        "kerf_mm": prefs.get_default_kerf_mm(),
        "cut_opt": prefs.get_default_optimize_for_cut_path(),
    }


def _restore_prefs(prefs: SquatchCutPreferences, snapshot: dict) -> None:
    prefs.set_measurement_system(snapshot["measurement_system"])
    prefs.set_default_sheet_width_mm(snapshot["width_mm"])
    prefs.set_default_sheet_height_mm(snapshot["height_mm"])
    prefs.set_default_sheet_width_in(snapshot["width_in"])
    prefs.set_default_sheet_height_in(snapshot["height_in"])
    prefs.set_default_spacing_mm(snapshot["spacing_mm"])
    prefs.set_default_kerf_mm(snapshot["kerf_mm"])
    prefs.set_default_optimize_for_cut_path(snapshot["cut_opt"])
    settings.hydrate_from_params()


def test_taskpanel_initial_state_uses_hydrated_defaults_imperial():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("imperial")
        prefs.set_default_sheet_width_in(50.0)
        prefs.set_default_sheet_height_in(100.0)
        prefs.set_default_spacing_mm(5.0)
        prefs.set_default_kerf_mm(3.0)
        prefs.set_default_optimize_for_cut_path(True)
        settings.hydrate_from_params()

        panel = SquatchCutTaskPanel.__new__(SquatchCutTaskPanel)
        panel._prefs = prefs
        state = panel._compute_initial_state(doc=None)

        assert state["measurement_system"] == "imperial"
        assert math.isclose(state["sheet_width_mm"], sc_units.inches_to_mm(50.0), rel_tol=1e-6)
        assert math.isclose(state["sheet_height_mm"], sc_units.inches_to_mm(100.0), rel_tol=1e-6)
        assert sc_units.get_units() == "in"
    finally:
        _restore_prefs(prefs, snap)


def test_taskpanel_initial_state_uses_hydrated_defaults_metric():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("metric")
        prefs.set_default_sheet_width_mm(1220.0)
        prefs.set_default_sheet_height_mm(2440.0)
        settings.hydrate_from_params()

        panel = SquatchCutTaskPanel.__new__(SquatchCutTaskPanel)
        panel._prefs = prefs
        state = panel._compute_initial_state(doc=None)

        assert state["measurement_system"] == "metric"
        assert math.isclose(state["sheet_width_mm"], 1220.0, rel_tol=1e-6)
        assert math.isclose(state["sheet_height_mm"], 2440.0, rel_tol=1e-6)
        assert sc_units.get_units() == "mm"
    finally:
        _restore_prefs(prefs, snap)


def test_taskpanel_init_does_not_auto_select_preset():
    settings.hydrate_from_params()
    panel = SquatchCutTaskPanel.__new__(SquatchCutTaskPanel)
    panel._prefs = SquatchCutPreferences()
    state = panel._compute_initial_state(doc=None)
    panel.measurement_system = state["measurement_system"]
    panel._preset_state = sc_sheet_presets.PresetSelectionState()
    panel._presets = sc_sheet_presets.get_preset_entries(panel.measurement_system)
    # The initial preset state should remain at index 0 (None) until the user changes it.
    assert panel._preset_state.current_index == 0
    assert panel._preset_state.current_id is None
