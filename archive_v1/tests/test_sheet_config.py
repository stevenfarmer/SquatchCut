"""Core sheet configuration behaviors (presets, defaults) without FreeCAD deps."""

from SquatchCut.core import sheet_presets


def test_initial_sheet_size_prefers_session_then_user_then_factory():
    # Session size wins
    size = sheet_presets.get_initial_sheet_size(
        "metric", session_size=(111.0, 222.0), user_default_size=(333.0, 444.0)
    )
    assert size == (111.0, 222.0)

    # User default used when session is empty
    size = sheet_presets.get_initial_sheet_size(
        "metric", session_size=(None, None), user_default_size=(333.0, 444.0)
    )
    assert size == (333.0, 444.0)

    # Factory default when nothing else is set
    size = sheet_presets.get_initial_sheet_size(
        "metric", session_size=(None, None), user_default_size=(None, None)
    )
    assert size == sheet_presets.get_factory_default_sheet_size("metric")


def test_find_matching_preset_uses_tolerance():
    preset = sheet_presets.get_presets_for_system("imperial")[0]
    width = preset["width_mm"] + sheet_presets.DEFAULT_MATCH_TOLERANCE_MM / 2
    height = preset["height_mm"]
    match = sheet_presets.find_matching_preset("imperial", width, height)
    assert match is not None
    assert match["id"] == preset["id"]

    # Outside tolerance should not match
    width = preset["width_mm"] + sheet_presets.DEFAULT_MATCH_TOLERANCE_MM * 2
    assert sheet_presets.find_matching_preset("imperial", width, height) is None


def test_preset_selection_state_clamps_and_clears():
    entries = sheet_presets.get_preset_entries("metric")
    state = sheet_presets.PresetSelectionState()

    # Clamp index to last entry
    idx = state.set_index(999, entries)
    assert idx == len(entries) - 1
    assert state.current_id == entries[-1]["id"]

    # Clear resets to None selection
    state.clear()
    assert state.current_index == 0
    assert state.current_id is None
