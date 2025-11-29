import os

try:
    import FreeCAD
    import FreeCADGui
except Exception:
    FreeCAD = None
    FreeCADGui = None

from SquatchCut.gui.qt_compat import QtWidgets
from SquatchCut import settings

from SquatchCut.core import session, session_state
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core import logger
from SquatchCut.core import units as sc_units
from SquatchCut.core.units import (
    format_length,
    parse_length,
    unit_label_for_system,
)
from SquatchCut.ui.messages import show_info, show_error
from SquatchCut.gui.commands.cmd_import_csv import run_csv_import
from SquatchCut.gui.commands import cmd_run_gui_tests, cmd_run_nesting


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

        # Ensure session_state reflects persisted preferences before reading it.
        try:
            settings.hydrate_from_params()
        except Exception:
            pass

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
        self.measurement_system = session_state.get_measurement_system()

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
        self.sheet_width_edit = QtWidgets.QLineEdit()
        self.sheet_height_label = QtWidgets.QLabel()
        self.sheet_height_edit = QtWidgets.QLineEdit()

        sheet_layout.addRow("Units:", self.units_combo)
        sheet_layout.addRow(self.sheet_width_label, self.sheet_width_edit)
        sheet_layout.addRow(self.sheet_height_label, self.sheet_height_edit)

        main_layout.addWidget(sheet_group)

        # ---------------- Cutting Parameters group ----------------
        cut_group = QtWidgets.QGroupBox("Cutting Parameters")
        cut_layout = QtWidgets.QFormLayout(cut_group)

        self.kerf_label = QtWidgets.QLabel()
        self.kerf_edit = QtWidgets.QLineEdit()
        self.gap_label = QtWidgets.QLabel()
        self.gap_edit = QtWidgets.QLineEdit()

        cut_layout.addRow(self.kerf_label, self.kerf_edit)
        cut_layout.addRow(self.gap_label, self.gap_edit)

        main_layout.addWidget(cut_group)

        # Apply initial unit conversions to sheet size and spacing
        self._update_unit_labels()
        self._set_length_text(self.sheet_width_edit, float(sheet_w))
        self._set_length_text(self.sheet_height_edit, float(sheet_h))
        self._set_length_text(self.kerf_edit, float(kerf_mm))
        self._set_length_text(self.gap_edit, float(gap_mm))

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
        dev_mode_enabled = prefs.get_developer_mode()
        self.dev_mode_checkbox.setChecked(dev_mode_enabled)
        self._update_developer_group_visibility()
        log_layout.addRow("Report View logging:", self.report_log_combo)
        log_layout.addRow("Python console logging:", self.console_log_combo)
        main_layout.addWidget(log_group)

        dev_toggle_layout = QtWidgets.QHBoxLayout()
        self.dev_mode_checkbox = QtWidgets.QCheckBox("Enable developer mode")
        self.dev_mode_checkbox.setToolTip("Show additional developer tools and diagnostics for SquatchCut.")
        dev_toggle_layout.addWidget(self.dev_mode_checkbox)
        dev_toggle_layout.addStretch(1)
        main_layout.addLayout(dev_toggle_layout)

        self.developer_group = QtWidgets.QGroupBox("Developer tools")
        dev_layout = QtWidgets.QHBoxLayout(self.developer_group)
        self.dev_logging_button = QtWidgets.QPushButton("Use developer logging")
        self.run_gui_tests_button = QtWidgets.QPushButton("Run GUI Tests")
        dev_layout.addWidget(self.dev_logging_button)
        dev_layout.addWidget(self.run_gui_tests_button)
        main_layout.addWidget(self.developer_group)

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
        self.dev_mode_checkbox.toggled.connect(self._on_dev_mode_toggled)
        self.dev_logging_button.clicked.connect(self._set_developer_logging)
        self.run_gui_tests_button.clicked.connect(self._run_gui_tests_command)

    # ---------- Internal helpers ----------

    def _apply_settings_to_state_and_doc(self):
        """Apply current UI values to session_state and the document."""
        if self.doc is None:
            FreeCAD.Console.PrintError("[SquatchCut] No active document in ControlPanel._apply_settings_to_state_and_doc().\n")
            return

        try:
            sheet_w = self._parse_length_text(self.sheet_width_edit.text())
            sheet_h = self._parse_length_text(self.sheet_height_edit.text())
            kerf_mm = self._parse_length_text(self.kerf_edit.text())
            gap_mm = self._parse_length_text(self.gap_edit.text())
        except ValueError as exc:
            self._handle_parse_error(exc)
            return
        default_allow = bool(self.default_rotate_check.isChecked())
        prefs = SquatchCutPreferences()
        prefs.set_measurement_system(self.measurement_system)
        sc_units.set_units("in" if self.measurement_system == "imperial" else "mm")
        session_state.set_measurement_system(self.measurement_system)
        prefs.set_default_sheet_width_mm(sheet_w)
        prefs.set_default_sheet_height_mm(sheet_h)
        prefs.set_default_kerf_mm(kerf_mm)
        prefs.set_default_spacing_mm(gap_mm)

        session_state.set_sheet_size(sheet_w, sheet_h)
        session_state.set_kerf_mm(kerf_mm)
        session_state.set_gap_mm(gap_mm)
        session_state.set_default_allow_rotate(default_allow)
        prefs.set_report_view_log_level(self._index_to_level(self.report_log_combo.currentIndex()))
        prefs.set_python_console_log_level(self._index_to_level(self.console_log_combo.currentIndex()))
        prefs.set_developer_mode(bool(self.dev_mode_checkbox.isChecked()))

        try:
            settings.hydrate_from_params()
        except Exception:
            pass

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
        try:
            SquatchCutPreferences().set_measurement_system(system)
        except Exception:
            pass
        self._update_unit_labels()
        # Re-apply conversions to current values to keep display consistent
        sheet_w_mm = session_state.get_sheet_size()[0] or SquatchCutPreferences().get_default_sheet_width_mm()
        sheet_h_mm = session_state.get_sheet_size()[1] or SquatchCutPreferences().get_default_sheet_height_mm()
        session_state.set_measurement_system(self.measurement_system)
        sc_units.set_units("in" if self.measurement_system == "imperial" else "mm")
        self._set_length_text(self.sheet_width_edit, float(sheet_w_mm))
        self._set_length_text(self.sheet_height_edit, float(sheet_h_mm))
        self._set_length_text(self.kerf_edit, float(session_state.get_kerf_mm()))
        self._set_length_text(self.gap_edit, float(session_state.get_gap_mm()))

    def _update_unit_labels(self):
        unit = unit_label_for_system(self.measurement_system)
        self.sheet_width_label.setText(f"Width ({unit}):")
        self.sheet_height_label.setText(f"Height ({unit}):")
        self.kerf_label.setText(f"Kerf width ({unit}):")
        self.gap_label.setText(f"Additional gap ({unit}):")
        self.kerf_edit.setPlaceholderText("")
        self.gap_edit.setPlaceholderText("")

    def _parse_length_text(self, text: str) -> float:
        """Parse the given text into millimeters based on the current measurement system."""
        return parse_length(text, self.measurement_system)

    def _format_length(self, value_mm: float) -> str:
        """Format a millimeter value for display in the current measurement system."""
        return format_length(value_mm, self.measurement_system)

    def _set_length_text(self, widget: QtWidgets.QLineEdit, value_mm: float) -> None:
        """Populate a line edit with a formatted length string."""
        widget.setText(self._format_length(value_mm))

    def _handle_parse_error(self, exc: Exception) -> None:
        """Show a user-friendly parse error without overwriting existing text."""
        if self.measurement_system == "imperial":
            message = "Invalid imperial value. Use formats like 48, 48.5, 48 1/2, or 48-1/2."
        else:
            message = str(exc)
        show_error(message, title="SquatchCut")
        logger.error(f"Failed to parse length input: {exc}")

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

    def _on_dev_mode_toggled(self, enabled: bool) -> None:
        prefs = SquatchCutPreferences()
        prefs.set_developer_mode(enabled)
        self._update_developer_group_visibility()

    def _update_developer_group_visibility(self) -> None:
        self.developer_group.setVisible(bool(self.dev_mode_checkbox.isChecked()))

    def _set_developer_logging(self) -> None:
        prefs = SquatchCutPreferences()
        self.report_log_combo.setCurrentIndex(self._level_to_index("verbose"))
        self.console_log_combo.setCurrentIndex(self._level_to_index("verbose"))
        prefs.set_report_view_log_level("verbose")
        prefs.set_python_console_log_level("verbose")

    def _run_gui_tests_command(self) -> None:
        if FreeCADGui is None:
            show_error("No FreeCAD GUI available for GUI tests.", title="SquatchCut")
            return
        try:
            FreeCADGui.runCommand("SquatchCut_RunGUITests")
        except Exception as exc:
            logger.error(f"RunGuiTests button failed: {exc!r}")
