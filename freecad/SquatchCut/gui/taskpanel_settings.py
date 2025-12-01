"""SquatchCut Settings panel for managing global defaults."""

from __future__ import annotations

try:
    import FreeCADGui as Gui
except Exception:
    Gui = None

from SquatchCut.gui.qt_compat import QtWidgets
from SquatchCut.core import units as sc_units
from SquatchCut import settings
from SquatchCut.core.preferences import SquatchCutPreferences


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
        self.measurement_system = self._prefs.get_measurement_system()
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

    def _load_values(self) -> None:
        self.units_combo.setCurrentIndex(0 if self.measurement_system == "metric" else 1)
        self._update_unit_labels()
        if self._prefs.has_default_sheet_size(self.measurement_system):
            width_mm = self._prefs.get_default_sheet_width_mm()
            height_mm = self._prefs.get_default_sheet_height_mm()
            self._set_length_text(self.sheet_width_edit, width_mm)
            self._set_length_text(self.sheet_height_edit, height_mm)
        else:
            self.sheet_width_edit.clear()
            self.sheet_height_edit.clear()
        self._set_length_text(self.kerf_edit, self._prefs.get_default_kerf_mm())
        self.gap_edit.setText(str(self._prefs.get_default_spacing_mm()))
        self.allow_rotation_check.setChecked(self._prefs.get_default_allow_rotate())

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
            raise ValueError(f"Invalid value for {name}: {exc}")

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
        self._prefs.set_measurement_system(system)
        if width_mm is not None and height_mm is not None:
            self._prefs.set_default_sheet_width_mm(width_mm)
            self._prefs.set_default_sheet_height_mm(height_mm)
        else:
            self._prefs.clear_default_sheet_size()
        self._prefs.set_default_kerf_mm(kerf_mm)
        if gap is not None:
            self._prefs.set_default_spacing_mm(gap)
        self._prefs.set_default_allow_rotate(self.allow_rotation_check.isChecked())

        return True

    def _on_units_changed(self) -> None:
        old_system = self.measurement_system
        system = self.units_combo.currentData() or "metric"
        self.measurement_system = system
        sc_units.set_units("in" if system == "imperial" else "mm")
        self._update_unit_labels()
        # Reformat existing values in the new system
        for edit in (self.sheet_width_edit, self.sheet_height_edit, self.kerf_edit):
            text = edit.text().strip()
            if not text:
                continue
            try:
                mm_value = sc_units.parse_length(text, old_system)
                edit.blockSignals(True)
                edit.setText(sc_units.format_length(mm_value, system))
                edit.blockSignals(False)
            except Exception:
                edit.blockSignals(True)
                edit.clear()
                edit.blockSignals(False)

    def _update_unit_labels(self) -> None:
        unit_label = sc_units.unit_label_for_system(self.measurement_system)
        self.sheet_width_label.setText(f"Default sheet width ({unit_label}):")
        self.sheet_height_label.setText(f"Default sheet height ({unit_label}):")
        self.kerf_label.setText(f"Default kerf ({unit_label}):")
        self.gap_label.setText("Default gap (mm):")

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
