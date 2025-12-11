"""SquatchCut Settings panel for managing global defaults."""

from __future__ import annotations

from SquatchCut import settings
from SquatchCut.core import gui_tests, logger, sheet_presets
from SquatchCut.core import units as sc_units
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core.units import mm_to_inches
from SquatchCut.freecad_integration import Gui
from SquatchCut.gui.qt_compat import QtWidgets


class _UnitRadioProxy:
    """Lightweight proxy to mimic unit radio buttons for GUI tests."""

    def __init__(self, panel, value: str):
        self._panel = panel
        self._value = value

    def isChecked(self) -> bool:
        return (getattr(self._panel, "measurement_system", None) or "metric") == self._value

    def setChecked(self, checked: bool) -> None:
        if not checked:
            return
        idx = self._panel.units_combo.findData(self._value)
        if idx >= 0:
            self._panel.units_combo.setCurrentIndex(idx)
            self._panel.measurement_system = self._value
            if hasattr(self._panel, "_on_units_changed"):
                self._panel._on_units_changed()


class SquatchCutSettingsPanel(QtWidgets.QWidget):
    """Settings TaskPanel that edits global SquatchCut defaults."""

    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            settings.hydrate_from_params()
        except Exception:
            pass
        self.form = self
        self._close_callback = None
        self._prefs = SquatchCutPreferences()
        system = self._determine_measurement_system()
        self.measurement_system = system
        self._initial_state = self._compute_initial_state(system)
        self._build_ui()
        # Compatibility proxies for GUI tests that expect unit radio buttons.
        self.rbUnitsMetric = _UnitRadioProxy(self, "metric")
        self.rbUnitsImperial = _UnitRadioProxy(self, "imperial")
        self._apply_initial_state(self._initial_state)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        layout.addWidget(self._build_units_group())
        layout.addWidget(self._build_sheet_defaults_group())
        layout.addWidget(self._build_cut_defaults_group())
        layout.addWidget(self._build_rotation_group())

        # Developer Mode Checkbox (always visible)
        self.developer_mode_check = QtWidgets.QCheckBox("Enable Developer Mode")
        self.developer_mode_check.setToolTip("Show advanced logging and developer tools.")
        self.developer_mode_check.toggled.connect(self._on_developer_mode_toggled)
        layout.addWidget(self.developer_mode_check)

        # Developer Tools Group (gated by checkbox)
        self.developer_group_box = self._build_developer_group()
        layout.addWidget(self.developer_group_box)

        layout.addStretch(1)

    def _build_units_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Measurement system")
        row = QtWidgets.QHBoxLayout(group)
        self.units_combo = QtWidgets.QComboBox()
        self.units_combo.addItem("Metric (mm)", "metric")
        self.units_combo.addItem("Imperial (in)", "imperial")
        self.units_combo.currentIndexChanged.connect(self._on_units_changed)
        row.addWidget(self.units_combo)
        row.addStretch(1)
        return group

    def _build_sheet_defaults_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Sheet size defaults")
        form = QtWidgets.QFormLayout(group)

        self.sheet_width_edit = QtWidgets.QLineEdit()
        self.sheet_height_edit = QtWidgets.QLineEdit()

        self.sheet_width_label = QtWidgets.QLabel()
        self.sheet_height_label = QtWidgets.QLabel()

        form.addRow(self.sheet_width_label, self.sheet_width_edit)
        form.addRow(self.sheet_height_label, self.sheet_height_edit)

        return group

    def _build_cut_defaults_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Cutting defaults")
        form = QtWidgets.QFormLayout(group)

        self.kerf_edit = QtWidgets.QLineEdit()
        self.gap_edit = QtWidgets.QLineEdit()

        self.kerf_label = QtWidgets.QLabel("Default kerf:")
        self.gap_label = QtWidgets.QLabel("Default gap (mm):")

        form.addRow(self.kerf_label, self.kerf_edit)
        form.addRow(self.gap_label, self.gap_edit)
        return group

    def _build_rotation_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Rotation defaults")
        layout = QtWidgets.QVBoxLayout(group)
        self.allow_rotation_check = QtWidgets.QCheckBox("Allow rotation by default")
        self.allow_rotation_check.setToolTip("Applied when CSV panels omit orientation flags.")
        layout.addWidget(self.allow_rotation_check)
        return group

    def _build_developer_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Developer tools")
        layout = QtWidgets.QVBoxLayout(group)

        # Logging Controls
        log_form = QtWidgets.QFormLayout()

        self.log_level_report_combo = QtWidgets.QComboBox()
        self.log_level_report_combo.addItem("None", "none")
        self.log_level_report_combo.addItem("Normal", "normal")
        self.log_level_report_combo.addItem("Verbose", "verbose")
        log_form.addRow("Report View Log Level:", self.log_level_report_combo)

        self.log_level_console_combo = QtWidgets.QComboBox()
        self.log_level_console_combo.addItem("None", "none")
        self.log_level_console_combo.addItem("Normal", "normal")
        self.log_level_console_combo.addItem("Verbose", "verbose")
        log_form.addRow("Python Console Log Level:", self.log_level_console_combo)

        layout.addLayout(log_form)

        # GUI Test Suite
        helper = QtWidgets.QLabel("Run the SquatchCut GUI test suite inside FreeCAD.")
        if hasattr(helper, "setWordWrap"):
            helper.setWordWrap(True)
        layout.addWidget(helper)

        self.run_gui_tests_button = QtWidgets.QPushButton("Run GUI Test Suite")
        self.run_gui_tests_button.setToolTip("Run SquatchCut's GUI regression suite. Results are logged to the Report view.")
        self.run_gui_tests_button.clicked.connect(self.on_run_gui_tests_clicked)
        layout.addWidget(self.run_gui_tests_button)

        self.dev_tools_status_label = QtWidgets.QLabel()
        self.dev_tools_status_label.setStyleSheet("color: gray;")
        self._set_dev_tools_status("Ready")
        layout.addWidget(self.dev_tools_status_label)

        return group

    def _on_developer_mode_toggled(self) -> None:
        is_dev = self.developer_mode_check.isChecked()
        self.developer_group_box.setVisible(is_dev)

    def _determine_measurement_system(self, preferred: str | None = None) -> str:
        if preferred in ("metric", "imperial"):
            return preferred
        ms_from_units = "imperial" if sc_units.get_units() == "in" else "metric"
        ms_from_prefs = self._prefs.get_measurement_system()
        measurement_system = ms_from_units or ms_from_prefs or "metric"
        if measurement_system not in ("metric", "imperial"):
            measurement_system = "metric"
        return measurement_system

    def _compute_initial_state(self, measurement_system: str) -> dict:
        has_defaults = self._prefs.has_default_sheet_size(measurement_system)
        if has_defaults:
            width_mm, height_mm = self._prefs.get_default_sheet_size_mm(measurement_system)
        else:
            width_mm, height_mm = sheet_presets.get_factory_default_sheet_size(measurement_system)

        return {
            "measurement_system": measurement_system,
            "sheet_width_mm": width_mm,
            "sheet_height_mm": height_mm,
            "kerf_mm": self._prefs.get_default_kerf_mm(system=measurement_system),
            "gap_mm": self._prefs.get_default_spacing_mm(system=measurement_system),
            "allow_rotate": self._prefs.get_default_allow_rotate(),
            "developer_mode": self._prefs.get_developer_mode(),
            "log_level_report": self._prefs.get_report_view_log_level(),
            "log_level_console": self._prefs.get_python_console_log_level(),
        }

    def _apply_initial_state(self, state: dict) -> None:
        if not state:
            return
        self.measurement_system = state.get("measurement_system", "metric")
        idx = self.units_combo.findData(self.measurement_system)
        if idx < 0:
            idx = 0
        self.units_combo.blockSignals(True)
        self.units_combo.setCurrentIndex(idx)
        self.units_combo.blockSignals(False)
        self._update_unit_labels()

        self._set_length_text(self.sheet_width_edit, state.get("sheet_width_mm"))
        self._set_length_text(self.sheet_height_edit, state.get("sheet_height_mm"))
        self._set_length_text(self.kerf_edit, state.get("kerf_mm"))

        gap_value = state.get("gap_mm")
        if gap_value is None:
            self.gap_edit.clear()
        else:
            self.gap_edit.setText(str(gap_value))
        self.allow_rotation_check.setChecked(bool(state.get("allow_rotate")))

        # Developer Mode & Logging
        dev_mode = bool(state.get("developer_mode", False))
        self.developer_mode_check.setChecked(dev_mode)
        self._on_developer_mode_toggled()  # Sync visibility

        report_level = state.get("log_level_report", "normal")
        idx_r = self.log_level_report_combo.findData(report_level)
        if idx_r >= 0:
            self.log_level_report_combo.setCurrentIndex(idx_r)

        console_level = state.get("log_level_console", "none")
        idx_c = self.log_level_console_combo.findData(console_level)
        if idx_c >= 0:
            self.log_level_console_combo.setCurrentIndex(idx_c)

    def _set_length_text(self, widget: QtWidgets.QLineEdit, value_mm: float | None) -> None:
        if value_mm is None:
            widget.clear()
            return
        widget.setText(sc_units.format_length(value_mm, self.measurement_system))

    def _parse_length(self, widget: QtWidgets.QLineEdit, name: str) -> float | None:
        text = widget.text().strip()
        if not text:
            return None
        try:
            return sc_units.parse_length(text, self.measurement_system)
        except Exception as exc:
            raise ValueError(f"Invalid value for {name}: {exc}") from exc

    def _apply_changes(self) -> bool:
        try:
            width_mm = self._parse_length(self.sheet_width_edit, "Sheet width")
            height_mm = self._parse_length(self.sheet_height_edit, "Sheet height")
            kerf_mm = self._parse_length(self.kerf_edit, "Kerf")
            gap = float(self.gap_edit.text().strip()) if self.gap_edit.text().strip() else None
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "SquatchCut", str(exc))
            return False

        if kerf_mm is None:
            QtWidgets.QMessageBox.warning(self, "SquatchCut", "Kerf must not be blank.")
            return False

        system = self.units_combo.currentData() or "metric"
        system = "imperial" if system == "imperial" else "metric"
        self._prefs.set_measurement_system(system)
        if system == "imperial":
            width_in = mm_to_inches(width_mm) if width_mm is not None else None
            height_in = mm_to_inches(height_mm) if height_mm is not None else None
            if width_in is not None and height_in is not None:
                self._prefs.set_default_sheet_width_in(width_in)
                self._prefs.set_default_sheet_height_in(height_in)
            else:
                self._prefs.clear_default_sheet_size_for_system("imperial")
        else:
            if width_mm is not None and height_mm is not None:
                self._prefs.set_default_sheet_width_mm(width_mm)
                self._prefs.set_default_sheet_height_mm(height_mm)
            else:
                self._prefs.clear_default_sheet_size_for_system("metric")
        self._prefs.set_default_kerf_mm(kerf_mm)
        if gap is not None:
            self._prefs.set_default_spacing_mm(gap)
        self._prefs.set_default_allow_rotate(self.allow_rotation_check.isChecked())

        # Save Developer Mode
        self._prefs.set_developer_mode(self.developer_mode_check.isChecked())

        # Save Log Levels
        report_level = self.log_level_report_combo.currentData()
        if report_level:
            self._prefs.set_report_view_log_level(report_level)

        console_level = self.log_level_console_combo.currentData()
        if console_level:
            self._prefs.set_python_console_log_level(console_level)

        return True

    def _on_units_changed(self) -> None:
        system = self.units_combo.currentData() or "metric"
        system = "imperial" if system == "imperial" else "metric"
        self.measurement_system = system
        sc_units.set_units("in" if system == "imperial" else "mm")
        self._update_unit_labels()
        state = self._compute_initial_state(system)
        self._apply_initial_state(state)

    def _update_unit_labels(self) -> None:
        unit_label = sc_units.unit_label_for_system(self.measurement_system)
        self.sheet_width_label.setText(f"Default sheet width ({unit_label}):")
        self.sheet_height_label.setText(f"Default sheet height ({unit_label}):")
        self.kerf_label.setText(f"Default kerf ({unit_label}):")
        self.gap_label.setText("Default gap (mm):")

    def _set_dev_tools_status(self, message: str) -> None:
        if hasattr(self, "dev_tools_status_label"):
            self.dev_tools_status_label.setText(f"Status: {message}")

    def on_run_gui_tests_clicked(self) -> None:
        """Run the SquatchCut GUI test suite from the settings panel."""
        self._set_dev_tools_status("Running GUI tests...")
        try:
            results = gui_tests.run_gui_test_suite_from_freecad()
        except Exception as exc:
            logger.error(f"GUI tests failed to start: {exc!r}")
            self._set_dev_tools_status("GUI tests failed to run. See Report view.")
            return

        if results is None:
            self._set_dev_tools_status("GUI tests failed to run. See Report view.")
            return

        passed = sum(1 for result in results if getattr(result, "passed", False))
        total = len(results)
        failed = total - passed
        if failed:
            self._set_dev_tools_status(f"GUI tests completed with {failed} failure(s). See Report view.")
        else:
            self._set_dev_tools_status("GUI tests completed successfully. See Report view.")

    def accept(self) -> None:
        if self._apply_changes() and Gui is not None:
            QtWidgets.QMessageBox.information(
                self.form, "SquatchCut", "Settings saved.", QtWidgets.QMessageBox.Ok
            )
            try:
                Gui.Control.closeDialog()
            except Exception:
                pass

    def reject(self) -> None:
        if Gui is not None:
            QtWidgets.QMessageBox.information(
                self.form,
                "SquatchCut",
                "Settings changes discarded.",
                QtWidgets.QMessageBox.Ok,
            )
            try:
                Gui.Control.closeDialog()
            except Exception:
                pass

    def getWidget(self):
        return self

    def set_close_callback(self, callback):
        self._close_callback = callback

    def closeEvent(self, event):
        if self._close_callback is not None:
            try:
                self._close_callback()
            except Exception:
                pass
        super().closeEvent(event)


TaskPanel_Settings = SquatchCutSettingsPanel


def create_settings_panel_for_tests():
    """Factory used by GUI tests to build a settings panel instance."""
    prefs = SquatchCutPreferences()
    current_units = sc_units.get_units()
    prefs.set_measurement_system("imperial" if current_units == "in" else "metric")
    settings.hydrate_from_params()
    return SquatchCutSettingsPanel()
