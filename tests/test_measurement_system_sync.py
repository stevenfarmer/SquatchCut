from SquatchCut import settings
from SquatchCut.core import session_state
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel


def _snapshot_measurement_pref(prefs: SquatchCutPreferences) -> dict:
    return {
        "measurement_system": prefs.get_measurement_system(),
        "csv_units": prefs.get_csv_units("imperial"),
    }


def _restore_measurement_pref(prefs: SquatchCutPreferences, snapshot: dict) -> None:
    prefs.set_measurement_system(snapshot["measurement_system"])
    prefs.set_csv_units(snapshot["csv_units"])


def _reset_session_state() -> None:
    session_state.clear_sheet_size()
    session_state.clear_job_sheets()
    session_state.set_sheet_mode("simple")
    # Don't override measurement system - let hydration handle it


def test_csv_units_combo_is_locked_and_syncs_with_sheet_units():
    prefs = SquatchCutPreferences()
    snapshot = _snapshot_measurement_pref(prefs)
    try:
        prefs.set_measurement_system("imperial")
        prefs.set_csv_units("imperial")
        settings.hydrate_from_params()
        _reset_session_state()

        panel = SquatchCutTaskPanel()
        csv_combo = panel.input_widget.csv_units_combo
        is_enabled = getattr(csv_combo, "isEnabled", None)
        if callable(is_enabled):
            assert is_enabled() is False

        assert (
            panel.input_widget.get_csv_units() == session_state.get_measurement_system()
        )

        metric_idx = panel.sheet_widget.units_combo.findData("metric")
        assert metric_idx >= 0
        panel.sheet_widget.units_combo.setCurrentIndex(metric_idx)
        # Manually trigger the units change signal since qt_compat doesn't auto-emit
        panel.sheet_widget._on_units_changed()
        # Also trigger the main panel's units change handler to propagate to input widget
        panel._on_units_changed()

        assert panel.input_widget.get_csv_units() == "metric"
        assert session_state.get_measurement_system() == "metric"
        assert prefs.get_measurement_system() == "metric"
        assert prefs.get_csv_units("imperial") == "metric"
    finally:
        _restore_measurement_pref(prefs, snapshot)
        settings.hydrate_from_params()
