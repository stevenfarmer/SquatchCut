"""Heuristic that prioritizes aligned cut paths."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from SquatchCut.core.nesting import Part, PlacedPart


def nest_cut_optimized(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    kerf: float = 0.0,
    margin: float = 0.0,
    sheet_sizes: Optional[list[tuple[float, float]]] = None,
) -> list[PlacedPart]:
    """Row/column oriented heuristic intended to reduce distinct cut lines."""

    from SquatchCut.core.nesting import PlacedPart, resolve_sheet_dimensions

    if sheet_width <= 0 or sheet_height <= 0:
        return []

    spacing = max(0.0, kerf)
    margin = max(0.0, margin)
    configured_sizes = sheet_sizes or [(sheet_width, sheet_height)]

    def _usable_dims(sw: float, sh: float) -> tuple[float, float]:
        return max(0.0, sw - 2 * margin), max(0.0, sh - 2 * margin)

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
            sheet_index += 1
            current_sheet_width, current_sheet_height = _sheet_dimensions(sheet_index)
            usable_width, usable_height = _usable_dims(
                current_sheet_width, current_sheet_height
            )
            current_y = margin
            continue

        current_y += row_height + spacing
        if current_y > current_sheet_height - margin + 1e-6 and remaining:
            sheet_index += 1
            current_sheet_width, current_sheet_height = _sheet_dimensions(sheet_index)
            usable_width, usable_height = _usable_dims(
                current_sheet_width, current_sheet_height
            )
            current_y = margin

    return placements
