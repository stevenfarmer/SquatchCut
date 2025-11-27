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
    kerf_mm: float = 0.0,
    gap_mm: float = 0.0,
) -> List[PlacedPart]:
    """
    Shelf-based rectangle packing across multiple sheets with optional 90° rotation.

    - Parts are sorted by their max(height, width) (tallest/longest first).
    - Each sheet is divided into horizontal rows (shelves).
    - Parts with can_rotate=True may be rotated 90° if that helps them fit.
    - New sheets are created as needed.
    - Returns a flat list of PlacedPart with sheet_index + x/y + rotation_deg.

    Raises ValueError if any single part is too large to fit on a sheet in any
    allowed orientation.
    """

    # Fail early if something cannot physically fit in any orientation
    for p in parts:
        eff_w0 = p.width + 2 * gap_mm
        eff_h0 = p.height + 2 * gap_mm
        eff_w90 = p.height + 2 * gap_mm
        eff_h90 = p.width + 2 * gap_mm
        can_fit_unrotated = eff_w0 <= sheet_width and eff_h0 <= sheet_height
        can_fit_rotated = p.can_rotate and eff_w90 <= sheet_width and eff_h90 <= sheet_height
        if not (can_fit_unrotated or can_fit_rotated):
            raise ValueError(
                f"Part {p.id} ({p.width} x {p.height}) does not fit "
                f"on sheet {sheet_width} x {sheet_height} in any allowed orientation."
            )

    # Sort by max dimension so big parts get placed first
    remaining = sorted(
        parts,
        key=lambda p: max(p.width, p.height),
        reverse=True,
    )

    placed: List[PlacedPart] = []

    # Each sheet: list of rows (dicts with y, row_height, used_width)
    sheets: List[List[dict]] = []
    sheets.append([])  # start with first empty sheet

    def orientations_for_part(p: Part):
        """Yield (eff_w, eff_h, rotation_deg) options, preferring 0° then 90°."""
        yield (p.width + 2 * gap_mm, p.height + 2 * gap_mm, 0, p.width, p.height)
        if p.can_rotate and p.width != p.height:
            yield (p.height + 2 * gap_mm, p.width + 2 * gap_mm, 90, p.width, p.height)

    for part in remaining:
        placed_on_sheet = False

        # Try to place this part on existing sheets
        for sheet_index, rows in enumerate(sheets):
            # current max height of this sheet
            current_max_height = (
                max((r["y"] + r["row_height"] for r in rows), default=0.0)
                if rows
                else 0.0
            )

            # 1) Try to fit in existing rows on this sheet
            for row in rows:
                for w_eff, h_eff, rot, true_w, true_h in orientations_for_part(part):
                    spacing = kerf_mm if row["used_width"] > 0 else 0.0
                    if row["used_width"] + spacing + w_eff > sheet_width:
                        continue

                    # height fit? (row may grow taller)
                    new_row_height = max(row["row_height"], h_eff)
                    if row["y"] + new_row_height > sheet_height:
                        continue

                    # Fits: place it here
                    x = row["used_width"] + spacing
                    y = row["y"]

                    placed.append(
                        PlacedPart(
                            id=part.id,
                            sheet_index=sheet_index,
                            x=x + gap_mm,
                            y=y + gap_mm,
                            width=true_w,
                            height=true_h,
                            rotation_deg=rot,
                        )
                    )

                    row["used_width"] = x + w_eff
                    row["row_height"] = new_row_height
                    placed_on_sheet = True
                    break  # out of orientations

                if placed_on_sheet:
                    break  # out of rows

            if placed_on_sheet:
                break  # out of sheets

            # 2) Could not fit in any existing row on this sheet; try a new row
            for w_eff, h_eff, rot, true_w, true_h in orientations_for_part(part):
                if w_eff > sheet_width:
                    continue

                y_new = current_max_height + (kerf_mm if rows else 0.0)
                if y_new + h_eff > sheet_height:
                    continue

                new_row = {
                    "y": y_new,
                    "row_height": h_eff,
                    "used_width": w_eff,
                }
                rows.append(new_row)

                placed.append(
                    PlacedPart(
                        id=part.id,
                        sheet_index=sheet_index,
                        x=0.0 + gap_mm,
                        y=y_new + gap_mm,
                        width=true_w,
                        height=true_h,
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

        # Try orientations for the first row on the new sheet
        placed_here = False
        for w_eff, h_eff, rot, true_w, true_h in orientations_for_part(part):
            if w_eff <= sheet_width and h_eff <= sheet_height:
                new_row = {
                    "y": 0.0,
                    "row_height": h_eff,
                    "used_width": w_eff,
                }
                new_rows.append(new_row)

                placed.append(
                    PlacedPart(
                        id=part.id,
                        sheet_index=new_sheet_index,
                        x=0.0 + gap_mm,
                        y=0.0 + gap_mm,
                        width=true_w,
                        height=true_h,
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
