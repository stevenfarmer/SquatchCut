"""@codex
Tests for pure session_state helpers (sheet size, kerf/gap, last layout copies).
"""

import importlib

import SquatchCut.core.session_state as session_state
from SquatchCut.core.session_state import (
    set_sheet_size,
    get_sheet_size,
    set_kerf_mm,
    get_kerf_mm,
    set_gap_mm,
    get_gap_mm,
    set_last_layout,
    get_last_layout,
    set_default_allow_rotate,
    get_default_allow_rotate,
    set_job_allow_rotate,
    get_job_allow_rotate,
    clear_job_allow_rotate,
    set_panels,
    add_panels,
    get_panels,
    clear_panels,
    set_optimization_mode,
    get_optimization_mode,
    set_optimize_for_cut_path,
    get_optimize_for_cut_path,
    set_kerf_width_mm,
    get_kerf_width_mm,
    set_allowed_rotations_deg,
    get_allowed_rotations_deg,
    set_nesting_stats,
    get_nesting_stats,
    set_measurement_system,
    get_measurement_system,
)
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core.nesting import PlacedPart


def test_sheet_size_roundtrip():
    set_sheet_size(123.0, 456.0)
    w, h = get_sheet_size()
    assert w == 123.0
    assert h == 456.0


def test_kerf_and_gap_roundtrip():
    set_kerf_mm(3.5)
    set_gap_mm(1.25)
    assert get_kerf_mm() == 3.5
    assert get_gap_mm() == 1.25


def test_last_layout_roundtrip_is_copy():
    layout = [
        PlacedPart(
            id="p1",
            sheet_index=0,
            x=0.0,
            y=0.0,
            width=100.0,
            height=50.0,
            rotation_deg=0,
        )
    ]
    set_last_layout(layout)
    got = get_last_layout()
    # Contents equal
    assert len(got) == 1
    assert got[0].id == "p1"
    # But list should be a copy, not the same reference
    assert got is not layout


def test_last_layout_none_returns_none():
    set_last_layout(None)
    assert get_last_layout() is None


def test_default_allow_rotate_roundtrip():
    set_default_allow_rotate(True)
    assert get_default_allow_rotate() is True
    set_default_allow_rotate(False)
    assert get_default_allow_rotate() is False


def test_job_allow_rotate_roundtrip():
    clear_job_allow_rotate()
    assert get_job_allow_rotate() is None
    set_job_allow_rotate(True)
    assert get_job_allow_rotate() is True
    set_job_allow_rotate(False)
    assert get_job_allow_rotate() is False
    clear_job_allow_rotate()
    assert get_job_allow_rotate() is None


def test_panels_set_add_clear_are_copied():
    clear_panels()

    set_panels([{"id": "a"}])
    initial = get_panels()

    # Mutating the returned list should not affect stored panels
    initial.append({"id": "mutate"})
    assert get_panels() == [{"id": "a"}]

    add_panels(None)
    add_panels([])
    add_panels([{"id": "b"}])
    assert get_panels() == [{"id": "a"}, {"id": "b"}]

    clear_panels()
    assert get_panels() == []


def test_optimization_mode_roundtrip():
    set_optimization_mode("material")
    assert get_optimization_mode() == "material"
    set_optimization_mode("cuts")
    assert get_optimization_mode() == "cuts"
    # Invalid values fall back to material
    set_optimization_mode("bogus")
    assert get_optimization_mode() == "material"


def test_advanced_cut_settings_roundtrip():
    set_optimize_for_cut_path(True)
    assert get_optimize_for_cut_path() is True
    set_optimize_for_cut_path(False)
    assert get_optimize_for_cut_path() is False

    set_kerf_width_mm(4.2)
    assert get_kerf_width_mm() == 4.2

    set_allowed_rotations_deg((0, 90))
    assert get_allowed_rotations_deg() == (0, 90)
    set_allowed_rotations_deg([90])
    assert get_allowed_rotations_deg() == (90,)


def test_nesting_stats_roundtrip():
    set_nesting_stats(3, 12.5)
    stats = get_nesting_stats()
    assert stats["sheets_used"] == 3
    assert stats["cut_complexity"] == 12.5


def test_measurement_system_preferences_roundtrip():
    prefs = SquatchCutPreferences()
    prefs.set_measurement_system("imperial")
    assert prefs.get_measurement_system() == "imperial"
    prefs.set_measurement_system("metric")
    assert prefs.get_measurement_system() == "metric"


def test_session_state_defaults_after_reload():
    """Reload module to ensure pure-Python defaults stay intact without FreeCAD."""
    importlib.reload(session_state)
    assert session_state.get_sheet_size() == (None, None)
    assert session_state.get_gap_mm() == 0.0
    assert session_state.get_kerf_mm() == 0.0
    assert session_state.get_default_allow_rotate() is False
    assert session_state.get_job_allow_rotate() is None
    assert session_state.get_measurement_system() == "metric"


def test_measurement_system_rejects_invalid_values():
    importlib.reload(session_state)
    set_measurement_system("bogus")
    assert get_measurement_system() == "metric"
    set_measurement_system("imperial")
    assert get_measurement_system() == "imperial"
