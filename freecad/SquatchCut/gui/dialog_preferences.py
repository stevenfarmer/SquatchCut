"""SquatchCut Preferences dialog using FreeCAD ParamGet."""

from __future__ import annotations

from SquatchCut.gui.qt_compat import QtWidgets

from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core import units as sc_units


class SquatchCutPreferencesDialog(QtWidgets.QDialog):
    """Dialog for editing SquatchCut default settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SquatchCut Preferences")
        self._prefs = SquatchCutPreferences()
        self.measurement_system = self._prefs.get_measurement_system()
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QtWidgets.QFormLayout(self)

        self.sheet_width_label = QtWidgets.QLabel()
        self.sheet_width_edit = QtWidgets.QLineEdit()

        self.sheet_height_label = QtWidgets.QLabel()
        self.sheet_height_edit = QtWidgets.QLineEdit()

        self.spacing_label = QtWidgets.QLabel()
        self.spacing_edit = QtWidgets.QLineEdit()

        self.kerf_label = QtWidgets.QLabel()
        self.kerf_edit = QtWidgets.QLineEdit()

        self.cut_mode_check = QtWidgets.QCheckBox("Cut Optimization: Woodshop Mode")
        self.rotate_check = QtWidgets.QCheckBox("Allow rotation by default")

        layout.addRow(self.sheet_width_label, self.sheet_width_edit)
        layout.addRow(self.sheet_height_label, self.sheet_height_edit)
        layout.addRow(self.spacing_label, self.spacing_edit)
        layout.addRow(self.kerf_label, self.kerf_edit)
        layout.addRow(self.cut_mode_check)
        layout.addRow(self.rotate_check)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        self._update_unit_labels()

    def _load_values(self):
        self._set_length_text(self.sheet_width_edit, self._prefs.get_default_sheet_width_mm())
        self._set_length_text(self.sheet_height_edit, self._prefs.get_default_sheet_height_mm())
        self._set_length_text(self.spacing_edit, self._prefs.get_default_spacing_mm())
        self._set_length_text(self.kerf_edit, self._prefs.get_default_kerf_mm())
        self.cut_mode_check.setChecked(self._prefs.get_default_optimize_for_cut_path())
        self.rotate_check.setChecked(self._prefs.get_default_allow_rotate())

    def accept(self):  # noqa: D401
        """Persist preferences on OK."""
        try:
            sheet_width = self._parse_length(self.sheet_width_edit.text())
            sheet_height = self._parse_length(self.sheet_height_edit.text())
            spacing = self._parse_length(self.spacing_edit.text())
            kerf = self._parse_length(self.kerf_edit.text())
        except ValueError as exc:
            self._show_parse_error(exc)
            return
        self._prefs.set_default_sheet_width_mm(sheet_width)
        self._prefs.set_default_sheet_height_mm(sheet_height)
        self._prefs.set_default_spacing_mm(spacing)
        self._prefs.set_default_kerf_mm(kerf)
        self._prefs.set_default_optimize_for_cut_path(self.cut_mode_check.isChecked())
        self._prefs.set_default_allow_rotate(self.rotate_check.isChecked())
        super().accept()

    def _update_unit_labels(self):
        unit = sc_units.unit_label_for_system(self.measurement_system)
        self.sheet_width_label.setText(f"Default sheet width ({unit}):")
        self.sheet_height_label.setText(f"Default sheet height ({unit}):")
        self.spacing_label.setText(f"Default spacing between parts ({unit}):")
        self.kerf_label.setText(f"Default kerf width ({unit}):")

    def _format_length(self, value_mm: float) -> str:
        return sc_units.format_length(value_mm, self.measurement_system)

    def _parse_length(self, text: str) -> float:
        return sc_units.parse_length(text, self.measurement_system)

    def _set_length_text(self, widget: QtWidgets.QLineEdit, value_mm: float) -> None:
        widget.setText(self._format_length(value_mm))

    def _show_parse_error(self, exc: Exception) -> None:
        if self.measurement_system == "imperial":
            message = "Invalid imperial value. Use formats like 48, 48.5, 48 1/2, or 48-1/2."
        else:
            message = str(exc)
        QtWidgets.QMessageBox.warning(self, "SquatchCut", message)
