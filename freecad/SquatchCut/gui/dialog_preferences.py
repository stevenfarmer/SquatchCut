"""SquatchCut Preferences dialog using FreeCAD ParamGet."""

from __future__ import annotations

try:
    from PySide import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

from SquatchCut.core.preferences import SquatchCutPreferences


class SquatchCutPreferencesDialog(QtWidgets.QDialog):
    """Dialog for editing SquatchCut default settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SquatchCut Preferences")
        self._prefs = SquatchCutPreferences()
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QtWidgets.QFormLayout(self)

        self.sheet_width_spin = QtWidgets.QDoubleSpinBox()
        self.sheet_width_spin.setRange(10.0, 10000.0)
        self.sheet_width_spin.setDecimals(1)
        self.sheet_width_spin.setSingleStep(10.0)

        self.sheet_height_spin = QtWidgets.QDoubleSpinBox()
        self.sheet_height_spin.setRange(10.0, 10000.0)
        self.sheet_height_spin.setDecimals(1)
        self.sheet_height_spin.setSingleStep(10.0)

        self.spacing_spin = QtWidgets.QDoubleSpinBox()
        self.spacing_spin.setRange(0.0, 100.0)
        self.spacing_spin.setDecimals(2)
        self.spacing_spin.setSingleStep(0.1)

        self.kerf_spin = QtWidgets.QDoubleSpinBox()
        self.kerf_spin.setRange(0.0, 100.0)
        self.kerf_spin.setDecimals(2)
        self.kerf_spin.setSingleStep(0.1)

        self.cut_mode_check = QtWidgets.QCheckBox("Cut Optimization: Woodshop Mode")

        layout.addRow("Default sheet width (mm):", self.sheet_width_spin)
        layout.addRow("Default sheet height (mm):", self.sheet_height_spin)
        layout.addRow("Default spacing between parts (mm):", self.spacing_spin)
        layout.addRow("Default kerf width (mm):", self.kerf_spin)
        layout.addRow(self.cut_mode_check)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _load_values(self):
        self.sheet_width_spin.setValue(self._prefs.get_default_sheet_width_mm())
        self.sheet_height_spin.setValue(self._prefs.get_default_sheet_height_mm())
        self.spacing_spin.setValue(self._prefs.get_default_spacing_mm())
        self.kerf_spin.setValue(self._prefs.get_default_kerf_mm())
        self.cut_mode_check.setChecked(self._prefs.get_default_optimize_for_cut_path())

    def accept(self):  # noqa: D401
        """Persist preferences on OK."""
        self._prefs.set_default_sheet_width_mm(self.sheet_width_spin.value())
        self._prefs.set_default_sheet_height_mm(self.sheet_height_spin.value())
        self._prefs.set_default_spacing_mm(self.spacing_spin.value())
        self._prefs.set_default_kerf_mm(self.kerf_spin.value())
        self._prefs.set_default_optimize_for_cut_path(self.cut_mode_check.isChecked())
        super().accept()
