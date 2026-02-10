"""Unified SquatchCut task panel (Controller)."""

from __future__ import annotations

import webbrowser
from collections.abc import Callable
from typing import Optional

from SquatchCut import settings
from SquatchCut.core import exporter, logger, session, session_state, view_controller
from SquatchCut.core import units as sc_units
from SquatchCut.core.nesting import (
    compute_utilization_for_sheets,
    derive_sheet_sizes_for_layout,
    estimate_cut_counts_for_sheets,
)
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.commands import cmd_run_nesting
from SquatchCut.gui.qt_compat import QtCore, QtWidgets
from SquatchCut.gui.taskpanel_banner import SheetWarningBanner
from SquatchCut.gui.taskpanel_input import InputGroupWidget
from SquatchCut.gui.taskpanel_nesting import NestingGroupWidget
from SquatchCut.gui.taskpanel_output import TaskPanelOutputWidget
from SquatchCut.gui.taskpanel_sheet import SheetConfigWidget
from SquatchCut.ui.messages import show_error


class SquatchCutTaskPanel:
    """
    Consolidated Task panel acting as Controller for sub-widgets.
    """

    FALLBACK_SHEET_SIZE_MM = (1220.0, 2440.0)
    FALLBACK_MATCH_TOLERANCE_MM = 2.0
    _test_force_measurement_system: Optional[str] = None

    def __init__(self, doc=None):
        self._prefs = SquatchCutPreferences()
        effective_doc = doc or (App.ActiveDocument if App is not None else None)
        test_override = self.__class__._test_force_measurement_system
        self.__class__._test_force_measurement_system = None
        doc_units = (
            test_override
            if test_override in ("metric", "imperial")
            else session.detect_document_measurement_system(effective_doc)
        )

        self.doc = effective_doc
        self._close_callback: Optional[Callable[[], None]] = None

        self.has_csv_data = False
        self.is_sheet_valid = False
        self.overlaps_count = 0

        self._sheet_warning_active = False

        self.form = QtWidgets.QWidget()
        self._build_ui()

        # Hydrate and Apply
        self._initial_state = self._compute_initial_state(effective_doc, doc_units)
        self.measurement_system = self._initial_state["measurement_system"]
        self._apply_initial_state(self._initial_state)

        # Force unit update if mismatch (fixes initialization default)
        if self.sheet_widget.units_combo.currentData() != self.measurement_system:
            idx = self.sheet_widget.units_combo.findData(self.measurement_system)
            if idx >= 0:
                self.sheet_widget.units_combo.setCurrentIndex(idx)

    def set_close_callback(self, callback: Callable[[], None]) -> None:
        self._close_callback = callback

    def _notify_close(self) -> None:
        if self._close_callback:
            try:
                self._close_callback()
            except Exception:
                pass
            self._close_callback = None

    def _build_ui(self) -> None:
        outer_layout = QtWidgets.QVBoxLayout(self.form)
        outer_layout.setContentsMargins(6, 6, 6, 6)
        outer_layout.setSpacing(4)

        # Scroll Area Setup
        layout = outer_layout
        scroll_area = None
        scroll_cls = getattr(QtWidgets, "QScrollArea", None)
        try:
            scroll_area = scroll_cls() if scroll_cls is not None else None
        except Exception:
            scroll_area = None
        if scroll_area is not None and hasattr(scroll_area, "setWidgetResizable"):
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            outer_layout.addWidget(scroll_area)
            content = QtWidgets.QWidget()
            scroll_area.setWidget(content)
            layout = QtWidgets.QVBoxLayout(content)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)
        else:
            layout.setSpacing(8)

        # 1. Warning Banner
        self.sheet_warning_widget = SheetWarningBanner()
        layout.addWidget(self.sheet_warning_widget)

        # 2. Input Group
        self.input_widget = InputGroupWidget(self._prefs)
        self.input_widget.csv_imported.connect(self._on_csv_imported)
        self.input_widget.shapes_selected.connect(self._on_shapes_selected)
        self.input_widget.data_changed.connect(self._on_data_changed)
        layout.addWidget(self.input_widget)

        # 3. Sheet Group
        self.sheet_widget = SheetConfigWidget(self._prefs)
        self.sheet_widget.units_changed.connect(self._on_units_changed)
        self.sheet_widget.validation_changed.connect(self._on_sheet_validation_changed)
        self.sheet_widget.config_changed.connect(self._on_config_changed)
        layout.addWidget(self.sheet_widget)

        # 4. Nesting Group
        self.nesting_widget = NestingGroupWidget(self._prefs)
        self.nesting_widget.run_requested.connect(self.on_apply_clicked)
        self.nesting_widget.preview_requested.connect(self.on_preview_clicked)
        self.nesting_widget.settings_changed.connect(self._on_nesting_settings_changed)
        layout.addWidget(self.nesting_widget)

        # 5. Output/Results Group
        self.output_widget = TaskPanelOutputWidget()
        self.output_widget.btnViewSource.clicked.connect(self._on_view_source_clicked)
        self.output_widget.btnViewSheets.clicked.connect(self._on_view_sheets_clicked)
        self.output_widget.show_sheet_check.toggled.connect(self._on_view_toggled)
        self.output_widget.show_nested_check.toggled.connect(self._on_view_toggled)
        self.output_widget.show_part_labels_check.toggled.connect(
            self._on_nesting_view_toggled
        )
        self.output_widget.simplified_view_check.toggled.connect(
            self._on_nesting_view_toggled
        )
        self.output_widget.show_source_button.clicked.connect(self.on_show_source_panels)
        self.output_widget.export_button.clicked.connect(self.on_export_clicked)
        self.output_widget.include_labels_check.stateChanged.connect(
            self._on_export_options_changed
        )
        self.output_widget.include_dimensions_check.stateChanged.connect(
            self._on_export_options_changed
        )
        self.output_widget.include_leader_lines_check.stateChanged.connect(
            self._on_export_options_changed
        )
        self.output_widget.btnExportCutlist.clicked.connect(
            self.on_export_cutlist_clicked
        )
        layout.addWidget(self.output_widget)

        # Report bug link
        report_row = QtWidgets.QHBoxLayout()
        report_row.addStretch(1)
        self.report_bug_button = QtWidgets.QPushButton("Report a Bug")
        self.report_bug_button.setFlat(True)
        self.report_bug_button.clicked.connect(self.on_report_bug_clicked)
        report_row.addWidget(self.report_bug_button)
        layout.addLayout(report_row)

        layout.addStretch(1)

    def _compute_initial_state(
        self, doc, doc_measurement_system: Optional[str] = None
    ) -> dict:
        override = (
            doc_measurement_system
            if doc_measurement_system in ("metric", "imperial")
            else None
        )
        try:
            settings.hydrate_from_params(measurement_override=override)
        except Exception:
            pass

        measurement_system = override or session_state.get_measurement_system()

        # Doc sync (Simplified)
        if doc is not None:
            try:
                # We need defaults to sync?
                w, h = self._prefs.get_default_sheet_size_mm(measurement_system)
                session.sync_state_from_doc(doc, measurement_system, (w, h))
            except Exception:
                pass

        measurement_system = override or session_state.get_measurement_system()
        session_state.set_measurement_system(measurement_system)
        sc_units.set_units("in" if measurement_system == "imperial" else "mm")

        # Gather state for widgets
        sheet_w, sheet_h = session_state.get_sheet_size()
        kerf_mm = session_state.get_kerf_mm()
        margin_mm = session_state.get_gap_mm()

        return {
            "measurement_system": measurement_system,
            "sheet_width_mm": sheet_w,
            "sheet_height_mm": sheet_h,
            "kerf_mm": kerf_mm,
            "margin_mm": margin_mm,
            "kerf_width_mm": session_state.get_kerf_width_mm(),
            "cut_mode": session_state.get_optimize_for_cut_path(),
            "job_allow_rotate": (
                session_state.get_job_allow_rotate()
                if session_state.get_job_allow_rotate() is not None
                else session_state.get_default_allow_rotate()
            ),
            "mode": session_state.get_optimization_mode(),
            "csv_units": self._prefs.get_csv_units(measurement_system),
            "include_labels": self._prefs.get_export_include_labels(),
            "include_dimensions": self._prefs.get_export_include_dimensions(),
            "panels": session_state.get_panels(),
            "sheet_mode": session_state.get_sheet_mode(),
        }

    def _apply_initial_state(self, state: dict) -> None:
        self.input_widget.apply_state(state)
        self.sheet_widget.apply_state(state)
        self.nesting_widget.apply_state(state)

        self.output_widget.include_labels_check.setChecked(bool(state["include_labels"]))
        self.output_widget.include_dimensions_check.setChecked(
            bool(state["include_dimensions"])
        )

        # Initialize leader lines from preferences (default to False)
        try:
            include_leader_lines = self._prefs.get_export_include_leader_lines()
        except Exception:
            include_leader_lines = False
        self.output_widget.include_leader_lines_check.setChecked(include_leader_lines)

        # Initialize nesting view controls with user preferences
        try:
            self.output_widget.show_part_labels_check.setChecked(
                self._prefs.get_nesting_show_part_labels()
            )
            self.output_widget.simplified_view_check.setChecked(
                self._prefs.get_nesting_simplified_view()
            )
        except Exception as e:
            logger.warning(f"Failed to initialize nesting view controls: {e}")

        self._refresh_summary()
        self._validate_readiness()

    # --- Signal Handlers ---

    def _on_csv_imported(self):
        self.set_status("CSV Imported.")
        self.has_csv_data = True
        self._validate_readiness()

    def _on_shapes_selected(self):
        self.set_status("Shapes Selected.")
        self.has_csv_data = True  # Treat shape selection like CSV data
        self._validate_readiness()

    def _on_data_changed(self):
        self.has_csv_data = bool(session_state.get_panels())
        self._validate_readiness()

    def _on_units_changed(self):
        # Propagate to other widgets
        self.input_widget.on_units_changed()
        self.nesting_widget.update_unit_labels()
        self._refresh_summary()  # Update labels if needed?

        # Re-apply defaults if doc exists?
        # Logic from old taskpanel... simplified here.
        # Just ensure UI consistency
        self.measurement_system = session_state.get_measurement_system()

    def _on_sheet_validation_changed(self, valid: bool):
        self.is_sheet_valid = valid
        self._validate_readiness()

    def _on_config_changed(self):
        self._update_cut_mode_sheet_warning()
        self._validate_readiness()

    def _on_nesting_settings_changed(self):
        self._update_cut_mode_sheet_warning()
        self._refresh_summary()  # Update labels (Mode)

    def _update_cut_mode_sheet_warning(self) -> None:
        advanced = session_state.is_job_sheets_mode()
        sheet_count = 0
        for entry in session_state.get_job_sheets() or []:
            qty = entry.get("quantity", 1)
            try:
                sheet_count += max(1, int(qty))
            except Exception:
                sheet_count += 1

        uses_cut_modes = bool(self.nesting_widget.cut_mode_check.isChecked()) or (
            self.nesting_widget.mode_combo.currentData() == "cuts"
        )
        show_warning = advanced and sheet_count > 1 and uses_cut_modes

        warning_message = (
            "Advanced job sheets with cut-friendly or guillotine layouts are partially supported. "
            "Sheets are processed sequentially; review the layout to ensure each configured sheet was used."
        )
        self.sheet_warning_widget.update_warning(show_warning, warning_message)
        self._sheet_warning_active = show_warning

    def _validate_readiness(self):
        # Update sheet warning state
        self._update_cut_mode_sheet_warning()

        # Update Run buttons based on state
        can_run = self.has_csv_data and self.is_sheet_valid
        self.nesting_widget.set_run_enabled(can_run)

        if not self.has_csv_data:
            self.set_status("No parts loaded.")
        elif not self.is_sheet_valid:
            self.set_status("Invalid sheet config.")
        elif self.overlaps_count > 0:
            self.set_status("Overlaps detected.")
        else:
            self.set_status("Ready.")

    def set_status(self, msg):
        self.output_widget.set_status(msg)

    def update_run_button_state(self):
        """Legacy alias for _validate_readiness (used by tests)."""
        self._validate_readiness()

    # --- Actions ---

    def _ensure_document(self):
        doc = self.doc or App.ActiveDocument
        if doc is None:
            try:
                doc = App.newDocument("SquatchCut")
                self.doc = doc
            except Exception:
                return None
        return doc

    def _cleanup_preview_geometry(self, doc) -> None:
        """Clean up any existing preview or applied geometry."""
        if doc is None:
            return
        try:
            view_controller.clear_squatchcut_groups(doc)
        except Exception as exc:
            logger.warning(f"Cleanup failed: {exc}")

    def _cleanup_preview_artifacts(self, doc) -> None:
        """Clean up preview-specific artifacts before applying."""
        if doc is None:
            return
        try:
            # Look for geometry marked as preview and clean it up
            nested_group = doc.getObject("SquatchCut_NestedParts")
            if (
                nested_group
                and hasattr(nested_group, "IsPreview")
                and nested_group.IsPreview
            ):
                # Clear preview geometry before applying
                view_controller.clear_squatchcut_groups(doc)
                logger.info("[SquatchCut] Cleaned up preview artifacts before apply")
        except Exception as exc:
            logger.warning(f"Preview cleanup failed: {exc}")

    def on_preview_clicked(self):
        """Run non-destructive preview that doesn't permanently change session state."""
        doc = self._ensure_document()
        if not doc:
            return

        # Clean up any existing geometry
        self._cleanup_preview_geometry(doc)

        # Use the preview command instead of the regular nesting command
        try:
            from SquatchCut.gui.commands.cmd_run_nesting import PreviewNestingCommand

            cmd = PreviewNestingCommand()
            cmd.Activated()

            # Update UI with preview results (but don't save to session permanently)
            self._refresh_summary()
            self._validate_readiness()

        except Exception as exc:
            show_error(f"Preview failed:\n{exc}", title="SquatchCut")
            return

    def on_apply_clicked(self):
        """Apply nesting permanently, cleaning up any preview artifacts first."""
        doc = self._ensure_document()
        if not doc:
            return

        # Clean up preview artifacts before applying
        self._cleanup_preview_artifacts(doc)

        # Run the regular nesting command for permanent application
        self._run_nesting(apply_to_doc=True, doc=doc)

    def _run_nesting(self, apply_to_doc: bool = True, doc=None):
        # Settings already applied to session via widgets
        try:
            cmd = cmd_run_nesting.RunNestingCommand()
            cmd.Activated()
            if getattr(cmd, "validation_error", None):
                self.set_status("Nesting failed: validation error.")
                return
        except Exception as exc:
            show_error(f"Nesting failed:\n{exc}", title="SquatchCut")
            return

        self._refresh_summary()
        self._validate_readiness()

        if apply_to_doc:
            try:
                Gui.Control.closeDialog()
            except Exception:
                pass

    def _refresh_summary(self):
        layout = session_state.get_last_layout() or []
        sheet_w, sheet_h = session_state.get_sheet_size()

        if not layout:
            return

        fallback_width, fallback_height = self.FALLBACK_SHEET_SIZE_MM
        target_width = float(sheet_w) if sheet_w else fallback_width
        target_height = float(sheet_h) if sheet_h else fallback_height

        sheet_sizes = derive_sheet_sizes_for_layout(
            session_state.get_sheet_mode(),
            session_state.get_job_sheets(),
            target_width,
            target_height,
            layout,
        )
        if not sheet_sizes:
            sheet_sizes = [(target_width, target_height)]

        util = compute_utilization_for_sheets(layout, sheet_sizes)
        cuts = estimate_cut_counts_for_sheets(layout, sheet_sizes)

        self.output_widget.sheets_label.setText(
            f"Sheets used: {util.get('sheets_used', 0)}"
        )
        self.output_widget.utilization_label.setText(
            f"Utilization: {util.get('utilization_percent', 0.0):.1f}%"
        )
        self.output_widget.cutcount_label.setText(
            f"Estimated cuts: {cuts.get('total', 0)}"
        )
        per_sheet = util.get("per_sheet_stats") or []
        if per_sheet:
            min_util = min(s["utilization_percent"] for s in per_sheet)
            max_util = max(s["utilization_percent"] for s in per_sheet)
            if len(per_sheet) == 1:
                range_text = f"{min_util:.1f}%"
            else:
                range_text = f"{min_util:.1f}%–{max_util:.1f}%"
        else:
            range_text = "–"
        self.output_widget.sheet_utilization_label.setText(range_text)

        stats = session_state.get_nesting_stats()
        self.overlaps_count = stats.get("overlaps_count", 0) or 0
        if self.overlaps_count > 0:
            self.output_widget.overlaps_label.setText(
                f"{self.overlaps_count} conflicts!"
            )
            self.output_widget.overlaps_label.setStyleSheet("color: red;")
        else:
            self.output_widget.overlaps_label.setText("None")
            self.output_widget.overlaps_label.setStyleSheet("")

    def _on_export_options_changed(self):
        self._prefs.set_export_include_labels(
            self.output_widget.include_labels_check.isChecked()
        )
        self._prefs.set_export_include_dimensions(
            self.output_widget.include_dimensions_check.isChecked()
        )
        self._prefs.set_export_include_leader_lines(
            self.output_widget.include_leader_lines_check.isChecked()
        )

    def on_export_clicked(self):
        export_job = exporter.build_export_job_from_current_nesting(
            self._ensure_document()
        )
        if not export_job:
            self.set_status("No layout to export.")
            return

        fmt = self.output_widget.export_format_combo.currentData()
        # ... logic similar to before, simplified ...
        initial_path = exporter.suggest_export_path(
            self._ensure_document(),
            "." + fmt.split("_")[-1] if "_" in fmt else "." + fmt,
        )
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            None, "Export", initial_path, "All files (*.*)"
        )
        if not file_path:
            return

        try:
            if fmt == "cutlist_txt":
                exporter.export_cutlist(export_job, file_path, as_text=True)
            elif fmt == "cutlist_csv":
                exporter.export_cutlist(export_job, file_path)
            elif fmt == "svg":
                exporter.export_nesting_to_svg(
                    export_job,
                    file_path,
                    include_labels=self.output_widget.include_labels_check.isChecked(),
                    include_dimensions=self.output_widget.include_dimensions_check.isChecked(),
                    include_leader_lines=self.output_widget.include_leader_lines_check.isChecked(),
                )
            elif fmt == "dxf":
                exporter.export_nesting_to_dxf(export_job, file_path)

            self.set_status(f"Exported to {file_path}")
        except Exception as e:
            self.set_status("Export failed.")
            logger.error(f"Export error: {e}")

    # View toggles (simplified)
    def _on_view_source_clicked(self):
        self.output_widget.btnViewSource.setChecked(True)
        self.output_widget.btnViewSheets.setChecked(False)
        view_controller.show_source_view(self._ensure_document())

    def _on_view_sheets_clicked(self):
        self.output_widget.btnViewSource.setChecked(False)
        self.output_widget.btnViewSheets.setChecked(True)
        view_controller.show_nesting_view(self._ensure_document())

    def on_show_source_panels(self):
        view_controller.show_source_view(self._ensure_document())

    def _on_view_toggled(self):
        # Implement visibility logic if needed
        pass

    def _on_nesting_view_toggled(self):
        """Handle nesting view preference changes and trigger view refresh."""
        try:
            # Update preferences
            prefs = self._prefs
            prefs.set_nesting_show_part_labels(
                self.output_widget.show_part_labels_check.isChecked()
            )
            prefs.set_nesting_simplified_view(
                self.output_widget.simplified_view_check.isChecked()
            )

            # Trigger view refresh if we have nested parts
            if hasattr(self, "_last_nesting_result") and self._last_nesting_result:
                self._refresh_nesting_view()

        except Exception as e:
            logger.warning(f"Failed to update nesting view preferences: {e}")

    def _refresh_nesting_view(self):
        """Refresh the nesting view with current preferences."""
        try:
            # Trigger a view refresh by calling the view controller
            from SquatchCut.core import view_controller

            doc = self._ensure_document()
            if doc:
                view_controller.rebuild_nested_layout_view(doc)
        except Exception as e:
            logger.warning(f"Failed to refresh nesting view: {e}")

    def on_export_cutlist_clicked(self):
        try:
            Gui.runCommand("SquatchCut_ExportCutlist")
        except Exception:
            pass

    def on_report_bug_clicked(self):
        webbrowser.open("https://github.com/stevenfarmer/SquatchCut/issues")

    # Standard API
    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

    def accept(self):
        try:
            Gui.Control.closeDialog()
        except Exception:
            pass
        self._notify_close()

    def reject(self):
        try:
            Gui.Control.closeDialog()
        except Exception:
            pass
        self._notify_close()

    def getIcon(self):
        """Return the icon for this TaskPanel."""
        from SquatchCut.gui.icons import get_icon

        return get_icon("main")

    def needsFullSpace(self):
        """Return True if this TaskPanel needs full space."""
        return True

    def isAllowedAlterDocument(self):
        """Return True if this TaskPanel is allowed to alter the document."""
        return True

    def isAllowedAlterView(self):
        """Return True if this TaskPanel is allowed to alter the view."""
        return True


# Factory
def create_main_panel_for_tests():
    SquatchCutTaskPanel._test_force_measurement_system = (
        session_state.get_measurement_system()
    )
    return SquatchCutTaskPanel()
