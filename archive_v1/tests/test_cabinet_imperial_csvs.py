"""Tests for cabinet-sized imperial CSV files to ensure multi-sheet nesting works correctly."""

from pathlib import Path

import pytest
from SquatchCut.core.csv_import import validate_csv_file
from SquatchCut.core.nesting import Part, nest_parts
from SquatchCut.core.units import inches_to_mm


def csv_to_parts(csv_path: str, measurement_system: str = "metric") -> list[Part]:
    """Convert CSV file to list of Part objects."""
    parts_data, errors = validate_csv_file(csv_path, csv_units=measurement_system)
    if errors:
        raise ValueError(f"CSV validation errors: {errors}")

    parts = []
    for part_data in parts_data:
        # The validate_csv_file already converts to mm, so just use the values directly
        width_mm = float(part_data["width"])
        height_mm = float(part_data["height"])

        # Handle quantity by creating multiple parts
        qty = int(part_data.get("qty", 1))
        can_rotate = bool(part_data.get("allow_rotate", False))

        for i in range(qty):
            part_id = part_data["id"]
            if qty > 1:
                part_id = f"{part_id}_{i+1}"

            parts.append(
                Part(
                    id=part_id, width=width_mm, height=height_mm, can_rotate=can_rotate
                )
            )

    return parts


class TestCabinetImperialCSVs:
    """Test cabinet-sized imperial CSV files for realistic woodworking scenarios."""

    @pytest.fixture
    def csv_dir(self):
        """Return path to test CSV directory."""
        return Path(__file__).parent.parent / "freecad" / "testing" / "csv"

    @pytest.fixture
    def standard_plywood_sheet(self):
        """Standard 4x8 plywood sheet in mm."""
        return inches_to_mm(48), inches_to_mm(96)

    def test_kitchen_cabinet_csv_import(self, csv_dir):
        """Test that kitchen cabinet CSV imports correctly."""
        csv_path = csv_dir / "cabinet_kitchen_imperial.csv"
        assert csv_path.exists(), f"Kitchen cabinet CSV not found: {csv_path}"

        parts = csv_to_parts(str(csv_path), measurement_system="imperial")

        # Should have many parts due to quantities
        assert len(parts) > 50

        # Check some specific parts
        cabinet_sides = [p for p in parts if p.id.startswith("Cabinet_Side_A")]
        assert len(cabinet_sides) == 4  # qty=4

        # Verify dimensions are converted to mm correctly
        cabinet_side = cabinet_sides[0]
        expected_width_mm = inches_to_mm(23.25)  # 23 1/4"
        expected_height_mm = inches_to_mm(30)
        assert abs(cabinet_side.width - expected_width_mm) < 0.1
        assert abs(cabinet_side.height - expected_height_mm) < 0.1
        assert not cabinet_side.can_rotate  # allow_rotate=0

    def test_kitchen_cabinet_multi_sheet_nesting(self, csv_dir, standard_plywood_sheet):
        """Test that kitchen cabinet parts require multiple sheets."""
        csv_path = csv_dir / "cabinet_kitchen_imperial.csv"
        parts = csv_to_parts(str(csv_path), measurement_system="imperial")

        sheet_width, sheet_height = standard_plywood_sheet
        placed_parts = nest_parts(parts, sheet_width, sheet_height)

        # Should require multiple sheets for all these cabinet parts
        sheet_indices = {p.sheet_index for p in placed_parts}
        assert len(sheet_indices) >= 2, "Kitchen cabinet should require multiple sheets"

        # All parts should be placed
        assert len(placed_parts) == len(parts)

    def _rectangles_overlap(self, part1, part2):
        """Check if two placed parts overlap."""
        return not (
            part1.x >= part2.x + part2.width
            or part2.x >= part1.x + part1.width
            or part1.y >= part2.y + part2.height
            or part2.y >= part1.y + part1.height
        )
