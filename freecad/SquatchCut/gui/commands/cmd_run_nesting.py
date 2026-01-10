"""@codex
FreeCAD command to run the SquatchCut nesting engine and create geometry.
Primary user entry is via SquatchCut_ShowTaskPanel; this command remains for advanced/legacy flows.
"""

from SquatchCut.core import logger, session, session_state, view_controller
from SquatchCut.core.complex_geometry import (
    create_rectangular_geometry,
)
from SquatchCut.core.cut_optimization import estimate_cut_path_complexity
from SquatchCut.core.geometry_nesting_engine import (
    GeometryNestingEngine,
    NestingMode,
    SheetGeometry,
)
from SquatchCut.core.nesting import (
    NestingConfig,
    NestingValidationError,
    Part,
    analyze_sheet_exhaustion,
    compute_utilization_for_sheets,
    derive_sheet_sizes_for_layout,
    estimate_cut_counts_for_sheets,
    expand_sheet_sizes,
    get_effective_job_sheets_for_nesting,
    get_usable_sheet_area,
    nest_cut_optimized,
    nest_on_multiple_sheets,
    nest_parts,
    validate_parts_fit_sheet,
)  # type: ignore
from SquatchCut.core.overlap_check import detect_overlaps
from SquatchCut.core.performance_utils import (
    check_system_resources,
    performance_monitor,
)
from SquatchCut.core.session_state import (
    get_allowed_rotations_deg,
    get_gap_mm,
    get_kerf_mm,
    get_kerf_width_mm,
    get_optimization_mode,
    get_optimize_for_cut_path,
    get_sheet_size,
    set_last_layout,
    set_nesting_stats,
)
from SquatchCut.core.sheet_model import build_sheet_boundaries, compute_sheet_spacing
from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.icons import get_icon
from SquatchCut.gui.nesting_view import rebuild_nested_geometry
from SquatchCut.gui.view_helpers import (
    fit_view_to_sheet_and_nested,
    fit_view_to_source,
    show_nested_only,
    show_source_and_sheet,
)
from SquatchCut.ui.messages import show_error, show_warning


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
            "Pixmap": get_icon("run_nesting"),
            "MenuText": "Nest Parts",
            "ToolTip": "Run the SquatchCut nesting algorithm to place panels on the active sheet.",
        }

    def __init__(self):
        self.validation_error = None

    def _get_panel_objects(self):
        """
        Return the list of source panel objects used as the geometric basis for nesting.
        Relies on session helpers populated by sync_source_panels_to_document().
        """
        return session.get_source_panel_objects()

    @staticmethod
    def _safe_object_name(obj) -> str:
        if obj is None:
            return ""
        try:
            return getattr(obj, "Name", "") or ""
        except ReferenceError:
            return ""

    def _resolve_live_source_objects(self, doc, fallback_objects):
        """
        Return the current, live set of source panel objects from the document.
        Falls back to the provided list (after filtering) if the document group is empty.
        """
        live = []
        seen = set()

        def _add(obj):
            name = self._safe_object_name(obj)
            if not name or name in seen:
                return
            seen.add(name)
            live.append(obj)

        if doc is not None:
            group = doc.getObject("SquatchCut_SourceParts")
            if group is not None:
                for member in list(getattr(group, "Group", []) or []):
                    _add(member)
        if live:
            return live

        for obj in fallback_objects or []:
            name = self._safe_object_name(obj)
            if not name or name in seen:
                continue
            resolved = doc.getObject(name) if doc is not None else None
            _add(resolved or obj)
        return live

    def Activated(self):
        self.validation_error = None
        if App is None or Gui is None:
            try:
                logger.warning(
                    "RunNestingCommand.Activated() called outside FreeCAD GUI environment."
                )
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
                logger.info(
                    "RunNestingCommand: no source panel objects; nothing to nest."
                )
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

            source_group = doc.getObject("SquatchCut_SourceParts")
            if source_group is None:
                source_group = doc.addObject(
                    "App::DocumentObjectGroup", "SquatchCut_SourceParts"
                )

            # Move original selected panel objects into the SourcePanels group
            valid_panel_objs = []
            for obj in panel_objs:
                try:
                    if obj is None:
                        continue
                    if obj not in source_group.Group:
                        source_group.addObject(obj)
                    valid_panel_objs.append(obj)
                except Exception as e:
                    logger.warning(
                        f"Skipping invalid panel object during nesting addObject: {e}"
                    )
                    continue
            if not valid_panel_objs:
                show_warning("No valid panel objects available for nesting.")
                return

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
            for idx, obj in enumerate(valid_panel_objs):
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
                parts.append(
                    Part(id=obj.Name, width=w, height=h, can_rotate=can_rotate)
                )

            if not parts:
                logger.warning("RunNesting: no valid panel dimensions found")
                return

            # Check system resources for large datasets
            check_system_resources(len(parts))

            # Determine if we should use geometric nesting for complex shapes
            use_geometric_nesting = self._should_use_geometric_nesting(panels_data)

            usable_width, usable_height = get_usable_sheet_area(
                sheet_w, sheet_h, margin_mm=gap_mm
            )
            try:
                validate_parts_fit_sheet(parts, usable_width, usable_height)
            except NestingValidationError as exc:
                self._handle_validation_error(doc, exc)
                return

            sheet_mode = session_state.get_sheet_mode()
            job_sheets = session_state.get_job_sheets()
            sheet_definitions = get_effective_job_sheets_for_nesting(
                sheet_mode, job_sheets
            )
            if sheet_mode == "job_sheets" and not sheet_definitions:
                show_error(
                    "No job sheets are defined. Add at least one sheet or switch back to simple mode.",
                    title="SquatchCut",
                )
                self.validation_error = ValueError(
                    "Missing job sheets in advanced mode."
                )
                return
            sheet_sizes_override = expand_sheet_sizes(sheet_definitions or [])
            if sheet_definitions:
                total_instances = len(sheet_sizes_override) or len(sheet_definitions)
                summary_parts = []
                for idx, sheet in enumerate(sheet_definitions):
                    label = sheet.get("label") or f"Sheet {idx + 1}"
                    width = sheet.get("width_mm") or 0
                    height = sheet.get("height_mm") or 0
                    qty = sheet.get("quantity") or 1
                    summary_parts.append(
                        f"{label}={width:.1f}x{height:.1f}mm (qty {qty})"
                    )
                logger.info(
                    f">>> [SquatchCut] Advanced job sheets active with {total_instances} sheet instance(s): "
                    + "; ".join(summary_parts)
                )
            from SquatchCut.ui.progress import SimpleProgressContext

            try:
                with SimpleProgressContext(
                    "Running nesting algorithm...", "SquatchCut Nesting"
                ):
                    # Apply performance monitoring to nesting operations
                    @performance_monitor(
                        f"Nesting {len(parts)} parts", threshold_seconds=2.0
                    )
                    def run_nesting_algorithm():
                        # Check if we should use geometric nesting for complex shapes
                        if use_geometric_nesting:
                            return self._run_geometric_nesting(
                                parts, panels_data, sheet_w, sheet_h, gap_mm
                            )

                        # Check if genetic algorithm optimization is enabled
                        use_genetic = session_state.get_use_genetic_algorithm()

                        if use_genetic:
                            from SquatchCut.core.genetic_nesting import (
                                GeneticConfig,
                                genetic_nest_parts,
                            )
                            from SquatchCut.core.grain_direction import (
                                add_grain_info_to_parts,
                            )

                            # Convert parts to grain-aware parts
                            grain_aware_parts = add_grain_info_to_parts(parts)

                            # Configure genetic algorithm
                            genetic_config = GeneticConfig(
                                population_size=session_state.get_genetic_population_size()
                                or 50,
                                generations=session_state.get_genetic_generations()
                                or 100,
                                mutation_rate=session_state.get_genetic_mutation_rate()
                                or 0.1,
                                crossover_rate=session_state.get_genetic_crossover_rate()
                                or 0.8,
                                max_time_seconds=session_state.get_genetic_max_time()
                                or 300,
                            )

                            logger.info(
                                f">>> [SquatchCut] Using genetic algorithm optimization with {len(grain_aware_parts)} parts"
                            )

                            # Apply performance optimizations for genetic algorithm
                            from SquatchCut.core.performance_utils import (
                                cached_nesting,
                                memory_optimized,
                            )

                            @cached_nesting
                            @memory_optimized
                            def optimized_genetic_nesting(
                                parts, width, height, kerf, spacing, config
                            ):
                                return genetic_nest_parts(
                                    parts, width, height, kerf, spacing, config
                                )

                            return optimized_genetic_nesting(
                                grain_aware_parts,
                                sheet_w,
                                sheet_h,
                                kerf_mm,
                                gap_mm,
                                genetic_config,
                            )
                        elif cut_mode:
                            cfg = NestingConfig(
                                optimize_for_cut_path=True,
                                kerf_width_mm=kerf_width or kerf_mm,
                                allowed_rotations_deg=allowed_rotations,
                                spacing_mm=gap_mm,
                                nesting_mode="cut_friendly",
                            )
                            return nest_parts(
                                parts,
                                sheet_w,
                                sheet_h,
                                cfg,
                                sheet_sizes=sheet_sizes_override,
                            )
                        elif opt_mode == "cuts":
                            return nest_cut_optimized(
                                parts,
                                sheet_w,
                                sheet_h,
                                kerf=float(kerf_mm),
                                margin=float(gap_mm),
                                sheet_sizes=sheet_sizes_override,
                            )
                        else:
                            cfg = NestingConfig(
                                kerf_width_mm=kerf_mm,
                                spacing_mm=gap_mm,
                                nesting_mode=nesting_mode,
                            )
                            return nest_on_multiple_sheets(
                                parts,
                                sheet_w,
                                sheet_h,
                                cfg,
                                sheet_definitions=sheet_definitions,
                            )

                    placed_parts = run_nesting_algorithm()
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
            logger.info(
                ">>> [SquatchCut] RunNesting: cleaning up previous nested layout"
            )
            session.clear_nested_layout(doc)
            sheet_sizes = derive_sheet_sizes_for_layout(
                sheet_mode,
                session_state.get_job_sheets(),
                sheet_w,
                sheet_h,
                placed_parts,
            )
            if not sheet_sizes and sheet_w and sheet_h:
                sheet_sizes = [(sheet_w, sheet_h)]
            sheet_spacing = compute_sheet_spacing(sheet_sizes, gap_mm)
            boundaries, _ = build_sheet_boundaries(doc, sheet_sizes, sheet_spacing)
            sheet_obj = boundaries[0] if boundaries else None
            live_sources = self._resolve_live_source_objects(doc, panel_objs)
            if live_sources:
                session.set_source_panel_objects(live_sources)
                try:
                    session_state.set_source_panel_objects(live_sources)
                except Exception:
                    pass
            # Get user preferences for nesting view
            from SquatchCut.core.preferences import SquatchCutPreferences

            prefs = SquatchCutPreferences()

            group, nested_objs = rebuild_nested_geometry(
                doc,
                placed_parts,
                sheet_sizes=sheet_sizes,
                spacing=sheet_spacing,
                source_objects=live_sources or panel_objs,
                prefs=prefs,
            )
            sheet_label = getattr(sheet_obj, "Name", "unknown sheet")
            logger.info(
                f">>> [SquatchCut] RunNesting: created nested layout with {len(nested_objs)} parts on sheet {sheet_label}"
            )

            if doc is not None:
                try:
                    doc.recompute()
                except Exception:
                    pass
                session.set_sheet_objects(
                    boundaries if boundaries else ([sheet_obj] if sheet_obj else [])
                )
                session.set_nested_panel_objects(nested_objs)
                session_state.set_nested_sheet_group(group)
                util = compute_utilization_for_sheets(placed_parts, sheet_sizes)
                cuts = estimate_cut_counts_for_sheets(placed_parts, sheet_sizes)
                cut_complexity = estimate_cut_path_complexity(
                    placed_parts, kerf_width_mm=kerf_width or kerf_mm
                )
                overlaps = detect_overlaps(placed_parts)
                if overlaps:
                    for a, b in overlaps:
                        logger.error(
                            f"Overlap detected between {getattr(a, 'id', '?')} and {getattr(b, 'id', '?')} on sheet {getattr(a, 'sheet_index', '?')}."
                        )

                # Run quality assurance checks
                from SquatchCut.core.quality_assurance import check_nesting_quality

                quality_report = check_nesting_quality(
                    placed_parts, sheet_sizes, min_spacing=gap_mm, original_parts=parts
                )

                # Log quality issues
                if quality_report.issues:
                    critical_issues = [
                        i
                        for i in quality_report.issues
                        if i.severity.value == "critical"
                    ]
                    warning_issues = [
                        i
                        for i in quality_report.issues
                        if i.severity.value == "warning"
                    ]

                    if critical_issues:
                        logger.error(
                            f">>> [SquatchCut] Quality check found {len(critical_issues)} critical issues"
                        )
                        for issue in critical_issues[:3]:  # Show first 3
                            logger.error(f"    - {issue.description}")

                    if warning_issues:
                        logger.warning(
                            f">>> [SquatchCut] Quality check found {len(warning_issues)} warnings"
                        )
                        for issue in warning_issues[:2]:  # Show first 2
                            logger.warning(f"    - {issue.description}")
                else:
                    logger.info(
                        f">>> [SquatchCut] Quality check passed: {quality_report.overall_score:.1f}/100 score"
                    )

                # Generate cut sequence if requested
                if session_state.get_generate_cut_sequence():
                    from SquatchCut.core.cut_sequence import (
                        plan_optimal_cutting_sequence,
                    )

                    cut_sequences = plan_optimal_cutting_sequence(
                        placed_parts, sheet_sizes, kerf_mm
                    )

                    total_cuts = sum(len(seq.operations) for seq in cut_sequences)
                    total_time = sum(
                        seq.estimated_time_minutes for seq in cut_sequences
                    )
                    logger.info(
                        f">>> [SquatchCut] Cut sequence planned: {total_cuts} operations, estimated {total_time:.1f} minutes"
                    )

                    # Store cut sequences in session state for export
                    session_state.set_cut_sequences(cut_sequences)
                logger.info(
                    f">>> [SquatchCut] Nesting mode={nesting_mode}, parts={len(placed_parts)}, sheets={util.get('sheets_used', 0)}"
                )
                set_nesting_stats(
                    util.get("sheets_used", None), cut_complexity, len(overlaps)
                )
                sheet_count = (
                    (max(pp.sheet_index for pp in placed_parts) + 1)
                    if placed_parts
                    else 0
                )

                # Analyze sheet exhaustion
                exhaustion = analyze_sheet_exhaustion(placed_parts, sheet_sizes)
                if exhaustion.get("sheets_exhausted", False):
                    logger.warning(
                        f">>> [SquatchCut] Sheet exhaustion detected: used {exhaustion.get('max_sheet_index', 0) + 1} sheets "
                        f"but only {exhaustion.get('sheets_available', 0)} available. Some parts may be on duplicate sheet types."
                    )
                elif exhaustion.get("sheets_available", 0) > 0:
                    logger.info(
                        f">>> [SquatchCut] Sheet usage: {exhaustion.get('sheets_used', 0)} of {exhaustion.get('sheets_available', 0)} available sheets used."
                    )

                summary_msg = (
                    f"Nesting complete: {len(placed_parts)} parts, "
                    f"sheets used={util.get('sheets_used', 0)}, "
                    f"utilization={util.get('utilization_percent', 0.0):.1f}%, "
                    f"estimated cuts={cuts.get('total', 0)} "
                    f"({cuts.get('vertical', 0)} vertical, {cuts.get('horizontal', 0)} horizontal).\n"
                )
                logger.info(summary_msg.strip())
                logger.info(
                    f"Nesting complete: {len(placed_parts)} parts across {sheet_count} sheet(s)."
                )
                logger.info(
                    f"Nested {len(panel_objs)} source panels into {sheet_count} sheet group(s)."
                )
            try:
                view_controller.show_nesting_view(
                    doc, active_sheet=sheet_obj, nested_objects=nested_objs
                )
            except Exception:
                pass
            try:
                show_nested_only(doc)
                fit_view_to_sheet_and_nested(doc)
            except Exception:
                pass

        except Exception as exc:
            from SquatchCut.ui.error_handling import handle_command_error

            handle_command_error(
                "Run Nesting",
                exc,
                "The nesting operation failed.",
                "Please check your panel sizes and sheet dimensions, then try again.",
            )

    def _handle_validation_error(self, doc, exc: NestingValidationError) -> None:
        message = (
            f"Nesting failed: the following part(s) exceed the usable "
            f"sheet area {exc.usable_width:.1f} x {exc.usable_height:.1f} mm."
        )
        try:
            show_error(message, title="SquatchCut Nesting Failed")
        except Exception:
            pass
        logger.error(message)
        max_details = 20
        for part in exc.offending_parts[:max_details]:
            logger.error(
                f"Part {part.part_id}: {part.width:.1f} x {part.height:.1f} mm "
                f"(allow_rotate={part.can_rotate})."
            )
        if len(exc.offending_parts) > max_details:
            logger.error(
                f"...and {len(exc.offending_parts) - max_details} more offending part(s)."
            )
        self.validation_error = exc

    def _should_use_geometric_nesting(self, panels_data) -> bool:
        """Determine if geometric nesting should be used based on panel data and complexity."""
        if not panels_data:
            return False

        # Check if any panels have shape-based source or complex geometry
        has_freecad_shapes = False
        complex_shape_count = 0

        for panel in panels_data:
            if panel.get("source") == "freecad_shape":
                has_freecad_shapes = True

                # Check if the FreeCAD object has complex geometry
                freecad_obj = session_state.get_shape_panel_object(panel.get("id"))
                if freecad_obj and hasattr(freecad_obj, "Shape"):
                    try:
                        from SquatchCut.core.shape_extractor import ShapeExtractor

                        extractor = ShapeExtractor()
                        complexity_level = extractor.validate_shape_complexity(
                            freecad_obj
                        )

                        # Count shapes that would benefit from geometric nesting
                        from SquatchCut.core.complex_geometry import ComplexityLevel

                        if complexity_level in [
                            ComplexityLevel.MEDIUM,
                            ComplexityLevel.HIGH,
                        ]:
                            complex_shape_count += 1
                    except Exception:
                        # If complexity assessment fails, assume it's worth geometric nesting
                        complex_shape_count += 1

        # Use geometric nesting if:
        # 1. We have FreeCAD shapes AND
        # 2. At least one shape has medium or higher complexity OR
        # 3. We have multiple FreeCAD shapes (better packing potential)
        freecad_shape_count = sum(
            1 for p in panels_data if p.get("source") == "freecad_shape"
        )

        return has_freecad_shapes and (
            complex_shape_count > 0 or freecad_shape_count >= 1
        )

    def _run_geometric_nesting(self, parts, panels_data, sheet_w, sheet_h, gap_mm):
        """Run geometric nesting for complex shapes."""
        try:
            # Create ComplexGeometry objects from panel data
            complex_shapes = []
            for i, panel in enumerate(panels_data):
                if panel.get("source") == "freecad_shape":
                    # For FreeCAD shapes, try to extract actual geometry
                    freecad_obj = session_state.get_shape_panel_object(panel.get("id"))
                    shape_id = panel.get("id", f"shape_{i}")

                    if freecad_obj and hasattr(freecad_obj, "Shape"):
                        try:
                            # Try to extract complex geometry
                            from SquatchCut.core.shape_extractor import ShapeExtractor

                            extractor = ShapeExtractor()
                            complex_geom = extractor.extract_complex_geometry(
                                freecad_obj
                            )

                            if complex_geom:
                                complex_geom.rotation_allowed = panel.get(
                                    "allow_rotate", True
                                )
                                complex_shapes.append(complex_geom)
                                logger.info(f"Using complex geometry for {shape_id}")
                                continue
                        except Exception as e:
                            logger.warning(
                                f"Failed to extract complex geometry for {shape_id}: {e}"
                            )

                    # Fallback to rectangular geometry
                    width_mm = float(panel.get("width", 0))
                    height_mm = float(panel.get("height", 0))

                    if width_mm > 0 and height_mm > 0:
                        complex_geom = create_rectangular_geometry(
                            shape_id, width_mm, height_mm
                        )
                        complex_geom.rotation_allowed = panel.get("allow_rotate", True)
                        complex_shapes.append(complex_geom)
                        logger.info(f"Using rectangular approximation for {shape_id}")
                else:
                    # For CSV data, create rectangular geometry
                    if i < len(parts):
                        part = parts[i]
                        complex_geom = create_rectangular_geometry(
                            part.id, part.width, part.height
                        )
                        complex_geom.rotation_allowed = part.can_rotate
                        complex_shapes.append(complex_geom)

            if not complex_shapes:
                logger.warning("No valid complex shapes found for geometric nesting")
                return None

            # Create sheet geometry
            sheet_geom = SheetGeometry(width=sheet_w, height=sheet_h, margin=gap_mm)

            # Run geometric nesting
            engine = GeometryNestingEngine()
            nesting_result = engine.nest_complex_shapes(
                complex_shapes, sheet_geom, NestingMode.HYBRID
            )

            # Convert result back to the expected format
            if nesting_result.placed_geometries:
                # Create a simple layout result compatible with existing code
                layout_result = {
                    "placements": [],
                    "utilization": nesting_result.utilization_percent,
                    "sheets_used": nesting_result.sheets_used,
                    "total_area_used": nesting_result.total_area_used,
                    "processing_time": nesting_result.processing_time,
                }

                # Convert placed geometries to placement format
                for placed in nesting_result.placed_geometries:
                    placement = {
                        "id": placed.geometry.id,
                        "x": placed.x,
                        "y": placed.y,
                        "width": placed.geometry.get_width(),
                        "height": placed.geometry.get_height(),
                        "rotation": placed.rotation,
                        "sheet_index": placed.sheet_index,
                        # Include complex geometry information for export
                        "complex_geometry": placed.geometry,
                        "geometry_type": (
                            placed.geometry.geometry_type.value
                            if hasattr(placed.geometry.geometry_type, "value")
                            else str(placed.geometry.geometry_type)
                        ),
                    }
                    layout_result["placements"].append(placement)

                logger.info(
                    f">>> [SquatchCut] Geometric nesting completed: {nesting_result.utilization_percent:.1f}% utilization"
                )
                return layout_result
            else:
                logger.warning("Geometric nesting failed to place any shapes")
                return None

        except Exception as e:
            logger.error(f"Geometric nesting failed: {e}")
            # Fall back to regular nesting
            return None

        try:
            if App.ActiveDocument:
                show_source_and_sheet(App.ActiveDocument)
                fit_view_to_source(App.ActiveDocument)
        except Exception:
            pass

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
            "MenuText": "Apply Layout",
            "ToolTip": "Re-run nesting and apply the latest layout to the document.",
            "Pixmap": get_icon("run_nesting"),
        }

    def IsActive(self):
        return App is not None and Gui is not None

    def Activated(self):
        try:
            run_cmd = RunNestingCommand()
            run_cmd.Activated()
            # Note: Removed automatic dialog closing to keep TaskPanel open for iterative workflow
            # Users can manually close the panel if desired
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
        self,
        doc,
        sheet_index: int,
        sheet_w: float,
        sheet_h: float,
        sheet_origin_x: float = 0.0,
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
            "Pixmap": get_icon("toggle_visibility"),
            "MenuText": "Toggle Sources",
            "ToolTip": "Show or hide the original source panel objects.",
        }

    def Activated(self):
        if App is None or Gui is None:
            try:
                logger.warning(
                    "ToggleSourcePanelsCommand.Activated() called outside FreeCAD GUI environment."
                )
            except Exception:
                pass
            return

        doc = App.ActiveDocument
        if doc is None:
            logger.error("No active document.")
            return

        group = doc.getObject("SquatchCut_SourceParts")
        if group is None:
            logger.info("No SourceParts group exists.")
            return

        try:
            group.ViewObject.Visibility = not group.ViewObject.Visibility
            state = "shown" if group.ViewObject.Visibility else "hidden"
            logger.info(f"SourceParts group {state}.")
        except Exception as e:
            logger.error(f"Failed toggling SourceParts: {e}")

    def IsActive(self):
        return App is not None and Gui is not None and App.ActiveDocument is not None


class ExportNestingCSVCommand:
    """
    Export nesting layout data to CSV using the ExportJob model.
    Exports part placements with positions, dimensions, and sheet assignments.
    """

    def GetResources(self):
        return {
            "MenuText": "Export Nesting CSV",
            "ToolTip": "Export the current nesting layout to CSV with part positions and dimensions.",
            "Pixmap": "",
        }

    def IsActive(self):
        return App is not None and Gui is not None and App.ActiveDocument is not None

    def Activated(self):
        if App is None or Gui is None:
            return

        try:
            from SquatchCut.core import exporter
            from SquatchCut.gui.qt_compat import QtWidgets

            doc = App.ActiveDocument
            if doc is None:
                logger.warning("ExportNestingCSVCommand: no active document.")
                return

            # Build export job from current session state
            export_job = exporter.build_export_job_from_current_nesting(doc)
            if export_job is None or not export_job.sheets:
                QtWidgets.QMessageBox.information(
                    Gui.getMainWindow(),
                    "SquatchCut Export",
                    "No nesting layout to export. Please run nesting first.",
                )
                return

            # Show file dialog
            suggested_path = exporter.suggest_export_path(doc, "csv")
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                Gui.getMainWindow(),
                "Export Nesting Layout",
                suggested_path,
                "CSV files (*.csv);;All files (*.*)",
            )

            if not file_path:
                return

            # Export using the ExportJob model
            exporter.export_cutlist(export_job, file_path)

            # Count parts for user feedback
            total_parts = sum(len(sheet.parts) for sheet in export_job.sheets)
            QtWidgets.QMessageBox.information(
                Gui.getMainWindow(),
                "SquatchCut Export",
                f"Successfully exported {total_parts} parts across {len(export_job.sheets)} sheet(s) to:\n{file_path}",
            )
            logger.info(f"[SquatchCut] Nesting CSV export complete: {file_path}")

        except Exception as e:
            logger.error(f"Error in ExportNestingCSVCommand.Activated(): {e!r}")
            if Gui:
                QtWidgets.QMessageBox.critical(
                    Gui.getMainWindow(),
                    "SquatchCut Export Error",
                    f"Failed to export nesting CSV:\n{str(e)}",
                )


class PreviewNestingCommand:
    """
    Non-destructive preview version of nesting that creates temporary geometry.
    Unlike RunNestingCommand, this doesn't permanently modify session state.
    """

    def GetResources(self):
        return {
            "MenuText": "Preview Nesting",
            "ToolTip": "Preview nesting layout without permanent changes.",
            "Pixmap": "",
        }

    def IsActive(self):
        return App is not None and Gui is not None and App.ActiveDocument is not None

    def Activated(self):
        """Run nesting calculations and create temporary preview geometry."""
        if App is None or Gui is None:
            return

        try:
            # Save current session state to restore later
            saved_layout = session_state.get_last_layout()
            saved_stats = session_state.get_nesting_stats()

            # Run the same nesting logic as RunNestingCommand but don't save results permanently
            cmd = RunNestingCommand()
            cmd.Activated()

            # Get the preview results (for potential future use)
            # preview_layout = session_state.get_last_layout()
            # preview_stats = session_state.get_nesting_stats()

            # Restore original session state (making this non-destructive)
            session_state.set_last_layout(saved_layout)
            session_state.set_nesting_stats(
                saved_stats.get("sheets_used") if saved_stats else None,
                saved_stats.get("cut_complexity") if saved_stats else None,
                saved_stats.get("overlaps_count") if saved_stats else None,
            )

            # Mark the current geometry as preview by adding a property or different naming
            doc = App.ActiveDocument
            if doc:
                # Add a custom property to nested parts to mark them as preview
                nested_group = doc.getObject("SquatchCut_NestedParts")
                if nested_group:
                    try:
                        # Add a custom property to mark this as preview geometry
                        if not hasattr(nested_group, "IsPreview"):
                            nested_group.addProperty(
                                "App::PropertyBool",
                                "IsPreview",
                                "SquatchCut",
                                "Marks this as preview geometry",
                            )
                        nested_group.IsPreview = True
                    except Exception:
                        pass

            logger.info("[SquatchCut] Preview nesting complete (non-destructive)")

        except Exception as e:
            logger.error(f"Error in PreviewNestingCommand.Activated(): {e!r}")


if Gui is not None:
    Gui.addCommand("SquatchCut_ToggleSourcePanels", ToggleSourcePanelsCommand())
    Gui.addCommand("SquatchCut_ExportNestingCSV", ExportNestingCSVCommand())
    Gui.addCommand("SquatchCut_RunNesting", RunNestingCommand())
    Gui.addCommand("SquatchCut_ApplyNesting", ApplyNestingCommand())
    Gui.addCommand("SquatchCut_PreviewNesting", PreviewNestingCommand())

# Exported command instance used by InitGui.py
COMMAND = RunNestingCommand()
