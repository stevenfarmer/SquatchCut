"""Dialog for selecting detected shapes from the current FreeCAD document."""

from __future__ import annotations

"""@codex
Dialog: Select detected shapes from the document.
get_data fields: selected_shapes (list of identifiers or labels).
Note: UI only; do not implement business logic here.
"""

# Qt bindings (FreeCAD ships PySide / PySide2, not PySide6)
try:
    from PySide import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui


class SC_SelectShapesDialog(QtWidgets.QDialog):
    """Show list of detected shapes and allow selection."""

    def __init__(self, items: list[dict] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Shapes")
        self.resize(400, 300)
        self.items = items or []
        self.build_ui()
        self._populate()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        info_label = QtWidgets.QLabel("Detected shapes:")
        self.shapes_list = QtWidgets.QListWidget()
        self.shapes_list.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(info_label)
        layout.addWidget(self.shapes_list)
        layout.addWidget(button_box)

    def get_data(self) -> dict:
        """Return placeholder selection data."""
        selected_panels = []
        for idx in range(self.shapes_list.count()):
            item = self.shapes_list.item(idx)
            if item.checkState() == QtCore.Qt.Checked:
                payload = item.data(QtCore.Qt.UserRole)
                selected_panels.append(payload)
        return {"selected_shapes": selected_panels}

    def _populate(self):
        for panel in self.items:
            label = panel.get("id") or panel.get("name") or "Unnamed"
            item = QtWidgets.QListWidgetItem(str(label))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(QtCore.Qt.UserRole, panel)
            self.shapes_list.addItem(item)
