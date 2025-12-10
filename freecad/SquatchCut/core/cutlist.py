from __future__ import annotations

from dataclasses import dataclass

from SquatchCut.core import logger, session, session_state
from SquatchCut.freecad_integration import App


@dataclass
class CutOp:
    sheet_index: int
    sheet_name: str
    orientation: str  # "vertical" or "horizontal"
    position_mm: float
    length_mm: float


def _merge_edges(edges, tol=4.0):
    """
    Given a sorted list of edge positions (floats), merge edges that are
    closer together than 'tol' mm. This reduces double cuts like 500 and 503.
    """
    if not edges:
        return []

    merged = [edges[0]]
    for x in edges[1:]:
        if abs(x - merged[-1]) < tol:
            continue
        merged.append(x)
    return merged


def _filter_edges_by_panels(edges, panels, axis, span_min, span_max):
    """
    Keep only those edges that actually intersect at least one panel
    across the relevant span.

    axis: "x" or "y"
    span_min/span_max: the sheet's span in the other axis (for overlap check).
    """
    filtered = []
    for edge in edges:
        has_crossing = False
        for p in panels:
            try:
                bb = p.Shape.BoundBox
            except Exception:
                continue

            if axis == "x":
                p_min = bb.XMin
                p_max = bb.XMax
                other_min = bb.YMin
                other_max = bb.YMax
            else:
                p_min = bb.YMin
                p_max = bb.YMax
                other_min = bb.XMin
                other_max = bb.XMax

            if not (p_min < edge < p_max):
                continue

            if other_max <= span_min or other_min >= span_max:
                continue

            has_crossing = True
            break

        if has_crossing:
            filtered.append(edge)

    return filtered


def _get_sheet_bounds(sheet_obj):
    """Return (min_x, max_x, min_y, max_y) for the given sheet shape."""
    bb = sheet_obj.Shape.BoundBox
    return bb.XMin, bb.XMax, bb.YMin, bb.YMax


def _get_panel_bounds(panel_obj):
    """Return (min_x, max_x, min_y, max_y) for the given nested panel shape."""
    bb = panel_obj.Shape.BoundBox
    return bb.XMin, bb.XMax, bb.YMin, bb.YMax


def generate_cutops_from_session() -> list[CutOp]:
    """
    Inspect the current SquatchCut nesting in the active document and
    derive a simple list of cut operations.
    """
    if App is None:
        logger.warning("cutlist.generate_cutops_from_session(): FreeCAD not available.")
        return []

    doc = App.ActiveDocument
    if doc is None:
        logger.warning("cutlist.generate_cutops_from_session(): no active document.")
        return []

    try:
        sheet_objs = session.get_sheet_objects()
    except Exception:
        logger.warning("cutlist: session.get_sheet_objects() not available or failed.")
        sheet_objs = []

    try:
        panel_objs = session.get_nested_panel_objects()
    except Exception:
        logger.warning("cutlist: session.get_nested_panel_objects() not available or failed.")
        panel_objs = []

    cut_ops: list[CutOp] = []

    if sheet_objs and panel_objs:
        for sheet_index, sheet_obj in enumerate(sheet_objs, start=1):
            try:
                s_min_x, s_max_x, s_min_y, s_max_y = _get_sheet_bounds(sheet_obj)
            except Exception as e:
                logger.warning(f"cutlist: failed to get bounds for sheet {getattr(sheet_obj, 'Name', '?')}: {e!r}")
                continue

            x_edges = [s_min_x, s_max_x]
            y_edges = [s_min_y, s_max_y]
            sheet_panels = []

            for p in panel_objs:
                try:
                    p_min_x, p_max_x, p_min_y, p_max_y = _get_panel_bounds(p)
                except Exception:
                    continue

                # Simple overlap check in XY
                if p_max_x <= s_min_x or p_min_x >= s_max_x:
                    continue
                if p_max_y <= s_min_y or p_min_y >= s_max_y:
                    continue

                x_edges.extend([p_min_x, p_max_x])
                y_edges.extend([p_min_y, p_max_y])
                sheet_panels.append(p)

            if not sheet_panels:
                continue

            x_edges = sorted(set(x_edges))
            y_edges = sorted(set(y_edges))

            x_edges = _merge_edges(x_edges, tol=4.0)
            y_edges = _merge_edges(y_edges, tol=4.0)

            interior_x = [x for x in x_edges if s_min_x < x < s_max_x]
            interior_y = [y for y in y_edges if s_min_y < y < s_max_y]

            interior_x = _filter_edges_by_panels(interior_x, sheet_panels, "x", s_min_y, s_max_y)
            interior_y = _filter_edges_by_panels(interior_y, sheet_panels, "y", s_min_x, s_max_x)

            sheet_height = s_max_y - s_min_y
            for x in interior_x:
                cut_ops.append(
                    CutOp(
                        sheet_index=sheet_index,
                        sheet_name=getattr(sheet_obj, "Name", f"Sheet_{sheet_index}"),
                        orientation="vertical",
                        position_mm=float(x),
                        length_mm=float(sheet_height),
                    )
                )

            sheet_width = s_max_x - s_min_x
            for y in interior_y:
                cut_ops.append(
                    CutOp(
                        sheet_index=sheet_index,
                        sheet_name=getattr(sheet_obj, "Name", f"Sheet_{sheet_index}"),
                        orientation="horizontal",
                        position_mm=float(y),
                        length_mm=float(sheet_width),
                    )
                )

    # If geometry-based calculation produced nothing, fall back to placement-based map
    if not cut_ops:
        try:
            placements = session_state.get_last_layout()
        except Exception:
            placements = None

        if placements:
            try:
                sheet_w, sheet_h = session_state.get_sheet_size()
            except Exception:
                sheet_w = sheet_h = 0.0
            return _cutops_from_cutlist_map(generate_cutlist(placements, (sheet_w, sheet_h)))

        logger.info("cutlist: no sheets or nested panels; nothing to cut.")
        return []

    cut_ops.sort(key=lambda c: (c.sheet_index, c.orientation, c.position_mm))
    return cut_ops


def export_cutops_to_csv(path: str, cut_ops: list[CutOp]):
    """Write the given cut operations to a CSV file at 'path'."""
    import csv

    if not cut_ops:
        logger.warning("cutlist.export_cutops_to_csv(): no cuts to export.")
        return

    try:
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["sheet_index", "sheet_name", "orientation", "position_mm", "length_mm"])
            for c in cut_ops:
                writer.writerow(
                    [c.sheet_index, c.sheet_name, c.orientation, f"{c.position_mm:.3f}", f"{c.length_mm:.3f}"]
                )
        logger.info(f"[SquatchCut] Cutlist exported to: {path}")
    except Exception as e:
        logger.error(f"cutlist.export_cutops_to_csv() failed: {e!r}")


# ---------------------------------------------------------------------------
# Legacy-style cutlist generator (placements -> cut map) to keep existing
# exports and tests working. This operates purely on placement geometry and
# does not depend on FreeCAD.
# ---------------------------------------------------------------------------
def generate_cutlist(placements, sheet_size_mm):
    """
    Build a simple cutlist map from rectangular placements.

    Returns a dict: sheet_index -> list of cuts, where each cut is a dict with
    keys expected by existing exporter helpers/tests.
    """
    try:
        sheet_w, sheet_h = sheet_size_mm
    except Exception:
        sheet_w = sheet_h = 0.0

    # Group placements by sheet
    placements_by_sheet = {}
    for p in placements or []:
        idx = int(getattr(p, "sheet_index", 0) or 0)
        placements_by_sheet.setdefault(idx, []).append(p)

    cutlist_by_sheet = {}

    for sheet_idx, sheet_parts in placements_by_sheet.items():
        x_edges = {0.0, float(sheet_w)}
        y_edges = {0.0, float(sheet_h)}

        for p in sheet_parts:
            try:
                x = float(getattr(p, "x", 0.0))
                y = float(getattr(p, "y", 0.0))
                w = float(getattr(p, "width", 0.0))
                h = float(getattr(p, "height", 0.0))
            except Exception:
                continue
            x_edges.update({x, x + w})
            y_edges.update({y, y + h})

        interior_x = sorted([x for x in x_edges if 0.0 < x < float(sheet_w)])
        interior_y = sorted([y for y in y_edges if 0.0 < y < float(sheet_h)])

        cuts = []
        order = 1

        # Vertical cuts (RIP) along X edges
        for x in interior_x:
            affected = []
            for p in sheet_parts:
                try:
                    px = float(getattr(p, "x", 0.0))
                    pw = float(getattr(p, "width", 0.0))
                    pid = getattr(p, "id", getattr(p, "label", ""))
                except Exception:
                    continue
                if px < x < px + pw:
                    affected.append(pid)

            cuts.append(
                {
                    "sheet_index": sheet_idx,
                    "cut_order": order,
                    "cut_type": "RIP",
                    "cut_direction": "X",
                    "from_edge": "LEFT",
                    "distance_from_edge_mm": float(x),
                    "cut_length_mm": float(sheet_h),
                    "parts_affected": affected,
                    "notes": "",
                }
            )
            order += 1

        # Horizontal cuts (CROSSCUT) along Y edges
        for y in interior_y:
            affected = []
            for p in sheet_parts:
                try:
                    py = float(getattr(p, "y", 0.0))
                    ph = float(getattr(p, "height", 0.0))
                    pid = getattr(p, "id", getattr(p, "label", ""))
                except Exception:
                    continue
                if py < y < py + ph:
                    affected.append(pid)

            cuts.append(
                {
                    "sheet_index": sheet_idx,
                    "cut_order": order,
                    "cut_type": "CROSSCUT",
                    "cut_direction": "Y",
                    "from_edge": "BOTTOM",
                    "distance_from_edge_mm": float(y),
                    "cut_length_mm": float(sheet_w),
                    "parts_affected": affected,
                    "notes": "",
                }
            )
            order += 1

        cutlist_by_sheet[sheet_idx] = cuts

    return cutlist_by_sheet


def _cutops_from_cutlist_map(cutlist_map: dict) -> list[CutOp]:
    """Convert legacy cutlist map format into CutOp entries."""
    cut_ops: list[CutOp] = []
    for sheet_idx in sorted(cutlist_map.keys()):
        sheet_name = f"Sheet_{sheet_idx + 1}"
        for cut in cutlist_map.get(sheet_idx, []):
            try:
                orientation = "vertical"
                direction = cut.get("cut_direction", "")
                cut_type = cut.get("cut_type", "")
                if direction.upper() == "Y" or cut_type.upper() == "CROSSCUT":
                    orientation = "horizontal"
                position = float(cut.get("distance_from_edge_mm", 0.0))
                length = float(cut.get("cut_length_mm", 0.0))
            except Exception:
                continue

            cut_ops.append(
                CutOp(
                    sheet_index=sheet_idx + 1,
                    sheet_name=sheet_name,
                    orientation=orientation,
                    position_mm=position,
                    length_mm=length,
                )
            )

    cut_ops.sort(key=lambda c: (c.sheet_index, c.orientation, c.position_mm))
    return cut_ops
