"""Dialog for entering sheet dimensions and spacing settings."""

from __future__ import annotations

"""@codex
Dialog: Configure sheet width, height, and kerf/spacing.
get_data fields: width (float), height (float), spacing (float).
Note: UI only; do not implement business logic here.
"""

# Qt bindings (FreeCAD ships PySide / PySide2, not PySide6)
try:
    from PySide import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets


class SC_SheetSizeDialog(QtWidgets.QDialog):
    """Allow user to enter sheet width, height, and kerf/spacing."""

    def __init__(self, width: float | None = None, height: float | None = None, kerf: float | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sheet Size")
        self.resize(320, 200)
        self._initial = {"width": width, "height": height, "kerf": kerf}
        self.build_ui()
        self._load_defaults()

    def build_ui(self):
        layout = QtWidgets.QFormLayout(self)

        self.width_spin = QtWidgets.QDoubleSpinBox()
        self.width_spin.setSuffix(" mm")
        self.width_spin.setMaximum(100000.0)

        self.height_spin = QtWidgets.QDoubleSpinBox()
        self.height_spin.setSuffix(" mm")
        self.height_spin.setMaximum(100000.0)

        self.spacing_spin = QtWidgets.QDoubleSpinBox()
        self.spacing_spin.setSuffix(" mm")
        self.spacing_spin.setMaximum(1000.0)

        layout.addRow("Width", self.width_spin)
        layout.addRow("Height", self.height_spin)
        layout.addRow("Kerf / Spacing", self.spacing_spin)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_data(self) -> dict:
        """Return placeholder sheet size data."""
        return {
            "width": self.width_spin.value(),
            "height": self.height_spin.value(),
            "spacing": self.spacing_spin.value(),
        }

    def get_values(self):
        """
        Return (width, height, units) from the dialog inputs.
        Units are currently fixed to millimeters.
        """
        width_val = self.width_spin.value()
        height_val = self.height_spin.value()
        units = "mm"
        return width_val, height_val, units

    def _load_defaults(self):
        if self._initial["width"] is not None:
            self.width_spin.setValue(float(self._initial["width"]))
        if self._initial["height"] is not None:
            self.height_spin.setValue(float(self._initial["height"]))
        if self._initial["kerf"] is not None:
            self.spacing_spin.setValue(float(self._initial["kerf"]))
