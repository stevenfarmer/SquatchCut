"""@codex
FreeCAD command to run the SquatchCut nesting engine and create geometry.
"""

import traceback

import FreeCAD as App  # type: ignore
import FreeCADGui as Gui  # type: ignore

# Geometry
try:
    import Part  # type: ignore
except Exception:
    Part = None

# Qt imports (for message boxes)
try:
    from PySide import QtWidgets, QtCore, QtGui  # type: ignore
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui  # type: ignore

try:
    from SquatchCut.core import session_state as ss, nesting as nesting_core  # type: ignore
except Exception:
    import SquatchCut.core.session_state as ss  # type: ignore
    import SquatchCut.core.nesting as nesting_core  # type: ignore


class RunNestingCommand:
    """
    SquatchCut - Run Nesting command.

    Uses:
        - session_state.SESSION.panels
        - session_state.SESSION.sheet_width / sheet_height / sheet_units

    Steps:
        1) Validate prerequisites.
        2) Call nesting_engine.compute_layout(...).
        3) Create geometry via geometry_output.create_geometry_from_layout(...).
        4) Store layout in SESSION.last_layout (if available).
    """

    def GetResources(self):
        return {
            "MenuText": "Run Nesting",
            "ToolTip": "Run the nesting engine and generate sheet geometry.",
            "Pixmap": "SquatchCut_RunNesting",
        }

    def Activated(self):
        App.Console.PrintMessage(
            ">>> [SquatchCut] RunNestingCommand.Activated() entered\n"
        )

        try:
            sess = ss.SESSION

            panels = getattr(sess, "panels", None)
            if not panels:
                App.Console.PrintMessage(
                    ">>> [SquatchCut] RunNesting: no panels loaded in session\n"
                )
                return

            sheet_w = getattr(sess, "sheet_width", 0)
            sheet_h = getattr(sess, "sheet_height", 0)
            if not sheet_w or not sheet_h:
                App.Console.PrintMessage(
                    ">>> [SquatchCut] RunNesting: sheet size not defined in session\n"
                )
                return

            placements = nesting_core.run_shelf_nesting(
                sheet_width=sheet_w,
                sheet_height=sheet_h,
                panels=panels,
                margin=5.0,
            )

            if not placements:
                App.Console.PrintMessage(
                    ">>> [SquatchCut] RunNesting: no placements generated\n"
                )
                return

            doc = App.ActiveDocument
            if doc is None:
                App.Console.PrintMessage(">>> [SquatchCut] RunNesting: no active document\n")
                return

            # Collect all SquatchCut panel objects from the active document
            panel_objs = []
            for obj in doc.Objects:
                try:
                    if hasattr(obj, "SquatchCutPanel") and bool(obj.SquatchCutPanel):
                        panel_objs.append(obj)
                except Exception:
                    continue

            num_panels = len(panel_objs)
            num_places = len(placements)

            App.Console.PrintMessage(
                f">>> [SquatchCut] RunNesting: placements={num_places}, panels={num_panels}\n"
            )

            if num_panels == 0 or num_places == 0:
                App.Console.PrintMessage(
                    ">>> [SquatchCut] RunNesting: nothing to place (no panels or no placements)\n"
                )
                return

            # Sort panels by Name so placement order is stable
            panel_objs.sort(key=lambda o: o.Name)

            count = min(num_panels, num_places)

            placed_objs = []

            # Apply ABSOLUTE placements to each panel
            for i in range(count):
                obj = panel_objs[i]
                place = placements[i]

                x = float(place.get("x", 0.0))
                y = float(place.get("y", 0.0))

                base_vec = App.Vector(x, y, 0.0)
                rotation = App.Rotation(0.0, 0.0, 0.0)
                obj.Placement = App.Placement(base_vec, rotation)
                placed_objs.append(obj)

            # Remove existing sheet outline
            for obj in list(doc.Objects):
                if getattr(obj, "Label", "") == "SquatchCut_Sheet":
                    try:
                        doc.removeObject(obj.Name)
                    except Exception:
                        pass

            if Part is not None:
                p0 = App.Vector(0, 0, 0)
                p1 = App.Vector(sheet_w, 0, 0)
                p2 = App.Vector(sheet_w, sheet_h, 0)
                p3 = App.Vector(0, sheet_h, 0)
                wire = Part.makePolygon([p0, p1, p2, p3, p0])
                face = Part.Face(wire)
                sheet_obj = doc.addObject("Part::Feature", "SquatchCut_Sheet")
                sheet_obj.Label = "SquatchCut_Sheet"
                sheet_obj.Shape = face

            # Visually highlight placed panels so the user can see them clearly
            if placed_objs:
                App.Console.PrintMessage(
                    f">>> [SquatchCut] RunNesting: highlighting {len(placed_objs)} placed panels\n"
                )

            for pobj in placed_objs:
                try:
                    vobj = getattr(pobj, "ViewObject", None)
                    if vobj is None:
                        continue

                    # Loud magenta-ish color so it stands out
                    highlight_line = (1.0, 0.0, 1.0)
                    highlight_face = (1.0, 0.6, 1.0)

                    # Set basic colors
                    if hasattr(vobj, "LineColor"):
                        vobj.LineColor = highlight_line
                    if hasattr(vobj, "ShapeColor"):
                        vobj.ShapeColor = highlight_face

                    # If DiffuseColor exists (some Part::Feature types),
                    # make all entries the same highlight color.
                    if hasattr(vobj, "DiffuseColor"):
                        try:
                            dc = list(vobj.DiffuseColor)
                            if dc:
                                vobj.DiffuseColor = [highlight_face] * len(dc)
                        except Exception:
                            pass

                    # Thicken the outline if supported
                    if hasattr(vobj, "LineWidth"):
                        try:
                            vobj.LineWidth = max(getattr(vobj, "LineWidth", 1.0), 3.0)
                        except Exception:
                            pass

                except Exception:
                    # View styling is non-critical; ignore failures
                    continue

            if doc is not None:
                doc.recompute()

            App.Console.PrintMessage(
                f">>> [SquatchCut] RunNesting: placed {len(placed_objs)} panels on sheet {sheet_w} x {sheet_h} {getattr(sess, 'sheet_units', 'mm')}\n"
            )

        except Exception as exc:
            App.Console.PrintError(
                f">>> [SquatchCut] Error in RunNestingCommand.Activated(): {exc}\n"
            )
            App.Console.PrintError(traceback.format_exc())
            QtWidgets.QMessageBox.critical(
                None,
                "SquatchCut – Nesting Error",
                f"An error occurred while running nesting:\n{exc}",
            )
        finally:
            App.Console.PrintMessage(
                ">>> [SquatchCut] RunNestingCommand.Activated() completed\n"
            )

    def IsActive(self):
        # For now, always active.
        return True


# Exported command instance used by InitGui.py
COMMAND = RunNestingCommand()
