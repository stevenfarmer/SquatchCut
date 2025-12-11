import math

import pytest

from SquatchCut.core import units as sc_units
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.gui.taskpanel_settings import SquatchCutSettingsPanel

# Helper to isolate tests
@pytest.fixture
def isolated_prefs():
    prefs = SquatchCutPreferences()
    backup = dict(SquatchCutPreferences._local_shared)

    # Reset state
    SquatchCutPreferences._local_shared.clear()
    # Re-init to trigger _ensure_default_storage and migration logic
    # We want to simulate a clean state.
    # But _ensure_default_storage runs in __init__.

    # Let's manually populate factory defaults as if fresh install
    prefs._set_metric_defaults(prefs.METRIC_DEFAULT_WIDTH_MM, prefs.METRIC_DEFAULT_HEIGHT_MM)
    prefs._set_imperial_defaults(prefs.IMPERIAL_DEFAULT_WIDTH_IN, prefs.IMPERIAL_DEFAULT_HEIGHT_IN)
    prefs._set_float(prefs.METRIC_KERF_KEY, prefs.METRIC_DEFAULT_KERF_MM)
    prefs._set_float(prefs.IMPERIAL_KERF_KEY, prefs.IMPERIAL_DEFAULT_KERF_IN)
    prefs._set_float(prefs.METRIC_SPACING_KEY, prefs.METRIC_DEFAULT_SPACING_MM)
    prefs._set_float(prefs.IMPERIAL_SPACING_KEY, prefs.IMPERIAL_DEFAULT_SPACING_IN)

    # Mark migrations as done to prevent overwrite during test
    prefs._set_bool(prefs.SEPARATE_DEFAULTS_MIGRATED_KEY, True)
    prefs._set_bool(prefs.KERF_DEFAULTS_MIGRATED_KEY, True)

    prefs.set_measurement_system("metric")

    yield prefs

    SquatchCutPreferences._local_shared.clear()
    SquatchCutPreferences._local_shared.update(backup)

def test_kerf_defaults_bleed_metric_to_imperial(isolated_prefs):
    """
    Reproduce issue: Switching to Imperial in Settings shows converted Metric Kerf
    instead of Imperial Kerf default.
    """
    prefs = isolated_prefs

    # Set explicit Metric Kerf (e.g. 5.0mm) which is approx 0.197 inches
    # Imperial Default is 0.125 inches.
    prefs.set_default_kerf_mm(5.0, system="metric")

    # Ensure Imperial is still factory default (0.125)
    # Note: set_default_kerf_mm(5.0, "metric") updates "MetricKerfMM" AND "DefaultKerfMM"
    # But should NOT update "ImperialKerfIn".
    imperial_kerf_stored = prefs.get_default_kerf_mm(system="imperial")
    assert math.isclose(imperial_kerf_stored, 3.175, rel_tol=1e-4), "Stored Imperial Kerf should be 0.125in (3.175mm)"

    # Open Settings Panel (defaults to Metric)
    panel = SquatchCutSettingsPanel()

    # Assert initial UI shows 5.0mm
    assert panel.kerf_edit.text() == "5"

    # Switch to Imperial
    idx = panel.units_combo.findData("imperial")
    panel.units_combo.setCurrentIndex(idx)
    # The signal isn't auto-connected in test without main loop?
    # In TaskPanel_Settings, it connects: self.units_combo.currentIndexChanged.connect(self._on_units_changed)
    # QComboBox signals usually fire immediately in tests if changed programmatically.
    # But let's call it manually to be safe and consistent with existing tests.
    panel._on_units_changed()

    # Check what is displayed in Kerf box.
    # EXPECTED (Fixed): Should show 1/8" (or 0.125)
    # ACTUAL (Bug): Shows converted 5mm -> ~0.197"
    text = panel.kerf_edit.text()

    # We assert the BUG exists currently (so we expect failure or we assert for the bug behavior to confirm repro)
    # Let's assert for CORRECT behavior, so the test FAILS.

    # 0.125 inches
    expected_val_mm = 3.175
    actual_val_mm = sc_units.parse_length(text, "imperial")

    print(f"DEBUG: Text '{text}' -> {actual_val_mm} mm. Expected {expected_val_mm} mm")

    assert math.isclose(actual_val_mm, expected_val_mm, rel_tol=1e-4), \
        f"Bleed detected! Expected Imperial default 1/8\" (3.175mm), got {text}"

def test_gap_defaults_bleed_imperial_to_metric(isolated_prefs):
    """
    Reproduce issue: Switching to Metric in Settings shows converted Imperial Gap
    instead of Metric Gap default.
    """
    prefs = isolated_prefs
    sc_units.set_units("in")
    prefs.set_measurement_system("imperial")

    # Set Imperial Gap to 1 inch (25.4mm)
    prefs.set_default_spacing_mm(25.4, system="imperial")

    # Ensure Metric Gap is still factory default (0.0mm)
    metric_gap_stored = prefs.get_default_spacing_mm(system="metric")
    assert metric_gap_stored == 0.0

    panel = SquatchCutSettingsPanel()

    # Assert initial UI shows 25.4 (Gap is always mm in UI)
    assert "25.4" in panel.gap_edit.text()

    # Switch to Metric
    idx = panel.units_combo.findData("metric")
    panel.units_combo.setCurrentIndex(idx)
    panel._on_units_changed()

    # Check displayed Gap
    # EXPECTED (Fixed): 0
    # ACTUAL (Bug): 25.4
    text = panel.gap_edit.text()
    val = float(text) if text else 0.0

    assert val == 0.0, f"Bleed detected! Expected Metric default 0.0, got {val}"

def test_fallback_logic_must_be_removed(isolated_prefs):
    """
    Verify fallback logic is removed.
    If we delete Imperial defaults, getting Imperial defaults should NOT fallback to Metric.
    It should return Factory Imperial defaults (or None/Error if we want strictness,
    but user asked to remove fallback to OTHER system. Returning Factory is safe).
    """
    prefs = isolated_prefs

    # Set Metric Width to 1000mm
    prefs.set_default_sheet_width_mm(1000.0)

    # Delete Imperial Width key
    if prefs.IMPERIAL_WIDTH_KEY in prefs._local:
        del prefs._local[prefs.IMPERIAL_WIDTH_KEY]

    # Try to get Imperial Width
    # Current behavior: Falls back to Metric (1000mm -> 39.37")
    # Desired behavior: Factory Imperial (48" -> 1219.2mm)

    width_in = prefs.get_default_sheet_width_in()

    # 48 inches
    assert math.isclose(width_in, 48.0, rel_tol=1e-9), \
        f"Fallback detected! Expected 48.0, got {width_in}"
