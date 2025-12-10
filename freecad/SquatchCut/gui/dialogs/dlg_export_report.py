"""Dialog for choosing export destination and report options."""

from __future__ import annotations

# Qt bindings (FreeCAD ships PySide / PySide2, not PySide6)
from SquatchCut.gui.qt_compat import QtWidgets

# @codex
# Dialog: Choose export directory and report options.
# get_data fields: directory (string), generate_pdf (bool), generate_csv (bool).
# Note: UI only; do not implement business logic here.


class SC_ExportReportDialog(QtWidgets.QDialog):
    """Choose export directory and report options (PDF/CSV)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Report")
        self.resize(400, 220)
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        dir_layout = QtWidgets.QHBoxLayout()
        self.dir_edit = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse…")
        dir_layout.addWidget(QtWidgets.QLabel("Export Directory:"))
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(browse_btn)

        options_group = QtWidgets.QGroupBox("Report Options")
        options_layout = QtWidgets.QVBoxLayout(options_group)
        self.pdf_check = QtWidgets.QCheckBox("Generate PDF")
        self.csv_check = QtWidgets.QCheckBox("Generate CSV")
        options_layout.addWidget(self.pdf_check)
        options_layout.addWidget(self.csv_check)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(dir_layout)
        layout.addWidget(options_group)
        layout.addStretch(1)
        layout.addWidget(button_box)

        browse_btn.clicked.connect(self._on_browse_clicked)

    def _on_browse_clicked(self):
        """Placeholder for directory picker."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Export Directory", ""
        )
        if directory:
            self.dir_edit.setText(directory)

        self.pdf_check.setChecked(True)
        self.csv_check.setChecked(True)

    def get_data(self) -> dict:
        """Return placeholder export settings."""
        return {
            "directory": self.dir_edit.text(),
            "generate_pdf": self.pdf_check.isChecked(),
            "generate_csv": self.csv_check.isChecked(),
        }
