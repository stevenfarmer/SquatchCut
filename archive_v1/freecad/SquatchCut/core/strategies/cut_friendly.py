"""Lane-based nesting optimized for saw-friendly cuts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from SquatchCut.core.nesting import NestingConfig, Part, PlacedPart


def nest_cut_friendly(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    config: Optional[NestingConfig] = None,
    sheet_sizes: Optional[list[tuple[float, float]]] = None,
) -> list[PlacedPart]:
    """Lane-based heuristic aimed at woodshop-style rips/crosscuts."""

    import importlib

    nesting_module = importlib.import_module("SquatchCut.core.nesting")
    NestingConfigCls = nesting_module.NestingConfig
    PlacedPartCls = nesting_module.PlacedPart
    resolve_sheet_dimensions = nesting_module.resolve_sheet_dimensions

    cfg = config or NestingConfigCls()
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
        seed = remaining.pop(0)
        lane_width = seed.width
        lane_parts = [seed]

        fitted = []
        for p in list(remaining):
            fits = p.width <= lane_width or (p.can_rotate and p.height <= lane_width)
            if fits:
                fitted.append(p)
        for p in fitted:
            remaining.remove(p)
            lane_parts.append(p)

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
                if p.can_rotate and h <= lane_width:
                    w, h = h, w
                    rot = 90
                else:
                    remaining.insert(0, p)
                    continue

            if current_y + h + margin > current_sheet_height:
                remaining.insert(0, p)
                break

            placements.append(
                PlacedPartCls(
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
            sheet_index += 1
            current_sheet_width, current_sheet_height = _sheet_dimensions(sheet_index)
            lane_origin_x = margin
            remaining.sort(key=lambda p: (p.width, p.height), reverse=True)

    return placements
