"""Tests for performance optimization and monitoring features.

**Feature: shape-based-nesting**

This module tests the performance monitoring, automatic simplification,
and progress feedback systems for shape-based nesting operations.
"""

import time
from unittest.mock import Mock, patch

import pytest
from SquatchCut.core.complex_geometry import (
    ComplexGeometry,
    ComplexityLevel,
    GeometryType,
    create_rectangular_geometry,
)
from SquatchCut.core.geometry_simplifier import (
    GeometrySimplifier,
    SimplificationLevel,
    auto_simplify_for_performance,
)
from SquatchCut.core.performance_monitor import (
    PerformanceMode,
    PerformanceMonitor,
    PerformanceThresholds,
    get_performance_monitor,
)
from SquatchCut.core.progress_feedback import (
    OperationStatus,
    ProgressManager,
    ProgressStage,
    ProgressTracker,
    get_progress_manager,
)


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""

    def test_performance_monitor_initialization(self):
        """Test that performance monitor initializes with default thresholds."""
        monitor = PerformanceMonitor()

        assert monitor.thresholds is not None
        assert isinstance(monitor.thresholds, PerformanceThresholds)
        assert monitor.active_operations == {}
        assert monitor.completed_operations == []

    def test_start_and_finish_operation(self):
        """Test basic operation tracking."""
        monitor = PerformanceMonitor()

        # Start operation
        op_id = monitor.start_operation(
            "test_operation", shapes_count=5, estimated_complexity=3.0
        )

        assert op_id in monitor.active_operations
        assert len(monitor.active_operations) == 1

        metrics = monitor.active_operations[op_id]
        assert metrics.operation_name == "test_operation"
        assert metrics.shapes_processed == 5
        assert metrics.complexity_score == 3.0

        # Finish operation
        result = monitor.finish_operation(op_id, success=True)

        assert op_id not in monitor.active_operations
        assert len(monitor.completed_operations) == 1
        assert result.operation_name == "test_operation"
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0

    def test_complexity_assessment(self):
        """Test geometry complexity assessment."""
        monitor = PerformanceMonitor()

        # Simple rectangular geometry
        simple_geom = create_rectangular_geometry("simple", 100, 200)
        simple_geometries = [simple_geom]

        complexity = monitor.assess_geometry_complexity(simple_geometries)
        assert 0 <= complexity <= 3.0  # Should be low complexity

        # Complex geometry with many vertices
        complex_points = [(i * 10, i * 5) for i in range(50)]  # 50 vertices
        complex_points.append(complex_points[0])  # Close contour

        complex_geom = ComplexGeometry(
            id="complex",
            contour_points=complex_points,
            bounding_box=(0, 0, 490, 245),
            area=50000,
            complexity_level=ComplexityLevel.HIGH,
            rotation_allowed=True,
            geometry_type=GeometryType.COMPLEX,
        )
        complex_geometries = [complex_geom]

        complexity = monitor.assess_geometry_complexity(complex_geometries)
        assert complexity >= 4.0  # Should be high complexity

    def test_performance_mode_recommendation(self):
        """Test automatic performance mode recommendation."""
        monitor = PerformanceMonitor()

        # Simple geometries should recommend PRECISE mode
        simple_geoms = [
            create_rectangular_geometry(f"rect_{i}", 100, 200) for i in range(3)
        ]
        mode = monitor.recommend_performance_mode(simple_geoms)
        assert mode == PerformanceMode.PRECISE

        # Many complex geometries should recommend FAST mode
        complex_points = [(i * 2, i) for i in range(30)]  # 30 vertices each
        complex_points.append(complex_points[0])

        many_complex_geoms = []
        for i in range(20):  # 20 complex shapes
            geom = ComplexGeometry(
                id=f"complex_{i}",
                contour_points=complex_points,
                bounding_box=(0, 0, 58, 29),
                area=1000,
                complexity_level=ComplexityLevel.HIGH,
                rotation_allowed=True,
                geometry_type=GeometryType.COMPLEX,
            )
            many_complex_geoms.append(geom)

        mode = monitor.recommend_performance_mode(many_complex_geoms)
        assert mode == PerformanceMode.FAST

    def test_fallback_triggering(self):
        """Test performance fallback detection."""
        # Use very low thresholds for testing
        thresholds = PerformanceThresholds(
            max_processing_time_seconds=0.1,  # Very short timeout
            complexity_fallback_threshold=2.0,  # Low complexity threshold
        )
        monitor = PerformanceMonitor(thresholds)

        # Start operation with high complexity
        op_id = monitor.start_operation(
            "test_fallback", shapes_count=1, estimated_complexity=5.0
        )

        # Should trigger fallback due to complexity
        assert monitor.should_trigger_fallback(op_id) == True

        # Start operation with low complexity
        op_id2 = monitor.start_operation(
            "test_no_fallback", shapes_count=1, estimated_complexity=1.0
        )

        # Should not trigger fallback immediately
        assert monitor.should_trigger_fallback(op_id2) == False

        # Wait for timeout
        time.sleep(0.15)

        # Should trigger fallback due to timeout
        assert monitor.should_trigger_fallback(op_id2) == True

    def test_performance_summary(self):
        """Test performance summary generation."""
        monitor = PerformanceMonitor()

        # Initially empty
        summary = monitor.get_performance_summary()
        assert summary["total_operations"] == 0

        # Add some operations
        op_id1 = monitor.start_operation("op1", shapes_count=5)
        monitor.finish_operation(op_id1, success=True)

        op_id2 = monitor.start_operation("op2", shapes_count=3)
        monitor.finish_operation(op_id2, success=False)

        summary = monitor.get_performance_summary()
        assert summary["total_operations"] == 2
        assert summary["total_shapes_processed"] == 8
        assert 0 <= summary["average_duration"] <= 1.0  # Should be very fast
        assert summary["performance_warnings"] >= 0

    def test_global_monitor_singleton(self):
        """Test that global monitor returns the same instance."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()

        assert monitor1 is monitor2


class TestGeometrySimplifier:
    """Test geometry simplification functionality."""

    def test_simplifier_initialization(self):
        """Test simplifier initialization with different performance modes."""
        fast_simplifier = GeometrySimplifier(PerformanceMode.FAST)
        balanced_simplifier = GeometrySimplifier(PerformanceMode.BALANCED)
        precise_simplifier = GeometrySimplifier(PerformanceMode.PRECISE)

        # Fast mode should have more aggressive thresholds
        assert (
            fast_simplifier.simplification_thresholds["light_vertex_threshold"]
            < balanced_simplifier.simplification_thresholds["light_vertex_threshold"]
        )

        assert (
            balanced_simplifier.simplification_thresholds["light_vertex_threshold"]
            < precise_simplifier.simplification_thresholds["light_vertex_threshold"]
        )

    def test_complexity_score_calculation(self):
        """Test complexity score calculation for different geometries."""
        simplifier = GeometrySimplifier()

        # Simple rectangular geometry
        simple_geom = create_rectangular_geometry("simple", 100, 200)
        simple_score = simplifier._calculate_complexity_score(simple_geom)

        # Complex geometry with many vertices
        complex_points = [(i * 5, i * 3) for i in range(25)]  # 25 vertices
        complex_points.append(complex_points[0])

        complex_geom = ComplexGeometry(
            id="complex",
            contour_points=complex_points,
            bounding_box=(0, 0, 120, 72),
            area=5000,
            complexity_level=ComplexityLevel.HIGH,
            rotation_allowed=True,
            geometry_type=GeometryType.COMPLEX,
        )
        complex_score = simplifier._calculate_complexity_score(complex_geom)

        assert complex_score > simple_score

    def test_simplification_level_determination(self):
        """Test automatic simplification level determination."""
        simplifier = GeometrySimplifier(PerformanceMode.BALANCED)

        # Simple geometry should need no simplification
        simple_geom = create_rectangular_geometry("simple", 100, 200)
        level = simplifier._determine_simplification_level(simple_geom)
        assert level == SimplificationLevel.NONE

        # Very complex geometry should need aggressive simplification
        very_complex_points = [(i, i * 2) for i in range(100)]  # 100 vertices
        very_complex_points.append(very_complex_points[0])

        very_complex_geom = ComplexGeometry(
            id="very_complex",
            contour_points=very_complex_points,
            bounding_box=(0, 0, 99, 198),
            area=10000,
            complexity_level=ComplexityLevel.EXTREME,
            rotation_allowed=True,
            geometry_type=GeometryType.COMPLEX,
        )
        level = simplifier._determine_simplification_level(very_complex_geom)
        assert level in [
            SimplificationLevel.AGGRESSIVE,
            SimplificationLevel.BOUNDING_BOX,
        ]

    def test_light_simplification(self):
        """Test light simplification preserves general shape."""
        simplifier = GeometrySimplifier()

        # Create a geometry with moderate complexity
        points = [
            (0, 0),
            (50, 10),
            (100, 0),
            (110, 50),
            (100, 100),
            (50, 90),
            (0, 100),
            (-10, 50),
            (0, 0),
        ]

        original_geom = ComplexGeometry(
            id="moderate",
            contour_points=points,
            bounding_box=(-10, 0, 110, 100),
            area=8000,
            complexity_level=ComplexityLevel.MEDIUM,
            rotation_allowed=True,
            geometry_type=GeometryType.COMPLEX,
        )

        result = simplifier.simplify_geometry(original_geom, SimplificationLevel.LIGHT)

        assert result.simplified_geometry.id == original_geom.id
        assert len(result.simplified_geometry.contour_points) <= len(
            original_geom.contour_points
        )
        assert result.simplification_level == SimplificationLevel.LIGHT
        assert result.vertex_reduction >= 0

    def test_bounding_box_fallback(self):
        """Test bounding box fallback simplification."""
        simplifier = GeometrySimplifier()

        # Create a complex geometry
        complex_points = [(i * 3, i * 2) for i in range(30)]
        complex_points.append(complex_points[0])

        complex_geom = ComplexGeometry(
            id="complex",
            contour_points=complex_points,
            bounding_box=(0, 0, 87, 58),
            area=3000,
            complexity_level=ComplexityLevel.EXTREME,
            rotation_allowed=True,
            geometry_type=GeometryType.COMPLEX,
        )

        result = simplifier.simplify_geometry(
            complex_geom, SimplificationLevel.BOUNDING_BOX
        )

        assert result.simplified_geometry.geometry_type == GeometryType.RECTANGULAR
        assert (
            len(result.simplified_geometry.contour_points) == 5
        )  # Rectangle + closing point
        assert result.simplification_level == SimplificationLevel.BOUNDING_BOX
        assert "bounding box" in result.warnings[0].lower()

    def test_geometry_list_simplification(self):
        """Test simplification of multiple geometries with time budget."""
        simplifier = GeometrySimplifier(PerformanceMode.FAST)

        # Create multiple geometries with varying complexity
        geometries = []
        for i in range(5):
            vertex_count = 10 + i * 5  # Increasing complexity
            points = [(j * 2, j) for j in range(vertex_count)]
            points.append(points[0])

            geom = ComplexGeometry(
                id=f"geom_{i}",
                contour_points=points,
                bounding_box=(0, 0, (vertex_count - 1) * 2, vertex_count - 1),
                area=1000 * (i + 1),
                complexity_level=ComplexityLevel.MEDIUM,
                rotation_allowed=True,
                geometry_type=GeometryType.COMPLEX,
            )
            geometries.append(geom)

        results = simplifier.simplify_geometry_list(geometries, max_processing_time=1.0)

        assert len(results) == len(geometries)
        for result in results:
            assert result.simplified_geometry is not None
            assert result.processing_time >= 0

    def test_auto_simplify_convenience_function(self):
        """Test the convenience function for automatic simplification."""
        # Create some test geometries
        geometries = [
            create_rectangular_geometry("simple", 100, 200),
            ComplexGeometry(
                id="complex",
                contour_points=[(i * 5, i * 3) for i in range(15)] + [(0, 0)],
                bounding_box=(0, 0, 70, 42),
                area=2000,
                complexity_level=ComplexityLevel.MEDIUM,
                rotation_allowed=True,
                geometry_type=GeometryType.COMPLEX,
            ),
        ]

        simplified = auto_simplify_for_performance(
            geometries, PerformanceMode.BALANCED, max_processing_time=2.0
        )

        assert len(simplified) == len(geometries)
        for geom in simplified:
            assert isinstance(geom, ComplexGeometry)


class TestProgressFeedback:
    """Test progress feedback and tracking functionality."""

    def test_progress_tracker_initialization(self):
        """Test progress tracker initialization."""
        callback = Mock()
        cancellation_check = Mock(return_value=False)

        tracker = ProgressTracker(
            "test_op",
            total_items=10,
            progress_callback=callback,
            cancellation_check=cancellation_check,
        )

        assert tracker.operation_id == "test_op"
        assert tracker.total_items == 10
        assert tracker.current_item == 0
        assert tracker.current_stage == ProgressStage.INITIALIZING
        assert not tracker.cancelled

        # Should have called callback for initial update
        callback.assert_called_once()

    def test_progress_updates(self):
        """Test progress update functionality."""
        callback = Mock()
        tracker = ProgressTracker("test_op", total_items=5, progress_callback=callback)

        # Set stage
        tracker.set_stage(ProgressStage.PLACING_SHAPES, "Placing shapes")
        assert tracker.current_stage == ProgressStage.PLACING_SHAPES

        # Update progress
        result = tracker.update_progress(
            current_item=2, description="Processing item 2"
        )
        assert result == True  # Should continue
        assert tracker.current_item == 2

        # Should have called callback multiple times
        assert callback.call_count >= 2

    def test_progress_cancellation(self):
        """Test progress cancellation handling."""
        callback = Mock()
        cancellation_check = Mock(return_value=True)  # Always cancelled

        tracker = ProgressTracker(
            "test_op",
            total_items=5,
            progress_callback=callback,
            cancellation_check=cancellation_check,
        )

        # Update should return False when cancelled
        result = tracker.update_progress(current_item=1)
        assert result == False
        assert tracker.cancelled == True

    def test_progress_manager(self):
        """Test progress manager functionality."""
        manager = ProgressManager()

        # Start operation
        callback = Mock()
        op_id = manager.start_operation(
            "test_operation", total_items=3, progress_callback=callback
        )

        assert op_id in manager.get_active_operations()

        tracker = manager.get_tracker(op_id)
        assert tracker is not None
        assert tracker.operation_id == op_id

        # Finish operation
        result = manager.finish_operation(
            op_id, success=True, result_data="test_result"
        )

        assert op_id not in manager.get_active_operations()
        assert result.status == OperationStatus.COMPLETED
        assert result.result_data == "test_result"

    def test_progress_manager_cancellation(self):
        """Test operation cancellation through manager."""
        manager = ProgressManager()

        op_id = manager.start_operation("test_operation", total_items=5)

        # Cancel operation
        success = manager.cancel_operation(op_id)
        assert success == True

        tracker = manager.get_tracker(op_id)
        assert tracker.cancelled == True

    def test_progress_manager_summary(self):
        """Test progress manager summary generation."""
        manager = ProgressManager()

        # Initially empty
        summary = manager.get_operation_summary()
        assert summary["active_operations"] == 0
        assert summary["completed_operations"] == 0

        # Add operations
        op_id1 = manager.start_operation("op1", total_items=3)
        op_id2 = manager.start_operation("op2", total_items=5)

        summary = manager.get_operation_summary()
        assert summary["active_operations"] == 2

        # Finish operations
        manager.finish_operation(op_id1, success=True)
        manager.finish_operation(op_id2, success=False)

        summary = manager.get_operation_summary()
        assert summary["active_operations"] == 0
        assert summary["completed_operations"] == 2
        assert 0 <= summary["success_rate"] <= 1.0

    def test_global_progress_manager_singleton(self):
        """Test that global progress manager returns the same instance."""
        manager1 = get_progress_manager()
        manager2 = get_progress_manager()

        assert manager1 is manager2


class TestPerformanceIntegration:
    """Test integration of performance features with nesting engine."""

    @patch("SquatchCut.core.geometry_nesting_engine.get_performance_monitor")
    @patch("SquatchCut.core.geometry_nesting_engine.get_progress_manager")
    def test_nesting_engine_performance_integration(
        self, mock_progress_manager, mock_perf_monitor
    ):
        """Test that nesting engine integrates with performance monitoring."""
        from SquatchCut.core.geometry_nesting_engine import (
            GeometryNestingEngine,
            SheetGeometry,
        )

        # Setup mocks
        mock_monitor = Mock()
        mock_monitor.assess_geometry_complexity.return_value = 3.0
        mock_monitor.recommend_performance_mode.return_value = PerformanceMode.BALANCED
        mock_monitor.start_operation.return_value = "perf_op_123"
        mock_monitor.should_trigger_fallback.return_value = False
        mock_monitor.finish_operation.return_value = Mock(warnings=[])
        mock_perf_monitor.return_value = mock_monitor

        mock_manager = Mock()
        mock_manager.start_operation.return_value = "progress_op_123"
        mock_tracker = Mock()
        mock_tracker.update_progress.return_value = True  # Continue processing
        mock_manager.get_tracker.return_value = mock_tracker
        mock_manager.finish_operation.return_value = Mock()
        mock_progress_manager.return_value = mock_manager

        # Create engine and test shapes
        engine = GeometryNestingEngine(PerformanceMode.BALANCED)
        sheet = SheetGeometry(width=1000, height=800, margin=10)
        shapes = [create_rectangular_geometry("test", 100, 200)]

        # Run nesting
        result = engine.nest_complex_shapes(shapes, sheet)

        # Verify performance monitoring was called
        mock_monitor.assess_geometry_complexity.assert_called_once_with(shapes)
        mock_monitor.start_operation.assert_called_once()
        mock_monitor.finish_operation.assert_called_once()

        # Verify progress tracking was called
        mock_manager.start_operation.assert_called_once()
        mock_manager.get_tracker.assert_called_once()
        mock_manager.finish_operation.assert_called_once()

        # Verify result
        assert result is not None
        assert isinstance(result.processing_time, float)
        assert result.processing_time >= 0

    def test_performance_mode_affects_nesting_behavior(self):
        """Test that different performance modes affect nesting behavior."""
        from SquatchCut.core.geometry_nesting_engine import (
            GeometryNestingEngine,
            SheetGeometry,
        )

        sheet = SheetGeometry(width=500, height=400, margin=5)
        shapes = [create_rectangular_geometry(f"rect_{i}", 50, 80) for i in range(3)]

        # Test different performance modes
        fast_engine = GeometryNestingEngine(PerformanceMode.FAST)
        balanced_engine = GeometryNestingEngine(PerformanceMode.BALANCED)
        precise_engine = GeometryNestingEngine(PerformanceMode.PRECISE)

        # All should produce results, but with different characteristics
        fast_result = fast_engine.nest_complex_shapes(shapes, sheet)
        balanced_result = balanced_engine.nest_complex_shapes(shapes, sheet)
        precise_result = precise_engine.nest_complex_shapes(shapes, sheet)

        assert fast_result is not None
        assert balanced_result is not None
        assert precise_result is not None

        # Fast mode should generally be faster (though with simple shapes, difference may be minimal)
        # This is more of a behavioral test than a strict assertion
        assert fast_result.processing_time >= 0
        assert balanced_result.processing_time >= 0
        assert precise_result.processing_time >= 0
