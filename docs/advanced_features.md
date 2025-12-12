# SquatchCut Advanced Features

This document describes the advanced features implemented in SquatchCut for enhanced nesting optimization, export capabilities, cut planning, quality assurance, and performance.

## Overview

The advanced features system provides five major enhancements to SquatchCut's core functionality:

1. **Advanced Nesting Algorithms** - Genetic algorithm optimization with grain direction support
2. **Enhanced Export Capabilities** - SVG with cut lines, DXF export, and enhanced CSV exports
3. **Smart Cut Optimization** - Automated cut sequence planning for efficient material processing
4. **Quality Assurance** - Comprehensive layout validation and quality reporting
5. **Performance Enhancements** - Multi-threading, caching, and memory optimization

## Feature 1: Advanced Nesting Algorithms

### Genetic Algorithm Optimization

The genetic algorithm provides superior nesting results for complex layouts by evolving solutions over multiple generations.

**Key Components:**
- `GeneticNestingOptimizer` - Main optimization engine
- `GeneticConfig` - Configuration for population size, generations, mutation rates
- `Individual` - Represents a single nesting solution in the population

**Configuration Options:**
```python
config = GeneticConfig(
    population_size=50,      # Number of solutions per generation
    generations=100,         # Number of evolution cycles
    mutation_rate=0.1,       # Probability of random changes
    crossover_rate=0.8,      # Probability of combining solutions
    max_time_seconds=300,    # Maximum optimization time
    target_utilization=0.95  # Stop if this utilization is reached
)
```

**Usage:**
```python
from SquatchCut.core.genetic_nesting import genetic_nest_parts, GeneticConfig

config = GeneticConfig(population_size=30, generations=50)
placed_parts = genetic_nest_parts(parts, sheet_width, sheet_height, config=config)
```

### Grain Direction Support

Wood grain direction awareness ensures parts are oriented correctly for structural integrity and appearance.

**Grain Directions:**
- `HORIZONTAL` - Grain runs left-right
- `VERTICAL` - Grain runs up-down
- `ANY` - No grain preference

**Key Components:**
- `GrainAwarePart` - Part with grain direction information
- `GrainConstraints` - Rules for grain compliance
- Automatic grain inference from part dimensions
- Grain compatibility checking and penalty calculation

**Usage:**
```python
from SquatchCut.core.grain_direction import GrainAwarePart, GrainConstraints

# Create grain-aware part
part = GrainAwarePart("panel", 200, 50, grain_direction=GrainDirection.HORIZONTAL)

# Set constraints
constraints = GrainConstraints(
    sheet_grain=GrainDirection.HORIZONTAL,
    enforce_part_grain=True,
    allow_cross_grain=False
)
```

## Feature 2: Enhanced Export Capabilities

### SVG Export with Cut Lines

Enhanced SVG exports include visual cut lines and waste area highlighting for better workshop planning.

**New SVG Features:**
- Cut line visualization (dashed red lines)
- Waste area highlighting (semi-transparent red)
- Improved part labeling and dimensions
- Multi-sheet support with proper scaling

**Usage:**
```python
from SquatchCut.core.exporter import export_nesting_to_svg

paths = export_nesting_to_svg(
    export_job,
    "nesting_layout.svg",
    include_labels=True,
    include_dimensions=True,
    include_cut_lines=True,
    include_waste_areas=True
)
```

### DXF Export

Professional CAD-compatible DXF export for CNC and CAM software integration.

**DXF Features:**
- Industry-standard R2010 format
- Organized layers (SHEET_BOUNDARY, PARTS, LABELS, CUT_LINES, DIMENSIONS)
- Proper scaling and units
- Cut line generation for automated cutting

**Usage:**
```python
from SquatchCut.core.exporter import export_nesting_to_dxf

paths = export_nesting_to_dxf(
    export_job,
    "nesting_layout.dxf",
    include_labels=True,
    include_cut_lines=True
)
```

### Enhanced CSV Export

Improved CSV exports with measurement system formatting and additional metadata.

**CSV Enhancements:**
- Display dimensions in user's preferred units (metric/imperial)
- Sheet information included
- Rotation and position data
- Export job metadata

## Feature 3: Smart Cut Optimization

### Cut Sequence Planning

Automated planning of optimal cutting sequences to minimize material handling and setup time.

**Key Components:**
- `CutSequencePlanner` - Main planning engine
- `CutOperation` - Individual cut with metadata
- `CutSequence` - Complete sequence for one sheet

**Cut Types:**
- **Rip cuts** - Vertical cuts along the grain
- **Crosscuts** - Horizontal cuts across the grain
- **Trim cuts** - Final sizing operations

**Planning Strategy:**
1. Collect all required cut lines from part boundaries
2. Plan rip cuts first (left to right)
3. Plan crosscuts second (bottom to top)
4. Optimize sequence to minimize material handling
5. Calculate time estimates and cut lengths

**Usage:**
```python
from SquatchCut.core.cut_sequence import plan_optimal_cutting_sequence

sequences = plan_optimal_cutting_sequence(placed_parts, sheet_sizes, kerf_width=3.0)

for sequence in sequences:
    print(f"Sheet {sequence.sheet_index}: {len(sequence.operations)} cuts")
    print(f"Total cut length: {sequence.total_cut_length:.1f}mm")
    print(f"Estimated time: {sequence.estimated_time_minutes:.1f} minutes")
```

### Cut Optimization Features

- **Material handling optimization** - Minimize offcut movement
- **Setup time reduction** - Group similar cuts together
- **Cut length optimization** - Only cut where necessary
- **Time estimation** - Realistic cutting time predictions

## Feature 4: Quality Assurance

### Comprehensive Layout Validation

Automated quality checks ensure nesting layouts meet production requirements.

**Quality Checks:**
- **Overlap detection** - Find overlapping parts
- **Bounds compliance** - Ensure parts fit within sheets
- **Spacing requirements** - Verify minimum spacing between parts
- **Rotation validation** - Check for valid rotation angles
- **Dimension consistency** - Compare with original part specifications
- **Grain direction compliance** - Validate grain requirements

**Issue Severity Levels:**
- **Critical** - Must be fixed before production
- **Warning** - Should be reviewed
- **Info** - Informational only

**Usage:**
```python
from SquatchCut.core.quality_assurance import check_nesting_quality

report = check_nesting_quality(
    placed_parts,
    sheet_sizes,
    min_spacing=3.0,
    original_parts=parts
)

print(f"Quality Score: {report.overall_score:.1f}/100")
print(f"Issues Found: {len(report.issues)}")

for issue in report.issues:
    print(f"- {issue.severity.value.upper()}: {issue.description}")
```

### Quality Reporting

Detailed quality reports provide actionable feedback for layout improvements.

**Report Contents:**
- Overall quality score (0-100)
- Issue breakdown by severity
- Quality metrics (utilization, compliance rates)
- Suggested fixes for each issue
- Pass/fail status for each check

## Feature 5: Performance Enhancements

### Intelligent Caching

Results caching eliminates redundant calculations for identical nesting parameters.

**Cache Features:**
- Memory and disk-based caching
- Automatic cache key generation
- Configurable cache size limits
- Thread-safe operations

**Usage:**
```python
from SquatchCut.core.performance_utils import cached_nesting, configure_cache

# Configure cache
configure_cache(cache_dir="/tmp/squatchcut_cache", max_cache_size=100)

# Use caching decorator
@cached_nesting
def my_nesting_function(parts, width, height, config=None):
    # Expensive nesting calculation
    return result
```

### Multi-threading Support

Parallel processing capabilities for large datasets and multiple sheets.

**Parallel Processing:**
- Multi-sheet processing in parallel
- Large dataset batch processing
- Configurable worker threads
- Automatic load balancing

**Usage:**
```python
from SquatchCut.core.performance_utils import ParallelNestingProcessor

processor = ParallelNestingProcessor(max_workers=4)

# Process multiple sheet configurations
results = processor.process_multiple_sheets(sheet_configs, nesting_function)

# Process large datasets in batches
batch_results = processor.process_part_batches(parts, batch_size=100, processing_func)
```

### Memory Optimization

Memory usage optimization for large datasets and extended operations.

**Memory Features:**
- Part data structure optimization
- Intermediate data cleanup
- Garbage collection triggers
- Memory usage monitoring

**Usage:**
```python
from SquatchCut.core.performance_utils import memory_optimized

@memory_optimized
def memory_efficient_nesting(parts, width, height):
    # Memory-optimized nesting operation
    return result
```

## Integration with Main System

### Session State Integration

All advanced features integrate with SquatchCut's session state system:

```python
# Enable genetic algorithm
session_state.set_use_genetic_algorithm(True)
session_state.set_genetic_population_size(50)
session_state.set_genetic_generations(100)

# Enable cut sequence generation
session_state.set_generate_cut_sequence(True)
```

### Command Integration

Advanced features are automatically used when enabled in the main nesting command:

1. **Genetic Algorithm** - Activated when `use_genetic_algorithm` is enabled
2. **Quality Assurance** - Always runs after nesting completion
3. **Cut Sequence Planning** - Activated when `generate_cut_sequence` is enabled
4. **Performance Optimizations** - Applied automatically for large datasets

### Export Integration

Enhanced export capabilities are available through the existing export commands:

- SVG exports automatically include cut lines when requested
- DXF export is available as a new export option
- CSV exports include enhanced formatting and metadata

## Configuration and Settings

### Genetic Algorithm Settings

```python
# Population and evolution settings
session_state.set_genetic_population_size(50)      # 10-200 recommended
session_state.set_genetic_generations(100)         # 50-500 recommended
session_state.set_genetic_mutation_rate(0.1)       # 0.05-0.2 recommended
session_state.set_genetic_crossover_rate(0.8)      # 0.6-0.9 recommended
session_state.set_genetic_max_time(300)            # Maximum seconds
```

### Quality Assurance Settings

```python
# Quality check configuration
checker = QualityAssuranceChecker(
    min_spacing=3.0,           # Minimum spacing between parts (mm)
    tolerance=0.1,             # Measurement tolerance (mm)
    check_grain_direction=True # Enable grain direction checking
)
```

### Performance Settings

```python
# Cache configuration
configure_cache(
    cache_dir="/path/to/cache",  # Cache directory
    max_cache_size=100           # Maximum cached items
)

# Parallel processing
processor = ParallelNestingProcessor(
    max_workers=4,        # Number of worker threads
    use_processes=False   # Use threads (False) or processes (True)
)
```

## Best Practices

### When to Use Genetic Algorithm

- **Complex layouts** with many parts
- **High utilization requirements** (>90%)
- **Grain direction constraints** are important
- **Standard algorithms** produce suboptimal results

### Export Recommendations

- **SVG with cut lines** for workshop planning and manual cutting
- **DXF export** for CNC and automated cutting systems
- **Enhanced CSV** for detailed part lists and inventory

### Quality Assurance Guidelines

- **Always run quality checks** before production
- **Address critical issues** immediately
- **Review warnings** for potential improvements
- **Monitor quality scores** over time

### Performance Optimization

- **Enable caching** for repeated operations
- **Use parallel processing** for large datasets (>100 parts)
- **Monitor memory usage** for very large projects
- **Clear cache periodically** to free disk space

## Troubleshooting

### Common Issues

1. **Genetic algorithm too slow**
   - Reduce population size or generations
   - Set shorter max_time_seconds
   - Enable caching for repeated runs

2. **Quality issues not detected**
   - Check tolerance settings
   - Verify minimum spacing requirements
   - Enable all quality checks

3. **Export failures**
   - Ensure sufficient disk space
   - Check file permissions
   - Verify export directory exists

4. **Memory issues with large datasets**
   - Enable memory optimization
   - Process in smaller batches
   - Increase system memory

### Performance Tuning

- **Small datasets (<50 parts)**: Use standard algorithms
- **Medium datasets (50-500 parts)**: Enable caching and memory optimization
- **Large datasets (>500 parts)**: Enable all performance features
- **Very large datasets (>1000 parts)**: Use parallel processing and batching

## Future Enhancements

The advanced features system is designed for extensibility. Planned enhancements include:

- **Machine learning** optimization algorithms
- **Advanced grain patterns** (diagonal, radial)
- **3D nesting** for thick materials
- **Real-time collaboration** features
- **Cloud-based optimization** services

## API Reference

For detailed API documentation, see the individual module documentation:

- `freecad/SquatchCut/core/genetic_nesting.py` - Genetic algorithm implementation
- `freecad/SquatchCut/core/grain_direction.py` - Grain direction support
- `freecad/SquatchCut/core/cut_sequence.py` - Cut sequence planning
- `freecad/SquatchCut/core/quality_assurance.py` - Quality assurance system
- `freecad/SquatchCut/core/performance_utils.py` - Performance enhancements
