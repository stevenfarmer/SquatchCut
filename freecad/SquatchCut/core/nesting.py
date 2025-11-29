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
from typing import Dict, List, Tuple


__all__ = [
    "run_shelf_nesting",
    "nest_on_multiple_sheets",
    "nest_cut_optimized",
    "nest_parts",
    "NestingConfig",
    "get_effective_spacing",
    "estimate_cut_counts",
    "compute_utilization",
    "Part",
    "PlacedPart",
]


@dataclass
class Part:
    id: str
    width: float   # mm
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
    allowed_rotations_deg: Tuple[int, ...] = (0, 90)
    spacing_mm: float = 0.0
    measurement_system: str = "metric"
    export_include_labels: bool = True
    export_include_dimensions: bool = False
    nesting_mode: str = "pack"  # "pack" (default) or "cut_friendly"


def get_effective_spacing(config) -> float:
    """
    Return effective spacing (base spacing + kerf width) to keep parts separated.
    """
    base_spacing = float(getattr(config, "spacing_mm", 0.0) or 0.0)
    kerf = float(getattr(config, "kerf_width_mm", 0.0) or 0.0)
    return max(0.0, base_spacing + kerf)


def _nest_rectangular_default(
    parts: List[Part],
    sheet_width: float,
    sheet_height: float,
    config: NestingConfig | None = None,
) -> List[PlacedPart]:
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

    # Early validation: each part must fit on an empty sheet in some allowed orientation.
    for p in parts:
        can_fit_unrotated = p.width <= sheet_width and p.height <= sheet_height
        can_fit_rotated = p.can_rotate and p.height <= sheet_width and p.width <= sheet_height
        if not (can_fit_unrotated or can_fit_rotated):
            raise ValueError(
                f"Part {p.id} ({p.width} x {p.height}) does not fit "
                f"on sheet {sheet_width} x {sheet_height} in any allowed orientation."
            )

    # Sort by max dimension so bigger parts get placed first.
    remaining = sorted(
        parts,
        key=lambda p: max(p.width, p.height),
        reverse=True,
    )

    placed: List[PlacedPart] = []

    # Each sheet is a list of rows.
    # Each row is a dict: {"y": float, "height": float, "used_width": float}
    sheets: List[List[dict]] = []
    sheets.append([])  # first sheet with no rows yet

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

            # 1) Try to place in existing rows on this sheet
            for row in rows:
                for w, h, rot in orientations_for_part(part):
                    # Must fit within row height and sheet width
                    if h > row["height"]:
                        continue
                    if row["used_width"] + w + spacing > sheet_width + 1e-6:
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
                if w > sheet_width:
                    continue

                new_total_height = total_height + (spacing if rows else 0.0) + h
                if new_total_height > sheet_height:
                    continue

                # Start a new row with fixed height = h
                new_row = {
                    "y": total_height + (spacing if rows else 0.0),
                    "height": h,
                    "used_width": w + spacing,
                }
                rows.append(new_row)

                placed.append(
                    PlacedPart(
                        id=part.id,
                        sheet_index=sheet_index,
                        x=0.0,
                        y=total_height + (spacing if rows else 0.0),
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
        new_rows: List[dict] = []
        sheets.append(new_rows)

        placed_here = False
        for w, h, rot in orientations_for_part(part):
            if w <= sheet_width and h <= sheet_height:
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
            raise ValueError(
                f"Part {part.id} ({part.width} x {part.height}) unexpectedly "
                f"cannot be placed on a new sheet {sheet_width} x {sheet_height}."
            )

    return placed


def nest_on_multiple_sheets(
    parts: List[Part],
    sheet_width: float,
    sheet_height: float,
    config: NestingConfig | None = None,
) -> List[PlacedPart]:
    """
    Backward-compatible entry that runs the default shelf-based nesting.
    """
    return _nest_rectangular_default(parts, sheet_width, sheet_height, config=config)


def nest_cut_optimized(
    parts: List[Part],
    sheet_width: float,
    sheet_height: float,
    kerf: float = 0.0,
    margin: float = 0.0,
) -> List[PlacedPart]:
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
    usable_width = max(0.0, sheet_width - 2 * margin)
    usable_height = max(0.0, sheet_height - 2 * margin)

    # Validate parts fit in some orientation within usable area
    for p in parts:
        fits_unrotated = p.width <= usable_width and p.height <= usable_height
        fits_rotated = (
            p.can_rotate and p.height <= usable_width and p.width <= usable_height
        )
        if not (fits_unrotated or fits_rotated):
            raise ValueError(
                f"Part {p.id} ({p.width} x {p.height}) does not fit "
                f"in usable sheet area {usable_width} x {usable_height}."
            )

    remaining: List[Part] = sorted(
        parts,
        key=lambda p: (p.height, p.width),
        reverse=True,
    )

    placements: List[PlacedPart] = []
    sheet_index = 0
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
                    if current_x + w + spacing > sheet_width - margin + 1e-6:
                        continue
                    if current_y + max(row_height, h) + spacing > sheet_height - margin + 1e-6:
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
            current_y = margin
            continue

        # Move to next row
        current_y += row_height + spacing
        if current_y > sheet_height - margin + 1e-6 and remaining:
            # Start a new sheet
            sheet_index += 1
            current_y = margin

    return placements


def _nest_cut_friendly(
    parts: List[Part],
    sheet_width: float,
    sheet_height: float,
    config: NestingConfig | None = None,
) -> List[PlacedPart]:
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

    if sheet_width <= 0 or sheet_height <= 0:
        return []

    remaining = sorted(parts, key=lambda p: (p.width, p.height), reverse=True)
    placements: List[PlacedPart] = []

    sheet_index = 0
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
        lane_parts.sort(key=lambda p: max(p.height, p.width if p.can_rotate else p.height), reverse=True)

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

            if current_y + h + margin > sheet_height:
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

        if lane_origin_x > sheet_width - margin:
            # Move to next sheet
            sheet_index += 1
            lane_origin_x = margin
            # Reset order by width for remaining parts on the new sheet
            remaining.sort(key=lambda p: (p.width, p.height), reverse=True)

    return placements


def nest_parts(
    parts: List[Part],
    sheet_width: float,
    sheet_height: float,
    config: NestingConfig | None = None,
) -> List[PlacedPart]:
    """
    Strategy selector for nesting.
    - When optimize_for_cut_path is True, use guillotine-style nesting.
    - Otherwise, fall back to the default shelf-based nesting.
    """
    cfg = config or NestingConfig()
    if cfg.optimize_for_cut_path:
        from SquatchCut.core import cut_optimization

        return cut_optimization.guillotine_nest_parts(
            parts,
            {"width": sheet_width, "height": sheet_height},
            cfg,
        )
    if getattr(cfg, "nesting_mode", "pack") == "cut_friendly":
        return _nest_cut_friendly(parts, sheet_width, sheet_height, cfg)
    return _nest_rectangular_default(parts, sheet_width, sheet_height, cfg)


def estimate_cut_counts(
    placements: List[PlacedPart],
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


def compute_utilization(
    placements: List[PlacedPart],
    sheet_width: float,
    sheet_height: float,
) -> dict:
    """
    Compute basic material utilization metrics for a set of placements.
    Returns: {"utilization_percent": float, "sheets_used": int, "placed_area": float, "sheet_area": float}
    """
    if not placements or sheet_width <= 0 or sheet_height <= 0:
        return {"utilization_percent": 0.0, "sheets_used": 0, "placed_area": 0.0, "sheet_area": 0.0}

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


def run_shelf_nesting(
    sheet_width: float,
    sheet_height: float,
    panels: List[Dict],
    margin: float = 5.0,
) -> List[Dict]:
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

    placements: List[Dict] = []
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
