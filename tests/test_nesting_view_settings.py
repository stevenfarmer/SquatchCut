"""Tests for nesting view settings in preferences and TaskPanel."""

import pytest
from SquatchCut.core.preferences import SquatchCutPreferences


@pytest.fixture(autouse=True)
def reset_preferences():
    """Reset preferences to defaults before each test to ensure isolation."""
    # Clear the shared local dictionary
    SquatchCutPreferences._local_shared.clear()
    yield
    # Clean up after test
    SquatchCutPreferences._local_shared.clear()


def test_nesting_view_preferences_defaults():
    """Test that nesting view preferences have correct default values."""
    prefs = SquatchCutPreferences()

    # Test defaults match our specified values
    assert prefs.get_nesting_sheet_display_mode() == "transparent"
    assert prefs.get_nesting_sheet_layout() == "side_by_side"
    assert prefs.get_nesting_color_scheme() == "default"
    assert prefs.get_nesting_show_part_labels() is True
    assert prefs.get_nesting_show_cut_lines() is False
    assert prefs.get_nesting_show_waste_areas() is False
    assert prefs.get_nesting_simplified_view() is False


def test_nesting_view_preferences_set_get():
    """Test setting and getting nesting view preferences."""
    prefs = SquatchCutPreferences()

    # Test sheet display mode
    prefs.set_nesting_sheet_display_mode("wireframe")
    assert prefs.get_nesting_sheet_display_mode() == "wireframe"

    prefs.set_nesting_sheet_display_mode("solid")
    assert prefs.get_nesting_sheet_display_mode() == "solid"

    # Test invalid value falls back to default
    prefs.set_nesting_sheet_display_mode("invalid")
    assert prefs.get_nesting_sheet_display_mode() == "transparent"

    # Test sheet layout
    prefs.set_nesting_sheet_layout("stacked")
    assert prefs.get_nesting_sheet_layout() == "stacked"

    prefs.set_nesting_sheet_layout("auto")
    assert prefs.get_nesting_sheet_layout() == "auto"

    # Test color scheme
    prefs.set_nesting_color_scheme("professional")
    assert prefs.get_nesting_color_scheme() == "professional"

    prefs.set_nesting_color_scheme("high_contrast")
    assert prefs.get_nesting_color_scheme() == "high_contrast"

    # Test boolean settings
    prefs.set_nesting_show_part_labels(False)
    assert prefs.get_nesting_show_part_labels() is False

    prefs.set_nesting_show_cut_lines(True)
    assert prefs.get_nesting_show_cut_lines() is True

    prefs.set_nesting_show_waste_areas(True)
    assert prefs.get_nesting_show_waste_areas() is True

    prefs.set_nesting_simplified_view(True)
    assert prefs.get_nesting_simplified_view() is True


def test_nesting_view_preferences_validation():
    """Test that invalid values are handled correctly."""
    prefs = SquatchCutPreferences()

    # Test invalid sheet display modes
    invalid_modes = ["invalid", "", "TRANSPARENT", "wire_frame"]
    for mode in invalid_modes:
        prefs.set_nesting_sheet_display_mode(mode)
        assert prefs.get_nesting_sheet_display_mode() == "transparent"

    # Test invalid sheet layouts
    invalid_layouts = ["invalid", "", "SIDE_BY_SIDE", "side-by-side"]
    for layout in invalid_layouts:
        prefs.set_nesting_sheet_layout(layout)
        assert prefs.get_nesting_sheet_layout() == "side_by_side"

    # Test invalid color schemes
    invalid_schemes = ["invalid", "", "DEFAULT", "high-contrast"]
    for scheme in invalid_schemes:
        prefs.set_nesting_color_scheme(scheme)
        assert prefs.get_nesting_color_scheme() == "default"


def test_nesting_view_preferences_persistence():
    """Test that preferences persist across instances."""
    prefs1 = SquatchCutPreferences()

    # Set some values
    prefs1.set_nesting_sheet_display_mode("wireframe")
    prefs1.set_nesting_sheet_layout("stacked")
    prefs1.set_nesting_color_scheme("professional")
    prefs1.set_nesting_show_part_labels(False)
    prefs1.set_nesting_show_cut_lines(True)

    # Create new instance and verify values persist
    prefs2 = SquatchCutPreferences()
    assert prefs2.get_nesting_sheet_display_mode() == "wireframe"
    assert prefs2.get_nesting_sheet_layout() == "stacked"
    assert prefs2.get_nesting_color_scheme() == "professional"
    assert prefs2.get_nesting_show_part_labels() is False
    assert prefs2.get_nesting_show_cut_lines() is True
