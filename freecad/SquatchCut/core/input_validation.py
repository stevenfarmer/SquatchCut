"""Input validation utilities for SquatchCut."""

import re

from SquatchCut.core import units
from SquatchCut.ui.error_handling import ValidationError


def validate_positive_number(
    value: str | float | int, field_name: str, allow_zero: bool = False
) -> float:
    """Validate that a value is a positive number."""
    try:
        num_value = float(value) if isinstance(value, str) else float(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid {field_name}",
            f"'{value}' is not a valid number",
            f"Please enter a valid number for {field_name}",
        )

    if allow_zero and num_value < 0:
        raise ValidationError(
            f"Invalid {field_name}",
            f"Value must be non-negative, got {num_value}",
            f"Please enter a non-negative number for {field_name}",
        )
    elif not allow_zero and num_value <= 0:
        raise ValidationError(
            f"Invalid {field_name}",
            f"Value must be positive, got {num_value}",
            f"Please enter a positive number for {field_name}",
        )

    return num_value


def validate_sheet_dimensions(
    width: str | float, height: str | float, units_system: str = "metric"
) -> tuple[float, float]:
    """Validate sheet width and height dimensions."""
    # Validate width
    if isinstance(width, str):
        try:
            width_mm = units.parse_length(width.strip(), units_system)
        except ValueError as e:
            raise ValidationError(
                "Invalid Sheet Width",
                str(e),
                "Please enter a valid width (e.g., '48' or '48 1/2' for imperial, '1220' for metric)",
            )
    else:
        width_mm = validate_positive_number(width, "sheet width")
        if units_system == "imperial":
            width_mm = width_mm * 25.4  # Convert inches to mm

    # Validate height
    if isinstance(height, str):
        try:
            height_mm = units.parse_length(height.strip(), units_system)
        except ValueError as e:
            raise ValidationError(
                "Invalid Sheet Height",
                str(e),
                "Please enter a valid height (e.g., '96' or '96 1/4' for imperial, '2440' for metric)",
            )
    else:
        height_mm = validate_positive_number(height, "sheet height")
        if units_system == "imperial":
            height_mm = height_mm * 25.4  # Convert inches to mm

    # Check reasonable limits
    max_dimension_mm = 10000  # 10 meters
    min_dimension_mm = 10  # 1 cm

    if width_mm > max_dimension_mm or height_mm > max_dimension_mm:
        raise ValidationError(
            "Sheet Too Large",
            f"Sheet dimensions exceed maximum of {max_dimension_mm}mm ({max_dimension_mm/25.4:.1f} inches)",
            "Please enter smaller sheet dimensions",
        )

    if width_mm < min_dimension_mm or height_mm < min_dimension_mm:
        raise ValidationError(
            "Sheet Too Small",
            f"Sheet dimensions must be at least {min_dimension_mm}mm ({min_dimension_mm/25.4:.2f} inches)",
            "Please enter larger sheet dimensions",
        )

    return width_mm, height_mm


def validate_kerf_and_spacing(
    kerf: str | float, spacing: str | float, units_system: str = "metric"
) -> tuple[float, float]:
    """Validate kerf and spacing values."""
    # Validate kerf
    if isinstance(kerf, str):
        try:
            kerf_mm = units.parse_length(kerf.strip(), units_system)
        except ValueError as e:
            raise ValidationError(
                "Invalid Kerf Width",
                str(e),
                "Please enter a valid kerf width (e.g., '1/8' for imperial, '3' for metric)",
            )
    else:
        kerf_mm = validate_positive_number(kerf, "kerf width", allow_zero=True)
        if units_system == "imperial":
            kerf_mm = units.display_to_mm(kerf_mm)

    # Validate spacing
    if isinstance(spacing, str):
        try:
            spacing_mm = units.parse_length(spacing.strip(), units_system)
        except ValueError as e:
            raise ValidationError(
                "Invalid Spacing",
                str(e),
                "Please enter a valid spacing value (e.g., '0' or '1/16' for imperial, '0' or '1' for metric)",
            )
    else:
        spacing_mm = validate_positive_number(spacing, "spacing", allow_zero=True)
        if units_system == "imperial":
            spacing_mm = units.display_to_mm(spacing_mm)

    # Check reasonable limits
    max_kerf_mm = 25  # 1 inch
    max_spacing_mm = 50  # 2 inches

    if kerf_mm > max_kerf_mm:
        raise ValidationError(
            "Kerf Too Large",
            f"Kerf width exceeds maximum of {max_kerf_mm}mm ({max_kerf_mm/25.4:.2f} inches)",
            "Please enter a smaller kerf width",
        )

    if spacing_mm > max_spacing_mm:
        raise ValidationError(
            "Spacing Too Large",
            f"Spacing exceeds maximum of {max_spacing_mm}mm ({max_spacing_mm/25.4:.2f} inches)",
            "Please enter a smaller spacing value",
        )

    return kerf_mm, spacing_mm


def validate_csv_file_path(file_path: str) -> str:
    """Validate CSV file path."""
    if not file_path or not file_path.strip():
        raise ValidationError(
            "No File Selected",
            "File path is empty",
            "Please select a CSV file to import",
        )

    file_path = file_path.strip()

    # Check file extension
    if not file_path.lower().endswith(".csv"):
        raise ValidationError(
            "Invalid File Type",
            f"File must have .csv extension, got: {file_path}",
            "Please select a CSV file (.csv extension)",
        )

    return file_path


def validate_panel_data(
    panel_id: str,
    width: str | float,
    height: str | float,
    quantity: str | int = 1,
    units_system: str = "metric",
) -> dict:
    """Validate individual panel data from CSV."""
    # Validate ID
    if not panel_id or not str(panel_id).strip():
        raise ValidationError(
            "Missing Panel ID",
            "Panel ID cannot be empty",
            "Please provide a unique ID for each panel",
        )

    panel_id = str(panel_id).strip()

    # Validate dimensions
    try:
        width_mm, height_mm = validate_sheet_dimensions(width, height, units_system)
    except ValidationError as e:
        # Re-raise with panel context
        raise ValidationError(
            f"Invalid Panel Dimensions (ID: {panel_id})", e.details, e.user_action
        )

    # Validate quantity
    try:
        qty = int(quantity) if quantity is not None else 1
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid Quantity (ID: {panel_id})",
            f"'{quantity}' is not a valid quantity",
            "Please enter a positive integer for quantity",
        )

    if qty <= 0:
        raise ValidationError(
            f"Invalid Quantity (ID: {panel_id})",
            f"Quantity must be positive, got {qty}",
            "Please enter a positive integer for quantity",
        )

    # Check for reasonable panel sizes
    max_panel_mm = 5000  # 5 meters
    min_panel_mm = 1  # 1 mm

    if width_mm > max_panel_mm or height_mm > max_panel_mm:
        raise ValidationError(
            f"Panel Too Large (ID: {panel_id})",
            f"Panel dimensions exceed maximum of {max_panel_mm}mm",
            "Please check panel dimensions - they seem unusually large",
        )

    if width_mm < min_panel_mm or height_mm < min_panel_mm:
        raise ValidationError(
            f"Panel Too Small (ID: {panel_id})",
            f"Panel dimensions must be at least {min_panel_mm}mm",
            "Please check panel dimensions - they seem unusually small",
        )

    return {"id": panel_id, "width": width_mm, "height": height_mm, "qty": qty}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    if not filename:
        return "untitled"

    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(" .")

    # Ensure it's not empty after sanitization
    if not sanitized:
        return "untitled"

    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]

    return sanitized


def validate_export_path(file_path: str, expected_extension: str = ".csv") -> str:
    """Validate export file path."""
    if not file_path or not file_path.strip():
        raise ValidationError(
            "No Export Path",
            "Export path is empty",
            "Please specify where to save the exported file",
        )

    file_path = file_path.strip()

    # Ensure proper extension
    if not file_path.lower().endswith(expected_extension.lower()):
        file_path += expected_extension

    # Sanitize the filename part
    import os

    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)

    sanitized_name = sanitize_filename(name)
    file_path = os.path.join(directory, sanitized_name + ext)

    return file_path
