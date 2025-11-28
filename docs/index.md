# SquatchCut (logo placeholder)

SquatchCut is a cryptid-powered nesting workbench for FreeCAD that extracts panels, nests them, and exports reports.

## Key Features
- FreeCAD workbench with panel extraction and nesting
- CSV import (optional per-part rotation) and TypeScript validation tools
- Multi-sheet rectangular nesting with kerf/gap controls and per-part 0°/90° rotation
- Geometry generation and PDF/CSV reporting plus manual “Export Nesting CSV” dialog
- Embedded Codex workflows for guided development

## Workflow Notes
- CSV import shows source panel rectangles in the XY plane and fits the view automatically.
- Preview/Apply nesting hides source panels and builds fresh sheets + nested clones each run (older sheets are cleared first).
- Use the “Show Source Panels” button in the task panel to hide sheets and reveal sources again at any time.

## Explore
- [Getting Started](getting-started/installation.md)
- [User Guide](user/commands.md)
- [Developer Guide](architecture.md)
