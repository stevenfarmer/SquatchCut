"""@codex
Simple deterministic 2D shelf nesting for rectangular panels.
Pure logic module: no FreeCAD or GUI dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

__all__ = ["run_shelf_nesting", "nest_on_multiple_sheets", "Part", "PlacedPart"]


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


def nest_on_multiple_sheets(
    parts: List[Part],
    sheet_width: float,
    sheet_height: float,
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
            # Compute current total height for this sheet from its rows
            total_height = sum(r["height"] for r in rows)

            # 1) Try to place in existing rows on this sheet
            for row in rows:
                for w, h, rot in orientations_for_part(part):
                    # Must fit within row height and sheet width
                    if h > row["height"]:
                        continue
                    if row["used_width"] + w > sheet_width:
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

                    row["used_width"] += w
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

                new_total_height = total_height + h
                if new_total_height > sheet_height:
                    continue

                # Start a new row with fixed height = h
                new_row = {
                    "y": total_height,
                    "height": h,
                    "used_width": w,
                }
                rows.append(new_row)

                placed.append(
                    PlacedPart(
                        id=part.id,
                        sheet_index=sheet_index,
                        x=0.0,
                        y=total_height,
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
