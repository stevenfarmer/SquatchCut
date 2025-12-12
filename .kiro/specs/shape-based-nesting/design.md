# Shape-Based Nesting Design Document

## Overview

This design document outlines the technical approach for enhancing SquatchCut to support comprehensive shape-based nesting workflows. The enhancement builds upon the existing `ShapeExtractor` foundation to provide true geometric nesting capabilities, improved user workflows, and robust testing infrastructure.

The implementation follows a phased approach: first enhancing the UI and selection workflow, then implementing non-rectangular nesting algorithms, followed by comprehensive testing and performance optimization, and finally documentation updates.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FreeCAD       │    │   SquatchCut     │    │   Output        │
│   Document      │───▶│   Shape-Based    │───▶│   Optimized     │
│   (User Shapes) │    │   Nesting        │    │   Layouts       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Enhanced       │
                    │   Selection UI   │
                    └──────────────────┘
```

### Component Integration

The shape-based nesting system integrates with existing SquatchCut components:

- **Enhanced ShapeExtractor**: Upgraded to handle complex geometry extraction
- **New GeometryNestingEngine**: Handles non-rectangular nesting algorithms
- **Enhanced Selection UI**: Improved dialog for shape selection and preview
- **Updated TaskPanel Integration**: Seamless workflow from selection to nesting
- **Extended Export System**: Support for complex shape export formats

## Components and Interfaces

### Enhanced ShapeExtractor

**Purpose**: Extract geometric data from FreeCAD objects with support for complex shapes

**Key Methods**:
```python
class EnhancedShapeExtractor(ShapeExtractor):
    def extract_complex_geometry(self, shape_obj) -> ComplexGeometry
    def extract_contour_points(self, shape_obj) -> List[Point2D]
    def validate_shape_complexity(self, shape_obj) -> ComplexityLevel
    def extract_with_fallback(self, shape_obj) -> Union[ComplexGeometry, BoundingBox]
```

**Interfaces**:
- Input: FreeCAD objects with Shape properties
- Output: ComplexGeometry objects or BoundingBox fallbacks

### GeometryNestingEngine

**Purpose**: Handle nesting of complex, non-rectangular shapes

**Key Methods**:
```python
class GeometryNestingEngine:
    def nest_complex_shapes(self, shapes: List[ComplexGeometry], sheet: SheetGeometry) -> NestingResult
    def detect_geometry_overlaps(self, shape1: ComplexGeometry, shape2: ComplexGeometry) -> bool
    def apply_kerf_to_geometry(self, geometry: ComplexGeometry, kerf_mm: float) -> ComplexGeometry
    def calculate_actual_utilization(self, layout: NestingResult) -> UtilizationStats
```

**Interfaces**:
- Input: ComplexGeometry objects, sheet dimensions, nesting parameters
- Output: NestingResult with precise shape placements

### Enhanced Selection Dialog

**Purpose**: Provide intuitive interface for selecting FreeCAD shapes for nesting

**Key Components**:
```python
class EnhancedShapeSelectionDialog(QtWidgets.QDialog):
    def populate_shape_list(self, detected_shapes: List[ShapeInfo]) -> None
    def generate_shape_previews(self, shapes: List[ShapeInfo]) -> List[PreviewWidget]
    def validate_selection(self) -> SelectionValidationResult
    def get_selected_shapes(self) -> List[ShapeInfo]
```

**UI Elements**:
- Shape list with checkboxes
- Preview thumbnails or geometry descriptions
- Dimension display (width × height × depth)
- Selection summary and validation feedback

### ComplexGeometry Data Model

**Purpose**: Represent non-rectangular shapes for nesting algorithms

```python
@dataclass
class ComplexGeometry:
    id: str
    contour_points: List[Point2D]
    bounding_box: BoundingBox
    area: float
    complexity_level: ComplexityLevel
    rotation_allowed: bool
    kerf_compensation: Optional[float] = None

    def rotate(self, angle_degrees: float) -> 'ComplexGeometry'
    def apply_kerf(self, kerf_mm: float) -> 'ComplexGeometry'
    def check_overlap(self, other: 'ComplexGeometry') -> bool
```

## Data Models

### Core Data Structures

**ShapeInfo**: Extended information about detected FreeCAD shapes
```python
@dataclass
class ShapeInfo:
    freecad_object: Any
    label: str
    dimensions: Tuple[float, float, float]  # width, height, depth
    geometry_type: GeometryType  # RECTANGULAR, CURVED, COMPLEX
    complexity_score: float
    preview_data: Optional[PreviewData]
    extraction_method: ExtractionMethod  # BOUNDING_BOX, CONTOUR, HYBRID
```

**NestingConfiguration**: Enhanced configuration for shape-based nesting
```python
@dataclass
class NestingConfiguration:
    nesting_mode: NestingMode  # RECTANGULAR, GEOMETRIC, HYBRID
    complexity_threshold: float
    performance_mode: PerformanceMode  # FAST, BALANCED, PRECISE
    kerf_handling: KerfHandling  # BOUNDING_BOX, GEOMETRIC
    fallback_enabled: bool
    progress_callback: Optional[Callable]
```

**NestingResult**: Extended results with geometric accuracy metrics
```python
@dataclass
class NestingResult:
    layouts: List[SheetLayout]
    utilization_stats: UtilizationStats
    geometric_accuracy: GeometricAccuracy
    processing_time: float
    fallback_count: int
    complexity_warnings: List[str]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After reviewing all testable properties from the prework analysis, I identified several areas where properties can be consolidated:

- **Shape Detection Properties**: Properties 1.1, 1.2, and 1.3 all relate to shape detection and can be combined into comprehensive detection validation
- **Selection Workflow Properties**: Properties 1.4, 3.1, 3.3, and 3.4 all test selection functionality and can be unified
- **Geometric Accuracy Properties**: Properties 2.1, 2.4, and 8.1 all validate geometric precision and can be consolidated
- **Nesting Validation Properties**: Properties 2.2, 8.2, and 8.5 all test nesting correctness and overlap prevention

The consolidated properties provide comprehensive coverage while eliminating redundancy.

**Property 1: Comprehensive Shape Detection**
*For any* FreeCAD document containing objects with Shape properties, SquatchCut should detect all valid objects and extract accurate dimensional and geometric data
**Validates: Requirements 1.1, 1.2, 1.3**

**Property 2: Selection Workflow Integrity**
*For any* set of detected shapes, the selection interface should allow users to choose specific shapes and process only the selected objects while preserving their identification
**Validates: Requirements 1.4, 1.5, 3.1, 3.3, 3.4**

**Property 3: Geometric Nesting Accuracy**
*For any* non-rectangular shape, the nesting system should extract actual geometric contours and calculate utilization based on true shape areas rather than bounding box approximations
**Validates: Requirements 2.1, 2.4, 8.1**

**Property 4: Overlap Prevention**
*For any* pair of complex shapes in a nesting layout, the system should detect and prevent overlaps between actual shape geometries, maintaining specified margins between contours
**Validates: Requirements 2.2, 8.2**

**Property 5: Rotation Preservation**
*For any* complex shape that undergoes rotation, the system should maintain geometric accuracy and preserve kerf and margin settings in the new orientation
**Validates: Requirements 2.3, 8.3**

**Property 6: Export Accuracy**
*For any* nesting layout containing complex shapes, exported files should include accurate shape outlines and kerf-compensated geometry for cutting guidance
**Validates: Requirements 2.5, 8.4**

**Property 7: Selection UI Completeness**
*For any* document with detected shapes, the selection interface should display all objects with names, dimensions, and appropriate visual elements
**Validates: Requirements 3.2**

**Property 8: Error Handling Robustness**
*For any* invalid input (malformed geometry, empty documents, invalid shapes), the system should handle errors gracefully without crashes
**Validates: Requirements 4.5**

**Property 9: Progress Feedback**
*For any* long-running nesting operation, the system should provide progress feedback to users
**Validates: Requirements 7.2**

**Property 10: Simplified Mode Availability**
*For any* complex geometry scenario, the system should offer simplified nesting modes for faster processing
**Validates: Requirements 7.4**

**Property 11: Graceful Fallback**
*For any* overly complex processing scenario, the system should fall back to bounding box nesting with appropriate user notification
**Validates: Requirements 7.5**

**Property 12: Boundary Validation with Kerf**
*For any* shape with kerf compensation applied, the system should verify that kerf-adjusted shapes still fit within sheet boundaries
**Validates: Requirements 8.5**

## Error Handling

### Error Categories

**Shape Extraction Errors**:
- Invalid or corrupted FreeCAD objects
- Objects without valid Shape properties
- Geometry too complex for processing
- Memory limitations with large shapes

**Nesting Algorithm Errors**:
- Shapes too large for available sheets
- Geometric complexity exceeding algorithm limits
- Overlap detection failures
- Performance timeouts

**UI Interaction Errors**:
- Empty shape selection
- Invalid user input in selection dialog
- UI component initialization failures
- Preview generation errors

### Error Recovery Strategies

**Graceful Degradation**: Fall back to bounding box nesting when geometric nesting fails
**User Notification**: Clear error messages with suggested remediation steps
**Partial Processing**: Continue with valid shapes when some shapes fail extraction
**Performance Limits**: Automatic simplification when complexity thresholds are exceeded

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit testing and property-based testing to ensure comprehensive coverage:

**Unit Tests**: Verify specific examples, edge cases, and error conditions for individual components
**Property Tests**: Verify universal properties that should hold across all inputs using randomized testing

### Property-Based Testing Framework

We will use **Hypothesis** (Python property-based testing library) to implement the correctness properties. Each property-based test will:
- Run a minimum of 100 iterations with randomized inputs
- Be tagged with comments referencing the specific correctness property
- Use the format: `**Feature: shape-based-nesting, Property {number}: {property_text}**`

### Test Categories

**Shape Extraction Tests**:
- Unit tests for specific FreeCAD object types (boxes, cylinders, complex curves)
- Property tests for extraction accuracy across randomized geometries
- Edge case tests for malformed or invalid objects

**Nesting Algorithm Tests**:
- Unit tests for specific shape combinations and layouts
- Property tests for overlap detection and geometric accuracy
- Performance tests for complex geometry handling

**UI Integration Tests**:
- Unit tests for selection dialog behavior with known shape sets
- Property tests for UI state management across various inputs
- GUI tests for user interaction workflows

**End-to-End Tests**:
- Complete workflow tests from FreeCAD design to final export
- Multi-scenario cabinet maker workflow validation
- Cross-platform compatibility testing

### Test Data Strategy

**Synthetic Geometry**: Programmatically generated shapes with known properties
**Real-World Samples**: Actual cabinet parts and furniture components
**Edge Cases**: Boundary conditions, invalid inputs, and stress test scenarios
**Performance Benchmarks**: Large documents with many complex shapes
