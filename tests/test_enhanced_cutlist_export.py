"""Tests for enhanced woodshop-friendly cutlist export functionality."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from SquatchCut.core.exporter import (
    ExportJob,
    ExportPartPlacement,
    ExportSheet,
    _format_sheet_size_for_export,
    _generate_cut_instructions,
    _get_current_timestamp,
    export_cutlist,
)


class TestEnhancedCutlistExport:
    """Test enhanced cutlist export with woodshop-friendly instructions."""

    @pytest.fixture
    def sample_export_job(self):
        """Create a sample export job for testing."""
        parts = [
            ExportPartPlacement(
                "Cabinet_Side", 0, 0, 0, 590.55, 762, 0
            ),  # 23 1/4" x 30"
            ExportPartPlacement(
                "Door", 0, 600, 0, 394.97, 749.3, 0
            ),  # 15 1/2" x 29 1/2"
            ExportPartPlacement(
                "Shelf", 0, 0, 800, 577.85, 577.85, 90
            ),  # 22 3/4" x 22 3/4" rotated
        ]
        sheet = ExportSheet(0, 1219.2, 2438.4, parts)  # 48" x 96" sheet
        return ExportJob("Kitchen Cabinet", "imperial", [sheet])

    def test_enhanced_csv_export_structure(self, sample_export_job, tmp_path):
        """Test that enhanced CSV export has correct structure and headers."""
        output_path = tmp_path / "test_cutlist.csv"

        export_cutlist(sample_export_job, str(output_path), enhanced_format=True)

        assert output_path.exists()

        with open(output_path, newline="", encoding="utf-8") as f:
            content = f.read()

        # Should have project header information
        assert "# SquatchCut Cutting List" in content
        assert "# Generated:" in content
        assert "# Measurement System: Imperial" in content
        assert "# Total Sheets: 1" in content

        # Should have woodshop-friendly column headers
        assert "Sheet" in content
        assert "Sheet_Size" in content
        assert "Part_Name" in content
        assert "Width" in content
        assert "Height" in content
        assert "Cut_Instructions" in content

        # Should have cutting tips
        assert "# Cutting Tips:" in content
        assert "# 1. Cut all parts from one sheet before moving to the next" in content
        assert "# 2. Mark each part clearly before cutting" in content

    def test_enhanced_csv_export_data_accuracy(self, sample_export_job, tmp_path):
        """Test that exported data is accurate and properly formatted."""
        output_path = tmp_path / "test_cutlist.csv"

        export_cutlist(sample_export_job, str(output_path), enhanced_format=True)

        # Read the CSV data (skip header comments)
        with open(output_path, newline="", encoding="utf-8") as f:
            lines = f.readlines()

        # Find the data rows (after headers and comments)
        data_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith("Sheet,"):
                data_start = i + 1
                break

        assert data_start is not None, "Could not find data section in CSV"

        # Parse data rows
        data_lines = [
            line.strip()
            for line in lines[data_start:]
            if line.strip() and not line.startswith("#")
        ]

        # Should have 3 parts
        assert len(data_lines) >= 3

        # Check first part (Cabinet_Side)
        first_part = data_lines[0].split(",")
        assert first_part[0] == "Sheet 1"
        assert "48" in first_part[1] and "96" in first_part[1]  # Sheet size
        assert first_part[2] == "Cabinet_Side"
        assert "23 1/4" in first_part[3]  # Width in fractional inches
        assert "30" in first_part[4]  # Height
        assert first_part[9] == "No"  # Not rotated (column index 9)

    def test_cut_instructions_generation(self, sample_export_job):
        """Test that cut instructions are clear and actionable."""
        sheet = sample_export_job.sheets[0]
        part = sheet.parts[0]  # Cabinet_Side

        instructions = _generate_cut_instructions(part, sheet, sample_export_job)

        # Should contain dimensions
        assert "23 1/4" in instructions
        assert "30" in instructions

        # Should contain position information
        assert "from left edge" in instructions
        assert "from bottom edge" in instructions

        # Should be clear and actionable
        assert "Cut" in instructions
        assert instructions.startswith("Cut")

    def test_rotated_part_instructions(self, sample_export_job):
        """Test that rotated parts have clear rotation instructions."""
        sheet = sample_export_job.sheets[0]
        rotated_part = sheet.parts[2]  # Shelf (rotated 90°)

        instructions = _generate_cut_instructions(
            rotated_part, sheet, sample_export_job
        )

        # Should indicate rotation
        assert "rotated 90°" in instructions
        assert "Cut" in instructions

    def test_sheet_size_formatting(self, sample_export_job):
        """Test that sheet sizes are formatted clearly."""
        sheet = sample_export_job.sheets[0]

        formatted_size = _format_sheet_size_for_export(sheet, sample_export_job)

        # Should be in imperial format
        assert "48" in formatted_size
        assert "96" in formatted_size
        assert "in" in formatted_size
        assert "x" in formatted_size

    def test_metric_export_formatting(self, tmp_path):
        """Test that metric exports are formatted correctly."""
        # Create metric export job
        parts = [
            ExportPartPlacement("Panel_A", 0, 0, 0, 600, 800, 0),
        ]
        sheet = ExportSheet(0, 1220, 2440, parts)
        metric_job = ExportJob("Metric Test", "metric", [sheet])

        output_path = tmp_path / "metric_cutlist.csv"
        export_cutlist(metric_job, str(output_path), enhanced_format=True)

        with open(output_path, newline="", encoding="utf-8") as f:
            content = f.read()

        # Should indicate metric system
        assert "# Measurement System: Metric" in content

        # Should have metric units
        assert "mm" in content

    def test_timestamp_generation(self):
        """Test that timestamp is generated correctly."""
        timestamp = _get_current_timestamp()
        # Just verify it returns a string in the expected format
        assert isinstance(timestamp, str)
        assert len(timestamp) == 16  # "YYYY-MM-DD HH:MM" format
        assert timestamp[4] == "-"
        assert timestamp[7] == "-"
        assert timestamp[10] == " "
        assert timestamp[13] == ":"

    def test_multi_sheet_export_organization(self, tmp_path):
        """Test that multi-sheet exports are well organized."""
        # Create multi-sheet job
        parts1 = [ExportPartPlacement("Part_A", 0, 0, 0, 600, 800, 0)]
        parts2 = [ExportPartPlacement("Part_B", 1, 0, 0, 500, 700, 0)]

        sheet1 = ExportSheet(0, 1220, 2440, parts1)
        sheet2 = ExportSheet(1, 1220, 2440, parts2)

        multi_job = ExportJob("Multi Sheet", "imperial", [sheet1, sheet2])

        output_path = tmp_path / "multi_sheet_cutlist.csv"
        export_cutlist(multi_job, str(output_path), enhanced_format=True)

        with open(output_path, newline="", encoding="utf-8") as f:
            content = f.read()

        # Should indicate total sheets
        assert "# Total Sheets: 2" in content

        # Should have both sheets
        assert "Sheet 1" in content
        assert "Sheet 2" in content

    def test_export_handles_empty_job(self, tmp_path):
        """Test that export handles empty jobs gracefully."""
        empty_job = ExportJob("Empty", "imperial", [])

        output_path = tmp_path / "empty_cutlist.csv"

        # Should not crash, but should handle gracefully
        export_cutlist(empty_job, str(output_path), enhanced_format=True)

        # File should not be created or should be empty
        if output_path.exists():
            assert output_path.stat().st_size == 0

    def test_woodshop_friendly_language(self, sample_export_job, tmp_path):
        """Test that the export uses woodshop-friendly language throughout."""
        output_path = tmp_path / "friendly_cutlist.csv"

        export_cutlist(sample_export_job, str(output_path), enhanced_format=True)

        with open(output_path, newline="", encoding="utf-8") as f:
            content = f.read()

        # Should use clear, actionable language
        assert "Cut" in content
        assert "Position" in content
        assert "from left edge" in content
        assert "from bottom edge" in content

        # Should avoid technical jargon
        assert "x_mm" not in content
        assert "y_mm" not in content
        assert "rotation_deg" not in content

        # Should have helpful tips
        assert "Measure twice, cut once" in content
        assert "Account for saw kerf" in content
