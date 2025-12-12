"""Performance monitoring and optimization for shape-based nesting.

This module provides performance tracking, complexity assessment, and automatic
optimization strategies for complex geometry nesting operations.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from SquatchCut.core import logger


class PerformanceMode(Enum):
    """Performance vs accuracy trade-off modes."""

    FAST = "fast"  # Prioritize speed, use simplified algorithms
    BALANCED = "balanced"  # Balance speed and accuracy
    PRECISE = "precise"  # Prioritize accuracy, allow longer processing


class ComplexityLevel(Enum):
    """Geometry complexity assessment levels."""

    LOW = 1  # Simple rectangles, basic shapes
    MEDIUM = 2  # Moderate complexity, some curves
    HIGH = 3  # Complex shapes, many vertices
    EXTREME = 4  # Very complex, performance-critical


@dataclass
class PerformanceMetrics:
    """Performance metrics for a nesting operation."""

    operation_name: str
    start_time: float
    end_time: float | None = None
    duration_seconds: float | None = None
    memory_usage_mb: float | None = None
    shapes_processed: int = 0
    complexity_score: float = 0.0
    mode_used: PerformanceMode = PerformanceMode.BALANCED
    fallback_triggered: bool = False
    warnings: list[str] = field(default_factory=list)

    def finish(self) -> None:
        """Mark the operation as finished and calculate duration."""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration_seconds = self.end_time - self.start_time

    def add_warning(self, message: str) -> None:
        """Add a performance warning."""
        self.warnings.append(message)
        logger.warning(f"[Performance] {self.operation_name}: {message}")


@dataclass
class PerformanceThresholds:
    """Configurable performance thresholds for automatic optimization."""

    max_processing_time_seconds: float = 30.0
    max_shapes_for_precise_mode: int = 50
    max_vertices_per_shape: int = 100
    complexity_fallback_threshold: float = 8.0
    memory_limit_mb: float = 512.0

    # Automatic mode switching thresholds
    fast_mode_vertex_limit: int = 20
    balanced_mode_vertex_limit: int = 50

    def should_use_fast_mode(self, total_vertices: int, shape_count: int) -> bool:
        """Determine if fast mode should be used based on complexity."""
        return (
            total_vertices > self.fast_mode_vertex_limit * shape_count
            or shape_count > self.max_shapes_for_precise_mode
        )

    def should_use_balanced_mode(self, total_vertices: int, shape_count: int) -> bool:
        """Determine if balanced mode should be used."""
        return (
            total_vertices > self.balanced_mode_vertex_limit * shape_count
            and not self.should_use_fast_mode(total_vertices, shape_count)
        )


class PerformanceMonitor:
    """Monitor and optimize performance for shape-based nesting operations."""

    def __init__(self, thresholds: PerformanceThresholds | None = None):
        """Initialize performance monitor with configurable thresholds."""
        self.thresholds = thresholds or PerformanceThresholds()
        self.active_operations: dict[str, PerformanceMetrics] = {}
        self.completed_operations: list[PerformanceMetrics] = []
        self._operation_counter = 0

    def start_operation(
        self,
        operation_name: str,
        shapes_count: int = 0,
        estimated_complexity: float = 0.0,
    ) -> str:
        """Start monitoring a performance-critical operation.

        Args:
            operation_name: Human-readable name for the operation
            shapes_count: Number of shapes being processed
            estimated_complexity: Estimated complexity score (0-10)

        Returns:
            Operation ID for tracking
        """
        self._operation_counter += 1
        operation_id = f"{operation_name}_{self._operation_counter}"

        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            shapes_processed=shapes_count,
            complexity_score=estimated_complexity,
        )

        self.active_operations[operation_id] = metrics

        logger.info(
            f"[Performance] Started {operation_name} "
            f"(shapes: {shapes_count}, complexity: {estimated_complexity:.1f})"
        )

        return operation_id

    def finish_operation(
        self,
        operation_id: str,
        success: bool = True,
        additional_metrics: dict[str, Any] | None = None,
    ) -> PerformanceMetrics:
        """Finish monitoring an operation and return metrics.

        Args:
            operation_id: ID returned by start_operation
            success: Whether the operation completed successfully
            additional_metrics: Additional metrics to record

        Returns:
            Complete performance metrics
        """
        if operation_id not in self.active_operations:
            logger.warning(f"[Performance] Unknown operation ID: {operation_id}")
            # Create a dummy metrics object
            return PerformanceMetrics(
                operation_name="unknown",
                start_time=time.time(),
                end_time=time.time(),
                duration_seconds=0.0,
            )

        metrics = self.active_operations.pop(operation_id)
        metrics.finish()

        # Add any additional metrics
        if additional_metrics:
            for key, value in additional_metrics.items():
                setattr(metrics, key, value)

        # Check for performance issues
        self._analyze_performance(metrics, success)

        self.completed_operations.append(metrics)

        logger.info(
            f"[Performance] Finished {metrics.operation_name} "
            f"in {metrics.duration_seconds:.2f}s "
            f"({'success' if success else 'failed'})"
        )

        return metrics

    def add_warning(self, operation_id: str, message: str) -> None:
        """Add a warning to an active operation."""
        if operation_id in self.active_operations:
            self.active_operations[operation_id].add_warning(message)

    def assess_geometry_complexity(self, geometries: list[Any]) -> float:
        """Assess the complexity of a list of geometries.

        Args:
            geometries: List of ComplexGeometry objects or similar

        Returns:
            Complexity score from 0.0 (simple) to 10.0 (extremely complex)
        """
        if not geometries:
            return 0.0

        total_complexity = 0.0

        for geom in geometries:
            # Base complexity from vertex count
            if hasattr(geom, "contour_points"):
                vertex_count = len(geom.contour_points)
                vertex_complexity = min(vertex_count / 20.0, 5.0)  # Cap at 5.0
            else:
                vertex_complexity = 1.0  # Assume simple if no contour data

            # Additional complexity factors
            area_complexity = 0.0
            if (
                hasattr(geom, "area")
                and hasattr(geom, "get_width")
                and hasattr(geom, "get_height")
            ):
                # Non-rectangular shapes add complexity
                bbox_area = geom.get_width() * geom.get_height()
                if bbox_area > 0:
                    area_ratio = geom.area / bbox_area
                    if area_ratio < 0.8:  # Significantly non-rectangular
                        area_complexity = 1.0

            # Rotation complexity
            rotation_complexity = 0.0
            if hasattr(geom, "rotation_allowed") and geom.rotation_allowed:
                rotation_complexity = 0.5

            geom_complexity = vertex_complexity + area_complexity + rotation_complexity
            total_complexity += geom_complexity

        # Average complexity, but weight by count
        avg_complexity = total_complexity / len(geometries)
        count_factor = min(len(geometries) / 10.0, 2.0)  # More shapes = more complex

        final_complexity = min(avg_complexity + count_factor, 10.0)
        return final_complexity

    def recommend_performance_mode(self, geometries: list[Any]) -> PerformanceMode:
        """Recommend optimal performance mode based on geometry complexity.

        Args:
            geometries: List of geometries to analyze

        Returns:
            Recommended performance mode
        """
        shape_count = len(geometries)

        # Calculate total vertices
        total_vertices = 0
        for geom in geometries:
            if hasattr(geom, "contour_points"):
                total_vertices += len(geom.contour_points)
            else:
                total_vertices += 4  # Assume rectangle

        # Apply threshold logic
        if self.thresholds.should_use_fast_mode(total_vertices, shape_count):
            return PerformanceMode.FAST
        elif self.thresholds.should_use_balanced_mode(total_vertices, shape_count):
            return PerformanceMode.BALANCED
        else:
            return PerformanceMode.PRECISE

    def should_trigger_fallback(self, operation_id: str) -> bool:
        """Check if an operation should trigger fallback due to performance.

        Args:
            operation_id: Active operation to check

        Returns:
            True if fallback should be triggered
        """
        if operation_id not in self.active_operations:
            return False

        metrics = self.active_operations[operation_id]
        current_time = time.time()
        elapsed = current_time - metrics.start_time

        # Check time threshold
        if elapsed > self.thresholds.max_processing_time_seconds:
            self.add_warning(
                operation_id,
                f"Processing time exceeded {self.thresholds.max_processing_time_seconds}s",
            )
            return True

        # Check complexity threshold
        if metrics.complexity_score > self.thresholds.complexity_fallback_threshold:
            self.add_warning(
                operation_id,
                f"Complexity score {metrics.complexity_score:.1f} exceeds threshold",
            )
            return True

        return False

    def get_performance_summary(self) -> dict[str, Any]:
        """Get a summary of performance metrics.

        Returns:
            Dictionary with performance statistics
        """
        if not self.completed_operations:
            return {
                "total_operations": 0,
                "average_duration": 0.0,
                "success_rate": 0.0,
                "fallback_rate": 0.0,
            }

        total_ops = len(self.completed_operations)
        total_duration = sum(
            op.duration_seconds or 0.0 for op in self.completed_operations
        )
        fallback_count = sum(
            1 for op in self.completed_operations if op.fallback_triggered
        )

        return {
            "total_operations": total_ops,
            "average_duration": total_duration / total_ops,
            "fallback_rate": fallback_count / total_ops,
            "total_shapes_processed": sum(
                op.shapes_processed for op in self.completed_operations
            ),
            "average_complexity": sum(
                op.complexity_score for op in self.completed_operations
            )
            / total_ops,
            "performance_warnings": sum(
                len(op.warnings) for op in self.completed_operations
            ),
        }

    def _analyze_performance(self, metrics: PerformanceMetrics, success: bool) -> None:
        """Analyze completed operation performance and add warnings."""
        if not success:
            metrics.add_warning("Operation failed")
            return

        duration = metrics.duration_seconds or 0.0

        # Check for slow operations
        if duration > self.thresholds.max_processing_time_seconds:
            metrics.add_warning(f"Slow operation: {duration:.1f}s")

        # Check complexity vs performance
        if metrics.complexity_score > 5.0 and duration > 10.0:
            metrics.add_warning("High complexity with slow performance")

        # Check for excessive shape count
        if metrics.shapes_processed > self.thresholds.max_shapes_for_precise_mode:
            metrics.add_warning(f"Large shape count: {metrics.shapes_processed}")


# Global performance monitor instance
_global_monitor: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def monitor_performance(
    operation_name: str, shapes_count: int = 0, estimated_complexity: float = 0.0
):
    """Decorator for monitoring function performance.

    Usage:
        @monitor_performance("shape_extraction", shapes_count=10, estimated_complexity=3.5)
        def extract_shapes(shapes):
            # ... implementation
            return result
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            operation_id = monitor.start_operation(
                operation_name, shapes_count, estimated_complexity
            )

            try:
                result = func(*args, **kwargs)
                monitor.finish_operation(operation_id, success=True)
                return result
            except Exception:
                monitor.finish_operation(operation_id, success=False)
                raise

        return wrapper

    return decorator
