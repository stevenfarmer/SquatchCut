"""Input/CSV section for the SquatchCut TaskPanel."""

from __future__ import annotations

import os
from typing import Optional

from SquatchCut.core import logger, session_state
from SquatchCut.core import units as sc_units
from SquatchCut.core.shape_extractor import ShapeExtractor
from SquatchCut.freecad_integration import App
from SquatchCut.gui.commands.cmd_import_csv import run_csv_import
from SquatchCut.gui.dialogs.dlg_select_shapes import (
    EnhancedShapeSelectionDialog,
    ShapeInfo,
)
from SquatchCut.gui.qt_compat import QtCore, QtWidgets
from SquatchCut.ui.messages import show_error
from SquatchCut.ui.progress import ProgressDialog


class InputGroupWidget(QtWidgets.QGroupBox):
    """
    Widget handling CSV import and parts table display.

    Signals:
        csv_imported: Emitted when a CSV is successfully loaded.
        data_changed: Emitted when parts data changes (e.g. reload).
    """

    csv_imported = QtCore.Signal()
    data_changed = QtCore.Signal()
    shapes_selected = QtCore.Signal()

    def __init__(self, prefs, parent=None):
        super().__init__("Input", parent)
        self._prefs = prefs
        self._last_csv_path: Optional[str] = None
        self._build_ui()
        if hasattr(self, "setObjectName"):
            self.setObjectName("input_group_box")

    def _build_ui(self) -> None:
        vbox = QtWidgets.QVBoxLayout(self)

        self.csv_path_label = QtWidgets.QLabel("No file loaded")
        self.csv_path_label.setStyleSheet("color: gray;")
        if hasattr(self.csv_path_label, "setWordWrap"):
            self.csv_path_label.setWordWrap(True)
        self.csv_path_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        # Helper for size policy
        setter = getattr(self.csv_path_label, "setSizePolicy", None)
        if callable(setter):
            setter(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        # Input method selection
        input_method_layout = QtWidgets.QHBoxLayout()

        self.load_csv_button = QtWidgets.QPushButton("Import CSV")
        self.load_csv_button.setToolTip("Import a SquatchCut panels CSV file.")
        input_method_layout.addWidget(self.load_csv_button)

        self.select_shapes_button = QtWidgets.QPushButton("Select Shapes")
        self.select_shapes_button.setToolTip(
            "Select FreeCAD shapes from the current document for nesting."
        )
        input_method_layout.addWidget(self.select_shapes_button)

        vbox.addLayout(input_method_layout)
        vbox.addWidget(self.csv_path_label)

        csv_units_form = QtWidgets.QFormLayout()
        csv_units_label = QtWidgets.QLabel("CSV units:")
        self.csv_units_combo = QtWidgets.QComboBox()
        self.csv_units_combo.addItem("Metric (mm)", "metric")
        self.csv_units_combo.addItem("Imperial (in)", "imperial")
        if hasattr(self.csv_units_combo, "setEnabled"):
            self.csv_units_combo.setEnabled(False)
        if hasattr(self.csv_units_combo, "setToolTip"):
            self.csv_units_combo.setToolTip(
                "CSV units follow the Sheet units selection."
            )
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
            self.parts_table.setSizePolicy(
                size_policy_cls.Expanding, size_policy_cls.Expanding
            )

        self.parts_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.parts_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.parts_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        vbox.addWidget(self.parts_table)

        self.load_csv_button.clicked.connect(self._choose_csv_file)
        self.select_shapes_button.clicked.connect(self._select_shapes)

        self._update_table_headers()

    def get_csv_units(self) -> str:
        """Return current measurement system for CSV operations."""
        data = self.csv_units_combo.currentData()
        if data in ("metric", "imperial"):
            return data
        return "metric"

    def _sync_csv_units_display(self, system: Optional[str]) -> None:
        normalized = "imperial" if system == "imperial" else "metric"
        idx = self.csv_units_combo.findData(normalized)
        if idx >= 0:
            self.csv_units_combo.blockSignals(True)
            self.csv_units_combo.setCurrentIndex(idx)
            self.csv_units_combo.blockSignals(False)

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
            # Auto-detect units from CSV content
            logger.info(f">>> [SquatchCut] Importing CSV: {file_path}")
            run_csv_import(doc, file_path, csv_units="auto")

            # Update UI to reflect detected units
            detected_system = session_state.get_measurement_system()
            self._sync_csv_units_display(detected_system)
            self._prefs.set_csv_units(detected_system)

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
                width_text = (
                    sc_units.format_length(float(width), measurement_system)
                    if width not in (None, "")
                    else ""
                )
            except Exception:
                width_text = str(width)
            try:
                height_text = (
                    sc_units.format_length(float(height), measurement_system)
                    if height not in (None, "")
                    else ""
                )
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
                selectable = getattr(qt, "ItemIsSelectable", None) if qt else None
                enabled = getattr(qt, "ItemIsEnabled", None) if qt else None
                if selectable is not None and enabled is not None:
                    mask = selectable | enabled
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
        system = state.get("measurement_system", "metric")
        self._sync_csv_units_display(system)
        self.refresh_table()

    def on_units_changed(self) -> None:
        """Handle global unit change."""
        self._sync_csv_units_display(session_state.get_measurement_system())
        self._update_table_headers()
        self.refresh_table()

    def _select_shapes(self) -> None:
        """Open shape selection dialog and process selected shapes."""
        doc = App.ActiveDocument
        if doc is None:
            show_error("Unable to find an active document.", title="SquatchCut")
            return

        try:
            # Extract shapes from the current document
            extractor = ShapeExtractor()
            detected_shapes = []

            # Get all objects with Shape properties
            shape_objects = [
                obj
                for obj in doc.Objects
                if hasattr(obj, "Shape") and obj.Shape is not None
            ]

            if not shape_objects:
                show_error(
                    "No valid shapes found in the current document.", title="SquatchCut"
                )
                return

            # Create progress dialog for shape processing
            with ProgressDialog(title="Processing Shapes", parent=self) as progress:
                progress.set_range(0, len(shape_objects))
                progress.set_label("Extracting shape geometries...")

                for i, obj in enumerate(shape_objects):
                    progress.set_value(i)
                    progress.set_label(f"Processing {obj.Label}...")

                    # Allow UI updates
                    QtWidgets.QApplication.processEvents()

                    try:
                        # Use fallback extraction for robust shape processing
                        geometry, extraction_method, notification = (
                            extractor.extract_with_fallback(obj)
                        )

                        # Log notification if provided
                        if notification:
                            logger.info(f"Shape extraction: {notification}")

                        # Get dimensions from the extracted geometry
                        width_mm = geometry.get_width()
                        height_mm = geometry.get_height()
                        depth_mm = (
                            getattr(obj.Shape.BoundBox, "ZLength", 0.0)
                            if hasattr(obj, "Shape")
                            else 0.0
                        )

                        # Create ShapeInfo for the dialog
                        shape_info = ShapeInfo(
                            freecad_object=obj,
                            label=obj.Label,
                            dimensions=(width_mm, height_mm, depth_mm),
                            geometry_type=geometry.geometry_type,
                            complexity_score=geometry.complexity_level,
                            extraction_method=extraction_method,
                            area_mm2=geometry.area,
                        )
                        detected_shapes.append(shape_info)

                    except Exception as e:
                        logger.warning(f"Failed to process object {obj.Label}: {e}")
                        continue

                progress.set_value(len(shape_objects))
                progress.set_label("Shape processing complete")

            if not detected_shapes:
                show_error(
                    "No shapes could be processed successfully.", title="SquatchCut"
                )
                return

            headless_dialog = not callable(getattr(QtWidgets.QDialog, "exec_", None)) and not callable(
                getattr(QtWidgets.QDialog, "exec", None)
            )
            selected_shapes = []

            if headless_dialog:
                selected_shapes = detected_shapes
            else:
                # Open selection dialog
                dialog = EnhancedShapeSelectionDialog(detected_shapes, parent=self)
                exec_fn = getattr(dialog, "exec_", None)
                if exec_fn is None:
                    exec_fn = getattr(dialog, "exec", None)

                try:
                    dialog_result = exec_fn() if callable(exec_fn) else QtWidgets.QDialog.Accepted
                except Exception:
                    dialog_result = QtWidgets.QDialog.Accepted

                if dialog_result == getattr(QtWidgets.QDialog, "Accepted", 1):
                    try:
                        selection_data = dialog.get_data()
                        selected_shapes = selection_data["selected_shapes"]
                    except Exception:
                        selected_shapes = detected_shapes

            if selected_shapes:
                # Convert selected shapes to panel format for session_state
                panels = []

                # Show progress for shape conversion if there are many shapes
                if len(selected_shapes) > 5:
                    with ProgressDialog(title="Converting Shapes", parent=self) as progress:
                        progress.set_range(0, len(selected_shapes))
                        progress.set_label("Converting shapes to panels...")

                        for i, shape_info in enumerate(selected_shapes):
                            progress.set_value(i)
                            progress.set_label(f"Converting {shape_info.label}...")
                            QtWidgets.QApplication.processEvents()

                            width_mm, height_mm, _ = shape_info.dimensions
                            panel = {
                                "id": shape_info.label,
                                "label": shape_info.label,
                                "width": width_mm,
                                "height": height_mm,
                                "qty": 1,
                                "allow_rotate": True,  # Default to allowing rotation
                                "source": "freecad_shape",
                                "freecad_object": shape_info.freecad_object,
                            }
                            panels.append(panel)

                        progress.set_value(len(selected_shapes))
                        progress.set_text("Conversion complete")
                else:
                    # For small numbers of shapes, convert without progress dialog
                    for shape_info in selected_shapes:
                        width_mm, height_mm, _ = shape_info.dimensions
                        panel = {
                            "id": shape_info.label,
                            "label": shape_info.label,
                            "width": width_mm,
                            "height": height_mm,
                            "qty": 1,
                            "allow_rotate": True,  # Default to allowing rotation
                            "source": "freecad_shape",
                            "freecad_object": shape_info.freecad_object,
                        }
                        panels.append(panel)

                # Update session state with selected shapes
                session_state.set_panels(panels)

                # Update UI
                self._set_csv_label("")  # Clear CSV label
                self.csv_path_label.setText(f"{len(selected_shapes)} shapes selected")
                self.csv_path_label.setStyleSheet("")
                self.refresh_table()
                self.shapes_selected.emit()

                logger.info(f">>> [SquatchCut] Selected {len(selected_shapes)} shapes for nesting")

        except Exception as exc:
            show_error(f"Failed to select shapes:\n{exc}", title="SquatchCut")
