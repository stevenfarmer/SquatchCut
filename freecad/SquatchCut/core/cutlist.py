"""Cutlist generation from placements for SquatchCut."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List


def _dedup_sorted(values: Iterable[float], epsilon: float) -> List[float]:
    uniq: List[float] = []
    for v in sorted(values):
        if not uniq or abs(v - uniq[-1]) > epsilon:
            uniq.append(v)
    return uniq


def generate_cutlist(placements, sheet_size_mm: tuple[float, float], epsilon: float = 1e-6) -> Dict[int, List[dict]]:
    """Generate a simple guillotine-style cutlist from placements."""
    sheet_w, sheet_h = sheet_size_mm
    by_sheet = defaultdict(list)
    for p in placements or []:
        by_sheet[getattr(p, "sheet_index", 0)].append(p)

    cutlists: Dict[int, List[dict]] = {}

    for sheet_index, plist in by_sheet.items():
        if not plist:
            continue

        # Collect candidate cut positions from part edges
        x_positions = []
        y_positions = []
        for p in plist:
            try:
                x_positions.extend([float(p.x), float(p.x) + float(p.width)])
                y_positions.extend([float(p.y), float(p.y) + float(p.height)])
            except Exception:
                continue

        x_positions = _dedup_sorted(x_positions, epsilon)
        y_positions = _dedup_sorted(y_positions, epsilon)

        cuts: List[dict] = []

        # Vertical cuts (rips) left -> right (skip outer edges)
        for x_cut in x_positions[1:-1]:
            if x_cut <= epsilon or x_cut >= sheet_w - epsilon:
                continue
            cuts.append(
                {
                    "sheet_index": sheet_index,
                    "cut_type": "RIP",
                    "cut_direction": "X",
                    "from_edge": "LEFT",
                    "distance_from_edge_mm": x_cut,
                    "cut_length_mm": sheet_h,
                    "parts_affected": [],
                    "notes": "",
                }
            )

        # Horizontal cuts (crosscuts) bottom -> top (skip outer edges)
        for y_cut in y_positions[1:-1]:
            if y_cut <= epsilon or y_cut >= sheet_h - epsilon:
                continue
            cuts.append(
                {
                    "sheet_index": sheet_index,
                    "cut_type": "CROSSCUT",
                    "cut_direction": "Y",
                    "from_edge": "BOTTOM",
                    "distance_from_edge_mm": y_cut,
                    "cut_length_mm": sheet_w,
                    "parts_affected": [],
                    "notes": "",
                }
            )

        # Order: all rips then crosscuts
        cuts_sorted = [c for c in cuts if c["cut_type"] == "RIP"]
        cuts_sorted.extend([c for c in cuts if c["cut_type"] == "CROSSCUT"])
        for idx, c in enumerate(cuts_sorted, start=1):
            c["cut_order"] = idx

        # Map cuts that intersect each part; last intersecting cut releases part
        for p in plist:
            pid = getattr(p, "id", None) or getattr(p, "label", None) or ""
            px1 = float(getattr(p, "x", 0.0))
            px2 = px1 + float(getattr(p, "width", 0.0))
            py1 = float(getattr(p, "y", 0.0))
            py2 = py1 + float(getattr(p, "height", 0.0))

            intersecting_orders: List[int] = []
            for c in cuts_sorted:
                if c["cut_direction"] == "X":
                    x_cut = c["distance_from_edge_mm"]
                    if px1 + epsilon < x_cut < px2 - epsilon:
                        intersecting_orders.append(c["cut_order"])
                else:
                    y_cut = c["distance_from_edge_mm"]
                    if py1 + epsilon < y_cut < py2 - epsilon:
                        intersecting_orders.append(c["cut_order"])

            if intersecting_orders:
                release_order = max(intersecting_orders)
                for c in cuts_sorted:
                    if c["cut_order"] == release_order:
                        c["parts_affected"].append(pid)

        cutlists[sheet_index] = cuts_sorted

    return cutlists
