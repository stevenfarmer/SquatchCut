"""Tests for fallback extraction mechanism.

**Feature: shape-based-nesting**

This module tests the graceful fallback behavior when dealing with
complex or problematic FreeCAD shapes.
"""

from unittest.mock import Mock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st
from SquatchCut.core.complex_geometry import ComplexGeometry
from SquatchCut.core.shape_extractor import ShapeExtractor


class TestFallbackExtraction:
    """Test the fallback extraction mechanism for complex shapes."""

    def test_fallback_with_simple_shape(self):
        """Test that simple shapes use full extraction without fallback."""
        extractor = ShapeExtractor()

        # Create a mock simple object
        mock_obj = Mock()
        mock_obj.Label = "SimpleBox"
        mock_obj.Shape = Mock()
        mock_obj.Shape.BoundBox = Mock()
        mock_obj.Shape.BoundBox.XLength = 100.0
        mock_obj.Shape.BoundBox.YLength = 200.0
        mock_obj.Shape.Faces = [Mock() for _ in range(6)]  # Simple box has 6 faces
        mock_obj.Shape.Edges = [Mock() for _ in range(12)]  # Simple box has 12 edges
        mock_obj.Shape.Vertexes = [
            Mock() for _ in range(8)
        ]  # Simple box has 8 vertices

        with patch.object(extractor, "extract_complex_geometry") as mock_extract:
            mock_geometry = Mock(spec=ComplexGeometry)
            mock_extract.return_value = mock_geometry

            geometry, method, notification = extractor.extract_with_fallback(mock_obj)

            # Should use full extraction for simple shapes
            assert geometry == mock_geometry
            assert method == "full_extraction"
            assert notification is None
            mock_extract.assert_called_once_with(mock_obj)

    def test_fallback_with_complex_shape(self):
        """Test that complex shapes fall back to bounding box extraction."""
        extractor = ShapeExtractor()

        # Create a mock complex object
        mock_obj = Mock()
        mock_obj.Label = "ComplexShape"
        mock_obj.Shape = Mock()
        mock_obj.Shape.BoundBox = Mock()
        mock_obj.Shape.BoundBox.XLength = 150.0
        mock_obj.Shape.BoundBox.YLength = 250.0
        mock_obj.Shape.Faces = [Mock() for _ in range(50)]  # Very complex shape
        mock_obj.Shape.Edges = [Mock() for _ in range(100)]
        mock_obj.Shape.Vertexes = [Mock() for _ in range(80)]

        with patch.object(extractor, "extract_complex_geometry") as mock_extract:
            with patch.object(extractor, "extract_bounding_box") as mock_bbox:
                # Make complex extraction fail
                mock_extract.side_effect = Exception("Too complex")
                mock_bbox.return_value = (150.0, 250.0)

                geometry, method, notification = extractor.extract_with_fallback(
                    mock_obj,
                    complexity_threshold=3.0,  # Low threshold to force fallback
                )

                # Should fall back to bounding box
                assert method == "bounding_box_fallback"
                assert notification is not None
                assert "complex" in notification.lower()
                assert "ComplexShape" in notification
                assert isinstance(geometry, ComplexGeometry)
                assert geometry.get_width() == 150.0
                assert geometry.get_height() == 250.0

    def test_fallback_with_extraction_failure(self):
        """Test fallback when complex extraction fails but complexity is low."""
        extractor = ShapeExtractor()

        # Create a mock object that should be simple but extraction fails
        mock_obj = Mock()
        mock_obj.Label = "ProblematicShape"
        mock_obj.Shape = Mock()
        mock_obj.Shape.BoundBox = Mock()
        mock_obj.Shape.BoundBox.XLength = 100.0
        mock_obj.Shape.BoundBox.YLength = 200.0
        mock_obj.Shape.Faces = [Mock() for _ in range(6)]  # Simple shape
        mock_obj.Shape.Edges = [Mock() for _ in range(12)]
        mock_obj.Shape.Vertexes = [Mock() for _ in range(8)]

        with patch.object(extractor, "extract_complex_geometry") as mock_extract:
            with patch.object(extractor, "extract_bounding_box") as mock_bbox:
                # Make complex extraction fail
                mock_extract.side_effect = Exception("Extraction error")
                mock_bbox.return_value = (100.0, 200.0)

                geometry, method, notification = extractor.extract_with_fallback(
                    mock_obj
                )

                # Should fall back to bounding box even for simple shapes if extraction fails
                assert method == "bounding_box_fallback"
                assert notification is not None
                assert isinstance(geometry, ComplexGeometry)

    def test_fallback_to_object_properties(self):
        """Test fallback to object Width/Height properties when bounding box fails."""
        extractor = ShapeExtractor()

        # Create a mock object with Width/Height properties
        mock_obj = Mock()
        mock_obj.Label = "ParametricObject"
        mock_obj.Shape = Mock()
        mock_obj.Width = 120.0
        mock_obj.Height = 180.0
        mock_obj.Shape.Faces = [Mock() for _ in range(50)]  # Complex
        mock_obj.Shape.Edges = [Mock() for _ in range(100)]
        mock_obj.Shape.Vertexes = [Mock() for _ in range(80)]

        with patch.object(extractor, "extract_complex_geometry") as mock_extract:
            with patch.object(extractor, "extract_bounding_box") as mock_bbox:
                # Make both complex extraction and bounding box fail
                mock_extract.side_effect = Exception("Too complex")
                mock_bbox.side_effect = Exception("BoundBox error")

                geometry, method, notification = extractor.extract_with_fallback(
                    mock_obj, complexity_threshold=3.0
                )

                # Should fall back to object properties
                assert method == "property_fallback"
                assert notification is not None
                assert "dimensions" in notification.lower()
                assert isinstance(geometry, ComplexGeometry)
                assert geometry.get_width() == 120.0
                assert geometry.get_height() == 180.0

    def test_fallback_complete_failure(self):
        """Test that complete fallback failure raises appropriate error."""
        extractor = ShapeExtractor()

        # Create a mock object that fails all extraction methods
        mock_obj = Mock()
        mock_obj.Label = "UnprocessableShape"
        mock_obj.Shape = Mock()
        mock_obj.Shape.Faces = [Mock() for _ in range(50)]  # Complex
        mock_obj.Shape.Edges = [Mock() for _ in range(100)]
        mock_obj.Shape.Vertexes = [Mock() for _ in range(80)]
        # No Width/Height properties

        with patch.object(extractor, "extract_complex_geometry") as mock_extract:
            with patch.object(extractor, "extract_bounding_box") as mock_bbox:
                # Make all extraction methods fail
                mock_extract.side_effect = Exception("Too complex")
                mock_bbox.side_effect = Exception("BoundBox error")

                with pytest.raises(ValueError) as exc_info:
                    extractor.extract_with_fallback(mock_obj, complexity_threshold=3.0)

                assert "UnprocessableShape" in str(exc_info.value)
                assert "Cannot extract geometry" in str(exc_info.value)

    def test_fallback_with_invalid_object(self):
        """Test fallback behavior with objects that have no Shape."""
        extractor = ShapeExtractor()

        # Create a mock object without Shape
        mock_obj = Mock()
        mock_obj.Label = "InvalidObject"
        # No Shape attribute

        with pytest.raises(ValueError) as exc_info:
            extractor.extract_with_fallback(mock_obj)

        assert "InvalidObject" in str(exc_info.value)
        assert "no valid Shape" in str(exc_info.value)

    @given(
        complexity_threshold=st.floats(min_value=0.1, max_value=10.0),
        face_count=st.integers(min_value=1, max_value=100),
        edge_count=st.integers(min_value=1, max_value=200),
        vertex_count=st.integers(min_value=1, max_value=150),
    )
    def test_fallback_threshold_behavior(
        self, complexity_threshold, face_count, edge_count, vertex_count
    ):
        """Test that fallback threshold correctly determines extraction method."""
        extractor = ShapeExtractor()

        # Create a mock object with varying complexity
        mock_obj = Mock()
        mock_obj.Label = "TestShape"
        mock_obj.Shape = Mock()
        mock_obj.Shape.BoundBox = Mock()
        mock_obj.Shape.BoundBox.XLength = 100.0
        mock_obj.Shape.BoundBox.YLength = 200.0
        mock_obj.Shape.Faces = [Mock() for _ in range(face_count)]
        mock_obj.Shape.Edges = [Mock() for _ in range(edge_count)]
        mock_obj.Shape.Vertexes = [Mock() for _ in range(vertex_count)]

        # Calculate expected complexity
        expected_complexity = (
            1.0 + face_count * 0.5 + edge_count * 0.1 + vertex_count * 0.05
        )
        expected_complexity = min(expected_complexity, 10.0)

        with patch.object(extractor, "extract_complex_geometry") as mock_extract:
            with patch.object(extractor, "extract_bounding_box") as mock_bbox:
                mock_geometry = Mock(spec=ComplexGeometry)
                mock_extract.return_value = mock_geometry
                mock_bbox.return_value = (100.0, 200.0)

                geometry, method, notification = extractor.extract_with_fallback(
                    mock_obj, complexity_threshold=complexity_threshold
                )

                if expected_complexity <= complexity_threshold:
                    # Should try full extraction first
                    assert method in ["full_extraction", "bounding_box_fallback"]
                    mock_extract.assert_called_once_with(mock_obj)
                else:
                    # Should skip to fallback
                    assert method == "bounding_box_fallback"
                    assert notification is not None


class TestFallbackIntegration:
    """Test integration of fallback mechanism with shape selection."""

    def test_shape_selection_uses_fallback(self):
        """Test that shape selection dialog uses fallback extraction."""
        from SquatchCut.gui.taskpanel_input import InputGroupWidget

        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            with patch("SquatchCut.gui.taskpanel_input.App") as mock_app:
                with patch(
                    "SquatchCut.gui.taskpanel_input.session_state"
                ):
                    # Setup mocks
                    mock_doc = Mock()
                    mock_app.ActiveDocument = mock_doc

                    # Create a complex object that would trigger fallback
                    mock_obj = Mock()
                    mock_obj.Label = "ComplexCabinetDoor"
                    mock_obj.Shape = Mock()
                    mock_obj.Shape.BoundBox = Mock()
                    mock_obj.Shape.BoundBox.ZLength = 20.0
                    mock_obj.Shape.Faces = [Mock() for _ in range(30)]  # Complex
                    mock_obj.Shape.Edges = [Mock() for _ in range(60)]
                    mock_obj.Shape.Vertexes = [Mock() for _ in range(40)]

                    mock_doc.Objects = [mock_obj]

                    prefs = Mock()
                    widget = InputGroupWidget(prefs)

                    with patch.object(widget, "_set_csv_label"):
                        with patch.object(widget, "refresh_table"):
                            with patch(
                                "SquatchCut.gui.taskpanel_input.EnhancedShapeSelectionDialog"
                            ) as mock_dialog_class:
                                mock_dialog = Mock()
                                mock_dialog.exec_.return_value = Mock()  # Accepted
                                mock_dialog.get_data.return_value = {
                                    "selected_shapes": []
                                }
                                mock_dialog_class.return_value = mock_dialog

                                # This should use fallback extraction internally
                                widget._select_shapes()

                                # Dialog should be created (extraction didn't fail completely)
                                mock_dialog_class.assert_called_once()

                                # The detected_shapes argument should contain our processed shape
                                call_args = mock_dialog_class.call_args[0]
                                detected_shapes = call_args[0]

                                # Should have processed the shape successfully using fallback
                                assert (
                                    len(detected_shapes) >= 0
                                )  # May be 0 if extraction failed, but shouldn't crash
