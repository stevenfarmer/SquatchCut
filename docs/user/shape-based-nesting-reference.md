# Shape-Based Nesting Technical Reference

**API Documentation and Configuration Guide**

Version: v3.4+
Feature: Shape-Based Nesting
Target Audience: Advanced users, developers, system integrators

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Configuration Options](#configuration-options)
4. [Nesting Modes](#nesting-modes)
5. [Performance Tuning](#performance-tuning)
6. [API Reference](#api-reference)
7. [Integration Guide](#integration-guide)
8. [Advanced Configuration](#advanced-configuration)

---

## Architecture Overview

### System Architecture

Shape-based nesting extends SquatchCut's core architecture with new components for handling complex geometry:

```
┌─────────────────────────────────────────────────────────┐
│                    SquatchCut v3.4+                     │
├─────────────────────────────────────────────────────────┤
│  GUI Layer                                              │
│  ├── EnhancedShapeSelectionDialog                       │
│  ├── TaskPanel Integration                              │
│  └── Progress Feedback System                           │
├─────────────────────────────────────────────────────────┤
│  Core Processing Layer                                  │
│  ├── ShapeExtractor (Enhanced)                         │
│  ├── GeometryNestingEngine                             │
│  ├── ComplexGeometry Data Model                        │
│  └── Performance Monitor                               │
├─────────────────────────────────────────────────────────┤
│  Optimization Layer                                     │
│  ├── Geometry Simplifier                               │
│  ├── Automatic Fallback System                         │
│  └── Progress Feedback                                  │
├─────────────────────────────────────────────────────────┤
│  Export Layer                                           │
│  ├── Enhanced SVG Export                               │
│  ├── DXF Export with Complex Shapes                    │
│  └── Enhanced Cutlist Generation                       │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Shape Detection**: FreeCAD objects → ShapeExtractor → ComplexGeometry objects
2. **User Selection**: ComplexGeometry objects → EnhancedShapeSelectionDialog → Selected shapes
3. **Nesting Processing**: Selected shapes → GeometryNestingEngine → Optimized layout
4. **Export Generation**: Layout → Export system → Production files

---

## Core Components

### ComplexGeometry Class

The foundation of shape-based nesting, representing non-rectangular parts.

**Key Properties:**
```python
class ComplexGeometry:
    id: str                          # Unique identifier
    contour_points: List[Tuple[float, float]]  # Shape boundary points
    bounding_box: Tuple[float, float, float, float]  # Min/max coordinates
    area: float                      # Actual shape area (mm²)
    complexity_level: ComplexityLevel  # LOW, MEDIUM, HIGH, EXTREME
    rotation_allowed: bool           # Can this shape be rotated?
    geometry_type: GeometryType      # RECTANGULAR, COMPLEX
    kerf_compensation: float         # Applied kerf width (mm)
```

**Complexity Levels:**
- **LOW**: ≤4 vertices, simple rectangles
- **MEDIUM**: 5-20 vertices, moderate complexity
- **HIGH**: 21-100 vertices, complex shapes
- **EXTREME**: >100 vertices, very complex shapes

### ShapeExtractor (Enhanced)

Converts FreeCAD objects into ComplexGeometry instances.

**Key Methods:**
```python
def extract_complex_geometry(self, freecad_obj) -> ComplexGeometry:
    """Extract detailed geometry from FreeCAD object."""

def extract_contour_points(self, shape) -> List[Tuple[float, float]]:
    """Extract boundary points from FreeCAD Shape."""

def validate_shape_complexity(self, geometry) -> bool:
    """Check if shape is suitable for geometric nesting."""

def extract_with_fallback(self, freecad_obj) -> ComplexGeometry:
    """Extract with automatic fallback to bounding box if needed."""
```

**Fallback Behavior:**
- Attempts complex geometry extraction first
- Falls back to bounding box if:
  - Shape is too complex (>1000 vertices)
  - Extraction fails due to invalid geometry
  - Processing time exceeds thresholds

### GeometryNestingEngine

Handles nesting of complex shapes with overlap detection.

**Core Capabilities:**
- True geometric overlap detection
- Rotation of complex shapes
- Kerf compensation for non-rectangular geometry
- Multi-mode nesting (rectangular, geometric, hybrid)

**Key Methods:**
```python
def nest_complex_shapes(self, geometries, sheet, mode) -> NestingResult:
    """Main nesting algorithm for complex shapes."""

def detect_geometry_overlaps(self, geom1, geom2, margin) -> bool:
    """Precise overlap detection between complex shapes."""

def apply_kerf_to_geometry(self, geometry, kerf_mm) -> ComplexGeometry:
    """Apply kerf compensation to complex geometry."""

def calculate_actual_utilization(self, result) -> UtilizationStats:
    """Calculate true material utilization based on actual areas."""
```

---

## Configuration Options

### Global Settings

Shape-based nesting adds new configuration options to SquatchCut settings:

**Performance Settings:**
```python
# Maximum complexity before automatic simplification
MAX_COMPLEXITY_VERTICES = 500

# Processing timeout (seconds)
NESTING_TIMEOUT_SECONDS = 300

# Memory usage threshold (MB)
MAX_MEMORY_USAGE_MB = 1024

# Enable automatic fallback to bounding box
AUTO_FALLBACK_ENABLED = True
```

**Quality Settings:**
```python
# Geometric precision (mm)
GEOMETRIC_PRECISION = 0.1

#imum margin between complex shapes (mm)
MIN_COMPLEX_MARGIN = 1.0

# Overlap detection tolerance (mm)
OVERLAP_TOLERANCE = 0.01

# Rotation angle increment (degrees)
ROTATION_INCREMENT = 15.0
```

### Per-Project Configuration

Settings that can be adjusted per nesting operation:

**Nesting Mode Selection:**
- `AUTO`: Automatically choose based on shape complexity
- `RECTANGULAR`: Force rectangular nesting for all shapes
- `GEOMETRIC`: Force geometric nesting for all shapes
- `HYBRID`: Mix rectangular and geometric as appropriate

**Performance vs. Quality Trade-offs:**
- `FAST`: Prioritize speed, use simplifications
- `BALANCED`: Balance speed and accuracy (default)
- `ACCURATE`: Prioritize accuracy, allow longer processing

### Environment Variables

Advanced configuration through environment variables:

```bash
# Enable debug logging for shape extraction
export SQUATCHCUT_DEBUG_SHAPES=1

# Override complexity thresholds
export SQUATCHCUT_MAX_VERTICES=1000

# Force specific nesting mode
export SQUATCHCUT_FORCE_MODE=geometric

# Enable performance profiling
export SQUATCHCUT_PROFILE=1
```

---

## Nesting Modes

### Rectangular Mode

**When Used:**
- All selected shapes are classified as rectangular
- User explicitly selects rectangular mode
- Fallback when geometric mode fails

**Characteristics:**
- Uses traditional bin-packing algorithms
- Fastest processing time
- Treats all shapes as bounding boxes
- Suitable for simple cabinet parts

**Performance:**
- Processing time: O(n log n) where n = number of parts
- Memory usage: Minimal
- Typical speed: 1000+ parts per second

### Geometric Mode

**When Used:**
- Complex shapes detected in selection
- User explicitly selects geometric mode
- Maximum accuracy required

**Characteristics:**
- Considers actual shape geometry
- Precise overlap detection
- Supports rotation of complex shapes
- Accounts for true shape areas

**Performance:**
- Processing time: O(n²) for overlap detection
- Memory usage: Higher due to contour storage
- Typical speed: 10-100 parts per second (depends on complexity)

### Hybrid Mode

**When Used:**
- Mixed rectangular and complex shapes
- Automatic mode selection (default)
- Balancing speed and accuracy

**Characteristics:**
- Rectangular shapes use fast algorithms
- Complex shapes use geometric algorithms
- Optimizes processing order
- Best overall performance/accuracy balance

**Algorithm Selection Logic:**
```python
def select_algorithm(geometry):
    if geometry.complexity_level == ComplexityLevel.LOW:
        return RectangularAlgorithm()
    elif geometry.complexity_level in [ComplexityLevel.MEDIUM, ComplexityLevel.HIGH]:
        return GeometricAlgorithm()
    else:  # EXTREME complexity
        return SimplifiedGeometricAlgorithm()
```

---

## Performance Tuning

### Complexity Management

**Automatic Simplification:**
Shape-based nesting includes automatic simplification for performance:

1. **Light Simplification** (100-500 vertices):
   - Reduce contour point density
   - Maintain overall shape accuracy
   - ~20% performance improvement

2. **Moderate Simplification** (500-1000 vertices):
   - Approximate curves with line segments
   - Preserve critical features
   - ~50% performance improvement

3. **Aggressive Simplification** (1000+ vertices):
   - Use convex hull approximation
   - Maintain bounding box accuracy
   - ~80% performance improvement

4. **Bounding Box Fallback** (extreme cases):
   - Fall back to rectangular nesting
   - Fastest processing
   - Maintains compatibility

### Performance Monitoring

**Built-in Metrics:**
```python
class PerformanceMetrics:
    extraction_time: float      # Shape extraction time (seconds)
    nesting_time: float        # Nesting algorithm time (seconds)
    memory_usage: float        # Peak memory usage (MB)
    complexity_score: float    # Overall complexity (0-1)
    simplification_applied: bool  # Was simplification used?
```

**Monitoring Thresholds:**
- **Warning**: Processing time > 30 seconds
- **Alert**: Memory usage > 512 MB
- **Critical**: Processing time > 300 seconds

### Optimization Strategies

**For Large Projects (100+ parts):**
1. Group parts by complexity level
2. Process in smaller batches (20-50 parts)
3. Use simplified nesting mode
4. Consider multiple sheet layouts

**For Complex Shapes:**
1. Enable automatic simplification
2. Increase processing timeout
3. Use hybrid mode for mixed complexity
4. Monitor memory usage

**For Production Environments:**
1. Set conservative complexity limits
2. Enable automatic fallback
3. Use performance monitoring
4. Implement timeout handling

---

## API Reference

### Core Classes

#### ComplexGeometry

```python
class ComplexGeometry:
    def __init__(self, id: str, contour_points: List[Tuple[float, float]],
                 bounding_box: Tuple[float, float, float, float], area: float,
                 complexity_level: ComplexityLevel, rotation_allowed: bool = True,
                 geometry_type: GeometryType = GeometryType.COMPLEX):
        """Initialize ComplexGeometry object."""

    def get_width(self) -> float:
        """Get bounding box width."""

    def get_height(self) -> float:
        """Get bounding box height."""

    def get_centroid(self) -> Tuple[float, float]:
        """Calculate geometric centroid."""

    def rotate(self, angle_degrees: float) -> 'ComplexGeometry':
        """Rotate geometry by specified angle."""

    def apply_kerf(self, kerf_mm: float) -> 'ComplexGeometry':
        """Apply kerf compensation to geometry."""

    def check_overlap(self, other: 'ComplexGeometry') -> bool:
        """Check if this geometry overlaps with another."""

    def is_rectangular(self) -> bool:
        """Check if geometry is rectangular."""
```

#### GeometryNestingEngine

```python
class GeometryNestingEngine:
    def __init__(self):
        """Initialize nesting engine."""

    def nest_complex_shapes(self, geometries: List[ComplexGeometry],
                          sheet: SheetGeometry, mode: NestingMode) -> NestingResult:
        """Nest complex shapes on sheet."""

    def detect_geometry_overlaps(self, geom1: ComplexGeometry,
                               geom2: ComplexGeometry, margin: float) -> bool:
        """Detect overlaps between positioned geometries."""

    def calculate_actual_utilization(self, result: NestingResult) -> UtilizationStats:
        """Calculate utilization based on actual shape areas."""

    def apply_kerf_to_geometry(self, geometry: ComplexGeometry,
                             kerf_mm: float) -> ComplexGeometry:
        """Apply kerf compensation to geometry."""
```

#### ShapeExtractor

```python
class ShapeExtractor:
    def extract_complex_geometry(self, freecad_obj) -> Optional[ComplexGeometry]:
        """Extract complex geometry from FreeCAD object."""

    def extract_contour_points(self, shape) -> List[Tuple[float, float]]:
        """Extract contour points from FreeCAD Shape."""

    def validate_shape_complexity(self, geometry: ComplexGeometry) -> bool:
        """Validate shape complexity for nesting."""

    def extract_with_fallback(self, freecad_obj) -> ComplexGeometry:
        """Extract with automatic fallback to bounding box."""
```

### Data Structures

#### NestingResult

```python
@dataclass
class NestingResult:
    placed_geometries: List[PlacedGeometry]
    unplaced_geometries: List[ComplexGeometry]
    sheets_used: int
    utilization_percent: float
    processing_time: float
    total_area_used: float
```

#### PlacedGeometry

```python
@dataclass
class PlacedGeometry:
    geometry: ComplexGeometry
    x: float
    y: float
    rotation: float
    sheet_index: int
```

#### UtilizationStats

```python
@dataclass
class UtilizationStats:
    sheets_used: int
    utilization_percent: float
    area_used_mm2: float
    area_wasted_mm2: float
    geometric_efficiency: float
    placement_efficiency: float
```

### Enumerations

```python
class ComplexityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class GeometryType(Enum):
    RECTANGULAR = "rectangular"
    COMPLEX = "complex"

class NestingMode(Enum):
    AUTO = "auto"
    RECTANGULAR = "rectangular"
    GEOMETRIC = "geometric"
    HYBRID = "hybrid"
```

---

## Integration Guide

### Integrating with Existing Workflows

**CSV + Shape Hybrid Workflow:**
```python
# Example: Combine CSV parts with FreeCAD shapes
csv_parts = load_csv_parts("cutlist.csv")
freecad_shapes = extract_shapes_from_document()

# Convert CSV to ComplexGeometry for unified processing
csv_geometries = [create_rectangular_geometry(p['id'], p['width'], p['height'])
                  for p in csv_parts]

# Combine and nest
all_geometries = csv_geometries + freecad_shapes
result = nesting_engine.nest_complex_shapes(all_geometries, sheet, NestingMode.HYBRID)
```

**Custom Shape Extraction:**
```python
# Example: Custom shape extraction for specialized objects
class CustomShapeExtractor(ShapeExtractor):
    def extract_complex_geometry(self, freecad_obj):
        if self.is_custom_type(freecad_obj):
            return self.extract_custom_geometry(freecad_obj)
        return super().extract_complex_geometry(freecad_obj)

    def extract_custom_geometry(self, obj):
        # Custom extraction logic
        contour = self.get_custom_contour(obj)
        return ComplexGeometry(
            id=obj.Label,
            contour_points=contour,
            bounding_box=self.calculate_bbox(contour),
            area=self.calculate_area(contour),
            complexity_level=self.assess_complexity(contour)
        )
```

### Plugin Development

**Creating Shape Processing Plugins:**
```python
class ShapeProcessingPlugin:
    def process_shapes(self, geometries: List[ComplexGeometry]) -> List[ComplexGeometry]:
        """Process shapes before nesting."""
        processed = []
        for geom in geometries:
            # Apply custom processing
            processed_geom = self.apply_custom_processing(geom)
            processed.append(processed_geom)
        return processed

    def apply_custom_processing(self, geometry: ComplexGeometry) -> ComplexGeometry:
        # Custom processing logic (e.g., optimization, validation)
        return geometry
```

**Registering Plugins:**
```python
# Register plugin with SquatchCut
from SquatchCut.core.plugin_manager import register_shape_plugin

register_shape_plugin("custom_processor", ShapeProcessingPlugin())
```

---

## Advanced Configuration

### Custom Nesting Algorithms

**Implementing Custom Algorithms:**
```python
class CustomNestingAlgorithm:
    def nest_shapes(self, geometries: List[ComplexGeometry],
                   sheet: SheetGeometry) -> NestingResult:
        """Custom nesting implementation."""
        # Implement your algorithm here
        placed = []
        unplaced = []

        # Your nesting logic
        for geom in geometries:
            position = self.find_best_position(geom, sheet, placed)
            if position:
                placed.append(PlacedGeometry(geom, position.x, position.y, 0, 0))
            else:
                unplaced.append(geom)

        return NestingResult(
            placed_geometries=placed,
            unplaced_geometries=unplaced,
            sheets_used=1,
            utilization_percent=self.calculate_utilization(placed, sheet),
            processing_time=0.0,
            total_area_used=sum(g.geometry.area for g in placed)
        )
```

### Performance Profiling

**Enable Detailed Profiling:**
```python
from SquatchCut.core.performance_monitor import PerformanceMonitor

# Enable profiling
monitor = PerformanceMonitor()
monitor.enable_profiling()

# Run nesting with profiling
with monitor.profile_operation("complex_nesting"):
    result = nesting_engine.nest_complex_shapes(geometries, sheet, mode)

# Get profiling results
profile_data = monitor.get_profile_data()
print(f"Processing time: {profile_data.total_time}s")
print(f"Memory usage: {profile_data.peak_memory}MB")
```

### Custom Export Formats

**Adding Custom Export Formats:**
```python
class CustomExporter:
    def export_layout(self, result: NestingResult, filename: str):
        """Export nesting result to custom format."""
        with open(filename, 'w') as f:
            f.write(self.generate_custom_format(result))

    def generate_custom_format(self, result: NestingResult) -> str:
        """Generate custom format output."""
        # Implement your export format
        output = []
        for placed in result.placed_geometries:
            line = f"{placed.geometry.id},{placed.x},{placed.y},{placed.rotation}"
            output.append(line)
        return "\n".join(output)

# Register custom exporter
from SquatchCut.core.exporter import register_export_format
register_export_format("custom", CustomExporter())
```

---

## Differences from Rectangular Nesting

### Key Distinctions

**Rectangular Nesting (Traditional):**
- Uses bounding box approximations
- Fast bin-packing algorithms
- Simple overlap detection (rectangle intersection)
- Uniform processing time regardless of shape complexity
- Limited material utilization for complex shapes

**Geometric Nesting (Shape-Based):**
- Uses actual shape geometry
- Complex geometric algorithms
- Precise contour-based overlap detection
- Processing time varies with shape complexity
- Maximum material utilization for all shape types

### Performance Comparison

| Aspect | Rectangular | Geometric | Hybrid |
|--------|-------------|-----------|---------|
| Speed | Fastest | Slowest | Balanced |
| Accuracy | Low for complex shapes | Highest | Good |
| Memory Usage | Minimal | Higher | Moderate |
| Complexity Handling | Poor | Excellent | Good |
| Material Utilization | 60-75% | 75-90% | 70-85% |

### When to Use Each Mode

**Use Rectangular Mode When:**
- All parts are simple rectangles
- Speed is critical
- Working with very large part counts (1000+)
- Legacy compatibility required

**Use Geometric Mode When:**
- Complex shapes are present
- Maximum material utilization needed
- Accuracy is more important than speed
- Working with expensive materials

**Use Hybrid Mode When:**
- Mixed part complexity
- Balancing speed and accuracy
- General-purpose nesting
- Uncertain about optimal mode

---

## Troubleshooting

### Common Issues and Solutions

**Issue: Shape extraction fails**
```
Error: "Unable to extract geometry from object"
Cause: Object lacks valid Shape property
Solution: Ensure object is a solid body, not sketch or assembly
```

**Issue: Nesting takes too long**
```
Warning: "Processing time exceeded threshold"
Cause: High shape complexity
Solution: Enable automatic simplification or use hybrid mode
```

**Issue: Poor material utilization**
```
Result: Utilization < 60%
Cause: Incompatible shapes or excessive margins
Solution: Adjust margins, try different sheet sizes, or group similar parts
```

**Issue: Memory usage too high**
```
Error: "Memory limit exceeded"
Cause: Too many complex shapes processed simultaneously
Solution: Process in smaller batches or increase memory limits
```

### Debug Information

**Enable Debug Logging:**
```python
import logging
logging.getLogger('SquatchCut.shape_nesting').setLevel(logging.DEBUG)
```

**Debug Output Example:**
```
DEBUG: Extracting geometry from object 'Door_Panel_001'
DEBUG: Detected 45 contour points, complexity: MEDIUM
DEBUG: Applying kerf compensation: 3.0mm
DEBUG: Nesting mode selected: GEOMETRIC
DEBUG: Processing 12 shapes, estimated time: 15s
DEBUG: Overlap detection: 0 conflicts found
DEBUG: Final utilization: 82.3%
```

---

## Version History

### v3.4.0 - Initial Shape-Based Nesting Release
- ComplexGeometry data model
- GeometryNestingEngine implementation
- Enhanced shape selection UI
- DXF export with complex shapes
- Performance optimization system

### Future Enhancements (Planned)
- **v3.5**: Advanced curve handling, spline support
- **v3.6**: 3D nesting for thick materials
- **v3.7**: AI-powered nesting optimization
- **v3.8**: Real-time collaborative nesting

---

## Support and Resources

### Documentation
- [Cabinet Maker Workflow Guide](cabinet-maker-workflow.md)
- [User Guide](../user_guide.md)
- [Developer Guide](../developer_guide.md)

### Community
- GitHub Issues: Report bugs and feature requests
- Forum: Community discussions and tips
- Wiki: Community-contributed examples and tutorials

### Professional Support
- Training: Available for teams and organizations
- Custom Development: Specialized features and integrations
- Consulting: Workflow optimization and best practices

---

*This technical reference covers SquatchCut v3.4+ shape-based nesting features. For general SquatchCut documentation, see the main [User Guide](../user_guide.md).*
