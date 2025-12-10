"""Structured CSV validation logic for SquatchCut panels."""

from __future__ import annotations

import csv
from dataclasses import dataclass

try:
    from SquatchCut.core import session_state
except Exception:
    session_state = None

MM_PER_INCH = 25.4
REQUIRED_COLUMNS = {"id", "width", "height"}


@dataclass
class CsvValidationError:
    row: int | None
    message: str


def validate_csv_file(path: str, csv_units: str = "metric") -> tuple[list[dict], list[CsvValidationError]]:
    """
    Parse and validate the CSV at `path`.

    Returns a tuple (parts, errors). If any validation errors occur, `parts`
    will be empty and `errors` will contain details to show to the user.
    """
    errors: list[CsvValidationError] = []
    parts: list[dict] = []
    normalized_units = _normalize_units(csv_units)

    try:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames or []
            if not headers:
                errors.append(CsvValidationError(None, "Missing header row."))
                return [], errors

            header_set = {name.strip().lower() for name in headers if name}
            missing = sorted(REQUIRED_COLUMNS - header_set)
            if missing:
                errors.append(
                    CsvValidationError(
                        None,
                        f"Missing required column(s): {', '.join(missing)}.",
                    )
                )
                return [], errors

            for idx, raw_row in enumerate(reader, start=2):
                normalized = _normalize_row(raw_row)
                if _is_empty_row(normalized):
                    continue
                part, error = _validate_panel_row(normalized, idx, normalized_units)
                if error:
                    errors.append(error)
                    continue
                parts.append(part)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise ValueError(f"Failed to read CSV: {exc}") from exc

    if errors:
        return [], errors

    return parts, []


def _normalize_units(csv_units: str) -> str:
    normalized = str(csv_units or "metric").strip().lower()
    if normalized == "metric":
        return "mm"
    if normalized == "imperial":
        return "in"
    return normalized


def _normalize_row(row: dict) -> dict:
    if not row:
        return {}
    normalized = {}
    for key, value in row.items():
        if not key:
            continue
        name = key.strip().lower()
        if value is None:
            normalized[name] = ""
        else:
            normalized[name] = str(value).strip()
    return normalized


def _is_empty_row(normalized: dict) -> bool:
    if not normalized:
        return True
    return all(not value for value in normalized.values())


def _validate_panel_row(row: dict, row_number: int, units: str) -> tuple[dict | None, CsvValidationError | None]:
    missing = [field for field in REQUIRED_COLUMNS if not row.get(field)]
    if missing:
        return None, CsvValidationError(row_number, f"Missing required fields: {', '.join(missing)}.")

    id_value = row["id"]
    width_value, width_error = _parse_positive_float(row["width"], row_number, "Width")
    if width_error:
        return None, width_error
    height_value, height_error = _parse_positive_float(row["height"], row_number, "Height")
    if height_error:
        return None, height_error

    width_value = _convert_units(width_value, units)
    height_value = _convert_units(height_value, units)

    qty_value, qty_error = _parse_positive_int(row.get("qty", ""), row_number, "Quantity")
    if qty_error:
        return None, qty_error

    label = row.get("label") or ""
    material = row.get("material") or ""
    grain_direction = row.get("grain_direction")

    allow_rotate = _parse_allow_rotate(row)

    panel = {
        "id": id_value,
        "width": width_value,
        "height": height_value,
        "qty": qty_value,
        "label": label or id_value,
        "material": material,
        "allow_rotate": allow_rotate,
    }
    if grain_direction:
        panel["grainDirection"] = grain_direction
    return panel, None


def _parse_positive_float(value: str, row_number: int, label: str) -> tuple[float | None, CsvValidationError | None]:
    text = (value or "").strip()
    if not text:
        return None, CsvValidationError(row_number, f"{label} is missing.")
    try:
        number = float(text)
    except ValueError:
        return None, CsvValidationError(row_number, f"{label} must be a number (got '{text}').")
    if number <= 0:
        return None, CsvValidationError(row_number, f"{label} must be greater than zero (got '{text}').")
    return number, None


def _parse_positive_int(value: str, row_number: int, label: str) -> tuple[int, CsvValidationError | None]:
    text = (value or "").strip()
    if not text:
        return 1, None
    try:
        number = int(text)
    except ValueError:
        return 0, CsvValidationError(row_number, f"{label} must be an integer (got '{text}').")
    if number <= 0:
        return 0, CsvValidationError(row_number, f"{label} must be greater than zero (got '{text}').")
    return number, None


def _parse_allow_rotate(row: dict) -> bool:
    raw = row.get("allow_rotate")
    if raw:
        return raw.lower() in ("1", "true", "yes", "y")
    if session_state is None:
        return False
    try:
        return session_state.get_default_allow_rotate()
    except Exception:
        return False


def _convert_units(value: float, units: str) -> float:
    if units == "in":
        return value * MM_PER_INCH
    return value
