"""Export helpers for SquatchCut nesting layouts (DXF, SVG, cut list CSV)."""

from __future__ import annotations

import csv
from typing import Iterable, Sequence


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


def _build_rectangles(doc, placements: Iterable, sheet_w: float, sheet_h: float):
    """Create temporary rectangles in the doc for export; returns list of objects."""
    try:
        import Part  # type: ignore
    except Exception:
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
        try:
            import FreeCAD  # type: ignore

            placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), rotation)
        except Exception:
            pass
        obj.Placement = placement
        objs.append(obj)
    return objs


def export_layout_to_dxf(placements: Sequence, sheet_size_mm: tuple[float, float], doc, file_path: str) -> None:
    """Export placements to DXF using temporary geometry."""
    try:
        import importDXF  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"DXF export not available: {exc}") from exc

    sheet_w, sheet_h = sheet_size_mm
    objs = _build_rectangles(doc, placements, sheet_w, sheet_h)
    try:
        importDXF.export(objs, file_path)
    finally:
        for obj in objs:
            try:
                doc.removeObject(obj.Name)
            except Exception:
                pass


def export_layout_to_svg(placements: Sequence, sheet_size_mm: tuple[float, float], doc, file_path: str) -> None:
    """Export placements to SVG using temporary geometry."""
    try:
        import importSVG  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"SVG export not available: {exc}") from exc

    sheet_w, sheet_h = sheet_size_mm
    objs = _build_rectangles(doc, placements, sheet_w, sheet_h)
    try:
        importSVG.export(objs, file_path)
    finally:
        for obj in objs:
            try:
                doc.removeObject(obj.Name)
            except Exception:
                pass
