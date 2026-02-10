"""@codex
Core nesting strategies for SquatchCut.

Algorithms:
- `nest_on_multiple_sheets`: material/yield-focused shelf nesting.
- `nest_cut_optimized`: row/column heuristic to approximate fewer saw cuts.
Utilities:
- `estimate_cut_counts` and `compute_utilization` to summarize layouts.
Pure logic module: no FreeCAD or GUI dependencies.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional, Union

__all__ = [
    "run_shelf_nesting",
    "nest_on_multiple_sheets",
    "nest_cut_optimized",
    "nest_parts",
    "NestingConfig",
    "expand_sheet_sizes",
    "get_effective_job_sheets_for_nesting",
    "derive_sheet_definitions_for_mode",
    "derive_sheet_sizes_for_layout",
    "get_effective_spacing",
    "estimate_cut_counts",
    "compute_utilization",
    "analyze_sheet_exhaustion",
    "Part",
    "PlacedPart",
    "NestingValidationError",
    "NestingOffendingPart",
    "get_usable_sheet_area",
    "part_fits_sheet",
    "validate_parts_fit_sheet",
]


@dataclass
class Part:
    id: str
    width: float  # mm
    height: float  # mm
    can_rotate: bool = False  # whether this part is allowed to rotate 90°


@dataclass
class PlacedPart:
    id: str
    sheet_index: int  # 0-based sheet number
    x: float
    y: float
    width: float
    height: float
    rotation_deg: int = 0  # 0 or 90


@dataclass
class NestingConfig:
    """
    Configuration for nesting strategy selection.

    optimize_for_cut_path:
        When True, use guillotine-style nesting to prioritize cut-aligned layouts.
    kerf_width_mm:
        Spacing between parts when optimize_for_cut_path is enabled.
    allowed_rotations_deg:
        Allowed rotation angles for parts; defaults to 0 and 90 degrees.
    """

    optimize_for_cut_path: bool = False
    kerf_width_mm: float = 3.0
    allowed_rotations_deg: tuple[int, ...] = (0, 90)
    spacing_mm: float = 0.0
    measurement_system: str = "metric"
    export_include_labels: bool = True
    export_include_dimensions: bool = False
    nesting_mode: str = "pack"  # "pack" (default) or "cut_friendly"


@dataclass
class NestingOffendingPart:
    part_id: str
    width: float
    height: float
    can_rotate: bool


class NestingValidationError(Exception):
    """
    Raised when one or more parts cannot fit inside the usable sheet area.
    """

    def __init__(
        self,
        usable_width: float,
        usable_height: float,
        offending_parts: tuple[NestingOffendingPart, ...],
    ):
        self.usable_width = usable_width
        self.usable_height = usable_height
        self.offending_parts = offending_parts
        super().__init__(
            f"Parts do not fit usable sheet area {usable_width} x {usable_height}: "
            + ", ".join(p.part_id for p in offending_parts)
        )


def get_usable_sheet_area(
    sheet_width: float, sheet_height: float, margin_mm: float = 0.0
) -> tuple[float, float]:
    """
    Return the usable width and height after subtracting edge margins.
    """
    usable_width = max(0.0, sheet_width - 2 * max(margin_mm, 0.0))
    usable_height = max(0.0, sheet_height - 2 * max(margin_mm, 0.0))
    return usable_width, usable_height


def _get_sheet_entry_field(entry: Any, *keys: str):
    if entry is None:
        return None
    if isinstance(entry, dict):
        for key in keys:
            if key in entry:
                return entry.get(key)
        return None
    for key in keys:
        if hasattr(entry, key):
            return getattr(entry, key)
    return None


def _normalize_sheet_definition(entry: Any) -> Optional[dict]:
    """Return normalized sheet definition dict or None if invalid."""
    width_raw = _get_sheet_entry_field(entry, "width_mm", "width")
    height_raw = _get_sheet_entry_field(entry, "height_mm", "height")
    try:
        width = float(width_raw)
    except Exception:
        width = None
    try:
        height = float(height_raw)
    except Exception:
        height = None
    if not width or not height or width <= 0 or height <= 0:
        return None

    quantity_raw = _get_sheet_entry_field(entry, "quantity")
    try:
        quantity = max(1, int(float(quantity_raw)))
    except Exception:
        quantity = 1

    label_raw = _get_sheet_entry_field(entry, "label", "name")
    label = str(label_raw) if label_raw not in (None, "") else None

    return {
        "width_mm": width,
        "height_mm": height,
        "quantity": quantity,
        "label": label,
    }


def expand_sheet_sizes(sheet_entries: list[dict]) -> list[tuple[float, float]]:
    """Return a flattened list of sheet (width, height) tuples based on job sheet entries."""
    result: list[tuple[float, float]] = []
    for entry in sheet_entries or []:
        normalized = _normalize_sheet_definition(entry)
        if not normalized:
            continue
        width = normalized["width_mm"]
        height = normalized["height_mm"]
        quantity = normalized.get("quantity", 1) or 1
        for _ in range(quantity):
            result.append((width, height))
    return result


def derive_sheet_definitions_for_mode(
    sheet_mode: str,
    job_sheets: Optional[list[dict]],
    default_width: Optional[float],
    default_height: Optional[float],
) -> list[dict]:
    """
    Return sheet definitions honoring sheet mode.

    - Simple mode returns an empty list so callers repeat the default sheet as needed.
    - Job sheets mode uses the supplied definitions verbatim (invalid ones filtered out elsewhere).
    """
    if sheet_mode == "job_sheets":
        return get_effective_job_sheets_for_nesting(sheet_mode, job_sheets)
    # Simple mode: rely on default repeated sheet (no explicit definitions)
    return []


def get_effective_job_sheets_for_nesting(
    sheet_mode: str,
    job_sheets: Optional[list[dict]],
) -> list[dict]:
    """
    Normalize and filter the explicit job sheets to be used for nesting.

    Returns an ordered list; empty list indicates either simple mode or that no valid sheets were configured.
    """
    if sheet_mode != "job_sheets":
        return []
    normalized: list[dict] = []
    for entry in job_sheets or []:
        data = _normalize_sheet_definition(entry)
        if data:
            normalized.append(data)
    return normalized


def derive_sheet_sizes_for_layout(
    sheet_mode: str,
    job_sheets: Optional[list[dict]],
    default_width: Optional[float],
    default_height: Optional[float],
    placements: Optional[list[PlacedPart]] = None,
) -> list[tuple[float, float]]:
    """
    Determine concrete sheet sizes to render layout geometry for the current mode.
    """
    if sheet_mode == "job_sheets":
        sizes = expand_sheet_sizes(job_sheets or [])
        if sizes:
            return sizes
    if default_width and default_height:
        count = 1
        if placements:
            count = max((pp.sheet_index for pp in placements), default=0) + 1
        return [(default_width, default_height)] * max(count, 1)
    return []


def resolve_sheet_dimensions(
    sheet_sizes: list[tuple[float, float]],
    index: int,
    fallback_width: float,
    fallback_height: float,
) -> tuple[float, float]:
    """Return the sheet dimensions for the requested index (clamped)."""
    if sheet_sizes:
        idx = max(0, min(index, len(sheet_sizes) - 1))
        width, height = sheet_sizes[idx]
        if width > 0 and height > 0:
            return width, height
        if len(sheet_sizes) > 1:
            for w, h in reversed(sheet_sizes[: idx + 1]):
                if w > 0 and h > 0:
                    return w, h
    if fallback_width > 0 and fallback_height > 0:
        return fallback_width, fallback_height
    return fallback_width, fallback_height


def part_fits_sheet(
    part_width: float,
    part_height: float,
    usable_width: float,
    usable_height: float,
    can_rotate: bool = False,
) -> bool:
    """
    Determine whether a part fits inside the usable area, optionally with rotation.
    """
    if part_width <= usable_width and part_height <= usable_height:
        return True
    if can_rotate and part_height <= usable_width and part_width <= usable_height:
        return True
    return False


def validate_parts_fit_sheet(
    parts: list[Part],
    usable_width: float,
    usable_height: float,
) -> None:
    """
    Raise NestingValidationError if any part cannot fit the usable sheet area.
    """
    offending: list[NestingOffendingPart] = []
    for part in parts or []:
        if not part_fits_sheet(
            part.width, part.height, usable_width, usable_height, part.can_rotate
        ):
            offending.append(
                NestingOffendingPart(
                    part_id=part.id,
                    width=part.width,
                    height=part.height,
                    can_rotate=part.can_rotate,
                )
            )
    if offending:
        raise NestingValidationError(
            usable_width=usable_width,
            usable_height=usable_height,
            offending_parts=tuple(offending),
        )


def get_effective_spacing(config) -> float:
    """
    Return effective spacing (base spacing + kerf width) to keep parts separated.
    """
    base_spacing = float(getattr(config, "spacing_mm", 0.0) or 0.0)
    kerf = float(getattr(config, "kerf_width_mm", 0.0) or 0.0)
    return max(0.0, base_spacing + kerf)


def nest_on_multiple_sheets(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    config: Optional[NestingConfig] = None,
    sheet_definitions: Optional[list[dict]] = None,
) -> list[PlacedPart]:
    """
    Entry that runs the default shelf-based nesting across the supplied sheet definitions.
    """
    import importlib

    shelf_module = importlib.import_module("SquatchCut.core.strategies.shelf")
    shelf_nest = shelf_module.nest_on_multiple_sheets

    return shelf_nest(
        parts,
        sheet_width,
        sheet_height,
        config=config,
        sheet_definitions=sheet_definitions,
    )


def nest_cut_optimized(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    kerf: float = 0.0,
    margin: float = 0.0,
    sheet_sizes: Optional[list[tuple[float, float]]] = None,
) -> list[PlacedPart]:
    """
    Row/column oriented heuristic intended to reduce distinct cut lines.
    """

    import importlib

    cut_optimized_module = importlib.import_module(
        "SquatchCut.core.strategies.cut_optimized"
    )
    cut_optimized_nest = cut_optimized_module.nest_cut_optimized

    return cut_optimized_nest(
        parts,
        sheet_width,
        sheet_height,
        kerf=kerf,
        margin=margin,
        sheet_sizes=sheet_sizes,
    )


def nest_parts(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    config: Optional[NestingConfig] = None,
    sheet_sizes: Optional[list[tuple[float, float]]] = None,
) -> list[PlacedPart]:
    """
    Strategy selector for nesting.
    - When optimize_for_cut_path is True, use guillotine-style nesting.
    - Otherwise, fall back to the default shelf-based nesting.
    """
    cfg = config or NestingConfig()
    sizes = sheet_sizes or []
    if cfg.optimize_for_cut_path:
        from SquatchCut.core import cut_optimization

        return cut_optimization.guillotine_nest_parts(
            parts,
            {"width": sheet_width, "height": sheet_height},
            cfg,
            sheet_sizes=sizes,
        )
    if getattr(cfg, "nesting_mode", "pack") == "cut_friendly":
        import importlib

        cut_friendly_module = importlib.import_module(
            "SquatchCut.core.strategies.cut_friendly"
        )
        return cut_friendly_module.nest_cut_friendly(
            parts,
            sheet_width,
            sheet_height,
            cfg,
            sheet_sizes=sizes,
        )
    import importlib

    shelf_module = importlib.import_module("SquatchCut.core.strategies.shelf")
    return shelf_module.pack_parts(
        parts,
        sheet_width,
        sheet_height,
        cfg,
        sheet_sizes=sizes if sizes else None,
    )


def estimate_cut_counts(
    placements: list[PlacedPart],
    sheet_width: Optional[float] = None,
    sheet_height: Optional[float] = None,
) -> dict:
    """
    Approximate saw cut counts by collecting unique vertical and horizontal cut lines.

    - Vertical cuts are inferred from x boundaries of placed parts (and sheet edges if provided).
    - Horizontal cuts use y boundaries of placed parts (and sheet edges if provided).
    """
    if not placements:
        return {"vertical": 0, "horizontal": 0, "total": 0}

    vertical = set()
    horizontal = set()

    if sheet_width is not None:
        vertical.add(0.0)
        vertical.add(float(sheet_width))
    if sheet_height is not None:
        horizontal.add(0.0)
        horizontal.add(float(sheet_height))

    for pp in placements:
        vertical.add(round(pp.x, 4))
        vertical.add(round(pp.x + pp.width, 4))
        horizontal.add(round(pp.y, 4))
        horizontal.add(round(pp.y + pp.height, 4))

    v_count = len(vertical)
    h_count = len(horizontal)
    return {"vertical": v_count, "horizontal": h_count, "total": v_count + h_count}


def estimate_cut_counts_for_sheets(
    placements: list[PlacedPart],
    sheet_sizes: list[tuple[float, float]],
) -> dict:
    """
    Approximate cut counts when nesting spans sheets of potentially varying dimensions.
    """
    if not placements or not sheet_sizes:
        return {"vertical": 0, "horizontal": 0, "total": 0}
    vertical = set()
    horizontal = set()
    fallback_width, fallback_height = sheet_sizes[0]
    for pp in placements:
        sw, sh = resolve_sheet_dimensions(
            sheet_sizes, pp.sheet_index, fallback_width, fallback_height
        )
        vertical.add(0.0)
        vertical.add(float(sw))
        horizontal.add(0.0)
        horizontal.add(float(sh))
    for pp in placements:
        vertical.add(round(pp.x, 4))
        vertical.add(round(pp.x + pp.width, 4))
        horizontal.add(round(pp.y, 4))
        horizontal.add(round(pp.y + pp.height, 4))
    v_count = len(vertical)
    h_count = len(horizontal)
    return {"vertical": v_count, "horizontal": h_count, "total": v_count + h_count}


def _group_placements_by_sheet(
    placements: list[PlacedPart],
) -> dict[int, list[PlacedPart]]:
    """Group placements by their sheet index for per-sheet statistics."""
    grouped: dict[int, list[PlacedPart]] = defaultdict(list)
    for placement in placements:
        grouped[placement.sheet_index].append(placement)
    return grouped


def compute_utilization(
    placements: list[PlacedPart],
    sheet_width: float,
    sheet_height: float,
) -> dict:
    """
    Compute basic material utilization metrics for a set of placements.
    Returns: {"utilization_percent": float, "sheets_used": int, "placed_area": float, "sheet_area": float}
    """
    if not placements or sheet_width <= 0 or sheet_height <= 0:
        return {
            "utilization_percent": 0.0,
            "sheets_used": 0,
            "placed_area": 0.0,
            "sheet_area": 0.0,
        }

    sheets_used = max(pp.sheet_index for pp in placements) + 1
    placed_area = sum(pp.width * pp.height for pp in placements)
    sheet_area = sheet_width * sheet_height * sheets_used
    util = (placed_area / sheet_area) * 100.0 if sheet_area > 0 else 0.0

    return {
        "utilization_percent": util,
        "sheets_used": sheets_used,
        "placed_area": placed_area,
        "sheet_area": sheet_area,
    }


def compute_utilization_for_sheets(
    placements: list[PlacedPart],
    sheet_sizes: list[tuple[float, float]],
) -> dict:
    if not placements or not sheet_sizes:
        return {
            "utilization_percent": 0.0,
            "sheets_used": 0,
            "placed_area": 0.0,
            "sheet_area": 0.0,
            "per_sheet_stats": [],
        }
    fallback_width, fallback_height = sheet_sizes[0]
    used_sheet_indices = {pp.sheet_index for pp in placements}
    total_sheet_area = 0.0
    per_sheet_stats: list[dict[str, Union[int, float]]] = []
    placements_by_sheet = _group_placements_by_sheet(placements)

    for sheet_index in sorted(used_sheet_indices):
        sw, sh = resolve_sheet_dimensions(
            sheet_sizes, sheet_index, fallback_width, fallback_height
        )
        sheet_area = sw * sh
        total_sheet_area += sheet_area
        sheet_parts = placements_by_sheet.get(sheet_index, [])
        placed_area_for_sheet = sum(pp.width * pp.height for pp in sheet_parts)
        utilization_percent_for_sheet = (
            (placed_area_for_sheet / sheet_area) * 100.0 if sheet_area > 0 else 0.0
        )
        per_sheet_stats.append(
            {
                "sheet_index": sheet_index,
                "width_mm": sw,
                "height_mm": sh,
                "sheet_area": sheet_area,
                "placed_area": placed_area_for_sheet,
                "utilization_percent": utilization_percent_for_sheet,
                "parts_placed": len(sheet_parts),
                "waste_area": max(sheet_area - placed_area_for_sheet, 0.0),
            }
        )
    placed_area = sum(pp.width * pp.height for pp in placements)
    util_percent = (
        (placed_area / total_sheet_area) * 100.0 if total_sheet_area > 0 else 0.0
    )
    return {
        "utilization_percent": util_percent,
        "sheets_used": len(used_sheet_indices),
        "placed_area": placed_area,
        "sheet_area": total_sheet_area,
        "per_sheet_stats": per_sheet_stats,
    }


def analyze_sheet_exhaustion(
    placements: list[PlacedPart],
    sheet_sizes: Optional[list[tuple[float, float]]] = None,
) -> dict[str, Union[int, bool]]:
    """
    Analyze whether sheet quantities were exhausted during nesting.

    Returns a dict with keys:
    - 'sheets_available': total number of sheet instances available
    - 'sheets_used': number of distinct sheets with at least one part
    - 'sheets_exhausted': boolean indicating if all available sheets were used
    - 'max_sheet_index': highest sheet index used (0-based)
    """
    if not placements:
        return {
            "sheets_available": len(sheet_sizes) if sheet_sizes else 0,
            "sheets_used": 0,
            "sheets_exhausted": False,
            "max_sheet_index": -1,
        }

    used_sheet_indices = {pp.sheet_index for pp in placements}
    sheets_used = len(used_sheet_indices)
    max_sheet_index = max(used_sheet_indices) if used_sheet_indices else -1
    sheets_available = len(sheet_sizes) if sheet_sizes else 0

    # Exhaustion occurs when we use more sheets than are available
    # (due to resolve_sheet_dimensions clamping to last available sheet)
    sheets_exhausted = sheets_available > 0 and max_sheet_index >= sheets_available

    return {
        "sheets_available": sheets_available,
        "sheets_used": sheets_used,
        "sheets_exhausted": sheets_exhausted,
        "max_sheet_index": max_sheet_index,
    }


def run_shelf_nesting(
    sheet_width: float,
    sheet_height: float,
    panels: list[dict],
    margin: float = 5.0,
) -> list[dict]:
    """
    Very simple shelf nesting algorithm.

    Returns a list of placement dicts:
    {
        "x": float,
        "y": float,
        "width": float,
        "height": float,
        "panel_index": int,   # index into the input panels list
        "instance_index": int # 0..qty-1 for that panel
    }
    """
    if not panels or sheet_width <= 0 or sheet_height <= 0:
        return []

    expanded = []
    for idx, panel in enumerate(panels):
        try:
            w = float(panel.get("width", 0))
            h = float(panel.get("height", 0))
        except Exception:
            continue
        if w <= 0 or h <= 0:
            continue
        qty = int(panel.get("qty", 1) or 1)
        for instance_index in range(qty):
            expanded.append(
                {
                    "width": w,
                    "height": h,
                    "panel_index": idx,
                    "instance_index": instance_index,
                }
            )

    expanded.sort(key=lambda p: (p["height"], p["width"]), reverse=True)

    placements: list[dict] = []
    usable_width = sheet_width - 2 * margin
    usable_height = sheet_height - 2 * margin

    current_x = margin
    current_y = margin
    current_row_height = 0.0

    for p in expanded:
        w = p["width"]
        h = p["height"]

        if w > usable_width or h > usable_height:
            continue

        if current_x + w > sheet_width - margin:
            current_x = margin
            current_y += current_row_height + margin
            current_row_height = 0.0

        if current_y + h > sheet_height - margin:
            break

        placements.append(
            {
                "x": current_x,
                "y": current_y,
                "width": w,
                "height": h,
                "panel_index": p["panel_index"],
                "instance_index": p["instance_index"],
            }
        )

        current_x += w + margin
        current_row_height = max(current_row_height, h)

    return placements
