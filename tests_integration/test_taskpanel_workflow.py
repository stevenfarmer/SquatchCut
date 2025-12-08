"""Integration tests for TaskPanel behavior inside FreeCAD."""

import pytest

pytest.importorskip("FreeCAD")
pytest.importorskip("FreeCADGui")

import FreeCAD  # type: ignore
from SquatchCut import settings
from SquatchCut.core import units as sc_units
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel


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


def test_taskpanel_uses_saved_defaults_in_imperial():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("imperial")
        prefs.set_default_sheet_width_in(48.0)
        prefs.set_default_sheet_height_in(96.0)
        prefs.set_default_kerf_mm(sc_units.inches_to_mm(0.125))
        settings.hydrate_from_params()

        panel = SquatchCutTaskPanel()
        assert panel.preset_combo.currentIndex() == 0
        assert "48" in panel.sheet_width_edit.text()
        assert "96" in panel.sheet_height_edit.text()
        assert panel.kerf_edit.text().strip() in {"1/8", "0.125", "1/8\""} or "1/8" in panel.kerf_edit.text()
    finally:
        _restore_prefs(prefs, snap)


def test_units_toggle_reformats_fields():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("metric")
        prefs.set_default_sheet_width_mm(1200.0)
        prefs.set_default_sheet_height_mm(2400.0)
        prefs.set_default_kerf_mm(3.0)
        settings.hydrate_from_params()

        panel = SquatchCutTaskPanel()
        # Switch to imperial
        idx = panel.units_combo.findData("imperial")
        assert idx >= 0
        panel.units_combo.setCurrentIndex(idx)
        panel._on_units_changed()
        assert panel.measurement_system == "imperial"
        assert "48" in panel.sheet_width_edit.text() or "47" in panel.sheet_width_edit.text()
        assert panel.kerf_edit.text()
    finally:
        _restore_prefs(prefs, snap)


def test_rotation_default_initial_state():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_default_allow_rotate(False)
        settings.hydrate_from_params()
        panel = SquatchCutTaskPanel()
        assert not panel.job_allow_rotation_check.isChecked()

        prefs.set_default_allow_rotate(True)
        settings.hydrate_from_params()
        panel2 = SquatchCutTaskPanel()
        assert panel2.job_allow_rotation_check.isChecked()
    finally:
        _restore_prefs(prefs, snap)
