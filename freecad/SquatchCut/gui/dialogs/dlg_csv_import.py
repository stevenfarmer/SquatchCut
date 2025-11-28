"""Dialog for configuring and confirming CSV panel imports."""

from __future__ import annotations

"""@codex
Dialog: Configure CSV import and preview rows.
get_data fields: path (string), preview_rows (list placeholder).
Note: UI only; do not implement business logic here.
"""

# Qt bindings (FreeCAD ships PySide / PySide2, not PySide6)
from SquatchCut.gui.qt_compat import QtWidgets, QtCore, QtGui


class SC_CSVImportDialog(QtWidgets.QDialog):
    """Let user choose a CSV file, preview rows, and confirm import."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import CSV")
        self.resize(500, 350)
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        file_layout = QtWidgets.QHBoxLayout()
        self.path_edit = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse…")
        file_layout.addWidget(QtWidgets.QLabel("CSV File:"))
        file_layout.addWidget(self.path_edit)
        file_layout.addWidget(browse_btn)

        self.preview_table = QtWidgets.QTableWidget()
        self.preview_table.setColumnCount(0)
        self.preview_table.setRowCount(0)
        self.preview_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(file_layout)
        layout.addWidget(QtWidgets.QLabel("Preview:"))
        layout.addWidget(self.preview_table)
        layout.addWidget(button_box)

        # Placeholder: wire browse button to no-op slot.
        browse_btn.clicked.connect(self._on_browse_clicked)

    def _on_browse_clicked(self):
        """Placeholder for file picker."""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if filename:
            self.path_edit.setText(filename)

    def get_data(self) -> dict:
        """Return placeholder CSV import parameters."""
        return {"path": self.path_edit.text() or None, "preview_rows": []}
