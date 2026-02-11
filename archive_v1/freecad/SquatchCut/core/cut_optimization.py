"""Guillotine-style nesting and cut-path helpers for SquatchCut."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional

from SquatchCut.core import nesting as nesting_mod
from SquatchCut.core.nesting import get_effective_spacing


@dataclass
class Sheet:
    width: float
    height: float


def _get_sheet_dims(sheet) -> tuple[float, float]:
    """Support dict-like or Sheet for dimensions."""
    if isinstance(sheet, dict):
        return float(sheet.get("width", 0.0)), float(sheet.get("height", 0.0))
    if isinstance(sheet, Sheet):
        return float(sheet.width), float(sheet.height)
    return float(getattr(sheet, "width", 0.0)), float(getattr(sheet, "height", 0.0))


def _orientations_for_part(part, allowed_rotations: tuple[int, ...]) -> Iterable[tuple[float, float, int]]:
    """Yield (width, height, rotation_deg) respecting part.can_rotate and allowed_rotations."""
    yield part.width, part.height, 0
    if getattr(part, "can_rotate", False) and 90 in allowed_rotations and part.width != part.height:
        yield part.height, part.width, 90


def guillotine_nest_parts(
    parts, sheet, config, sheet_sizes: Optional[list[tuple[float, float]]] = None
) -> list:
    """
    Guillotine-style nesting: place parts in free rectangles, splitting space after each placement.

    - Parts sorted largest-first.
    - Honors allowed rotations and kerf spacing.
    - Supports multi-sheet input by advancing through sheet_sizes when provided.
    - Returns PlacedPart objects from SquatchCut.core.nesting.
    """

    sheet_w, sheet_h = _get_sheet_dims(sheet)
    if sheet_w <= 0 or sheet_h <= 0:
        return []

    sizes = sheet_sizes or []

    def _sheet_dimensions(index: int) -> tuple[float, float]:
        return nesting_mod.resolve_sheet_dimensions(sizes, index, sheet_w, sheet_h)

    configured_sizes = sizes or [(sheet_w, sheet_h)]
    allowed_rots = tuple(getattr(config, "allowed_rotations_deg", (0, 90)) or (0, 90))

    for part in parts:
        fits_somewhere = False
        for sw, sh in configured_sizes:
            if sw <= 0 or sh <= 0:
                continue
            fits_plain = part.width <= sw and part.height <= sh
            fits_rotated = (
                getattr(part, "can_rotate", False)
                and 90 in allowed_rots
                and part.height <= sw
                and part.width <= sh
            )
            if fits_plain or fits_rotated:
                fits_somewhere = True
                break
        if not fits_somewhere:
            sw, sh = configured_sizes[0]
            raise ValueError(
                f"Part {part.id} ({part.width} x {part.height}) does not fit "
                f"on sheet {sw} x {sh} in any allowed orientation."
            )

    current_sheet_width, current_sheet_height = _sheet_dimensions(0)
    if current_sheet_width <= 0 or current_sheet_height <= 0:
        return []

    free_rects = [{"x": 0.0, "y": 0.0, "w": current_sheet_width, "h": current_sheet_height}]
    placements: list[nesting_mod.PlacedPart] = []

    remaining_parts = sorted(parts, key=lambda p: p.width * p.height, reverse=True)

    spacing = get_effective_spacing(config)
    kerf = spacing  # treat spacing as kerf/spacing budget

    sheet_index = 0
    while remaining_parts:
        part = remaining_parts.pop(0)
        placed = False
        for fr_idx, fr in enumerate(list(free_rects)):
            for w, h, rot in _orientations_for_part(part, allowed_rots):
                if w <= 0 or h <= 0:
                    continue

                # Check if part fits in free rect.
                # Note: We do NOT enforce w + kerf <= fr["w"] here, because a part
                # fitting exactly on the edge doesn't need trailing kerf if no other
                # part follows it in that direction. The split logic handles spacing.
                if w > fr["w"] + 1e-6 or h > fr["h"] + 1e-6:
                    continue

                x = fr["x"]
                y = fr["y"]
                # Sanity check against sheet bounds
                if x + w > current_sheet_width + 1e-6 or y + h > current_sheet_height + 1e-6:
                    continue

                placements.append(
                    nesting_mod.PlacedPart(
                        id=part.id,
                        sheet_index=sheet_index,
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        rotation_deg=rot,
                    )
                )

                # Split rectangle: Guillotine split (Vertical Split First strategy).
                # Right rect: covers full height to the right of the vertical cut line.
                right_rect = {
                    "x": x + w + kerf,
                    "y": y,
                    "w": fr["w"] - w - kerf,
                    "h": fr["h"],
                }
                # Bottom rect: covers width of the part (plus left region) below the horizontal cut line.
                # Constrained to width=w to avoid overlap with right_rect.
                bottom_rect = {
                    "x": x,
                    "y": y + h + kerf,
                    "w": w,
                    "h": fr["h"] - h - kerf,
                }

                free_rects.pop(fr_idx)
                for r in (right_rect, bottom_rect):
                    if r["w"] > 0 and r["h"] > 0:
                        free_rects.append(r)

                placed = True
                break
            if placed:
                break

        if not placed:
            sheet_index += 1
            current_sheet_width, current_sheet_height = _sheet_dimensions(sheet_index)
            if current_sheet_width <= 0 or current_sheet_height <= 0:
                raise ValueError(
                    f"Part {part.id} ({part.width} x {part.height}) does not fit "
                    f"on sheet {current_sheet_width} x {current_sheet_height} with guillotine nesting."
                )
            free_rects = [{"x": 0.0, "y": 0.0, "w": current_sheet_width, "h": current_sheet_height}]
            remaining_parts.insert(0, part)
            continue

    return placements


def estimate_cut_path_complexity(placements, kerf_width_mm: float = 0.0) -> float:
    """
    Rough heuristic for cut-path complexity based on distinct aligned edges.
    Returns a float for future refinement; higher means more cuts.
    """
    if not placements:
        return 0.0

    xs = set()
    ys = set()
    for p in placements:
        xs.add(round(p.x, 3))
        xs.add(round(p.x + p.width, 3))
        ys.add(round(p.y, 3))
        ys.add(round(p.y + p.height, 3))

    return float(len(xs) + len(ys)) + float(kerf_width_mm or 0.0) * 0.01
