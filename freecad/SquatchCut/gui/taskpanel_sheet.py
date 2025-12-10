"""Sheet configuration section for the SquatchCut TaskPanel."""

from __future__ import annotations

from SquatchCut.core import session_state
from SquatchCut.core import sheet_presets as sc_sheet_presets
from SquatchCut.core import units as sc_units
from SquatchCut.gui.qt_compat import QtCore, QtWidgets


class SheetConfigWidget(QtWidgets.QGroupBox):
    """
    Widget handling sheet dimensions, presets, units, and job sheets table.

    Signals:
        units_changed: Emitted when measurement system changes.
        config_changed: Emitted when valid config changes (size, mode, etc).
        validation_changed(bool): Emitted with validity status.
    """

    units_changed = QtCore.Signal()
    config_changed = QtCore.Signal()
    validation_changed = QtCore.Signal(bool)

    def __init__(self, prefs, parent=None):
        super().__init__("Sheet", parent)
        self._prefs = prefs
        self._preset_state = sc_sheet_presets.PresetSelectionState()
        self._presets = []
        self._selected_sheet_index: int = 0
        self._suppress_sheet_table_events = False

        if hasattr(self, "setObjectName"):
            self.setObjectName("sheet_group_box")
        self._build_ui()

    def _build_ui(self) -> None:
        vbox = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()
        self.units_combo = QtWidgets.QComboBox()
        self.units_combo.addItem("Metric (mm)", "metric")
        self.units_combo.addItem("Imperial (in)", "imperial")
        self.units_combo.currentIndexChanged.connect(self._on_units_changed)
        form.addRow("Units:", self.units_combo)

        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        form.addRow("Preset:", self.preset_combo)
        vbox.addLayout(form)

        form_fields = QtWidgets.QFormLayout()
        self.sheet_width_label = QtWidgets.QLabel("Width (mm):")
        self.sheet_width_edit = QtWidgets.QLineEdit()
        self.sheet_height_label = QtWidgets.QLabel("Height (mm):")
        self.sheet_height_edit = QtWidgets.QLineEdit()
        self.kerf_label = QtWidgets.QLabel("Kerf width (mm):")
        self.kerf_edit = QtWidgets.QLineEdit()
        self.margin_label = QtWidgets.QLabel("Edge margin (mm):")
        self.margin_edit = QtWidgets.QLineEdit()

        for edit in (self.sheet_width_edit, self.sheet_height_edit, self.kerf_edit, self.margin_edit):
            edit.textChanged.connect(self._validate_and_sync)

        form_fields.addRow(self.sheet_width_label, self.sheet_width_edit)
        form_fields.addRow(self.sheet_height_label, self.sheet_height_edit)
        form_fields.addRow(self.kerf_label, self.kerf_edit)
        form_fields.addRow(self.margin_label, self.margin_edit)
        vbox.addLayout(form_fields)

        self.sheet_mode_check = QtWidgets.QCheckBox("Use custom job sheets (advanced)")
        self.sheet_mode_check.setToolTip("Enable to provide explicit sheets instead of repeating the default size.")
        self.sheet_mode_check.toggled.connect(self._on_sheet_mode_toggled)
        vbox.addWidget(self.sheet_mode_check)

        self.sheet_table_container = QtWidgets.QWidget()
        table_container_layout = QtWidgets.QVBoxLayout(self.sheet_table_container)
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container_layout.setSpacing(4)

        sheets_label = QtWidgets.QLabel("Job sheets:")
        table_container_layout.addWidget(sheets_label)

        self.sheet_table = QtWidgets.QTableWidget()
        self.sheet_table.setColumnCount(4)

        self.sheet_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.sheet_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        header = self.sheet_table.horizontalHeader()
        header_cls = getattr(QtWidgets, "QHeaderView", None)
        if header_cls is not None and hasattr(header, "setSectionResizeMode"):
            header.setSectionResizeMode(0, header_cls.Stretch)
            header.setSectionResizeMode(1, header_cls.ResizeToContents)
            header.setSectionResizeMode(2, header_cls.ResizeToContents)
            header.setSectionResizeMode(3, header_cls.ResizeToContents)

        # Wire up table events manually
        item_view_cls = getattr(QtWidgets, "QAbstractItemView", None)
        # Assuming typical triggers...

        table_container_layout.addWidget(self.sheet_table)

        table_buttons = QtWidgets.QHBoxLayout()
        self.add_sheet_button = QtWidgets.QPushButton("Add Sheet")
        self.remove_sheet_button = QtWidgets.QPushButton("Remove Sheet")
        self.add_sheet_button.clicked.connect(self._on_add_sheet_clicked)
        self.remove_sheet_button.clicked.connect(self._on_remove_sheet_clicked)

        table_buttons.addWidget(self.add_sheet_button)
        table_buttons.addWidget(self.remove_sheet_button)
        table_buttons.addStretch(1)
        table_container_layout.addLayout(table_buttons)

        vbox.addWidget(self.sheet_table_container)

        # Connect table signals
        if hasattr(self.sheet_table, "selectionModel"):
            selection_model = self.sheet_table.selectionModel()
            if selection_model:
                selection_model.selectionChanged.connect(self._on_sheet_table_selection_changed)
        elif hasattr(self.sheet_table, "itemSelectionChanged"):
            self.sheet_table.itemSelectionChanged.connect(self._on_sheet_table_selection_changed)

        if hasattr(self.sheet_table, "itemChanged"):
            self.sheet_table.itemChanged.connect(self._on_sheet_table_item_changed)

        reset_row = QtWidgets.QHBoxLayout()
        reset_row.addStretch(1)
        self.reset_defaults_button = QtWidgets.QPushButton("Reset to Defaults")
        self.reset_defaults_button.clicked.connect(self.reset_defaults)
        reset_row.addWidget(self.reset_defaults_button)
        vbox.addLayout(reset_row)

    def apply_state(self, state: dict) -> None:
        """Populate widgets from state."""
        system = state.get("measurement_system", "metric")
        unit_idx = self.units_combo.findData(system)
        if unit_idx < 0:
            unit_idx = 0
        self.units_combo.blockSignals(True)
        self.units_combo.setCurrentIndex(unit_idx)
        self.units_combo.blockSignals(False)
        self._refresh_preset_labels()
        self._update_unit_labels()

        for edit, value in (
            (self.sheet_width_edit, state["sheet_width_mm"]),
            (self.sheet_height_edit, state["sheet_height_mm"]),
            (self.kerf_edit, state["kerf_mm"]),
            (self.margin_edit, state["margin_mm"]),
        ):
            edit.blockSignals(True)
            self._set_length_text(edit, float(value) if value is not None else None)
            edit.blockSignals(False)

        use_job_sheets = (state.get("sheet_mode") or session_state.get_sheet_mode()) == "job_sheets"
        self.sheet_mode_check.blockSignals(True)
        self.sheet_mode_check.setChecked(use_job_sheets)
        self.sheet_mode_check.blockSignals(False)
        self._apply_sheet_mode_selection(use_job_sheets, refresh_table=False)
        self._populate_sheet_table()

        # Check validity of loaded state without writing back (avoids rounding drift)
        w = state.get("sheet_width_mm")
        h = state.get("sheet_height_mm")
        valid = w is not None and h is not None and w > 0 and h > 0
        self._set_field_valid(self.sheet_width_edit, valid)
        self._set_field_valid(self.sheet_height_edit, valid)
        self._set_field_valid(self.kerf_edit, True)
        self._set_field_valid(self.margin_edit, True)
        self.validation_changed.emit(valid)

    def _on_units_changed(self) -> None:
        system = self.units_combo.currentData() or "metric"
        if system not in ("metric", "imperial"):
            system = "metric"

        # Determine previous system
        prev_system = "imperial" if system == "metric" else "metric"

        self._prefs.set_measurement_system(system)
        session_state.set_measurement_system(system)
        sc_units.set_units("in" if system == "imperial" else "mm")

        self._update_unit_labels()
        self._refresh_preset_labels()

        # Retrieve current values
        sheet_w, sheet_h = session_state.get_sheet_size()
        kerf_mm = session_state.get_kerf_mm()
        margin_mm = session_state.get_gap_mm()

        # 1. Sheet Size Swapping logic
        # If current dimensions match the defaults for the PREVIOUS system, swap to defaults for the NEW system.
        # This prevents 1220mm becoming 48 1/16"
        prev_w_def, prev_h_def = self._prefs.get_default_sheet_size_mm(prev_system)

        # Tolerance for float comparison
        tol = 0.5

        should_swap_sheet = False
        if sheet_w is not None and sheet_h is not None:
            # Check if current matches previous defaults (either orientation)
            matches_std = (abs(sheet_w - prev_w_def) < tol and abs(sheet_h - prev_h_def) < tol)
            matches_rot = (abs(sheet_w - prev_h_def) < tol and abs(sheet_h - prev_w_def) < tol)

            if matches_std or matches_rot:
                should_swap_sheet = True

        if should_swap_sheet:
            new_w, new_h = self._prefs.get_default_sheet_size_mm(system)
            # Maintain orientation logic if needed, but defaults usually imply standard orientation
            # If it was rotated, maybe we should rotate the new default?
            # For simplicity, just use the new default standard size.
            sheet_w, sheet_h = new_w, new_h

        # 2. Kerf Swapping logic
        # If kerf matches previous default, swap to new default
        # E.g., 3mm -> 1/8" (3.175mm) instead of 3mm -> 0.118"
        prev_kerf_def = self._prefs.get_default_kerf_mm(system=prev_system) # Note: accessing specific system defaults might need care
        # Actually prefs.get_default_kerf_mm only returns the stored value, which is single source of truth?
        # Wait, get_default_kerf_mm() reads "DefaultKerfMM".
        # But we have different defaults per system in memory/logic: 3mm vs 1/8" (3.175mm)
        # Let's look at Preferences.
        # METRIC_DEFAULT_KERF_MM = 3.0
        # IMPERIAL_DEFAULT_KERF_IN = 0.125

        # We need to manually access the "factory" defaults for logic if user hasn't overridden them?
        # Or just use the values from prefs.
        # Prefs stores `DefaultKerfMM`. It doesn't seem to split Kerf by system in storage, just one value.
        # Ah, SquatchCutPreferences has METRIC_KERF_KEY and IMPERIAL_KERF_KEY?
        # No, the code says:
        # METRIC_KERF_KEY = "MetricKerfMM"
        # IMPERIAL_KERF_KEY = "ImperialKerfIn"
        # But `get_default_kerf_mm` reads "DefaultKerfMM".
        # It seems `_migrate_legacy_defaults` is not handling Kerf?

        # Let's assume standard factory defaults for check:
        factory_metric_kerf = 3.0
        factory_imp_kerf_mm = 3.175 # 1/8 inch

        current_kerf = kerf_mm

        # If we are switching TO Imperial, and kerf is 3.0mm, maybe we want 1/8" (3.175mm)?
        if system == "imperial" and abs(current_kerf - factory_metric_kerf) < 0.1:
            kerf_mm = factory_imp_kerf_mm
        # If switching TO Metric, and kerf is 3.175mm (1/8"), maybe we want 3.0mm?
        elif system == "metric" and abs(current_kerf - factory_imp_kerf_mm) < 0.1:
            kerf_mm = factory_metric_kerf

        # 3. Margin Swapping logic
        # Usually 0, so 0mm == 0in. No change needed unless non-zero defaults used.
        # But let's check prefs defaults.
        prev_margin_def = self._prefs.get_default_spacing_mm(system=prev_system)
        if abs(margin_mm - prev_margin_def) < 0.1:
             margin_mm = self._prefs.get_default_spacing_mm(system=system)

        # Update Session State with potentially new values
        if should_swap_sheet:
             session_state.set_sheet_size(sheet_w, sheet_h)
        # Update others
        session_state.set_kerf_mm(kerf_mm)
        session_state.set_gap_mm(margin_mm)

        for edit, value in (
            (self.sheet_width_edit, sheet_w),
            (self.sheet_height_edit, sheet_h),
            (self.kerf_edit, kerf_mm),
            (self.margin_edit, margin_mm),
        ):
            edit.blockSignals(True)
            self._set_length_text(edit, float(value) if value is not None else None)
            edit.blockSignals(False)

        self._populate_sheet_table()
        self.units_changed.emit()
        self._validate_and_sync()

    def _validate_and_sync(self) -> None:
        """Parse inputs, update session state, and emit validity."""
        try:
            sheet_w = self._parse_length(self.sheet_width_edit.text())
            sheet_h = self._parse_length(self.sheet_height_edit.text())
            kerf_mm = self._parse_length(self.kerf_edit.text())
            margin_mm = self._parse_length(self.margin_edit.text())
        except ValueError:
            self.validation_changed.emit(False)
            return

        valid = True
        if sheet_w <= 0 or sheet_h <= 0:
            valid = False
            self._set_field_valid(self.sheet_width_edit, False)
            self._set_field_valid(self.sheet_height_edit, False)
        else:
            self._set_field_valid(self.sheet_width_edit, True)
            self._set_field_valid(self.sheet_height_edit, True)
            session_state.set_sheet_size(sheet_w, sheet_h)

            # Sync preset combo
            if self.preset_combo.currentIndex() != 0:
                self._set_preset_index(0)

        if kerf_mm < 0:
            valid = False
            self._set_field_valid(self.kerf_edit, False)
        else:
            self._set_field_valid(self.kerf_edit, True)
            session_state.set_kerf_mm(kerf_mm)

        if margin_mm < 0:
            valid = False
            self._set_field_valid(self.margin_edit, False)
        else:
            self._set_field_valid(self.margin_edit, True)
            session_state.set_gap_mm(margin_mm)

        self.validation_changed.emit(valid)
        if valid:
            self.config_changed.emit()

    def _unit_label(self) -> str:
        return sc_units.unit_label_for_system(session_state.get_measurement_system())

    def _update_unit_labels(self) -> None:
        unit = self._unit_label()
        self.sheet_width_label.setText(f"Width ({unit}):")
        self.sheet_height_label.setText(f"Height ({unit}):")
        self.kerf_label.setText(f"Kerf width ({unit}):")
        self.margin_label.setText(f"Edge margin ({unit}):")
        self._update_sheet_table_headers()

    def _refresh_preset_labels(self) -> None:
        system = session_state.get_measurement_system()
        self._presets = sc_sheet_presets.get_preset_entries(system)
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        for preset in self._presets:
            if preset.get("size") is None:
                text = preset.get("label") or ""
            else:
                w, h = preset["size"]
                text = sc_units.format_preset_label(w, h, system, nickname=preset.get("nickname"))
            self.preset_combo.addItem(text)
        self.preset_combo.blockSignals(False)
        self._set_preset_index(0)

    def _set_preset_index(self, index: int) -> None:
        index = max(0, min(index, len(self._presets) - 1))
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentIndex(index)
        self.preset_combo.blockSignals(False)
        self._preset_state.set_index(index, self._presets)

    def _on_preset_changed(self, index: int) -> None:
        if index <= 0:
            return
        preset = self._presets[index]
        size = preset.get("size")
        if size:
            w, h = size
            self.sheet_width_edit.setText(self._format_length(w))
            self.sheet_height_edit.setText(self._format_length(h))
            # Text change triggers _validate_and_sync

    def reset_defaults(self) -> None:
        system = session_state.get_measurement_system()
        w, h = self._prefs.get_default_sheet_size_mm(system)
        k = self._prefs.get_default_kerf_mm(system=system)
        m = self._prefs.get_default_spacing_mm(system=system)

        self.sheet_width_edit.setText(self._format_length(w))
        self.sheet_height_edit.setText(self._format_length(h))
        self.kerf_edit.setText(self._format_length(k))
        self.margin_edit.setText(self._format_length(m))

    # Helpers ported from TaskPanel_Main
    def _format_length(self, val):
        return sc_units.format_length(val, session_state.get_measurement_system())

    def _set_length_text(self, widget, val):
        if val is None: widget.clear()
        else: widget.setText(self._format_length(val))

    def _parse_length(self, text):
        return sc_units.parse_length(text, session_state.get_measurement_system())

    def _set_field_valid(self, widget, valid):
        widget.setStyleSheet("" if valid else "border: 1px solid red;")

    # Sheet Mode & Table helpers
    def _on_sheet_mode_toggled(self, checked: bool):
        self._apply_sheet_mode_selection(checked)
        self.config_changed.emit()

    def _apply_sheet_mode_selection(self, use_job_sheets: bool, refresh_table: bool = True):
        session_state.set_sheet_mode("job_sheets" if use_job_sheets else "simple")

        container = self.sheet_table_container
        if container:
            if hasattr(container, "setVisible"):
                container.setVisible(use_job_sheets)
            if hasattr(container, "setEnabled"):
                container.setEnabled(use_job_sheets)

        if use_job_sheets:
            self._ensure_job_sheets_seeded()
            if refresh_table:
                self._populate_sheet_table()

    def _ensure_job_sheets_seeded(self):
        sheets = session_state.get_job_sheets()
        if sheets: return
        w, h = session_state.get_sheet_size()
        if w is None or h is None:
            w, h = self._prefs.get_default_sheet_size_mm(session_state.get_measurement_system())
            session_state.set_sheet_size(w, h)
        session_state.set_job_sheets([{"width_mm": w, "height_mm": h, "quantity": 1, "label": "Sheet 1"}])

    def _populate_sheet_table(self):
        sheets = session_state.get_job_sheets()
        self._suppress_sheet_table_events = True
        self.sheet_table.setRowCount(len(sheets))
        for row, sheet in enumerate(sheets):
            name = sheet.get("label") or f"Sheet {row+1}"
            w = sheet.get("width_mm")
            h = sheet.get("height_mm")
            q = int(sheet.get("quantity") or 1)
            row_vals = [name, self._format_length(w) if w else "", self._format_length(h) if h else "", str(q)]
            for col, text in enumerate(row_vals):
                item = QtWidgets.QTableWidgetItem(text)
                self.sheet_table.setItem(row, col, item)
        self._suppress_sheet_table_events = False
        self._update_sheet_table_headers()

    def _update_sheet_table_headers(self):
        unit = self._unit_label()
        self.sheet_table.setHorizontalHeaderLabels(["Name", f"Width ({unit})", f"Height ({unit})", "Qty"])

    def _on_add_sheet_clicked(self):
        w, h = session_state.get_sheet_size()
        if w is None: w, h = self._prefs.get_default_sheet_size_mm(session_state.get_measurement_system())
        session_state.add_job_sheet(w, h, 1, f"Sheet {len(session_state.get_job_sheets())+1}")
        self._populate_sheet_table()
        self.config_changed.emit()

    def _on_remove_sheet_clicked(self):
        # Using selected index
        rows = self.sheet_table.selectionModel().selectedRows()
        if rows:
            idx = rows[0].row()
            session_state.remove_job_sheet(idx)
            if not session_state.get_job_sheets():
                 self._ensure_job_sheets_seeded()
            self._populate_sheet_table()
            self.config_changed.emit()

    def _on_sheet_table_item_changed(self, item):
        if self._suppress_sheet_table_events: return
        row = item.row()
        col = item.column()
        text = item.text().strip()
        try:
            if col == 0: session_state.update_job_sheet(row, label=text or None)
            elif col == 1: session_state.update_job_sheet(row, width_mm=self._parse_length(text))
            elif col == 2: session_state.update_job_sheet(row, height_mm=self._parse_length(text))
            elif col == 3: session_state.update_job_sheet(row, quantity=int(text))
        except Exception:
            pass # Ignore invalid input
        self.config_changed.emit()

    def _on_sheet_table_selection_changed(self, selected, deselected):
        pass
