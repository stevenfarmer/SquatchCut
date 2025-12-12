"""Tests for input validation utilities."""

import pytest

from SquatchCut.core.input_validation import (
    validate_positive_number,
    validate_sheet_dimensions,
    validate_kerf_and_spacing,
    validate_csv_file_path,
    validate_panel_data,
    sanitize_filename,
    validate_export_path,
)
from SquatchCut.ui.error_handling import ValidationError


class TestPositiveNumberValidation:
    """Test positive number validation."""

    def test_validate_positive_number_valid_int(self):
        """Test validation with valid integer."""
        result = validate_positive_number(42, "test_field")
        assert result == 42.0

    def test_validate_positive_number_valid_float(self):
        """Test validation with valid float."""
        result = validate_positive_number(3.14, "test_field")
        assert result == 3.14

    def test_validate_positive_number_valid_string(self):
        """Test validation with valid string number."""
        result = validate_positive_number("123.45", "test_field")
        assert result == 123.45

    def test_validate_positive_number_zero_not_allowed(self):
        """Test validation with zero when not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number(0, "test_field")

        assert "test_field" in str(exc_info.value.message)
        assert "positive" in str(exc_info.value.details)

    def test_validate_positive_number_zero_allowed(self):
        """Test validation with zero when allowed."""
        result = validate_positive_number(0, "test_field", allow_zero=True)
        assert result == 0.0

    def test_validate_positive_number_negative(self):
        """Test validation with negative number."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number(-5, "test_field")

        assert "test_field" in str(exc_info.value.message)

    def test_validate_positive_number_invalid_string(self):
        """Test validation with invalid string."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number("not_a_number", "test_field")

        assert "test_field" in str(exc_info.value.message)
        assert "not a valid number" in str(exc_info.value.details)


class TestSheetDimensionsValidation:
    """Test sheet dimensions validation."""

    def test_validate_sheet_dimensions_metric_numbers(self):
        """Test validation with metric numbers."""
        width_mm, height_mm = validate_sheet_dimensions(1220, 2440, "metric")
        assert width_mm == 1220.0
        assert height_mm == 2440.0

    def test_validate_sheet_dimensions_imperial_numbers(self):
        """Test validation with imperial numbers."""
        width_mm, height_mm = validate_sheet_dimensions(48, 96, "imperial")
        assert abs(width_mm - 48 * 25.4) < 0.01
        assert abs(height_mm - 96 * 25.4) < 0.01

    def test_validate_sheet_dimensions_metric_strings(self):
        """Test validation with metric string inputs."""
        width_mm, height_mm = validate_sheet_dimensions("1220", "2440", "metric")
        assert width_mm == 1220.0
        assert height_mm == 2440.0

    def test_validate_sheet_dimensions_imperial_strings(self):
        """Test validation with imperial string inputs."""
        width_mm, height_mm = validate_sheet_dimensions("48", "96 1/4", "imperial")
        assert abs(width_mm - 48 * 25.4) < 0.01
        assert abs(height_mm - (96.25 * 25.4)) < 0.01

    def test_validate_sheet_dimensions_too_large(self):
        """Test validation with oversized dimensions."""
        with pytest.raises(ValidationError) as exc_info:
            validate_sheet_dimensions(15000, 2440, "metric")

        assert "Sheet Too Large" in str(exc_info.value.message)

    def test_validate_sheet_dimensions_too_small(self):
        """Test validation with undersized dimensions."""
        with pytest.raises(ValidationError) as exc_info:
            validate_sheet_dimensions(5, 2440, "metric")

        assert "Sheet Too Small" in str(exc_info.value.message)

    def test_validate_sheet_dimensions_invalid_width(self):
        """Test validation with invalid width."""
        with pytest.raises(ValidationError) as exc_info:
            validate_sheet_dimensions("invalid", "2440", "metric")

        assert "Invalid Sheet Width" in str(exc_info.value.message)

    def test_validate_sheet_dimensions_invalid_height(self):
        """Test validation with invalid height."""
        with pytest.raises(ValidationError) as exc_info:
            validate_sheet_dimensions("1220", "invalid", "metric")

        assert "Invalid Sheet Height" in str(exc_info.value.message)


class TestKerfAndSpacingValidation:
    """Test kerf and spacing validation."""

    def test_validate_kerf_and_spacing_metric(self):
        """Test validation with metric values."""
        kerf_mm, spacing_mm = validate_kerf_and_spacing(3.0, 0.0, "metric")
        assert kerf_mm == 3.0
        assert spacing_mm == 0.0

    def test_validate_kerf_and_spacing_imperial(self):
        """Test validation with imperial values."""
        kerf_mm, spacing_mm = validate_kerf_and_spacing("1/8", "1/16", "imperial")
        assert abs(kerf_mm - (0.125 * 25.4)) < 0.01
        assert abs(spacing_mm - (0.0625 * 25.4)) < 0.01

    def test_validate_kerf_and_spacing_zero_values(self):
        """Test validation with zero values."""
        kerf_mm, spacing_mm = validate_kerf_and_spacing(0, 0, "metric")
        assert kerf_mm == 0.0
        assert spacing_mm == 0.0

    def test_validate_kerf_and_spacing_too_large_kerf(self):
        """Test validation with oversized kerf."""
        with pytest.raises(ValidationError) as exc_info:
            validate_kerf_and_spacing(30, 0, "metric")

        assert "Kerf Too Large" in str(exc_info.value.message)

    def test_validate_kerf_and_spacing_too_large_spacing(self):
        """Test validation with oversized spacing."""
        with pytest.raises(ValidationError) as exc_info:
            validate_kerf_and_spacing(3, 60, "metric")

        assert "Spacing Too Large" in str(exc_info.value.message)

    def test_validate_kerf_and_spacing_invalid_kerf(self):
        """Test validation with invalid kerf."""
        with pytest.raises(ValidationError) as exc_info:
            validate_kerf_and_spacing("invalid", 0, "metric")

        assert "Invalid Kerf Width" in str(exc_info.value.message)

    def test_validate_kerf_and_spacing_invalid_spacing(self):
        """Test validation with invalid spacing."""
        with pytest.raises(ValidationError) as exc_info:
            validate_kerf_and_spacing(3, "invalid", "metric")

        assert "Invalid Spacing" in str(exc_info.value.message)


class TestCSVFilePathValidation:
    """Test CSV file path validation."""

    def test_validate_csv_file_path_valid(self):
        """Test validation with valid CSV path."""
        result = validate_csv_file_path("test_file.csv")
        assert result == "test_file.csv"

    def test_validate_csv_file_path_with_spaces(self):
        """Test validation with path containing spaces."""
        result = validate_csv_file_path("  test_file.csv  ")
        assert result == "test_file.csv"

    def test_validate_csv_file_path_empty(self):
        """Test validation with empty path."""
        with pytest.raises(ValidationError) as exc_info:
            validate_csv_file_path("")

        assert "No File Selected" in str(exc_info.value.message)

    def test_validate_csv_file_path_wrong_extension(self):
        """Test validation with wrong file extension."""
        with pytest.raises(ValidationError) as exc_info:
            validate_csv_file_path("test_file.txt")

        assert "Invalid File Type" in str(exc_info.value.message)
        assert ".csv extension" in str(exc_info.value.details)

    def test_validate_csv_file_path_case_insensitive(self):
        """Test validation with uppercase extension."""
        result = validate_csv_file_path("test_file.CSV")
        assert result == "test_file.CSV"


class TestPanelDataValidation:
    """Test panel data validation."""

    def test_validate_panel_data_valid_metric(self):
        """Test validation with valid metric panel data."""
        result = validate_panel_data("P001", 100, 200, 2, "metric")

        assert result["id"] == "P001"
        assert result["width"] == 100.0
        assert result["height"] == 200.0
        assert result["qty"] == 2

    def test_validate_panel_data_valid_imperial(self):
        """Test validation with valid imperial panel data."""
        result = validate_panel_data("P001", "12", "24 1/2", 1, "imperial")

        assert result["id"] == "P001"
        assert abs(result["width"] - (12 * 25.4)) < 0.01
        assert abs(result["height"] - (24.5 * 25.4)) < 0.01
        assert result["qty"] == 1

    def test_validate_panel_data_default_quantity(self):
        """Test validation with default quantity."""
        result = validate_panel_data("P001", 100, 200, units_system="metric")
        assert result["qty"] == 1

    def test_validate_panel_data_empty_id(self):
        """Test validation with empty panel ID."""
        with pytest.raises(ValidationError) as exc_info:
            validate_panel_data("", 100, 200, 1, "metric")

        assert "Missing Panel ID" in str(exc_info.value.message)

    def test_validate_panel_data_invalid_dimensions(self):
        """Test validation with invalid dimensions."""
        with pytest.raises(ValidationError) as exc_info:
            validate_panel_data("P001", "invalid", 200, 1, "metric")

        assert "Invalid Panel Dimensions" in str(exc_info.value.message)
        assert "P001" in str(exc_info.value.message)

    def test_validate_panel_data_invalid_quantity(self):
        """Test validation with invalid quantity."""
        with pytest.raises(ValidationError) as exc_info:
            validate_panel_data("P001", 100, 200, "invalid", "metric")

        assert "Invalid Quantity" in str(exc_info.value.message)
        assert "P001" in str(exc_info.value.message)

    def test_validate_panel_data_zero_quantity(self):
        """Test validation with zero quantity."""
        with pytest.raises(ValidationError) as exc_info:
            validate_panel_data("P001", 100, 200, 0, "metric")

        assert "Invalid Quantity" in str(exc_info.value.message)

    def test_validate_panel_data_too_large(self):
        """Test validation with oversized panel."""
        with pytest.raises(ValidationError) as exc_info:
            validate_panel_data("P001", 6000, 200, 1, "metric")

        assert "Panel Too Large" in str(exc_info.value.message)
        assert "P001" in str(exc_info.value.message)

    def test_validate_panel_data_too_small(self):
        """Test validation with undersized panel."""
        with pytest.raises(ValidationError) as exc_info:
            validate_panel_data("P001", 0.5, 200, 1, "metric")

        assert "Invalid Panel Dimensions" in str(exc_info.value.message)
        assert "P001" in str(exc_info.value.message)


class TestFilenameValidation:
    """Test filename sanitization."""

    def test_sanitize_filename_valid(self):
        """Test sanitization with valid filename."""
        result = sanitize_filename("valid_filename")
        assert result == "valid_filename"

    def test_sanitize_filename_with_invalid_chars(self):
        """Test sanitization with invalid characters."""
        result = sanitize_filename("file<name>with:invalid|chars")
        assert result == "file_name_with_invalid_chars"

    def test_sanitize_filename_empty(self):
        """Test sanitization with empty filename."""
        result = sanitize_filename("")
        assert result == "untitled"

    def test_sanitize_filename_whitespace_only(self):
        """Test sanitization with whitespace only."""
        result = sanitize_filename("   ")
        assert result == "untitled"

    def test_sanitize_filename_too_long(self):
        """Test sanitization with very long filename."""
        long_name = "a" * 250
        result = sanitize_filename(long_name)
        assert len(result) == 200

    def test_sanitize_filename_with_dots(self):
        """Test sanitization with leading/trailing dots."""
        result = sanitize_filename("...filename...")
        assert result == "filename"


class TestExportPathValidation:
    """Test export path validation."""

    def test_validate_export_path_valid(self):
        """Test validation with valid export path."""
        result = validate_export_path("/path/to/file.csv", ".csv")
        assert result == "/path/to/file.csv"

    def test_validate_export_path_missing_extension(self):
        """Test validation with missing extension."""
        result = validate_export_path("/path/to/file", ".csv")
        assert result == "/path/to/file.csv"

    def test_validate_export_path_wrong_extension(self):
        """Test validation with wrong extension."""
        result = validate_export_path("/path/to/file.txt", ".csv")
        assert result == "/path/to/file.txt.csv"

    def test_validate_export_path_empty(self):
        """Test validation with empty path."""
        with pytest.raises(ValidationError) as exc_info:
            validate_export_path("", ".csv")

        assert "No Export Path" in str(exc_info.value.message)

    def test_validate_export_path_sanitize_filename(self):
        """Test validation with filename that needs sanitization."""
        result = validate_export_path("/path/to/file<name>.csv", ".csv")
        assert "file_name" in result
        assert result.endswith(".csv")

    def test_validate_export_path_case_insensitive_extension(self):
        """Test validation with case-insensitive extension matching."""
        result = validate_export_path("/path/to/file.CSV", ".csv")
        assert result == "/path/to/file.CSV"
