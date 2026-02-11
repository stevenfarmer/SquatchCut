"""Tests for the ExportNestingCSVCommand."""

import tempfile
from pathlib import Path

from SquatchCut.core import session_state
from SquatchCut.core.nesting import PlacedPart
from SquatchCut.gui.commands.cmd_run_nesting import ExportNestingCSVCommand


class TestExportNestingCSVCommand:
    """Test the CSV export command functionality."""

    def test_command_resources(self):
        """Test command metadata."""
        cmd = ExportNestingCSVCommand()
        resources = cmd.GetResources()

        assert "Export Nesting CSV" in resources["MenuText"]
        assert "CSV" in resources["ToolTip"]

    def test_csv_export_end_to_end(self):
        """Test complete CSV export functionality."""
        from SquatchCut.core.exporter import (
            build_export_job_from_current_nesting,
            export_cutlist,
        )

        # Set up test data
        session_state.set_measurement_system("metric")
        session_state.set_sheet_size(1200, 2400)
        placements = [
            PlacedPart(
                id="TestPart1",
                x=10.5,
                y=20.25,
                width=100,
                height=200,
                sheet_index=0,
                rotation_deg=0,
            ),
            PlacedPart(
                id="TestPart2",
                x=120,
                y=20,
                width=150,
                height=200,
                sheet_index=0,
                rotation_deg=90,
            ),
        ]
        session_state.set_last_layout(placements)

        # Build and export
        export_job = build_export_job_from_current_nesting()
        assert export_job is not None

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            export_cutlist(export_job, csv_path)

            # Verify file contents
            csv_file = Path(csv_path)
            assert csv_file.exists()

            content = csv_file.read_text()
            lines = content.strip().split("\n")

            # Check header
            header = lines[0]
            expected_columns = [
                "sheet_index",
                "part_id",
                "x_mm",
                "y_mm",
                "width_mm",
                "height_mm",
                "rotation_deg",
            ]
            for col in expected_columns:
                assert col in header

            # Check data rows
            assert len(lines) >= 3  # Header + 2 parts
            assert "TestPart1" in content
            assert "TestPart2" in content
            assert "10.5" in content  # Precise positioning
            assert "20.25" in content

        finally:
            if Path(csv_path).exists():
                Path(csv_path).unlink()

    def test_empty_layout_handling(self):
        """Test behavior when no layout exists."""
        from SquatchCut.core.exporter import build_export_job_from_current_nesting

        # Clear layout
        session_state.set_last_layout([])

        # Should return None for empty layout
        export_job = build_export_job_from_current_nesting()
        assert export_job is None
