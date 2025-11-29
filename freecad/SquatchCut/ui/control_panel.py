import os

try:
    import FreeCAD
    import FreeCADGui
except Exception:
    FreeCAD = None
    FreeCADGui = None

from SquatchCut.gui.qt_compat import QtWidgets

from SquatchCut.core import session, session_state
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core import logger
from SquatchCut.core import units as sc_units
from SquatchCut.core.units import mm_to_inches, inches_to_mm
from SquatchCut.ui.messages import show_info, show_error
from SquatchCut.gui.commands.cmd_import_csv import run_csv_import
from SquatchCut.gui.commands import cmd_run_nesting


class SquatchCutControlPanel:
    """
    Unified control panel for SquatchCut:

    - Sheet size (mm)
    - Cutting parameters (kerf, gap)
    - Default rotation behavior
    - CSV path selection
    - Import + Nest button
    """

    def __init__(self, doc=None):
        if doc is None:
            doc = FreeCAD.ActiveDocument
        self.doc = doc

        if self.doc is not None:
            session.sync_state_from_doc(self.doc)

        # Build root widget + layout
        self.form = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(self.form)

        # Fetch current state
        sheet_w, sheet_h = session_state.get_sheet_size()
        kerf_mm = session_state.get_kerf_mm()
        gap_mm = session_state.get_gap_mm()
        default_allow = session_state.get_default_allow_rotate()
        prefs = SquatchCutPreferences()
        self.measurement_system = prefs.get_measurement_system()

        if sheet_w is None:
            sheet_w = prefs.get_default_sheet_width_mm()
        if sheet_h is None:
            sheet_h = prefs.get_default_sheet_height_mm()

        # ---------------- Sheet Size group ----------------
        sheet_group = QtWidgets.QGroupBox("Sheet Size")
        sheet_layout = QtWidgets.QFormLayout(sheet_group)

        self.units_combo = QtWidgets.QComboBox()
        self.units_combo.addItem("Metric (mm)", "metric")
        self.units_combo.addItem("Imperial (in)", "imperial")
        unit_idx = self.units_combo.findData(self.measurement_system)
        if unit_idx < 0:
            unit_idx = 0
        self.units_combo.setCurrentIndex(unit_idx)

        self.sheet_width_label = QtWidgets.QLabel()
        self.sheet_width_spin = QtWidgets.QDoubleSpinBox()
        self.sheet_width_spin.setRange(1.0, 100000.0)
        self.sheet_width_spin.setDecimals(3)
        self.sheet_width_spin.setSingleStep(10.0)

        self.sheet_height_label = QtWidgets.QLabel()
        self.sheet_height_spin = QtWidgets.QDoubleSpinBox()
        self.sheet_height_spin.setRange(1.0, 100000.0)
        self.sheet_height_spin.setDecimals(3)
        self.sheet_height_spin.setSingleStep(10.0)

        sheet_layout.addRow("Units:", self.units_combo)
        sheet_layout.addRow(self.sheet_width_label, self.sheet_width_spin)
        sheet_layout.addRow(self.sheet_height_label, self.sheet_height_spin)

        main_layout.addWidget(sheet_group)

        # ---------------- Cutting Parameters group ----------------
        cut_group = QtWidgets.QGroupBox("Cutting Parameters")
        cut_layout = QtWidgets.QFormLayout(cut_group)

        self.kerf_spin = QtWidgets.QDoubleSpinBox()
        self.kerf_spin.setRange(0.0, 100.0)
        self.kerf_spin.setDecimals(2)
        self.kerf_spin.setSingleStep(0.1)
        self.kerf_spin.setValue(kerf_mm)

        self.gap_spin = QtWidgets.QDoubleSpinBox()
        self.gap_spin.setRange(0.0, 100.0)
        self.gap_spin.setDecimals(2)
        self.gap_spin.setSingleStep(0.1)
        self.gap_spin.setValue(gap_mm)

        cut_layout.addRow("Kerf (mm):", self.kerf_spin)
        cut_layout.addRow("Additional gap (mm):", self.gap_spin)

        main_layout.addWidget(cut_group)

        # Apply initial unit conversions to sheet size and spacing
        self._update_unit_labels()
        display_w = self._to_display_units(float(sheet_w))
        display_h = self._to_display_units(float(sheet_h))
        self.sheet_width_spin.setValue(display_w)
        self.sheet_height_spin.setValue(display_h)
        self.kerf_spin.setValue(self._to_display_units(float(kerf_mm)))
        self.gap_spin.setValue(self._to_display_units(float(gap_mm)))

        # ---------------- Rotation group ----------------
        rot_group = QtWidgets.QGroupBox("Rotation")
        rot_layout = QtWidgets.QVBoxLayout(rot_group)

        self.default_rotate_check = QtWidgets.QCheckBox("Allow rotation by default")
        self.default_rotate_check.setChecked(default_allow)
        rot_layout.addWidget(self.default_rotate_check)

        rot_helper = QtWidgets.QLabel(
            "If a CSV does not specify per-part rotation, this default will be used."
        )
        rot_helper.setWordWrap(True)
        rot_layout.addWidget(rot_helper)

        main_layout.addWidget(rot_group)

        # ---------------- Logging group ----------------
        log_group = QtWidgets.QGroupBox("Logging")
        log_layout = QtWidgets.QFormLayout(log_group)
        self.report_log_combo = QtWidgets.QComboBox()
        self.report_log_combo.addItems(["No logging", "Normal logging", "Verbose logging"])
        self.console_log_combo = QtWidgets.QComboBox()
        self.console_log_combo.addItems(["No logging", "Normal logging", "Verbose logging"])
        prefs = SquatchCutPreferences()
        rv_level = prefs.get_report_view_log_level()
        pc_level = prefs.get_python_console_log_level()
        self.report_log_combo.setCurrentIndex(self._level_to_index(rv_level))
        self.console_log_combo.setCurrentIndex(self._level_to_index(pc_level))
        log_layout.addRow("Report View logging:", self.report_log_combo)
        log_layout.addRow("Python console logging:", self.console_log_combo)
        main_layout.addWidget(log_group)

        # ---------------- CSV Import & Nest group ----------------
        csv_group = QtWidgets.QGroupBox("CSV Import & Nesting")
        csv_layout = QtWidgets.QGridLayout(csv_group)

        self.csv_path_edit = QtWidgets.QLineEdit()
        self.csv_browse_button = QtWidgets.QPushButton("Browse…")
        self.import_and_nest_button = QtWidgets.QPushButton("Import CSV && Nest")

        csv_layout.addWidget(QtWidgets.QLabel("CSV file:"), 0, 0)
        csv_layout.addWidget(self.csv_path_edit, 0, 1)
        csv_layout.addWidget(self.csv_browse_button, 0, 2)
        csv_layout.addWidget(self.import_and_nest_button, 1, 1, 1, 2)

        main_layout.addWidget(csv_group)

        # ---------------- Footer info ----------------
        footer_label = QtWidgets.QLabel(
            "These settings are stored with this FreeCAD document and used for all SquatchCut nesting operations."
        )
        footer_label.setWordWrap(True)
        footer_label.setStyleSheet("color: gray; font-size: 10pt;")
        main_layout.addWidget(footer_label)

        main_layout.addStretch()

        # Wire up buttons
        self.csv_browse_button.clicked.connect(self._on_browse_clicked)
        self.import_and_nest_button.clicked.connect(self._on_import_and_nest_clicked)
        self.units_combo.currentIndexChanged.connect(self._on_units_changed)

    # ---------- Internal helpers ----------

    def _apply_settings_to_state_and_doc(self):
        """Apply current UI values to session_state and the document."""
        if self.doc is None:
            FreeCAD.Console.PrintError("[SquatchCut] No active document in ControlPanel._apply_settings_to_state_and_doc().\n")
            return

        sheet_w = self._to_mm(float(self.sheet_width_spin.value()))
        sheet_h = self._to_mm(float(self.sheet_height_spin.value()))
        kerf_mm = self._to_mm(float(self.kerf_spin.value()))
        gap_mm = self._to_mm(float(self.gap_spin.value()))
        default_allow = bool(self.default_rotate_check.isChecked())
        prefs = SquatchCutPreferences()
        prefs.set_measurement_system(self.measurement_system)
        sc_units.set_units("in" if self.measurement_system == "imperial" else "mm")
        session_state.set_measurement_system(self.measurement_system)
        prefs.set_default_sheet_width_mm(sheet_w)
        prefs.set_default_sheet_height_mm(sheet_h)

        session_state.set_sheet_size(sheet_w, sheet_h)
        session_state.set_kerf_mm(kerf_mm)
        session_state.set_gap_mm(gap_mm)
        session_state.set_default_allow_rotate(default_allow)
        prefs.set_report_view_log_level(self._index_to_level(self.report_log_combo.currentIndex()))
        prefs.set_python_console_log_level(self._index_to_level(self.console_log_combo.currentIndex()))

        session.sync_doc_from_state(self.doc)
        self.doc.recompute()

        logger.info(
            f"Updated settings: sheet {sheet_w} x {sheet_h} mm, kerf={kerf_mm} mm, gap={gap_mm} mm, default_allow_rotate={default_allow}"
        )

    def _on_units_changed(self):
        """Handle measurement system toggle."""
        system = self.units_combo.currentData() or "metric"
        if system not in ("metric", "imperial"):
            system = "metric"
        self.measurement_system = system
        self._update_unit_labels()
        # Re-apply conversions to current values to keep display consistent
        sheet_w_mm = session_state.get_sheet_size()[0] or SquatchCutPreferences().get_default_sheet_width_mm()
        sheet_h_mm = session_state.get_sheet_size()[1] or SquatchCutPreferences().get_default_sheet_height_mm()
        self.sheet_width_spin.setValue(self._to_display_units(float(sheet_w_mm)))
        self.sheet_height_spin.setValue(self._to_display_units(float(sheet_h_mm)))
        self.kerf_spin.setValue(self._to_display_units(float(session_state.get_kerf_mm())))
        self.gap_spin.setValue(self._to_display_units(float(session_state.get_gap_mm())))

    def _update_unit_labels(self):
        unit = "in" if self.measurement_system == "imperial" else "mm"
        self.sheet_width_label.setText(f"Width ({unit}):")
        self.sheet_height_label.setText(f"Height ({unit}):")
        self.kerf_spin.setSuffix(f" {unit}")
        self.gap_spin.setSuffix(f" {unit}")
        # Ensure spin ranges are reasonable for inches
        step = 1.0 if unit == "in" else 10.0
        self.sheet_width_spin.setSingleStep(step)
        self.sheet_height_spin.setSingleStep(step)

    def _to_mm(self, value: float) -> float:
        """Convert a value in current display units to mm."""
        if self.measurement_system == "imperial":
            return inches_to_mm(value)
        return float(value)

    def _to_display_units(self, value_mm: float) -> float:
        """Convert an internal mm value to current display units."""
        if self.measurement_system == "imperial":
            return mm_to_inches(value_mm)
        return float(value_mm)

    def _on_browse_clicked(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dlg.setNameFilter("CSV files (*.csv)")
        dlg.setWindowTitle("Select panels CSV for SquatchCut")

        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        files = dlg.selectedFiles()
        if not files:
            return

        self.csv_path_edit.setText(files[0])

    def _on_import_and_nest_clicked(self):
        if self.doc is None:
            show_error("No active document for CSV import and nesting.", title="SquatchCut")
            return

        csv_path = self.csv_path_edit.text().strip()
        if not csv_path:
            show_error("Please choose a CSV file first.", title="SquatchCut")
            return

        if not os.path.isfile(csv_path):
            show_error(f"CSV file not found:\n{csv_path}", title="SquatchCut")
            return

        # Apply settings before import & nest
        self._apply_settings_to_state_and_doc()

        # Run CSV import
        try:
            prefs = SquatchCutPreferences()
            csv_units = prefs.get_csv_units(prefs.get_measurement_system())
            run_csv_import(self.doc, csv_path, csv_units=csv_units)
            prefs.set_csv_units(csv_units)
        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            show_error(f"CSV import failed:\n{e}", title="SquatchCut")
            return

        # Run nesting using the existing command
        try:
            cmd = cmd_run_nesting.RunNestingCommand()
            cmd.Activated()
        except Exception as e:
            logger.error(f"Nesting failed after CSV import: {e}")
            show_error(f"Nesting failed after CSV import:\n{e}", title="SquatchCut")
            return

        show_info("CSV imported and nesting completed.", title="SquatchCut")
        logger.info("Import + Nest completed from control panel.")

    # ---------- FreeCAD TaskPanel API ----------

    def accept(self):
        """Called when user clicks OK on the TaskPanel wrapper."""
        if self.doc is None:
            logger.error("No active document in ControlPanel.accept().")
            FreeCADGui.Control.closeDialog()
            return

        self._apply_settings_to_state_and_doc()
        FreeCADGui.Control.closeDialog()

    def reject(self):
        """Called when user clicks Cancel/Close in the TaskPanel wrapper."""
        FreeCADGui.Control.closeDialog()

    def _level_to_index(self, level: str) -> int:
        return {"none": 0, "normal": 1, "verbose": 2}.get(level, 1)

    def _index_to_level(self, idx: int) -> str:
        return {0: "none", 1: "normal", 2: "verbose"}.get(idx, "normal")
