"""SquatchCut Settings panel (units selection for now)."""

from __future__ import annotations

from SquatchCut.gui.qt_compat import QtWidgets
from SquatchCut.core import units as sc_units


class SquatchCutSettingsPanel(QtWidgets.QWidget):
    """Minimal settings panel exposing units selection."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load_units()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        units_group_box = QtWidgets.QGroupBox("Units")
        units_layout = QtWidgets.QHBoxLayout(units_group_box)

        self.rbUnitsMetric = QtWidgets.QRadioButton("Metric (mm)")
        self.rbUnitsImperial = QtWidgets.QRadioButton("Imperial (in)")

        units_layout.addWidget(self.rbUnitsMetric)
        units_layout.addWidget(self.rbUnitsImperial)
        units_layout.addStretch(1)
        units_group_box.setLayout(units_layout)
        layout.addWidget(units_group_box)

        self.rbUnitsMetric.toggled.connect(self._on_units_changed)
        self.rbUnitsImperial.toggled.connect(self._on_units_changed)

    def _load_units(self):
        units = sc_units.get_units()
        if units == "in":
            self.rbUnitsImperial.setChecked(True)
            self.rbUnitsMetric.setChecked(False)
        else:
            self.rbUnitsMetric.setChecked(True)
            self.rbUnitsImperial.setChecked(False)

    def _on_units_changed(self):
        if self.rbUnitsImperial.isChecked():
            sc_units.set_units("in")
        elif self.rbUnitsMetric.isChecked():
            sc_units.set_units("mm")


def create_settings_panel_for_tests():
    """
    Factory used by GUI tests to instantiate the SquatchCut Settings panel
    without going through FreeCAD's dialog machinery.
    """
    return SquatchCutSettingsPanel()
