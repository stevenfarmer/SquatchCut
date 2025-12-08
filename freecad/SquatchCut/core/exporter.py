"""Export helpers for SquatchCut nesting layouts (DXF, SVG, cut list CSV)."""

from __future__ import annotations

import csv
import os
import tempfile
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from SquatchCut.freecad_integration import App, Part
from SquatchCut.core import logger, units as unit_utils
from SquatchCut.core.cutlist import generate_cutlist
from SquatchCut.core.nesting import derive_sheet_sizes_for_layout, resolve_sheet_dimensions
from SquatchCut.core.text_helpers import create_export_shape_text

_EXPORT_SUBDIR = "SquatchCutExports"


def _default_export_directory() -> Path:
    candidates = []
    try:
        home = Path.home()
        if home.exists():
            candidates.append(home / _EXPORT_SUBDIR)
    except Exception:
        pass
    candidates.append(Path(tempfile.gettempdir()) / _EXPORT_SUBDIR)
    for directory in candidates:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return directory
        except Exception:
            continue
    fallback = Path(tempfile.gettempdir())
    try:
        fallback.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return fallback


def _base_name_for_document(doc, suffix: str) -> tuple[Path, str]:
    doc_file = ""
    if doc is not None:
        doc_file = getattr(doc, "FileName", "") or ""
    if doc_file:
        path = Path(doc_file)
        directory = path.parent
        name = f"{path.stem}{suffix}"
        return directory, name
    directory = _default_export_directory()
    name = f"SquatchCut{suffix}"
    return directory, name


def _resolve_export_path(
    file_path: str | os.PathLike | None,
    doc,
    extension: str,
    ensure_dir: bool = True,
) -> Path:
    extension = extension if extension.startswith(".") else f".{extension}"
    if file_path:
        candidate = Path(file_path).expanduser()
    else:
        base_dir, base_name = _base_name_for_document(doc, "_nesting")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidate = base_dir / f"{base_name}_{timestamp}{extension}"
    if not candidate.suffix:
        candidate = candidate.with_suffix(extension)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if ensure_dir:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.warning(f"[SquatchCut] Unable to prepare export directory '{candidate.parent}': {exc}")
            fallback = _default_export_directory()
            candidate = fallback / candidate.name
            try:
                candidate.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
    return candidate


def suggest_export_path(doc, extension: str) -> str:
    """Suggest a default export path without enforcing directory creation."""
    path = _resolve_export_path(None, doc, extension, ensure_dir=False)
    return str(path)


def export_cutlist_to_csv(placements: Sequence, file_path: str) -> None:
    """Write a cut list CSV from placements (all dimensions in mm)."""
    with open(file_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["sheet_index", "part_id", "width_mm", "height_mm", "rotation_deg", "x_mm", "y_mm"]
        )
        for p in placements:
            writer.writerow(
                [
                    getattr(p, "sheet_index", 0),
                    getattr(p, "id", getattr(p, "label", "")),
                    getattr(p, "width", 0.0),
                    getattr(p, "height", 0.0),
                    getattr(p, "rotation_deg", 0),
                    getattr(p, "x", 0.0),
                    getattr(p, "y", 0.0),
                ]
            )


def _build_rectangles(
    doc,
    placements: Iterable,
    sheet_w: float,
    sheet_h: float,
    include_labels: bool = True,
    include_dimensions: bool = False,
):
    """Create temporary rectangles in the doc for export; returns list of objects."""
    if Part is None:
        return []

    objs = []
    sheet_spacing = sheet_w * 0.25 if sheet_w else 0.0

    def _label_size(width: float, height: float) -> float:
        try:
            base = min(max(width, 1.0), max(height, 1.0)) * 0.18
        except Exception:
            base = 10.0
        return max(base, 4.0)

    for p in placements:
        try:
            w = float(getattr(p, "width", 0.0))
            h = float(getattr(p, "height", 0.0))
            x = float(getattr(p, "x", 0.0))
            y = float(getattr(p, "y", 0.0))
            rotation = float(getattr(p, "rotation_deg", 0.0))
            sheet_index = int(getattr(p, "sheet_index", 0))
        except Exception:
            continue

        plane = Part.makePlane(w, h)
        obj = doc.addObject("Part::Feature", f"SC_Export_{getattr(p, 'id', 'part')}")
        obj.Shape = plane
        placement = obj.Placement
        placement.Base.x = x + sheet_index * (sheet_w + sheet_spacing)
        placement.Base.y = y
        placement.Base.z = 0.0
        if App:
            try:
                placement.Rotation = App.Rotation(App.Vector(0, 0, 1), rotation)
            except Exception:
                pass
        obj.Placement = placement
        objs.append(obj)

        # Optional label
        if include_labels:
            label = getattr(p, "id", None) or getattr(p, "label", None) or ""
            tx = x + w / 2.0 + sheet_index * (sheet_w + sheet_spacing)
            ty = y + h / 2.0
            txt = create_export_shape_text(doc, str(label), tx, ty, 0.0, size=_label_size(w, h))
            if txt is not None:
                objs.append(txt)

        # Optional simple dimensions (text only near edges)
        if include_dimensions:
            margin = 5.0
            tx = x + w / 2.0 + sheet_index * (sheet_w + sheet_spacing)
            ty = y - margin
            tw = create_export_shape_text(doc, f"W: {w:.1f} mm", tx, ty, 0.0, size=_label_size(w, h) * 0.6)
            if tw is not None:
                objs.append(tw)
            tx = x + w + margin + sheet_index * (sheet_w + sheet_spacing)
            ty = y + h / 2.0
            th = create_export_shape_text(doc, f"H: {h:.1f} mm", tx, ty, 0.0, size=_label_size(w, h) * 0.6)
            if th is not None:
                objs.append(th)
    return objs


def export_cutlist_map_to_csv(cutlist_by_sheet: Dict[int, list], file_path: str) -> None:
    """Write a cutlist mapping (sheet -> cuts) to CSV."""
    with open(file_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "sheet_index",
                "cut_order",
                "cut_type",
                "cut_direction",
                "from_edge",
                "distance_from_edge_mm",
                "cut_length_mm",
                "parts_affected",
                "notes",
            ]
        )
        for sheet_index in sorted(cutlist_by_sheet.keys()):
            for cut in cutlist_by_sheet[sheet_index]:
                writer.writerow(
                    [
                        cut.get("sheet_index", sheet_index),
                        cut.get("cut_order", ""),
                        cut.get("cut_type", ""),
                        cut.get("cut_direction", ""),
                        cut.get("from_edge", ""),
                        cut.get("distance_from_edge_mm", ""),
                        cut.get("cut_length_mm", ""),
                        ";".join(cut.get("parts_affected", []) or []),
                        cut.get("notes", ""),
                    ]
                )


def export_cutlist_to_text(cutlist_by_sheet: Dict[int, list], file_path: str) -> None:
    """Write a human-readable cutlist script to text."""
    with open(file_path, "w", encoding="utf-8") as fh:
        for sheet_index in sorted(cutlist_by_sheet.keys()):
            fh.write(f"Sheet {sheet_index + 1}\n")
            fh.write("-" * 22 + "\n")
            for cut in cutlist_by_sheet[sheet_index]:
                fh.write(f"{cut.get('cut_order', '')}. {cut.get('cut_type', '')} cut:\n")
                fh.write(
                    f"   Direction: {cut.get('cut_direction', '')} from {cut.get('from_edge', '')} "
                    f"at {float(cut.get('distance_from_edge_mm', 0.0)):.1f} mm\n"
                )
                fh.write(f"   Length: {float(cut.get('cut_length_mm', 0.0)):.1f} mm\n")
                parts = ";".join(cut.get("parts_affected", []) or []) or "None"
                fh.write(f"   Parts released: {parts}\n\n")
def export_layout_to_dxf(
    placements: Sequence,
    sheet_size_mm: tuple[float, float],
    doc,
    file_path: str,
    include_labels: bool = True,
    include_dimensions: bool = False,
) -> None:
    """Export placements to DXF using temporary geometry."""
    try:
        import importDXF  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"DXF export not available: {exc}") from exc

    sheet_w, sheet_h = sheet_size_mm
    target_path = _resolve_export_path(file_path, doc, ".dxf")
    objs = _build_rectangles(
        doc,
        placements,
        sheet_w,
        sheet_h,
        include_labels=include_labels,
        include_dimensions=include_dimensions,
    )
    try:
        importDXF.export(objs, str(target_path))
    except OSError as exc:
        logger.warning(f"[SquatchCut] DXF export failed for '{target_path}': {exc}")
        raise
    finally:
        for obj in objs:
            try:
                doc.removeObject(obj.Name)
            except Exception:
                pass


def export_layout_to_svg(
    placements: Sequence,
    sheet_size_mm: tuple[float, float],
    doc,
    file_path: str,
    *,
    measurement_system: str,
    sheet_mode: str,
    job_sheets: Sequence[dict] | None,
    include_labels: bool = True,
    include_dimensions: bool = False,
) -> List[Path]:
    """
    Export placements to one SVG per sheet using a deterministic 2D writer.

    Returns a list of generated file paths.
    """
    placements = list(placements or [])
    if not placements:
        raise ValueError("No placements available for SVG export.")

    sheet_w = float(sheet_size_mm[0] or 0.0)
    sheet_h = float(sheet_size_mm[1] or 0.0)
    base_target = _resolve_export_path(file_path, doc, ".svg")

    measurement_system = "imperial" if measurement_system == "imperial" else "metric"
    sheet_mode = sheet_mode or "simple"
    job_sheet_defs = list(job_sheets or [])
    sheet_sizes = derive_sheet_sizes_for_layout(sheet_mode, job_sheet_defs, sheet_w, sheet_h, placements)

    placements_by_sheet = _group_placements_by_sheet(placements)
    if not placements_by_sheet:
        raise ValueError("Placements could not be grouped by sheet for SVG export.")
    max_sheet_index = max(placements_by_sheet.keys())
    sheet_total = max_sheet_index + 1

    generated_paths: List[Path] = []
    for sheet_index in sorted(placements_by_sheet.keys()):
        width_mm, height_mm = resolve_sheet_dimensions(sheet_sizes, sheet_index, sheet_w, sheet_h)
        content = _render_sheet_svg(
            sheet_number=sheet_index + 1,
            total_sheets=sheet_total,
            sheet_dimensions=(width_mm, height_mm),
            placements=placements_by_sheet[sheet_index],
            measurement_system=measurement_system,
            include_labels=include_labels,
            include_dimensions=include_dimensions,
        )
        target_path = _sheet_specific_path(base_target, sheet_index + 1)
        try:
            target_path.write_text(content, encoding="utf-8")
        except OSError as exc:
            logger.warning(f"[SquatchCut] SVG export failed for '{target_path}': {exc}")
            raise
        generated_paths.append(target_path)

    logger.info(
        f"[SquatchCut] SVG export complete: wrote {len(generated_paths)} file(s) to {base_target.parent}"
    )
    return generated_paths


def _group_placements_by_sheet(placements: Sequence) -> Dict[int, List]:
    grouped: Dict[int, List] = defaultdict(list)
    for placement in placements or []:
        try:
            sheet_index = int(getattr(placement, "sheet_index", 0) or 0)
        except Exception:
            sheet_index = 0
        grouped[sheet_index].append(placement)
    return dict(grouped)


def _sheet_specific_path(base_path: Path, sheet_number: int) -> Path:
    stem = base_path.stem or "SquatchCut_nesting"
    new_name = f"{stem}_S{sheet_number}{base_path.suffix or '.svg'}"
    return base_path.with_name(new_name)


def _fmt_float(value: float, precision: int = 3) -> str:
    text = f"{float(value):.{precision}f}"
    text = text.rstrip("0").rstrip(".")
    return text or "0"


def _svg_y(sheet_height: float, math_y: float) -> float:
    """Convert mathematical coordinate (origin bottom-left) to SVG (origin top-left)."""
    return sheet_height - math_y


def _format_dimension_pair(width_mm: float, height_mm: float, measurement_system: str) -> str:
    label = unit_utils.unit_label_for_system(measurement_system)
    width_str = unit_utils.format_length(width_mm, measurement_system)
    height_str = unit_utils.format_length(height_mm, measurement_system)
    return f"{width_str} x {height_str} {label}"


def _part_font_size(width_mm: float, height_mm: float, sheet_size: Tuple[float, float]) -> float:
    min_sheet_dim = max(min(sheet_size), 1.0)
    base = min(width_mm, height_mm) * 0.25
    base = min(base, min_sheet_dim / 10.0)
    return max(base, min_sheet_dim / 50.0, 6.0)


def _render_sheet_svg(
    sheet_number: int,
    total_sheets: int,
    sheet_dimensions: Tuple[float, float],
    placements: List,
    measurement_system: str,
    include_labels: bool,
    include_dimensions: bool,
) -> str:
    width_mm, height_mm = sheet_dimensions
    width_mm = float(width_mm or 0.0)
    height_mm = float(height_mm or 0.0)
    min_sheet_dim = max(min(width_mm, height_mm), 1.0)
    header_font = max(min_sheet_dim / 18.0, 10.0)
    header_margin = min(max(min_sheet_dim * 0.04, 8.0), 30.0)
    header_y_math = height_mm - header_margin
    header_y = _svg_y(height_mm, header_y_math)
    header_text = f"Sheet {sheet_number} of {total_sheets} – {_format_dimension_pair(width_mm, height_mm, measurement_system)}"
    style_block = (
        "<style>"
        ".sheet-border{fill:none;stroke:#000;stroke-width:1;}"
        ".part-rect{fill:none;stroke:#111;stroke-width:0.5;}"
        ".part-label{fill:#111;font-family:sans-serif;text-anchor:middle;}"
        ".sheet-header{fill:#000;font-family:sans-serif;text-anchor:middle;}"
        "</style>"
    )

    body: List[str] = []
    body.append('<?xml version="1.0" encoding="UTF-8"?>')
    body.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_fmt_float(width_mm)}mm" '
        f'height="{_fmt_float(height_mm)}mm" viewBox="0 0 {_fmt_float(width_mm)} {_fmt_float(height_mm)}" '
        'preserveAspectRatio="xMinYMin meet" version="1.1">'
    )
    body.append(style_block)
    body.append(
        f'<rect class="sheet-border" x="0" y="0" width="{_fmt_float(width_mm)}" height="{_fmt_float(height_mm)}" />'
    )
    body.append(
        f'<text class="sheet-header" font-size="{_fmt_float(header_font)}" '
        f'x="{_fmt_float(width_mm / 2.0)}" y="{_fmt_float(header_y)}">'
        f"{escape(header_text)}</text>"
    )

    sorted_parts = sorted(
        placements,
        key=lambda p: (
            -float(getattr(p, "y", 0.0) or 0.0),
            float(getattr(p, "x", 0.0) or 0.0),
            str(getattr(p, "id", "")),
        ),
    )

    for placement in sorted_parts:
        try:
            x = float(getattr(placement, "x", 0.0))
            y = float(getattr(placement, "y", 0.0))
            w = float(getattr(placement, "width", 0.0))
            h = float(getattr(placement, "height", 0.0))
        except Exception:
            continue
        if w <= 0 or h <= 0:
            continue

        rect_y = _svg_y(height_mm, y + h)
        body.append(
            f'<rect class="part-rect" x="{_fmt_float(x)}" y="{_fmt_float(rect_y)}" '
            f'width="{_fmt_float(w)}" height="{_fmt_float(h)}" />'
        )

        if not include_labels:
            continue

        part_font = _part_font_size(w, h, (width_mm, height_mm))
        center_x = x + w / 2.0
        center_y = _svg_y(height_mm, y + h / 2.0)
        lines = [str(getattr(placement, "id", "") or "Part")]
        if include_dimensions:
            dim_text = _format_dimension_pair(w, h, measurement_system)
            lines.append(dim_text)

        line_spacing = 1.2
        start_offset = -line_spacing * (len(lines) - 1) / 2.0
        label_parts = [
            f'<text class="part-label" font-size="{_fmt_float(part_font)}" '
            f'x="{_fmt_float(center_x)}" y="{_fmt_float(center_y)}" dominant-baseline="middle">'
        ]
        for idx, line in enumerate(lines):
            if idx == 0 and len(lines) > 1:
                dy_attr = f' dy="{_fmt_float(start_offset, 2)}em"'
            elif idx == 0:
                dy_attr = ""
            else:
                dy_attr = f' dy="{_fmt_float(line_spacing, 2)}em"'
            label_parts.append(
                f'<tspan x="{_fmt_float(center_x)}"{dy_attr}>{escape(line)}</tspan>'
            )
        label_parts.append("</text>")
        body.append("".join(label_parts))

    body.append("</svg>")
    return "\n".join(body)
