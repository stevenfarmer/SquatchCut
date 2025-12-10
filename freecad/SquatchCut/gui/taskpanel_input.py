"""Input/CSV section for the SquatchCut TaskPanel."""

from __future__ import annotations

import os
from typing import List

from SquatchCut.gui.qt_compat import QtWidgets, QtCore
from SquatchCut.core import session_state, logger, units as sc_units
from SquatchCut.gui.commands.cmd_import_csv import run_csv_import
from SquatchCut.ui.messages import show_error
from SquatchCut.freecad_integration import App


class InputGroupWidget(QtWidgets.QGroupBox):
    """
    Widget handling CSV import and parts table display.

    Signals:
        csv_imported: Emitted when a CSV is successfully loaded.
        data_changed: Emitted when parts data changes (e.g. reload).
    """

    csv_imported = QtCore.Signal()
    data_changed = QtCore.Signal()

    def __init__(self, prefs, parent=None):
        super().__init__("Input", parent)
        self._prefs = prefs
        self._last_csv_path: str | None = None
        self._build_ui()
        if hasattr(self, "setObjectName"):
            self.setObjectName("input_group_box")

    def _build_ui(self) -> None:
        vbox = QtWidgets.QVBoxLayout(self)

        self.load_csv_button = QtWidgets.QPushButton("Import CSV")
        self.load_csv_button.setToolTip("Import a SquatchCut panels CSV file.")
        self.csv_path_label = QtWidgets.QLabel("No file loaded")
        self.csv_path_label.setStyleSheet("color: gray;")
        if hasattr(self.csv_path_label, "setWordWrap"):
            self.csv_path_label.setWordWrap(True)
        self.csv_path_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        # Helper for size policy
        setter = getattr(self.csv_path_label, "setSizePolicy", None)
        if callable(setter):
            setter(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        vbox.addWidget(self.load_csv_button)
        vbox.addWidget(self.csv_path_label)

        csv_units_form = QtWidgets.QFormLayout()
        csv_units_label = QtWidgets.QLabel("CSV units:")
        self.csv_units_combo = QtWidgets.QComboBox()
        self.csv_units_combo.addItem("Metric (mm)", "mm")
        self.csv_units_combo.addItem("Imperial (in)", "in")
        csv_units_form.addRow(csv_units_label, self.csv_units_combo)
        vbox.addLayout(csv_units_form)

        self.parts_table = QtWidgets.QTableWidget()
        self.parts_table.setColumnCount(5)
        header = self.parts_table.horizontalHeader()
        if hasattr(header, "setStretchLastSection"):
            header.setStretchLastSection(True)
        header_view_cls = getattr(QtWidgets, "QHeaderView", None)
        if header_view_cls is not None and hasattr(header, "setSectionResizeMode"):
            header.setSectionResizeMode(0, header_view_cls.Stretch)
            for col in range(1, 5):
                header.setSectionResizeMode(col, header_view_cls.ResizeToContents)

        size_policy_cls = getattr(QtWidgets, "QSizePolicy", None)
        if size_policy_cls is not None and hasattr(self.parts_table, "setSizePolicy"):
            self.parts_table.setSizePolicy(size_policy_cls.Expanding, size_policy_cls.Expanding)

        self.parts_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.parts_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.parts_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        vbox.addWidget(self.parts_table)

        self.load_csv_button.clicked.connect(self._choose_csv_file)

        self._update_table_headers()

    def get_csv_units(self) -> str:
        """Return csv units selection ('mm' or 'in')."""
        data = self.csv_units_combo.currentData()
        if data in ("mm", "in"):
            return data
        return "mm"

    def _choose_csv_file(self) -> None:
        caption = "Select panels CSV"
        file_filter = "CSV files (*.csv);;All files (*.*)"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            caption,
            self._last_csv_path or "",
            file_filter,
        )
        if not file_path:
            return
        self._import_csv(file_path)

    def _import_csv(self, file_path: str) -> None:
        doc = App.ActiveDocument
        if doc is None:
            show_error("Unable to find an active document.", title="SquatchCut")
            return

        try:
            # We assume settings are already applied to session state by the main controller/sheet widget
            # But strictly CSV import depends on CSV units and file path.
            csv_units = self.get_csv_units()
            logger.info(f">>> [SquatchCut] Importing CSV: {file_path}")
            run_csv_import(doc, file_path, csv_units=csv_units)
            self._prefs.set_csv_units(csv_units)
            self._last_csv_path = file_path
            self._set_csv_label(file_path)
            self.refresh_table()
            self.csv_imported.emit()
        except Exception as exc:
            show_error(f"Failed to import CSV:\n{exc}", title="SquatchCut")

    def _set_csv_label(self, path: str) -> None:
        display = os.path.basename(path) if path else "No file loaded"
        self.csv_path_label.setText(display)
        self.csv_path_label.setToolTip(path)
        self.csv_path_label.setStyleSheet("" if path else "color: gray;")

    def refresh_table(self) -> None:
        panels = session_state.get_panels()
        self.parts_table.setRowCount(0)
        if not panels:
            self.data_changed.emit()
            return

        self.parts_table.setRowCount(len(panels))
        self._update_table_headers()

        measurement_system = session_state.get_measurement_system()

        for row, panel in enumerate(panels):
            name = panel.get("label") or panel.get("id") or f"Panel {row + 1}"
            width = panel.get("width", "")
            height = panel.get("height", "")
            qty = panel.get("qty", 1)
            allow_rotate = panel.get("allow_rotate", False)

            try:
                width_text = sc_units.format_length(float(width), measurement_system) if width not in (None, "") else ""
            except Exception:
                width_text = str(width)
            try:
                height_text = sc_units.format_length(float(height), measurement_system) if height not in (None, "") else ""
            except Exception:
                height_text = str(height)

            values = [
                str(name),
                width_text,
                height_text,
                str(int(qty) if qty not in (None, "") else 1),
                "Yes" if allow_rotate else "No",
            ]

            for col, text in enumerate(values):
                item = QtWidgets.QTableWidgetItem(text)
                # Set flags...
                # Simulating _qt_flag_mask logic
                qt = getattr(QtCore, "Qt", None)
                if qt:
                     mask = qt.ItemIsSelectable | qt.ItemIsEnabled
                     item.setFlags(mask)
                self.parts_table.setItem(row, col, item)

        self.parts_table.resizeColumnsToContents()
        self.data_changed.emit()

    def _update_table_headers(self) -> None:
        unit = sc_units.unit_label_for_system(session_state.get_measurement_system())
        headers = ["Name", f"Width ({unit})", f"Height ({unit})", "Qty", "Allow rotate"]
        self.parts_table.setHorizontalHeaderLabels(headers)

    def apply_state(self, state: dict) -> None:
        """Apply hydrated state to widgets."""
        csv_units = state.get("csv_units")
        idx = self.csv_units_combo.findData(csv_units)
        if idx >= 0:
            self.csv_units_combo.blockSignals(True)
            self.csv_units_combo.setCurrentIndex(idx)
            self.csv_units_combo.blockSignals(False)
        self.refresh_table()

    def on_units_changed(self) -> None:
        """Handle global unit change."""
        self._update_table_headers()
        self.refresh_table()
