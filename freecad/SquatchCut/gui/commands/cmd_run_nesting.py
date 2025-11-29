"""@codex
FreeCAD command to run the SquatchCut nesting engine and create geometry.
Primary user entry is via SquatchCut_ShowTaskPanel; this command remains for advanced/legacy flows.
"""

import os
import traceback

try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
    FreeCAD = App
except Exception:
    App = None
    Gui = None
    FreeCAD = None
from SquatchCut.gui.qt_compat import QtWidgets

# Geometry
try:
    import Part  # type: ignore
except Exception:
    Part = None

from SquatchCut.core import logger, session, session_state
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
from SquatchCut.core.geometry_sync import ensure_sheet_object
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
from SquatchCut.gui.nesting_view import rebuild_nested_geometry
from SquatchCut.gui.view_utils import zoom_to_objects
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

    def _get_panel_objects(self):
        """
        Return the list of source panel objects used as the geometric basis for nesting.
        Relies on session helpers populated by sync_source_panels_to_document().
        """
        return session.get_source_panel_objects()

    def Activated(self):
        if App is None or Gui is None:
            try:
                logger.warning("RunNestingCommand.Activated() called outside FreeCAD GUI environment.")
            except Exception:
                pass
            return

        try:
            doc = App.ActiveDocument
            if doc is None:
                doc = App.newDocument("SquatchCut")
            try:
                Gui.ActiveDocument = Gui.getDocument(doc.Name)
            except Exception:
                pass

            panels = session.get_panels()
            if not panels:
                logger.info("RunNestingCommand: no panels in session; nothing to nest.")
                return

            panel_objs = self._get_panel_objects()
            if not panel_objs:
                logger.info("RunNestingCommand: no source panel objects; nothing to nest.")
                return

            for src in panel_objs:
                try:
                    if hasattr(src, "ViewObject"):
                        src.ViewObject.Visibility = False
                except Exception:
                    continue

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
                logger.error("Cannot read sheet size from session_state.")
                return

            kerf_mm = get_kerf_mm()
            gap_mm = get_gap_mm()
            opt_mode = get_optimization_mode()
            cut_mode = get_optimize_for_cut_path()
            kerf_width = get_kerf_width_mm()
            allowed_rotations = get_allowed_rotations_deg()
            export_labels = get_export_include_labels()
            export_dims = get_export_include_dimensions()
            nesting_mode = session_state.get_nesting_mode()

            # Manage SourcePanels group: keep originals, hide them
            if not panel_objs:
                msg = (
                    "No panels were selected for nesting.\n\n"
                    "Select one or more panel objects (rectangles/faces) and try again."
                )
                show_warning(msg)
                logger.warning("No panels selected for nesting.")
                return

            source_group = doc.getObject("SquatchCut_SourcePanels")
            if source_group is None:
                source_group = doc.addObject("App::DocumentObjectGroup", "SquatchCut_SourcePanels")

            # Move original selected panel objects into the SourcePanels group
            for obj in panel_objs:
                if obj not in source_group.Group:
                    source_group.addObject(obj)

            # Hide SourcePanels group by default
            try:
                source_group.ViewObject.Visibility = False
            except Exception:
                pass

            session_state.set_source_panel_objects(source_group.Group)
            try:
                session.set_source_panel_objects(source_group.Group)
            except Exception:
                pass
            # Also hide individual source objects
            for obj in source_group.Group:
                try:
                    obj.ViewObject.Visibility = False
                except Exception:
                    pass

            parts: list[Part] = []
            panels_data = session.get_panels() or []
            for idx, obj in enumerate(panel_objs):
                try:
                    w = h = None
                    if panels_data:
                        try:
                            panel_data = panels_data[idx % len(panels_data)]
                            w = float(panel_data.get("width", 0) or 0)
                            h = float(panel_data.get("height", 0) or 0)
                        except Exception:
                            w = h = None
                    if not w or not h or w <= 0 or h <= 0:
                        w, h = self._get_obj_dimensions_mm(obj)
                except Exception:
                    continue
                if w <= 0 or h <= 0:
                    continue
                can_rotate = False
                if hasattr(obj, "SquatchCutCanRotate"):
                    try:
                        can_rotate = bool(obj.SquatchCutCanRotate)
                    except Exception:
                        can_rotate = False
                parts.append(Part(id=obj.Name, width=w, height=h, can_rotate=can_rotate))

            if not parts:
                logger.warning("RunNesting: no valid panel dimensions found")
                return

            try:
                if cut_mode:
                    cfg = NestingConfig(
                        optimize_for_cut_path=True,
                        kerf_width_mm=kerf_width or kerf_mm,
                        allowed_rotations_deg=allowed_rotations,
                        spacing_mm=gap_mm,
                        nesting_mode="cut_friendly",
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
                    cfg = NestingConfig(
                        kerf_width_mm=kerf_mm,
                        spacing_mm=gap_mm,
                        nesting_mode=nesting_mode,
                    )
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
                logger.error(f"Nesting failed: {e}")
                return
            except Exception as e:
                show_error(
                    f"An unexpected error occurred during nesting:\n\n{e}",
                    title="SquatchCut Nesting Error",
                )
                logger.error(f"Unexpected nesting error: {e}")
                return
            set_last_layout(placed_parts)
            if not placed_parts:
                show_warning(
                    "Nesting completed but no panels were placed.\n"
                    "Check that your panel sizes and sheet size are valid."
                )
                logger.warning("Nesting produced no placements.")
                return

            logger.info(">>> [SquatchCut] Rebuilding nested layout view...")
            sheet_obj = ensure_sheet_object(doc)
            group, nested_objs = rebuild_nested_geometry(doc, placed_parts, sheet_w, sheet_h, panel_objs)

            if doc is not None:
                try:
                    doc.recompute()
                except Exception:
                    pass
                session.set_sheet_objects([sheet_obj] if sheet_obj else [])
                session.set_nested_panel_objects(nested_objs)
                session_state.set_nested_sheet_group(group)
                util = compute_utilization(placed_parts, sheet_w, sheet_h)
                cuts = estimate_cut_counts(placed_parts, sheet_w, sheet_h)
                cut_complexity = estimate_cut_path_complexity(placed_parts, kerf_width_mm=kerf_width or kerf_mm)
                overlaps = detect_overlaps(placed_parts)
                if overlaps:
                    for a, b in overlaps:
                        logger.error(
                            f"Overlap detected between {getattr(a, 'id', '?')} and {getattr(b, 'id', '?')} on sheet {getattr(a, 'sheet_index', '?')}."
                        )
                logger.info(
                    f">>> [SquatchCut] Nesting mode={nesting_mode}, parts={len(placed_parts)}, sheets={util.get('sheets_used', 0)}"
                )
                set_nesting_stats(util.get("sheets_used", None), cut_complexity, len(overlaps))
                sheet_count = (max(pp.sheet_index for pp in placed_parts) + 1) if placed_parts else 0
                summary_msg = (
                    f"Nesting complete: {len(placed_parts)} parts, "
                    f"sheets used={util.get('sheets_used', 0)}, "
                    f"utilization={util.get('utilization_percent', 0.0):.1f}%, "
                    f"estimated cuts={cuts.get('total', 0)} "
                    f"({cuts.get('vertical', 0)} vertical, {cuts.get('horizontal', 0)} horizontal).\n"
                )
                logger.info(summary_msg.strip())
                logger.info(f"Nesting complete: {len(placed_parts)} parts across {sheet_count} sheet(s).")
                logger.info(f"Nested {len(panel_objs)} source panels into {sheet_count} sheet group(s).")
                try:
                    targets = []
                    if sheet_obj:
                        targets.append(sheet_obj)
                    targets.extend(nested_objs or [])
                    if targets:
                        zoom_to_objects(targets)
                except Exception:
                    pass

        except Exception as exc:
            logger.error(f"Error in RunNestingCommand.Activated(): {exc}")
            logger.debug(traceback.format_exc())
            QtWidgets.QMessageBox.critical(
                None,
                "SquatchCut – Nesting Error",
                f"An error occurred while running nesting:\n{exc}",
            )
        finally:
            logger.debug("RunNestingCommand.Activated() completed")

    def IsActive(self):
        # Only active inside a running FreeCAD GUI session.
        return App is not None and Gui is not None


class ApplyNestingCommand:
    """
    Applies the current nesting to the document by reusing RunNestingCommand,
    then closes the SquatchCut task panel.
    """

    def GetResources(self):
        return {
            "MenuText": "Apply SquatchCut",
            "ToolTip": "Run SquatchCut nesting and apply it to the active document",
        }

    def IsActive(self):
        return App is not None and Gui is not None

    def Activated(self):
        try:
            run_cmd = RunNestingCommand()
            run_cmd.Activated()
            try:
                Gui.Control.closeDialog()
            except Exception as e:
                logger.warning(f"ApplyNestingCommand: failed to close dialog: {e!r}")
        except Exception as e:
            logger.error(f"Error in ApplyNestingCommand.Activated(): {e!r}")

    # Helper methods wired into existing helpers/state -----------------

    def _get_sheet_size_mm(self, session) -> tuple[float, float]:
        """Return sheet size from SessionState or raise if missing."""
        sheet_w = getattr(session, "sheet_width", None)
        sheet_h = getattr(session, "sheet_height", None)
        if not sheet_w or not sheet_h:
            raise ValueError("sheet size not defined")
        return float(sheet_w), float(sheet_h)

    def _get_panel_objects(self):
        """
        Return the source panel objects stored in session helpers.
        Populated by sync_source_panels_to_document() after CSV import.
        """
        return session.get_source_panel_objects()

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
        if App is None or Gui is None:
            try:
                logger.warning("ToggleSourcePanelsCommand.Activated() called outside FreeCAD GUI environment.")
            except Exception:
                pass
            return

        doc = App.ActiveDocument
        if doc is None:
            logger.error("No active document.")
            return

        group = doc.getObject("SquatchCut_SourcePanels")
        if group is None:
            logger.info("No SourcePanels group exists.")
            return

        try:
            group.ViewObject.Visibility = not group.ViewObject.Visibility
            state = "shown" if group.ViewObject.Visibility else "hidden"
            logger.info(f"SourcePanels group {state}.")
        except Exception as e:
            logger.error(f"Failed toggling SourcePanels: {e}")

    def IsActive(self):
        return App is not None and Gui is not None and App.ActiveDocument is not None


class ExportNestingCSVCommand:
    """
    Placeholder command for exporting nesting data to CSV.
    This is a stub and currently does nothing. It exists only
    so the command can be registered without breaking imports.
    """

    def GetResources(self):
        return {
            "MenuText": "Export nesting CSV (not implemented)",
            "ToolTip": "Export nesting data to CSV (coming soon)",
            "Pixmap": "",
        }

    def IsActive(self):
        # Keep this command disabled for now until implemented.
        return False

    def Activated(self):
        # No-op for now; TODO: implement real CSV export.
        try:
            logger.info("ExportNestingCSVCommand.Activated() called, but feature is not implemented yet.")
        except Exception:
            pass


if Gui is not None:
    Gui.addCommand("SquatchCut_ToggleSourcePanels", ToggleSourcePanelsCommand())
    # TODO: Implement real nesting CSV export and enable this command.
    Gui.addCommand("SquatchCut_ExportNestingCSV", ExportNestingCSVCommand())
    Gui.addCommand("SquatchCut_RunNesting", RunNestingCommand())
    Gui.addCommand("SquatchCut_ApplyNesting", ApplyNestingCommand())

# Exported command instance used by InitGui.py
COMMAND = RunNestingCommand()
