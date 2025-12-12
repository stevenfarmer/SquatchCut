"""Enhanced dialog for selecting detected shapes from the current FreeCAD document.

This dialog provides an intuitive interface for users to select which FreeCAD objects
should be included in the nesting process, with previews, validation, and detailed
shape information display.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

# Qt bindings (FreeCAD ships PySide / PySide2, not PySide6)
from SquatchCut.gui.qt_compat import QtCore, QtWidgets
from SquatchCut.core.complex_geometry import (
    ComplexGeometry,
    GeometryType,
    ComplexityLevel,
)
from SquatchCut.core import units as sc_units
from SquatchCut.core import session_state


@dataclass
class ShapeInfo:
    """Information about a detected FreeCAD shape for selection display."""

    freecad_object: Any
    label: str
    dimensions: Tuple[float, float, float]  # width, height, depth in mm
    geometry_type: GeometryType
    complexity_score: float
    preview_data: Optional[str] = None
    extraction_method: str = "bounding_box"
    area_mm2: Optional[float] = None


class PreviewWidget(QtWidgets.QWidget):
    """Widget to display shape preview information."""

    def __init__(self, shape_info: ShapeInfo, parent=None):
        super().__init__(parent)
        self.shape_info = shape_info
        self._build_preview()

    def _build_preview(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Shape type indicator
        type_label = QtWidgets.QLabel(
            f"Type: {self.shape_info.geometry_type.value.title()}"
        )
        type_label.setStyleSheet("font-weight: bold; color: #2c5aa0;")
        layout.addWidget(type_label)

        # Dimensions display
        measurement_system = session_state.get_measurement_system()
        width_mm, height_mm, depth_mm = self.shape_info.dimensions

        if measurement_system == "imperial":
            width_str = sc_units.format_length(width_mm, "imperial")
            height_str = sc_units.format_length(height_mm, "imperial")
            depth_str = sc_units.format_length(depth_mm, "imperial")
        else:
            width_str = f"{width_mm:.1f} mm"
            height_str = f"{height_mm:.1f} mm"
            depth_str = f"{depth_mm:.1f} mm"

        dims_label = QtWidgets.QLabel(f"{width_str} × {height_str} × {depth_str}")
        layout.addWidget(dims_label)

        # Area if available
        if self.shape_info.area_mm2:
            if measurement_system == "imperial":
                area_in2 = self.shape_info.area_mm2 / (25.4 * 25.4)
                area_str = f"Area: {area_in2:.2f} in²"
            else:
                area_str = f"Area: {self.shape_info.area_mm2:.0f} mm²"
            area_label = QtWidgets.QLabel(area_str)
            area_label.setStyleSheet("color: #666;")
            layout.addWidget(area_label)

        # Complexity indicator
        complexity_colors = {
            GeometryType.RECTANGULAR: "#4CAF50",  # Green
            GeometryType.CURVED: "#FF9800",  # Orange
            GeometryType.COMPLEX: "#F44336",  # Red
        }
        color = complexity_colors.get(self.shape_info.geometry_type, "#666")
        complexity_label = QtWidgets.QLabel(
            f"Complexity: {self.shape_info.complexity_score:.1f}"
        )
        complexity_label.setStyleSheet(f"color: {color}; font-size: 10px;")
        layout.addWidget(complexity_label)


class EnhancedShapeSelectionDialog(QtWidgets.QDialog):
    """Enhanced dialog for selecting FreeCAD shapes with previews and validation.

    This dialog provides a comprehensive interface for users to select which
    FreeCAD objects should be included in the nesting process, featuring:
    - Visual previews of each shape
    - Detailed dimension and complexity information
    - Selection validation and feedback
    - Bulk selection controls
    """

    def __init__(self, detected_shapes: Optional[List[ShapeInfo]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Shapes for Nesting")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)

        self.detected_shapes = detected_shapes or []
        self.shape_widgets = {}  # Map shape_info to widget
        self.validation_errors = []

        self._build_ui()
        self._populate_shape_list()
        self._update_selection_summary()

    def _build_ui(self):
        """Build the enhanced user interface."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(8)

        # Header section
        header_layout = QtWidgets.QHBoxLayout()

        title_label = QtWidgets.QLabel("Select shapes to include in nesting:")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c5aa0;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Bulk selection controls
        self.select_all_btn = QtWidgets.QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        header_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QtWidgets.QPushButton("Select None")
        self.select_none_btn.clicked.connect(self._select_none)
        header_layout.addWidget(self.select_none_btn)

        main_layout.addLayout(header_layout)

        # Main content area with splitter
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left side: Shape list with checkboxes
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        list_label = QtWidgets.QLabel("Detected Shapes:")
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)

        self.shapes_list = QtWidgets.QListWidget()
        self.shapes_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.shapes_list.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.shapes_list)

        splitter.addWidget(left_widget)

        # Right side: Preview and details
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        preview_label = QtWidgets.QLabel("Shape Details:")
        preview_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(preview_label)

        # Scroll area for preview content
        self.preview_scroll = QtWidgets.QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setMinimumWidth(250)

        self.preview_content = QtWidgets.QWidget()
        self.preview_layout = QtWidgets.QVBoxLayout(self.preview_content)
        self.preview_scroll.setWidget(self.preview_content)

        right_layout.addWidget(self.preview_scroll)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 300])  # Give more space to the list

        main_layout.addWidget(splitter)

        # Selection summary
        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 8px; border-radius: 4px;"
        )
        main_layout.addWidget(self.summary_label)

        # Validation feedback area
        self.validation_label = QtWidgets.QLabel()
        self.validation_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        self.validation_label.setWordWrap(True)
        self.validation_label.hide()  # Hidden by default
        main_layout.addWidget(self.validation_label)

        # Button box
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        self.ok_button = button_box.button(QtWidgets.QDialogButtonBox.Ok)
        main_layout.addWidget(button_box)

    def populate_shape_list(self, detected_shapes: List[ShapeInfo]) -> None:
        """Populate the shape list with detected shapes."""
        self.detected_shapes = detected_shapes
        self._populate_shape_list()
        self._update_selection_summary()

    def generate_shape_previews(self, shapes: List[ShapeInfo]) -> List[PreviewWidget]:
        """Generate preview widgets for the provided shapes."""
        previews = []
        for shape_info in shapes:
            preview_widget = PreviewWidget(shape_info)
            previews.append(preview_widget)
        return previews

    def validate_selection(self) -> Dict[str, Any]:
        """Validate the current selection and return validation results."""
        selected_shapes = self.get_selected_shapes()

        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "selected_count": len(selected_shapes),
        }

        # Check if any shapes are selected
        if not selected_shapes:
            validation_result["is_valid"] = False
            validation_result["errors"].append(
                "No shapes selected. Please select at least one shape to nest."
            )

        # Check for overly complex shapes
        complex_shapes = [
            s
            for s in selected_shapes
            if s.geometry_type == GeometryType.COMPLEX and s.complexity_score > 8.0
        ]
        if complex_shapes:
            shape_names = [s.label for s in complex_shapes[:3]]  # Show first 3
            warning_msg = f"Complex shapes detected: {', '.join(shape_names)}"
            if len(complex_shapes) > 3:
                warning_msg += f" and {len(complex_shapes) - 3} more"
            warning_msg += ". These may require longer processing time."
            validation_result["warnings"].append(warning_msg)

        # Check for very small shapes
        small_shapes = [
            s for s in selected_shapes if min(s.dimensions[:2]) < 10.0
        ]  # Less than 10mm
        if small_shapes:
            validation_result["warnings"].append(
                f"{len(small_shapes)} very small shapes detected. Verify dimensions are correct."
            )

        return validation_result

    def get_selected_shapes(self) -> List[ShapeInfo]:
        """Return list of currently selected shapes."""
        selected_shapes = []
        for idx in range(self.shapes_list.count()):
            item = self.shapes_list.item(idx)
            if item.checkState() == QtCore.Qt.Checked:
                shape_info = item.data(QtCore.Qt.UserRole)
                if shape_info:
                    selected_shapes.append(shape_info)
        return selected_shapes

    def get_data(self) -> Dict[str, Any]:
        """Return selection data for processing."""
        selected_shapes = self.get_selected_shapes()
        return {
            "selected_shapes": selected_shapes,
            "selection_count": len(selected_shapes),
            "validation_result": self.validate_selection(),
        }

    def _populate_shape_list(self):
        """Populate the shapes list widget with detected shapes."""
        self.shapes_list.clear()
        self.shape_widgets.clear()

        if not self.detected_shapes:
            # Show message when no shapes detected
            no_shapes_item = QtWidgets.QListWidgetItem(
                "No shapes detected in the current document"
            )
            no_shapes_item.setFlags(QtCore.Qt.NoItemFlags)  # Make it non-interactive
            no_shapes_item.setForeground(QtCore.Qt.gray)
            self.shapes_list.addItem(no_shapes_item)
            return

        for shape_info in self.detected_shapes:
            # Create list item with checkbox
            display_text = f"{shape_info.label}"

            # Add dimension info to display text
            measurement_system = session_state.get_measurement_system()
            width_mm, height_mm, _ = shape_info.dimensions

            if measurement_system == "imperial":
                width_str = sc_units.format_length(width_mm, "imperial")
                height_str = sc_units.format_length(height_mm, "imperial")
            else:
                width_str = f"{width_mm:.1f}mm"
                height_str = f"{height_mm:.1f}mm"

            display_text += f" ({width_str} × {height_str})"

            item = QtWidgets.QListWidgetItem(display_text)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)  # Default to selected
            item.setData(QtCore.Qt.UserRole, shape_info)

            # Add visual indicators for geometry type
            if shape_info.geometry_type == GeometryType.RECTANGULAR:
                item.setIcon(self._create_type_icon("□", "#4CAF50"))
            elif shape_info.geometry_type == GeometryType.CURVED:
                item.setIcon(self._create_type_icon("◐", "#FF9800"))
            else:
                item.setIcon(self._create_type_icon("◆", "#F44336"))

            self.shapes_list.addItem(item)

            # Create preview widget
            preview_widget = PreviewWidget(shape_info)
            self.shape_widgets[shape_info] = preview_widget

    def _create_type_icon(self, symbol: str, color: str) -> QtCore.QIcon:
        """Create a simple icon for geometry type indication."""
        # This is a simplified implementation
        # In a full version, this would create proper QIcon objects
        return QtCore.QIcon()  # Placeholder

    def _on_selection_changed(self):
        """Handle selection change in the shapes list."""
        current_item = self.shapes_list.currentItem()
        if current_item and current_item.data(QtCore.Qt.UserRole):
            shape_info = current_item.data(QtCore.Qt.UserRole)
            self._show_shape_preview(shape_info)

        self._update_selection_summary()

    def _show_shape_preview(self, shape_info: ShapeInfo):
        """Show preview for the selected shape."""
        # Clear existing preview content
        for i in reversed(range(self.preview_layout.count())):
            child = self.preview_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Add preview widget
        if shape_info in self.shape_widgets:
            preview_widget = self.shape_widgets[shape_info]
            self.preview_layout.addWidget(preview_widget)

        self.preview_layout.addStretch()

    def _select_all(self):
        """Select all shapes in the list."""
        for idx in range(self.shapes_list.count()):
            item = self.shapes_list.item(idx)
            if item.flags() & QtCore.Qt.ItemIsUserCheckable:
                item.setCheckState(QtCore.Qt.Checked)
        self._update_selection_summary()

    def _select_none(self):
        """Deselect all shapes in the list."""
        for idx in range(self.shapes_list.count()):
            item = self.shapes_list.item(idx)
            if item.flags() & QtCore.Qt.ItemIsUserCheckable:
                item.setCheckState(QtCore.Qt.Unchecked)
        self._update_selection_summary()

    def _update_selection_summary(self):
        """Update the selection summary display."""
        selected_count = len(self.get_selected_shapes())
        total_count = len(self.detected_shapes)

        if total_count == 0:
            summary_text = "No shapes detected in the current document."
        else:
            summary_text = (
                f"Selected {selected_count} of {total_count} shapes for nesting."
            )

            if selected_count > 0:
                # Calculate total area if available
                selected_shapes = self.get_selected_shapes()
                total_area = sum(s.area_mm2 for s in selected_shapes if s.area_mm2)

                if total_area > 0:
                    measurement_system = session_state.get_measurement_system()
                    if measurement_system == "imperial":
                        area_in2 = total_area / (25.4 * 25.4)
                        summary_text += f" Total area: {area_in2:.2f} in²"
                    else:
                        summary_text += f" Total area: {total_area:.0f} mm²"

        self.summary_label.setText(summary_text)

        # Update OK button state
        validation_result = self.validate_selection()
        self.ok_button.setEnabled(validation_result["is_valid"])

        # Show validation feedback
        if validation_result["errors"]:
            self.validation_label.setText(validation_result["errors"][0])
            self.validation_label.show()
        elif validation_result["warnings"]:
            self.validation_label.setText(f"⚠ {validation_result['warnings'][0]}")
            self.validation_label.setStyleSheet("color: #f57c00; font-weight: bold;")
            self.validation_label.show()
        else:
            self.validation_label.hide()

    def _on_accept(self):
        """Handle OK button click with validation."""
        validation_result = self.validate_selection()

        if not validation_result["is_valid"]:
            # Show error message
            QtWidgets.QMessageBox.warning(
                self,
                "Selection Invalid",
                (
                    validation_result["errors"][0]
                    if validation_result["errors"]
                    else "Invalid selection."
                ),
            )
            return

        # Show warnings if any
        if validation_result["warnings"]:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Selection Warnings",
                f"{validation_result['warnings'][0]}\n\nDo you want to continue?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes,
            )

            if reply != QtWidgets.QMessageBox.Yes:
                return

        self.accept()


# Maintain backward compatibility
SC_SelectShapesDialog = EnhancedShapeSelectionDialog
