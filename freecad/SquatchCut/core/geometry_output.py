"""@codex
Geometry helpers to turn SquatchCut nesting layouts into FreeCAD objects.
"""

from __future__ import annotations

import FreeCAD as App  # type: ignore
import FreeCADGui as Gui  # type: ignore

try:
    import Part  # type: ignore
except Exception:
    Part = None


def create_geometry_from_layout(doc, layout, base_name="SC_Sheet"):
    """
    Given a layout dict from nesting_engine.compute_layout, create
    one FreeCAD object per panel on each sheet.

    Args:
        doc: active FreeCAD document (App.ActiveDocument).
        layout: dict as returned by compute_layout(...)
        base_name: prefix used for sheet group labels.

    Behavior:
        - For each sheet in layout["sheets"], create a Group or Part
          container named f"{base_name}_{index}".
        - For each panel in sheet["panels"], create a thin box or wire
          rectangle at (x, y) with given width/height.
    """
    if doc is None:
        raise RuntimeError("No active FreeCAD document provided")

    sheets = layout.get("sheets", []) or []

    created = []

    for sheet in sheets:
        idx = sheet.get("index", 1)
        group_name = f"{base_name}_{idx}"
        sheet_group = doc.addObject("App::DocumentObjectGroup", group_name)

        for panel in sheet.get("panels", []):
            w = float(panel.get("width", 0))
            h = float(panel.get("height", 0))
            x = float(panel.get("x", 0))
            y = float(panel.get("y", 0))

            if w <= 0 or h <= 0:
                continue

            name = f"SC_Panel_{panel.get('id', 0)}"
            if Part:
                # Simple thin box; Z is small for visibility
                box = doc.addObject("Part::Box", name)
                box.Width = w
                box.Length = h
                box.Height = 1.0
                # Move so that the rectangle starts at (x, y) in X-Y plane
                box.Placement.Base = App.Vector(x, y, 0)
                sheet_group.addObject(box)
                created.append(box)
            else:
                # Fallback: just create an empty group member name
                dummy = doc.addObject("App::FeaturePython", name)
                sheet_group.addObject(dummy)
                created.append(dummy)

    doc.recompute()
    return created
