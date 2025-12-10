import math

from SquatchCut import settings
from SquatchCut.core import session_state
from SquatchCut.core import units as sc_units
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core.units import inches_to_mm, mm_to_inches
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
    _reset_session_state()


def _reset_session_state() -> None:
    session_state.clear_sheet_size()
    session_state.clear_panels()
    session_state.set_last_layout(None)
    session_state.set_measurement_system("metric")
    session_state.set_sheet_mode("simple")


def test_imperial_default_sheet_48x96():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        _reset_session_state()
        prefs.set_measurement_system("imperial")
        prefs.clear_default_sheet_size()
        settings.hydrate_from_params()

        panel = SquatchCutTaskPanel()

        expected_width_mm = inches_to_mm(48.0)
        expected_height_mm = inches_to_mm(96.0)
        assert math.isclose(panel._initial_state["sheet_width_mm"], expected_width_mm, rel_tol=1e-9)
        assert math.isclose(panel._initial_state["sheet_height_mm"], expected_height_mm, rel_tol=1e-9)
        assert panel.sheet_widget.sheet_width_edit.text() == sc_units.format_length(expected_width_mm, "imperial")
        assert panel.sheet_widget.sheet_height_edit.text() == sc_units.format_length(expected_height_mm, "imperial")
        assert panel.sheet_widget.preset_combo.currentIndex() == 0
        imperial_defaults = prefs.get_default_sheet_size_mm("imperial")
        assert math.isclose(imperial_defaults[0], expected_width_mm, rel_tol=1e-9)
        assert math.isclose(imperial_defaults[1], expected_height_mm, rel_tol=1e-9)
    finally:
        sc_units.set_units("mm")
        _restore_prefs(prefs, snap)


def test_taskpanel_does_not_auto_select_preset():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        _reset_session_state()
        prefs.set_measurement_system("metric")
        prefs.set_default_sheet_width_mm(1220.0)
        prefs.set_default_sheet_height_mm(2440.0)
        settings.hydrate_from_params()

        panel = SquatchCutTaskPanel()
        assert panel.sheet_widget.preset_combo.currentIndex() == 0
        assert panel.sheet_widget._preset_state.current_id is None
        assert panel.sheet_widget.sheet_width_edit.text() == sc_units.format_length(1220.0, "metric")
        assert panel.sheet_widget.sheet_height_edit.text() == sc_units.format_length(2440.0, "metric")
    finally:
        _restore_prefs(prefs, snap)


def test_preset_applies_only_to_current_sheet():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        _reset_session_state()
        prefs.set_measurement_system("metric")
        prefs.set_default_sheet_width_mm(1000.0)
        prefs.set_default_sheet_height_mm(2000.0)
        settings.hydrate_from_params()

        panel = SquatchCutTaskPanel()
        default_width_text = sc_units.format_length(1000.0, "metric")
        assert panel.sheet_widget.sheet_width_edit.text() == default_width_text

        preset_index = next(
            i for i, entry in enumerate(panel.sheet_widget._presets) if entry.get("id") == "1220x2440"
        )
        panel.sheet_widget.preset_combo.setCurrentIndex(preset_index)
        panel.sheet_widget._on_preset_changed(preset_index)

        assert panel.sheet_widget.sheet_width_edit.text() == sc_units.format_length(1220.0, "metric")
        assert panel.sheet_widget.sheet_height_edit.text() == sc_units.format_length(2440.0, "metric")
        assert math.isclose(prefs.get_default_sheet_width_mm(), 1000.0, rel_tol=1e-9)
        assert math.isclose(prefs.get_default_sheet_height_mm(), 2000.0, rel_tol=1e-9)

        second_panel = SquatchCutTaskPanel()
        assert second_panel.sheet_widget.sheet_width_edit.text() == default_width_text
        assert second_panel.sheet_widget.preset_combo.currentIndex() == 0
    finally:
        _restore_prefs(prefs, snap)


def test_settings_changes_persist_defaults_but_not_presets():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        _reset_session_state()
        prefs.clear_default_sheet_size()
        sc_units.set_units("in")
        prefs.set_measurement_system("imperial")
        settings.hydrate_from_params()

        before_panel = SquatchCutTaskPanel()
        baseline_presets = [entry["size"] for entry in before_panel.sheet_widget._presets if entry["size"]]

        settings_panel = SquatchCutSettingsPanel()
        settings_panel.sheet_width_edit.setText("60")
        settings_panel.sheet_height_edit.setText("110")
        assert settings_panel._apply_changes() is True
        settings.hydrate_from_params()

        reopened_settings = SquatchCutSettingsPanel()
        assert reopened_settings.sheet_width_edit.text() == sc_units.format_length(inches_to_mm(60.0), "imperial")
        assert reopened_settings.sheet_height_edit.text() == sc_units.format_length(inches_to_mm(110.0), "imperial")

        task_panel = SquatchCutTaskPanel()
        assert task_panel.sheet_widget.sheet_width_edit.text() == sc_units.format_length(inches_to_mm(60.0), "imperial")
        assert task_panel.sheet_widget.sheet_height_edit.text() == sc_units.format_length(inches_to_mm(110.0), "imperial")
        current_presets = [entry["size"] for entry in task_panel.sheet_widget._presets if entry["size"]]
        assert current_presets == baseline_presets
    finally:
        sc_units.set_units("mm")
        _restore_prefs(prefs, snap)


def test_metric_and_imperial_round_trip_defaults():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        _reset_session_state()
        prefs.set_measurement_system("metric")
        prefs.set_default_sheet_width_mm(1500.0)
        prefs.set_default_sheet_height_mm(3200.0)
        settings.hydrate_from_params()

        metric_panel = SquatchCutTaskPanel()
        assert metric_panel.sheet_widget.sheet_width_edit.text() == sc_units.format_length(1500.0, "metric")
        assert metric_panel.sheet_widget.sheet_height_edit.text() == sc_units.format_length(3200.0, "metric")

        prefs.set_measurement_system("imperial")
        prefs.set_default_sheet_width_in(48.0)
        prefs.set_default_sheet_height_in(96.0)
        settings.hydrate_from_params()
        sc_units.set_units("in")
        imperial_panel = SquatchCutSettingsPanel()
        assert imperial_panel.sheet_width_edit.text() == sc_units.format_length(inches_to_mm(48.0), "imperial")
        assert imperial_panel.sheet_height_edit.text() == sc_units.format_length(inches_to_mm(96.0), "imperial")
        assert math.isclose(prefs.get_default_sheet_width_mm(), 1500.0, rel_tol=1e-9)
        assert math.isclose(prefs.get_default_sheet_height_mm(), 3200.0, rel_tol=1e-9)

        prefs.set_measurement_system("metric")
        settings.hydrate_from_params()
        reopened_panel = SquatchCutTaskPanel()
        assert reopened_panel.sheet_widget.sheet_width_edit.text() == sc_units.format_length(1500.0, "metric")
        assert reopened_panel.sheet_widget.sheet_height_edit.text() == sc_units.format_length(3200.0, "metric")
        assert math.isclose(prefs.get_default_sheet_width_mm(), 1500.0, rel_tol=1e-9)
        assert math.isclose(prefs.get_default_sheet_height_mm(), 3200.0, rel_tol=1e-9)
    finally:
        _restore_prefs(prefs, snap)


def test_metric_and_imperial_defaults_do_not_overwrite_each_other():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        _reset_session_state()
        prefs.set_default_sheet_width_mm(1300.0)
        prefs.set_default_sheet_height_mm(2600.0)
        prefs.set_default_sheet_width_in(40.0)
        prefs.set_default_sheet_height_in(80.0)
        settings.hydrate_from_params()

        sc_units.set_units("mm")
        prefs.set_measurement_system("metric")
        panel_metric = SquatchCutSettingsPanel()
        panel_metric.sheet_width_edit.setText("1500")
        panel_metric.sheet_height_edit.setText("2700")
        assert panel_metric._apply_changes() is True
        metric_defaults = prefs.get_default_sheet_size_mm("metric")
        assert math.isclose(metric_defaults[0], 1500.0, rel_tol=1e-9)
        assert math.isclose(metric_defaults[1], 2700.0, rel_tol=1e-9)
        imperial_defaults = prefs.get_default_sheet_size_in("imperial")
        assert math.isclose(imperial_defaults[0], 40.0, rel_tol=1e-9)
        assert math.isclose(imperial_defaults[1], 80.0, rel_tol=1e-9)

        sc_units.set_units("in")
        prefs.set_measurement_system("imperial")
        panel_imperial = SquatchCutSettingsPanel()
        panel_imperial.sheet_width_edit.setText("60")
        panel_imperial.sheet_height_edit.setText("110")
        assert panel_imperial._apply_changes() is True
        imperial_defaults = prefs.get_default_sheet_size_in("imperial")
        metric_defaults = prefs.get_default_sheet_size_mm("metric")
        assert math.isclose(metric_defaults[0], 1500.0, rel_tol=1e-9)
        assert math.isclose(metric_defaults[1], 2700.0, rel_tol=1e-9)
        assert math.isclose(imperial_defaults[0], 60.0, rel_tol=1e-9)
        assert math.isclose(imperial_defaults[1], 110.0, rel_tol=1e-9)
    finally:
        sc_units.set_units("mm")
        _restore_prefs(prefs, snap)


def test_taskpanel_uses_system_specific_defaults_on_first_open():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        _reset_session_state()
        prefs.set_default_sheet_width_mm(1400.0)
        prefs.set_default_sheet_height_mm(2300.0)
        prefs.set_default_sheet_width_in(40.0)
        prefs.set_default_sheet_height_in(82.0)

        sc_units.set_units("mm")
        prefs.set_measurement_system("metric")
        settings.hydrate_from_params()
        panel_metric = SquatchCutTaskPanel()
        width_mm, height_mm = session_state.get_sheet_size()
        assert math.isclose(width_mm, 1400.0, rel_tol=1e-9)
        assert math.isclose(height_mm, 2300.0, rel_tol=1e-9)

        _reset_session_state()
        sc_units.set_units("in")
        prefs.set_measurement_system("imperial")
        settings.hydrate_from_params()
        panel_imperial = SquatchCutTaskPanel()
        width_mm, height_mm = session_state.get_sheet_size()
        assert math.isclose(width_mm, inches_to_mm(40.0), rel_tol=1e-9)
        assert math.isclose(height_mm, inches_to_mm(82.0), rel_tol=1e-9)
    finally:
        sc_units.set_units("mm")
        _restore_prefs(prefs, snap)


def test_job_sheet_persists_across_unit_toggle():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        _reset_session_state()
        prefs.set_default_sheet_width_mm(1500.0)
        prefs.set_default_sheet_height_mm(2800.0)
        prefs.set_default_sheet_width_in(50.0)
        prefs.set_default_sheet_height_in(100.0)
        sc_units.set_units("mm")
        prefs.set_measurement_system("metric")
        settings.hydrate_from_params()

        panel = SquatchCutTaskPanel()
        panel.sheet_widget.sheet_width_edit.setText(sc_units.format_length(1510.0, "metric"))
        panel.sheet_widget._validate_and_sync()
        panel.sheet_widget.sheet_height_edit.setText(sc_units.format_length(2810.0, "metric"))
        panel.sheet_widget._validate_and_sync()
        # _apply_settings_to_session doesn't exist on main panel anymore, changes are propagated immediately
        # via signals connected in __init__
        width_mm, height_mm = session_state.get_sheet_size()
        assert math.isclose(width_mm, 1510.0, rel_tol=1e-9)
        assert math.isclose(height_mm, 2810.0, rel_tol=1e-9)
        metric_text = panel.sheet_widget.sheet_width_edit.text()
        assert metric_text == sc_units.format_length(1510.0, "metric")

        index = panel.sheet_widget.units_combo.findData("imperial")
        assert index >= 0
        panel.sheet_widget.units_combo.setCurrentIndex(index)
        panel.sheet_widget._on_units_changed()
        # _on_units_changed is triggered by signal
        width_after, height_after = session_state.get_sheet_size()
        # Relax tolerance for round-trip through fractional inches
        assert math.isclose(width_after, width_mm, abs_tol=0.2)
        assert math.isclose(height_after, height_mm, abs_tol=0.2)
        assert panel.sheet_widget.sheet_width_edit.text() == sc_units.format_length(width_mm, "imperial")
    finally:
        sc_units.set_units("mm")
        _restore_prefs(prefs, snap)


def test_unit_toggle_swaps_defaults_when_using_system_default():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        _reset_session_state()
        prefs.set_default_sheet_width_mm(1220.0)
        prefs.set_default_sheet_height_mm(2440.0)
        prefs.set_default_sheet_width_in(48.0)
        prefs.set_default_sheet_height_in(96.0)
        sc_units.set_units("in")
        prefs.set_measurement_system("imperial")
        settings.hydrate_from_params()

        panel = SquatchCutTaskPanel()
        width_mm, height_mm = session_state.get_sheet_size()
        expected_imperial = prefs.get_default_sheet_size_mm("imperial")
        assert math.isclose(width_mm, expected_imperial[0], rel_tol=1e-9)
        assert math.isclose(height_mm, expected_imperial[1], rel_tol=1e-9)

        index = panel.sheet_widget.units_combo.findData("metric")
        assert index >= 0
        panel.sheet_widget.units_combo.setCurrentIndex(index)
        panel.sheet_widget._on_units_changed()
        # Signal triggers _on_units_changed automatically
        new_width, new_height = session_state.get_sheet_size()
        metric_defaults = prefs.get_default_sheet_size_mm("metric")

        assert math.isclose(new_width, metric_defaults[0], rel_tol=1e-9)
        assert math.isclose(new_height, metric_defaults[1], rel_tol=1e-9)
        assert panel.sheet_widget.sheet_width_edit.text() == sc_units.format_length(metric_defaults[0], "metric")
    finally:
        sc_units.set_units("mm")
        _restore_prefs(prefs, snap)


def test_settings_clear_only_affects_current_system():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        _reset_session_state()
        prefs.set_default_sheet_width_mm(1600.0)
        prefs.set_default_sheet_height_mm(3200.0)
        prefs.set_default_sheet_width_in(44.0)
        prefs.set_default_sheet_height_in(88.0)
        sc_units.set_units("mm")
        prefs.set_measurement_system("metric")
        settings.hydrate_from_params()

        panel_metric = SquatchCutSettingsPanel()
        panel_metric.sheet_width_edit.clear()
        panel_metric.sheet_height_edit.clear()
        assert panel_metric._apply_changes() is True
        metric_defaults = prefs.get_default_sheet_size_mm("metric")
        assert math.isclose(metric_defaults[0], prefs.METRIC_DEFAULT_WIDTH_MM, rel_tol=1e-9)
        assert math.isclose(metric_defaults[1], prefs.METRIC_DEFAULT_HEIGHT_MM, rel_tol=1e-9)
        imperial_defaults = prefs.get_default_sheet_size_in("imperial")
        assert math.isclose(imperial_defaults[0], 44.0, rel_tol=1e-9)
        assert math.isclose(imperial_defaults[1], 88.0, rel_tol=1e-9)
    finally:
        sc_units.set_units("mm")
        _restore_prefs(prefs, snap)


def test_legacy_single_default_migration():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    backup = dict(SquatchCutPreferences._local_shared)
    try:
        SquatchCutPreferences._local_shared.clear()
        SquatchCutPreferences._local_shared[prefs.METRIC_WIDTH_KEY] = 1700.0
        SquatchCutPreferences._local_shared[prefs.METRIC_HEIGHT_KEY] = 3400.0
        SquatchCutPreferences._local_shared[prefs._default_flag_key("metric")] = True
        SquatchCutPreferences._local_shared[prefs.SEPARATE_DEFAULTS_MIGRATED_KEY] = False

        migrated = SquatchCutPreferences()
        width_mm, height_mm = migrated.get_default_sheet_size_mm("metric")
        width_in, height_in = migrated.get_default_sheet_size_in("imperial")
        assert math.isclose(width_mm, 1700.0, rel_tol=1e-9)
        assert math.isclose(height_mm, 3400.0, rel_tol=1e-9)
        assert math.isclose(width_in, mm_to_inches(1700.0), rel_tol=1e-9)
        assert math.isclose(height_in, mm_to_inches(3400.0), rel_tol=1e-9)
    finally:
        SquatchCutPreferences._local_shared.clear()
        SquatchCutPreferences._local_shared.update(backup)
        _restore_prefs(prefs, snap)
