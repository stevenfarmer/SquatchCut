"""@codex
Module: Shape extraction utilities for building SquatchCut panels from FreeCAD documents.
Boundaries: Do not load CSV files or perform nesting optimization; only inspect FreeCAD shapes and convert to panel objects.
Primary methods: scan_document, extract_bounding_boxes, to_panel_objects, apply_rotation_rules, filter_selection.
Enhanced methods: extract_complex_geometry, extract_contour_points, validate_shape_complexity, extract_with_fallback.
Note: Update incrementally; do not overwrite this module when adding logic.
"""

from __future__ import annotations

from SquatchCut.core.complex_geometry import (
    BoundingBox,
    ComplexGeometry,
    ComplexityLevel,
    ExtractionMethod,
    GeometryType,
    Point2D,
    assess_geometry_complexity,
)
from SquatchCut.freecad_integration import Gui


class ShapeExtractor:
    """Scans a FreeCAD document and produces panel objects for nesting."""

    def scan_document(self, document, selection_only: bool = False):
        """Scan the document for valid shapes; optionally limit to user selection."""
        if selection_only:
            return self.extract_from_selection(None)
        return self.extract_from_document(document)

    def extract_bounding_boxes(self, shapes):
        """Return bounding boxes (width, height) for each shape."""
        results = []
        for shape in shapes:
            bbox = self.extract_bounding_box(shape)
            if bbox:
                results.append(bbox)
        return results

    def to_panel_objects(self, shapes):
        """Convert shapes into normalized panel objects."""
        panels = []
        for shape in shapes:
            panel = self.to_panel_object(shape)
            if panel:
                panels.append(panel)
        return panels

    def apply_rotation_rules(self, panels):
        """Apply rotation rules to panels and annotate rotation allowances."""
        for panel in panels:
            panel.setdefault("rotation_allowed", True)
        return panels

    def filter_selection(self, document):
        """Return shapes filtered to the current user selection."""
        return self.extract_from_selection(None)

    def extract_from_document(self, document):
        """Iterate over document objects and extract panels."""
        if document is None:
            return []
        panels = []
        for obj in getattr(document, "Objects", []):
            panel = self.to_panel_object(obj)
            if panel:
                panels.append(panel)
        return panels

    def extract_from_selection(self, selection):
        """Process the current selection (or provided selection list) into panels."""
        selected_objects = []
        if selection is not None:
            selected_objects = selection
        elif Gui and hasattr(Gui, "Selection"):
            selected_objects = Gui.Selection.getSelection()

        panels = []
        for obj in selected_objects or []:
            panel = self.to_panel_object(obj)
            if panel:
                panels.append(panel)
        return panels

    def extract_bounding_box(self, shape):
        """Compute axis-aligned bounding box for a shape or object in mm."""
        bound = None
        if hasattr(shape, "Shape") and hasattr(shape.Shape, "BoundBox"):
            bound = shape.Shape.BoundBox
        elif hasattr(shape, "BoundBox"):
            bound = shape.BoundBox

        if bound is None:
            return None

        width = float(bound.XLength)
        height = float(bound.YLength)
        return width, height

    def to_panel_object(self, shape_or_obj):
        """Convert a FreeCAD object or shape to a panel dict."""
        bbox = self.extract_bounding_box(shape_or_obj)
        if not bbox:
            return None

        width, height = bbox
        if width <= 0 or height <= 0:
            return None

        label = getattr(shape_or_obj, "Label", None) or getattr(
            shape_or_obj, "Name", "panel"
        )
        return {
            "id": str(label),
            "width": width,
            "height": height,
            "rotation_allowed": True,
        }

    def extract_complex_geometry(self, shape_or_obj) -> ComplexGeometry | None:
        """Extract complex geometry from a FreeCAD object with full contour support.

        This method attempts to extract the actual geometric contour of the shape
        rather than just its bounding box, enabling true non-rectangular nesting.

        Args:
            shape_or_obj: FreeCAD object or shape to extract geometry from.

        Returns:
            ComplexGeometry object or None if extraction fails.
        """
        try:
            # Get basic properties
            label = getattr(shape_or_obj, "Label", None) or getattr(
                shape_or_obj, "Name", "shape"
            )

            # Try to extract contour points
            contour_points = self.extract_contour_points(shape_or_obj)
            if not contour_points or len(contour_points) < 3:
                # Fall back to bounding box extraction
                return self.extract_with_fallback(shape_or_obj)

            # Calculate bounding box from contour points
            min_x = min(p[0] for p in contour_points)
            min_y = min(p[1] for p in contour_points)
            max_x = max(p[0] for p in contour_points)
            max_y = max(p[1] for p in contour_points)
            bounding_box = (min_x, min_y, max_x, max_y)

            # Calculate area using shoelace formula
            area = self._calculate_polygon_area(contour_points)
            if area <= 0:
                return self.extract_with_fallback(shape_or_obj)

            # Assess complexity
            complexity_level = assess_geometry_complexity(contour_points, area)

            # Determine geometry type
            geometry_type = self._classify_geometry_type(
                contour_points, bounding_box, area
            )

            return ComplexGeometry(
                id=str(label),
                contour_points=contour_points,
                bounding_box=bounding_box,
                area=area,
                complexity_level=complexity_level,
                rotation_allowed=True,  # Default, can be overridden
                geometry_type=geometry_type,
                extraction_method=ExtractionMethod.CONTOUR,
            )

        except Exception:
            # If complex extraction fails, fall back to bounding box
            return self.extract_with_fallback(shape_or_obj)

    def extract_contour_points(self, shape_or_obj) -> list[Point2D] | None:
        """Extract detailed contour points from a FreeCAD shape.

        This method attempts to extract the actual boundary points of the shape
        for accurate geometric representation in nesting algorithms.

        Args:
            shape_or_obj: FreeCAD object or shape to extract contour from.

        Returns:
            List of 2D points representing the shape contour, or None if extraction fails.
        """
        try:
            # Get the shape object
            shape = None
            if hasattr(shape_or_obj, "Shape"):
                shape = shape_or_obj.Shape
            elif hasattr(shape_or_obj, "BoundBox"):
                shape = shape_or_obj

            if shape is None:
                return None

            # For now, implement a simplified contour extraction
            # In a full implementation, this would use FreeCAD's discretization methods
            # to extract actual contour points from curves, splines, etc.

            # Try to get wire/edge information if available
            if hasattr(shape, "Wires") and shape.Wires:
                # Extract points from the first wire (outer boundary)
                wire = shape.Wires[0]
                return self._extract_points_from_wire(wire)

            elif hasattr(shape, "Edges") and shape.Edges:
                # Extract points from edges
                return self._extract_points_from_edges(shape.Edges)

            else:
                # Fall back to bounding box approximation
                return self._create_rectangular_contour_from_bbox(shape)

        except Exception:
            return None

    def validate_shape_complexity(self, shape_or_obj) -> ComplexityLevel:
        """Assess the computational complexity of a shape for performance optimization.

        This method evaluates how computationally expensive it would be to process
        the shape with complex nesting algorithms, helping determine whether to
        use simplified algorithms or fallback methods.

        Args:
            shape_or_obj: FreeCAD object or shape to assess.

        Returns:
            ComplexityLevel indicating the computational complexity.
        """
        try:
            contour_points = self.extract_contour_points(shape_or_obj)
            if not contour_points:
                return ComplexityLevel.LOW

            # Calculate approximate area
            area = self._calculate_polygon_area(contour_points)

            return assess_geometry_complexity(contour_points, area)

        except Exception:
            return ComplexityLevel.LOW

    def extract_with_fallback(self, shape_or_obj) -> ComplexGeometry | None:
        """Extract geometry with graceful fallback to bounding box method.

        This method provides a robust extraction approach that attempts complex
        geometry extraction but falls back to rectangular approximation if needed.

        Args:
            shape_or_obj: FreeCAD object or shape to extract geometry from.

        Returns:
            ComplexGeometry object using the best available extraction method.
        """
        try:
            # Get basic bounding box information
            bbox = self.extract_bounding_box(shape_or_obj)
            if not bbox:
                return None

            width, height = bbox
            if width <= 0 or height <= 0:
                return None

            label = getattr(shape_or_obj, "Label", None) or getattr(
                shape_or_obj, "Name", "shape"
            )

            # Create rectangular ComplexGeometry as fallback
            return ComplexGeometry.from_rectangle(
                id=str(label), width=width, height=height, rotation_allowed=True
            )

        except Exception:
            return None

    def _extract_points_from_wire(self, wire) -> list[Point2D]:
        """Extract 2D points from a FreeCAD wire object."""
        points = []
        try:
            # This is a simplified implementation
            # In a full version, this would properly discretize the wire
            if hasattr(wire, "Vertexes"):
                for vertex in wire.Vertexes:
                    if hasattr(vertex, "Point"):
                        point = vertex.Point
                        points.append((float(point.x), float(point.y)))

            # Ensure contour is closed
            if points and len(points) > 2:
                if points[0] != points[-1]:
                    points.append(points[0])

        except Exception:
            pass

        return points

    def _extract_points_from_edges(self, edges) -> list[Point2D]:
        """Extract 2D points from a list of FreeCAD edge objects."""
        points = []
        try:
            for edge in edges:
                if hasattr(edge, "Vertexes"):
                    for vertex in edge.Vertexes:
                        if hasattr(vertex, "Point"):
                            point = vertex.Point
                            point_2d = (float(point.x), float(point.y))
                            # Avoid duplicate points
                            if not points or point_2d != points[-1]:
                                points.append(point_2d)

            # Ensure contour is closed
            if points and len(points) > 2:
                if points[0] != points[-1]:
                    points.append(points[0])

        except Exception:
            pass

        return points

    def _create_rectangular_contour_from_bbox(self, shape) -> list[Point2D]:
        """Create a rectangular contour from a shape's bounding box."""
        try:
            if hasattr(shape, "BoundBox"):
                bbox = shape.BoundBox
                min_x = float(bbox.XMin)
                min_y = float(bbox.YMin)
                max_x = float(bbox.XMax)
                max_y = float(bbox.YMax)

                return [
                    (min_x, min_y),
                    (max_x, min_y),
                    (max_x, max_y),
                    (min_x, max_y),
                    (min_x, min_y),  # Close the contour
                ]
        except Exception:
            pass

        return []

    def _calculate_polygon_area(self, points: list[Point2D]) -> float:
        """Calculate the area of a polygon using the shoelace formula."""
        if len(points) < 3:
            return 0.0

        area = 0.0
        for i in range(len(points) - 1):
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
            area += x0 * y1 - x1 * y0

        return abs(area) / 2.0

    def _classify_geometry_type(
        self, contour_points: list[Point2D], bounding_box: BoundingBox, area: float
    ) -> GeometryType:
        """Classify the geometry type based on contour analysis."""
        if len(contour_points) <= 5:  # Rectangle has 5 points (including closure)
            # Check if it's actually rectangular
            bbox_area = (bounding_box[2] - bounding_box[0]) * (
                bounding_box[3] - bounding_box[1]
            )
            if abs(area - bbox_area) < 0.001:
                return GeometryType.RECTANGULAR

        # Check for curves by analyzing edge angles
        if self._has_curved_edges(contour_points):
            return GeometryType.CURVED

        return GeometryType.COMPLEX

    def _has_curved_edges(self, contour_points: list[Point2D]) -> bool:
        """Detect if the contour has curved edges based on point distribution."""
        if len(contour_points) < 10:
            return False

        # Simple heuristic: if we have many points, it's likely curved
        # A more sophisticated implementation would analyze curvature
        return len(contour_points) > 20

    def _classify_geometry_type(self, freecad_obj) -> GeometryType:
        """Classify geometry type from a FreeCAD object (overloaded method)."""
        try:
            if not hasattr(freecad_obj, "Shape") or freecad_obj.Shape is None:
                return GeometryType.RECTANGULAR

            shape = freecad_obj.Shape

            # Simple classification based on shape type
            if hasattr(shape, "ShapeType"):
                shape_type = shape.ShapeType
                if shape_type in ["Solid", "CompSolid"]:
                    # For solids, check if it's a simple box
                    bbox = shape.BoundBox
                    if hasattr(bbox, "XLength") and hasattr(bbox, "YLength"):
                        # Simple heuristic: if it's a box-like solid, consider it rectangular
                        return GeometryType.RECTANGULAR
                elif shape_type in ["Face", "Shell"]:
                    # Faces could be curved
                    return GeometryType.CURVED

            # Default to complex for unknown types
            return GeometryType.COMPLEX

        except Exception:
            return GeometryType.RECTANGULAR

    def _assess_complexity(self, freecad_obj) -> float:
        """Assess the complexity score of a FreeCAD object."""
        try:
            if not hasattr(freecad_obj, "Shape") or freecad_obj.Shape is None:
                return 1.0

            shape = freecad_obj.Shape

            # Simple complexity scoring based on shape properties
            complexity_score = 1.0

            # Add complexity based on number of faces
            if hasattr(shape, "Faces"):
                face_count = len(shape.Faces)
                complexity_score += face_count * 0.5

            # Add complexity based on number of edges
            if hasattr(shape, "Edges"):
                edge_count = len(shape.Edges)
                complexity_score += edge_count * 0.1

            # Add complexity based on number of vertices
            if hasattr(shape, "Vertexes"):
                vertex_count = len(shape.Vertexes)
                complexity_score += vertex_count * 0.05

            return min(complexity_score, 10.0)  # Cap at 10.0

        except Exception:
            return 1.0

    def extract_with_fallback_advanced(
        self, freecad_obj, complexity_threshold: float = 5.0
    ):
        """
        Extract geometry with automatic fallback to simpler methods for complex shapes.

        This method provides graceful degradation when dealing with very complex
        geometries that might be too expensive to process with full accuracy.

        Args:
            freecad_obj: FreeCAD object to extract geometry from
            complexity_threshold: Threshold above which to use fallback (default 5.0)

        Returns:
            tuple: (ComplexGeometry, extraction_method_used, user_notification)

        Raises:
            ValueError: If the object cannot be processed at all
        """
        if not hasattr(freecad_obj, "Shape") or freecad_obj.Shape is None:
            raise ValueError(
                f"Object {getattr(freecad_obj, 'Label', 'Unknown')} has no valid Shape"
            )

        # Assess complexity
        complexity = self._assess_complexity(freecad_obj)

        # Try full extraction first if complexity is manageable
        if complexity <= complexity_threshold:
            try:
                geometry = self.extract_complex_geometry(freecad_obj)
                return geometry, "full_extraction", None
            except Exception:
                # Fall through to fallback methods
                pass

        # Fallback 1: Use bounding box extraction
        try:
            bbox = self.extract_bounding_box(freecad_obj)
            if bbox is not None:
                width_mm, height_mm = bbox
                from SquatchCut.core.complex_geometry import create_rectangular_geometry

                geometry = create_rectangular_geometry(
                    freecad_obj.Label, width_mm, height_mm
                )

                notification = (
                    f"Shape '{freecad_obj.Label}' is complex (score: {complexity:.1f}). "
                    f"Using simplified rectangular approximation for better performance."
                )

                return geometry, "bounding_box_fallback", notification
        except Exception:
            pass

        # Fallback 2: Use default dimensions if available
        try:
            # Try to get dimensions from object properties
            width = getattr(freecad_obj, "Width", None)
            height = getattr(freecad_obj, "Height", None)

            if width is not None and height is not None:
                from SquatchCut.core.complex_geometry import create_rectangular_geometry

                geometry = create_rectangular_geometry(
                    freecad_obj.Label, float(width), float(height)
                )

                notification = (
                    f"Shape '{freecad_obj.Label}' could not be processed geometrically. "
                    f"Using object dimensions ({width}mm x {height}mm)."
                )

                return geometry, "property_fallback", notification
        except Exception:
            pass

        # Final fallback: Use minimal default size
        raise ValueError(
            f"Cannot extract geometry from object '{freecad_obj.Label}'. "
            f"The shape may be invalid or too complex to process."
        )
