"""Export helpers for SquatchCut nesting layouts (DXF, SVG, cut list CSV)."""

from __future__ import annotations

import csv
from typing import Dict, Iterable, Sequence

from SquatchCut.freecad_integration import App, Draft, Part
from SquatchCut.core.cutlist import generate_cutlist


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
    if Part is None or Draft is None:
        return []

    objs = []
    sheet_spacing = sheet_w * 0.25 if sheet_w else 0.0
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
            try:
                tx = x + w / 2.0 + sheet_index * (sheet_w + sheet_spacing)
                ty = y + h / 2.0
                txt = Draft.makeText([str(label)], point=(tx, ty, 0))
                objs.append(txt)
            except Exception:
                pass

        # Optional simple dimensions (text only near edges)
        if include_dimensions:
            margin = 5.0
            try:
                tx = x + w / 2.0 + sheet_index * (sheet_w + sheet_spacing)
                ty = y - margin
                tw = Draft.makeText([f"W: {w:.1f} mm"], point=(tx, ty, 0))
                objs.append(tw)
            except Exception:
                pass
            try:
                tx = x + w + margin + sheet_index * (sheet_w + sheet_spacing)
                ty = y + h / 2.0
                th = Draft.makeText([f"H: {h:.1f} mm"], point=(tx, ty, 0))
                objs.append(th)
            except Exception:
                pass
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
    objs = _build_rectangles(
        doc,
        placements,
        sheet_w,
        sheet_h,
        include_labels=include_labels,
        include_dimensions=include_dimensions,
    )
    try:
        importDXF.export(objs, file_path)
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
    include_labels: bool = True,
    include_dimensions: bool = False,
) -> None:
    """Export placements to SVG using temporary geometry."""
    try:
        import importSVG  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"SVG export not available: {exc}") from exc

    sheet_w, sheet_h = sheet_size_mm
    objs = _build_rectangles(
        doc,
        placements,
        sheet_w,
        sheet_h,
        include_labels=include_labels,
        include_dimensions=include_dimensions,
    )
    try:
        importSVG.export(objs, file_path)
    finally:
        for obj in objs:
            try:
                doc.removeObject(obj.Name)
            except Exception:
                pass
