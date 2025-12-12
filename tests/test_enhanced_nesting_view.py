"""Tests for enhanced nesting view with colors, labels, and sheet boundaries."""

import pytest
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.gui.nesting_colors import (
    COLOR_SCHEMES,
    get_color_scheme,
    get_freecad_color,
    get_transparency_for_display_mode,
    rgb_to_freecad_color,
)


def test_color_schemes_exist():
    """Test that all required color schemes are defined."""
    required_schemes = ["default", "professional", "high_contrast"]
    for scheme in required_schemes:
        assert scheme in COLOR_SCHEMES

    # Test that each scheme has all required colors
    required_colors = [
        "sheet_outline",
        "sheet_fill",
        "part_default",
        "part_rotated",
        "part_label",
        "cut_lines",
        "waste_area",
        "sheet_label",
    ]

    for scheme_name, scheme in COLOR_SCHEMES.items():
        for color_key in required_colors:
            assert color_key in scheme, f"Missing {color_key} in {scheme_name} scheme"


def test_rgb_to_freecad_color():
    """Test RGB to FreeCAD color conversion."""
    # Test black
    assert rgb_to_freecad_color((0, 0, 0)) == (0.0, 0.0, 0.0)

    # Test white
    assert rgb_to_freecad_color((255, 255, 255)) == (1.0, 1.0, 1.0)

    # Test mid-gray
    assert rgb_to_freecad_color((128, 128, 128)) == pytest.approx(
        (0.502, 0.502, 0.502), abs=0.01
    )


def test_get_color_scheme():
    """Test color scheme retrieval with fallback."""
    # Test valid scheme
    default_scheme = get_color_scheme("default")
    assert "sheet_outline" in default_scheme

    # Test invalid scheme falls back to default
    invalid_scheme = get_color_scheme("nonexistent")
    assert invalid_scheme == COLOR_SCHEMES["default"]


def test_get_freecad_color():
    """Test getting FreeCAD-compatible colors from schemes."""
    # Test valid scheme and color
    color = get_freecad_color("default", "sheet_outline")
    assert isinstance(color, tuple)
    assert len(color) == 3
    assert all(0.0 <= c <= 1.0 for c in color)

    # Test invalid color key returns gray
    gray_color = get_freecad_color("default", "nonexistent")
    expected_gray = rgb_to_freecad_color((128, 128, 128))
    assert gray_color == expected_gray


def test_get_transparency_for_display_mode():
    """Test transparency values for different display modes."""
    assert get_transparency_for_display_mode("transparent") == 0.7
    assert get_transparency_for_display_mode("wireframe") == 1.0
    assert get_transparency_for_display_mode("solid") == 0.0
    assert get_transparency_for_display_mode("invalid") == 0.7  # Default


def test_nesting_view_preferences_integration():
    """Test that nesting view preferences work with color system."""
    prefs = SquatchCutPreferences()

    # Test that we can get colors for each preference setting
    for scheme_name in ["default", "professional", "high_contrast"]:
        prefs.set_nesting_color_scheme(scheme_name)
        assert prefs.get_nesting_color_scheme() == scheme_name

        # Test that we can get colors for this scheme
        color = get_freecad_color(scheme_name, "part_default")
        assert isinstance(color, tuple)
        assert len(color) == 3


def test_color_scheme_accessibility():
    """Test that high contrast scheme uses appropriate colors."""
    high_contrast = get_color_scheme("high_contrast")

    # High contrast should use black, white, and yellow primarily
    sheet_outline = high_contrast["sheet_outline"]
    sheet_fill = high_contrast["sheet_fill"]
    part_rotated = high_contrast["part_rotated"]

    # Sheet outline should be black
    assert sheet_outline == (0, 0, 0)

    # Sheet fill should be white
    assert sheet_fill == (255, 255, 255)

    # Rotated parts should be yellow for visibility
    assert part_rotated == (255, 255, 0)


def test_professional_color_scheme():
    """Test that professional scheme uses muted colors."""
    professional = get_color_scheme("professional")

    # Professional scheme should use greens and browns
    part_default = professional["part_default"]
    sheet_outline = professional["sheet_outline"]

    # Should be green-ish (G component higher than R and B)
    r, g, b = part_default
    assert g > r and g > b, "Professional part color should be green-ish"

    # Sheet outline should be olive/brown-ish
    r, g, b = sheet_outline
    assert r < 100 and g > r, "Professional sheet outline should be olive-ish"
