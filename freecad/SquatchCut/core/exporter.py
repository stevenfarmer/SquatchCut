"""Export helpers for SquatchCut nesting layouts (DXF, SVG, cut list CSV).

This module also defines the canonical export data model:
    - ExportPartPlacement: single nested part instance (geometry in mm).
    - ExportSheet: one sheet with its parts.
    - ExportJob: the entire nesting result (list of sheets + measurement system hint).

All geometry must remain in millimeters internally. Measurement system metadata
is only used when formatting strings for UI/export output.
"""

from __future__ import annotations

import csv
import os
import tempfile
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from html import escape
from pathlib import Path

from SquatchCut.core import logger, session_state
from SquatchCut.core import units as unit_utils
from SquatchCut.core.cutlist import generate_cutlist
from SquatchCut.core.nesting import (
    PlacedPart,
    derive_sheet_sizes_for_layout,
    resolve_sheet_dimensions,
)
from SquatchCut.freecad_integration import App, Part

try:
    from SquatchCut.core.text_helpers import create_export_shape_text
except ImportError:  # pragma: no cover - fallback for stripped installs
    _MISSING_TEXT_HELPER_WARNED = False

    def create_export_shape_text(*_args, **_kwargs):
        global _MISSING_TEXT_HELPER_WARNED
        if not _MISSING_TEXT_HELPER_WARNED:
            logger.warning(
                "[SquatchCut] text helper module unavailable; export labels disabled."
            )
            _MISSING_TEXT_HELPER_WARNED = True
        return None


_EXPORT_SUBDIR = "SquatchCutExports"


@dataclass
class ExportPartPlacement:
    """Normalized placement information for a single nested part (all units in mm)."""

    part_id: str
    sheet_index: int
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotation_deg: int = 0


@dataclass
class ExportSheet:
    """One nested sheet and its associated parts."""

    sheet_index: int
    width_mm: float
    height_mm: float
    parts: list[ExportPartPlacement] = field(default_factory=list)


@dataclass
class ExportJob:
    """Canonical description of a full SquatchCut nesting result."""

    job_name: str
    measurement_system: str  # "metric" or "imperial"
    sheets: list[ExportSheet] = field(default_factory=list)


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
            logger.warning(
                f"[SquatchCut] Unable to prepare export directory '{candidate.parent}': {exc}"
            )
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
            [
                "sheet_index",
                "part_id",
                "width_mm",
                "height_mm",
                "rotation_deg",
                "x_mm",
                "y_mm",
            ]
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
            txt = create_export_shape_text(
                doc, str(label), tx, ty, 0.0, size=_label_size(w, h)
            )
            if txt is not None:
                objs.append(txt)

        # Optional simple dimensions (text only near edges)
        if include_dimensions:
            margin = 5.0
            tx = x + w / 2.0 + sheet_index * (sheet_w + sheet_spacing)
            ty = y - margin
            tw = create_export_shape_text(
                doc, f"W: {w:.1f} mm", tx, ty, 0.0, size=_label_size(w, h) * 0.6
            )
            if tw is not None:
                objs.append(tw)
            tx = x + w + margin + sheet_index * (sheet_w + sheet_spacing)
            ty = y + h / 2.0
            th = create_export_shape_text(
                doc, f"H: {h:.1f} mm", tx, ty, 0.0, size=_label_size(w, h) * 0.6
            )
            if th is not None:
                objs.append(th)
    return objs


def export_cutlist_map_to_csv(
    cutlist_by_sheet: dict[int, list], file_path: str
) -> None:
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


def export_cutlist_to_text(
    cutlist_by_sheet: dict[int, list],
    file_path: str,
    export_job: ExportJob | None = None,
) -> None:
    """Write a human-readable cutlist script to text."""

    def _fmt(val_mm):
        if export_job:
            return format_dimension_for_export(float(val_mm or 0.0), export_job)
        return f"{float(val_mm or 0.0):.1f} mm"

    with open(file_path, "w", encoding="utf-8") as fh:
        for sheet_index in sorted(cutlist_by_sheet.keys()):
            fh.write(f"Sheet {sheet_index + 1}\n")
            fh.write("-" * 22 + "\n")
            for cut in cutlist_by_sheet[sheet_index]:
                fh.write(
                    f"{cut.get('cut_order', '')}. {cut.get('cut_type', '')} cut:\n"
                )
                fh.write(
                    f"   Direction: {cut.get('cut_direction', '')} from {cut.get('from_edge', '')} "
                    f"at {_fmt(cut.get('distance_from_edge_mm'))}\n"
                )
                fh.write(f"   Length: {_fmt(cut.get('cut_length_mm'))}\n")
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
) -> list[Path]:
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
    sheet_sizes = derive_sheet_sizes_for_layout(
        sheet_mode, job_sheet_defs, sheet_w, sheet_h, placements
    )

    placements_by_sheet = _group_placements_by_sheet(placements)
    if not placements_by_sheet:
        raise ValueError("Placements could not be grouped by sheet for SVG export.")
    max_sheet_index = max(placements_by_sheet.keys())
    sheet_total = max_sheet_index + 1

    generated_paths: list[Path] = []
    for sheet_index in sorted(placements_by_sheet.keys()):
        width_mm, height_mm = resolve_sheet_dimensions(
            sheet_sizes, sheet_index, sheet_w, sheet_h
        )
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


def _group_placements_by_sheet(placements: Sequence) -> dict[int, list]:
    grouped: dict[int, list] = defaultdict(list)
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


def _get_current_timestamp() -> str:
    """Get current timestamp for cutlist header."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _format_sheet_size_for_export(sheet: ExportSheet, export_job: ExportJob) -> str:
    """Format sheet size for display in cutlist."""
    width_display = format_dimension_for_export(sheet.width_mm, export_job)
    height_display = format_dimension_for_export(sheet.height_mm, export_job)
    unit_label = "in" if export_job.measurement_system == "imperial" else "mm"
    return f"{width_display} x {height_display} {unit_label}"


def _generate_cut_instructions(
    part: ExportPartPlacement, sheet: ExportSheet, export_job: ExportJob
) -> str:
    """Generate human-readable cutting instructions for a part."""
    width_display = format_dimension_for_export(part.width_mm, export_job)
    height_display = format_dimension_for_export(part.height_mm, export_job)

    # Determine if part is rotated
    if part.rotation_deg != 0:
        rotation_note = " (rotated 90°)"
    else:
        rotation_note = ""

    # Generate position-based instruction
    pos_left = format_dimension_for_export(part.x_mm, export_job)
    pos_bottom = format_dimension_for_export(part.y_mm, export_job)

    # Create clear, actionable instruction
    instruction = f"Cut {width_display} x {height_display}{rotation_note}"

    # Add position guidance for precision work
    if export_job.measurement_system == "imperial":
        instruction += (
            f" - Position: {pos_left} from left edge, {pos_bottom} from bottom edge"
        )
    else:
        instruction += (
            f" - Position: {pos_left}mm from left, {pos_bottom}mm from bottom"
        )

    return instruction


def _svg_y(sheet_height: float, math_y: float) -> float:
    """Convert mathematical coordinate (origin bottom-left) to SVG (origin top-left)."""
    return sheet_height - math_y


def _format_dimension_pair(
    width_mm: float, height_mm: float, measurement_system: str
) -> str:
    label = unit_utils.unit_label_for_system(measurement_system)
    width_str = unit_utils.format_length(width_mm, measurement_system)
    height_str = unit_utils.format_length(height_mm, measurement_system)
    return f"{width_str} x {height_str} {label}"


def _part_font_size(
    width_mm: float, height_mm: float, sheet_size: tuple[float, float]
) -> float:
    min_sheet_dim = max(min(sheet_size), 1.0)
    base = min(width_mm, height_mm) * 0.25
    base = min(base, min_sheet_dim / 10.0)
    return max(base, min_sheet_dim / 50.0, 6.0)


def _render_sheet_svg(
    sheet_number: int,
    total_sheets: int,
    sheet_dimensions: tuple[float, float],
    sheet: ExportSheet,
    measurement_system: str,
    include_labels: bool,
    include_dimensions: bool,
    include_cut_lines: bool,
    include_waste_areas: bool,
    export_job: ExportJob,
) -> str:
    width_mm, height_mm = sheet_dimensions
    width_mm = float(width_mm or 0.0)
    height_mm = float(height_mm or 0.0)
    min_sheet_dim = max(min(width_mm, height_mm), 1.0)
    header_font = max(min_sheet_dim / 18.0, 10.0)
    header_margin = min(max(min_sheet_dim * 0.04, 8.0), 30.0)
    header_y = height_mm - header_margin
    header_text = f"Sheet {sheet_number} of {total_sheets} – {_format_dimension_pair(width_mm, height_mm, measurement_system)}"
    style_block = (
        "<style>"
        ".sheet-border{fill:none;stroke:#000;stroke-width:1;}"
        ".part-rect{fill:none;stroke:#111;stroke-width:0.5;}"
        ".part-label{fill:#111;font-family:sans-serif;text-anchor:middle;}"
        ".sheet-header{fill:#000;font-family:sans-serif;text-anchor:middle;}"
        ".cut-line{stroke:#ff0000;stroke-width:0.3;stroke-dasharray:2,2;}"
        ".waste-area{fill:#ffcccc;fill-opacity:0.3;stroke:none;}"
        "</style>"
    )

    body: list[str] = []
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
        f'x="{_fmt_float(width_mm / 2.0)}" y="{_fmt_float(header_y)}" dominant-baseline="middle">'
        f"{escape(header_text)}</text>"
    )

    parts_sorted = sorted(sheet.parts, key=lambda p: (p.y_mm, p.x_mm, p.part_id or ""))

    # Add cut lines if requested
    if include_cut_lines:
        cut_lines = _calculate_cut_lines(sheet.parts, width_mm, height_mm)
        for line in cut_lines:
            if line["direction"] == "vertical":
                body.append(
                    f'<line class="cut-line" x1="{_fmt_float(line["position"])}" y1="0" '
                    f'x2="{_fmt_float(line["position"])}" y2="{_fmt_float(height_mm)}" />'
                )
            else:  # horizontal
                body.append(
                    f'<line class="cut-line" x1="0" y1="{_fmt_float(line["position"])}" '
                    f'x2="{_fmt_float(width_mm)}" y2="{_fmt_float(line["position"])}" />'
                )

    # Add waste areas if requested
    if include_waste_areas:
        waste_areas = _calculate_waste_areas(sheet.parts, width_mm, height_mm)
        for area in waste_areas:
            body.append(
                f'<rect class="waste-area" x="{_fmt_float(area["x"])}" y="{_fmt_float(area["y"])}" '
                f'width="{_fmt_float(area["width"])}" height="{_fmt_float(area["height"])}" />'
            )

    for part in parts_sorted:
        x = float(part.x_mm or 0.0)
        y = float(part.y_mm or 0.0)
        w = float(part.width_mm or 0.0)
        h = float(part.height_mm or 0.0)
        if w <= 0 or h <= 0:
            continue

        body.append(
            f'<rect class="part-rect" x="{_fmt_float(x)}" y="{_fmt_float(y)}" '
            f'width="{_fmt_float(w)}" height="{_fmt_float(h)}" />'
        )

        if not include_labels:
            continue

        part_font = _part_font_size(w, h, (width_mm, height_mm))
        center_x = x + w / 2.0
        center_y = y + h / 2.0
        ident = part.part_id or "Part"
        lines = [str(ident)]
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


def build_export_job_from_current_nesting(doc=None) -> ExportJob | None:
    """
    Adapt the latest nesting layout stored in session_state to the ExportJob model.

    Returns None when no placements are available.
    """

    placements = session_state.get_last_layout() or []
    if not placements:
        logger.info("[SquatchCut] ExportJob build skipped: no placements stored.")
        return None

    measurement_system = session_state.get_measurement_system() or "metric"
    sheet_mode = session_state.get_sheet_mode()
    job_sheets = session_state.get_job_sheets()
    default_sheet_w, default_sheet_h = session_state.get_sheet_size()
    sheet_sizes = derive_sheet_sizes_for_layout(
        sheet_mode,
        job_sheets,
        default_sheet_w,
        default_sheet_h,
        placements,
    )

    fallback_w = float(default_sheet_w or 0.0)
    fallback_h = float(default_sheet_h or 0.0)
    grouped = _group_placements_by_sheet(placements)

    sheets: list[ExportSheet] = []
    total_parts = 0
    for sheet_index in sorted(grouped.keys()):
        width_mm, height_mm = resolve_sheet_dimensions(
            sheet_sizes, sheet_index, fallback_w, fallback_h
        )
        export_parts: list[ExportPartPlacement] = []
        for placement in grouped[sheet_index]:
            try:
                part_id = str(getattr(placement, "id", "") or "")
                x_mm = float(getattr(placement, "x", 0.0))
                y_mm = float(getattr(placement, "y", 0.0))
                width = float(getattr(placement, "width", 0.0))
                height = float(getattr(placement, "height", 0.0))
                rotation = int(getattr(placement, "rotation_deg", 0) or 0)
            except Exception:
                continue
            export_parts.append(
                ExportPartPlacement(
                    part_id=part_id,
                    sheet_index=sheet_index,
                    x_mm=x_mm,
                    y_mm=y_mm,
                    width_mm=width,
                    height_mm=height,
                    rotation_deg=rotation,
                )
            )
        total_parts += len(export_parts)
        sheets.append(
            ExportSheet(
                sheet_index=sheet_index,
                width_mm=float(width_mm or 0.0),
                height_mm=float(height_mm or 0.0),
                parts=export_parts,
            )
        )

    job_name = _resolve_job_name(doc)
    export_job = ExportJob(
        job_name=job_name, measurement_system=measurement_system, sheets=sheets
    )
    logger.info(
        f"[SquatchCut] ExportJob summary: {len(sheets)} sheet(s), {total_parts} part(s)."
    )
    for sheet in sheets[:3]:
        logger.info(
            f"[SquatchCut]   Sheet {sheet.sheet_index}: {_fmt_float(sheet.width_mm)} x {_fmt_float(sheet.height_mm)} mm, {len(sheet.parts)} part(s)."
        )
    return export_job


def _resolve_job_name(doc) -> str:
    if doc is None:
        return "SquatchCut Job"
    for attr in ("Label", "LabelText", "Name"):
        try:
            value = getattr(doc, attr, None)
        except Exception:
            value = None
        if value:
            return str(value)
    file_name = getattr(doc, "FileName", "") or ""
    if file_name:
        return Path(file_name).stem
    return "SquatchCut Job"


def export_cutlist(
    export_job: ExportJob, target_path: str, *, as_text: bool = False
) -> None:
    """
    Export a cutlist for the provided ExportJob.

    CSV path writes rows directly from ExportJob. Text path reuses legacy helpers.
    """
    if as_text:
        placements = _export_job_to_placements(export_job)
        if not placements:
            logger.warning(
                "[SquatchCut] No placements available; cutlist export skipped."
            )
            return
        primary_sheet = _job_primary_sheet_size(export_job)
        cutlist_map = generate_cutlist(placements, primary_sheet)
        export_cutlist_to_text(cutlist_map, target_path, export_job=export_job)
        return

    if export_job is None or not export_job.sheets:
        logger.warning("[SquatchCut] No sheets available; cutlist export skipped.")
        return

    # Enhanced header with woodshop-friendly column names
    header = [
        "Sheet",
        "Sheet_Size",
        "Part_Name",
        "Width",
        "Height",
        "Qty",
        "Rotated",
        "Position_From_Left",
        "Position_From_Bottom",
        "Cut_Instructions",
    ]

    path = Path(target_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    try:
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)

            # Write project header information
            writer.writerow(["# SquatchCut Cutting List"])
            writer.writerow([f"# Generated: {_get_current_timestamp()}"])
            writer.writerow(
                [f"# Measurement System: {export_job.measurement_system.title()}"]
            )
            writer.writerow([f"# Total Sheets: {len(export_job.sheets)}"])
            writer.writerow([])  # Blank line

            # Write column headers
            writer.writerow(header)

            # Group parts by sheet for better organization
            for sheet in sorted(export_job.sheets, key=lambda s: s.sheet_index):
                sheet_size_display = _format_sheet_size_for_export(sheet, export_job)

                # Sort parts by position for logical cutting order
                sorted_parts = sorted(sheet.parts, key=lambda p: (p.y_mm, p.x_mm))

                for part in sorted_parts:
                    width_display = format_dimension_for_export(
                        part.width_mm, export_job
                    )
                    height_display = format_dimension_for_export(
                        part.height_mm, export_job
                    )

                    # Generate human-readable cutting instructions
                    cut_instructions = _generate_cut_instructions(
                        part, sheet, export_job
                    )

                    # Position from edges (more intuitive for woodworkers)
                    pos_left = format_dimension_for_export(part.x_mm, export_job)
                    pos_bottom = format_dimension_for_export(part.y_mm, export_job)

                    writer.writerow(
                        [
                            f"Sheet {sheet.sheet_index + 1}",
                            sheet_size_display,
                            part.part_id,
                            width_display,
                            height_display,
                            1,  # Individual parts (qty handled during import)
                            "Yes" if part.rotation_deg != 0 else "No",
                            pos_left,
                            pos_bottom,
                            cut_instructions,
                        ]
                    )

                # Add blank line between sheets for readability
                if sheet.sheet_index < len(export_job.sheets) - 1:
                    writer.writerow([])

            # Add cutting tips at the end
            writer.writerow([])
            writer.writerow(["# Cutting Tips:"])
            writer.writerow(
                ["# 1. Cut all parts from one sheet before moving to the next"]
            )
            writer.writerow(["# 2. Mark each part clearly before cutting"])
            writer.writerow(["# 3. Measure twice, cut once"])
            writer.writerow(["# 4. Account for saw kerf in your measurements"])

    except OSError as exc:
        logger.warning(f"[SquatchCut] CSV export failed for '{target_path}': {exc}")
        raise
    return


def export_nesting_to_svg(
    export_job: ExportJob,
    base_path: str,
    *,
    include_labels: bool = True,
    include_dimensions: bool = False,
    include_cut_lines: bool = False,
    include_waste_areas: bool = False,
) -> list[Path]:
    """
    Export one SVG per sheet for the provided ExportJob.

    Returns the list of generated file paths.
    """
    if export_job is None or not export_job.sheets:
        logger.warning("[SquatchCut] SVG export skipped: job has no sheets.")
        return []

    base_target = Path(base_path)
    if base_target.suffix.lower() != ".svg":
        base_target = base_target.with_suffix(".svg")
    try:
        base_target.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    total_sheets = len(export_job.sheets)
    measurement_system = export_job.measurement_system or "metric"
    generated_paths: list[Path] = []
    for idx, sheet in enumerate(sorted(export_job.sheets, key=lambda s: s.sheet_index)):
        content = _render_sheet_svg(
            sheet_number=idx + 1,
            total_sheets=total_sheets,
            sheet_dimensions=(sheet.width_mm, sheet.height_mm),
            sheet=sheet,
            measurement_system=measurement_system,
            include_labels=include_labels,
            include_dimensions=include_dimensions,
            include_cut_lines=include_cut_lines,
            include_waste_areas=include_waste_areas,
            export_job=export_job,
        )
        target_path = _sheet_specific_path(base_target, idx + 1)
        try:
            target_path.write_text(content, encoding="utf-8")
        except OSError as exc:
            logger.warning(f"[SquatchCut] SVG export failed for '{target_path}': {exc}")
            raise
        generated_paths.append(target_path)

    logger.info(
        f"[SquatchCut] SVG export complete via gateway: {len(generated_paths)} file(s)."
    )
    return generated_paths


def export_nesting_to_dxf(export_job: ExportJob, base_path: str) -> None:
    """Placeholder DXF exporter for ExportJob inputs."""
    logger.warning("[SquatchCut] DXF export via gateway is not implemented yet.")
    raise NotImplementedError("DXF export via ExportJob is not available yet.")


def _job_primary_sheet_size(export_job: ExportJob) -> tuple[float, float]:
    if export_job.sheets:
        first = export_job.sheets[0]
        return float(first.width_mm or 0.0), float(first.height_mm or 0.0)
    return 0.0, 0.0


def _export_job_to_placements(export_job: ExportJob) -> list[PlacedPart]:
    placements: list[PlacedPart] = []
    for sheet in export_job.sheets:
        for part in sheet.parts:
            placements.append(
                PlacedPart(
                    id=part.part_id or "",
                    sheet_index=sheet.sheet_index,
                    x=part.x_mm,
                    y=part.y_mm,
                    width=part.width_mm,
                    height=part.height_mm,
                    rotation_deg=int(part.rotation_deg or 0),
                )
            )
    return placements


def _sheet_part_proxies(sheet: ExportSheet) -> list[ExportPartPlacement]:
    # Return shallow copies to avoid mutating the original ExportJob data.
    proxies: list[ExportPartPlacement] = []
    for part in sheet.parts:
        proxies.append(
            ExportPartPlacement(
                part_id=part.part_id,
                sheet_index=sheet.sheet_index,
                x_mm=part.x_mm,
                y_mm=part.y_mm,
                width_mm=part.width_mm,
                height_mm=part.height_mm,
                rotation_deg=part.rotation_deg,
            )
        )
    return proxies


def format_dimension_for_export(value_mm: float, export_job: ExportJob) -> str:
    """Format a dimension in the measurement system requested by the ExportJob."""
    system = (export_job.measurement_system or "metric").lower()
    if system == "imperial":
        inches = unit_utils.mm_to_inches(value_mm)
        formatted = unit_utils.inches_to_fraction_str(inches)
        return f"{formatted} in"
    metric_value = unit_utils.format_metric_length(value_mm, decimals=3)
    return f"{metric_value} mm"


def _calculate_cut_lines(
    parts: list[ExportPartPlacement], sheet_width: float, sheet_height: float
) -> list[dict]:
    """Calculate cut lines for efficient cutting sequence."""
    cut_lines = []

    # Collect all unique x and y coordinates from part boundaries
    x_coords = set([0.0, sheet_width])
    y_coords = set([0.0, sheet_height])

    for part in parts:
        x_coords.add(part.x_mm)
        x_coords.add(part.x_mm + part.width_mm)
        y_coords.add(part.y_mm)
        y_coords.add(part.y_mm + part.height_mm)

    # Add vertical cut lines
    for x in sorted(x_coords):
        if 0 < x < sheet_width:  # Exclude sheet edges
            cut_lines.append(
                {"direction": "vertical", "position": x, "length": sheet_height}
            )

    # Add horizontal cut lines
    for y in sorted(y_coords):
        if 0 < y < sheet_height:  # Exclude sheet edges
            cut_lines.append(
                {"direction": "horizontal", "position": y, "length": sheet_width}
            )

    return cut_lines


def _calculate_waste_areas(
    parts: list[ExportPartPlacement], sheet_width: float, sheet_height: float
) -> list[dict]:
    """Calculate waste areas (unused space) on the sheet."""
    waste_areas = []

    # Create a grid to track occupied areas
    # Use 1mm resolution for reasonable performance
    grid_resolution = 1.0
    grid_width = int(sheet_width / grid_resolution) + 1
    grid_height = int(sheet_height / grid_resolution) + 1
    occupied = [[False for _ in range(grid_height)] for _ in range(grid_width)]

    # Mark occupied areas
    for part in parts:
        x_start = int(part.x_mm / grid_resolution)
        x_end = int((part.x_mm + part.width_mm) / grid_resolution) + 1
        y_start = int(part.y_mm / grid_resolution)
        y_end = int((part.y_mm + part.height_mm) / grid_resolution) + 1

        for x in range(max(0, x_start), min(grid_width, x_end)):
            for y in range(max(0, y_start), min(grid_height, y_end)):
                occupied[x][y] = True

    # Find rectangular waste areas
    visited = [[False for _ in range(grid_height)] for _ in range(grid_width)]

    for x in range(grid_width):
        for y in range(grid_height):
            if not occupied[x][y] and not visited[x][y]:
                # Found unoccupied cell, try to expand into rectangle
                width = 0
                height = 0

                # Find maximum width
                while (
                    x + width < grid_width
                    and not occupied[x + width][y]
                    and not visited[x + width][y]
                ):
                    width += 1

                # Find maximum height for this width
                valid_height = True
                while valid_height and y + height < grid_height:
                    for w in range(width):
                        if occupied[x + w][y + height] or visited[x + w][y + height]:
                            valid_height = False
                            break
                    if valid_height:
                        height += 1

                # Mark area as visited
                for w in range(width):
                    for h in range(height):
                        if x + w < grid_width and y + h < grid_height:
                            visited[x + w][y + h] = True

                # Add waste area if it's significant (> 100 sq mm)
                area_mm2 = (width * grid_resolution) * (height * grid_resolution)
                if area_mm2 > 100:
                    waste_areas.append(
                        {
                            "x": x * grid_resolution,
                            "y": y * grid_resolution,
                            "width": width * grid_resolution,
                            "height": height * grid_resolution,
                            "area": area_mm2,
                        }
                    )

    return waste_areas


def export_nesting_to_dxf(
    export_job: ExportJob,
    base_path: str,
    *,
    include_labels: bool = True,
    include_dimensions: bool = False,
    include_cut_lines: bool = False,
) -> list[Path]:
    """
    Export nesting layout to DXF format with optional cut lines.

    Returns list of generated file paths (one per sheet).
    """
    if export_job is None or not export_job.sheets:
        logger.warning("[SquatchCut] DXF export skipped: job has no sheets.")
        return []

    try:
        import ezdxf
    except ImportError:
        raise RuntimeError(
            "DXF export requires the 'ezdxf' package. Install it with: pip install ezdxf"
        )

    base_target = Path(base_path)
    if base_target.suffix.lower() != ".dxf":
        base_target = base_target.with_suffix(".dxf")

    try:
        base_target.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    generated_paths: list[Path] = []

    for idx, sheet in enumerate(sorted(export_job.sheets, key=lambda s: s.sheet_index)):
        # Create new DXF document
        doc = ezdxf.new("R2010")  # Use R2010 for broad compatibility
        msp = doc.modelspace()

        # Add sheet boundary
        msp.add_lwpolyline(
            [
                (0, 0),
                (sheet.width_mm, 0),
                (sheet.width_mm, sheet.height_mm),
                (0, sheet.height_mm),
                (0, 0),
            ],
            close=True,
            dxfattribs={"layer": "SHEET_BOUNDARY", "color": 1},
        )

        # Add parts
        for part in sheet.parts:
            x, y = part.x_mm, part.y_mm
            w, h = part.width_mm, part.height_mm

            # Add part rectangle
            msp.add_lwpolyline(
                [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)],
                close=True,
                dxfattribs={"layer": "PARTS", "color": 2},
            )

            # Add part label if requested
            if include_labels and part.part_id:
                text_x = x + w / 2
                text_y = y + h / 2
                text_height = min(w, h) * 0.1
                msp.add_text(
                    part.part_id,
                    dxfattribs={
                        "layer": "LABELS",
                        "color": 3,
                        "height": max(text_height, 2.0),
                    },
                ).set_pos((text_x, text_y), align="MIDDLE_CENTER")

            # Add dimensions if requested
            if include_dimensions:
                dim_layer = "DIMENSIONS"
                # Width dimension (bottom)
                msp.add_linear_dim(
                    base=(x, y - 5),
                    p1=(x, y),
                    p2=(x + w, y),
                    dxfattribs={"layer": dim_layer, "color": 4},
                )
                # Height dimension (left)
                msp.add_linear_dim(
                    base=(x - 5, y),
                    p1=(x, y),
                    p2=(x, y + h),
                    dxfattribs={"layer": dim_layer, "color": 4},
                )

        # Add cut lines if requested
        if include_cut_lines:
            cut_lines = _calculate_cut_lines(
                sheet.parts, sheet.width_mm, sheet.height_mm
            )
            for line in cut_lines:
                if line["direction"] == "vertical":
                    msp.add_line(
                        (line["position"], 0),
                        (line["position"], sheet.height_mm),
                        dxfattribs={
                            "layer": "CUT_LINES",
                            "color": 1,
                            "linetype": "DASHED",
                        },
                    )
                else:  # horizontal
                    msp.add_line(
                        (0, line["position"]),
                        (sheet.width_mm, line["position"]),
                        dxfattribs={
                            "layer": "CUT_LINES",
                            "color": 1,
                            "linetype": "DASHED",
                        },
                    )

        # Save DXF file
        target_path = _sheet_specific_path(base_target, idx + 1)
        target_path = target_path.with_suffix(".dxf")

        try:
            doc.saveas(str(target_path))
            generated_paths.append(target_path)
        except Exception as exc:
            logger.warning(f"[SquatchCut] DXF export failed for '{target_path}': {exc}")
            raise

    logger.info(f"[SquatchCut] DXF export complete: {len(generated_paths)} file(s).")
    return generated_paths
