"""Color schemes and visual styling for nesting view."""

from __future__ import annotations

from typing import Dict, Tuple

# Color definitions as (R, G, B) tuples (0-255)
ColorRGB = Tuple[int, int, int]

# Color scheme definitions
COLOR_SCHEMES: Dict[str, Dict[str, ColorRGB]] = {
    "default": {
        # Soft blues and grays - works well with FreeCAD themes
        "sheet_outline": (70, 130, 180),  # Steel blue
        "sheet_fill": (173, 216, 230),  # Light blue (semi-transparent)
        "part_default": (100, 149, 237),  # Cornflower blue
        "part_rotated": (255, 165, 0),  # Orange for rotated parts
        "part_label": (25, 25, 112),  # Midnight blue
        "cut_lines": (105, 105, 105),  # Dim gray
        "waste_area": (255, 192, 203),  # Light pink
        "sheet_label": (47, 79, 79),  # Dark slate gray
    },
    "professional": {
        # Muted greens and browns - CAD-friendly
        "sheet_outline": (85, 107, 47),  # Dark olive green
        "sheet_fill": (144, 238, 144),  # Light green (semi-transparent)
        "part_default": (34, 139, 34),  # Forest green
        "part_rotated": (184, 134, 11),  # Dark goldenrod
        "part_label": (0, 100, 0),  # Dark green
        "cut_lines": (128, 128, 128),  # Gray
        "waste_area": (222, 184, 135),  # Burlywood
        "sheet_label": (101, 67, 33),  # Dark brown
    },
    "high_contrast": {
        # Black, white, yellow - accessibility focused
        "sheet_outline": (0, 0, 0),  # Black
        "sheet_fill": (255, 255, 255),  # White (semi-transparent)
        "part_default": (0, 0, 0),  # Black
        "part_rotated": (255, 255, 0),  # Yellow for rotated parts
        "part_label": (0, 0, 0),  # Black
        "cut_lines": (128, 128, 128),  # Gray
        "waste_area": (255, 255, 0),  # Yellow
        "sheet_label": (0, 0, 0),  # Black
    },
}


def get_color_scheme(scheme_name: str) -> Dict[str, ColorRGB]:
    """Get color scheme by name, falling back to default if not found."""
    return COLOR_SCHEMES.get(scheme_name, COLOR_SCHEMES["default"])


def rgb_to_freecad_color(rgb: ColorRGB) -> Tuple[float, float, float]:
    """Convert RGB (0-255) to FreeCAD color format (0.0-1.0)."""
    r, g, b = rgb
    return (r / 255.0, g / 255.0, b / 255.0)


def get_freecad_color(scheme_name: str, color_key: str) -> Tuple[float, float, float]:
    """Get a FreeCAD-compatible color from a scheme."""
    scheme = get_color_scheme(scheme_name)
    rgb = scheme.get(color_key, (128, 128, 128))  # Default to gray
    return rgb_to_freecad_color(rgb)


def get_transparency_for_display_mode(display_mode: str) -> float:
    """Get transparency value based on sheet display mode."""
    transparency_map = {
        "transparent": 0.7,  # 70% transparent
        "wireframe": 1.0,  # Fully transparent (wireframe only)
        "solid": 0.0,  # Opaque
    }
    return transparency_map.get(display_mode, 0.7)
