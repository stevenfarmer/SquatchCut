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
from typing import Optional, Union

from SquatchCut.core import logger, session_state
from SquatchCut.core import units as unit_utils
from SquatchCut.core.cutlist import generate_cutlist
from SquatchCut.core.nesting import (
    PlacedPart,
    derive_sheet_sizes_for_layout,
    resolve_sheet_dimensions,
)
from SquatchCut.core.session import detect_document_measurement_system
from SquatchCut.freecad_integration import App, Part

# Import for complex geometry support
try:
    from SquatchCut.core.complex_geometry import ComplexGeometry
except ImportError:
    ComplexGeometry = None

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
    # Enhanced fields for complex geometry support
    complex_geometry: Optional[ComplexGeometry] = None
    kerf_compensation: Optional[float] = None
    geometry_type: str = "rectangular"  # "rectangular", "curved", "complex"


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
    file_path: Optional[Union[str, os.PathLike]],
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
    export_job: Optional[ExportJob] = None,
) -> None:
    """Write human-friendly cutting instructions to text file."""

    def _fmt(val_mm):
        if export_job:
            return format_dimension_for_export(float(val_mm or 0.0), export_job)
        return f"{float(val_mm or 0.0):.1f} mm"

    with open(file_path, "w", encoding="utf-8") as fh:
        # Write header
        fh.write("SquatchCut Cutting Instructions\n")
        fh.write("=" * 40 + "\n\n")

        if export_job:
            fh.write(f"Project: {export_job.job_name}\n")
            fh.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            fh.write(f"Measurement System: {export_job.measurement_system.title()}\n")
            fh.write(f"Total Sheets: {len(export_job.sheets)}\n\n")

        # Write cutting instructions for each sheet
        for sheet_index in sorted(cutlist_by_sheet.keys()):
            sheet_num = sheet_index + 1
            fh.write(f"SHEET {sheet_num} CUTTING INSTRUCTIONS\n")
            fh.write("-" * 35 + "\n\n")

            cuts = cutlist_by_sheet[sheet_index]
            if not cuts:
                fh.write("No cuts required for this sheet.\n\n")
                continue

            fh.write("Recommended cutting sequence:\n\n")

            for i, cut in enumerate(cuts, 1):
                cut_type = cut.get("cut_type", "Cut").title()
                direction = cut.get("cut_direction", "").title()
                from_edge = cut.get("from_edge", "").replace("_", " ").title()
                distance = _fmt(cut.get("distance_from_edge_mm", 0))
                length = _fmt(cut.get("cut_length_mm", 0))
                parts = cut.get("parts_affected", []) or []

                fh.write(f"{i}. {cut_type} Cut\n")
                fh.write(
                    f"   • Cut {direction.lower()} from {from_edge.lower()} edge\n"
                )
                fh.write(f"   • Measure {distance} from edge\n")
                fh.write(f"   • Cut length: {length}\n")

                if parts:
                    if len(parts) == 1:
                        fh.write(f"   • This releases part: {parts[0]}\n")
                    else:
                        fh.write(f"   • This releases parts: {', '.join(parts)}\n")

                fh.write("\n")

            fh.write("\n")

        # Write safety reminder
        fh.write("SAFETY REMINDERS\n")
        fh.write("-" * 16 + "\n")
        fh.write("• Always wear safety glasses and hearing protection\n")
        fh.write("• Check blade sharpness and alignment before cutting\n")
        fh.write("• Support long pieces properly to prevent binding\n")
        fh.write("• Double-check measurements before making cuts\n")
        fh.write("• Keep hands clear of blade path\n\n")

        fh.write("Generated by SquatchCut - FreeCAD Nesting Add-on\n")


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
    job_sheets: Optional[Sequence[dict]],
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

    # Create clear, actionable instruction based on geometry type
    geometry_type = _get_geometry_type_display(part)

    if geometry_type == "Rectangle":
        instruction = f"Cut {width_display} x {height_display}{rotation_note}"
    else:
        instruction = f"Cut {geometry_type} - {width_display} x {height_display} bounding box{rotation_note}"

        # Add shape-specific cutting advice
        if hasattr(part, "complex_geometry") and part.complex_geometry is not None:
            if (
                hasattr(part.complex_geometry, "kerf_compensation")
                and part.complex_geometry.kerf_compensation
            ):
                instruction += " (kerf compensated)"

            # Add complexity warning for complex shapes
            complexity = _get_complexity_display(part)
            if complexity in ["Complex", "Very Complex"]:
                instruction += f" - {complexity} shape: use template or CNC"

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
    """Calculate appropriate font size for part labels.

    Font size is based primarily on part dimensions to ensure labels
    fit within their parts and don't cross into adjacent parts.

    Returns a font size that:
    1. Fits within the part dimensions (most important)
    2. Is readable but not overwhelming
    3. Is consistent across parts of similar size
    """
    min_part_dim = min(width_mm, height_mm)

    # Font size based ONLY on part size, not sheet size
    # This prevents labels from crossing into adjacent parts
    # Use 8-10% of the smaller dimension
    font_size = min_part_dim * 0.08

    # Absolute bounds for readability
    min_readable = 8.0  # Minimum for readability
    max_reasonable = 16.0  # Maximum to prevent overwhelming

    # Clamp to bounds
    font_size = max(font_size, min_readable)
    font_size = min(font_size, max_reasonable)

    return font_size


def _complex_geometry_to_svg_path(
    geometry: ComplexGeometry, offset_x: float = 0.0, offset_y: float = 0.0
) -> str:
    """Convert ComplexGeometry contour points to SVG path data.

    Args:
        geometry: ComplexGeometry object with contour points
        offset_x: X offset to apply to all points
        offset_y: Y offset to apply to all points

    Returns:
        SVG path data string, or empty string if conversion fails
    """
    if not geometry or not geometry.contour_points or len(geometry.contour_points) < 3:
        return ""

    try:
        path_parts = []

        # Start with move to first point
        first_point = geometry.contour_points[0]
        start_x = first_point[0] + offset_x
        start_y = first_point[1] + offset_y
        path_parts.append(f"M {_fmt_float(start_x)} {_fmt_float(start_y)}")

        # Add line segments to subsequent points
        for point in geometry.contour_points[1:]:
            x = point[0] + offset_x
            y = point[1] + offset_y
            path_parts.append(f"L {_fmt_float(x)} {_fmt_float(y)}")

        # Close the path
        path_parts.append("Z")

        return " ".join(path_parts)

    except Exception as e:
        logger.warning(f"Failed to convert ComplexGeometry to SVG path: {e}")
        return ""


def _add_parts_legend(
    body: list[str],
    parts: list,
    sheet_width: float,
    sheet_height: float,
    measurement_system: str,
    include_dimensions: bool = False,
) -> None:
    """Add a parts legend at the bottom of the SVG."""
    if not parts:
        return

    # Calculate legend space needed
    legend_margin = 10.0
    legend_font_size = 10.0
    line_height = 12.0

    # Legend starts below the sheet with some padding
    legend_start_y = sheet_height + 30.0

    # Add legend background for readability
    legend_height = (len(parts) + 2) * line_height + 10.0
    body.append(
        f'<rect x="0" y="{legend_start_y - 15}" '
        f'width="{sheet_width}" height="{legend_height}" '
        f'fill="#f9f9f9" stroke="#ccc" stroke-width="0.5"/>'
    )

    # Add legend title
    body.append(
        f'<text font-family="sans-serif" font-size="{legend_font_size + 2}" '
        f'x="{legend_margin}" y="{legend_start_y}" font-weight="bold" fill="#000">'
        f"PARTS LIST</text>"
    )

    # Add parts list
    current_y = legend_start_y + line_height + 5.0
    for idx, part in enumerate(parts, 1):
        part_id = escape(str(part.part_id or f"Part-{idx}"))
        w = float(part.width_mm or 0.0)
        h = float(part.height_mm or 0.0)

        # Build the legend entry
        if include_dimensions:
            dims = _format_dimension_pair(w, h, measurement_system)
            legend_text = f"{idx}. {part_id} — {dims}"
        else:
            legend_text = f"{idx}. {part_id}"

        body.append(
            f'<text font-family="sans-serif" font-size="{legend_font_size}" '
            f'x="{legend_margin}" y="{current_y}" fill="#333">'
            f"{legend_text}</text>"
        )
        current_y += line_height


def _add_leader_lines(
    body: list[str],
    parts: list,
    sheet_width: float,
    sheet_height: float,
    measurement_system: str,
    min_label_size: float,
) -> None:
    """Add leader lines for parts too small to have internal labels."""
    if not parts:
        return

    # Track which parts need leader lines (too small for internal labels)
    parts_needing_leaders = []

    for idx, part in enumerate(parts, 1):
        x = float(part.x_mm or 0.0)
        y = float(part.y_mm or 0.0)
        w = float(part.width_mm or 0.0)
        h = float(part.height_mm or 0.0)

        # Check if part is too small for internal label
        if w < min_label_size * 3 or h < min_label_size * 2:
            parts_needing_leaders.append(
                {
                    "idx": idx,
                    "part": part,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    "center_x": x + w / 2.0,
                    "center_y": y + h / 2.0,
                }
            )

    if not parts_needing_leaders:
        return

    # Add leader lines
    label_font_size = 9.0
    label_offset = 15.0  # Distance from part to label

    for item in parts_needing_leaders:
        idx = item["idx"]
        part = item["part"]
        center_x = item["center_x"]
        center_y = item["center_y"]
        w = item["w"]
        h = item["h"]

        # Determine best position for label (try to avoid overlaps)
        # Simple strategy: place above if in bottom half, below if in top half
        if center_y < sheet_height / 2:
            # Place below
            label_x = center_x
            label_y = item["y"] + h + label_offset
            line_end_y = item["y"] + h
        else:
            # Place above
            label_x = center_x
            label_y = item["y"] - label_offset
            line_end_y = item["y"]

        # Draw leader line
        body.append(
            f'<line x1="{_fmt_float(center_x)}" y1="{_fmt_float(center_y)}" '
            f'x2="{_fmt_float(label_x)}" y2="{_fmt_float(line_end_y)}" '
            f'stroke="#666" stroke-width="0.5" stroke-dasharray="2,2"/>'
        )

        # Draw label background for readability
        part_id = escape(str(part.part_id or f"Part-{idx}"))
        dims = _format_dimension_pair(w, h, measurement_system)
        label_text = f"{idx}. {part_id}"

        # Estimate text width for background
        text_width = len(label_text) * label_font_size * 0.6

        body.append(
            f'<rect x="{_fmt_float(label_x - text_width/2 - 2)}" '
            f'y="{_fmt_float(label_y - label_font_size)}" '
            f'width="{_fmt_float(text_width + 4)}" height="{label_font_size + 4}" '
            f'fill="white" fill-opacity="0.9" stroke="#666" stroke-width="0.3"/>'
        )

        # Draw label text
        body.append(
            f'<text font-family="sans-serif" font-size="{label_font_size}" '
            f'x="{_fmt_float(label_x)}" y="{_fmt_float(label_y)}" '
            f'text-anchor="middle" fill="#000">{label_text}</text>'
        )


def _render_sheet_svg(
    sheet_number: int,
    total_sheets: int,
    sheet_dimensions: tuple[float, float],
    sheet: ExportSheet,
    measurement_system: str,
    include_labels: bool,  # Now controls legend display
    include_dimensions: bool,  # Now controls dimension display in legend
    include_cut_lines: bool,
    include_waste_areas: bool,
    export_job: ExportJob,
    include_leader_lines: bool = False,  # New parameter for leader lines
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
        ".kerf-line{fill:none;stroke:#0066cc;stroke-width:0.3;stroke-dasharray:1,1;}"
        "</style>"
    )

    body: list[str] = []
    body.append('<?xml version="1.0" encoding="UTF-8"?>')

    # Sort parts first so we can calculate legend space
    parts_sorted = sorted(sheet.parts, key=lambda p: (p.y_mm, p.x_mm, p.part_id or ""))

    # Calculate total height including legend space if labels are enabled
    legend_space = 0.0
    if include_labels and parts_sorted:
        # Estimate legend height: title + parts list + padding
        line_height = 12.0
        legend_space = (len(parts_sorted) + 2) * line_height + 50.0  # Extra padding

    total_height = height_mm + legend_space

    body.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_fmt_float(width_mm)}mm" '
        f'height="{_fmt_float(total_height)}mm" viewBox="0 0 {_fmt_float(width_mm)} {_fmt_float(total_height)}" '
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

        # Render shape based on geometry type
        if hasattr(part, "complex_geometry") and part.complex_geometry is not None:
            # Render complex geometry as SVG path
            geometry = part.complex_geometry

            # Render original geometry
            path_data = _complex_geometry_to_svg_path(geometry, x, y)
            if path_data:
                body.append(f'<path class="part-rect" d="{path_data}" />')

                # Render kerf-compensated geometry if available and different
                if (
                    hasattr(part, "kerf_compensation")
                    and part.kerf_compensation is not None
                    and abs(part.kerf_compensation) > 0.001
                ):
                    try:
                        kerf_geometry = geometry.apply_kerf(part.kerf_compensation)
                        kerf_path_data = _complex_geometry_to_svg_path(
                            kerf_geometry, x, y
                        )
                        if kerf_path_data:
                            body.append(
                                f'<path class="kerf-line" d="{kerf_path_data}" />'
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to render kerf compensation for {part.part_id}: {e}"
                        )
            else:
                # Fallback to rectangle if path generation fails
                body.append(
                    f'<rect class="part-rect" x="{_fmt_float(x)}" y="{_fmt_float(y)}" '
                    f'width="{_fmt_float(w)}" height="{_fmt_float(h)}" />'
                )
        else:
            # Render as rectangle (default behavior)
            body.append(
                f'<rect class="part-rect" x="{_fmt_float(x)}" y="{_fmt_float(y)}" '
                f'width="{_fmt_float(w)}" height="{_fmt_float(h)}" />'
            )

    # Add leader lines if requested (for parts too small for internal labels)
    if include_labels and include_leader_lines:
        min_label_size = 10.0  # Minimum size for readable labels
        _add_leader_lines(
            body, parts_sorted, width_mm, height_mm, measurement_system, min_label_size
        )

    # Add parts legend at bottom of sheet (always shown if include_labels is True)
    if include_labels:
        _add_parts_legend(
            body,
            parts_sorted,
            width_mm,
            height_mm,
            measurement_system,
            include_dimensions,
        )

    body.append("</svg>")
    return "\n".join(body)


def build_export_job_from_current_nesting(doc=None) -> Optional[ExportJob]:
    """
    Adapt the latest nesting layout stored in session_state to the ExportJob model.

    Returns None when no placements are available.
    """

    placements = session_state.get_last_layout() or []
    if not placements:
        logger.info("[SquatchCut] ExportJob build skipped: no placements stored.")
        return None

    # Detect measurement system: prioritize session state when no document
    if doc is None:
        measurement_system = session_state.get_measurement_system() or "metric"
    else:
        measurement_system = (
            detect_document_measurement_system(doc)
            or session_state.get_measurement_system()
            or "metric"
        )
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
            # Try to get complex geometry information from the placement
            complex_geom = None
            kerf_comp = None
            geom_type = "rectangular"

            # Check if placement has complex geometry information
            if (
                hasattr(placement, "complex_geometry")
                and placement.complex_geometry is not None
            ):
                complex_geom = placement.complex_geometry
                geom_type = (
                    complex_geom.geometry_type.value
                    if hasattr(complex_geom.geometry_type, "value")
                    else str(complex_geom.geometry_type)
                )
                kerf_comp = complex_geom.kerf_compensation
            elif hasattr(placement, "geometry_type"):
                geom_type = str(placement.geometry_type)

            export_parts.append(
                ExportPartPlacement(
                    part_id=part_id,
                    sheet_index=sheet_index,
                    x_mm=x_mm,
                    y_mm=y_mm,
                    width_mm=width,
                    height_mm=height,
                    rotation_deg=rotation,
                    complex_geometry=complex_geom,
                    kerf_compensation=kerf_comp,
                    geometry_type=geom_type,
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


def _calculate_part_actual_area(
    part: ExportPartPlacement, export_job: ExportJob
) -> str:
    """Calculate and format the actual area of a part based on its geometry."""
    try:
        if hasattr(part, "complex_geometry") and part.complex_geometry is not None:
            # Use actual geometry area
            area_mm2 = part.complex_geometry.area
        else:
            # Use bounding box area
            area_mm2 = part.width_mm * part.height_mm

        # Format area based on measurement system
        if export_job.measurement_system == "imperial":
            area_in2 = area_mm2 / (25.4 * 25.4)
            return f"{area_in2:.2f} in²"
        else:
            return f"{area_mm2:.0f} mm²"
    except Exception:
        return "N/A"


def _get_geometry_type_display(part: ExportPartPlacement) -> str:
    """Get a user-friendly display of the geometry type."""
    if hasattr(part, "geometry_type") and part.geometry_type:
        type_map = {
            "rectangular": "Rectangle",
            "curved": "Curved",
            "complex": "Complex Shape",
        }
        return type_map.get(part.geometry_type.lower(), part.geometry_type.title())
    return "Rectangle"


def _get_complexity_display(part: ExportPartPlacement) -> str:
    """Get a user-friendly display of the shape complexity."""
    try:
        if hasattr(part, "complex_geometry") and part.complex_geometry is not None:
            complexity = part.complex_geometry.complexity_level
            if hasattr(complexity, "value"):
                complexity_str = complexity.value
            else:
                complexity_str = str(complexity)

            # Map complexity levels to user-friendly terms
            complexity_map = {
                "low": "Simple",
                "medium": "Moderate",
                "high": "Complex",
                "extreme": "Very Complex",
            }
            return complexity_map.get(complexity_str.lower(), complexity_str.title())
        return "Simple"
    except Exception:
        return "Simple"


def export_cutlist(
    export_job: ExportJob,
    target_path: str,
    *,
    as_text: bool = False,
    enhanced_format: bool = False,
) -> None:
    """
    Export a cutlist for the provided ExportJob.

    Args:
        export_job: The export job to process
        target_path: Path to write the cutlist file
        as_text: If True, export as human-readable text instead of CSV
        enhanced_format: If True, use enhanced woodshop-friendly CSV format with headers and instructions

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

    path = Path(target_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    if enhanced_format:
        _export_enhanced_cutlist_csv(export_job, path)
    else:
        _export_simple_cutlist_csv(export_job, path)


def _export_simple_cutlist_csv(export_job: ExportJob, path: Path) -> None:
    """Export cutlist in simple CSV format for backward compatibility."""
    # Simple header matching original format
    header = [
        "sheet_index",
        "sheet_width_mm",
        "sheet_height_mm",
        "part_id",
        "x_mm",
        "y_mm",
        "width_mm",
        "height_mm",
        "rotation_deg",
        "width_display",
        "height_display",
    ]

    try:
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(header)

            for sheet in sorted(export_job.sheets, key=lambda s: s.sheet_index):
                for part in sheet.parts:
                    width_display = format_dimension_for_export(
                        part.width_mm, export_job
                    )
                    height_display = format_dimension_for_export(
                        part.height_mm, export_job
                    )

                    writer.writerow(
                        [
                            sheet.sheet_index,
                            sheet.width_mm,
                            sheet.height_mm,
                            part.part_id,
                            part.x_mm,
                            part.y_mm,
                            part.width_mm,
                            part.height_mm,
                            part.rotation_deg,
                            width_display,
                            height_display,
                        ]
                    )

    except OSError as exc:
        logger.warning(f"[SquatchCut] CSV export failed for '{path}': {exc}")
        raise


def _export_enhanced_cutlist_csv(export_job: ExportJob, path: Path) -> None:
    """Export cutlist in enhanced woodshop-friendly format."""
    # Enhanced header with woodshop-friendly column names and shape-based info
    header = [
        "Sheet",
        "Sheet_Size",
        "Part_Name",
        "Width",
        "Height",
        "Actual_Area",
        "Geometry_Type",
        "Complexity",
        "Qty",
        "Rotated",
        "Position_From_Left",
        "Position_From_Bottom",
        "Cut_Instructions",
    ]

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

                    # Calculate actual area and complexity information
                    actual_area = _calculate_part_actual_area(part, export_job)
                    geometry_type = _get_geometry_type_display(part)
                    complexity_info = _get_complexity_display(part)

                    writer.writerow(
                        [
                            f"Sheet {sheet.sheet_index + 1}",
                            sheet_size_display,
                            part.part_id,
                            width_display,
                            height_display,
                            actual_area,
                            geometry_type,
                            complexity_info,
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
        logger.warning(f"[SquatchCut] CSV export failed for '{path}': {exc}")
        raise


def export_nesting_to_svg(
    export_job: ExportJob,
    base_path: str,
    *,
    include_labels: bool = True,
    include_dimensions: bool = False,
    include_cut_lines: bool = False,
    include_waste_areas: bool = False,
    include_leader_lines: bool = False,
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
            include_leader_lines=include_leader_lines,
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


def export_nesting_to_dxf(
    export_job: ExportJob,
    base_path: str,
    *,
    include_labels: bool = True,
    include_dimensions: bool = False,
    separate_kerf_layer: bool = True,
    precision_decimals: int = 3,
) -> list[Path]:
    """
    Export nesting layouts to DXF format with support for complex shapes.

    Args:
        export_job: The nesting job to export
        base_path: Base path for output files
        include_labels: Whether to include part labels
        include_dimensions: Whether to include dimension annotations
        separate_kerf_layer: Whether to put kerf-compensated geometry on separate layer
        precision_decimals: Number of decimal places for coordinates

    Returns:
        List of generated DXF file paths

    Raises:
        RuntimeError: If DXF export is not available
        OSError: If file writing fails
    """
    if export_job is None or not export_job.sheets:
        logger.warning("[SquatchCut] DXF export skipped: job has no sheets.")
        return []

    try:
        import importDXF  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"DXF export not available: {exc}") from exc

    # Ensure we have a valid FreeCAD document for temporary objects
    if App is None:
        raise RuntimeError("FreeCAD App module not available for DXF export")

    doc = App.newDocument("SquatchCut_DXF_Export")
    if doc is None:
        raise RuntimeError("Failed to create temporary FreeCAD document")

    try:
        base_target = Path(base_path)
        if base_target.suffix.lower() != ".dxf":
            base_target = base_target.with_suffix(".dxf")

        base_target.parent.mkdir(parents=True, exist_ok=True)

        generated_paths: list[Path] = []

        for idx, sheet in enumerate(
            sorted(export_job.sheets, key=lambda s: s.sheet_index)
        ):
            # Create DXF objects for this sheet
            objs = _build_dxf_objects_for_sheet(
                doc=doc,
                sheet=sheet,
                sheet_number=idx + 1,
                export_job=export_job,
                include_labels=include_labels,
                include_dimensions=include_dimensions,
                separate_kerf_layer=separate_kerf_layer,
                precision_decimals=precision_decimals,
            )

            # Generate sheet-specific file path
            target_path = _sheet_specific_path(base_target, idx + 1)
            target_path = target_path.with_suffix(".dxf")

            try:
                # Export to DXF
                importDXF.export(objs, str(target_path))
                generated_paths.append(target_path)
                logger.info(
                    f"[SquatchCut] DXF sheet {idx + 1} exported to {target_path}"
                )
            except OSError as exc:
                logger.warning(
                    f"[SquatchCut] DXF export failed for '{target_path}': {exc}"
                )
                raise
            finally:
                # Clean up temporary objects for this sheet
                for obj in objs:
                    try:
                        doc.removeObject(obj.Name)
                    except Exception:
                        pass

        logger.info(
            f"[SquatchCut] DXF export complete: {len(generated_paths)} file(s) generated"
        )
        return generated_paths

    finally:
        # Clean up temporary document
        try:
            App.closeDocument(doc.Name)
        except Exception:
            pass


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


def _build_dxf_objects_for_sheet(
    doc,
    sheet: ExportSheet,
    sheet_number: int,
    export_job: ExportJob,
    include_labels: bool,
    include_dimensions: bool,
    separate_kerf_layer: bool,
    precision_decimals: int,
) -> list:
    """
    Create FreeCAD objects for DXF export of a single sheet.

    Handles both rectangular and complex geometry parts with layer separation.
    """
    if Part is None:
        logger.warning("[SquatchCut] Part module not available for DXF export")
        return []

    objs = []

    # Create sheet boundary
    try:
        sheet_boundary = Part.makePlane(sheet.width_mm, sheet.height_mm)
        boundary_obj = doc.addObject("Part::Feature", f"Sheet_{sheet_number}_Boundary")
        boundary_obj.Shape = sheet_boundary
        boundary_obj.Label = f"Sheet {sheet_number} Boundary"
        objs.append(boundary_obj)
    except Exception as e:
        logger.warning(f"Failed to create sheet boundary: {e}")

    # Process each part
    for part_idx, part in enumerate(sheet.parts):
        try:
            part_objs = _create_dxf_objects_for_part(
                doc=doc,
                part=part,
                part_index=part_idx,
                sheet_number=sheet_number,
                export_job=export_job,
                include_labels=include_labels,
                include_dimensions=include_dimensions,
                separate_kerf_layer=separate_kerf_layer,
                precision_decimals=precision_decimals,
            )
            objs.extend(part_objs)
        except Exception as e:
            logger.warning(f"Failed to create DXF objects for part {part.part_id}: {e}")
            # Continue with other parts even if one fails

    return objs


def _create_dxf_objects_for_part(
    doc,
    part: ExportPartPlacement,
    part_index: int,
    sheet_number: int,
    export_job: ExportJob,
    include_labels: bool,
    include_dimensions: bool,
    separate_kerf_layer: bool,
    precision_decimals: int,
) -> list:
    """Create FreeCAD objects for a single part in DXF export."""
    objs = []

    # Determine if this is a complex geometry part
    has_complex_geometry = (
        hasattr(part, "complex_geometry")
        and part.complex_geometry is not None
        and part.complex_geometry.contour_points
        and len(part.complex_geometry.contour_points) >= 3
    )

    if has_complex_geometry:
        # Create complex geometry objects
        part_objs = _create_complex_geometry_dxf_objects(
            doc=doc,
            part=part,
            part_index=part_index,
            sheet_number=sheet_number,
            separate_kerf_layer=separate_kerf_layer,
            precision_decimals=precision_decimals,
        )
        objs.extend(part_objs)
    else:
        # Create rectangular geometry objects
        part_objs = _create_rectangular_dxf_objects(
            doc=doc,
            part=part,
            part_index=part_index,
            sheet_number=sheet_number,
            precision_decimals=precision_decimals,
        )
        objs.extend(part_objs)

    # Add labels if requested
    if include_labels:
        label_objs = _create_part_label_objects(
            doc=doc,
            part=part,
            part_index=part_index,
            sheet_number=sheet_number,
            export_job=export_job,
        )
        objs.extend(label_objs)

    # Add dimensions if requested
    if include_dimensions:
        dimension_objs = _create_part_dimension_objects(
            doc=doc,
            part=part,
            part_index=part_index,
            sheet_number=sheet_number,
            export_job=export_job,
        )
        objs.extend(dimension_objs)

    return objs


def _create_complex_geometry_dxf_objects(
    doc,
    part: ExportPartPlacement,
    part_index: int,
    sheet_number: int,
    separate_kerf_layer: bool,
    precision_decimals: int,
) -> list:
    """Create DXF objects for complex geometry parts."""
    objs = []

    try:
        geometry = part.complex_geometry

        # Round coordinates to specified precision
        def round_coord(coord):
            return round(coord, precision_decimals)

        # Create wire from contour points
        points = []
        for point in geometry.contour_points:
            # Apply part position offset
            x = round_coord(point[0] + part.x_mm)
            y = round_coord(point[1] + part.y_mm)
            points.append(App.Vector(x, y, 0.0))

        # Close the contour if not already closed
        if len(points) > 2 and points[0] != points[-1]:
            points.append(points[0])

        # Create edges from points
        edges = []
        for i in range(len(points) - 1):
            try:
                edge = Part.makeLine(points[i], points[i + 1])
                edges.append(edge)
            except Exception as e:
                logger.warning(
                    f"Failed to create edge {i} for part {part.part_id}: {e}"
                )

        if edges:
            # Create wire from edges
            try:
                wire = Part.Wire(edges)

                # Create main geometry object
                main_obj = doc.addObject(
                    "Part::Feature", f"Part_{sheet_number}_{part_index}_Main"
                )
                main_obj.Shape = wire
                main_obj.Label = f"{part.part_id}_Main"
                objs.append(main_obj)

                # Create kerf-compensated geometry if available and requested
                if (
                    separate_kerf_layer
                    and hasattr(part, "kerf_compensation")
                    and part.kerf_compensation is not None
                    and abs(part.kerf_compensation) > 0.001
                ):
                    try:
                        kerf_geometry = geometry.apply_kerf(part.kerf_compensation)
                        if kerf_geometry and kerf_geometry.contour_points:
                            # Create kerf-compensated wire
                            kerf_points = []
                            for point in kerf_geometry.contour_points:
                                x = round_coord(point[0] + part.x_mm)
                                y = round_coord(point[1] + part.y_mm)
                                kerf_points.append(App.Vector(x, y, 0.0))

                            if (
                                len(kerf_points) > 2
                                and kerf_points[0] != kerf_points[-1]
                            ):
                                kerf_points.append(kerf_points[0])

                            kerf_edges = []
                            for i in range(len(kerf_points) - 1):
                                try:
                                    edge = Part.makeLine(
                                        kerf_points[i], kerf_points[i + 1]
                                    )
                                    kerf_edges.append(edge)
                                except Exception:
                                    pass

                            if kerf_edges:
                                kerf_wire = Part.Wire(kerf_edges)
                                kerf_obj = doc.addObject(
                                    "Part::Feature",
                                    f"Part_{sheet_number}_{part_index}_Kerf",
                                )
                                kerf_obj.Shape = kerf_wire
                                kerf_obj.Label = f"{part.part_id}_Kerf"
                                objs.append(kerf_obj)

                    except Exception as e:
                        logger.warning(
                            f"Failed to create kerf geometry for part {part.part_id}: {e}"
                        )

            except Exception as e:
                logger.warning(f"Failed to create wire for part {part.part_id}: {e}")
                # Fallback to rectangular representation
                fallback_objs = _create_rectangular_dxf_objects(
                    doc, part, part_index, sheet_number, precision_decimals
                )
                objs.extend(fallback_objs)

    except Exception as e:
        logger.warning(
            f"Failed to process complex geometry for part {part.part_id}: {e}"
        )
        # Fallback to rectangular representation
        fallback_objs = _create_rectangular_dxf_objects(
            doc, part, part_index, sheet_number, precision_decimals
        )
        objs.extend(fallback_objs)

    return objs


def _create_rectangular_dxf_objects(
    doc,
    part: ExportPartPlacement,
    part_index: int,
    sheet_number: int,
    precision_decimals: int,
) -> list:
    """Create DXF objects for rectangular parts."""
    objs = []

    try:
        # Round coordinates to specified precision
        x = round(part.x_mm, precision_decimals)
        y = round(part.y_mm, precision_decimals)
        w = round(part.width_mm, precision_decimals)
        h = round(part.height_mm, precision_decimals)

        # Create rectangular plane
        plane = Part.makePlane(w, h)
        obj = doc.addObject("Part::Feature", f"Part_{sheet_number}_{part_index}")
        obj.Shape = plane
        obj.Label = part.part_id or f"Part_{part_index}"

        # Apply position and rotation
        placement = obj.Placement
        placement.Base.x = x
        placement.Base.y = y
        placement.Base.z = 0.0

        # Apply rotation if specified
        if part.rotation_deg != 0 and App:
            try:
                placement.Rotation = App.Rotation(
                    App.Vector(0, 0, 1), part.rotation_deg
                )
            except Exception as e:
                logger.warning(f"Failed to apply rotation to part {part.part_id}: {e}")

        obj.Placement = placement
        objs.append(obj)

    except Exception as e:
        logger.warning(
            f"Failed to create rectangular DXF object for part {part.part_id}: {e}"
        )

    return objs


def _create_part_label_objects(
    doc,
    part: ExportPartPlacement,
    part_index: int,
    sheet_number: int,
    export_job: ExportJob,
) -> list:
    """Create text label objects for parts in DXF export."""
    objs = []

    try:
        # Calculate label position (center of part)
        center_x = part.x_mm + part.width_mm / 2.0
        center_y = part.y_mm + part.height_mm / 2.0

        # Determine appropriate text size
        min_dim = min(part.width_mm, part.height_mm)
        text_size = max(min_dim * 0.1, 2.0)  # At least 2mm high

        # Create label text
        label_text = part.part_id or f"Part_{part_index}"

        # Use text helper if available
        text_obj = create_export_shape_text(
            doc, label_text, center_x, center_y, 0.0, size=text_size
        )

        if text_obj is not None:
            text_obj.Label = f"{part.part_id}_Label"
            objs.append(text_obj)

    except Exception as e:
        logger.warning(f"Failed to create label for part {part.part_id}: {e}")

    return objs


def _create_part_dimension_objects(
    doc,
    part: ExportPartPlacement,
    part_index: int,
    sheet_number: int,
    export_job: ExportJob,
) -> list:
    """Create dimension annotation objects for parts in DXF export."""
    objs = []

    try:
        # Calculate dimension positions
        margin = 3.0  # 3mm margin from part edge
        text_size = 1.5  # 1.5mm text height

        # Width dimension (below part)
        width_text = format_dimension_for_export(part.width_mm, export_job)
        width_x = part.x_mm + part.width_mm / 2.0
        width_y = part.y_mm - margin

        width_obj = create_export_shape_text(
            doc, f"W: {width_text}", width_x, width_y, 0.0, size=text_size
        )

        if width_obj is not None:
            width_obj.Label = f"{part.part_id}_Width"
            objs.append(width_obj)

        # Height dimension (right of part)
        height_text = format_dimension_for_export(part.height_mm, export_job)
        height_x = part.x_mm + part.width_mm + margin
        height_y = part.y_mm + part.height_mm / 2.0

        height_obj = create_export_shape_text(
            doc, f"H: {height_text}", height_x, height_y, 0.0, size=text_size
        )

        if height_obj is not None:
            height_obj.Label = f"{part.part_id}_Height"
            objs.append(height_obj)

    except Exception as e:
        logger.warning(f"Failed to create dimensions for part {part.part_id}: {e}")

    return objs
