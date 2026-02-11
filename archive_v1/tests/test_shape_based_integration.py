"""Tests for shape-based nesting integration with main TaskPanel.

**Feature: shape-based-nesting**

This module tests the integration between shape selection and the main SquatchCut workflow.
"""

from unittest.mock import Mock, patch

from SquatchCut.gui.taskpanel_input import InputGroupWidget
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel


class TestShapeBasedIntegration:
    """Test integration between shape selection and main TaskPanel."""

    def test_input_widget_has_shape_selection_button(self):
        """Test that InputGroupWidget has a shape selection button."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            prefs = Mock()
            widget = InputGroupWidget(prefs)

            # Should have both CSV and shape selection buttons
            assert hasattr(widget, "load_csv_button")
            assert hasattr(widget, "select_shapes_button")
            assert widget.select_shapes_button.text() == "Select Shapes"

    def test_input_widget_has_shapes_selected_signal(self):
        """Test that InputGroupWidget emits shapes_selected signal."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            prefs = Mock()
            widget = InputGroupWidget(prefs)

            # Should have the shapes_selected signal
            assert hasattr(widget, "shapes_selected")

    @patch("SquatchCut.gui.taskpanel_input.show_error")
    @patch("SquatchCut.gui.taskpanel_input.App")
    @patch("SquatchCut.gui.dialogs.dlg_select_shapes.EnhancedShapeSelectionDialog")
    def test_select_shapes_opens_dialog(
        self, mock_dialog_class, mock_app, mock_show_error
    ):
        """Test that clicking Select Shapes opens the selection dialog."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.Objects = []
        mock_app.ActiveDocument = mock_doc

        mock_dialog = Mock()
        mock_dialog.exec_.return_value = Mock()  # QDialog.Rejected
        mock_dialog_class.return_value = mock_dialog

        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            prefs = Mock()
            widget = InputGroupWidget(prefs)

            # Trigger shape selection
            widget._select_shapes()

            # Should show error for no shapes found
            mock_show_error.assert_called_once()

    @patch("SquatchCut.core.session_state")
    def test_main_taskpanel_handles_shapes_selected_signal(self, mock_session_state):
        """Test that main TaskPanel handles shapes_selected signal."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            with patch(
                "SquatchCut.core.session.detect_document_measurement_system",
                return_value="metric",
            ):
                with patch(
                    "SquatchCut.gui.taskpanel_main.session_state"
                ) as mock_main_session:
                    with patch("SquatchCut.gui.taskpanel_main.settings"):
                        # Mock session state methods
                        mock_main_session.get_sheet_size.return_value = (1220.0, 2440.0)
                        mock_main_session.get_measurement_system.return_value = "metric"
                        mock_main_session.get_panels.return_value = []
                        mock_main_session.get_last_layout.return_value = (
                            []
                        )  # Empty layout
                        mock_main_session.get_nesting_stats.return_value = {}

                        panel = SquatchCutTaskPanel()

                        # Should have connected to shapes_selected signal
                        assert hasattr(panel, "_on_shapes_selected")

                        # Test the signal handler
                        panel._on_shapes_selected()

                        # Should update status and validation
                        assert panel.has_csv_data  # Treat shapes like CSV data

    def test_nesting_command_detects_shape_based_data(self):
        """Test that RunNestingCommand can detect shape-based data."""
        from SquatchCut.gui.commands.cmd_run_nesting import RunNestingCommand

        command = RunNestingCommand()

        # Test with CSV data (should return False)
        csv_panels = [{"id": "panel1", "width": 100, "height": 200}]
        assert not command._should_use_geometric_nesting(csv_panels)

        # Test with shape-based data (should return True)
        shape_panels = [
            {"id": "shape1", "width": 100, "height": 200, "source": "freecad_shape"}
        ]
        assert command._should_use_geometric_nesting(shape_panels)

        # Test with mixed data (should return True if any shape-based)
        mixed_panels = [
            {"id": "panel1", "width": 100, "height": 200},
            {"id": "shape1", "width": 150, "height": 250, "source": "freecad_shape"},
        ]
        assert command._should_use_geometric_nesting(mixed_panels)

    @patch("SquatchCut.gui.commands.cmd_run_nesting.GeometryNestingEngine")
    def test_geometric_nesting_integration(self, mock_engine_class):
        """Test that geometric nesting is called for shape-based data."""
        from SquatchCut.core.nesting import Part
        from SquatchCut.gui.commands.cmd_run_nesting import RunNestingCommand

        # Setup mock engine
        mock_engine = Mock()
        mock_result = Mock()

        # Create a mock placed geometry
        mock_placed_geom = Mock()
        mock_placed_geom.geometry.id = "shape1"
        mock_placed_geom.x = 10
        mock_placed_geom.y = 20
        mock_placed_geom.geometry.get_width.return_value = 100
        mock_placed_geom.geometry.get_height.return_value = 200
        mock_placed_geom.rotation = 0
        mock_placed_geom.sheet_index = 0

        mock_result.placed_geometries = [mock_placed_geom]  # Non-empty list
        mock_result.utilization_percent = 75.0
        mock_result.sheets_used = 1
        mock_result.total_area_used = 1000.0
        mock_result.processing_time = 0.5
        mock_engine.nest_complex_shapes.return_value = mock_result
        mock_engine_class.return_value = mock_engine

        command = RunNestingCommand()

        # Test data
        parts = [Part(id="shape1", width=100, height=200, can_rotate=True)]
        panels_data = [
            {
                "id": "shape1",
                "width": 100,
                "height": 200,
                "source": "freecad_shape",
                "allow_rotate": True,
            }
        ]

        # Run geometric nesting
        result = command._run_geometric_nesting(parts, panels_data, 1000, 800, 5)

        # Should call the geometric nesting engine
        mock_engine_class.assert_called_once()
        mock_engine.nest_complex_shapes.assert_called_once()

        # Should return a valid result when there are placements
        assert result is not None
        assert "placements" in result
        assert len(result["placements"]) == 1
        assert result["utilization"] == 75.0

    def test_shape_extractor_methods_exist(self):
        """Test that ShapeExtractor has the required methods for integration."""
        from SquatchCut.core.shape_extractor import ShapeExtractor

        extractor = ShapeExtractor()

        # Should have the overloaded methods for FreeCAD objects
        assert hasattr(extractor, "_classify_geometry_type")
        assert hasattr(extractor, "_assess_complexity")

        # Test with mock FreeCAD object
        mock_obj = Mock()
        mock_obj.Shape = Mock()
        mock_obj.Shape.ShapeType = "Solid"
        mock_obj.Shape.BoundBox = Mock()
        mock_obj.Shape.BoundBox.XLength = 100
        mock_obj.Shape.BoundBox.YLength = 200
        mock_obj.Shape.Faces = []
        mock_obj.Shape.Edges = []
        mock_obj.Shape.Vertexes = []

        # Should not raise exceptions
        geom_type = extractor._classify_geometry_type(mock_obj)
        complexity = extractor._assess_complexity(mock_obj)

        assert geom_type is not None
        assert isinstance(complexity, (int, float))
        assert complexity >= 0
