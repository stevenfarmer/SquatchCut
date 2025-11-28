"""@codex
FreeCAD command to run the SquatchCut nesting engine and create geometry.
Primary user entry is via SquatchCut_MainUI; this command remains for advanced/legacy flows.
"""

import os
import traceback

import FreeCAD  # type: ignore
import FreeCADGui  # type: ignore
import FreeCAD as App  # type: ignore
import FreeCADGui as Gui  # type: ignore
from PySide2 import QtWidgets  # type: ignore

# Geometry
try:
    import Part  # type: ignore
except Exception:
    Part = None

from SquatchCut.core import session
from SquatchCut.core.nesting import (
    Part,
    nest_on_multiple_sheets,
    nest_cut_optimized,
    estimate_cut_counts,
    compute_utilization,
    nest_parts,
    NestingConfig,
)  # type: ignore
from SquatchCut.core.cut_optimization import estimate_cut_path_complexity
from SquatchCut.core.overlap_check import detect_overlaps
from SquatchCut.core.session_state import (
    get_gap_mm,
    get_kerf_mm,
    get_kerf_width_mm,
    get_last_layout,
    get_sheet_size,
    get_optimization_mode,
    get_optimize_for_cut_path,
    get_allowed_rotations_deg,
    get_export_include_labels,
    get_export_include_dimensions,
    set_last_layout,
    set_nesting_stats,
)
from SquatchCut.ui.messages import show_error, show_info, show_warning


class RunNestingCommand:
    """
    SquatchCut - Run Nesting command.

    Uses:
        - session_state for sheet width / sheet height / kerf / gap

    Steps:
        1) Validate prerequisites.
        2) Call nesting_engine.compute_layout(...).
        3) Create geometry via geometry_output.create_geometry_from_layout(...).
        4) Store layout in session_state.
    """

    def GetResources(self):
        return {
            "Pixmap": ":/icons/Draft_Rectangle.svg",
            "MenuText": "Run Nesting",
            "ToolTip": "Nest panels onto one or more sheets",
        }

    def Activated(self):
        try:
            doc = App.ActiveDocument
            if doc is None:
                App.Console.PrintMessage(">>> [SquatchCut] RunNesting: no active document\n")
                return

            # Sync session_state from document properties
            try:
                session.sync_state_from_doc(doc)
            except Exception:
                pass

            try:
                sheet_w, sheet_h = get_sheet_size()
            except Exception:
                sheet_w = sheet_h = None
            if not sheet_w or not sheet_h:
                App.Console.PrintError(">>> [SquatchCut] Cannot read sheet size from session_state.\n")
                return

            kerf_mm = get_kerf_mm()
            gap_mm = get_gap_mm()
            opt_mode = get_optimization_mode()
            cut_mode = get_optimize_for_cut_path()
            kerf_width = get_kerf_width_mm()
            allowed_rotations = get_allowed_rotations_deg()
            export_labels = get_export_include_labels()
            export_dims = get_export_include_dimensions()

            panel_objs = self._get_panel_objects(doc)

            # Manage SourcePanels group: move originals aside and hide them
            if not panel_objs:
                msg = (
                    "No panels were selected for nesting.\n\n"
                    "Select one or more panel objects (rectangles/faces) and try again."
                )
                show_warning(msg)
                FreeCAD.Console.PrintMessage("[SquatchCut] No panels selected for nesting.\n")
                return

            source_group = doc.getObject("SourcePanels")
            if source_group is None:
                source_group = doc.addObject("App::DocumentObjectGroup", "SourcePanels")

            SHEET_MARGIN = sheet_w * 0.25
            offset_x = -(sheet_w + SHEET_MARGIN)

            # Offset the source panels group to the left of all sheets
            try:
                placement = source_group.Placement
                base = placement.Base
                base.x = offset_x
                base.y = 0.0
                base.z = 0.0
                placement.Base = base
                source_group.Placement = placement
            except Exception:
                # If the group cannot be moved as a whole, shift members instead
                for obj in panel_objs:
                    try:
                        placement = obj.Placement
                        base = placement.Base
                        base.x += offset_x
                        placement.Base = base
                        obj.Placement = placement
                    except Exception:
                        continue

            # Move original selected panel objects into the SourcePanels group
            for obj in panel_objs:
                if obj not in source_group.Group:
                    source_group.addObject(obj)

            # Hide SourcePanels group by default
            try:
                source_group.ViewObject.Visibility = False
            except Exception:
                pass

            parts: list[Part] = []
            for obj in panel_objs:
                try:
                    w, h = self._get_obj_dimensions_mm(obj)
                except Exception:
                    continue
                can_rotate = False
                if hasattr(obj, "SquatchCutCanRotate"):
                    try:
                        can_rotate = bool(obj.SquatchCutCanRotate)
                    except Exception:
                        can_rotate = False
                parts.append(Part(id=obj.Name, width=w, height=h, can_rotate=can_rotate))

            if not parts:
                App.Console.PrintMessage(
                    ">>> [SquatchCut] RunNesting: no valid panel dimensions found\n"
                )
                return

            try:
                if cut_mode:
                    cfg = NestingConfig(
                        optimize_for_cut_path=True,
                        kerf_width_mm=kerf_width or kerf_mm,
                        allowed_rotations_deg=allowed_rotations,
                        spacing_mm=gap_mm,
                    )
                    placed_parts = nest_parts(parts, sheet_w, sheet_h, cfg)
                elif opt_mode == "cuts":
                    placed_parts = nest_cut_optimized(
                        parts,
                        sheet_w,
                        sheet_h,
                        kerf=float(kerf_mm),
                        margin=float(gap_mm),
                    )
                else:
                    cfg = NestingConfig(kerf_width_mm=kerf_mm, spacing_mm=gap_mm)
                    placed_parts = nest_on_multiple_sheets(
                        parts,
                        sheet_w,
                        sheet_h,
                        cfg,
                    )
            except ValueError as e:
                show_error(
                    f"Nesting failed due to panel size constraints:\n\n{e}",
                    title="SquatchCut Nesting Failed",
                )
                FreeCAD.Console.PrintError(f"[SquatchCut] Nesting failed: {e}\n")
                return
            except Exception as e:
                show_error(
                    f"An unexpected error occurred during nesting:\n\n{e}",
                    title="SquatchCut Nesting Error",
                )
                FreeCAD.Console.PrintError(f"[SquatchCut] Unexpected nesting error: {e}\n")
                return
            set_last_layout(placed_parts)
            if not placed_parts:
                show_warning(
                    "Nesting completed but no panels were placed.\n"
                    "Check that your panel sizes and sheet size are valid."
                )
                FreeCAD.Console.PrintWarning("[SquatchCut] Nesting produced no placements.\n")
                return

            # Create sheet groups and place clones from placed_parts
            sheet_groups = {}  # sheet_index -> (group, sheet_origin_x)
            SHEET_MARGIN = sheet_w * 0.25  # space between sheets

            for pp in placed_parts:
                sheet_index = pp.sheet_index

                # Create / fetch group for this sheet
                if sheet_index not in sheet_groups:
                    sheet_origin_x = sheet_index * (sheet_w + SHEET_MARGIN)
                    group_name = f"Sheet_{sheet_index + 1}"
                    group = doc.addObject("App::DocumentObjectGroup", group_name)

                    # Optional boundary rectangle for the sheet
                    try:
                        import Draft
                        rect = Draft.makeRectangle(length=sheet_w, height=sheet_h)
                        rect.Label = f"{group_name}_Boundary"
                        rect.Placement.Base.x = sheet_origin_x
                        rect.Placement.Base.y = 0.0
                        group.addObject(rect)
                    except Exception:
                        pass

                    sheet_groups[sheet_index] = (group, sheet_origin_x)

                sheet_group, sheet_origin_x = sheet_groups[sheet_index]

                # Find original source object by id
                src_obj = doc.getObject(pp.id)
                if src_obj is None:
                    FreeCAD.Console.PrintError(f"[SquatchCut] Object {pp.id} not found.\n")
                    continue

                # Clone into this sheet group
                try:
                    import Draft
                    clone = Draft.clone(src_obj)
                except Exception:
                    clone = doc.copyObject(src_obj)

                sheet_group.addObject(clone)

                # Reset placement and set new coordinates
                placement = clone.Placement
                placement.Base.x = 0.0
                placement.Base.y = 0.0
                placement.Base.z = 0.0
                try:
                    rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), pp.rotation_deg)
                except Exception:
                    rotation = FreeCAD.Rotation()
                placement.Rotation = rotation

                placement.Base.x = sheet_origin_x + pp.x
                placement.Base.y = pp.y
                clone.Placement = placement

                FreeCAD.Console.PrintMessage(
                    f"[SquatchCut] Placed {pp.id} on sheet {sheet_index + 1} "
                    f"at ({sheet_origin_x + pp.x:.1f}, {pp.y:.1f}) "
                    f"size {pp.width:.1f} x {pp.height:.1f} mm\n"
                )

            if doc is not None:
                doc.recompute()
                util = compute_utilization(placed_parts, sheet_w, sheet_h)
                cuts = estimate_cut_counts(placed_parts, sheet_w, sheet_h)
                cut_complexity = estimate_cut_path_complexity(placed_parts, kerf_width_mm=kerf_width or kerf_mm)
                overlaps = detect_overlaps(placed_parts)
                if overlaps:
                    for a, b in overlaps:
                        FreeCAD.Console.PrintError(
                            f"[SquatchCut] Overlap detected between {getattr(a, 'id', '?')} and {getattr(b, 'id', '?')} on sheet {getattr(a, 'sheet_index', '?')}.\n"
                        )
                set_nesting_stats(util.get("sheets_used", None), cut_complexity, len(overlaps))
                summary_msg = (
                    f"[SquatchCut] Nesting complete: {len(placed_parts)} parts, "
                    f"sheets used={util.get('sheets_used', 0)}, "
                    f"utilization={util.get('utilization_percent', 0.0):.1f}%, "
                    f"estimated cuts={cuts.get('total', 0)} "
                    f"({cuts.get('vertical', 0)} vertical, {cuts.get('horizontal', 0)} horizontal).\n"
                )
                FreeCAD.Console.PrintMessage(summary_msg)
                FreeCAD.Console.PrintMessage(
                    f"[SquatchCut] Nesting complete: {len(placed_parts)} parts across {len(sheet_groups)} sheet(s).\n"
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
            FreeCAD.Console.PrintMessage("[SquatchCut] RunNestingCommand.Activated() completed\n")

    def IsActive(self):
        # For now, always active.
        return True

    # Helper methods wired into existing helpers/state -----------------

    def _get_sheet_size_mm(self, session) -> tuple[float, float]:
        """Return sheet size from SessionState or raise if missing."""
        sheet_w = getattr(session, "sheet_width", None)
        sheet_h = getattr(session, "sheet_height", None)
        if not sheet_w or not sheet_h:
            raise ValueError("sheet size not defined")
        return float(sheet_w), float(sheet_h)

    def _get_panel_objects(self, doc):
        """Return a list of FreeCAD objects to be treated as rectangular panels."""
        try:
            sel = Gui.Selection.getSelection()
            if sel:
                all_flagged = [
                    obj for obj in getattr(doc, "Objects", []) if getattr(obj, "SquatchCutPanel", False)
                ]
                if all_flagged and len(sel) < len(all_flagged):
                    show_warning(
                        f"{len(sel)} panel(s) selected, but {len(all_flagged)} are available.\n"
                        "Only selected panels will be nested.",
                        title="SquatchCut Nesting Selection",
                    )
                return sel
        except Exception:
            pass

        panels = []
        for obj in getattr(doc, "Objects", []):
            try:
                if hasattr(obj, "SquatchCutPanel") and bool(obj.SquatchCutPanel):
                    panels.append(obj)
            except Exception:
                continue
        return panels

    def _get_obj_dimensions_mm(self, obj) -> tuple[float, float]:
        """Given a panel object, return (width_mm, height_mm) using its bounding box."""
        bb = obj.Shape.BoundBox
        width = bb.XLength
        height = bb.YLength
        return float(width), float(height)

    def _create_sheet_group(
        self, doc, sheet_index: int, sheet_w: float, sheet_h: float, sheet_origin_x: float = 0.0
    ):
        """Create and return a Group to hold one sheet's panels."""
        group_name = f"Sheet_{sheet_index + 1}"
        group = doc.addObject("App::DocumentObjectGroup", group_name)

        try:
            import Draft

            rect = Draft.makeRectangle(length=sheet_w, height=sheet_h)
            rect.Label = f"{group_name}_Boundary"
            rect.Placement.Base.x = sheet_origin_x
            rect.Placement.Base.y = 0.0
            group.addObject(rect)
        except Exception:
            pass

        return group

    def _clone_into_group(self, doc, src_obj, group):
        """Clone src_obj into group and return the clone."""
        try:
            import Draft

            clone = Draft.clone(src_obj)
        except Exception:
            clone = doc.copyObject(src_obj)
        group.addObject(clone)
        return clone


# Toggle command to show/hide SourcePanels group
class ToggleSourcePanelsCommand:
    def GetResources(self):
        return {
            "Pixmap": ":/icons/Std_ToggleVisibility.svg",
            "MenuText": "Toggle Source Panels",
            "ToolTip": "Show or hide the original source panel objects",
        }

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if doc is None:
            FreeCAD.Console.PrintError("[SquatchCut] No active document.\n")
            return

        group = doc.getObject("SourcePanels")
        if group is None:
            FreeCAD.Console.PrintMessage("[SquatchCut] No SourcePanels group exists.\n")
            return

        try:
            group.ViewObject.Visibility = not group.ViewObject.Visibility
            state = "shown" if group.ViewObject.Visibility else "hidden"
            FreeCAD.Console.PrintMessage(
                f"[SquatchCut] SourcePanels group {state}.\n"
            )
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"[SquatchCut] Failed toggling SourcePanels: {e}\n"
            )

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


class ExportNestingCSVCommand:
    def GetResources(self):
        return {
            "Pixmap": ":/icons/Std_Export.svg",
            "MenuText": "Export Nesting CSV",
            "ToolTip": "Export the last SquatchCut nesting layout as a CSV file",
        }

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if doc is None:
            FreeCAD.Console.PrintError("[SquatchCut] No active document for export.\n")
            return

        layout = get_last_layout()
        if not layout:
            show_info(
                "There is no nesting layout to export.\n"
                "Run the nesting command first, then try again.",
                title="SquatchCut Export",
            )
            FreeCAD.Console.PrintMessage("[SquatchCut] No layout available for export.\n")
            return

        # Determine default path suggestion
        if doc.FileName:
            base, _ = os.path.splitext(doc.FileName)
            default_path = base + "_squatchcut_nesting.csv"
        else:
            default_path = os.path.join(os.path.expanduser("~"), "squatchcut_nesting.csv")

        # Ask user where to save
        mw = FreeCADGui.getMainWindow()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            mw,
            "Export SquatchCut Nesting CSV",
            default_path,
            "CSV Files (*.csv)"
        )
        if not filename:
            show_info("Export canceled.", title="SquatchCut Export")
            FreeCAD.Console.PrintMessage("[SquatchCut] Export canceled by user.\n")
            return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                # Include rotation column
                f.write("sheet_index,part_id,width_mm,height_mm,x_mm,y_mm,angle_deg\n")
                for pp in layout:
                    line = (
                        f"{pp.sheet_index},{pp.id},"
                        f"{pp.width:.3f},{pp.height:.3f},"
                        f"{pp.x:.3f},{pp.y:.3f},{pp.rotation_deg}\n"
                    )
                    f.write(line)

            FreeCAD.Console.PrintMessage(
                f"[SquatchCut] Exported nesting CSV with {len(layout)} rows to: {filename}\n"
            )
        except Exception as e:
            show_error(
                f"Failed to export nesting CSV:\n\n{e}",
                title="SquatchCut Export Error",
            )
            FreeCAD.Console.PrintError(
                f"[SquatchCut] Failed to export nesting CSV: {e}\n"
            )

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


FreeCADGui.addCommand("SquatchCut_ToggleSourcePanels", ToggleSourcePanelsCommand())
FreeCADGui.addCommand("SquatchCut_ExportNestingCSV", ExportNestingCSVCommand())

# Exported command instance used by InitGui.py
COMMAND = RunNestingCommand()
