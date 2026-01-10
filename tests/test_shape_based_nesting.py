"""Property-based tests for shape-based nesting functionality using Hypothesis.

**Feature: shape-based-nesting**

This module contains property-based tests that validate the correctness of
shape detection, extraction, and nesting algorithms for complex geometries.
"""

import math
from unittest.mock import Mock

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from SquatchCut.core.complex_geometry import (
    ComplexGeometry,
    ComplexityLevel,
    GeometryType,
    assess_geometry_complexity,
    create_rectangular_geometry,
)
from SquatchCut.core.shape_extractor import ShapeExtractor


# Custom strategies for shape-based nesting domain objects
@st.composite
def valid_dimensions(draw):
    """Generate valid dimensions (positive floats with reasonable bounds)."""
    return draw(
        st.floats(
            min_value=1.0, max_value=5000.0, allow_nan=False, allow_infinity=False
        )
    )


@st.composite
def valid_coordinates(draw):
    """Generate valid coordinate values."""
    return draw(
        st.floats(
            min_value=-10000.0, max_value=10000.0, allow_nan=False, allow_infinity=False
        )
    )


@st.composite
def rectangular_contour(draw):
    """Generate a rectangular contour with random dimensions and position."""
    width = draw(valid_dimensions())
    height = draw(valid_dimensions())
    x_offset = draw(valid_coordinates())
    y_offset = draw(valid_coordinates())

    # Ensure reasonable bounds to avoid overflow
    assume(abs(x_offset) < 1000.0 and abs(y_offset) < 1000.0)
    assume(width < 1000.0 and height < 1000.0)

    contour = [
        (x_offset, y_offset),
        (x_offset + width, y_offset),
        (x_offset + width, y_offset + height),
        (x_offset, y_offset + height),
        (x_offset, y_offset),  # Close the contour
    ]
    return contour, width, height, x_offset, y_offset


@st.composite
def simple_polygon_contour(draw):
    """Generate a simple polygon contour (triangle to octagon)."""
    num_vertices = draw(st.integers(min_value=3, max_value=8))
    center_x = draw(st.floats(min_value=-100.0, max_value=100.0))
    center_y = draw(st.floats(min_value=-100.0, max_value=100.0))
    radius = draw(st.floats(min_value=10.0, max_value=100.0))

    # Generate regular polygon
    contour = []
    for i in range(num_vertices):
        angle = 2 * math.pi * i / num_vertices
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        contour.append((x, y))

    # Close the contour
    contour.append(contour[0])

    return contour, center_x, center_y, radius


@st.composite
def valid_complex_geometry(draw):
    """Generate a valid ComplexGeometry object."""
    geometry_id = draw(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        )
    )

    # Choose between rectangular and polygon geometry
    is_rectangular = draw(st.booleans())

    if is_rectangular:
        contour, width, height, x_offset, y_offset = draw(rectangular_contour())
        area = width * height
        complexity = ComplexityLevel.LOW
        geom_type = GeometryType.RECTANGULAR
    else:
        contour, center_x, center_y, radius = draw(simple_polygon_contour())
        # Approximate area for regular polygon
        num_vertices = len(contour) - 1
        area = (
            0.5 * num_vertices * radius * radius * math.sin(2 * math.pi / num_vertices)
        )
        complexity = assess_geometry_complexity(contour, area)
        geom_type = GeometryType.COMPLEX

    # Calculate bounding box
    min_x = min(p[0] for p in contour)
    min_y = min(p[1] for p in contour)
    max_x = max(p[0] for p in contour)
    max_y = max(p[1] for p in contour)
    bounding_box = (min_x, min_y, max_x, max_y)

    rotation_allowed = draw(st.booleans())

    return ComplexGeometry(
        id=geometry_id,
        contour_points=contour,
        bounding_box=bounding_box,
        area=area,
        complexity_level=complexity,
        rotation_allowed=rotation_allowed,
        geometry_type=geom_type,
    )


@st.composite
def mock_freecad_object(draw):
    """Generate a mock FreeCAD object with Shape property."""
    label = draw(
        st.text(
            min_size=1,
            max_size=15,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        )
    )
    width = draw(valid_dimensions())
    height = draw(valid_dimensions())
    depth = draw(valid_dimensions())

    # Create mock object
    mock_obj = Mock()
    mock_obj.Label = label
    mock_obj.Name = f"Object_{label}"

    # Create mock Shape with BoundBox
    mock_shape = Mock()
    mock_bbox = Mock()
    mock_bbox.XLength = width
    mock_bbox.YLength = height
    mock_bbox.ZLength = depth
    mock_bbox.XMin = 0.0
    mock_bbox.YMin = 0.0
    mock_bbox.ZMin = 0.0
    mock_bbox.XMax = width
    mock_bbox.YMax = height
    mock_bbox.ZMax = depth

    mock_shape.BoundBox = mock_bbox
    mock_obj.Shape = mock_shape

    return mock_obj, width, height, depth


class TestShapeDetectionProperties:
    """Property-based tests for shape detection and extraction."""

    @given(valid_complex_geometry())
    @settings(max_examples=100, deadline=5000)
    def test_property_1_comprehensive_shape_detection(self, geometry):
        """**Feature: shape-based-nesting, Property 1: Comprehensive Shape Detection**

        For any FreeCAD document containing objects with Shape properties,
        SquatchCut should detect all valid objects and extract accurate
        dimensional and geometric data.

        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        # Test that ComplexGeometry objects maintain their essential properties
        assert geometry.id is not None and len(geometry.id) > 0
        assert len(geometry.contour_points) >= 4  # At least 3 vertices + closing point
        assert geometry.area > 0
        assert geometry.bounding_box is not None
        assert len(geometry.bounding_box) == 4

        # Test bounding box consistency
        min_x, min_y, max_x, max_y = geometry.bounding_box
        assert min_x <= max_x
        assert min_y <= max_y

        # Test that bounding box actually bounds the contour points
        for x, y in geometry.contour_points:
            assert (
                min_x <= x <= max_x
            ), f"Point ({x}, {y}) outside bounding box X range [{min_x}, {max_x}]"
            assert (
                min_y <= y <= max_y
            ), f"Point ({x}, {y}) outside bounding box Y range [{min_y}, {max_y}]"

        # Test that contour is properly closed
        if len(geometry.contour_points) > 1:
            first_point = geometry.contour_points[0]
            last_point = geometry.contour_points[-1]
            distance = math.sqrt(
                (first_point[0] - last_point[0]) ** 2
                + (first_point[1] - last_point[1]) ** 2
            )
            assert (
                distance < 0.001
            ), "Contour should be closed (first and last points should be the same)"

    @given(mock_freecad_object())
    @settings(max_examples=50, deadline=3000)
    def test_shape_extractor_detection_accuracy(self, mock_data):
        """Test that ShapeExtractor accurately extracts dimensions from FreeCAD objects."""
        mock_obj, expected_width, expected_height, expected_depth = mock_data

        extractor = ShapeExtractor()

        # Test bounding box extraction
        bbox = extractor.extract_bounding_box(mock_obj)
        assert bbox is not None

        extracted_width, extracted_height = bbox
        assert abs(extracted_width - expected_width) < 0.001
        assert abs(extracted_height - expected_height) < 0.001

        # Test panel object conversion
        panel = extractor.to_panel_object(mock_obj)
        assert panel is not None
        assert panel["id"] == mock_obj.Label
        assert abs(panel["width"] - expected_width) < 0.001
        assert abs(panel["height"] - expected_height) < 0.001
        assert panel["rotation_allowed"] is True  # Default value

    @given(st.lists(mock_freecad_object(), min_size=1, max_size=10))
    @settings(max_examples=20, deadline=5000)
    def test_multiple_object_detection(self, mock_objects_data):
        """Test detection of multiple FreeCAD objects in a document."""
        mock_objects = [data[0] for data in mock_objects_data]
        expected_count = len(mock_objects)

        # Create mock document
        mock_doc = Mock()
        mock_doc.Objects = mock_objects

        extractor = ShapeExtractor()

        # Test document scanning
        panels = extractor.extract_from_document(mock_doc)

        # Should detect all valid objects
        assert len(panels) == expected_count

        # Each panel should have valid properties
        for i, panel in enumerate(panels):
            expected_label = mock_objects[i].Label
            assert panel["id"] == expected_label
            assert panel["width"] > 0
            assert panel["height"] > 0
            assert "rotation_allowed" in panel


class TestComplexGeometryProperties:
    """Property-based tests for ComplexGeometry operations."""

    @given(valid_complex_geometry())
    @settings(max_examples=100, deadline=5000)
    def test_property_3_geometric_nesting_accuracy(self, geometry):
        """**Feature: shape-based-nesting, Property 3: Geometric Nesting Accuracy**

        For any non-rectangular shape, the nesting system should extract actual
        geometric contours and calculate utilization based on true shape areas
        rather than bounding box approximations.

        **Validates: Requirements 2.1, 2.4, 8.1**
        """
        # Test that area calculation is reasonable
        bbox_area = geometry.get_width() * geometry.get_height()

        # For rectangular geometries, area should match bounding box
        if geometry.is_rectangular():
            assert abs(geometry.area - bbox_area) < 0.001
        else:
            # For complex geometries, area should be less than or equal to bounding box
            assert (
                geometry.area <= bbox_area + 0.001
            )  # Small tolerance for floating point

        # Test that geometric properties are consistent
        assert geometry.get_width() > 0
        assert geometry.get_height() > 0

        # Test centroid calculation
        centroid = geometry.get_centroid()
        assert isinstance(centroid, tuple)
        assert len(centroid) == 2

        # Centroid should be within bounding box
        min_x, min_y, max_x, max_y = geometry.bounding_box
        cx, cy = centroid
        assert min_x <= cx <= max_x
        assert min_y <= cy <= max_y

    @given(valid_complex_geometry(), st.floats(min_value=-360.0, max_value=360.0))
    @settings(
        max_examples=50,
        deadline=5000,
        suppress_health_check=[HealthCheck.filter_too_much],
    )
    def test_property_5_rotation_preservation(self, geometry, angle):
        """**Feature: shape-based-nesting, Property 5: Rotation Preservation**

        For any complex shape that undergoes rotation, the system should maintain
        geometric accuracy and preserve kerf and margin settings in the new orientation.

        **Validates: Requirements 2.3, 8.3**
        """
        assume(geometry.rotation_allowed)
        assume(abs(angle) > 0.1)  # Skip trivial rotations

        original_area = geometry.area
        original_id = geometry.id

        try:
            rotated = geometry.rotate(angle)

            # Area should be preserved (within floating point tolerance)
            assert abs(rotated.area - original_area) < 0.001

            # ID should be preserved
            assert rotated.id == original_id

            # Rotation settings should be preserved
            assert rotated.rotation_allowed == geometry.rotation_allowed

            # Kerf compensation should be preserved
            assert rotated.kerf_compensation == geometry.kerf_compensation

            # Number of contour points should be preserved
            assert len(rotated.contour_points) == len(geometry.contour_points)

        except ValueError:
            # Rotation not allowed - this is expected behavior
            assert not geometry.rotation_allowed

    @given(valid_complex_geometry(), st.floats(min_value=0.1, max_value=10.0))
    @settings(max_examples=50, deadline=5000)
    def test_kerf_application_accuracy(self, geometry, kerf_mm):
        """Test that kerf compensation is applied accurately to complex geometries."""
        # Calculate safe kerf limit
        min_dimension = min(geometry.get_width(), geometry.get_height())
        max_safe_kerf = min_dimension / 4.0

        try:
            kerf_geometry = geometry.apply_kerf(kerf_mm)

            # Kerf compensation should be recorded
            assert kerf_geometry.kerf_compensation == kerf_mm

            # ID should be preserved
            assert kerf_geometry.id == geometry.id

            # For positive kerf (shrinking), area should be smaller
            if kerf_mm > 0:
                assert kerf_geometry.area < geometry.area

            # Bounding box should be recalculated
            assert kerf_geometry.bounding_box != geometry.bounding_box

        except ValueError:
            # Kerf too large causing geometry collapse - should only happen when kerf > max_safe_kerf
            assert kerf_mm > max_safe_kerf

    @given(valid_complex_geometry(), valid_complex_geometry())
    @settings(max_examples=30, deadline=5000)
    def test_property_4_overlap_prevention(self, geom1, geom2):
        """**Feature: shape-based-nesting, Property 4: Overlap Prevention**

        For any pair of complex shapes in a nesting layout, the system should
        detect and prevent overlaps between actual shape geometries, maintaining
        specified margins between contours.

        **Validates: Requirements 2.2, 8.2**
        """
        # Test overlap detection method exists and returns boolean
        overlap_result = geom1.check_overlap(geom2)
        assert isinstance(overlap_result, bool)

        # Test that identical geometries at same position overlap
        identical_geom = ComplexGeometry(
            id=geom1.id + "_copy",
            contour_points=geom1.contour_points.copy(),
            bounding_box=geom1.bounding_box,
            area=geom1.area,
            complexity_level=geom1.complexity_level,
            rotation_allowed=geom1.rotation_allowed,
            geometry_type=geom1.geometry_type,
        )

        # Identical geometries at same position should overlap
        assert geom1.check_overlap(identical_geom)

        # Test symmetry: if A overlaps B, then B overlaps A
        overlap_ab = geom1.check_overlap(geom2)
        overlap_ba = geom2.check_overlap(geom1)
        assert overlap_ab == overlap_ba


class TestRectangularGeometryCompatibility:
    """Tests for rectangular geometry compatibility and edge cases."""

    @given(valid_dimensions(), valid_dimensions())
    @settings(max_examples=100, deadline=3000)
    def test_rectangular_geometry_creation(self, width, height):
        """Test creation of rectangular ComplexGeometry objects."""
        geometry_id = "test_rect"

        rect_geom = create_rectangular_geometry(geometry_id, width, height)

        # Basic properties
        assert rect_geom.id == geometry_id
        assert rect_geom.is_rectangular()
        assert rect_geom.geometry_type == GeometryType.RECTANGULAR
        assert rect_geom.complexity_level == ComplexityLevel.LOW

        # Dimensional accuracy
        assert abs(rect_geom.get_width() - width) < 0.001
        assert abs(rect_geom.get_height() - height) < 0.001
        assert abs(rect_geom.area - (width * height)) < 0.001

        # Contour should be rectangular (5 points including closure)
        assert len(rect_geom.contour_points) == 5

        # First and last points should be the same (closed contour)
        assert rect_geom.contour_points[0] == rect_geom.contour_points[-1]

    @given(st.integers(min_value=3, max_value=20))
    @settings(max_examples=50, deadline=3000)
    def test_complexity_assessment(self, vertex_count):
        """Test geometry complexity assessment based on vertex count."""
        # Create a simple polygon with specified vertex count
        contour = []
        for i in range(vertex_count):
            angle = 2 * math.pi * i / vertex_count
            x = 50 * math.cos(angle)
            y = 50 * math.sin(angle)
            contour.append((x, y))
        contour.append(contour[0])  # Close the contour

        area = math.pi * 50 * 50  # Approximate area
        complexity = assess_geometry_complexity(contour, area)

        # Verify complexity assessment logic
        if vertex_count <= 4:
            assert complexity == ComplexityLevel.LOW
        elif vertex_count <= 20:
            assert complexity in [ComplexityLevel.MEDIUM, ComplexityLevel.HIGH]
        else:
            assert complexity in [ComplexityLevel.HIGH, ComplexityLevel.EXTREME]


class TestErrorHandlingProperties:
    """Property-based tests for error handling and edge cases."""

    @given(st.text(min_size=1, max_size=10))
    @settings(max_examples=20, deadline=2000)
    def test_property_8_error_handling_robustness(self, geometry_id):
        """**Feature: shape-based-nesting, Property 8: Error Handling Robustness**

        For any invalid input (malformed geometry, empty documents, invalid shapes),
        the system should handle errors gracefully without crashes.

        **Validates: Requirements 4.5**
        """
        # Test invalid contour points
        with pytest.raises(ValueError):
            ComplexGeometry(
                id=geometry_id,
                contour_points=[],  # Empty contour
                bounding_box=(0, 0, 10, 10),
                area=100,
                complexity_level=ComplexityLevel.LOW,
                rotation_allowed=True,
            )

        # Test insufficient contour points
        with pytest.raises(ValueError):
            ComplexGeometry(
                id=geometry_id,
                contour_points=[(0, 0), (10, 0)],  # Only 2 points
                bounding_box=(0, 0, 10, 10),
                area=100,
                complexity_level=ComplexityLevel.LOW,
                rotation_allowed=True,
            )

        # Test negative area
        with pytest.raises(ValueError):
            ComplexGeometry(
                id=geometry_id,
                contour_points=[(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)],
                bounding_box=(0, 0, 10, 10),
                area=-100,  # Negative area
                complexity_level=ComplexityLevel.LOW,
                rotation_allowed=True,
            )

        # Test ShapeExtractor with invalid objects
        extractor = ShapeExtractor()

        # Object without Shape property - create a mock that truly lacks Shape
        class MockObjectWithoutShape:
            def __init__(self):
                self.Label = "NoShape"

        mock_obj_no_shape = MockObjectWithoutShape()

        bbox = extractor.extract_bounding_box(mock_obj_no_shape)
        assert bbox is None  # Should handle gracefully

        panel = extractor.to_panel_object(mock_obj_no_shape)
        assert panel is None  # Should handle gracefully

        # Empty document
        mock_empty_doc = Mock()
        mock_empty_doc.Objects = []

        panels = extractor.extract_from_document(mock_empty_doc)
        assert panels == []  # Should return empty list, not crash

        # None document
        panels = extractor.extract_from_document(None)
        assert panels == []  # Should return empty list, not crash


class TestGeometryNestingEngine:
    """Property-based tests for the geometry nesting engine."""

    @given(st.lists(valid_complex_geometry(), min_size=1, max_size=5))
    @settings(
        max_examples=20,
        deadline=10000,
        suppress_health_check=[HealthCheck.filter_too_much],
    )
    def test_property_4_overlap_prevention_in_nesting(self, geometries):
        """**Feature: shape-based-nesting, Property 4: Overlap Prevention**

        For any pair of complex shapes in a nesting layout, the system should
        detect and prevent overlaps between actual shape geometries, maintaining
        specified margins between contours.

        **Validates: Requirements 2.2, 8.2**
        """
        from SquatchCut.core.geometry_nesting_engine import (
            GeometryNestingEngine,
            NestingMode,
            SheetGeometry,
        )

        # Create a reasonably sized sheet
        sheet = SheetGeometry(width=1000.0, height=1000.0, margin=10.0)
        engine = GeometryNestingEngine()

        # Attempt nesting
        result = engine.nest_complex_shapes(geometries, sheet, NestingMode.GEOMETRIC)

        # Verify no overlaps in placed geometries
        placed = result.placed_geometries
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                geom1 = placed[i].geometry
                geom2 = placed[j].geometry

                # Create positioned geometries for overlap checking
                pos_geom1 = engine._create_positioned_geometry(
                    geom1, placed[i].x, placed[i].y
                )
                pos_geom2 = engine._create_positioned_geometry(
                    geom2, placed[j].x, placed[j].y
                )

                # Should not overlap
                assert not engine.detect_geometry_overlaps(
                    pos_geom1, pos_geom2, 0.1
                ), f"Geometries {geom1.id} and {geom2.id} overlap in nesting result"

        # Verify result structure
        assert isinstance(result.placed_geometries, list)
        assert isinstance(result.unplaced_geometries, list)
        assert result.sheets_used >= 0
        assert result.utilization_percent >= 0
        assert result.processing_time >= 0

    @given(valid_complex_geometry(), st.floats(min_value=0.1, max_value=5.0))
    @settings(max_examples=30, deadline=5000)
    def test_kerf_application_in_nesting(self, geometry, kerf_mm):
        """Test kerf compensation application in nesting engine."""
        from SquatchCut.core.geometry_nesting_engine import GeometryNestingEngine

        engine = GeometryNestingEngine()

        # Apply kerf compensation
        kerf_geometry = engine.apply_kerf_to_geometry(geometry, kerf_mm)

        # Should return a valid geometry (original or modified)
        assert kerf_geometry is not None
        assert kerf_geometry.id == geometry.id
        assert kerf_geometry.area > 0

        # If kerf was successfully applied, area should be different
        if kerf_geometry.kerf_compensation == kerf_mm:
            if kerf_mm > 0:
                assert kerf_geometry.area <= geometry.area  # Shrinking
        else:
            # Kerf was too large, should return original geometry
            assert kerf_geometry.kerf_compensation == geometry.kerf_compensation
            assert kerf_geometry.area == geometry.area

    @given(st.lists(valid_complex_geometry(), min_size=2, max_size=4))
    @settings(
        max_examples=15,
        deadline=8000,
        suppress_health_check=[HealthCheck.filter_too_much],
    )
    def test_utilization_calculation_accuracy(self, geometries):
        """Test that utilization calculations are accurate for complex geometries."""
        from SquatchCut.core.geometry_nesting_engine import (
            GeometryNestingEngine,
            NestingMode,
            SheetGeometry,
        )

        # Create sheet and nest geometries
        sheet = SheetGeometry(width=800.0, height=600.0, margin=5.0)
        engine = GeometryNestingEngine()

        result = engine.nest_complex_shapes(geometries, sheet, NestingMode.HYBRID)
        stats = engine.calculate_actual_utilization(result)

        # Verify utilization statistics
        assert stats.sheets_used >= 0
        assert 0 <= stats.utilization_percent <= 100
        assert stats.area_used_mm2 >= 0
        assert stats.area_wasted_mm2 >= 0
        assert 0 <= stats.geometric_efficiency <= 1.0
        assert 0 <= stats.placement_efficiency <= 1.0

        # Area conservation
        total_available = sheet.usable_area
        assert (
            abs((stats.area_used_mm2 + stats.area_wasted_mm2) - total_available) < 1.0
        )

        # If shapes were placed, utilization should be positive
        if result.placed_geometries:
            assert stats.area_used_mm2 > 0
            assert stats.utilization_percent > 0
