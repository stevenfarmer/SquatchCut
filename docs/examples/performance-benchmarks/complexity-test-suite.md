# Shape-Based Nesting Performance Benchmarks

**Test Suite for Performance Validation and Optimization**

## Overview

This benchmark suite provides standardized tests for evaluating SquatchCut's shape-based nesting performance across different complexity levels, part counts, and system configurations.

## Test Categories

### 1. Complexity Scaling Tests

**Purpose:** Measure performance impact of increasing shape complexity

#### Test 1.1: Vertex Count Scaling
```
Test Parts: Single shape with varying vertex counts
Vertex Counts: 4, 10, 25, 50, 100, 250, 500, 1000
Sheet Size: 1220×2440mm
Expected Results:
- 4-25 vertices: < 1 second processing
- 50-100 vertices: 1-5 seconds processing
- 250-500 vertices: 5-30 seconds processing
- 1000+ vertices: Automatic simplification triggered
```

#### Test 1.2: Shape Type Performance
```
Test Shapes:
- Rectangle: 4 vertices (baseline)
- Hexagon: 6 vertices
- Circle (approximated): 24 vertices
- Complex curve: 100 vertices
- Highly detailed: 500+ verti
ics:
- Processing time per shape type
- Memory usage scaling
- Accuracy vs performance trade-offs
```

### 2. Part Count Scaling Tests

**Purpose:** Evaluate performance with increasing numbers of parts

#### Test 2.1: Rectangular Parts Scaling
```
Part Counts: 10, 50, 100, 500, 1000, 2000
Part Type: Simple rectangles (2×4 ratio)
Sheet Size: 2440×1220mm
Expected Performance:
- 10 parts: < 0.1 seconds
- 100 parts: < 1 second
- 1000 parts: < 10 seconds
- 2000 parts: < 30 seconds
```

#### Test 2.2: Complex Parts Scaling
```
Part Counts: 5, 10, 25, 50, 100
Part Type: 50-vertex polygons
Sheet Size: 2440×1220mm
Expected Performance:
- 5 parts: < 2 seconds
- 10 parts: < 10 seconds
- 25 parts: < 60 seconds
- 50+ parts: May require batching
```

### 3. Memory Usage Tests

**Purpose:** Validate memory efficiency and identify limits

#### Test 3.1: Memory Scaling
```
Test Scenario: Increasing part complexity and count
Monitor: Peak memory usage, memory leaks
Limits:
- Warning threshold: 512MB
- Critical threshold: 1GB
- Maximum recommended: 2GB
```

#### Test 3.2: Memory Stress Test
```
Scenario: Maximum realistic workload
Parts: 1000 rectangular + 100 complex shapes
Duration: 10 minutes continuous processing
Success Criteria: No memory leaks, stable performance
```

### 4. Algorithm Performance Tests

**Purpose:** Compare different nesting algorithms and modes

#### Test 4.1: Mode Comparison
```
Test Data: Mixed complexity parts (25 rectangular, 10 complex)
Modes Tested:
- Rectangular Mode: Force all parts as rectangles
- Geometric Mode: Full geometric processing
- Hybrid Mode: Automatic selection
- Auto Mode: System chooses optimal

Metrics:
- Processing time
- Material utilization
- Accuracy (overlap detection)
```

#### Test 4.2: Optimization Effectiveness
```
Test Scenarios:
- No optimization: Raw geometric processing
- Light optimization: Basic simplification
- Aggressive optimization: Maximum simplification
- Automatic optimization: System-managed

Success Criteria:
- < 20% performance degradation with optimization
- Maintained accuracy for critical features
- Graceful fallback behavior
```

## Benchmark Test Files

### Simple Complexity Tests

#### benchmark_simple_rectangles.py
```python
"""
Benchmark: Simple rectangular parts
Purpose: Baseline performance measurement
Parts: 100 rectangles, various sizes
Expected: Sub-second processing
"""

import time
from SquatchCut.core.complex_geometry import create_rectangular_geometry
from SquatchCut.core.geometry_nesting_engine import GeometryNestingEngine, SheetGeometry, NestingMode

def benchmark_simple_rectangles():
    # Create test parts
    parts = []
    for i in range(100):
        width = 100 + (i % 50) * 10  # 100-590mm widths
        height = 200 + (i % 30) * 15  # 200-635mm heights
        part = create_rectangular_geometry(f"rect_{i}", width, height)
        parts.append(part)

    # Setup nesting
    sheet = SheetGeometry(width=2440, height=1220, margin=5)
    engine = GeometryNestingEngine()

    # Benchmark nesting
    start_time = time.time()
    result = engine.nest_complex_shapes(parts, sheet, NestingMode.RECTANGULAR)
    end_time = time.time()

    # Report results
    processing_time = end_time - start_time
    utilization = result.utilization_percent

    print(f"Simple Rectangles Benchmark:")
    print(f"  Parts: {len(parts)}")
    print(f"  Processing Time: {processing_time:.3f}s")
    print(f"  Utilization: {utilization:.1f}%")
    print(f"  Parts Placed: {len(result.placed_geometries)}")

    # Performance assertions
    assert processing_time < 1.0, f"Processing too slow: {processing_time}s"
    assert utilization > 60, f"Poor utilization: {utilization}%"
    assert len(result.placed_geometries) > 80, "Too few parts placed"

    return {
        'processing_time': processing_time,
        'utilization': utilization,
        'parts_placed': len(result.placed_geometries)
    }

if __name__ == "__main__":
    benchmark_simple_rectangles()
```

#### benchmark_complex_shapes.py
```python
"""
Benchmark: Complex geometric shapes
Purpose: Measure geometric nesting performance
Parts: 25 complex polygons
Expected: 10-30 second processing
"""

import time
import math
from SquatchCut.core.complex_geometry import ComplexGeometry, ComplexityLevel, GeometryType
from SquatchCut.core.geometry_nesting_engine import GeometryNestingEngine, SheetGeometry, NestingMode

def create_complex_polygon(id_str, center_x, center_y, radius, vertices):
    """Create a complex polygon for testing."""
    contour = []
    for i in range(vertices):
        angle = 2 * math.pi * i / vertices
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        contour.append((x, y))
    contour.append(contour[0])  # Close contour

    # Calculate bounding box
    min_x = min(p[0] for p in contour)
    min_y = min(p[1] for p in contour)
    max_x = max(p[0] for p in contour)
    max_y = max(p[1] for p in contour)

    # Approximate area
    area = math.pi * radius * radius

    return ComplexGeometry(
        id=id_str,
        contour_points=contour,
        bounding_box=(min_x, min_y, max_x, max_y),
        area=area,
        complexity_level=ComplexityLevel.MEDIUM,
        rotation_allowed=True,
        geometry_type=GeometryType.COMPLEX
    )

def benchmark_complex_shapes():
    # Create test parts with varying complexity
    parts = []
    for i in range(25):
        vertices = 8 + (i % 20)  # 8-27 vertices
        radius = 50 + (i % 10) * 20  # 50-250mm radius
        part = create_complex_polygon(f"complex_{i}", 0, 0, radius, vertices)
        parts.append(part)

    # Setup nesting
    sheet = SheetGeometry(width=2440, height=1220, margin=10)
    engine = GeometryNestingEngine()

    # Benchmark nesting
    start_time = time.time()
    result = engine.nest_complex_shapes(parts, sheet, NestingMode.GEOMETRIC)
    end_time = time.time()

    # Report results
    processing_time = end_time - start_time
    utilization = result.utilization_percent

    print(f"Complex Shapes Benchmark:")
    print(f"  Parts: {len(parts)}")
    print(f"  Processing Time: {processing_time:.3f}s")
    print(f"  Utilization: {utilization:.1f}%")
    print(f"  Parts Placed: {len(result.placed_geometries)}")

    # Performance assertions
    assert processing_time < 60.0, f"Processing too slow: {processing_time}s"
    assert utilization > 50, f"Poor utilization: {utilization}%"
    assert len(result.placed_geometries) > 15, "Too few parts placed"

    return {
        'processing_time': processing_time,
        'utilization': utilization,
        'parts_placed': len(result.placed_geometries)
    }

if __name__ == "__main__":
    benchmark_complex_shapes()
```

### Memory Usage Tests

#### benchmark_memory_usage.py
```python
"""
Benchmark: Memory usage monitoring
Purpose: Track memory consumption patterns
Focus: Memory leaks, peak usage, efficiency
"""

import psutil
import os
import time
from SquatchCut.core.complex_geometry import create_rectangular_geometry
from SquatchCut.core.geometry_nesting_engine import GeometryNestingEngine, SheetGeometry, NestingMode

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def benchmark_memory_usage():
    initial_memory = get_memory_usage()
    peak_memory = initial_memory

    print(f"Memory Usage Benchmark:")
    print(f"  Initial Memory: {initial_memory:.1f}MB")

    # Test with increasing part counts
    for part_count in [100, 500, 1000, 2000]:
        print(f"\n  Testing {part_count} parts...")

        # Create parts
        parts = []
        for i in range(part_count):
            width = 100 + (i % 100) * 5
            height = 200 + (i % 50) * 10
            part = create_rectangular_geometry(f"part_{i}", width, height)
            parts.append(part)

        current_memory = get_memory_usage()
        print(f"    After creating parts: {current_memory:.1f}MB")

        # Run nesting
        sheet = SheetGeometry(width=2440, height=1220, margin=5)
        engine = GeometryNestingEngine()

        start_time = time.time()
        result = engine.nest_complex_shapes(parts, sheet, NestingMode.RECTANGULAR)
        end_time = time.time()

        current_memory = get_memory_usage()
        peak_memory = max(peak_memory, current_memory)

        print(f"    After nesting: {current_memory:.1f}MB")
        print(f"    Processing time: {end_time - start_time:.3f}s")
        print(f"    Utilization: {result.utilization_percent:.1f}%")

        # Clean up
        del parts
        del result

        # Force garbage collection
        import gc
        gc.collect()

        final_memory = get_memory_usage()
        print(f"    After cleanup: {final_memory:.1f}MB")

    print(f"\n  Peak Memory Usage: {peak_memory:.1f}MB")
    print(f"  Memory Increase: {peak_memory - initial_memory:.1f}MB")

    # Memory usage assertions
    assert peak_memory < 1024, f"Excessive memory usage: {peak_memory}MB"
    assert (peak_memory - initial_memory) < 512, "Potential memory leak detected"

    return {
        'initial_memory': initial_memory,
        'peak_memory': peak_memory,
        'memory_increase': peak_memory - initial_memory
    }

if __name__ == "__main__":
    benchmark_memory_usage()
```

## Performance Targets

### Processing Time Targets

| Part Count | Complexity | Target Time | Maximum Time |
|------------|------------|-------------|--------------|
| 10 | Simple | < 0.1s | 0.5s |
| 100 | Simple | < 1s | 5s |
| 1000 | Simple | < 10s | 30s |
| 10 | Complex | < 5s | 15s |
| 50 | Complex | < 30s | 120s |
| 100 | Complex | < 120s | 300s |

### Memory Usage Targets

| Scenario | Target Memory | Maximum Memory |
|----------|---------------|----------------|
| 100 simple parts | < 50MB | 100MB |
| 1000 simple parts | < 200MB | 500MB |
| 50 complex parts | < 300MB | 800MB |
| Mixed workload | < 400MB | 1GB |

### Utilization Targets

| Part Type | Target Utilization | Minimum Acceptable |
|-----------|-------------------|-------------------|
| Rectangles only | > 80% | 70% |
| Mixed complexity | > 75% | 65% |
| Complex shapes | > 70% | 60% |
| Highly complex | > 65% | 55% |

## Running the Benchmark Suite

### Prerequisites

```bash
# Install required packages
pip install psutil memory-profiler

# Set environment variables for testing
export SQUATCHCUT_BENCHMARK_MODE=1
export SQUATCHCUT_DEBUG_PERFORMANCE=1
```

### Execution

```bash
# Run individual benchmarks
python benchmark_simple_rectangles.py
python benchmark_complex_shapes.py
python benchmark_memory_usage.py

# Run complete suite
python run_all_benchmarks.py

# Generate performance report
python generate_performance_report.py
```

### Automated Testing

```python
# benchmark_runner.py
"""
Automated benchmark runner for CI/CD integration
"""

import subprocess
import json
import time
from datetime import datetime

def run_benchmark_suite():
    """Run all benchmarks and collect results."""
    results = {
        'timestamp': datetime.now().isoformat(),
        'benchmarks': {}
    }

    benchmarks = [
        'benchmark_simple_rectangles.py',
        'benchmark_complex_shapes.py',
        'benchmark_memory_usage.py'
    ]

    for benchmark in benchmarks:
        print(f"Running {benchmark}...")
        try:
            start_time = time.time()
            result = subprocess.run(['python', benchmark],
                                  capture_output=True, text=True, timeout=600)
            end_time = time.time()

            if result.returncode == 0:
                results['benchmarks'][benchmark] = {
                    'status': 'passed',
                    'execution_time': end_time - start_time,
                    'output': result.stdout
                }
            else:
                results['benchmarks'][benchmark] = {
                    'status': 'failed',
                    'error': result.stderr,
                    'output': result.stdout
                }
        except subprocess.TimeoutExpired:
            results['benchmarks'][benchmark] = {
                'status': 'timeout',
                'error': 'Benchmark exceeded 10 minute timeout'
            }

    # Save results
    with open('benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    results = run_benchmark_suite()

    # Print summary
    passed = sum(1 for r in results['benchmarks'].values() if r['status'] == 'passed')
    total = len(results['benchmarks'])

    print(f"\nBenchmark Summary: {passed}/{total} passed")

    if passed == total:
        print("All benchmarks passed!")
        exit(0)
    else:
        print("Some benchmarks failed!")
        exit(1)
```

## Performance Regression Testing

### Continuous Integration

```yaml
# .github/workflows/performance-tests.yml
name: Performance Benchmarks

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  performance:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
        pip install psutil memory-profiler

    - name: Run performance benchmarks
      run: |
        cd docs/examples/performance-benchmarks
        python benchmark_runner.py

    - name: Upload benchmark results
      uses: actions/upload-artifact@v2
      with:
        name: benchmark-results
        path: benchmark_results.json

    - name: Performance regression check
      run: |
        python check_performance_regression.py
```

### Regression Detection

```python
# check_performance_regression.py
"""
Check for performance regressions against baseline
"""

import json
import sys

def check_regression():
    # Load current results
    with open('benchmark_results.json', 'r') as f:
        current = json.load(f)

    # Load baseline (if exists)
    try:
        with open('baseline_performance.json', 'r') as f:
            baseline = json.load(f)
    except FileNotFoundError:
        print("No baseline found, creating new baseline")
        with open('baseline_performance.json', 'w') as f:
            json.dump(current, f, indent=2)
        return True

    # Check for regressions
    regressions = []

    for benchmark_name in current['benchmarks']:
        if benchmark_name not in baseline['benchmarks']:
            continue

        current_time = current['benchmarks'][benchmark_name].get('execution_time', 0)
        baseline_time = baseline['benchmarks'][benchmark_name].get('execution_time', 0)

        if baseline_time > 0:
            regression_percent = ((current_time - baseline_time) / baseline_time) * 100

            if regression_percent > 20:  # 20% regression threshold
                regressions.append({
                    'benchmark': benchmark_name,
                    'baseline_time': baseline_time,
                    'current_time': current_time,
                    'regression_percent': regression_percent
                })

    if regressions:
        print("Performance regressions detected:")
        for reg in regressions:
            print(f"  {reg['benchmark']}: {reg['regression_percent']:.1f}% slower")
            print(f"    Baseline: {reg['baseline_time']:.3f}s")
            print(f"    Current:  {reg['current_time']:.3f}s")
        return False
    else:
        print("No performance regressions detected")
        return True

if __name__ == "__main__":
    if not check_regression():
        sys.exit(1)
```

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4GB available
- **Storage**: 1GB free space
- **Python**: 3.8+

### Recommended Requirements
- **CPU**: 4+ cores, 3.0+ GHz
- **RAM**: 8GB+ available
- **Storage**: 5GB+ free space (for large test files)
- **Python**: 3.9+

### High-Performance Requirements
- **CPU**: 8+ cores, 3.5+ GHz
- **RAM**: 16GB+ available
- **Storage**: SSD with 10GB+ free space
- **Python**: 3.10+

## Interpreting Results

### Performance Analysis

**Good Performance Indicators:**
- Processing time scales linearly with part count
- Memory usage remains stable across runs
- Utilization consistently above targets
- No timeout errors or crashes

**Performance Warning Signs:**
- Exponential time scaling with complexity
- Memory usage continuously increasing
- Frequent fallback to simplified modes
- Utilization below minimum thresholds

**Critical Performance Issues:**
- Timeouts or crashes during processing
- Memory usage exceeding system limits
- Complete failure to place parts
- Severe performance degradation over time

### Optimization Recommendations

**For Slow Processing:**
1. Enable automatic simplification
2. Use hybrid nesting mode
3. Process in smaller batches
4. Upgrade hardware if needed

**For High Memory Usage:**
1. Reduce part complexity
2. Process fewer parts simultaneously
3. Enable garbage collection
4. Check for memory leaks

**For Poor Utilization:**
1. Adjust sheet sizes
2. Reduce margins and kerf
3. Group compatible parts
4. Try different nesting modes

---

*This benchmark suite provides comprehensive performance validation for SquatchCut v3.4+ shape-based nesting features.*
