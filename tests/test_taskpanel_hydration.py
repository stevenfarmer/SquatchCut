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


def _reset_session_state() -> None:
    session_state.clear_sheet_size()
    session_state.set_measurement_system("metric")
    session_state.set_sheet_mode("simple")


def test_taskpanel_defaults_to_simple_sheet_mode():
    settings.hydrate_from_params()
    session_state.set_sheet_mode("simple")
    session_state.clear_job_sheets()
    panel = SquatchCutTaskPanel()
    assert panel.sheet_widget.sheet_mode_check.isChecked() is False
    assert session_state.get_sheet_mode() == "simple"


class _DocStub:
    def __init__(self, unit_label: str, width: float | None = None, height: float | None = None):
        self.Metadata = {"UnitSystem": unit_label}
        if width is not None:
            self.SquatchCutSheetWidth = float(width)
        if height is not None:
            self.SquatchCutSheetHeight = float(height)

    def addProperty(self, *_args, **_kwargs):
        return None

    def recompute(self):
        return None


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


def test_imperial_document_initializes_imperial_defaults():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_default_sheet_width_in(48.0)
        prefs.set_default_sheet_height_in(96.0)
        prefs.set_default_sheet_width_mm(1300.0)
        prefs.set_default_sheet_height_mm(2600.0)
        _reset_session_state()
        doc = _DocStub("Imperial (ft-in)")
        panel = SquatchCutTaskPanel(doc=doc)
        assert panel.measurement_system == "imperial"
        width_mm, height_mm = session_state.get_sheet_size()
        expected = prefs.get_default_sheet_size_mm("imperial")
        assert math.isclose(width_mm, expected[0], rel_tol=1e-9)
        assert math.isclose(height_mm, expected[1], rel_tol=1e-9)
        assert panel.sheet_widget.sheet_width_edit.text() == sc_units.format_length(expected[0], "imperial")
        assert getattr(doc, "SquatchCutSheetUnits", "") == "in"
    finally:
        _restore_prefs(prefs, snap)


def test_metric_document_initializes_metric_defaults():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_default_sheet_width_mm(1500.0)
        prefs.set_default_sheet_height_mm(3000.0)
        prefs.set_default_sheet_width_in(40.0)
        prefs.set_default_sheet_height_in(80.0)
        _reset_session_state()
        doc = _DocStub("Metric (mm)")
        panel = SquatchCutTaskPanel(doc=doc)
        assert panel.measurement_system == "metric"
        width_mm, height_mm = session_state.get_sheet_size()
        assert math.isclose(width_mm, 1500.0, rel_tol=1e-9)
        assert math.isclose(height_mm, 3000.0, rel_tol=1e-9)
        assert panel.sheet_widget.sheet_width_edit.text() == sc_units.format_length(1500.0, "metric")
        assert getattr(doc, "SquatchCutSheetUnits", "") == "mm"
    finally:
        _restore_prefs(prefs, snap)


def test_switching_documents_switches_modes_without_overwriting_defaults():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_default_sheet_width_mm(1800.0)
        prefs.set_default_sheet_height_mm(3200.0)
        prefs.set_default_sheet_width_in(60.0)
        prefs.set_default_sheet_height_in(110.0)
        _reset_session_state()

        doc_imperial = _DocStub("Imperial (ft-in)")
        panel_imperial = SquatchCutTaskPanel(doc=doc_imperial)
        assert panel_imperial.measurement_system == "imperial"
        width_imperial, height_imperial = session_state.get_sheet_size()
        expected_imperial = prefs.get_default_sheet_size_mm("imperial")
        assert math.isclose(width_imperial, expected_imperial[0], rel_tol=1e-9)
        assert math.isclose(height_imperial, expected_imperial[1], rel_tol=1e-9)

        doc_metric = _DocStub("Metric (mm)")
        panel_metric = SquatchCutTaskPanel(doc=doc_metric)
        assert panel_metric.measurement_system == "metric"
        width_metric, height_metric = session_state.get_sheet_size()
        assert math.isclose(width_metric, 1800.0, rel_tol=1e-9)
        assert math.isclose(height_metric, 3200.0, rel_tol=1e-9)

        assert math.isclose(prefs.get_default_sheet_width_in(), 60.0, rel_tol=1e-9)
        assert math.isclose(prefs.get_default_sheet_height_in(), 110.0, rel_tol=1e-9)
        assert math.isclose(prefs.get_default_sheet_width_mm(), 1800.0, rel_tol=1e-9)
        assert math.isclose(prefs.get_default_sheet_height_mm(), 3200.0, rel_tol=1e-9)
    finally:
        _restore_prefs(prefs, snap)


def test_job_sheet_mm_stays_constant_when_document_units_change():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_default_sheet_width_mm(1600.0)
        prefs.set_default_sheet_height_mm(2800.0)
        prefs.set_default_sheet_width_in(60.0)
        prefs.set_default_sheet_height_in(120.0)
        _reset_session_state()
        doc = _DocStub("Metric (mm)", width=1400.0, height=2600.0)

        panel_metric = SquatchCutTaskPanel(doc=doc)
        assert panel_metric.measurement_system == "metric"
        width_metric, height_metric = session_state.get_sheet_size()
        assert math.isclose(width_metric, 1400.0, rel_tol=1e-9)
        assert math.isclose(height_metric, 2600.0, rel_tol=1e-9)

        doc.Metadata["UnitSystem"] = "Imperial (ft-in)"
        panel_imperial = SquatchCutTaskPanel(doc=doc)
        assert panel_imperial.measurement_system == "imperial"
        width_after, height_after = session_state.get_sheet_size()
        assert math.isclose(width_after, 1400.0, rel_tol=1e-9)
        assert math.isclose(height_after, 2600.0, rel_tol=1e-9)
        assert panel_imperial.sheet_widget.sheet_width_edit.text() == sc_units.format_length(1400.0, "imperial")
    finally:
        _restore_prefs(prefs, snap)


def test_ui_displays_correct_format_after_document_switch():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_default_sheet_width_mm(1220.0)
        prefs.set_default_sheet_height_mm(2440.0)
        prefs.set_default_sheet_width_in(48.0)
        prefs.set_default_sheet_height_in(96.0)
        _reset_session_state()

        doc_imperial = _DocStub("Imperial (ft-in)")
        panel_imperial = SquatchCutTaskPanel(doc=doc_imperial)
        expected_imperial = prefs.get_default_sheet_size_mm("imperial")
        assert panel_imperial.sheet_widget.sheet_width_edit.text() == sc_units.format_length(expected_imperial[0], "imperial")

        doc_metric = _DocStub("Metric (mm)")
        panel_metric = SquatchCutTaskPanel(doc=doc_metric)
        assert panel_metric.sheet_widget.sheet_width_edit.text() == sc_units.format_length(1220.0, "metric")
    finally:
        _restore_prefs(prefs, snap)


def test_job_sheets_persist_across_mode_toggle_and_unit_change():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        settings.hydrate_from_params()
        session_state.clear_job_sheets()
        session_state.set_sheet_mode("job_sheets")
        custom_sheets = [
            {"width_mm": 400.0, "height_mm": 800.0, "quantity": 1, "label": "Half"},
            {"width_mm": 600.0, "height_mm": 1200.0, "quantity": 2, "label": "Full"},
        ]
        session_state.set_job_sheets(custom_sheets)
        panel = SquatchCutTaskPanel()

        initial_sheets = session_state.get_job_sheets()
        assert len(initial_sheets) == 2

        panel.sheet_widget.sheet_mode_check.setChecked(False)
        panel.sheet_widget._on_sheet_mode_toggled(False)
        assert session_state.get_sheet_mode() == "simple"
        assert session_state.get_job_sheets() == initial_sheets

        panel.sheet_widget.sheet_mode_check.setChecked(True)
        panel.sheet_widget._on_sheet_mode_toggled(True)
        assert session_state.get_sheet_mode() == "job_sheets"
        assert session_state.get_job_sheets() == initial_sheets

        idx = panel.sheet_widget.units_combo.findData("imperial")
        assert idx >= 0
        panel.sheet_widget.units_combo.setCurrentIndex(idx)
        panel.sheet_widget._on_units_changed()
        assert session_state.get_job_sheets() == initial_sheets
    finally:
        _restore_prefs(prefs, snap)
        session_state.clear_job_sheets()
        session_state.set_sheet_mode("simple")


def test_cut_mode_warning_shown_with_multiple_job_sheets():
    settings.hydrate_from_params()
    _reset_session_state()
    try:
        session_state.set_sheet_mode("job_sheets")
        session_state.set_job_sheets(
            [
                {"width_mm": 300.0, "height_mm": 400.0, "quantity": 1},
                {"width_mm": 600.0, "height_mm": 400.0, "quantity": 1},
            ]
        )
        panel = SquatchCutTaskPanel()
        panel.nesting_widget.cut_mode_check.setChecked(True)
        panel.update_run_button_state()
        assert panel._sheet_warning_active is True
        assert "Advanced job sheets" in panel.sheet_warning_label.text()
    finally:
        _reset_session_state()
        session_state.clear_job_sheets()


def test_warning_shown_for_cuts_mode_when_multiple_sheets_active():
    settings.hydrate_from_params()
    _reset_session_state()
    try:
        session_state.set_sheet_mode("job_sheets")
        session_state.set_job_sheets(
            [
                {"width_mm": 400.0, "height_mm": 800.0, "quantity": 2},
            ]
        )
        panel = SquatchCutTaskPanel()
        panel.nesting_widget.cut_mode_check.setChecked(False)
        idx = panel.nesting_widget.mode_combo.findData("cuts")
        assert idx >= 0
        panel.nesting_widget.mode_combo.setCurrentIndex(idx)
        panel.update_run_button_state()
        assert panel._sheet_warning_active is True
    finally:
        _reset_session_state()
        session_state.clear_job_sheets()


def test_sheet_warning_hidden_when_advanced_disabled():
    settings.hydrate_from_params()
    _reset_session_state()
    try:
        session_state.set_sheet_mode("simple")
        session_state.clear_job_sheets()
        panel = SquatchCutTaskPanel()
        panel.nesting_widget.cut_mode_check.setChecked(True)
        panel.update_run_button_state()
        assert panel._sheet_warning_active is False
    finally:
        _reset_session_state()


def test_sheet_warning_banner_container_initialized_hidden():
    settings.hydrate_from_params()
    panel = SquatchCutTaskPanel()
    container = getattr(panel, "sheet_warning_container", None)
    assert container is not None
    assert panel._sheet_warning_active is False
