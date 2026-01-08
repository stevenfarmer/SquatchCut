import math

from SquatchCut import settings
from SquatchCut.core import session_state
from SquatchCut.core import units as sc_units
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core.units import inches_to_mm
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel
from SquatchCut.gui.taskpanel_settings import SquatchCutSettingsPanel


def _snapshot_prefs(prefs: SquatchCutPreferences) -> dict:
    return {
        "measurement_system": prefs.get_measurement_system(),
        "width_mm": prefs.get_default_sheet_width_mm(),
        "height_mm": prefs.get_default_sheet_height_mm(),
        "width_in": prefs.get_default_sheet_width_in(),
        "height_in": prefs.get_default_sheet_height_in(),
        "spacing_mm": prefs.get_default_spacing_mm(),
        "kerf_mm": prefs.get_default_kerf_mm(),
        "allow_rotate": prefs.get_default_allow_rotate(),
    }


def _restore_prefs(prefs: SquatchCutPreferences, snap: dict) -> None:
    prefs.set_measurement_system(snap["measurement_system"])
    prefs.set_default_sheet_width_mm(snap["width_mm"])
    prefs.set_default_sheet_height_mm(snap["height_mm"])
    prefs.set_default_sheet_width_in(snap["width_in"])
    prefs.set_default_sheet_height_in(snap["height_in"])
    prefs.set_default_spacing_mm(snap["spacing_mm"])
    prefs.set_default_kerf_mm(snap["kerf_mm"])
    prefs.set_default_allow_rotate(snap["allow_rotate"])
    settings.hydrate_from_params()


def test_main_taskpanel_hydration_order():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("imperial")
        prefs.set_default_sheet_width_in(64.0)
        prefs.set_default_sheet_height_in(96.0)
        prefs.set_default_spacing_mm(3.0)
        prefs.set_default_kerf_mm(sc_units.inches_to_mm(0.125))
        settings.hydrate_from_params()

        panel = SquatchCutTaskPanel()

        assert panel.measurement_system == "imperial"
        expected_width_text = sc_units.format_length(sc_units.inches_to_mm(64.0), "imperial")
        expected_height_text = sc_units.format_length(sc_units.inches_to_mm(96.0), "imperial")
        assert panel.sheet_widget.sheet_width_edit.text() == expected_width_text
        assert panel.sheet_widget.sheet_height_edit.text() == expected_height_text
        assert panel.sheet_widget.margin_edit.text() == sc_units.format_length(3.0, "imperial")
        assert panel._initial_state["measurement_system"] == "imperial"
        current = _snapshot_prefs(prefs)
        assert current["measurement_system"] == "imperial"
        assert math.isclose(current["width_in"], 64.0, rel_tol=1e-6)
        assert math.isclose(current["height_in"], 96.0, rel_tol=1e-6)
        assert math.isclose(current["spacing_mm"], 3.0, rel_tol=1e-6)
        assert math.isclose(current["kerf_mm"], sc_units.inches_to_mm(0.125), rel_tol=1e-6)
    finally:
        _restore_prefs(prefs, snap)


def test_settings_panel_hydration_and_persistence():
    # Ensure clean state for this test
    session_state.clear_job_allow_rotate()

    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("metric")
        prefs.set_default_sheet_width_mm(1200.0)
        prefs.set_default_sheet_height_mm(2400.0)
        prefs.set_default_spacing_mm(5.0)
        prefs.set_default_kerf_mm(3.0)
        prefs.set_default_allow_rotate(True)
        settings.hydrate_from_params()

        panel = SquatchCutSettingsPanel()
        assert panel.sheet_width_edit.text() == sc_units.format_length(1200.0, "metric")
        assert panel.sheet_height_edit.text() == sc_units.format_length(2400.0, "metric")
        assert panel.kerf_edit.text() == sc_units.format_length(3.0, "metric")
        assert panel.gap_edit.text() == "5.0"
        assert panel.allow_rotation_check.isChecked() is True

        panel.sheet_width_edit.setText("1500")
        panel.sheet_height_edit.setText("3100")
        panel.kerf_edit.setText("4")
        panel.gap_edit.setText("6.5")
        panel.allow_rotation_check.setChecked(False)
        assert panel._apply_changes() is True
        settings.hydrate_from_params()

        reopened = SquatchCutSettingsPanel()
        assert reopened.sheet_width_edit.text() == sc_units.format_length(1500.0, "metric")
        assert reopened.sheet_height_edit.text() == sc_units.format_length(3100.0, "metric")
        assert reopened.kerf_edit.text() == sc_units.format_length(4.0, "metric")
        assert reopened.gap_edit.text() == "6.5"
        assert reopened.allow_rotation_check.isChecked() is False

        main_panel = SquatchCutTaskPanel()
        assert math.isclose(main_panel._initial_state["sheet_width_mm"], 1500.0, rel_tol=1e-6)
        assert math.isclose(main_panel._initial_state["sheet_height_mm"], 3100.0, rel_tol=1e-6)
        assert main_panel.nesting_widget.job_allow_rotation_check.isChecked() is False
    finally:
        _restore_prefs(prefs, snap)


def test_hydrate_from_params_preserves_job_sheets():
    settings.hydrate_from_params()
    session_state.clear_job_sheets()
    session_state.set_sheet_mode("job_sheets")
    sheets = [
        {"width_mm": 500.0, "height_mm": 1000.0, "quantity": 1, "label": "Test"},
    ]
    session_state.set_job_sheets(sheets)
    settings.hydrate_from_params()
    assert session_state.get_job_sheets() == sheets
    assert session_state.get_sheet_mode() == "job_sheets"
    session_state.clear_job_sheets()
    session_state.set_sheet_mode("simple")


def test_hydrate_from_params_is_gui_free(monkeypatch):
    from SquatchCut import settings as sc_settings

    recorded = {}

    class DummyPrefs:
        def has_default_sheet_size(self, system):
            recorded["has_default_sheet_size"] = system
            return True

        def get_default_sheet_width_mm(self):
            return 1000.0

        def get_default_sheet_height_mm(self):
            return 500.0

        def get_default_sheet_size_mm(self, system):
            if system == "imperial":
                return inches_to_mm(48.0), inches_to_mm(96.0)
            return 1000.0, 500.0

        def get_default_spacing_mm(self):
            return 4.5

        def get_default_kerf_mm(self):
            return 1.5

        def get_default_optimize_for_cut_path(self):
            return True

        def get_default_allow_rotate(self):
            return False

        def get_measurement_system(self):
            return "imperial"

        def get_export_include_labels(self):
            return True

        def get_export_include_dimensions(self):
            return False

    class DummySession:
        def __init__(self):
            self.values = {}

        def set_measurement_system(self, value):
            self.values["measurement_system"] = value

        def set_sheet_size(self, width, height):
            self.values["sheet_size"] = (width, height)

        def clear_sheet_size(self):
            self.values["sheet_size"] = None

        def set_kerf_mm(self, value):
            self.values["kerf_mm"] = value

        def set_gap_mm(self, value):
            self.values["gap_mm"] = value

        def set_kerf_width_mm(self, value):
            self.values["kerf_width_mm"] = value

        def set_optimize_for_cut_path(self, value):
            self.values["optimize_for_cut_path"] = value

        def set_default_allow_rotate(self, value):
            self.values["allow_rotate"] = value

        def set_export_include_labels(self, value):
            self.values["labels"] = value

        def set_export_include_dimensions(self, value):
            self.values["dimensions"] = value

    class DummyUnits:
        def __init__(self):
            self.units_value = None

        def set_units(self, value):
            self.units_value = value

    dummy_state = DummySession()
    dummy_units = DummyUnits()

    monkeypatch.setattr(sc_settings, "SquatchCutPreferences", DummyPrefs)
    monkeypatch.setattr(sc_settings, "session_state", dummy_state)
    monkeypatch.setattr(sc_settings, "sc_units", dummy_units)

    sc_settings.hydrate_from_params()

    assert dummy_units.units_value == "in"
    assert dummy_state.values["measurement_system"] == "imperial"
    assert dummy_state.values["sheet_size"] == (inches_to_mm(48.0), inches_to_mm(96.0))
    assert dummy_state.values["kerf_mm"] == 1.5
    assert dummy_state.values["gap_mm"] == 4.5
    assert dummy_state.values["kerf_width_mm"] == 1.5
    assert dummy_state.values["optimize_for_cut_path"] is True
    assert dummy_state.values["allow_rotate"] is False
    assert dummy_state.values["labels"] is True
    assert dummy_state.values["dimensions"] is False
