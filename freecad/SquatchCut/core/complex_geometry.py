"""Complex geometry data models for shape-based nesting.

This module provides data structures and algorithms for handling non-rectangular
shapes in SquatchCut's nesting system. It supports contour-based geometry
representation, rotation, kerf compensation, and overlap detection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union

# Type aliases for clarity
Point2D = Tuple[float, float]
BoundingBox = Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)


class GeometryType(Enum):
    """Classification of geometry complexity."""

    RECTANGULAR = "rectangular"
    CURVED = "curved"
    COMPLEX = "complex"


class ComplexityLevel(Enum):
    """Performance-oriented complexity classification."""

    LOW = "low"  # Simple rectangles, basic shapes
    MEDIUM = "medium"  # Moderate curves, simple polygons
    HIGH = "high"  # Complex curves, many vertices
    EXTREME = "extreme"  # Very complex geometry requiring fallback


class ExtractionMethod(Enum):
    """Method used to extract geometry from FreeCAD objects."""

    BOUNDING_BOX = "bounding_box"  # Simple rectangular approximation
    CONTOUR = "contour"  # Full contour extraction
    HYBRID = "hybrid"  # Contour with bounding box fallback


@dataclass
class ComplexGeometry:
    """Represents a complex, potentially non-rectangular shape for nesting.

    This class handles the geometric representation of parts that go beyond
    simple rectangles, supporting contour-based nesting, rotation, and
    kerf compensation while maintaining performance through complexity assessment.
    """

    id: str
    contour_points: List[Point2D]
    bounding_box: BoundingBox
    area: float
    complexity_level: ComplexityLevel
    rotation_allowed: bool
    kerf_compensation: Optional[float] = None
    geometry_type: GeometryType = GeometryType.COMPLEX
    extraction_method: ExtractionMethod = ExtractionMethod.CONTOUR

    def __post_init__(self):
        """Validate geometry data after initialization."""
        if not self.contour_points:
            raise ValueError(f"ComplexGeometry {self.id} must have contour points")

        if len(self.contour_points) < 3:
            raise ValueError(
                f"ComplexGeometry {self.id} must have at least 3 contour points"
            )

        if self.area <= 0:
            raise ValueError(f"ComplexGeometry {self.id} must have positive area")

        # Ensure contour is closed (first and last points should be the same or very close)
        if len(self.contour_points) > 0:
            first = self.contour_points[0]
            last = self.contour_points[-1]
            distance = math.sqrt((first[0] - last[0]) ** 2 + (first[1] - last[1]) ** 2)
            if distance > 0.001:  # 0.001mm tolerance
                # Close the contour by adding the first point at the end
                self.contour_points.append(first)

    @classmethod
    def from_rectangle(
        cls,
        id: str,
        width: float,
        height: float,
        x_offset: float = 0.0,
        y_offset: float = 0.0,
        rotation_allowed: bool = True,
    ) -> "ComplexGeometry":
        """Create ComplexGeometry from rectangular dimensions.

        This is a convenience method for creating ComplexGeometry objects
        from simple rectangular parts, maintaining compatibility with
        existing rectangular nesting workflows.
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"Rectangle {id} must have positive dimensions")

        # Create rectangular contour points
        contour_points = [
            (x_offset, y_offset),
            (x_offset + width, y_offset),
            (x_offset + width, y_offset + height),
            (x_offset, y_offset + height),
            (x_offset, y_offset),  # Close the contour
        ]

        bounding_box = (x_offset, y_offset, x_offset + width, y_offset + height)
        area = width * height

        return cls(
            id=id,
            contour_points=contour_points,
            bounding_box=bounding_box,
            area=area,
            complexity_level=ComplexityLevel.LOW,
            rotation_allowed=rotation_allowed,
            geometry_type=GeometryType.RECTANGULAR,
            extraction_method=ExtractionMethod.BOUNDING_BOX,
        )

    def rotate(
        self, angle_degrees: float, center: Optional[Point2D] = None
    ) -> "ComplexGeometry":
        """Rotate the geometry by the specified angle around a center point.

        Args:
            angle_degrees: Rotation angle in degrees (positive = counterclockwise)
            center: Center point for rotation. If None, uses geometry centroid.

        Returns:
            New ComplexGeometry object with rotated contour points.
        """
        if not self.rotation_allowed:
            raise ValueError(f"Rotation not allowed for geometry {self.id}")

        if abs(angle_degrees) < 0.001:  # No meaningful rotation
            return self

        # Convert angle to radians
        angle_rad = math.radians(angle_degrees)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Use provided center or calculate centroid
        if center is None:
            center = self._calculate_centroid()

        cx, cy = center

        # Rotate all contour points
        rotated_points = []
        for x, y in self.contour_points:
            # Translate to origin
            tx = x - cx
            ty = y - cy

            # Rotate
            rx = tx * cos_a - ty * sin_a
            ry = tx * sin_a + ty * cos_a

            # Translate back
            rotated_points.append((rx + cx, ry + cy))

        # Recalculate bounding box for rotated geometry
        new_bounding_box = self._calculate_bounding_box(rotated_points)

        return ComplexGeometry(
            id=self.id,
            contour_points=rotated_points,
            bounding_box=new_bounding_box,
            area=self.area,  # Area doesn't change with rotation
            complexity_level=self.complexity_level,
            rotation_allowed=self.rotation_allowed,
            kerf_compensation=self.kerf_compensation,
            geometry_type=self.geometry_type,
            extraction_method=self.extraction_method,
        )

    def apply_kerf(self, kerf_mm: float) -> "ComplexGeometry":
        """Apply kerf compensation to the geometry.

        For complex geometries, this creates an offset contour that accounts
        for the cutting tool width. Positive kerf values shrink the geometry
        (inside offset), negative values expand it (outside offset).

        Args:
            kerf_mm: Kerf width in millimeters. Positive = shrink, negative = expand.

        Returns:
            New ComplexGeometry with kerf-compensated contour.
        """
        if abs(kerf_mm) < 0.001:  # No meaningful kerf
            return self

        # For now, implement a simple uniform offset
        # In a full implementation, this would use proper polygon offsetting algorithms
        offset_points = self._apply_uniform_offset(self.contour_points, -kerf_mm)

        if not offset_points or len(offset_points) < 3:
            # Kerf too large, geometry collapsed
            raise ValueError(f"Kerf {kerf_mm}mm too large for geometry {self.id}")

        # Recalculate properties for offset geometry
        new_bounding_box = self._calculate_bounding_box(offset_points)
        new_area = self._calculate_polygon_area(offset_points)

        return ComplexGeometry(
            id=self.id,
            contour_points=offset_points,
            bounding_box=new_bounding_box,
            area=new_area,
            complexity_level=self.complexity_level,
            rotation_allowed=self.rotation_allowed,
            kerf_compensation=kerf_mm,
            geometry_type=self.geometry_type,
            extraction_method=self.extraction_method,
        )

    def check_overlap(self, other: "ComplexGeometry", tolerance: float = 0.001) -> bool:
        """Check if this geometry overlaps with another geometry.

        This uses a combination of bounding box pre-filtering and
        polygon intersection testing for accurate overlap detection.

        Args:
            other: The other geometry to check against.
            tolerance: Minimum overlap distance to consider significant.

        Returns:
            True if geometries overlap, False otherwise.
        """
        # Quick bounding box check first
        if not self._bounding_boxes_overlap(
            self.bounding_box, other.bounding_box, tolerance
        ):
            return False

        # If bounding boxes overlap, check actual geometry intersection
        return self._polygons_intersect(
            self.contour_points, other.contour_points, tolerance
        )

    def get_width(self) -> float:
        """Get the width of the geometry's bounding box."""
        min_x, _, max_x, _ = self.bounding_box
        return max_x - min_x

    def get_height(self) -> float:
        """Get the height of the geometry's bounding box."""
        _, min_y, _, max_y = self.bounding_box
        return max_y - min_y

    def get_centroid(self) -> Point2D:
        """Get the centroid (center of mass) of the geometry."""
        return self._calculate_centroid()

    def is_rectangular(self) -> bool:
        """Check if this geometry is effectively rectangular."""
        return self.geometry_type == GeometryType.RECTANGULAR

    def _calculate_centroid(self) -> Point2D:
        """Calculate the centroid of the polygon using the shoelace formula."""
        if not self.contour_points:
            return (0.0, 0.0)

        # For simple cases, use bounding box center
        if len(self.contour_points) <= 4:
            min_x, min_y, max_x, max_y = self.bounding_box
            return ((min_x + max_x) / 2, (min_y + max_y) / 2)

        # Use polygon centroid formula for complex shapes
        area = 0.0
        cx = 0.0
        cy = 0.0

        for i in range(len(self.contour_points) - 1):
            x0, y0 = self.contour_points[i]
            x1, y1 = self.contour_points[i + 1]

            cross = x0 * y1 - x1 * y0
            area += cross
            cx += (x0 + x1) * cross
            cy += (y0 + y1) * cross

        if abs(area) < 0.001:
            # Degenerate polygon, use bounding box center
            min_x, min_y, max_x, max_y = self.bounding_box
            return ((min_x + max_x) / 2, (min_y + max_y) / 2)

        area *= 0.5
        cx /= 6.0 * area
        cy /= 6.0 * area

        return (cx, cy)

    def _calculate_bounding_box(self, points: List[Point2D]) -> BoundingBox:
        """Calculate the axis-aligned bounding box for a set of points."""
        if not points:
            return (0.0, 0.0, 0.0, 0.0)

        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)

        return (min_x, min_y, max_x, max_y)

    def _calculate_polygon_area(self, points: List[Point2D]) -> float:
        """Calculate the area of a polygon using the shoelace formula."""
        if len(points) < 3:
            return 0.0

        area = 0.0
        for i in range(len(points) - 1):
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
            area += x0 * y1 - x1 * y0

        return abs(area) / 2.0

    def _apply_uniform_offset(
        self, points: List[Point2D], offset: float
    ) -> List[Point2D]:
        """Apply a uniform offset to polygon points.

        This is a simplified implementation. A production version would use
        proper polygon offsetting algorithms like those in CGAL or Clipper.
        """
        if len(points) < 3 or abs(offset) < 0.001:
            return points.copy()

        # Simple implementation: move each point inward/outward along edge normals
        offset_points = []
        n = len(points) - 1  # Exclude the closing point

        for i in range(n):
            # Get the two edges adjacent to this vertex
            prev_idx = (i - 1) % n
            next_idx = (i + 1) % n

            # Calculate edge vectors
            prev_edge = (
                points[i][0] - points[prev_idx][0],
                points[i][1] - points[prev_idx][1],
            )
            next_edge = (
                points[next_idx][0] - points[i][0],
                points[next_idx][1] - points[i][1],
            )

            # Calculate normals (perpendicular vectors)
            prev_normal = self._normalize_vector((-prev_edge[1], prev_edge[0]))
            next_normal = self._normalize_vector((-next_edge[1], next_edge[0]))

            # Average the normals to get the offset direction
            avg_normal = (
                (prev_normal[0] + next_normal[0]) / 2,
                (prev_normal[1] + next_normal[1]) / 2,
            )
            avg_normal = self._normalize_vector(avg_normal)

            # Apply offset
            new_point = (
                points[i][0] + avg_normal[0] * offset,
                points[i][1] + avg_normal[1] * offset,
            )
            offset_points.append(new_point)

        # Close the polygon
        if offset_points:
            offset_points.append(offset_points[0])

        return offset_points

    def _normalize_vector(self, vector: Point2D) -> Point2D:
        """Normalize a 2D vector to unit length."""
        x, y = vector
        length = math.sqrt(x * x + y * y)
        if length < 0.001:
            return (0.0, 0.0)
        return (x / length, y / length)

    def _bounding_boxes_overlap(
        self, bbox1: BoundingBox, bbox2: BoundingBox, tolerance: float
    ) -> bool:
        """Check if two bounding boxes overlap."""
        min_x1, min_y1, max_x1, max_y1 = bbox1
        min_x2, min_y2, max_x2, max_y2 = bbox2

        return not (
            max_x1 + tolerance < min_x2
            or max_x2 + tolerance < min_x1
            or max_y1 + tolerance < min_y2
            or max_y2 + tolerance < min_y1
        )

    def _polygons_intersect(
        self, poly1: List[Point2D], poly2: List[Point2D], tolerance: float
    ) -> bool:
        """Check if two polygons intersect using the Separating Axes Theorem (SAT).

        This is a simplified implementation for convex polygons.
        A full implementation would handle concave polygons properly.
        """
        # For now, use a simple point-in-polygon test
        # Check if any vertex of poly1 is inside poly2
        for point in poly1[:-1]:  # Exclude closing point
            if self._point_in_polygon(point, poly2):
                return True

        # Check if any vertex of poly2 is inside poly1
        for point in poly2[:-1]:  # Exclude closing point
            if self._point_in_polygon(point, poly1):
                return True

        # Check for edge intersections (simplified)
        return self._edges_intersect(poly1, poly2)

    def _point_in_polygon(self, point: Point2D, polygon: List[Point2D]) -> bool:
        """Check if a point is inside a polygon using the ray casting algorithm."""
        x, y = point
        n = len(polygon) - 1  # Exclude closing point
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def _edges_intersect(self, poly1: List[Point2D], poly2: List[Point2D]) -> bool:
        """Check if any edges of the two polygons intersect."""
        # Simplified edge intersection check
        for i in range(len(poly1) - 1):
            for j in range(len(poly2) - 1):
                if self._line_segments_intersect(
                    poly1[i], poly1[i + 1], poly2[j], poly2[j + 1]
                ):
                    return True
        return False

    def _line_segments_intersect(
        self, p1: Point2D, p2: Point2D, p3: Point2D, p4: Point2D
    ) -> bool:
        """Check if two line segments intersect."""

        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)


def assess_geometry_complexity(
    contour_points: List[Point2D], area: float
) -> ComplexityLevel:
    """Assess the complexity level of a geometry based on its characteristics.

    This function helps determine the appropriate nesting algorithm and
    performance optimizations to use for a given geometry.

    Args:
        contour_points: The contour points defining the geometry.
        area: The area of the geometry in square millimeters.

    Returns:
        ComplexityLevel indicating the computational complexity.
    """
    if not contour_points or len(contour_points) < 3:
        return ComplexityLevel.LOW

    vertex_count = len(contour_points) - 1  # Exclude closing point

    # Simple heuristics for complexity assessment
    if vertex_count <= 4:
        return ComplexityLevel.LOW
    elif vertex_count <= 20:
        return ComplexityLevel.MEDIUM
    elif vertex_count <= 100:
        return ComplexityLevel.HIGH
    else:
        return ComplexityLevel.EXTREME


def create_rectangular_geometry(
    id: str, width: float, height: float, rotation_allowed: bool = True
) -> ComplexGeometry:
    """Convenience function to create rectangular ComplexGeometry objects."""
    return ComplexGeometry.from_rectangle(id, width, height, 0.0, 0.0, rotation_allowed)
