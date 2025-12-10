"""Dialog for confirming the nesting run with a summary of panels/sheets."""

from __future__ import annotations

# Qt bindings (FreeCAD ships PySide / PySide2, not PySide6)
from SquatchCut.gui.qt_compat import QtWidgets

# @codex
# Dialog: Confirm running nesting with a summary.
# get_data fields: confirmed (bool).
# Note: UI only; do not implement business logic here.


class SC_RunNestingDialog(QtWidgets.QDialog):
    """Show nesting summary, panel count, and confirm running nesting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Run Nesting")
        self.resize(360, 240)
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.summary_label = QtWidgets.QLabel("Nesting summary will appear here.")
        self.panel_count_label = QtWidgets.QLabel("Panels: 0")

        layout.addWidget(self.summary_label)
        layout.addWidget(self.panel_count_label)
        layout.addStretch(1)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self) -> dict:
        """Return placeholder confirmation data."""
        return {"confirmed": self.result() == QtWidgets.QDialog.Accepted}

    def set_summary(self, panel_count: int, sheet_width: float, sheet_height: float):
        """Update summary labels."""
        self.panel_count_label.setText(f"Panels: {panel_count}")
        self.summary_label.setText(f"Sheet size: {sheet_width} x {sheet_height}")
