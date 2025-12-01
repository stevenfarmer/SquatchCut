import math

from SquatchCut import settings
from SquatchCut.core import session_state
from SquatchCut.core import units as sc_units
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel
from SquatchCut.gui.taskpanel_settings import SquatchCutSettingsPanel


def _snapshot_prefs(prefs: SquatchCutPreferences) -> dict:
    return {
        "measurement_system": prefs.get_measurement_system(),
        "width_mm": prefs.get_default_sheet_width_mm(),
        "height_mm": prefs.get_default_sheet_height_mm(),
        "kerf_mm": prefs.get_default_kerf_mm(),
        "gap_mm": prefs.get_default_spacing_mm(),
        "allow_rotate": prefs.get_default_allow_rotate(),
    }


def _restore_prefs(prefs: SquatchCutPreferences, snap: dict) -> None:
    prefs.set_measurement_system(snap["measurement_system"])
    prefs.set_default_sheet_width_mm(snap["width_mm"])
    prefs.set_default_sheet_height_mm(snap["height_mm"])
    prefs.set_default_kerf_mm(snap["kerf_mm"])
    prefs.set_default_spacing_mm(snap["gap_mm"])
    prefs.set_default_allow_rotate(snap["allow_rotate"])
    settings.hydrate_from_params()


def test_settings_display_respects_measurement_system_metric():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("metric")
        prefs.set_default_sheet_width_mm(1200.0)
        prefs.set_default_sheet_height_mm(2400.0)
        prefs.set_default_kerf_mm(3.0)
        settings.hydrate_from_params()

        panel = SquatchCutSettingsPanel()
        assert panel.sheet_width_edit.text() == sc_units.format_length(1200.0, "metric")
        assert panel.sheet_height_edit.text() == sc_units.format_length(2400.0, "metric")
        assert panel.kerf_edit.text() == sc_units.format_length(3.0, "metric")
    finally:
        _restore_prefs(prefs, snap)


def test_settings_display_respects_measurement_system_imperial_and_kerf_storage():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("imperial")
        prefs.set_default_sheet_width_mm(sc_units.inches_to_mm(50.0))
        prefs.set_default_sheet_height_mm(sc_units.inches_to_mm(100.0))
        prefs.set_default_kerf_mm(3.175)  # 1/8"
        settings.hydrate_from_params()

        panel = SquatchCutSettingsPanel()
        assert panel.sheet_width_edit.text() == sc_units.format_length(
            sc_units.inches_to_mm(50.0), "imperial"
        )
        assert panel.kerf_edit.text() == sc_units.format_length(3.175, "imperial")

        # Update kerf using imperial fraction and persist as mm
        panel.kerf_edit.setText("1/4")
        # Keep sheet defaults to avoid clearing them
        panel.sheet_width_edit.setText(sc_units.format_length(sc_units.inches_to_mm(50.0), "imperial"))
        panel.sheet_height_edit.setText(sc_units.format_length(sc_units.inches_to_mm(100.0), "imperial"))
        assert panel._apply_changes() is True
        assert math.isclose(prefs.get_default_kerf_mm(), sc_units.inches_to_mm(0.25), rel_tol=1e-6)
    finally:
        _restore_prefs(prefs, snap)


def test_rotation_defaults_sync_to_taskpanel():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_default_allow_rotate(True)
        settings.hydrate_from_params()
        panel = SquatchCutTaskPanel()
        assert panel.allow_90_check.isChecked()
        assert panel.allow_180_check.isChecked()

        prefs.set_default_allow_rotate(False)
        settings.hydrate_from_params()
        panel2 = SquatchCutTaskPanel()
        assert not panel2.allow_90_check.isChecked()
        assert not panel2.allow_180_check.isChecked()
    finally:
        _restore_prefs(prefs, snap)


def test_no_defaults_shows_empty_fields_and_no_preset():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.clear_default_sheet_size()
        settings.hydrate_from_params()
        panel_settings = SquatchCutSettingsPanel()
        assert panel_settings.sheet_width_edit.text() == ""
        assert panel_settings.sheet_height_edit.text() == ""

        panel_main = SquatchCutTaskPanel()
        assert panel_main.sheet_width_edit.text() == ""
        assert panel_main.sheet_height_edit.text() == ""
        assert panel_main.preset_combo.currentIndex() == 0
        assert panel_main._preset_state.current_id is None
    finally:
        _restore_prefs(prefs, snap)


def test_developer_mode_controls_absent():
    panel = SquatchCutSettingsPanel()
    assert not hasattr(panel, "dev_mode_check")
