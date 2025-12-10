"""Dialog for entering sheet dimensions and spacing settings."""

from __future__ import annotations

# Qt bindings (FreeCAD ships PySide / PySide2, not PySide6)
from SquatchCut.core import units as sc_units

# @codex
# Dialog: Configure sheet width, height, and kerf/spacing.
# get_data fields: width (float), height (float), spacing (float).
# Note: UI only; do not implement business logic here.
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.gui.qt_compat import QtWidgets


class SC_SheetSizeDialog(QtWidgets.QDialog):
    """Allow user to enter sheet width, height, and kerf/spacing."""

    def __init__(self, width: float | None = None, height: float | None = None, kerf: float | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sheet Size")
        self.resize(320, 200)
        self._initial = {"width": width, "height": height, "kerf": kerf}
        self._prefs = SquatchCutPreferences()
        self.measurement_system = self._prefs.get_measurement_system()
        self.build_ui()
        self._load_defaults()

    def build_ui(self):
        layout = QtWidgets.QFormLayout(self)

        self.width_label = QtWidgets.QLabel()
        self.width_edit = QtWidgets.QLineEdit()
        self.height_label = QtWidgets.QLabel()
        self.height_edit = QtWidgets.QLineEdit()
        self.spacing_label = QtWidgets.QLabel()
        self.spacing_edit = QtWidgets.QLineEdit()

        layout.addRow(self.width_label, self.width_edit)
        layout.addRow(self.height_label, self.height_edit)
        layout.addRow(self.spacing_label, self.spacing_edit)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        self._update_unit_labels()

    def get_data(self) -> dict:
        """Return parsed sheet size data in millimeters."""
        width = self._parse_length(self.width_edit.text())
        height = self._parse_length(self.height_edit.text())
        spacing = self._parse_length(self.spacing_edit.text())
        return {
            "width": width,
            "height": height,
            "spacing": spacing,
        }

    def get_values(self):
        """
        Return (width_mm, height_mm, units_label) from the dialog inputs.
        Internal units remain millimeters.
        """
        width_val = self._parse_length(self.width_edit.text())
        height_val = self._parse_length(self.height_edit.text())
        self._parse_length(self.spacing_edit.text())
        units = sc_units.unit_label_for_system(self.measurement_system)
        return width_val, height_val, units

    def _load_defaults(self):
        defaults = {
            "width": self._prefs.get_default_sheet_width_mm(),
            "height": self._prefs.get_default_sheet_height_mm(),
            "kerf": self._prefs.get_default_spacing_mm(),
        }
        for key in ("width", "height", "kerf"):
            if self._initial.get(key) is not None:
                defaults[key] = float(self._initial[key])

        self._set_length_text(self.width_edit, defaults["width"])
        self._set_length_text(self.height_edit, defaults["height"])
        self._set_length_text(self.spacing_edit, defaults["kerf"])

    def _update_unit_labels(self):
        unit = sc_units.unit_label_for_system(self.measurement_system)
        self.width_label.setText(f"Width ({unit})")
        self.height_label.setText(f"Height ({unit})")
        self.spacing_label.setText(f"Kerf / Spacing ({unit})")

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

    def accept(self) -> None:
        try:
            self.get_values()
        except ValueError as exc:
            self._show_parse_error(exc)
            return
        super().accept()
