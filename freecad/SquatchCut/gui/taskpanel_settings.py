"""SquatchCut Settings panel for managing global defaults."""

from __future__ import annotations

try:
    import FreeCADGui as Gui
except Exception:
    Gui = None

from SquatchCut.gui.qt_compat import QtWidgets
from SquatchCut.core.preferences import SquatchCutPreferences


class SquatchCutSettingsPanel(QtWidgets.QWidget):
    """Settings TaskPanel that edits global SquatchCut defaults."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.form = self
        self._close_callback = None
        self._prefs = SquatchCutPreferences()
        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        layout.addWidget(self._build_units_group())
        layout.addWidget(self._build_sheet_defaults_group())
        layout.addWidget(self._build_cut_defaults_group())
        layout.addWidget(self._build_rotation_group())
        layout.addWidget(self._build_optimization_group())
        layout.addWidget(self._build_logging_group())

        layout.addStretch(1)

    def _build_units_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Measurement system")
        row = QtWidgets.QHBoxLayout(group)
        self.units_combo = QtWidgets.QComboBox()
        self.units_combo.addItem("Metric (mm)", "metric")
        self.units_combo.addItem("Imperial (in)", "imperial")
        row.addWidget(self.units_combo)
        row.addStretch(1)
        return group

    def _build_sheet_defaults_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Sheet size defaults")
        form = QtWidgets.QFormLayout(group)

        self.imperial_width_edit = QtWidgets.QLineEdit()
        self.imperial_height_edit = QtWidgets.QLineEdit()
        self.metric_width_edit = QtWidgets.QLineEdit()
        self.metric_height_edit = QtWidgets.QLineEdit()

        form.addRow("Imperial width (in):", self.imperial_width_edit)
        form.addRow("Imperial height (in):", self.imperial_height_edit)
        form.addRow("Metric width (mm):", self.metric_width_edit)
        form.addRow("Metric height (mm):", self.metric_height_edit)

        return group

    def _build_cut_defaults_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Cutting defaults")
        form = QtWidgets.QFormLayout(group)

        self.kerf_edit = QtWidgets.QLineEdit()
        self.gap_edit = QtWidgets.QLineEdit()

        form.addRow("Default kerf (mm):", self.kerf_edit)
        form.addRow("Default gap (mm):", self.gap_edit)
        return group

    def _build_rotation_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Rotation defaults")
        layout = QtWidgets.QVBoxLayout(group)
        self.allow_rotation_check = QtWidgets.QCheckBox("Allow rotation by default")
        self.allow_rotation_check.setToolTip("Applied when CSV panels omit orientation flags.")
        layout.addWidget(self.allow_rotation_check)
        return group

    def _build_optimization_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Optimization defaults")
        layout = QtWidgets.QHBoxLayout(group)
        self.optimization_combo = QtWidgets.QComboBox()
        self.optimization_combo.addItem("Material (waste first)", "material")
        self.optimization_combo.addItem("Cuts (simplify cuts)", "cuts")
        layout.addWidget(self.optimization_combo)
        layout.addStretch(1)
        return group

    def _build_logging_group(self) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox("Logging & developer")
        form = QtWidgets.QFormLayout(group)
        self.report_log_combo = QtWidgets.QComboBox()
        self.report_log_combo.addItems(["None", "Normal", "Verbose"])
        self.console_log_combo = QtWidgets.QComboBox()
        self.console_log_combo.addItems(["None", "Normal", "Verbose"])
        self.dev_mode_check = QtWidgets.QCheckBox("Enable developer mode")
        form.addRow("Report view logging:", self.report_log_combo)
        form.addRow("Python console logging:", self.console_log_combo)
        form.addRow(self.dev_mode_check)
        return group

    def _load_values(self) -> None:
        self.units_combo.setCurrentIndex(0 if self._prefs.is_metric() else 1)
        imp_w, imp_h = self._prefs.get_default_sheet_size("imperial")
        self.imperial_width_edit.setText(str(imp_w))
        self.imperial_height_edit.setText(str(imp_h))
        met_w, met_h = self._prefs.get_default_sheet_size("metric")
        self.metric_width_edit.setText(str(met_w))
        self.metric_height_edit.setText(str(met_h))
        self.kerf_edit.setText(str(self._prefs.get_default_kerf_mm()))
        self.gap_edit.setText(str(self._prefs.get_default_spacing_mm()))
        self.allow_rotation_check.setChecked(self._prefs.get_default_allow_rotate())
        self.optimization_combo.setCurrentIndex(
            1 if self._prefs.get_default_optimize_for_cut_path() else 0
        )
        self.report_log_combo.setCurrentIndex(
            {"none": 0, "normal": 1, "verbose": 2}.get(
                self._prefs.get_report_view_log_level(), 1
            )
        )
        self.console_log_combo.setCurrentIndex(
            {"none": 0, "normal": 1, "verbose": 2}.get(
                self._prefs.get_python_console_log_level(), 0
            )
        )
        self.dev_mode_check.setChecked(self._prefs.get_developer_mode())

    def _parse_float(self, widget: QtWidgets.QLineEdit, name: str) -> float:
        text = widget.text().strip()
        if not text:
            raise ValueError(f"{name} must not be blank.")
        try:
            return float(text)
        except Exception as exc:
            raise ValueError(f"Invalid value for {name}: {exc}")

    def _apply_changes(self) -> bool:
        try:
            imp_width = self._parse_float(self.imperial_width_edit, "Imperial width")
            imp_height = self._parse_float(self.imperial_height_edit, "Imperial height")
            met_width = self._parse_float(self.metric_width_edit, "Metric width")
            met_height = self._parse_float(self.metric_height_edit, "Metric height")
            kerf = self._parse_float(self.kerf_edit, "Kerf")
            gap = self._parse_float(self.gap_edit, "Gap")
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "SquatchCut", str(exc))
            return False

        self._prefs.set_measurement_system(
            self.units_combo.currentData() or "metric"
        )
        self._prefs.set_default_sheet_width_in(imp_width)
        self._prefs.set_default_sheet_height_in(imp_height)
        self._prefs.set_default_sheet_width_mm(met_width)
        self._prefs.set_default_sheet_height_mm(met_height)
        self._prefs.set_default_kerf_mm(kerf)
        self._prefs.set_default_spacing_mm(gap)
        self._prefs.set_default_allow_rotate(self.allow_rotation_check.isChecked())
        self._prefs.set_default_optimize_for_cut_path(
            self.optimization_combo.currentData() == "cuts"
        )
        report_idx = self.report_log_combo.currentIndex()
        console_idx = self.console_log_combo.currentIndex()
        levels = ["none", "normal", "verbose"]
        self._prefs.set_report_view_log_level(levels[min(report_idx, 2)])
        self._prefs.set_python_console_log_level(levels[min(console_idx, 2)])
        self._prefs.set_developer_mode(self.dev_mode_check.isChecked())

        return True

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
