"""Unified SquatchCut task panel for sheet setup, CSV import, optimization choice, nesting, and results summary."""

from __future__ import annotations

import os
from typing import List

try:
    import FreeCAD as App
    import FreeCADGui as Gui
except Exception:
    App = None
    Gui = None
import webbrowser

from SquatchCut.gui.qt_compat import QtWidgets, QtCore

from SquatchCut.core import session, session_state
from SquatchCut.core.nesting import compute_utilization, estimate_cut_counts
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core import exporter
from SquatchCut.gui.commands.cmd_import_csv import run_csv_import
from SquatchCut.gui.commands import cmd_add_shapes, cmd_run_nesting
from SquatchCut.ui.messages import show_error


class SquatchCutTaskPanel:
    """
    Consolidated Task panel for SquatchCut:
    - Sheet configuration (size, kerf, margin, rotation)
    - CSV import and part table
    - Optimization mode selection (material vs cuts)
    - View toggles and run/preview controls
    - Results summary (sheets, utilization, estimated cuts, unplaced)
    """

    MM_PER_INCH = 25.4

    def __init__(self, doc=None):
        self.doc = doc or App.ActiveDocument
        self._last_csv_path: str | None = None
        self.has_csv_data = False
        self.has_valid_sheet = False
        self.has_valid_kerf = False
        self.overlaps_count = 0
        self._prefs = SquatchCutPreferences()
        self.measurement_system = self._prefs.get_measurement_system()
        self._presets: list[tuple[str, tuple[float, float] | None]] = [
            ("Custom…", None),
            ("1220 x 2440 mm (4x8 ft)", (1220.0, 2440.0)),
            ("1525 x 3050 mm (5x10 ft)", (1525.0, 3050.0)),
        ]

        if self.doc is not None:
            try:
                session.sync_state_from_doc(self.doc)
            except Exception:
                pass

        self.form = QtWidgets.QWidget()
        self._build_ui()
        self._load_initial_state_from_session()

    # ---------------- UI builders ----------------

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        layout.addWidget(self._build_general_group())
        layout.addWidget(self._build_nesting_group())
        layout.addWidget(self._build_cut_optimization_group())
        layout.addWidget(self._build_stats_group())
        layout.addWidget(self._build_export_group())

        # Bottom action buttons
        buttons_row = QtWidgets.QHBoxLayout()
        buttons_row.addStretch(1)
        self.preview_button = QtWidgets.QPushButton("Preview SquatchCut")
        self.run_button = QtWidgets.QPushButton("Apply SquatchCut")
        self.show_source_button = QtWidgets.QPushButton("Show Source Panels")
        self.preview_button.setToolTip("Generate a preview of the SquatchCut layout without modifying the document.")
        self.run_button.setToolTip("Create geometry in the FreeCAD document from the current SquatchCut layout.")
        self.show_source_button.setToolTip("Hide nested sheets and show source panels.")
        buttons_row.addWidget(self.preview_button)
        buttons_row.addWidget(self.run_button)
        buttons_row.addWidget(self.show_source_button)
        layout.addLayout(buttons_row)

        # Report bug link/button (low visual weight)
        report_row = QtWidgets.QHBoxLayout()
        report_row.addStretch(1)
        self.report_bug_button = QtWidgets.QPushButton("Report a Bug")
        self.report_bug_button.setFlat(True)
        self.report_bug_button.setToolTip("Open the SquatchCut GitHub issue tracker to report a bug or request a feature.")
        report_row.addWidget(self.report_bug_button)
        layout.addLayout(report_row)

        # Status label
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # Wire actions
        self.preview_button.clicked.connect(lambda: self._run_nesting(apply_to_doc=False))
        self.run_button.clicked.connect(lambda: self._run_nesting(apply_to_doc=True))
        self.show_source_button.clicked.connect(self.on_show_source_panels)
        self.report_bug_button.clicked.connect(self.on_report_bug_clicked)
        self._set_run_buttons_enabled(False)

    def _build_general_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("General")
        vbox = QtWidgets.QVBoxLayout(group)

        form = QtWidgets.QFormLayout()
        self.units_combo = QtWidgets.QComboBox()
        self.units_combo.addItem("Metric (mm)", "metric")
        self.units_combo.addItem("Imperial (in)", "imperial")
        form.addRow("Units:", self.units_combo)

        self.preset_combo = QtWidgets.QComboBox()
        for label, _ in self._presets:
            self.preset_combo.addItem(label)
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItem("Material (minimize waste)", "material")
        self.mode_combo.addItem("Cuts (minimize number of cuts)", "cuts")
        self.mode_combo.setToolTip(
            "Material: prioritize yield. Cuts: row/column layout to approximate fewer saw cuts."
        )
        form.addRow("Preset:", self.preset_combo)
        form.addRow("Optimization:", self.mode_combo)

        vbox.addLayout(form)

        # Parts / CSV section
        top_row = QtWidgets.QHBoxLayout()
        self.load_csv_button = QtWidgets.QPushButton("Load parts CSV…")
        self.csv_path_label = QtWidgets.QLabel("No file loaded")
        self.csv_path_label.setStyleSheet("color: gray;")
        self.csv_path_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        top_row.addWidget(self.load_csv_button)
        top_row.addWidget(self.csv_path_label, 1)
        vbox.addLayout(top_row)

        csv_units_row = QtWidgets.QHBoxLayout()
        csv_units_row.addWidget(QtWidgets.QLabel("CSV units:"))
        self.csv_units_combo = QtWidgets.QComboBox()
        self.csv_units_combo.addItem("Metric (mm)", "metric")
        self.csv_units_combo.addItem("Imperial (in)", "imperial")
        csv_units_row.addWidget(self.csv_units_combo)
        csv_units_row.addStretch(1)
        vbox.addLayout(csv_units_row)

        self.parts_table = QtWidgets.QTableWidget()
        self.parts_table.setColumnCount(5)
        self.parts_table.setHorizontalHeaderLabels(
            ["Name", "Width (mm)", "Height (mm)", "Qty", "Allow rotate"]
        )
        self.parts_table.horizontalHeader().setStretchLastSection(True)
        self.parts_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.parts_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.parts_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        vbox.addWidget(self.parts_table)

        # View toggles
        view_layout = QtWidgets.QHBoxLayout()
        self.show_sheet_check = QtWidgets.QCheckBox("Show sheet boundary")
        self.show_nested_check = QtWidgets.QCheckBox("Show nested parts")
        self.show_sheet_check.setChecked(True)
        self.show_nested_check.setChecked(True)
        view_layout.addWidget(self.show_sheet_check)
        view_layout.addWidget(self.show_nested_check)
        view_layout.addStretch(1)
        vbox.addLayout(view_layout)

        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.units_combo.currentIndexChanged.connect(self._on_units_changed)
        self.load_csv_button.clicked.connect(self._choose_csv_file)
        self.show_sheet_check.toggled.connect(self._on_view_toggled)
        self.show_nested_check.toggled.connect(self._on_view_toggled)

        return group

    def _build_nesting_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Nesting")
        form = QtWidgets.QGridLayout(group)
        form.setColumnStretch(1, 1)

        self.sheet_width_label = QtWidgets.QLabel("Width (mm):")
        self.sheet_width_spin = QtWidgets.QDoubleSpinBox()
        self.sheet_width_spin.setRange(10.0, 10000.0)
        self.sheet_width_spin.setDecimals(1)
        self.sheet_width_spin.setSingleStep(10.0)
        self.sheet_width_spin.valueChanged.connect(self.update_run_button_state)

        self.sheet_height_label = QtWidgets.QLabel("Height (mm):")
        self.sheet_height_spin = QtWidgets.QDoubleSpinBox()
        self.sheet_height_spin.setRange(10.0, 10000.0)
        self.sheet_height_spin.setDecimals(1)
        self.sheet_height_spin.setSingleStep(10.0)
        self.sheet_height_spin.valueChanged.connect(self.update_run_button_state)

        self.kerf_label = QtWidgets.QLabel("Kerf width (mm):")
        self.kerf_spin = QtWidgets.QDoubleSpinBox()
        self.kerf_spin.setRange(0.0, 100.0)
        self.kerf_spin.setDecimals(2)
        self.kerf_spin.setSingleStep(0.1)

        self.margin_label = QtWidgets.QLabel("Edge margin (mm):")
        self.margin_spin = QtWidgets.QDoubleSpinBox()
        self.margin_spin.setRange(0.0, 100.0)
        self.margin_spin.setDecimals(2)
        self.margin_spin.setSingleStep(0.5)

        self.allow_90_check = QtWidgets.QCheckBox("Allow 90° rotation")
        self.allow_180_check = QtWidgets.QCheckBox("Allow 180° rotation")

        form.addWidget(self.sheet_width_label, 0, 0)
        form.addWidget(self.sheet_width_spin, 0, 1)
        form.addWidget(self.sheet_height_label, 0, 2)
        form.addWidget(self.sheet_height_spin, 0, 3)
        form.addWidget(self.kerf_label, 1, 0)
        form.addWidget(self.kerf_spin, 1, 1)
        form.addWidget(self.margin_label, 1, 2)
        form.addWidget(self.margin_spin, 1, 3)
        form.addWidget(self.allow_90_check, 2, 0, 1, 2)
        form.addWidget(self.allow_180_check, 2, 2, 1, 2)

        reset_row = QtWidgets.QHBoxLayout()
        reset_row.addStretch(1)
        self.reset_defaults_button = QtWidgets.QPushButton("Reset to Defaults")
        reset_row.addWidget(self.reset_defaults_button)
        form.addLayout(reset_row, 3, 0, 1, 4)

        self.sheet_width_spin.valueChanged.connect(self._on_sheet_value_changed)
        self.sheet_height_spin.valueChanged.connect(self._on_sheet_value_changed)
        self.reset_defaults_button.clicked.connect(self._reset_defaults)

        return group

    def _build_cut_optimization_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Cut Optimization")
        form = QtWidgets.QFormLayout(group)

        self.cut_mode_check = QtWidgets.QCheckBox("Cut Optimization: Woodshop Mode")
        self.cut_mode_check.setToolTip(
            "Optimize nesting for real-world cutting efficiency using a guillotine-style layout."
        )

        self.kerf_width_label = QtWidgets.QLabel("Kerf Width (mm):")
        self.kerf_width_spin = QtWidgets.QDoubleSpinBox()
        self.kerf_width_spin.setRange(0.1, 20.0)
        self.kerf_width_spin.setSingleStep(0.1)
        self.kerf_width_spin.setDecimals(2)
        self.kerf_width_spin.setValue(3.0)
        self.kerf_width_spin.setToolTip("Blade thickness used to maintain spacing between parts.")
        self.kerf_width_spin.valueChanged.connect(self.update_run_button_state)

        rot_layout = QtWidgets.QHBoxLayout()
        self.rot0_check = QtWidgets.QCheckBox("0°")
        self.rot90_check = QtWidgets.QCheckBox("90°")
        self.rot0_check.setToolTip("Allowed orientations for nesting. 0° only means no rotation; 90° allows rotated placement.")
        self.rot90_check.setToolTip("Allowed orientations for nesting. 0° only means no rotation; 90° allows rotated placement.")
        rot_layout.addWidget(self.rot0_check)
        rot_layout.addWidget(self.rot90_check)
        rot_layout.addStretch(1)

        form.addRow(self.cut_mode_check)
        form.addRow(self.kerf_width_label, self.kerf_width_spin)
        form.addRow("Allowed rotations:", rot_layout)

        return group

    def _build_stats_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Nesting Stats")
        form = QtWidgets.QFormLayout(group)
        self.mode_label = QtWidgets.QLabel("Mode: –")
        self.sheets_label = QtWidgets.QLabel("Sheets used: –")
        self.utilization_label = QtWidgets.QLabel("Utilization: –")
        self.cutcount_label = QtWidgets.QLabel("Estimated cuts: –")
        self.unplaced_label = QtWidgets.QLabel("Unplaced parts: –")
        self.stats_sheets_label = QtWidgets.QLabel("Number of sheets used: –")
        self.stats_complexity_label = QtWidgets.QLabel("Estimated cut path complexity: –")
        self.overlaps_label = QtWidgets.QLabel("Overlaps: –")
        for lbl in (
            self.mode_label,
            self.sheets_label,
            self.utilization_label,
            self.cutcount_label,
            self.unplaced_label,
            self.stats_sheets_label,
            self.stats_complexity_label,
            self.overlaps_label,
        ):
            lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        form.addRow("Mode:", self.mode_label)
        form.addRow("Sheets:", self.sheets_label)
        form.addRow("Utilization:", self.utilization_label)
        form.addRow("Estimated cuts:", self.cutcount_label)
        form.addRow("Unplaced parts:", self.unplaced_label)
        form.addRow("Sheets used:", self.stats_sheets_label)
        form.addRow("Cut path complexity:", self.stats_complexity_label)
        form.addRow("Overlaps:", self.overlaps_label)
        return group

    def _build_export_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Export")
        form = QtWidgets.QFormLayout(group)
        self.export_format_combo = QtWidgets.QComboBox()
        self.export_format_combo.addItem("DXF", "dxf")
        self.export_format_combo.addItem("SVG", "svg")
        self.export_format_combo.addItem("Cut list CSV", "cutlist_csv")
        self.export_format_combo.addItem("Cut list script (text)", "cutlist_script")
        self.export_button = QtWidgets.QPushButton("Export SquatchCut")
        self.export_button.setToolTip("Export the current SquatchCut layout in the selected format.")
        self.export_button.clicked.connect(self.on_export_clicked)
        self.include_labels_check = QtWidgets.QCheckBox("Include part labels")
        self.include_labels_check.setToolTip("Include part names as text labels in DXF/SVG exports.")
        self.include_dimensions_check = QtWidgets.QCheckBox("Include dimensions")
        self.include_dimensions_check.setToolTip("Include basic width/height dimensions in DXF/SVG exports.")
        self.include_labels_check.stateChanged.connect(self._on_export_options_changed)
        self.include_dimensions_check.stateChanged.connect(self._on_export_options_changed)

        form.addRow("Export format:", self.export_format_combo)
        form.addRow(self.include_labels_check)
        form.addRow(self.include_dimensions_check)
        form.addRow(self.export_button)
        return group

    # ---------------- State helpers ----------------

    def _load_initial_state_from_session(self) -> None:
        """Populate widgets from session_state where possible."""
        if self.doc is not None:
            try:
                session.sync_state_from_doc(self.doc)
            except Exception:
                pass

        sheet_w, sheet_h = session_state.get_sheet_size()
        kerf_mm = session_state.get_kerf_mm()
        margin_mm = session_state.get_gap_mm()
        default_allow = session_state.get_default_allow_rotate()
        cut_mode = session_state.get_optimize_for_cut_path()
        kerf_width = session_state.get_kerf_width_mm()
        rotations = set(session_state.get_allowed_rotations_deg())
        self.measurement_system = self._prefs.get_measurement_system()
        include_labels = self._prefs.get_export_include_labels()
        include_dims = self._prefs.get_export_include_dimensions()

        if sheet_w is None:
            sheet_w = self._prefs.get_default_sheet_width_mm()
        if sheet_h is None:
            sheet_h = self._prefs.get_default_sheet_height_mm()

        if margin_mm is None:
            margin_mm = self._prefs.get_default_spacing_mm()
        if kerf_mm is None or kerf_mm <= 0:
            kerf_mm = self._prefs.get_default_kerf_mm()
        if kerf_width is None or kerf_width <= 0:
            kerf_width = self._prefs.get_default_kerf_mm()
        if cut_mode is None:
            cut_mode = self._prefs.get_default_optimize_for_cut_path()

        for spin, value in (
            (self.sheet_width_spin, sheet_w),
            (self.sheet_height_spin, sheet_h),
            (self.kerf_spin, kerf_mm),
            (self.margin_spin, margin_mm),
        ):
            spin.blockSignals(True)
            spin.setValue(self._to_display_units(float(value)))
            spin.blockSignals(False)

        self.allow_90_check.setChecked(bool(default_allow))
        self.allow_180_check.setChecked(bool(default_allow))
        self._select_matching_preset(sheet_w, sheet_h)
        # Optimization mode
        mode = session_state.get_optimization_mode()
        mode_idx = self.mode_combo.findData(mode)
        if mode_idx < 0:
            mode_idx = 0
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(mode_idx)
        self.mode_combo.blockSignals(False)
        self._populate_table(session_state.get_panels())
        self._reset_summary(mode)
        self._refresh_summary()
        # Cut optimization settings
        self.cut_mode_check.setChecked(bool(cut_mode))
        self.kerf_width_spin.setValue(self._to_display_units(float(kerf_width or 3.0)))
        self.rot0_check.setChecked(0 in rotations or not rotations)
        self.rot90_check.setChecked(90 in rotations)
        unit_idx = self.units_combo.findData(self.measurement_system)
        if unit_idx >= 0:
            self.units_combo.blockSignals(True)
            self.units_combo.setCurrentIndex(unit_idx)
            self.units_combo.blockSignals(False)
        csv_units = self._prefs.get_csv_units(self.measurement_system)
        csv_units_idx = self.csv_units_combo.findData(csv_units)
        if csv_units_idx >= 0:
            self.csv_units_combo.blockSignals(True)
            self.csv_units_combo.setCurrentIndex(csv_units_idx)
            self.csv_units_combo.blockSignals(False)
        self.include_labels_check.setChecked(bool(include_labels))
        self.include_dimensions_check.setChecked(bool(include_dims))
        self._update_unit_labels()
        self._validate_inputs()
        self.update_run_button_state()

    def _apply_settings_to_session(self) -> None:
        """Sync widget values to session_state and the document."""
        sheet_w = self._to_mm(float(self.sheet_width_spin.value()))
        sheet_h = self._to_mm(float(self.sheet_height_spin.value()))
        kerf_mm = self._to_mm(float(self.kerf_spin.value()))
        margin_mm = self._to_mm(float(self.margin_spin.value()))
        # session_state tracks a single default rotation flag; map from 90° toggle.
        default_allow = bool(self.allow_90_check.isChecked() or self.allow_180_check.isChecked())
        mode = self.mode_combo.currentData() or "material"
        cut_mode = bool(self.cut_mode_check.isChecked())
        kerf_width_display = float(self.kerf_width_spin.value())
        kerf_width = self._to_mm(kerf_width_display)
        export_include_labels = bool(self.include_labels_check.isChecked())
        export_include_dimensions = bool(self.include_dimensions_check.isChecked())
        rotations = []
        if self.rot0_check.isChecked():
            rotations.append(0)
        if self.rot90_check.isChecked():
            rotations.append(90)
        if not rotations:
            rotations = [0]

        session_state.set_sheet_size(sheet_w, sheet_h)
        session_state.set_kerf_mm(kerf_mm)
        session_state.set_gap_mm(margin_mm)
        session_state.set_default_allow_rotate(default_allow)
        session_state.set_optimization_mode(mode)
        session_state.set_optimize_for_cut_path(cut_mode)
        session_state.set_kerf_width_mm(kerf_width)
        session_state.set_allowed_rotations_deg(tuple(rotations))
        session_state.set_export_include_labels(export_include_labels)
        session_state.set_export_include_dimensions(export_include_dimensions)

        if self.doc is not None:
            try:
                session.sync_doc_from_state(self.doc)
                self.doc.recompute()
            except Exception:
                pass

    def _select_matching_preset(self, width: float, height: float) -> None:
        """Try to select a preset matching the given width/height."""
        for idx, (_, size) in enumerate(self._presets):
            if not size:
                continue
            preset_w, preset_h = size
            if abs(width - preset_w) < 0.01 and abs(height - preset_h) < 0.01:
                self.preset_combo.blockSignals(True)
                self.preset_combo.setCurrentIndex(idx)
                self.preset_combo.blockSignals(False)
                return
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.blockSignals(False)

    # ---------------- Event handlers ----------------

    def _on_preset_changed(self, index: int) -> None:
        label, size = self._presets[index]
        if size is None:
            return
        width, height = size
        self.sheet_width_spin.blockSignals(True)
        self.sheet_height_spin.blockSignals(True)
        self.sheet_width_spin.setValue(width)
        self.sheet_height_spin.setValue(height)
        self.sheet_width_spin.blockSignals(False)
        self.sheet_height_spin.blockSignals(False)

    def _on_sheet_value_changed(self) -> None:
        """Set preset to Custom when the user edits dimensions."""
        if self.preset_combo.currentIndex() != 0:
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentIndex(0)
            self.preset_combo.blockSignals(False)
        self.update_run_button_state()

    def _set_run_buttons_enabled(self, enabled: bool) -> None:
        """Enable/disable run buttons and update tooltips."""
        self.preview_button.setEnabled(enabled)
        apply_enabled = enabled and self.overlaps_count == 0
        self.run_button.setEnabled(apply_enabled)
        if not enabled:
            tooltip = "Load a parts CSV before running nesting."
            self.preview_button.setToolTip(tooltip)
            self.run_button.setToolTip(tooltip)
        elif not apply_enabled:
            self.preview_button.setToolTip("Generate a preview nesting layout.")
            self.run_button.setToolTip("Cannot apply: overlaps detected.")
        else:
            self.preview_button.setToolTip("Generate a preview nesting layout.")
            self.run_button.setToolTip("Create sheet objects in the active document.")
        self._update_status_label()

    def _on_mode_changed(self) -> None:
        """Persist optimization mode change immediately."""
        mode = self.mode_combo.currentData() or "material"
        session_state.set_optimization_mode(mode)
        self.update_run_button_state()

    def _choose_csv_file(self) -> None:
        caption = "Select panels CSV"
        file_filter = "CSV files (*.csv);;All files (*.*)"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            caption,
            self._last_csv_path or "",
            file_filter,
        )
        if not file_path:
            return
        self._import_csv(file_path)

    def _import_csv(self, file_path: str) -> None:
        doc = self._ensure_document()
        if doc is None:
            show_error("Unable to create or find an active document.", title="SquatchCut")
            return

        try:
            self._apply_settings_to_session()
            csv_units = self.csv_units_combo.currentData() or self.measurement_system or "metric"
            run_csv_import(doc, file_path, csv_units=csv_units)
            self._prefs.set_csv_units(csv_units)
            self._last_csv_path = file_path
            self._set_csv_label(file_path)
            self._populate_table(session_state.get_panels())
            self.update_run_button_state()
        except Exception as exc:
            show_error(f"Failed to import CSV:\n{exc}", title="SquatchCut")

    def _run_nesting(self, apply_to_doc: bool = True) -> None:
        doc = self._ensure_document()
        if doc is None:
            show_error("No active document available for nesting.", title="SquatchCut")
            return

        self._apply_settings_to_session()
        self._ensure_shapes_exist(doc)

        try:
            cmd = cmd_run_nesting.RunNestingCommand()
            cmd.Activated()
            # TODO: if a non-destructive preview path exists, route apply_to_doc=False accordingly.
        except Exception as exc:
            show_error(f"Nesting failed:\n{exc}", title="SquatchCut")
            return

        self._refresh_summary()
        self.update_run_button_state()

        if apply_to_doc:
            try:
                Gui.Control.closeDialog()
            except Exception:
                pass

    def _on_view_toggled(self) -> None:
        """Toggle visibility of sheet boundaries and nested parts (best-effort)."""
        doc = self.doc or App.ActiveDocument
        if doc is None:
            return

        show_sheet = self.show_sheet_check.isChecked()
        show_nested = self.show_nested_check.isChecked()

        for obj in getattr(doc, "Objects", []):
            try:
                name = getattr(obj, "Name", "") or ""
                label = getattr(obj, "Label", "") or ""
                is_sheet = name.startswith("Sheet_") or label.startswith("Sheet_")
                is_panel = bool(getattr(obj, "SquatchCutPanel", False))

                if is_sheet:
                    obj.ViewObject.Visibility = show_sheet
                elif is_panel:
                    obj.ViewObject.Visibility = show_nested
            except Exception:
                continue

    # ---------------- Helpers ----------------

    def _ensure_document(self):
        """Return an active document, creating one if needed."""
        doc = self.doc or App.ActiveDocument
        if doc is None:
            try:
                doc = App.newDocument("SquatchCut")
                self.doc = doc
            except Exception:
                return None
        return doc

    def _ensure_shapes_exist(self, doc) -> None:
        """If no SquatchCut panels exist in the doc, create them from session panels."""
        existing = [
            obj for obj in getattr(doc, "Objects", []) if getattr(obj, "SquatchCutPanel", False)
        ]
        if existing:
            return

        panels = session_state.get_panels()
        if not panels:
            return

        try:
            creator = cmd_add_shapes.AddShapesCommand()
            creator.Activated()
        except Exception:
            pass

    def _populate_table(self, panels: List[dict]) -> None:
        self.parts_table.setRowCount(0)
        if not panels:
            self._set_run_buttons_enabled(False)
            self.has_csv_data = False
            self.update_run_button_state()
            return

        self.parts_table.setRowCount(len(panels))
        headers = ["Name", "Width (mm)", "Height (mm)", "Qty", "Allow rotate"]
        self.parts_table.setHorizontalHeaderLabels(headers)

        for row, panel in enumerate(panels):
            name = panel.get("label") or panel.get("id") or f"Panel {row + 1}"
            width = panel.get("width", "")
            height = panel.get("height", "")
            qty = panel.get("qty", 1)
            allow_rotate = panel.get("allow_rotate", False)

            values = [
                str(name),
                f"{float(width):.1f}" if width not in (None, "") else "",
                f"{float(height):.1f}" if height not in (None, "") else "",
                str(int(qty) if qty not in (None, "") else 1),
                "Yes" if allow_rotate else "No",
            ]

            for col, text in enumerate(values):
                item = QtWidgets.QTableWidgetItem(text)
                item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.parts_table.setItem(row, col, item)

        self.parts_table.resizeColumnsToContents()
        self.has_csv_data = True
        self._set_run_buttons_enabled(True)
        self.update_run_button_state()

    def _set_csv_label(self, path: str) -> None:
        display = os.path.basename(path) if path else "No file loaded"
        self.csv_path_label.setText(display)
        self.csv_path_label.setToolTip(path)
        self.csv_path_label.setStyleSheet("" if path else "color: gray;")

    def _reset_summary(self, mode: str | None = None) -> None:
        """Reset results labels to neutral defaults."""
        mode_text = mode or session_state.get_optimization_mode()
        readable_mode = "Material (minimize waste)" if mode_text == "material" else "Cuts (minimize cuts)"
        self.mode_label.setText(readable_mode)
        self.sheets_label.setText("Sheets used: –")
        self.utilization_label.setText("Utilization: –")
        self.cutcount_label.setText("Estimated cuts: –")
        self.unplaced_label.setText("Unplaced parts: –")
        self.unplaced_label.setStyleSheet("")
        stats = session_state.get_nesting_stats()
        sheets_used = stats.get("sheets_used")
        cut_complexity = stats.get("cut_complexity")
        self.overlaps_count = stats.get("overlaps_count", 0) or 0
        self.stats_sheets_label.setText(
            f"Number of sheets used: {sheets_used}" if sheets_used is not None else "Number of sheets used: –"
        )
        if cut_complexity is None:
            self.stats_complexity_label.setText("Estimated cut path complexity: –")
        else:
            self.stats_complexity_label.setText(f"Estimated cut path complexity: {cut_complexity:.2f}")
        if self.overlaps_count > 0:
            self.overlaps_label.setText(f"{self.overlaps_count} conflicts detected")
            self.overlaps_label.setStyleSheet("color: red;")
        else:
            self.overlaps_label.setText("None")
            self.overlaps_label.setStyleSheet("")
        self._update_status_label()
        stats = session_state.get_nesting_stats()
        sheets_used = stats.get("sheets_used")
        cut_complexity = stats.get("cut_complexity")
        self.stats_sheets_label.setText(
            f"Number of sheets used: {sheets_used}" if sheets_used is not None else "Number of sheets used: –"
        )
        if cut_complexity is None:
            self.stats_complexity_label.setText("Estimated cut path complexity: –")
        else:
            self.stats_complexity_label.setText(f"Estimated cut path complexity: {cut_complexity:.2f}")
        self.overlaps_count = stats.get("overlaps_count", 0) or 0
        if self.overlaps_count > 0:
            self.overlaps_label.setText(f"{self.overlaps_count} conflicts detected")
            self.overlaps_label.setStyleSheet("color: red;")
        else:
            self.overlaps_label.setText("None")
            self.overlaps_label.setStyleSheet("")
        self._update_status_label()

    def update_run_button_state(self) -> None:
        """Enable/disable run controls based on CSV + input validity and update status."""
        self._validate_inputs()
        can_run = self.has_csv_data and self.has_valid_sheet and self.has_valid_kerf
        self._set_run_buttons_enabled(can_run)
        self._update_status_label()

    def _update_status_label(self) -> None:
        """Refresh status message based on readiness."""
        if not self.has_csv_data:
            self.status_label.setText("No parts loaded. Please import a CSV before running nesting.")
            self.status_label.setStyleSheet("color: orange;")
            return
        if not self.has_valid_sheet:
            self.status_label.setText("Sheet size is invalid. Please enter a positive width and height.")
            self.status_label.setStyleSheet("color: orange;")
            return
        if not self.has_valid_kerf:
            self.status_label.setText("Kerf width must be greater than zero.")
            self.status_label.setStyleSheet("color: orange;")
            return
        if self.overlaps_count > 0:
            self.status_label.setText("Cannot apply nesting: overlaps detected. Adjust settings or re-run.")
            self.status_label.setStyleSheet("color: red;")
            return
        self.status_label.setText("Ready to run nesting.")
        self.status_label.setStyleSheet("color: green;")

    def _validate_inputs(self) -> None:
        """Inline validation for sheet size and kerf width."""
        sheet_w = self._to_mm(float(self.sheet_width_spin.value()))
        sheet_h = self._to_mm(float(self.sheet_height_spin.value()))
        kerf_width = self._to_mm(float(self.kerf_width_spin.value()))

        self.has_valid_sheet = sheet_w > 0 and sheet_h > 0
        self.has_valid_kerf = kerf_width > 0

        self.sheet_width_spin.setStyleSheet("" if self.has_valid_sheet else "border: 1px solid red;")
        self.sheet_height_spin.setStyleSheet("" if self.has_valid_sheet else "border: 1px solid red;")
        self.kerf_width_spin.setStyleSheet("" if self.has_valid_kerf else "border: 1px solid red;")

    def _on_units_changed(self) -> None:
        """Handle measurement system changes."""
        system = self.units_combo.currentData() or "metric"
        if system not in ("metric", "imperial"):
            system = "metric"
        self.measurement_system = system
        self._prefs.set_measurement_system(system)
        self._update_unit_labels()
        # Re-apply stored mm values to display in new units
        sheet_w, sheet_h = session_state.get_sheet_size()
        kerf_mm = session_state.get_kerf_mm()
        margin_mm = session_state.get_gap_mm()
        kerf_width = session_state.get_kerf_width_mm()

        if sheet_w is not None:
            self.sheet_width_spin.setValue(self._to_display_units(float(sheet_w)))
        if sheet_h is not None:
            self.sheet_height_spin.setValue(self._to_display_units(float(sheet_h)))
        if kerf_mm is not None:
            self.kerf_spin.setValue(self._to_display_units(float(kerf_mm)))
        if margin_mm is not None:
            self.margin_spin.setValue(self._to_display_units(float(margin_mm)))
        if kerf_width is not None:
            self.kerf_width_spin.setValue(self._to_display_units(float(kerf_width)))

        self.update_run_button_state()

    def _on_export_options_changed(self) -> None:
        """Persist export options into preferences."""
        self._prefs.set_export_include_labels(bool(self.include_labels_check.isChecked()))
        self._prefs.set_export_include_dimensions(bool(self.include_dimensions_check.isChecked()))

    def _to_mm(self, value: float) -> float:
        """Convert a displayed value to mm based on current measurement system."""
        if self.measurement_system == "imperial":
            return value * self.MM_PER_INCH
        return value

    def _to_display_units(self, value_mm: float) -> float:
        """Convert mm to display units (mm or in)."""
        if self.measurement_system == "imperial":
            return value_mm / self.MM_PER_INCH
        return value_mm

    def _update_unit_labels(self) -> None:
        """Update labels to reflect current measurement system."""
        unit = "mm" if self.measurement_system == "metric" else "in"
        self.sheet_width_label.setText(f"Width ({unit}):")
        self.sheet_height_label.setText(f"Height ({unit}):")
        self.kerf_label.setText(f"Kerf width ({unit}):")
        self.margin_label.setText(f"Edge margin ({unit}):")
        self.kerf_width_label.setText(f"Kerf Width ({unit}):")

    def on_report_bug_clicked(self) -> None:
        """Open the SquatchCut GitHub issues page in the default browser."""
        url = "https://github.com/stevenfarmer/SquatchCut/issues/new/choose"
        try:
            webbrowser.open(url)
        except Exception as exc:
            try:
                App.Console.PrintError(f"[SquatchCut] Failed to open bug report URL: {exc}\n")
            except Exception:
                pass

    def on_export_clicked(self) -> None:
        """Export the current nesting layout based on selected format."""
        if self.overlaps_count > 0:
            self.status_label.setText("Cannot export: current nesting contains overlapping parts.")
            self.status_label.setStyleSheet("color: red;")
            return

        placements = session_state.get_last_layout() or []
        if not placements:
            self.status_label.setText("Cannot export: no nesting layout available.")
            self.status_label.setStyleSheet("color: orange;")
            return

        sheet_w, sheet_h = session_state.get_sheet_size()
        if not sheet_w or not sheet_h:
            self.status_label.setText("Cannot export: sheet size missing.")
            self.status_label.setStyleSheet("color: orange;")
            return

        fmt = self.export_format_combo.currentData()
        if fmt == "dxf":
            filter_str = "DXF files (*.dxf)"
            default_ext = ".dxf"
        elif fmt == "svg":
            filter_str = "SVG files (*.svg)"
            default_ext = ".svg"
        elif fmt == "cutlist_csv":
            filter_str = "CSV files (*.csv)"
            default_ext = ".csv"
        else:
            filter_str = "Text files (*.txt)"
            default_ext = ".txt"

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            None,
            "Export SquatchCut Layout",
            "",
            f"{filter_str};;All files (*.*)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(default_ext):
            file_path += default_ext

        try:
            if fmt == "dxf":
                exporter.export_layout_to_dxf(
                    placements,
                    (sheet_w, sheet_h),
                    self._ensure_document(),
                    file_path,
                    include_labels=session_state.get_export_include_labels(),
                    include_dimensions=session_state.get_export_include_dimensions(),
                )
            elif fmt == "svg":
                exporter.export_layout_to_svg(
                    placements,
                    (sheet_w, sheet_h),
                    self._ensure_document(),
                    file_path,
                    include_labels=session_state.get_export_include_labels(),
                    include_dimensions=session_state.get_export_include_dimensions(),
                )
            elif fmt == "cutlist_csv":
                cutlist_map = exporter.generate_cutlist(placements, (sheet_w, sheet_h))
                exporter.export_cutlist_map_to_csv(cutlist_map, file_path)
            else:
                cutlist_map = exporter.generate_cutlist(placements, (sheet_w, sheet_h))
                exporter.export_cutlist_to_text(cutlist_map, file_path)
            self.status_label.setText(f"Exported SquatchCut layout to: {file_path}")
            self.status_label.setStyleSheet("color: green;")
        except Exception as exc:
            try:
                App.Console.PrintError(f"[SquatchCut] Export failed: {exc}\n")
            except Exception:
                pass
            self.status_label.setText("Export failed. See Report View for details.")
            self.status_label.setStyleSheet("color: red;")

    def _reset_defaults(self) -> None:
        """Reset configuration fields to safe defaults (does not clear CSV)."""
        # Pull defaults from preferences
        self.sheet_width_spin.setValue(self._to_display_units(self._prefs.get_default_sheet_width_mm()))
        self.sheet_height_spin.setValue(self._to_display_units(self._prefs.get_default_sheet_height_mm()))
        self.kerf_spin.setValue(self._to_display_units(self._prefs.get_default_kerf_mm()))
        self.margin_spin.setValue(self._to_display_units(self._prefs.get_default_spacing_mm()))
        self.allow_90_check.setChecked(False)
        self.allow_180_check.setChecked(False)
        self.mode_combo.setCurrentIndex(0)
        self.cut_mode_check.setChecked(self._prefs.get_default_optimize_for_cut_path())
        self.kerf_width_spin.setValue(self._to_display_units(self._prefs.get_default_kerf_mm()))
        self.rot0_check.setChecked(True)
        self.rot90_check.setChecked(True)

        # Persist defaults into session state and refresh status
        self._apply_settings_to_session()
        self.update_run_button_state()

    def _refresh_summary(self) -> None:
        """Update summary labels from the last layout."""
        layout = session_state.get_last_layout() or []
        sheet_w, sheet_h = session_state.get_sheet_size()
        mode = session_state.get_optimization_mode()
        readable_mode = "Material (minimize waste)" if mode == "material" else "Cuts (minimize cuts)"
        self.mode_label.setText(readable_mode)

        if not layout or not sheet_w or not sheet_h:
            self.sheets_label.setText("Sheets used: –")
            self.utilization_label.setText("Utilization: –")
            self.cutcount_label.setText("Estimated cuts: –")
            self.unplaced_label.setText("Unplaced parts: –")
            self.unplaced_label.setStyleSheet("")
            return

        util = compute_utilization(layout, float(sheet_w), float(sheet_h))
        cuts = estimate_cut_counts(layout, float(sheet_w), float(sheet_h))
        sheets_used = util.get("sheets_used", 0)

        self.sheets_label.setText(f"Sheets used: {sheets_used}")
        self.utilization_label.setText(f"Utilization: {util.get('utilization_percent', 0.0):.1f}%")
        self.cutcount_label.setText(
            f"Estimated cuts: {cuts.get('total', 0)} "
            f"({cuts.get('vertical', 0)} vertical, {cuts.get('horizontal', 0)} horizontal)"
        )
        self.unplaced_label.setText("Unplaced parts: 0")
        self.unplaced_label.setStyleSheet("")

        stats = session_state.get_nesting_stats()
        sheets_used = stats.get("sheets_used")
        cut_complexity = stats.get("cut_complexity")
        self.stats_sheets_label.setText(
            f"Number of sheets used: {sheets_used}" if sheets_used is not None else "Number of sheets used: –"
        )
        if cut_complexity is None:
            self.stats_complexity_label.setText("Estimated cut path complexity: –")
        else:
            self.stats_complexity_label.setText(f"Estimated cut path complexity: {cut_complexity:.2f}")
        if self.overlaps_count > 0:
            self.overlaps_label.setText(f"{self.overlaps_count} conflicts detected")
            self.overlaps_label.setStyleSheet("color: red;")
        else:
            self.overlaps_label.setText("None")
            self.overlaps_label.setStyleSheet("")
        self._update_status_label()

    def on_show_source_panels(self):
        doc = App.ActiveDocument
        if doc is None:
            return

        sheets_group = doc.getObject("SquatchCut_Sheets")
        if sheets_group:
            for o in sheets_group.Group:
                try:
                    if hasattr(o, "ViewObject"):
                        o.ViewObject.Visibility = False
                except Exception:
                    continue

        for o in session.get_source_panel_objects():
            try:
                if hasattr(o, "ViewObject"):
                    o.ViewObject.Visibility = True
            except Exception:
                continue

        try:
            if Gui and Gui.ActiveDocument:
                view = Gui.ActiveDocument.ActiveView
                view.viewTop()
                view.fitAll()
        except Exception:
            pass

    # ---------------- Task panel API ----------------

    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

    def accept(self):
        self._run_nesting(apply_to_doc=True)

    def reject(self):
        try:
            Gui.Control.closeDialog()
        except Exception:
            pass
