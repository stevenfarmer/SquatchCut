from SquatchCut import settings
from SquatchCut.core import session_state, sheet_presets
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core.units import inches_to_mm, mm_to_inches


def test_factory_defaults_per_unit_system():
    metric = sheet_presets.get_factory_default_sheet_size("metric")
    imperial = sheet_presets.get_factory_default_sheet_size("imperial")

    assert metric == (1220.0, 2440.0)
    assert abs(imperial[0] - inches_to_mm(48.0)) < 1e-6
    assert abs(imperial[1] - inches_to_mm(96.0)) < 1e-6


def test_exact_preset_match_requires_precision():
    preset = sheet_presets.find_matching_preset(
        "imperial",
        inches_to_mm(48.0),
        inches_to_mm(96.0),
    )
    assert preset is not None
    assert preset["id"] == "4x8"


def test_custom_sizes_do_not_match_presets():
    preset = sheet_presets.find_matching_preset(
        "imperial",
        inches_to_mm(48.5),
        inches_to_mm(96.0),
    )
    assert preset is None


def test_manual_custom_size_does_not_select_preset():
    manual_size = (inches_to_mm(48.5625), inches_to_mm(96.5625))  # 48 9/16 x 96 9/16
    initial = sheet_presets.get_initial_sheet_size(
        "imperial",
        session_size=(None, None),
        user_default_size=manual_size,
    )
    assert initial == manual_size
    assert sheet_presets.find_matching_preset("imperial", *initial) is None


def test_preset_selection_sets_expected_dimensions():
    for system in ("imperial", "metric"):
        for preset in sheet_presets.get_presets_for_system(system):
            size = sheet_presets.apply_preset(system, preset["id"])
            assert size is not None
            width, height = size
            assert abs(width - preset["width_mm"]) < 1e-6
            assert abs(height - preset["height_mm"]) < 1e-6
            match = sheet_presets.find_matching_preset(system, width, height)
            assert match is not None
            assert match["id"] == preset["id"]


def test_preset_lists_match_expected_values():
    imperial_ids = [preset["id"] for preset in sheet_presets.get_presets_for_system("imperial")]
    assert imperial_ids == ["4x8", "2x4", "5x10"]
    metric_ids = [preset["id"] for preset in sheet_presets.get_presets_for_system("metric")]
    assert metric_ids == ["1220x2440", "1220x3050", "1500x3000"]


def test_reopen_panel_restores_sheet_and_preset_state():
    system = "imperial"
    preset_size = sheet_presets.apply_preset(system, "4x8")
    assert preset_size is not None
    session_size = preset_size
    initial = sheet_presets.get_initial_sheet_size(
        system,
        session_size=session_size,
        user_default_size=(None, None),
    )
    assert initial == preset_size
    match = sheet_presets.find_matching_preset(system, *initial)
    assert match is not None
    assert match["id"] == "4x8"

    custom = (inches_to_mm(48.5625), inches_to_mm(96.5625))
    initial_custom = sheet_presets.get_initial_sheet_size(
        system,
        session_size=(None, None),
        user_default_size=custom,
    )
    assert initial_custom == custom
    assert sheet_presets.find_matching_preset(system, *initial_custom) is None


def test_user_defaults_override_factory_defaults():
    prefs = SquatchCutPreferences()
    orig_system = prefs.get_measurement_system()
    orig_width = prefs.get_default_sheet_width_mm()
    orig_height = prefs.get_default_sheet_height_mm()
    try:
        prefs.set_measurement_system("imperial")
        prefs.set_default_sheet_width_in(mm_to_inches(1300.0))
        prefs.set_default_sheet_height_in(mm_to_inches(2500.0))
        settings.hydrate_from_params()

        width, height = session_state.get_sheet_size()
        assert abs(width - 1300.0) < 1e-6
        assert abs(height - 2500.0) < 1e-6
    finally:
        prefs.set_measurement_system(orig_system)
        prefs.set_default_sheet_width_mm(orig_width)
        prefs.set_default_sheet_height_mm(orig_height)
        settings.hydrate_from_params()


def test_user_defaults_persist_across_reinitialization():
    prefs = SquatchCutPreferences()
    orig_system = prefs.get_measurement_system()
    orig_width = prefs.get_default_sheet_width_mm()
    orig_height = prefs.get_default_sheet_height_mm()
    try:
        prefs.set_measurement_system("metric")
        prefs.set_default_sheet_width_mm(1300.0)
        prefs.set_default_sheet_height_mm(2500.0)
        settings.hydrate_from_params()
        # force another hydrate round with a different measurement system
        prefs.set_measurement_system("imperial")
        settings.hydrate_from_params()
        assert abs(prefs.get_default_sheet_width_mm() - 1300.0) < 1e-6
        assert abs(prefs.get_default_sheet_height_mm() - 2500.0) < 1e-6
    finally:
        prefs.set_measurement_system(orig_system)
        prefs.set_default_sheet_width_mm(orig_width)
        prefs.set_default_sheet_height_mm(orig_height)
        settings.hydrate_from_params()
