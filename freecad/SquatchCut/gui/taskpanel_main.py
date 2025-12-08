"""Unified SquatchCut task panel for sheet setup, CSV import, optimization choice, nesting, and results summary."""

from __future__ import annotations

import os
from typing import Callable, List, Optional

import webbrowser

from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.qt_compat import QtWidgets, QtCore

from SquatchCut import settings
from SquatchCut.core import sheet_presets as sc_sheet_presets
from SquatchCut.core import session, session_state, view_controller, logger
from SquatchCut.core import units as sc_units
from SquatchCut.core.nesting import compute_utilization, estimate_cut_counts
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core import exporter
from SquatchCut.gui.commands.cmd_import_csv import run_csv_import
from SquatchCut.gui.commands import cmd_add_shapes, cmd_run_nesting, cmd_export_cutlist
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

    FALLBACK_SHEET_SIZE_MM = (1220.0, 2440.0)
    FALLBACK_MATCH_TOLERANCE_MM = 2.0
    _test_force_measurement_system: str | None = None

    def __init__(self, doc=None):
        self._prefs = SquatchCutPreferences()
        effective_doc = doc or (App.ActiveDocument if App is not None else None)
        test_override = self.__class__._test_force_measurement_system
        self.__class__._test_force_measurement_system = None
        doc_units = test_override if test_override in ("metric", "imperial") else session.detect_document_measurement_system(effective_doc)
        self._initial_state = self._compute_initial_state(effective_doc, doc_units)
        self.measurement_system = self._initial_state["measurement_system"]
        self.doc = effective_doc
        self._last_csv_path: str | None = None
        self.has_csv_data = False
        self.has_valid_sheet = False
        self.has_valid_kerf = False
        self.overlaps_count = 0
        self._preset_state = sc_sheet_presets.PresetSelectionState()
        self._presets = sc_sheet_presets.get_preset_entries(self.measurement_system)
        self._current_preset_id = None
        self._close_callback: Optional[Callable[[], None]] = None

        self.form = QtWidgets.QWidget()
        self._build_ui()
        self._apply_initial_state(self._initial_state)
        self._connect_signals()

    def set_close_callback(self, callback: Callable[[], None]) -> None:
        self._close_callback = callback

    def _notify_close(self) -> None:
        if self._close_callback:
            try:
                self._close_callback()
            except Exception:
                pass
            self._close_callback = None

    # ---------------- UI builders ----------------

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self.form)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # View mode row (Source vs Sheets)
        view_mode_layout = QtWidgets.QHBoxLayout()
        view_mode_label = QtWidgets.QLabel("View:")
        view_mode_layout.addWidget(view_mode_label)

        self.btnViewSource = QtWidgets.QToolButton()
        self.btnViewSource.setText("Source")
        self.btnViewSource.setToolTip("Show original source panels from CSV")
        self.btnViewSource.setCheckable(True)
        self.btnViewSource.setAutoRaise(True)

        self.btnViewSheets = QtWidgets.QToolButton()
        self.btnViewSheets.setText("Nested")
        self.btnViewSheets.setToolTip("Show nested sheets and panel placements")
        self.btnViewSheets.setCheckable(True)
        self.btnViewSheets.setAutoRaise(True)

        view_mode_layout.addWidget(self.btnViewSource)
        view_mode_layout.addWidget(self.btnViewSheets)
        view_mode_layout.addStretch(1)
        layout.addLayout(view_mode_layout)

        layout.addWidget(self._build_general_group())
        layout.addWidget(self._build_nesting_group())
        layout.addWidget(self._build_cut_optimization_group())
        layout.addWidget(self._build_stats_group())
        layout.addWidget(self._build_export_group())

        # Bottom action buttons
        buttons_row = QtWidgets.QHBoxLayout()
        buttons_row.addStretch(1)
        self.preview_button = QtWidgets.QPushButton("Preview")
        self.run_button = QtWidgets.QPushButton("Run Nesting")
        self.show_source_button = QtWidgets.QPushButton("Show Source")
        self.btnExportCutlist = QtWidgets.QPushButton("Cutlist CSV")
        self.preview_button.setToolTip("Preview the nesting layout without leaving the task panel.")
        self.run_button.setToolTip("Generate nested geometry in the active document.")
        self.show_source_button.setToolTip("Hide nested sheets and show the imported source panels.")
        self.btnExportCutlist.setToolTip("Export a CSV cutlist from the current nested sheets.")
        buttons_row.addWidget(self.preview_button)
        buttons_row.addWidget(self.run_button)
        buttons_row.addWidget(self.show_source_button)
        buttons_row.addWidget(self.btnExportCutlist)
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
        self.status_label = QtWidgets.QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        self._set_run_buttons_enabled(False)
        self.btnViewSource.setChecked(True)
        self.btnViewSheets.setChecked(False)

    def _build_general_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Cut List")
        vbox = QtWidgets.QVBoxLayout(group)

        form = QtWidgets.QFormLayout()
        self.units_combo = QtWidgets.QComboBox()
        self.units_combo.addItem("Metric (mm)", "metric")
        self.units_combo.addItem("Imperial (in)", "imperial")
        form.addRow("Units:", self.units_combo)

        self.preset_combo = QtWidgets.QComboBox()
        self._refresh_preset_labels()
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
        self.load_csv_button = QtWidgets.QPushButton("Import CSV")
        self.csv_path_label = QtWidgets.QLabel("No file loaded")
        self.csv_path_label.setStyleSheet("color: gray;")
        self.csv_path_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        top_row.addWidget(self.load_csv_button)
        top_row.addWidget(self.csv_path_label, 1)
        vbox.addLayout(top_row)

        csv_units_row = QtWidgets.QHBoxLayout()
        csv_units_row.addWidget(QtWidgets.QLabel("CSV units:"))
        self.csv_units_combo = QtWidgets.QComboBox()
        self.csv_units_combo.addItem("Metric (mm)", "mm")
        self.csv_units_combo.addItem("Imperial (in)", "in")
        csv_units_row.addWidget(self.csv_units_combo)
        csv_units_row.addStretch(1)
        vbox.addLayout(csv_units_row)

        self.parts_table = QtWidgets.QTableWidget()
        self.parts_table.setColumnCount(5)
        self.parts_table.horizontalHeader().setStretchLastSection(True)
        self.parts_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.parts_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.parts_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        vbox.addWidget(self.parts_table)
        self._update_table_headers()

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

        return group

    def _build_nesting_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Sheet & Settings")
        form = QtWidgets.QGridLayout(group)
        form.setColumnStretch(1, 1)

        self.sheet_width_label = QtWidgets.QLabel("Width (mm):")
        self.sheet_width_edit = QtWidgets.QLineEdit()

        self.sheet_height_label = QtWidgets.QLabel("Height (mm):")
        self.sheet_height_edit = QtWidgets.QLineEdit()

        self.kerf_label = QtWidgets.QLabel("Kerf width (mm):")
        self.kerf_edit = QtWidgets.QLineEdit()

        self.margin_label = QtWidgets.QLabel("Edge margin (mm):")
        self.margin_edit = QtWidgets.QLineEdit()

        self.allow_90_check = QtWidgets.QCheckBox("Allow 90° rotation")
        self.allow_180_check = QtWidgets.QCheckBox("Allow 180° rotation")

        form.addWidget(self.sheet_width_label, 0, 0)
        form.addWidget(self.sheet_width_edit, 0, 1)
        form.addWidget(self.sheet_height_label, 0, 2)
        form.addWidget(self.sheet_height_edit, 0, 3)
        form.addWidget(self.kerf_label, 1, 0)
        form.addWidget(self.kerf_edit, 1, 1)
        form.addWidget(self.margin_label, 1, 2)
        form.addWidget(self.margin_edit, 1, 3)
        form.addWidget(self.allow_90_check, 2, 0, 1, 2)
        form.addWidget(self.allow_180_check, 2, 2, 1, 2)

        reset_row = QtWidgets.QHBoxLayout()
        reset_row.addStretch(1)
        self.reset_defaults_button = QtWidgets.QPushButton("Reset to Defaults")
        reset_row.addWidget(self.reset_defaults_button)
        form.addLayout(reset_row, 3, 0, 1, 4)

        return group

    def _build_cut_optimization_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Cut Optimization")
        form = QtWidgets.QFormLayout(group)

        self.cut_mode_check = QtWidgets.QCheckBox("Cut-friendly layout")
        self.cut_mode_check.setToolTip(
            "Bias nesting toward woodshop-style rips/crosscuts instead of tight packing."
        )

        self.kerf_width_label = QtWidgets.QLabel("Kerf Width (mm):")
        self.kerf_width_edit = QtWidgets.QLineEdit()
        self.kerf_width_edit.setToolTip("Blade thickness used to maintain spacing between parts.")

        rot_layout = QtWidgets.QHBoxLayout()
        self.rot0_check = QtWidgets.QCheckBox("0°")
        self.rot90_check = QtWidgets.QCheckBox("90°")
        self.rot0_check.setToolTip("Allowed orientations for nesting. 0° only means no rotation; 90° allows rotated placement.")
        self.rot90_check.setToolTip("Allowed orientations for nesting. 0° only means no rotation; 90° allows rotated placement.")
        rot_layout.addWidget(self.rot0_check)
        rot_layout.addWidget(self.rot90_check)
        rot_layout.addStretch(1)

        form.addRow(self.cut_mode_check)
        form.addRow(self.kerf_width_label, self.kerf_width_edit)
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
        self.include_labels_check = QtWidgets.QCheckBox("Include part labels")
        self.include_labels_check.setToolTip("Include part names as text labels in DXF/SVG exports.")
        self.include_dimensions_check = QtWidgets.QCheckBox("Include dimensions")
        self.include_dimensions_check.setToolTip("Include basic width/height dimensions in DXF/SVG exports.")

        form.addRow("Export format:", self.export_format_combo)
        form.addRow(self.include_labels_check)
        form.addRow(self.include_dimensions_check)
        form.addRow(self.export_button)
        return group

    # ---------------- State helpers ----------------

    def _compute_initial_state(self, doc, doc_measurement_system: str | None = None) -> dict:
        """Hydrate persisted settings before any UI widgets are built."""
        override = doc_measurement_system if doc_measurement_system in ("metric", "imperial") else None
        try:
            settings.hydrate_from_params(measurement_override=override)
        except Exception:
            pass

        measurement_system = override or session_state.get_measurement_system()
        has_defaults = self._prefs.has_default_sheet_size(measurement_system)
        if has_defaults:
            pref_sheet_w, pref_sheet_h = self._prefs.get_default_sheet_size_mm(measurement_system)
            user_defaults = (pref_sheet_w, pref_sheet_h)
            default_sheet_mm = user_defaults
        else:
            user_defaults = (None, None)
            default_sheet_mm = sc_sheet_presets.get_factory_default_sheet_size(measurement_system)

        if doc is not None:
            try:
                session.sync_state_from_doc(doc, measurement_system, default_sheet_mm)
            except Exception:
                pass

        measurement_system = override or session_state.get_measurement_system()
        session_state.set_measurement_system(measurement_system)
        sc_units.set_units("in" if measurement_system == "imperial" else "mm")

        session_sheet = session_state.get_sheet_size()
        kerf_mm = session_state.get_kerf_mm()
        margin_mm = session_state.get_gap_mm()
        default_allow = session_state.get_default_allow_rotate()
        cut_mode = session_state.get_optimize_for_cut_path()
        kerf_width = session_state.get_kerf_width_mm()
        rotations = set(session_state.get_allowed_rotations_deg())
        include_labels = self._prefs.get_export_include_labels()
        include_dims = self._prefs.get_export_include_dimensions()

        sheet_w, sheet_h = sc_sheet_presets.get_initial_sheet_size(
            measurement_system,
            session_sheet,
            user_defaults,
        )
        session_state.set_sheet_size(sheet_w, sheet_h)

        if margin_mm is None:
            margin_mm = self._prefs.get_default_spacing_mm()
        if kerf_mm is None or kerf_mm <= 0:
            kerf_mm = self._prefs.get_default_kerf_mm()
        if kerf_width is None or kerf_width <= 0:
            kerf_width = self._prefs.get_default_kerf_mm()
        if cut_mode is None:
            cut_mode = self._prefs.get_default_optimize_for_cut_path()

        mode = session_state.get_optimization_mode()
        csv_units = self._prefs.get_csv_units(measurement_system)
        if csv_units == "imperial":
            csv_units = "in"
        elif csv_units == "metric":
            csv_units = "mm"

        return {
            "measurement_system": measurement_system,
            "sheet_width_mm": float(sheet_w) if sheet_w is not None else None,
            "sheet_height_mm": float(sheet_h) if sheet_h is not None else None,
            "kerf_mm": float(kerf_mm),
            "margin_mm": float(margin_mm),
            "kerf_width_mm": float(kerf_width),
            "default_allow": bool(default_allow),
            "cut_mode": bool(cut_mode),
            "rotations": rotations,
            "mode": mode,
            "csv_units": csv_units,
            "include_labels": bool(include_labels),
            "include_dimensions": bool(include_dims),
            "panels": session_state.get_panels(),
        }

    def _apply_initial_state(self, state: dict) -> None:
        """Populate widgets from a pre-hydrated state dictionary."""
        for edit, value in (
            (self.sheet_width_edit, state["sheet_width_mm"]),
            (self.sheet_height_edit, state["sheet_height_mm"]),
            (self.kerf_edit, state["kerf_mm"]),
            (self.margin_edit, state["margin_mm"]),
        ):
            edit.blockSignals(True)
            self._set_length_text(edit, float(value) if value is not None else None)
            edit.blockSignals(False)

        self.allow_90_check.setChecked(bool(state["default_allow"]))
        self.allow_180_check.setChecked(bool(state["default_allow"]))

        mode_idx = self.mode_combo.findData(state["mode"])
        if mode_idx < 0:
            mode_idx = 0
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(mode_idx)
        self.mode_combo.blockSignals(False)

        unit_idx = self.units_combo.findData(self.measurement_system)
        if unit_idx < 0:
            unit_idx = 0
        self.units_combo.blockSignals(True)
        self.units_combo.setCurrentIndex(unit_idx)
        self.units_combo.blockSignals(False)
        self._update_unit_labels()
        self._populate_table(state["panels"])
        self._reset_summary(state["mode"])
        self._refresh_summary()

        nesting_mode = session_state.get_nesting_mode()
        self.cut_mode_check.setChecked(
            nesting_mode == "cut_friendly" or bool(state["cut_mode"])
        )
        self.kerf_width_edit.blockSignals(True)
        self._set_length_text(self.kerf_width_edit, float(state["kerf_width_mm"]))
        self.kerf_width_edit.blockSignals(False)
        self.rot0_check.setChecked(0 in state["rotations"] or not state["rotations"])
        self.rot90_check.setChecked(90 in state["rotations"])

        csv_units_idx = self.csv_units_combo.findData(state["csv_units"])
        if csv_units_idx >= 0:
            self.csv_units_combo.blockSignals(True)
            self.csv_units_combo.setCurrentIndex(csv_units_idx)
            self.csv_units_combo.blockSignals(False)
        self.include_labels_check.setChecked(bool(state["include_labels"]))
        self.include_dimensions_check.setChecked(bool(state["include_dimensions"]))
        self._update_unit_labels()
        self._validate_inputs()
        self.update_run_button_state()

    def _connect_signals(self) -> None:
        """Wire UI signals after all widgets are populated."""
        self.preview_button.clicked.connect(self.on_preview_clicked)
        self.run_button.clicked.connect(self.on_apply_clicked)
        self.show_source_button.clicked.connect(self.on_show_source_panels)
        self.btnExportCutlist.clicked.connect(self.on_export_cutlist_clicked)
        self.report_bug_button.clicked.connect(self.on_report_bug_clicked)
        self.btnViewSource.clicked.connect(self._on_view_source_clicked)
        self.btnViewSheets.clicked.connect(self._on_view_sheets_clicked)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.units_combo.currentIndexChanged.connect(self._on_units_changed)
        self.load_csv_button.clicked.connect(self._choose_csv_file)
        self.show_sheet_check.toggled.connect(self._on_view_toggled)
        self.show_nested_check.toggled.connect(self._on_view_toggled)
        self.sheet_width_edit.textChanged.connect(self.update_run_button_state)
        self.sheet_width_edit.textChanged.connect(self._on_sheet_value_changed)
        self.sheet_height_edit.textChanged.connect(self.update_run_button_state)
        self.sheet_height_edit.textChanged.connect(self._on_sheet_value_changed)
        self.kerf_edit.textChanged.connect(self.update_run_button_state)
        self.margin_edit.textChanged.connect(self.update_run_button_state)
        self.reset_defaults_button.clicked.connect(self._reset_defaults)
        self.cut_mode_check.toggled.connect(self._on_mode_changed)
        self.kerf_width_edit.textChanged.connect(self.update_run_button_state)
        self.export_button.clicked.connect(self.on_export_clicked)
        self.include_labels_check.stateChanged.connect(self._on_export_options_changed)
        self.include_dimensions_check.stateChanged.connect(self._on_export_options_changed)

    def _apply_default_sheet_override(
        self,
        sheet_w: float,
        sheet_h: float,
        pref_w: float,
        pref_h: float,
    ) -> tuple[float, float]:
        """Prefer preference defaults when the doc sheet is just the fallback metric preset."""
        if sheet_w is None or sheet_h is None:
            return sheet_w, sheet_h
        if pref_w is None or pref_h is None:
            return sheet_w, sheet_h
        fallback_w, fallback_h = self.FALLBACK_SHEET_SIZE_MM
        tol = self.FALLBACK_MATCH_TOLERANCE_MM
        uses_fallback = (
            sheet_w is not None
            and sheet_h is not None
            and abs(sheet_w - fallback_w) < tol
            and abs(sheet_h - fallback_h) < tol
        )
        prefers_custom = (
            abs(pref_w - fallback_w) > tol or abs(pref_h - fallback_h) > tol
        )
        if uses_fallback and prefers_custom:
            session_state.set_sheet_size(pref_w, pref_h)
            if self.doc is not None:
                session.sync_doc_from_state(self.doc)
            return pref_w, pref_h
        return sheet_w, sheet_h

    def _apply_settings_to_session(self) -> None:
        """Sync widget values to session_state and the document."""
        try:
            sheet_w = self._parse_length(self.sheet_width_edit.text())
            sheet_h = self._parse_length(self.sheet_height_edit.text())
            kerf_mm = self._parse_length(self.kerf_edit.text())
            margin_mm = self._parse_length(self.margin_edit.text())
            kerf_width = self._parse_length(self.kerf_width_edit.text())
        except ValueError as exc:
            self._handle_parse_error(exc)
            return
        if sheet_w <= 0 or sheet_h <= 0:
            self._handle_parse_error(ValueError("Sheet size must be positive."), "Sheet width and height must be greater than zero.")
            return
        if kerf_width <= 0:
            self._handle_parse_error(ValueError("Kerf width must be positive."), "Kerf width must be greater than zero.")
            return
        if kerf_mm < 0 or margin_mm < 0:
            self._handle_parse_error(ValueError("Kerf/margin cannot be negative."), "Kerf and edge margin cannot be negative.")
            return
        # session_state tracks a single default rotation flag; map from 90° toggle.
        default_allow = bool(self.allow_90_check.isChecked() or self.allow_180_check.isChecked())
        mode = self.mode_combo.currentData() or "material"
        cut_mode = bool(self.cut_mode_check.isChecked())
        export_include_labels = bool(self.include_labels_check.isChecked())
        export_include_dimensions = bool(self.include_dimensions_check.isChecked())
        rotations = []
        if self.rot0_check.isChecked():
            rotations.append(0)
        if self.rot90_check.isChecked():
            rotations.append(90)
        if not rotations:
            rotations = [0]

        # Persist measurement system preference for future sessions.
        try:
            self._prefs.set_measurement_system(self.measurement_system)
        except Exception:
            pass

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

    # ---------------- Event handlers ----------------

    def _on_preset_changed(self, index: int) -> None:
        if index <= 0:
            if self._preset_state.current_index != 0:
                self._set_preset_index(0)
            return
        self._preset_state.set_index(index, self._presets)
        self._current_preset_id = self._preset_state.current_id
        preset = self._presets[index]
        size = preset.get("size")
        if size is None:
            return
        width, height = size
        self.sheet_width_edit.blockSignals(True)
        self.sheet_height_edit.blockSignals(True)
        self._set_length_text(self.sheet_width_edit, width)
        self._set_length_text(self.sheet_height_edit, height)
        self.sheet_width_edit.blockSignals(False)
        self.sheet_height_edit.blockSignals(False)
        session_state.set_sheet_size(width, height)
        self.update_run_button_state()
        logger.info(f">>> [SquatchCut] Sheet preset applied: {preset.get('id')} ({width:.1f} x {height:.1f} mm)")

    def _on_sheet_value_changed(self) -> None:
        """Keep the preset selection synced to the entered sheet size."""
        sheet_w_ok, sheet_w = self._parse_length_safely(self.sheet_width_edit)
        sheet_h_ok, sheet_h = self._parse_length_safely(self.sheet_height_edit)
        if self.preset_combo.currentIndex() != 0:
            self._set_preset_index(0)
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
        session_state.set_nesting_mode("cut_friendly" if self.cut_mode_check.isChecked() else "pack")
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
            csv_units = self.get_csv_units()
            logger.info(f">>> [SquatchCut] Importing CSV from task panel: {file_path}")
            run_csv_import(doc, file_path, csv_units=csv_units)
            self._prefs.set_csv_units(csv_units)
            self._last_csv_path = file_path
            self._set_csv_label(file_path)
            self._populate_table(session_state.get_panels())
            self.update_run_button_state()
            parts_count = len(session_state.get_panels() or [])
            self.set_status(f"Imported {parts_count} parts from CSV.")
        except Exception as exc:
            self.set_status("CSV import failed. See report view for details.")
            show_error(f"Failed to import CSV:\n{exc}", title="SquatchCut")

    def _run_nesting(self, apply_to_doc: bool = True) -> None:
        doc = self._ensure_document()
        if doc is None:
            show_error("No active document available for nesting.", title="SquatchCut")
            return

        self._apply_settings_to_session()
        self._ensure_shapes_exist(doc)

        try:
            logger.info(">>> [SquatchCut] Running nesting from task panel.")
            cmd = cmd_run_nesting.RunNestingCommand()
            cmd.Activated()
            if getattr(cmd, "validation_error", None):
                self.set_status("Nesting failed: some panels too large for the sheet.")
                return
            # TODO: if a non-destructive preview path exists, route apply_to_doc=False accordingly.
        except Exception as exc:
            show_error(f"Nesting failed:\n{exc}", title="SquatchCut")
            self.set_status("Nesting failed. See report view for details.")
            return

        self._refresh_summary()
        self.update_run_button_state()
        nested_count = len(session_state.get_last_layout() or [])
        self.set_status(f"Nested {nested_count} parts on current sheet.")
        logger.info(">>> [SquatchCut] Nesting completed in task panel.")

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

    def get_csv_units(self):
        """Return csv units selection ('mm' or 'in')."""
        data = self.csv_units_combo.currentData()
        if data in ("mm", "in"):
            return data
        return "mm"

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

    def _unit_label(self) -> str:
        return sc_units.unit_label_for_system(self.measurement_system)

    def _sheet_matches_defaults(self, width_mm: float | None, height_mm: float | None, defaults: tuple[float, float], tolerance: float = 1e-3) -> bool:
        if width_mm is None or height_mm is None:
            return False
        default_w, default_h = defaults
        return abs(width_mm - default_w) <= tolerance and abs(height_mm - default_h) <= tolerance

    def _format_length(self, value_mm: float) -> str:
        return sc_units.format_length(value_mm, self.measurement_system)

    def _set_length_text(self, widget: QtWidgets.QLineEdit, value_mm: float | None) -> None:
        if value_mm is None:
            widget.clear()
        else:
            widget.setText(self._format_length(float(value_mm)))

    def _parse_length(self, text: str) -> float:
        return sc_units.parse_length(text, self.measurement_system)

    def _parse_length_safely(self, widget: QtWidgets.QLineEdit) -> tuple[bool, float | None]:
        try:
            return True, self._parse_length(widget.text())
        except ValueError:
            return False, None

    def _set_field_valid(self, widget: QtWidgets.QLineEdit, is_valid: bool) -> None:
        widget.setStyleSheet("" if is_valid else "border: 1px solid red;")

    def _handle_parse_error(self, exc: Exception, fallback_message: str | None = None) -> None:
        if fallback_message:
            message = fallback_message
        elif self.measurement_system == "imperial":
            message = "Invalid imperial value. Use formats like 48, 48.5, 48 1/2, or 48-1/2."
        else:
            message = str(exc)
        show_error(message, title="SquatchCut")
        logger.error(f"Failed to parse length input: {exc}")

    def set_status(self, message: str) -> None:
        self.status_label.setText(f"Status: {message}")

    def _format_preset_label(self, preset: dict) -> str:
        if preset.get("size") is None:
            return preset.get("label") or ""
        width_mm, height_mm = preset["size"]
        return sc_units.format_preset_label(
            width_mm,
            height_mm,
            self.measurement_system,
            nickname=preset.get("nickname"),
        )

    def _refresh_preset_labels(self) -> None:
        """Refresh preset combo text for the current measurement system."""
        self._presets = sc_sheet_presets.get_preset_entries(self.measurement_system)
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        for preset in self._presets:
            self.preset_combo.addItem(self._format_preset_label(preset))
        self.preset_combo.blockSignals(False)
        desired_index = self._preset_state.current_index
        if desired_index >= len(self._presets):
            desired_index = 0
        self._set_preset_index(desired_index)

    def _set_preset_index(self, index: int) -> None:
        index = max(0, min(index, len(self._presets) - 1))
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentIndex(index)
        self.preset_combo.blockSignals(False)
        self._preset_state.set_index(index, self._presets)
        self._current_preset_id = self._preset_state.current_id

    def _populate_table(self, panels: List[dict]) -> None:
        self.parts_table.setRowCount(0)
        if not panels:
            self._set_run_buttons_enabled(False)
            self.has_csv_data = False
            self.update_run_button_state()
            return

        self.parts_table.setRowCount(len(panels))
        self._update_table_headers()

        for row, panel in enumerate(panels):
            name = panel.get("label") or panel.get("id") or f"Panel {row + 1}"
            width = panel.get("width", "")
            height = panel.get("height", "")
            qty = panel.get("qty", 1)
            allow_rotate = panel.get("allow_rotate", False)

            try:
                width_text = self._format_length(float(width)) if width not in (None, "") else ""
            except Exception:
                width_text = str(width)
            try:
                height_text = self._format_length(float(height)) if height not in (None, "") else ""
            except Exception:
                height_text = str(height)

            values = [
                str(name),
                width_text,
                height_text,
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

    def _update_table_headers(self) -> None:
        unit = self._unit_label()
        headers = ["Name", f"Width ({unit})", f"Height ({unit})", "Qty", "Allow rotate"]
        self.parts_table.setHorizontalHeaderLabels(headers)

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
            self.status_label.setText("Kerf/margin values must be valid and kerf width must be greater than zero.")
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
        sheet_w_ok, sheet_w = self._parse_length_safely(self.sheet_width_edit)
        sheet_h_ok, sheet_h = self._parse_length_safely(self.sheet_height_edit)
        kerf_ok, kerf_mm = self._parse_length_safely(self.kerf_edit)
        margin_ok, margin_mm = self._parse_length_safely(self.margin_edit)
        kerf_width_ok, kerf_width = self._parse_length_safely(self.kerf_width_edit)

        self.has_valid_sheet = bool(sheet_w_ok and sheet_h_ok and sheet_w and sheet_h and sheet_w > 0 and sheet_h > 0)
        kerf_value_ok = kerf_ok and kerf_mm is not None and kerf_mm >= 0
        margin_value_ok = margin_ok and margin_mm is not None and margin_mm >= 0
        spacing_ok = kerf_value_ok and margin_value_ok
        self.has_valid_kerf = bool(kerf_width_ok and kerf_width and kerf_width > 0 and spacing_ok)

        self._set_field_valid(self.sheet_width_edit, self.has_valid_sheet)
        self._set_field_valid(self.sheet_height_edit, self.has_valid_sheet)
        self._set_field_valid(self.kerf_width_edit, self.has_valid_kerf)
        self._set_field_valid(self.kerf_edit, kerf_ok)
        self._set_field_valid(self.margin_edit, margin_ok)

    def _on_units_changed(self) -> None:
        """Handle measurement system changes."""
        previous_system = getattr(self, "measurement_system", None)
        system = self.units_combo.currentData() or "metric"
        if system not in ("metric", "imperial"):
            system = "metric"
        self.measurement_system = system
        self._prefs.set_measurement_system(system)
        session_state.set_measurement_system(system)
        sc_units.set_units("in" if system == "imperial" else "mm")
        self._update_unit_labels()
        self._refresh_preset_labels()
        # Re-apply stored mm values to display in new units
        sheet_w, sheet_h = session_state.get_sheet_size()
        kerf_mm = session_state.get_kerf_mm() or self._prefs.get_default_kerf_mm()
        margin_mm = session_state.get_gap_mm() or self._prefs.get_default_spacing_mm()
        kerf_width = session_state.get_kerf_width_mm() or self._prefs.get_default_kerf_mm()

        should_apply_new_defaults = sheet_w is None or sheet_h is None
        if not should_apply_new_defaults and previous_system in ("metric", "imperial"):
            prev_defaults = self._prefs.get_default_sheet_size_mm(previous_system)
            should_apply_new_defaults = self._sheet_matches_defaults(sheet_w, sheet_h, prev_defaults)

        if should_apply_new_defaults:
            sheet_w, sheet_h = self._prefs.get_default_sheet_size_mm(self.measurement_system)
            session_state.set_sheet_size(sheet_w, sheet_h)

        for edit, value in (
            (self.sheet_width_edit, sheet_w),
            (self.sheet_height_edit, sheet_h),
            (self.kerf_edit, kerf_mm),
            (self.margin_edit, margin_mm),
            (self.kerf_width_edit, kerf_width),
        ):
            edit.blockSignals(True)
            self._set_length_text(edit, float(value))
            edit.blockSignals(False)

        self._populate_table(session_state.get_panels())
        self.update_run_button_state()
        if self.doc is not None:
            try:
                session.sync_doc_from_state(self.doc, self.measurement_system)
            except Exception:
                pass

    def _on_export_options_changed(self) -> None:
        """Persist export options into preferences."""
        self._prefs.set_export_include_labels(bool(self.include_labels_check.isChecked()))
        self._prefs.set_export_include_dimensions(bool(self.include_dimensions_check.isChecked()))

    def _update_unit_labels(self) -> None:
        """Update labels to reflect current measurement system."""
        unit = self._unit_label()
        self.sheet_width_label.setText(f"Width ({unit}):")
        self.sheet_height_label.setText(f"Height ({unit}):")
        self.kerf_label.setText(f"Kerf width ({unit}):")
        self.margin_label.setText(f"Edge margin ({unit}):")
        self.kerf_width_label.setText(f"Kerf Width ({unit}):")
        self._update_table_headers()

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
        default_width, default_height = self._prefs.get_default_sheet_size_mm(self.measurement_system)
        self._set_length_text(self.sheet_width_edit, default_width)
        self._set_length_text(self.sheet_height_edit, default_height)
        self._set_length_text(self.kerf_edit, self._prefs.get_default_kerf_mm())
        self._set_length_text(self.margin_edit, self._prefs.get_default_spacing_mm())
        self.allow_90_check.setChecked(False)
        self.allow_180_check.setChecked(False)
        self.mode_combo.setCurrentIndex(0)
        self.cut_mode_check.setChecked(self._prefs.get_default_optimize_for_cut_path())
        self._set_length_text(self.kerf_width_edit, self._prefs.get_default_kerf_mm())
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

    def _on_view_source_clicked(self):
        """
        Switch to 'Source panels' view: show sources, hide sheets, fit view.
        """
        self.btnViewSource.setChecked(True)
        self.btnViewSheets.setChecked(False)

        doc = App.ActiveDocument
        if doc is None:
            return

        view_controller.show_source_view(doc)

    def _on_view_sheets_clicked(self):
        """
        Switch to 'Nested sheets' view: show sheets, hide sources, fit view.
        """
        self.btnViewSource.setChecked(False)
        self.btnViewSheets.setChecked(True)

        doc = App.ActiveDocument
        if doc is None:
            return

        sheet_objs = session.get_sheet_objects()
        active_sheet = sheet_objs[0] if sheet_objs else None
        view_controller.show_nesting_view(doc, active_sheet=active_sheet)

    def on_show_source_panels(self):
        doc = App.ActiveDocument
        if doc is None:
            return

        view_controller.show_source_view(doc)

    def on_preview_clicked(self):
        try:
            Gui.runCommand("SquatchCut_RunNesting")
        except Exception as e:
            logger.error(f"Failed to run preview nesting: {e!r}")

    def on_apply_clicked(self):
        try:
            Gui.runCommand("SquatchCut_ApplyNesting")
        except Exception as e:
            logger.error(f"Failed to apply nesting: {e!r}")

    def on_export_cutlist_clicked(self):
        """Trigger export cutlist command."""
        try:
            Gui.runCommand("SquatchCut_ExportCutlist")
        except Exception as e:
            logger.error(f"Failed to export cutlist: {e!r}")

    # ---------------- Task panel API ----------------

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


# Factory for tests
def create_main_panel_for_tests():
    """
    Factory used by GUI tests to instantiate the main SquatchCut task panel
    without going through FreeCAD's dialog machinery.
    """
    SquatchCutTaskPanel._test_force_measurement_system = session_state.get_measurement_system()
    return SquatchCutTaskPanel()
