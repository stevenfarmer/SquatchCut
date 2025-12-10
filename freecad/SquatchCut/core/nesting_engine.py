"""@codex
Module: Single-sheet rectangular nesting engine for SquatchCut.
Boundaries: Do not handle multi-sheet allocation, CSV I/O, or geometry output; focus only on placing panels within one sheet.
Primary methods: place_panels, _init_state, _place_panel, _finalize_placements.
Note: Update incrementally; do not overwrite this module when adding logic.
"""

from __future__ import annotations


class NestingEngine:
    """Places panels on a single sheet using rectangular nesting."""

    def place_panels(self, panels: list[dict], sheet_size: dict) -> list[dict]:
        """Compute placements for a single sheet and return placement objects."""
        width = sheet_size.get("width") if isinstance(sheet_size, dict) else None
        height = sheet_size.get("height") if isinstance(sheet_size, dict) else None
        if width is None or height is None:
            raise ValueError("sheet_size must include width and height")
        placements, _ = self.nest_panels(panels, float(width), float(height))
        return placements

    def _init_state(self, sheet_size: dict):
        """Initialize internal structures for skyline/guillotine placement."""
        width = sheet_size.get("width")
        height = sheet_size.get("height")
        free_rectangles = [
            {"x": 0.0, "y": 0.0, "width": float(width), "height": float(height)}
        ]
        return free_rectangles

    def _place_panel(self, panel: dict):
        """Attempt to place a single panel on the current sheet."""
        # Deprecated: use nest_panels directly.
        return None

    def _finalize_placements(self):
        """Return finalized placements after processing all panels."""
        return []

    # New MVP implementation
    def nest_panels(
        self, panels: list[dict], sheet_width: float, sheet_height: float
    ) -> tuple[list[dict], list[dict]]:
        """Simple skyline/guillotine-style nesting for one sheet."""
        free_rectangles = [
            {"x": 0.0, "y": 0.0, "width": float(sheet_width), "height": float(sheet_height)}
        ]
        placements: list[dict] = []
        remaining: list[dict] = []

        sorted_panels = sorted(
            panels, key=lambda p: max(float(p.get("width", 0)), float(p.get("height", 0))), reverse=True
        )

        for panel in sorted_panels:
            placed = self.place_panel(panel, free_rectangles)
            if placed:
                placements.append(placed)
            else:
                remaining.append(panel)

        return placements, remaining

    def place_panel(self, panel: dict, free_rectangles: list[dict]) -> dict | None:
        """Place a panel into the first fitting rectangle, updating free space."""
        width = float(panel.get("width", 0))
        height = float(panel.get("height", 0))
        rotation_allowed = bool(panel.get("rotation_allowed", True))

        candidates = []
        pos0 = self.find_position_for_panel(width, height, free_rectangles)
        if pos0:
            candidates.append((pos0, 0, width, height))
        if rotation_allowed:
            pos90 = self.find_position_for_panel(height, width, free_rectangles)
            if pos90:
                candidates.append((pos90, 90, height, width))

        if not candidates:
            return None

        # Choose the candidate that leaves the smallest rectangle area
        best = min(
            candidates,
            key=lambda c: free_rectangles[c[0][2]]["width"] * free_rectangles[c[0][2]]["height"],
        )
        (x, y, rect_index), rotation, used_w, used_h = best
        rect = free_rectangles.pop(rect_index)
        # Split remaining space: right and top
        right_w = rect["width"] - used_w
        top_h = rect["height"] - used_h

        if right_w > 0:
            free_rectangles.append(
                {"x": rect["x"] + used_w, "y": rect["y"], "width": right_w, "height": rect["height"]}
            )
        if top_h > 0:
            free_rectangles.append(
                {"x": rect["x"], "y": rect["y"] + used_h, "width": rect["width"], "height": top_h}
            )

        return {
            "panel_id": panel.get("id"),
            "x": x,
            "y": y,
            "rotation": rotation,
            "width": used_w,
            "height": used_h,
        }

    def find_position_for_panel(
        self, width: float, height: float, free_rectangles: list[dict]
    ) -> tuple[float, float, int] | None:
        """Find the first rectangle that fits the panel; return (x, y, index)."""
        best_index = None
        best = None
        for idx, rect in enumerate(free_rectangles):
            if rect["width"] >= width and rect["height"] >= height:
                area = rect["width"] * rect["height"]
                if best is None or area < best:
                    best = area
                    best_index = idx
        if best_index is None:
            return None
        rect = free_rectangles[best_index]
        return rect["x"], rect["y"], best_index


def compute_layout(panels, sheet_width, sheet_height, kerf=0.0, allow_rotation=True, max_sheets=50):
    """
    Compute a simple shelf-style layout for the provided panels.
    """
    sw = float(sheet_width)
    sh = float(sheet_height)
    k = float(kerf) if kerf is not None else 0.0
    k = max(k, 0.0)
    margin = k  # treat kerf as both spacing and edge margin

    if sw <= 0 or sh <= 0:
        return {"sheet_width": sw, "sheet_height": sh, "kerf": k, "sheets": []}

    normalized = []
    panel_id = 1
    for _idx, p in enumerate(panels or []):
        try:
            w = float(p.get("width"))
            h = float(p.get("height"))
        except Exception:
            continue

        if w <= 0 or h <= 0:
            continue

        qty = int(p.get("qty", 1) or 1)
        if qty <= 0:
            continue

        label = p.get("label")
        material = p.get("material")

        for _ in range(qty):
            normalized.append(
                {
                    "id": panel_id,
                    "width": w,
                    "height": h,
                    "label": label,
                    "material": material,
                }
            )
            panel_id += 1

    # Sort by height then width descending for more predictable packing
    normalized.sort(key=lambda item: (item["height"], item["width"]), reverse=True)

    usable_w = sw - 2 * margin
    usable_h = sh - 2 * margin
    if usable_w <= 0 or usable_h <= 0:
        return {"sheet_width": sw, "sheet_height": sh, "kerf": k, "sheets": []}

    x = 0.0
    y = 0.0
    row_height = 0.0

    placements = []

    for p in normalized:
        w = p["width"]
        h = p["height"]

        if w > usable_w or h > usable_h:
            continue

        if x + w > usable_w:
            x = 0.0
            y += row_height + k
            row_height = 0.0

        if y + h > usable_h:
            break

        placements.append(
            {
                "id": p["id"],
                "x": margin + x,
                "y": margin + y,
                "width": w,
                "height": h,
                "rotation": 0,
                "label": p.get("label"),
                "material": p.get("material"),
            }
        )

        x += w + k
        row_height = max(row_height, h)

    sheets = []
    if placements:
        sheets.append({"index": 1, "panels": placements})

    return {
        "sheet_width": sw,
        "sheet_height": sh,
        "kerf": k,
        "sheets": sheets,
    }
