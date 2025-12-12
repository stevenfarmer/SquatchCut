"""Tests for CSV unit auto-detection functionality."""

import os
import tempfile

from SquatchCut.core.csv_loader import detect_csv_units


class TestCsvUnitDetection:
    """Test CSV unit auto-detection."""

    def test_detect_imperial_fractional_inches(self):
        """Test detection of imperial units with fractional inches."""
        csv_content = """id,width,height,qty,allow_rotate
Panel1,23 1/4,12 3/8,1,1
Panel2,18 1/2,10,2,0
Panel3,30,8 3/4,1,1"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            try:
                result = detect_csv_units(f.name)
                assert result == "imperial"
            finally:
                os.unlink(f.name)

    def test_detect_metric_whole_numbers(self):
        """Test detection of metric units with whole numbers."""
        csv_content = """id,width,height,qty,allow_rotate
Panel1,600,400,1,1
Panel2,800,500,2,0
Panel3,1200,300,1,1"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            try:
                result = detect_csv_units(f.name)
                assert result == "metric"
            finally:
                os.unlink(f.name)

    def test_detect_imperial_mixed_fractions(self):
        """Test detection with mix of fractional and whole numbers (imperial)."""
        csv_content = """id,width,height,qty,allow_rotate
Panel1,24,12 1/4,1,1
Panel2,18 3/8,10,2,0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            try:
                result = detect_csv_units(f.name)
                assert result == "imperial"
            finally:
                os.unlink(f.name)

    def test_detect_metric_decimal_numbers(self):
        """Test detection of metric units with decimal numbers."""
        csv_content = """id,width,height,qty,allow_rotate
Panel1,600.5,400.25,1,1
Panel2,800.75,500,2,0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            try:
                result = detect_csv_units(f.name)
                assert result == "metric"
            finally:
                os.unlink(f.name)

    def test_detect_file_not_found(self):
        """Test graceful handling of missing file."""
        result = detect_csv_units("/nonexistent/file.csv")
        assert result == "metric"  # Default fallback

    def test_detect_empty_file(self):
        """Test handling of empty CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("")
            f.flush()

            try:
                result = detect_csv_units(f.name)
                assert result == "metric"  # Default fallback
            finally:
                os.unlink(f.name)

    def test_detect_only_headers(self):
        """Test handling of CSV with only headers."""
        csv_content = """id,width,height,qty,allow_rotate"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()

            try:
                result = detect_csv_units(f.name)
                assert result == "metric"  # Default fallback
            finally:
                os.unlink(f.name)

    def test_existing_cabinet_csvs(self):
        """Test detection on existing test CSV files."""
        # Test imperial cabinet files
        imperial_result = detect_csv_units(
            "freecad/testing/csv/cabinet_closet_imperial.csv"
        )
        assert imperial_result == "imperial"

        bathroom_result = detect_csv_units(
            "freecad/testing/csv/cabinet_bathroom_imperial.csv"
        )
        assert bathroom_result == "imperial"

        # Test metric files
        metric_result = detect_csv_units(
            "freecad/testing/csv/valid_panels_multi_sheet.csv"
        )
        assert metric_result == "metric"

        small_result = detect_csv_units("freecad/testing/csv/valid_panels_small.csv")
        assert small_result == "metric"

    def test_new_kitchen_cabinet_csv(self):
        """Test detection on the new 24x24x36 kitchen cabinet CSV."""
        result = detect_csv_units(
            "freecad/testing/csv/cabinet_kitchen_24x24x36_imperial.csv"
        )
        assert result == "imperial"

    def test_fractional_inch_parsing(self):
        """Test parsing of fractional inch values."""
        from SquatchCut.core.csv_loader import parse_fractional_inch

        # Test whole numbers
        assert parse_fractional_inch("24") == 24.0
        assert parse_fractional_inch("12") == 12.0

        # Test fractions with whole numbers
        assert parse_fractional_inch("23 1/4") == 23.25
        assert parse_fractional_inch("12 3/8") == 12.375
        assert parse_fractional_inch("18 1/2") == 18.5
        assert parse_fractional_inch("30 3/4") == 30.75

        # Test just fractions
        assert parse_fractional_inch("1/4") == 0.25
        assert parse_fractional_inch("3/8") == 0.375
        assert parse_fractional_inch("1/2") == 0.5
        assert parse_fractional_inch("3/4") == 0.75

        # Test decimal numbers
        assert parse_fractional_inch("12.5") == 12.5
        assert parse_fractional_inch("24.25") == 24.25

    def test_csv_loading_with_fractional_inches(self):
        """Test that CSV loading works with fractional inches."""
        from SquatchCut.core.csv_loader import CsvLoader

        loader = CsvLoader()
        panels = loader.load_csv(
            "freecad/testing/csv/cabinet_kitchen_24x24x36_imperial.csv",
            csv_units="imperial",
        )

        assert len(panels) > 0

        # Check that dimensions were converted to mm
        first_panel = panels[0]
        assert "width" in first_panel
        assert "height" in first_panel

        # 23 1/4 inches = 23.25 * 25.4 = 590.55 mm
        expected_width = 23.25 * 25.4
        assert abs(first_panel["width"] - expected_width) < 0.1
