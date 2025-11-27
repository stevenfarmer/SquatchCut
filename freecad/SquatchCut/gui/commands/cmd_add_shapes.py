"""FreeCAD command to add selected document shapes as nesting panels."""

from __future__ import annotations

"""@codex
Command: Trigger the Select Shapes dialog to collect panels from the active document.
Interactions: Should open SC_SelectShapesDialog and forward selections to core shape_extractor logic.
Note: Preserve FreeCAD command structure (GetResources, Activated, IsActive).
"""

# Qt bindings (FreeCAD ships PySide / PySide2, not PySide6)
try:
    from PySide import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets

import os

import FreeCAD as App
import FreeCADGui as Gui
import Part

from SquatchCut.core import session_state


ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # .../freecad/SquatchCut
    "resources",
    "icons",
)


class AddShapesCommand:
    """Create rectangular shapes for each loaded panel in the current document."""

    def GetResources(self):
        return {
            "MenuText": "Add Shapes",
            "ToolTip": "Create rectangle shapes for all loaded CSV panels.",
            "Pixmap": os.path.join(ICONS_DIR, "add_shapes.svg"),
        }

    def Activated(self):
        panels = session_state.get_panels()
        if not panels:
            App.Console.PrintError("[SquatchCut] No panels loaded. Import CSV first.\n")
            QtWidgets.QMessageBox.warning(
                None, "SquatchCut", "No panels loaded. Import CSV first."
            )
            return

        doc = App.ActiveDocument
        if doc is None:
            doc = App.newDocument("SquatchCut")

        shapes_per_row = 5
        count = 0

        for panel in panels:
            width = float(panel.get("width", 0) or 0)
            height = float(panel.get("height", 0) or 0)
            qty = int(panel.get("qty", 1) or 1)
            label = (panel.get("label") or "Panel").strip() or "Panel"

            for _ in range(qty):
                # Skip invalid dimensions
                if width <= 0 or height <= 0:
                    App.Console.PrintError(
                        f"[SquatchCut] Skipping panel with non-positive size: "
                        f"width={width}, height={height}\n"
                    )
                    continue

                # Build a rectangular face in the XY plane from (0,0) to (width, height)
                p0 = App.Vector(0, 0, 0)
                p1 = App.Vector(width, 0, 0)
                p2 = App.Vector(width, height, 0)
                p3 = App.Vector(0, height, 0)

                poly = Part.makePolygon([p0, p1, p2, p3, p0])
                face = Part.Face(poly)

                obj_name = f"{label}_{count + 1}"
                obj = doc.addObject("Part::Feature", obj_name)
                obj.Shape = face

                # Optional rotation flag from CSV panels
                allow_rotate = bool(panel.get("allow_rotate", False))
                try:
                    if not hasattr(obj, "SquatchCutCanRotate"):
                        obj.addProperty(
                            "App::PropertyBool",
                            "SquatchCutCanRotate",
                            "SquatchCut",
                            "Whether this panel may be rotated 90 degrees during nesting",
                        )
                    obj.SquatchCutCanRotate = allow_rotate
                except Exception:
                    pass

                # Tag this object so other commands (e.g. RunNesting) can find it
                try:
                    if not hasattr(obj, "SquatchCutPanel"):
                        obj.addProperty(
                            "App::PropertyBool",
                            "SquatchCutPanel",
                            "SquatchCut",
                            "True if this object is a panel created by SquatchCut.",
                        )
                    obj.SquatchCutPanel = True
                except Exception:
                    # Property creation is non-critical; fail silently if needed
                    pass

                # Give it a stable, human-friendly label
                try:
                    obj.Label = f"SquatchCut Panel {count + 1}"
                except Exception:
                    pass

                col = count % shapes_per_row
                row = count // shapes_per_row
                x_offset = col * (width + 5)
                y_offset = row * (height + 5)
                obj.Placement.Base = App.Vector(x_offset, y_offset, 0)

                count += 1

        App.Console.PrintMessage(f"[SquatchCut] Added {count} shapes to document.\n")
        App.Console.PrintMessage(
            f"[SquatchCut] AddShapesCommand created {count} shapes in the document.\n"
        )

        # Auto-fit view so newly created shapes are visible without manual zoom
        if count > 0:
            try:
                Gui.SendMsgToActiveView("ViewFit")
            except Exception:
                pass

    def IsActive(self):
        return True


COMMAND = AddShapesCommand()
