"""@codex
Module: CSV loader for panel definitions used by SquatchCut.
Boundaries: Do not touch FreeCAD documents or geometry; only read, validate, and normalize CSV data into panels.
Primary methods: load_file, _read_rows, _validate_rows, _normalize_types_and_units, _to_panels.
Note: Update incrementally; do not overwrite this module when adding logic.
"""

from __future__ import annotations

import csv
import re

from SquatchCut.freecad_integration import App

MM_PER_INCH = 25.4


def parse_fractional_inch(value_str: str) -> float:
    """
    Parse fractional inch strings like '23 1/4', '12 3/8', '24' into decimal inches.

    Args:
        value_str: String like "23 1/4" or "12.5" or "24"

    Returns:
        Decimal inch value as float
    """
    value_str = str(value_str).strip()

    # Check for fractional pattern like "23 1/4"
    fraction_match = re.match(r"^(\d+)\s+(\d+)/(\d+)$", value_str)
    if fraction_match:
        whole, numerator, denominator = fraction_match.groups()
        return float(whole) + float(numerator) / float(denominator)

    # Check for just fraction like "3/4"
    fraction_only_match = re.match(r"^(\d+)/(\d+)$", value_str)
    if fraction_only_match:
        numerator, denominator = fraction_only_match.groups()
        return float(numerator) / float(denominator)

    # Otherwise try to parse as regular decimal
    return float(value_str)


def in_to_mm(value_in_inch: float) -> float:
    """Convert inches to millimeters."""
    return float(value_in_inch) * MM_PER_INCH


def detect_csv_units(path: str) -> str:
    """
    Auto-detect if CSV contains imperial (fractional inches) or metric units.

    Returns:
        "imperial" if fractional inches detected, "metric" otherwise
    """
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)

            # Look at first few rows for fractional patterns
            rows_checked = 0
            for row in reader:
                if rows_checked >= 5:  # Check first 5 rows max
                    break

                width = str(row.get("width", "")).strip()
                height = str(row.get("height", "")).strip()

                # Check for fractional inch patterns like "23 1/4", "12 3/8", etc.
                fraction_pattern = r"\d+\s+\d+/\d+"
                if re.search(fraction_pattern, width) or re.search(
                    fraction_pattern, height
                ):
                    return "imperial"

                rows_checked += 1

        return "metric"
    except Exception:
        # If we can't read the file, default to metric
        return "metric"


class CsvLoader:
    """Loads panel definitions from CSV and returns normalized panel objects."""

    def load_file(self, path: str, csv_units: str = "metric") -> list[dict]:
        """Load a CSV file and return panel objects."""
        return self.load_csv(path, csv_units=csv_units)

    def load_csv(self, path: str, csv_units: str = "metric") -> list[dict]:
        """Load CSV rows, validate, and convert to panel objects."""
        import csv

        rows = []
        try:
            with open(path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for idx, row in enumerate(reader, start=1):
                    cleaned = self.validate_row(row, idx, csv_units=csv_units)
                    panel = self.to_panel_object(cleaned)
                    rows.append(panel)
        except FileNotFoundError as exc:
            raise ValueError(f"CSV file not found: {path}") from exc
        return rows

    def validate_row(
        self, row: dict, row_number: int | None = None, csv_units: str = "metric"
    ) -> dict:
        """Validate a single CSV row, ensuring required fields exist."""
        missing = [key for key in ("id", "width", "height") if not row.get(key)]
        if missing:
            prefix = f"Row {row_number}: " if row_number else ""
            raise ValueError(f"{prefix}Missing required fields: {', '.join(missing)}")

        try:
            if str(csv_units).lower() == "imperial":
                width = parse_fractional_inch(row["width"])
                height = parse_fractional_inch(row["height"])
            else:
                width = float(row["width"])
                height = float(row["height"])
        except (TypeError, ValueError) as exc:
            prefix = f"Row {row_number}: " if row_number else ""
            raise ValueError(f"{prefix}Width/height must be numeric") from exc

        if width <= 0 or height <= 0:
            prefix = f"Row {row_number}: " if row_number else ""
            raise ValueError(f"{prefix}Width/height must be greater than zero")

        if str(csv_units).lower() == "imperial":
            width = in_to_mm(width)
            height = in_to_mm(height)

        cleaned = {
            "id": str(row["id"]).strip(),
            "width": width,
            "height": height,
        }
        if row.get("grain_direction"):
            cleaned["grain_direction"] = str(row["grain_direction"]).strip()
        allow_rotate_raw = None
        # Support both exact and case-insensitive allow_rotate
        for key in row.keys():
            if key and key.strip().lower() == "allow_rotate":
                allow_rotate_raw = row.get(key)
                break
        if allow_rotate_raw is not None:
            cleaned["allow_rotate"] = str(allow_rotate_raw).strip().lower() in (
                "1",
                "true",
                "yes",
                "y",
            )
        else:
            cleaned["allow_rotate"] = False
        return cleaned

    def to_panel_object(self, row: dict) -> dict:
        """Map a validated row into the panel object format."""
        panel = {
            "id": row["id"],
            "width": row["width"],
            "height": row["height"],
            "allow_rotate": bool(row.get("allow_rotate", False)),
        }
        grain = row.get("grain_direction")
        if grain:
            panel["grainDirection"] = grain
        return panel

    # Legacy helper names retained for compatibility
    def _read_rows(self, path: str) -> list[dict]:
        """Read raw CSV rows from disk."""
        return self.load_csv(path)

    def _validate_rows(self, rows: list[dict]) -> list[dict]:
        """Validate CSV rows and raise on missing/invalid fields."""
        validated = []
        for idx, row in enumerate(rows, start=1):
            validated.append(self.validate_row(row, idx))
        return validated

    def _normalize_types_and_units(self, rows: list[dict]) -> list[dict]:
        """Normalize numeric fields and units across rows."""
        return self._validate_rows(rows)

    def _to_panels(self, rows: list[dict]) -> list[dict]:
        """Produce a list of panel objects from validated rows."""
        return [self.to_panel_object(row) for row in rows]


def load_csv(path: str, csv_units: str = "metric") -> list[dict]:
    """
    Simple CSV loader for SquatchCut panels.

    Expects headers: width, height (required), optional qty, label, material.
    Returns a list of dicts with normalized types and default values.
    """
    panels: list[dict] = []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                msg = f">>> [SquatchCut] load_csv: missing header row in {path}\n"
                if App:
                    App.Console.PrintError(msg)
                raise ValueError("Missing CSV header row")
            headers = {name.strip().lower() for name in reader.fieldnames if name}
            required = {"width", "height"}
            missing = required - headers
            if missing:
                msg = f">>> [SquatchCut] load_csv: missing required headers: {', '.join(sorted(missing))}\n"
                if App:
                    App.Console.PrintError(msg)
                raise ValueError(
                    f"Missing required headers: {', '.join(sorted(missing))}"
                )

            for idx, row in enumerate(reader, start=1):
                try:
                    width_raw = row.get("width", "") if row else ""
                    height_raw = row.get("height", "") if row else ""

                    if str(csv_units).lower() == "imperial":
                        width = (
                            parse_fractional_inch(width_raw)
                            if width_raw not in (None, "")
                            else None
                        )
                        height = (
                            parse_fractional_inch(height_raw)
                            if height_raw not in (None, "")
                            else None
                        )
                    else:
                        width = (
                            float(width_raw) if width_raw not in (None, "") else None
                        )
                        height = (
                            float(height_raw) if height_raw not in (None, "") else None
                        )

                    if width is None or height is None:
                        raise ValueError("Width/height missing")

                    if str(csv_units).lower() == "imperial":
                        width = in_to_mm(width)
                        height = in_to_mm(height)

                    qty_raw = row.get("qty", "") if row else ""
                    try:
                        qty = int(qty_raw) if str(qty_raw).strip() else 1
                    except (TypeError, ValueError):
                        qty = 1

                    label = str(row.get("label", "") or "").strip()
                    part_id = str(row.get("id", "") or "").strip()
                    material = str(row.get("material", "") or "").strip()
                    from SquatchCut.core.session_state import get_default_allow_rotate

                    allow_raw = None
                    if "allow_rotate" in headers:
                        allow_raw = row.get("allow_rotate", "")
                    if allow_raw is None or str(allow_raw).strip() == "":
                        allow_rotate = get_default_allow_rotate()
                    else:
                        allow_rotate = str(allow_raw).strip().lower() in (
                            "1",
                            "true",
                            "yes",
                            "y",
                        )

                    panels.append(
                        {
                            "id": part_id or label or f"panel_{idx}",
                            "width": float(width),
                            "height": float(height),
                            "qty": int(qty),
                            "label": label,
                            "material": material,
                            "allow_rotate": allow_rotate,
                        }
                    )
                except Exception as exc:
                    App.Console.PrintError(
                        f">>> [SquatchCut] load_csv: skipping row {idx} due to error: {exc}\n"
                    )
                    continue
    except FileNotFoundError:
        if App:
            App.Console.PrintError(
                f">>> [SquatchCut] load_csv: file not found: {path}\n"
            )
        raise
    except Exception:
        # Error already logged above where possible
        raise

    if App:
        App.Console.PrintMessage(
            f">>> [SquatchCut] load_csv: loaded {len(panels)} panel rows from {path}\n"
        )
    return panels
