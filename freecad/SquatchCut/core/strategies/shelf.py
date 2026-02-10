"""Shelf-based and related nesting helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from SquatchCut.core import logger

if TYPE_CHECKING:
    from SquatchCut.core.nesting import NestingConfig, Part, PlacedPart


def pack_parts(
    parts: list[Part],
    sheet_width: float,
    sheet_height: float,
    config: Optional[NestingConfig] = None,
    sheet_sizes: Optional[list[tuple[float, float]]] = None,
) -> list[PlacedPart]:
    """Shelf-based rectangle packing across multiple sheets."""

    from SquatchCut.core.nesting import (
        NestingConfig,
        PlacedPart,
        get_effective_spacing,
        resolve_sheet_dimensions,
    )

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

    remaining = sorted(parts, key=lambda p: max(p.width, p.height), reverse=True)
    placed: list[PlacedPart] = []

    sheets: list[list[dict]] = [[]]

    def _orientations_for_part(part):
        yield part.width, part.height, 0
        if part.can_rotate and part.width != part.height:
            yield part.height, part.width, 90

    for part in remaining:
        placed_on_sheet = False
        for sheet_index, rows in enumerate(sheets):
            total_height = 0.0
            for idx, r in enumerate(rows):
                total_height += r["height"]
                if idx < len(rows) - 1:
                    total_height += spacing
            current_sheet_width, current_sheet_height = resolve_sheet_dimensions(
                sheet_sizes or [], sheet_index, sheet_width, sheet_height
            )
            for row in rows:
                for w, h, rot in _orientations_for_part(part):
                    if h > row["height"]:
                        continue
                    if row["used_width"] + w + spacing > current_sheet_width + 1e-6:
                        continue
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
                    break
                if placed_on_sheet:
                    break
            if placed_on_sheet:
                break
            for w, h, rot in _orientations_for_part(part):
                if w > current_sheet_width:
                    continue
                row_spacing = spacing if rows else 0.0
                row_y = total_height + row_spacing
                new_total_height = row_y + h
                if new_total_height > current_sheet_height:
                    continue
                new_row = {"y": row_y, "height": h, "used_width": w + spacing}
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
                break
            if placed_on_sheet:
                break
        if placed_on_sheet:
            continue
        new_sheet_index = len(sheets)
        if sheet_sizes and new_sheet_index >= len(sheet_sizes):
            try:
                available_sheets = len(sheet_sizes)
                logger.warning(
                    f">>> [SquatchCut] Sheet exhaustion: trying to use sheet {new_sheet_index + 1} "
                    f"but only {available_sheets} sheet(s) available. Using last available sheet type."
                )
            except Exception:
                import warnings

                warnings.warn(
                    f"Sheet exhaustion: trying to use sheet {new_sheet_index + 1} "
                    f"but only {len(sheet_sizes)} sheet(s) available.",
                    stacklevel=2,
                )
        new_rows: list[dict] = []
        sheets.append(new_rows)
        placed_here = False
        new_sheet_width, new_sheet_height = resolve_sheet_dimensions(
            sheet_sizes or [], new_sheet_index, sheet_width, sheet_height
        )
        for w, h, rot in _orientations_for_part(part):
            if w <= new_sheet_width and h <= new_sheet_height:
                new_row = {"y": 0.0, "height": h, "used_width": w}
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
    config: Optional[NestingConfig] = None,
    sheet_definitions: Optional[list[dict]] = None,
) -> list[PlacedPart]:
    """Run shelf-based nesting honoring explicit sheet definitions."""

    from SquatchCut.core.nesting import expand_sheet_sizes

    sheet_sizes = expand_sheet_sizes(sheet_definitions or [])
    if not sheet_sizes:
        sheet_sizes = [(sheet_width, sheet_height)]
    return pack_parts(
        parts,
        sheet_width,
        sheet_height,
        config=config,
        sheet_sizes=sheet_sizes,
    )
