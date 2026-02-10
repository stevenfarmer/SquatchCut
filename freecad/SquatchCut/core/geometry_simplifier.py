"""Geometry simplification for performance optimization.

This module provides automatic simplification strategies for complex geometries
when performance thresholds are exceeded, enabling graceful degradation while
maintaining reasonable nesting accuracy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from SquatchCut.core.complex_geometry import (
    ComplexGeometry,
    ComplexityLevel,
    ExtractionMethod,
    GeometryType,
    create_rectangular_geometry,
)
from SquatchCut.core.performance_monitor import PerformanceMode


class SimplificationLevel(Enum):
    """Levels of geometry simplification."""

    NONE = "none"  # No simplification
    LIGHT = "light"  # Minor vertex reduction
    MODERATE = "moderate"  # Significant simplification
    AGGRESSIVE = "aggressive"  # Maximum simplification
    BOUNDING_BOX = "bounding_box"  # Fall back to bounding box


@dataclass
class SimplificationResult:
    """Result of geometry simplification operation."""

    original_geometry: ComplexGeometry
    simplified_geometry: ComplexGeometry
    simplification_level: SimplificationLevel
    vertex_reduction: int
    area_change_percent: float
    processing_time: float
    warnings: list[str]


class GeometrySimplifier:
    """Provides automatic geometry simplification for performance optimization."""

    def __init__(self, performance_mode: PerformanceMode = PerformanceMode.BALANCED):
        """Initialize simplifier with performance mode settings."""
        self.performance_mode = performance_mode
        self.simplification_thresholds = self._get_simplification_thresholds()

    def simplify_geometry(
        self,
        geometry: ComplexGeometry,
        target_level: Optional[SimplificationLevel] = None,
    ) -> SimplificationResult:
        """Simplify a complex geometry based on performance requirements.

        Args:
            geometry: The geometry to simplify
            target_level: Specific simplification level, or None for automatic

        Returns:
            SimplificationResult with original and simplified geometries
        """
        import time

        start_time = time.time()

        warnings = []

        # Determine simplification level
        if target_level is None:
            target_level = self._determine_simplification_level(geometry)

        # Apply simplification based on level
        if target_level == SimplificationLevel.NONE:
            simplified = geometry
        elif target_level == SimplificationLevel.LIGHT:
            simplified = self._light_simplification(geometry)
        elif target_level == SimplificationLevel.MODERATE:
            simplified = self._moderate_simplification(geometry)
        elif target_level == SimplificationLevel.AGGRESSIVE:
            simplified = self._aggressive_simplification(geometry)
        else:  # BOUNDING_BOX
            simplified = self._bounding_box_fallback(geometry)
            warnings.append("Fell back to bounding box due to extreme complexity")

        # Calculate metrics
        processing_time = time.time() - start_time
        vertex_reduction = len(geometry.contour_points) - len(simplified.contour_points)

        area_change = abs(simplified.area - geometry.area)
        area_change_percent = (
            (area_change / geometry.area * 100) if geometry.area > 0 else 0
        )

        if area_change_percent > 10.0:
            warnings.append(f"Significant area change: {area_change_percent:.1f}%")

        return SimplificationResult(
            original_geometry=geometry,
            simplified_geometry=simplified,
            simplification_level=target_level,
            vertex_reduction=vertex_reduction,
            area_change_percent=area_change_percent,
            processing_time=processing_time,
            warnings=warnings,
        )

    def simplify_geometry_list(
        self, geometries: list[ComplexGeometry], max_processing_time: float = 10.0
    ) -> list[SimplificationResult]:
        """Simplify a list of geometries with time budget management.

        Args:
            geometries: List of geometries to simplify
            max_processing_time: Maximum time to spend on simplification

        Returns:
            List of SimplificationResult objects
        """
        import time

        start_time = time.time()
        results = []

        # Sort by complexity (most complex first for early simplification)
        sorted_geometries = sorted(
            geometries, key=lambda g: self._calculate_complexity_score(g), reverse=True
        )

        time_per_geometry = max_processing_time / len(geometries) if geometries else 1.0

        for i, geometry in enumerate(sorted_geometries):
            elapsed = time.time() - start_time
            remaining_time = max_processing_time - elapsed

            if remaining_time <= 0:
                # Time budget exhausted, use aggressive simplification for remaining
                target_level = SimplificationLevel.AGGRESSIVE
            elif remaining_time < time_per_geometry:
                # Limited time remaining, use moderate simplification
                target_level = SimplificationLevel.MODERATE
            else:
                # Sufficient time, use automatic level determination
                target_level = None

            result = self.simplify_geometry(geometry, target_level)
            results.append(result)

            # Check if we're running out of time
            if time.time() - start_time > max_processing_time * 0.9:
                # Use bounding box for any remaining geometries
                for remaining_geom in sorted_geometries[i + 1 :]:
                    fallback_result = self.simplify_geometry(
                        remaining_geom, SimplificationLevel.BOUNDING_BOX
                    )
                    results.append(fallback_result)
                break

        return results

    def _determine_simplification_level(
        self, geometry: ComplexGeometry
    ) -> SimplificationLevel:
        """Automatically determine appropriate simplification level."""
        complexity_score = self._calculate_complexity_score(geometry)
        vertex_count = len(geometry.contour_points)

        # Apply performance mode thresholds
        thresholds = self.simplification_thresholds

        if complexity_score >= thresholds["bounding_box_threshold"]:
            return SimplificationLevel.BOUNDING_BOX
        elif complexity_score >= thresholds["aggressive_threshold"]:
            return SimplificationLevel.AGGRESSIVE
        elif complexity_score >= thresholds["moderate_threshold"]:
            return SimplificationLevel.MODERATE
        elif vertex_count > thresholds["light_vertex_threshold"]:
            return SimplificationLevel.LIGHT
        else:
            return SimplificationLevel.NONE

    def _calculate_complexity_score(self, geometry: ComplexGeometry) -> float:
        """Calculate a complexity score for a geometry."""
        vertex_count = len(geometry.contour_points)

        # Base score from vertex count
        vertex_score = min(vertex_count / 20.0, 5.0)

        # Area complexity (non-rectangular shapes are more complex)
        area_score = 0.0
        if geometry.geometry_type != GeometryType.RECTANGULAR:
            bbox_area = geometry.get_width() * geometry.get_height()
            if bbox_area > 0:
                area_ratio = geometry.area / bbox_area
                if area_ratio < 0.8:  # Significantly non-rectangular
                    area_score = 2.0
                elif area_ratio < 0.9:
                    area_score = 1.0

        # Complexity level contribution
        complexity_multiplier = {
            ComplexityLevel.LOW: 1.0,
            ComplexityLevel.MEDIUM: 1.5,
            ComplexityLevel.HIGH: 2.0,
            ComplexityLevel.EXTREME: 3.0,
        }.get(geometry.complexity_level, 1.0)

        return (vertex_score + area_score) * complexity_multiplier

    def _light_simplification(self, geometry: ComplexGeometry) -> ComplexGeometry:
        """Apply light simplification - minor vertex reduction."""
        if len(geometry.contour_points) <= 8:
            return geometry  # Already simple enough

        # Use Douglas-Peucker-like algorithm with small tolerance
        tolerance = (
            min(geometry.get_width(), geometry.get_height()) * 0.01
        )  # 1% tolerance
        simplified_points = self._simplify_contour(geometry.contour_points, tolerance)

        return self._create_simplified_geometry(geometry, simplified_points)

    def _moderate_simplification(self, geometry: ComplexGeometry) -> ComplexGeometry:
        """Apply moderate simplification - significant vertex reduction."""
        if len(geometry.contour_points) <= 6:
            return geometry

        # Use larger tolerance for more aggressive simplification
        tolerance = (
            min(geometry.get_width(), geometry.get_height()) * 0.05
        )  # 5% tolerance
        simplified_points = self._simplify_contour(geometry.contour_points, tolerance)

        # Ensure minimum vertex count
        if len(simplified_points) < 4:
            return self._bounding_box_fallback(geometry)

        return self._create_simplified_geometry(geometry, simplified_points)

    def _aggressive_simplification(self, geometry: ComplexGeometry) -> ComplexGeometry:
        """Apply aggressive simplification - maximum vertex reduction."""
        # For aggressive simplification, create a simplified polygon
        # that approximates the shape with minimal vertices

        if geometry.geometry_type == GeometryType.RECTANGULAR:
            return geometry  # Already optimal

        # Create octagon approximation for complex shapes
        center_x, center_y = geometry.get_centroid()
        width = geometry.get_width()
        height = geometry.get_height()

        # Use the larger dimension as radius for octagon
        radius = max(width, height) / 2.0

        # Create octagon points
        octagon_points = []
        for i in range(8):
            angle = 2 * math.pi * i / 8
            x = center_x + radius * math.cos(angle) * (width / max(width, height))
            y = center_y + radius * math.sin(angle) * (height / max(width, height))
            octagon_points.append((x, y))

        # Close the contour
        octagon_points.append(octagon_points[0])

        return self._create_simplified_geometry(geometry, octagon_points)

    def _bounding_box_fallback(self, geometry: ComplexGeometry) -> ComplexGeometry:
        """Fall back to rectangular bounding box."""
        return create_rectangular_geometry(
            geometry.id + "_simplified", geometry.get_width(), geometry.get_height()
        )

    def _simplify_contour(
        self, points: list[tuple[float, float]], tolerance: float
    ) -> list[tuple[float, float]]:
        """Simplify a contour using Douglas-Peucker algorithm."""
        if len(points) <= 3:
            return points

        # Find the point with maximum distance from line between first and last
        max_distance = 0.0
        max_index = 0

        first_point = points[0]
        last_point = points[-2]  # Exclude the closing point

        for i in range(1, len(points) - 2):
            distance = self._point_to_line_distance(points[i], first_point, last_point)
            if distance > max_distance:
                max_distance = distance
                max_index = i

        # If max distance is greater than tolerance, recursively simplify
        if max_distance > tolerance:
            # Recursively simplify the two segments
            left_segment = self._simplify_contour(points[: max_index + 1], tolerance)
            right_segment = self._simplify_contour(points[max_index:], tolerance)

            # Combine segments (remove duplicate point at junction)
            return left_segment[:-1] + right_segment
        else:
            # All points are within tolerance, return just endpoints
            return [first_point, last_point, points[-1]]  # Include closing point

    def _point_to_line_distance(
        self,
        point: tuple[float, float],
        line_start: tuple[float, float],
        line_end: tuple[float, float],
    ) -> float:
        """Calculate perpendicular distance from point to line."""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end

        # Handle degenerate case where line has zero length
        line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if line_length_sq < 1e-10:
            return math.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)

        # Calculate perpendicular distance
        numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        denominator = math.sqrt(line_length_sq)

        return numerator / denominator

    def _create_simplified_geometry(
        self, original: ComplexGeometry, simplified_points: list[tuple[float, float]]
    ) -> ComplexGeometry:
        """Create a new ComplexGeometry with simplified contour points."""
        # Calculate new bounding box
        if not simplified_points:
            return original

        min_x = min(p[0] for p in simplified_points)
        min_y = min(p[1] for p in simplified_points)
        max_x = max(p[0] for p in simplified_points)
        max_y = max(p[1] for p in simplified_points)
        new_bbox = (min_x, min_y, max_x, max_y)

        # Calculate new area using shoelace formula
        new_area = self._calculate_polygon_area(simplified_points)

        # Determine new complexity level based on vertex count
        vertex_count = len(simplified_points)
        if vertex_count <= 4:
            new_complexity = ComplexityLevel.LOW
        elif vertex_count <= 8:
            new_complexity = ComplexityLevel.MEDIUM
        else:
            new_complexity = ComplexityLevel.HIGH

        return ComplexGeometry(
            id=original.id,
            contour_points=simplified_points,
            bounding_box=new_bbox,
            area=new_area,
            complexity_level=new_complexity,
            rotation_allowed=original.rotation_allowed,
            kerf_compensation=original.kerf_compensation,
            geometry_type=(
                GeometryType.COMPLEX if vertex_count > 4 else GeometryType.RECTANGULAR
            ),
            extraction_method=ExtractionMethod.CONTOUR,
        )

    def _calculate_polygon_area(self, points: list[tuple[float, float]]) -> float:
        """Calculate polygon area using shoelace formula."""
        if len(points) < 3:
            return 0.0

        # Remove duplicate closing point if present
        if len(points) > 3 and points[0] == points[-1]:
            points = points[:-1]

        if len(points) < 3:
            return 0.0

        area = 0.0
        n = len(points)

        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]

        calculated_area = abs(area) / 2.0

        # Ensure minimum area for valid geometries
        if calculated_area < 1.0:
            # Calculate bounding box area as fallback
            if points:
                min_x = min(p[0] for p in points)
                max_x = max(p[0] for p in points)
                min_y = min(p[1] for p in points)
                max_y = max(p[1] for p in points)
                bbox_area = (max_x - min_x) * (max_y - min_y)
                return max(
                    calculated_area, bbox_area * 0.5
                )  # At least half of bounding box

        return calculated_area

    def _get_simplification_thresholds(self) -> dict:
        """Get simplification thresholds based on performance mode."""
        if self.performance_mode == PerformanceMode.FAST:
            return {
                "light_vertex_threshold": 8,
                "moderate_threshold": 3.0,
                "aggressive_threshold": 5.0,
                "bounding_box_threshold": 7.0,
            }
        elif self.performance_mode == PerformanceMode.BALANCED:
            return {
                "light_vertex_threshold": 15,
                "moderate_threshold": 5.0,
                "aggressive_threshold": 7.0,
                "bounding_box_threshold": 9.0,
            }
        else:  # PRECISE
            return {
                "light_vertex_threshold": 25,
                "moderate_threshold": 7.0,
                "aggressive_threshold": 9.0,
                "bounding_box_threshold": 12.0,
            }


def auto_simplify_for_performance(
    geometries: list[ComplexGeometry],
    performance_mode: PerformanceMode = PerformanceMode.BALANCED,
    max_processing_time: float = 10.0,
) -> list[ComplexGeometry]:
    """Convenience function to automatically simplify geometries for performance.

    Args:
        geometries: List of geometries to simplify
        performance_mode: Performance mode to use for simplification
        max_processing_time: Maximum time to spend on simplification

    Returns:
        List of simplified geometries
    """
    simplifier = GeometrySimplifier(performance_mode)
    results = simplifier.simplify_geometry_list(geometries, max_processing_time)
    return [result.simplified_geometry for result in results]
