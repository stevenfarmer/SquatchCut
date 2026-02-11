from SquatchCut.core import sheet_presets


def test_preset_entries_start_with_none():
    entries = sheet_presets.get_preset_entries("imperial")
    assert entries, "Preset entries should not be empty"
    assert entries[0]["id"] is None
    assert entries[0]["size"] is None


def test_preset_selection_state_tracks_custom_entries():
    entries = sheet_presets.get_preset_entries("imperial")
    state = sheet_presets.PresetSelectionState()
    assert state.current_index == 0
    assert state.current_id is None

    state.set_index(2, entries)
    assert state.current_index == 2
    assert state.current_id == entries[2]["id"]

    state.clear()
    assert state.current_index == 0
    assert state.current_id is None


def test_preset_selection_state_clamps_range():
    entries = sheet_presets.get_preset_entries("imperial")
    state = sheet_presets.PresetSelectionState()
    state.set_index(999, entries)
    assert state.current_index == len(entries) - 1
    assert state.current_id == entries[-1]["id"]
