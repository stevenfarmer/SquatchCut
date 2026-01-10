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

from dataclasses import dataclass
from typing import Any

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


def _normalize_sheet_definition(entry: Any) -> dict | None:
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
    job_sheets: list[dict] | None,
    default_width: float | None,
    default_height: float | None,
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
    job_sheets: list[dict] | None,
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
    job_sheets: list[dict] | None,
    default_width: float | None,
    default_height: float | None,
    placements: list[PlacedPart] | None = None,
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


def _nest_rectangular_default(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    config: NestingConfig | None = None,
    sheet_sizes: list[tuple[float, float]] | None = None,
) -> list[PlacedPart]:
    """
    Shelf-based rectangle packing across multiple sheets with optional 90° rotation.

    Rules:
    - Each sheet is divided into horizontal rows (shelves).
    - Each row has a fixed height determined by the first part placed in it.
    - Subsequent parts added to a row must have height <= row_height.
    - Parts may be rotated 90° (if can_rotate=True) to try to fit.
    - No row "grows" taller after creation, which guarantees no vertical overlap.
    - New rows are stacked vertically until the sheet is full.
    - New sheets are created as needed.
    - Returns a flat list of PlacedPart with sheet_index + x/y + rotation_deg.

    Raises ValueError if any part cannot fit on a sheet in any allowed orientation.
    """

    cfg = config or NestingConfig()
    spacing = get_effective_spacing(cfg)
    configured_sizes = sheet_sizes if sheet_sizes else [(sheet_width, sheet_height)]

    # Early validation: each part must fit on at least one configured sheet.
    for p in parts:
        fits_somewhere = False
        for sw, sh in configured_sizes:
            if sw <= 0 or sh <= 0:
                continue
            can_fit_unrotated = p.width <= sw and p.height <= sh
            can_fit_rotated = p.can_rotate and p.height <= sw and p.width <= sh
            if can_fit_unrotated or can_fit_rotated:
                fits_somewhere = True
                break
        if not fits_somewhere:
            sw, sh = configured_sizes[0]
            raise ValueError(
                f"Part {p.id} ({p.width} x {p.height}) does not fit "
                f"on sheet {sw} x {sh} in any allowed orientation."
            )

    # Sort by max dimension so bigger parts get placed first.
    remaining = sorted(
        parts,
        key=lambda p: max(p.width, p.height),
        reverse=True,
    )

    placed: list[PlacedPart] = []

    # Each sheet is a list of rows.
    # Each row is a dict: {"y": float, "height": float, "used_width": float}
    sheets: list[list[dict]] = []
    sheets.append([])  # first sheet with no rows yet

    def _sheet_dimensions(index: int) -> tuple[float, float]:
        return resolve_sheet_dimensions(
            sheet_sizes or [], index, sheet_width, sheet_height
        )

    def orientations_for_part(p: Part):
        """Yield (w, h, rot_deg) options, preferring 0° then 90°."""
        yield p.width, p.height, 0
        if p.can_rotate and p.width != p.height:
            yield p.height, p.width, 90

    for part in remaining:
        placed_on_sheet = False

        # Try to place the part on existing sheets
        for sheet_index, rows in enumerate(sheets):
            # Compute current total height for this sheet from its rows + spacing between rows
            total_height = 0.0
            for idx, r in enumerate(rows):
                total_height += r["height"]
                if idx < len(rows) - 1:
                    total_height += spacing

            current_sheet_width, current_sheet_height = _sheet_dimensions(sheet_index)
            # 1) Try to place in existing rows on this sheet
            for row in rows:
                for w, h, rot in orientations_for_part(part):
                    # Must fit within row height and sheet width
                    if h > row["height"]:
                        continue
                    if row["used_width"] + w + spacing > current_sheet_width + 1e-6:
                        continue

                    # Place in this row
                    x = row["used_width"]
                    y = row["y"]

                    placed.append(
                        PlacedPart(
                            id=part.id,
                            sheet_index=sheet_index,
                            x=x,
                            y=y,
                            width=w,
                            height=h,
                            rotation_deg=rot,
                        )
                    )

                    row["used_width"] += w + spacing
                    placed_on_sheet = True
                    break  # out of orientations

                if placed_on_sheet:
                    break  # out of rows

            if placed_on_sheet:
                break  # out of sheets

            # 2) Couldn't fit in any existing row; try to open a new row on this sheet.
            for w, h, rot in orientations_for_part(part):
                if w > current_sheet_width:
                    continue

                row_spacing = spacing if rows else 0.0
                row_y = total_height + row_spacing
                new_total_height = row_y + h
                if new_total_height > current_sheet_height:
                    continue

                # Start a new row with fixed height = h
                new_row = {
                    "y": row_y,
                    "height": h,
                    "used_width": w + spacing,
                }
                rows.append(new_row)

                placed.append(
                    PlacedPart(
                        id=part.id,
                        sheet_index=sheet_index,
                        x=0.0,
                        y=row_y,
                        width=w,
                        height=h,
                        rotation_deg=rot,
                    )
                )
                placed_on_sheet = True
                break  # out of orientations

            if placed_on_sheet:
                break  # out of sheets

        if placed_on_sheet:
            continue

        # 3) Could not place on any existing sheet → create a new sheet
        new_sheet_index = len(sheets)

        # Check if we're exceeding available sheet quantities
        if sheet_sizes and new_sheet_index >= len(sheet_sizes):
            try:
                from SquatchCut.core import logger

                available_sheets = len(sheet_sizes)
                logger.warning(
                    f">>> [SquatchCut] Sheet exhaustion: trying to use sheet {new_sheet_index + 1} "
                    f"but only {available_sheets} sheet(s) available. Using last available sheet type."
                )
            except Exception:
                # Fallback if logger import fails
                import warnings

                warnings.warn(
                    f"Sheet exhaustion: trying to use sheet {new_sheet_index + 1} "
                    f"but only {len(sheet_sizes)} sheet(s) available.",
                    stacklevel=2,
                )

        new_rows: list[dict] = []
        sheets.append(new_rows)

        placed_here = False
        new_sheet_width, new_sheet_height = _sheet_dimensions(new_sheet_index)
        for w, h, rot in orientations_for_part(part):
            if w <= new_sheet_width and h <= new_sheet_height:
                new_row = {
                    "y": 0.0,
                    "height": h,
                    "used_width": w,
                }
                new_rows.append(new_row)

                placed.append(
                    PlacedPart(
                        id=part.id,
                        sheet_index=new_sheet_index,
                        x=0.0,
                        y=0.0,
                        width=w,
                        height=h,
                        rotation_deg=rot,
                    )
                )
                placed_here = True
                break

        if not placed_here:
            sw, sh = new_sheet_width, new_sheet_height
            raise ValueError(
                f"Part {part.id} ({part.width} x {part.height}) unexpectedly "
                f"cannot be placed on a new sheet {sw} x {sh}."
            )

    return placed


def nest_on_multiple_sheets(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    config: NestingConfig | None = None,
    sheet_definitions: list[dict] | None = None,
) -> list[PlacedPart]:
    """
    Entry that runs the default shelf-based nesting across the supplied sheet definitions.
    """
    # Standard shelf nesting already respects explicit job sheets via sheet_definitions.
    sheet_sizes = expand_sheet_sizes(sheet_definitions or [])
    if not sheet_sizes:
        sheet_sizes = [(sheet_width, sheet_height)]
    return _nest_rectangular_default(
        parts,
        sheet_width,
        sheet_height,
        config=config,
        sheet_sizes=sheet_sizes,
    )


def nest_cut_optimized(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    kerf: float = 0.0,
    margin: float = 0.0,
    sheet_sizes: list[tuple[float, float]] | None = None,
) -> list[PlacedPart]:
    """
    Row/column oriented heuristic intended to reduce distinct cut lines.

    - Builds rows top-to-bottom.
    - Places parts left-to-right within a row, keeping aligned edges.
    - Starts new rows (or sheets) when horizontal space is exhausted.
    - Respects simple kerf spacing and edge margin.
    - Heuristic only: trades some yield for more aligned rip/crosscut lines.
    """
    if sheet_width <= 0 or sheet_height <= 0:
        return []

    spacing = max(0.0, kerf)
    margin = max(0.0, margin)
    configured_sizes = sheet_sizes or [(sheet_width, sheet_height)]

    def _usable_dims(sw: float, sh: float) -> tuple[float, float]:
        return max(0.0, sw - 2 * margin), max(0.0, sh - 2 * margin)

    # Validate parts fit in some orientation within usable area
    for p in parts:
        fits_somewhere = False
        for sw, sh in configured_sizes:
            if sw <= 0 or sh <= 0:
                continue
            usable_width, usable_height = _usable_dims(sw, sh)
            fits_unrotated = p.width <= usable_width and p.height <= usable_height
            fits_rotated = (
                p.can_rotate and p.height <= usable_width and p.width <= usable_height
            )
            if fits_unrotated or fits_rotated:
                fits_somewhere = True
                break
        if not fits_somewhere:
            sample_w, sample_h = configured_sizes[0]
            usable_width, usable_height = _usable_dims(sample_w, sample_h)
            raise ValueError(
                f"Part {p.id} ({p.width} x {p.height}) does not fit "
                f"in usable sheet area {usable_width} x {usable_height}."
            )

    sizes = sheet_sizes or []

    def _sheet_dimensions(index: int) -> tuple[float, float]:
        return resolve_sheet_dimensions(sizes, index, sheet_width, sheet_height)

    sheet_index = 0
    current_sheet_width, current_sheet_height = _sheet_dimensions(sheet_index)
    if current_sheet_width <= 0 or current_sheet_height <= 0:
        return []
    usable_width, usable_height = _usable_dims(
        current_sheet_width, current_sheet_height
    )

    remaining: list[Part] = sorted(
        parts,
        key=lambda p: (p.height, p.width),
        reverse=True,
    )

    placements: list[PlacedPart] = []
    current_y = margin

    def orientation_options(part: Part):
        yield part.width, part.height, 0
        if part.can_rotate and part.width != part.height:
            yield part.height, part.width, 90

    while remaining:
        current_x = margin
        row_height = 0.0
        placed_this_row = False

        while remaining:
            # Pick the first part in sorted order that fits the current row.
            candidate_idx = None
            candidate_orient = None

            for idx, part in enumerate(remaining):
                for w, h, rot in orientation_options(part):
                    if w > usable_width or h > usable_height:
                        continue
                    if current_x + w + spacing > current_sheet_width - margin + 1e-6:
                        continue
                    if (
                        current_y + max(row_height, h) + spacing
                        > current_sheet_height - margin + 1e-6
                    ):
                        continue
                    candidate_idx = idx
                    candidate_orient = (w, h, rot)
                    break
                if candidate_idx is not None:
                    break

            if candidate_idx is None:
                break

            part = remaining.pop(candidate_idx)
            w, h, rot = candidate_orient  # type: ignore

            placements.append(
                PlacedPart(
                    id=part.id,
                    sheet_index=sheet_index,
                    x=current_x,
                    y=current_y,
                    width=w,
                    height=h,
                    rotation_deg=rot,
                )
            )

            placed_this_row = True
            current_x += w + kerf
            row_height = max(row_height, h)
            current_x += spacing

        if not placed_this_row:
            # No part fit in this row; start a new sheet.
            sheet_index += 1
            current_sheet_width, current_sheet_height = _sheet_dimensions(sheet_index)
            usable_width, usable_height = _usable_dims(
                current_sheet_width, current_sheet_height
            )
            current_y = margin
            continue

        # Move to next row
        current_y += row_height + spacing
        if current_y > current_sheet_height - margin + 1e-6 and remaining:
            # Start a new sheet
            sheet_index += 1
            current_sheet_width, current_sheet_height = _sheet_dimensions(sheet_index)
            usable_width, usable_height = _usable_dims(
                current_sheet_width, current_sheet_height
            )
            current_y = margin

    return placements


def _nest_cut_friendly(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    config: NestingConfig | None = None,
    sheet_sizes: list[tuple[float, float]] | None = None,
) -> list[PlacedPart]:
    """
    Lane-based heuristic aimed at woodshop-style rips/crosscuts.

    - Sort parts by width descending (treat X as rip direction).
    - Build vertical lanes; each lane has thickness = max width of its parts.
    - Within a lane, stack parts along Y until height is exceeded, then start a new lane.
    - If a lane won't fit on the current sheet, start a new sheet.
    """
    cfg = config or NestingConfig()
    kerf = cfg.kerf_width_mm
    spacing = max(cfg.spacing_mm, 0.0)
    margin = spacing

    sizes = sheet_sizes or []

    def _sheet_dimensions(index: int) -> tuple[float, float]:
        return resolve_sheet_dimensions(sizes, index, sheet_width, sheet_height)

    configured_sizes = sizes or [(sheet_width, sheet_height)]
    for part in parts:
        fits_somewhere = False
        for sw, sh in configured_sizes:
            if sw <= 0 or sh <= 0:
                continue
            can_fit = (part.width <= sw and part.height <= sh) or (
                part.can_rotate and part.height <= sw and part.width <= sh
            )
            if can_fit:
                fits_somewhere = True
                break
        if not fits_somewhere:
            sw, sh = configured_sizes[0]
            raise ValueError(
                f"Part {part.id} ({part.width} x {part.height}) does not fit "
                f"on sheet {sw} x {sh} in any allowed orientation."
            )

    first_width, first_height = _sheet_dimensions(0)
    if first_width <= 0 or first_height <= 0:
        return []

    remaining = sorted(parts, key=lambda p: (p.width, p.height), reverse=True)
    placements: list[PlacedPart] = []

    sheet_index = 0
    current_sheet_width, current_sheet_height = first_width, first_height
    lane_origin_x = margin

    while remaining:
        # Start a new lane with the widest available part
        seed = remaining.pop(0)
        lane_width = seed.width
        lane_parts = [seed]

        # Collect parts that can fit within this lane width (allow rotation if permitted)
        fitted = []
        for p in list(remaining):
            fits = p.width <= lane_width or (p.can_rotate and p.height <= lane_width)
            if fits:
                fitted.append(p)
        for p in fitted:
            remaining.remove(p)
            lane_parts.append(p)

        # Sort lane parts by height descending for stacking
        lane_parts.sort(
            key=lambda p: max(p.height, p.width if p.can_rotate else p.height),
            reverse=True,
        )

        current_y = margin
        lane_used_height = 0.0
        for p in lane_parts:
            w, h = p.width, p.height
            rot = 0
            if p.can_rotate and h > lane_width and w <= lane_width:
                w, h = h, w
                rot = 90
            if w > lane_width:
                # rotate if possible to fit lane
                if p.can_rotate and h <= lane_width:
                    w, h = h, w
                    rot = 90
                else:
                    # Doesn't fit this lane; push back for later
                    remaining.insert(0, p)
                    continue

            if current_y + h + margin > current_sheet_height:
                # Lane full; put part back and break to start a new lane
                remaining.insert(0, p)
                break

            placements.append(
                PlacedPart(
                    id=p.id,
                    sheet_index=sheet_index,
                    x=lane_origin_x,
                    y=current_y,
                    width=w,
                    height=h,
                    rotation_deg=rot,
                )
            )
            current_y += h + kerf + spacing
            lane_used_height = max(lane_used_height, current_y)

        lane_thickness = lane_width + spacing
        lane_origin_x += lane_thickness + kerf

        if lane_origin_x > current_sheet_width - margin:
            # Move to next sheet
            sheet_index += 1
            current_sheet_width, current_sheet_height = _sheet_dimensions(sheet_index)
            lane_origin_x = margin
            # Reset order by width for remaining parts on the new sheet
            remaining.sort(key=lambda p: (p.width, p.height), reverse=True)

    return placements


def nest_parts(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    config: NestingConfig | None = None,
    sheet_sizes: list[tuple[float, float]] | None = None,
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
        return _nest_cut_friendly(
            parts, sheet_width, sheet_height, cfg, sheet_sizes=sizes
        )
    return _nest_rectangular_default(
        parts, sheet_width, sheet_height, cfg, sheet_sizes=sizes if sizes else None
    )


def estimate_cut_counts(
    placements: list[PlacedPart],
    sheet_width: float | None = None,
    sheet_height: float | None = None,
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
        }
    fallback_width, fallback_height = sheet_sizes[0]
    used_sheet_indices = {pp.sheet_index for pp in placements}
    total_sheet_area = 0.0
    for sheet_index in used_sheet_indices:
        sw, sh = resolve_sheet_dimensions(
            sheet_sizes, sheet_index, fallback_width, fallback_height
        )
        total_sheet_area += sw * sh
    placed_area = sum(pp.width * pp.height for pp in placements)
    util_percent = (
        (placed_area / total_sheet_area) * 100.0 if total_sheet_area > 0 else 0.0
    )
    return {
        "utilization_percent": util_percent,
        "sheets_used": len(used_sheet_indices),
        "placed_area": placed_area,
        "sheet_area": total_sheet_area,
    }


def analyze_sheet_exhaustion(
    placements: list[PlacedPart],
    sheet_sizes: list[tuple[float, float]] | None = None,
) -> dict[str, int | bool]:
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
