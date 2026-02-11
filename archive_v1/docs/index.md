# SquatchCut (logo placeholder)

SquatchCut is a cryptid-powered nesting workbench for FreeCAD that extracts panels, nests them, and exports reports.

**Status:** 0.3.x release line focuses on CSV/rectangular nesting. Shape-based nesting is available as an experimental preview (longer runs, feedback welcome). Tested on FreeCAD 0.21+.

## Key Features

### Traditional CSV Workflow
- FreeCAD workbench with panel extraction and nesting
- CSV import (optional per-part rotation) and TypeScript validation tools
- Multi-sheet rectangular nesting with kerf/gap controls and per-part 0°/90° rotation
- Fast processing for production runs and standard rectangular parts

### Shape-Based Nesting (Experimental Preview)
- **True Geometric Nesting**: Design complex parts directly in FreeCAD
- **Maximum Material Utilization**: Nest curved, angled, and detailed shapes efficiently
- **Accurate Shape Processing**: Considers actual part geometry, not just bounding boxes
- **Intelligent Mode Selection**: Automatically chooses optimal nesting algorithm
- **Export Support**: CSV/SVG/DXF exports generated through the SquatchCut exporter

### Common Features
- Units preference (metric/imperial) and CSV units selector; sheet size fields reflect the chosen units
- Geometry generation, PDF/CSV reporting, and cutlist CSV export from nested layouts
- Performance helpers for complex shapes and large datasets
- Embedded AI worker workflows (Codex-style prompts) for guided development

## Workflow Notes
- CSV import shows source panel rectangles in the XY plane and fits the view automatically.
- Preview/Apply nesting hides source panels and builds fresh sheets + nested clones each run (older sheets are cleared first).
- Use the **Show Source View** button in the task panel to hide sheets and reveal sources again at any time.
- Cutlist export derives rip/crosscut lines from the nested layout and now merges near-duplicate edges while ignoring cuts that don’t cross any panel, keeping the cutlist shop-friendly.

## Explore

### Getting Started
- [Installation Guide](getting-started/installation.md)
- [Basic Workflow](getting-started/workflow.md)
- [Quick Start Guide](quickstart.md)

### User Documentation
- [Complete User Guide](user_guide.md) - Traditional CSV and shape-based workflows
- [Cabinet Maker Workflow Guide](user/cabinet-maker-workflow.md) - Shape-based nesting for furniture makers
- [Technical Reference](user/shape-based-nesting-reference.md) - Advanced configuration and API documentation
- [Commands Reference](user/commands.md)

### Examples and Samples
- [Cabinet Projects](examples/cabinet-projects/face-frame-example.md) - Complete workflow examples
- [CSV Examples](examples/csv-examples/traditional-workflow-samples.md) - Traditional workflow samples
- [Performance Benchmarks](examples/performance-benchmarks/complexity-test-suite.md) - Testing and optimization

### Developer Resources
- [Developer Guide](architecture.md)
- [Project Guide v3.3 (archived)](archive/Project_Guide_v3.3.md)
- [AI Workflows](ai_workflows.md)
