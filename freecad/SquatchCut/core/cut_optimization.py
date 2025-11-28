"""Guillotine-style nesting and cut-path helpers for SquatchCut."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

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


def _orientations_for_part(part, allowed_rotations: Tuple[int, ...]) -> Iterable[tuple[float, float, int]]:
    """Yield (width, height, rotation_deg) respecting part.can_rotate and allowed_rotations."""
    yield part.width, part.height, 0
    if getattr(part, "can_rotate", False) and 90 in allowed_rotations and part.width != part.height:
        yield part.height, part.width, 90


def guillotine_nest_parts(parts, sheet, config) -> List:
    """
    Guillotine-style nesting: place parts in free rectangles, splitting space after each placement.

    - Parts sorted largest-first.
    - Honors allowed rotations and kerf spacing.
    - Returns PlacedPart objects from SquatchCut.core.nesting.
    """

    sheet_w, sheet_h = _get_sheet_dims(sheet)
    if sheet_w <= 0 or sheet_h <= 0:
        return []

    free_rects = [{"x": 0.0, "y": 0.0, "w": sheet_w, "h": sheet_h}]
    placements: list[nesting_mod.PlacedPart] = []

    sorted_parts = sorted(parts, key=lambda p: p.width * p.height, reverse=True)

    spacing = get_effective_spacing(config)
    kerf = spacing  # treat spacing as kerf/spacing budget
    allowed_rots = tuple(getattr(config, "allowed_rotations_deg", (0, 90)) or (0, 90))

    for part in sorted_parts:
        placed = False
        for fr_idx, fr in enumerate(list(free_rects)):
            for w, h, rot in _orientations_for_part(part, allowed_rots):
                if w <= 0 or h <= 0:
                    continue
                req_w = w + kerf
                req_h = h + kerf
                if req_w > fr["w"] or req_h > fr["h"]:
                    continue
                x = fr["x"]
                y = fr["y"]
                if x + w > sheet_w + 1e-6 or y + h > sheet_h + 1e-6:
                    continue

                placements.append(
                    nesting_mod.PlacedPart(
                        id=part.id,
                        sheet_index=0,
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        rotation_deg=rot,
                    )
                )

                # Split rectangle: right and bottom regions with kerf spacing.
                right_rect = {
                    "x": x + w + kerf,
                    "y": y,
                    "w": fr["w"] - w - kerf,
                    "h": fr["h"],
                }
                bottom_rect = {
                    "x": x,
                    "y": y + h + kerf,
                    "w": fr["w"],
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
            raise ValueError(f"Part {part.id} does not fit on sheet with guillotine nesting.")

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
