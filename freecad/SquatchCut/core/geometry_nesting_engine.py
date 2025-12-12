"""Geometry-based nesting engine for complex, non-rectangular shapes.

This module provides advanced nesting algorithms that work with actual shape
geometries rather than just bounding boxes, enabling more efficient material
utilization for complex parts like cabinet components.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from SquatchCut.core.complex_geometry import (
    BoundingBox,
    ComplexGeometry,
    ComplexityLevel,
    GeometryType,
)
from SquatchCut.core.performance_monitor import (
    PerformanceMode as PerfMode,
)
from SquatchCut.core.performance_monitor import (
    get_performance_monitor,
)
from SquatchCut.core.progress_feedback import (
    ProgressStage,
    ProgressTracker,
    get_progress_manager,
)


class NestingMode(Enum):
    """Nesting algorithm mode selection."""

    RECTANGULAR = "rectangular"  # Use bounding box approximation (fast)
    GEOMETRIC = "geometric"  # Use actual geometry (accurate)
    HYBRID = "hybrid"  # Automatic selection based on complexity


# Re-export PerformanceMode from performance_monitor for backward compatibility
PerformanceMode = PerfMode


@dataclass
class SheetGeometry:
    """Represents the geometry of a sheet for nesting."""

    width: float
    height: float
    margin: float = 0.0
    usable_area: float | None = None

    def __post_init__(self):
        if self.usable_area is None:
            usable_width = max(0, self.width - 2 * self.margin)
            usable_height = max(0, self.height - 2 * self.margin)
            self.usable_area = usable_width * usable_height


@dataclass
class PlacedGeometry:
    """Represents a placed geometry in a nesting layout."""

    geometry: ComplexGeometry
    x: float
    y: float
    rotation: float = 0.0
    sheet_index: int = 0
    placement_method: str = "geometric"


@dataclass
class NestingResult:
    """Results from a geometry-based nesting operation."""

    placed_geometries: list[PlacedGeometry]
    unplaced_geometries: list[ComplexGeometry]
    sheets_used: int
    total_area_used: float
    total_area_available: float
    utilization_percent: float
    processing_time: float
    complexity_warnings: list[str]
    fallback_count: int = 0


@dataclass
class GeometricAccuracy:
    """Metrics for geometric accuracy of nesting results."""

    overlap_count: int
    gap_efficiency: float  # How well gaps are utilized
    geometric_utilization: float  # Based on actual geometry vs bounding box
    rotation_efficiency: float  # How well rotations are utilized


@dataclass
class UtilizationStats:
    """Detailed utilization statistics for nesting results."""

    sheets_used: int
    utilization_percent: float
    area_used_mm2: float
    area_wasted_mm2: float
    geometric_efficiency: float  # Actual geometry area vs bounding box area
    placement_efficiency: float  # How well shapes are packed


class GeometryNestingEngine:
    """Advanced nesting engine for complex, non-rectangular shapes.

    This engine provides sophisticated nesting algorithms that work with actual
    shape geometries, enabling more efficient material utilization compared to
    traditional bounding box approaches.
    """

    def __init__(self, performance_mode: PerformanceMode = PerformanceMode.BALANCED):
        self.performance_mode = performance_mode
        self.complexity_threshold = self._get_complexity_threshold()
        self.max_rotation_attempts = self._get_max_rotation_attempts()
        self.placement_tolerance = 0.1  # mm
        self.performance_monitor = get_performance_monitor()
        self.progress_manager = get_progress_manager()
        self._current_operation_id: str | None = None
        self._current_progress_tracker: ProgressTracker | None = None

    def nest_complex_shapes(
        self,
        shapes: list[ComplexGeometry],
        sheet: SheetGeometry,
        nesting_mode: NestingMode = NestingMode.HYBRID,
        progress_callback: Any | None = None,
        cancellation_check: Any | None = None,
    ) -> NestingResult:
        """Nest complex shapes on a sheet using geometric algorithms.

        Args:
            shapes: List of ComplexGeometry objects to nest.
            sheet: SheetGeometry defining the available sheet space.
            nesting_mode: Algorithm mode (rectangular, geometric, or hybrid).
            progress_callback: Optional callback for progress updates.
            cancellation_check: Optional function to check for cancellation.

        Returns:
            NestingResult with placed and unplaced geometries.
        """
        # Start performance monitoring
        complexity_score = self.performance_monitor.assess_geometry_complexity(shapes)
        self._current_operation_id = self.performance_monitor.start_operation(
            "complex_shape_nesting",
            shapes_count=len(shapes),
            estimated_complexity=complexity_score,
        )

        # Check if we should recommend a different performance mode
        recommended_mode = self.performance_monitor.recommend_performance_mode(shapes)
        if recommended_mode != self.performance_mode:
            self.performance_monitor.add_warning(
                self._current_operation_id,
                f"Recommended mode: {recommended_mode.value}, using: {self.performance_mode.value}",
            )

        # Start progress tracking
        progress_operation_id = self.progress_manager.start_operation(
            "shape_nesting",
            total_items=len(shapes),
            progress_callback=progress_callback,
            cancellation_check=cancellation_check,
        )
        self._current_progress_tracker = self.progress_manager.get_tracker(
            progress_operation_id
        )

        if self._current_progress_tracker:
            self._current_progress_tracker.set_stage(
                ProgressStage.ANALYZING_SHAPES,
                f"Analyzing {len(shapes)} shapes for nesting",
            )
            if recommended_mode != self.performance_mode:
                self._current_progress_tracker.add_warning(
                    f"Using {self.performance_mode.value} mode instead of recommended {recommended_mode.value}"
                )

        import time

        start_time = time.time()

        placed_geometries = []
        unplaced_geometries = []
        complexity_warnings = []
        fallback_count = 0

        # Sort shapes by area (largest first) for better packing
        sorted_shapes = sorted(shapes, key=lambda s: s.area, reverse=True)

        # Track occupied regions on the sheet
        occupied_regions = []

        # Update progress to placing shapes stage
        if self._current_progress_tracker:
            self._current_progress_tracker.set_stage(
                ProgressStage.PLACING_SHAPES,
                f"Placing {len(sorted_shapes)} shapes on sheet",
            )

        for i, shape in enumerate(sorted_shapes):
            # Update progress for current shape
            if self._current_progress_tracker:
                if not self._current_progress_tracker.update_progress(
                    current_item=i,
                    description=f"Placing shape '{shape.id}' ({i+1}/{len(sorted_shapes)})",
                ):
                    # Operation was cancelled
                    unplaced_geometries.extend(sorted_shapes[i:])
                    break

            # Check for performance timeout periodically
            if i % 5 == 0 and self.performance_monitor.should_trigger_fallback(
                self._current_operation_id
            ):
                # Switch to faster mode for remaining shapes
                self.performance_mode = PerformanceMode.FAST
                self.performance_monitor.add_warning(
                    self._current_operation_id,
                    f"Performance timeout - switching to FAST mode for remaining {len(sorted_shapes) - i} shapes",
                )

            # Determine nesting approach based on mode and complexity
            use_geometric = self._should_use_geometric_nesting(shape, nesting_mode)

            if use_geometric:
                placement = self._place_shape_geometric(shape, sheet, occupied_regions)
            else:
                placement = self._place_shape_rectangular(
                    shape, sheet, occupied_regions
                )
                if not use_geometric:  # Was fallback
                    fallback_count += 1

            if placement:
                placed_geometries.append(placement)
                occupied_regions.append(self._get_occupied_region(placement))
            else:
                unplaced_geometries.append(shape)

                # Add complexity warning if shape is very complex
                if shape.complexity_level in [
                    ComplexityLevel.HIGH,
                    ComplexityLevel.EXTREME,
                ]:
                    complexity_warnings.append(
                        f"Complex shape '{shape.id}' could not be placed - consider simplification"
                    )

        # Update progress to calculation stage
        if self._current_progress_tracker:
            self._current_progress_tracker.set_stage(
                ProgressStage.CALCULATING_RESULTS, "Calculating utilization statistics"
            )

        # Calculate utilization statistics
        total_area_used = sum(p.geometry.area for p in placed_geometries)
        utilization_percent = (
            (total_area_used / sheet.usable_area) * 100 if sheet.usable_area > 0 else 0
        )

        processing_time = time.time() - start_time

        # Finish performance monitoring
        result = NestingResult(
            placed_geometries=placed_geometries,
            unplaced_geometries=unplaced_geometries,
            sheets_used=1,  # Single sheet for now
            total_area_used=total_area_used,
            total_area_available=sheet.usable_area,
            utilization_percent=utilization_percent,
            processing_time=processing_time,
            complexity_warnings=complexity_warnings,
            fallback_count=fallback_count,
        )

        # Record performance metrics
        success = len(placed_geometries) > 0 or len(shapes) == 0
        metrics = self.performance_monitor.finish_operation(
            self._current_operation_id,
            success=success,
            additional_metrics={
                "utilization_percent": utilization_percent,
                "fallback_count": fallback_count,
                "placed_count": len(placed_geometries),
                "unplaced_count": len(unplaced_geometries),
            },
        )

        # Add performance warnings to result
        if metrics.warnings:
            result.complexity_warnings.extend(
                [f"Performance: {w}" for w in metrics.warnings]
            )

        # Finish progress tracking
        if self._current_progress_tracker:
            self.progress_manager.finish_operation(
                progress_operation_id, success=success, result_data=result
            )
            self._current_progress_tracker = None

        self._current_operation_id = None
        return result

    def detect_geometry_overlaps(
        self, shape1: ComplexGeometry, shape2: ComplexGeometry, tolerance: float = 0.1
    ) -> bool:
        """Detect overlaps between two complex geometries with specified tolerance.

        Args:
            shape1: First geometry to check.
            shape2: Second geometry to check.
            tolerance: Minimum separation distance required.

        Returns:
            True if geometries overlap within tolerance, False otherwise.
        """
        # Use the ComplexGeometry's built-in overlap detection
        return shape1.check_overlap(shape2, tolerance)

    def apply_kerf_to_geometry(
        self, geometry: ComplexGeometry, kerf_mm: float
    ) -> ComplexGeometry:
        """Apply kerf compensation to a complex geometry.

        Args:
            geometry: The geometry to apply kerf compensation to.
            kerf_mm: Kerf width in millimeters.

        Returns:
            New ComplexGeometry with kerf compensation applied.
        """
        try:
            return geometry.apply_kerf(kerf_mm)
        except ValueError:
            # Kerf too large, return original geometry
            return geometry

    def calculate_actual_utilization(self, layout: NestingResult) -> UtilizationStats:
        """Calculate detailed utilization statistics based on actual geometry.

        Args:
            layout: NestingResult to analyze.

        Returns:
            UtilizationStats with detailed efficiency metrics.
        """
        if not layout.placed_geometries:
            return UtilizationStats(
                sheets_used=0,
                utilization_percent=0.0,
                area_used_mm2=0.0,
                area_wasted_mm2=layout.total_area_available,
                geometric_efficiency=0.0,
                placement_efficiency=0.0,
            )

        # Calculate actual geometry area vs bounding box area
        actual_area = sum(p.geometry.area for p in layout.placed_geometries)
        bounding_box_area = sum(
            p.geometry.get_width() * p.geometry.get_height()
            for p in layout.placed_geometries
        )

        geometric_efficiency = (
            actual_area / bounding_box_area if bounding_box_area > 0 else 0
        )

        # Calculate placement efficiency (how well shapes are packed)
        placement_efficiency = (
            actual_area / layout.total_area_available
            if layout.total_area_available > 0
            else 0
        )

        area_wasted = layout.total_area_available - actual_area

        return UtilizationStats(
            sheets_used=layout.sheets_used,
            utilization_percent=layout.utilization_percent,
            area_used_mm2=actual_area,
            area_wasted_mm2=area_wasted,
            geometric_efficiency=geometric_efficiency,
            placement_efficiency=placement_efficiency,
        )

    def _should_use_geometric_nesting(
        self, shape: ComplexGeometry, mode: NestingMode
    ) -> bool:
        """Determine whether to use geometric nesting for a shape."""
        if mode == NestingMode.RECTANGULAR:
            return False
        elif mode == NestingMode.GEOMETRIC:
            return True
        else:  # HYBRID mode
            # Use geometric nesting for non-rectangular shapes below complexity threshold
            return (
                shape.geometry_type != GeometryType.RECTANGULAR
                and shape.complexity_level != ComplexityLevel.EXTREME
            )

    def _place_shape_geometric(
        self,
        shape: ComplexGeometry,
        sheet: SheetGeometry,
        occupied_regions: list[dict[str, Any]],
    ) -> PlacedGeometry | None:
        """Place a shape using geometric nesting algorithms."""
        # Try different positions and rotations
        positions = self._generate_placement_positions(sheet, shape)
        rotations = self._generate_rotation_angles(shape)

        for position in positions:
            for rotation in rotations:
                # Create rotated geometry
                try:
                    if abs(rotation) > 0.1:
                        rotated_shape = shape.rotate(rotation)
                    else:
                        rotated_shape = shape

                    # Check if shape fits at this position
                    if self._shape_fits_at_position(
                        rotated_shape, position, sheet, occupied_regions
                    ):
                        return PlacedGeometry(
                            geometry=rotated_shape,
                            x=position[0],
                            y=position[1],
                            rotation=rotation,
                            placement_method="geometric",
                        )

                except ValueError:
                    # Rotation failed, skip this rotation
                    continue

        return None

    def _place_shape_rectangular(
        self,
        shape: ComplexGeometry,
        sheet: SheetGeometry,
        occupied_regions: list[dict[str, Any]],
    ) -> PlacedGeometry | None:
        """Place a shape using rectangular (bounding box) nesting algorithms."""
        # Use bounding box for placement
        width = shape.get_width()
        height = shape.get_height()

        # Try different positions
        positions = self._generate_placement_positions(sheet, shape)

        for position in positions:
            x, y = position

            # Check if bounding box fits
            if (
                x + width <= sheet.width - sheet.margin
                and y + height <= sheet.height - sheet.margin
            ):

                # Check for overlaps with occupied regions
                bbox_region = {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "type": "rectangular",
                }

                if not self._overlaps_with_regions(bbox_region, occupied_regions):
                    return PlacedGeometry(
                        geometry=shape,
                        x=x,
                        y=y,
                        rotation=0.0,
                        placement_method="rectangular",
                    )

        return None

    def _generate_placement_positions(
        self, sheet: SheetGeometry, shape: ComplexGeometry
    ) -> list[tuple[float, float]]:
        """Generate candidate placement positions for a shape."""
        positions = []

        # Start with corner positions
        positions.append((sheet.margin, sheet.margin))

        # Add grid positions based on performance mode
        if self.performance_mode == PerformanceMode.FAST:
            step_size = max(20.0, min(shape.get_width(), shape.get_height()) / 2)
        elif self.performance_mode == PerformanceMode.BALANCED:
            step_size = max(10.0, min(shape.get_width(), shape.get_height()) / 4)
        else:  # PRECISE
            step_size = max(5.0, min(shape.get_width(), shape.get_height()) / 8)

        x = sheet.margin
        while x + shape.get_width() <= sheet.width - sheet.margin:
            y = sheet.margin
            while y + shape.get_height() <= sheet.height - sheet.margin:
                positions.append((x, y))
                y += step_size
            x += step_size

        return positions

    def _generate_rotation_angles(self, shape: ComplexGeometry) -> list[float]:
        """Generate candidate rotation angles for a shape."""
        if not shape.rotation_allowed:
            return [0.0]

        angles = [0.0]  # Always try no rotation first

        # Add common angles based on performance mode
        if self.performance_mode == PerformanceMode.FAST:
            angles.extend([90.0])  # Only 90-degree rotation
        elif self.performance_mode == PerformanceMode.BALANCED:
            angles.extend([90.0, 180.0, 270.0])  # 90-degree increments
        else:  # PRECISE
            # More fine-grained rotation for complex shapes
            if shape.geometry_type == GeometryType.COMPLEX:
                angles.extend([45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0])
            else:
                angles.extend([90.0, 180.0, 270.0])

        return angles[: self.max_rotation_attempts]

    def _shape_fits_at_position(
        self,
        shape: ComplexGeometry,
        position: tuple[float, float],
        sheet: SheetGeometry,
        occupied_regions: list[dict[str, Any]],
    ) -> bool:
        """Check if a shape fits at a specific position without overlaps."""
        x, y = position

        # Check sheet boundaries using bounding box
        bbox = shape.bounding_box
        shape_width = bbox[2] - bbox[0]
        shape_height = bbox[3] - bbox[1]

        if (
            x + shape_width > sheet.width - sheet.margin
            or y + shape_height > sheet.height - sheet.margin
        ):
            return False

        # Create positioned geometry for overlap checking
        positioned_shape = self._create_positioned_geometry(shape, x, y)

        # Check for overlaps with occupied regions
        for region in occupied_regions:
            if region["type"] == "geometric":
                # Create positioned geometry from the region data
                region_positioned_geometry = self._create_positioned_geometry(
                    region["geometry"], region["x"], region["y"]
                )
                if self.detect_geometry_overlaps(
                    positioned_shape,
                    region_positioned_geometry,
                    self.placement_tolerance,
                ):
                    return False
            else:  # rectangular region
                if self._geometry_overlaps_rectangle(positioned_shape, region):
                    return False

        return True

    def _create_positioned_geometry(
        self, shape: ComplexGeometry, x: float, y: float
    ) -> ComplexGeometry:
        """Create a new geometry positioned at the specified coordinates."""
        # Translate contour points
        translated_points = [(px + x, py + y) for px, py in shape.contour_points]

        # Update bounding box
        min_x, min_y, max_x, max_y = shape.bounding_box
        new_bbox = (min_x + x, min_y + y, max_x + x, max_y + y)

        return ComplexGeometry(
            id=shape.id,
            contour_points=translated_points,
            bounding_box=new_bbox,
            area=shape.area,
            complexity_level=shape.complexity_level,
            rotation_allowed=shape.rotation_allowed,
            kerf_compensation=shape.kerf_compensation,
            geometry_type=shape.geometry_type,
            extraction_method=shape.extraction_method,
        )

    def _geometry_overlaps_rectangle(
        self, geometry: ComplexGeometry, rect_region: dict[str, Any]
    ) -> bool:
        """Check if a geometry overlaps with a rectangular region."""
        # Simple bounding box overlap check for now
        geom_bbox = geometry.bounding_box
        rect_bbox = (
            rect_region["x"],
            rect_region["y"],
            rect_region["x"] + rect_region["width"],
            rect_region["y"] + rect_region["height"],
        )

        return self._bounding_boxes_overlap(
            geom_bbox, rect_bbox, self.placement_tolerance
        )

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

    def _overlaps_with_regions(
        self, region: dict[str, Any], occupied_regions: list[dict[str, Any]]
    ) -> bool:
        """Check if a region overlaps with any occupied regions."""
        for occupied in occupied_regions:
            if occupied["type"] == "rectangular" and region["type"] == "rectangular":
                # Rectangle-rectangle overlap
                if self._rectangles_overlap(region, occupied):
                    return True
        return False

    def _rectangles_overlap(self, rect1: dict[str, Any], rect2: dict[str, Any]) -> bool:
        """Check if two rectangular regions overlap."""
        return not (
            rect1["x"] + rect1["width"] + self.placement_tolerance < rect2["x"]
            or rect2["x"] + rect2["width"] + self.placement_tolerance < rect1["x"]
            or rect1["y"] + rect1["height"] + self.placement_tolerance < rect2["y"]
            or rect2["y"] + rect2["height"] + self.placement_tolerance < rect1["y"]
        )

    def _get_occupied_region(self, placement: PlacedGeometry) -> dict[str, Any]:
        """Get the occupied region for a placed geometry."""
        if placement.placement_method == "geometric":
            return {
                "type": "geometric",
                "geometry": placement.geometry,
                "x": placement.x,
                "y": placement.y,
            }
        else:
            return {
                "type": "rectangular",
                "x": placement.x,
                "y": placement.y,
                "width": placement.geometry.get_width(),
                "height": placement.geometry.get_height(),
            }

    def _get_complexity_threshold(self) -> float:
        """Get complexity threshold based on performance mode."""
        thresholds = {
            PerformanceMode.FAST: 5.0,
            PerformanceMode.BALANCED: 8.0,
            PerformanceMode.PRECISE: 15.0,
        }
        return thresholds[self.performance_mode]

    def _get_max_rotation_attempts(self) -> int:
        """Get maximum rotation attempts based on performance mode."""
        attempts = {
            PerformanceMode.FAST: 2,
            PerformanceMode.BALANCED: 4,
            PerformanceMode.PRECISE: 8,
        }
        return attempts[self.performance_mode]
