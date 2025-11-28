# SquatchCut
### A cryptid-powered sheet optimization workbench for FreeCAD  
**Status: Beta – Work in progress. Expect breaking changes and incomplete features.**

## Overview
SquatchCut is a FreeCAD workbench for optimizing rectangular sheet goods. It provides a single Task panel where you configure sheets, load a parts CSV, choose an optimization strategy (material vs cuts), and run nesting. The workbench is Python-based with no external solver dependencies.

## Features
- Consolidated Task panel for sheet setup, CSV import, optimization mode, and nesting actions.
- Two optimization modes:
  - Material (minimize waste / maximize yield).
  - Cuts (row/column heuristic to approximate fewer saw cuts).
- Result summary after nesting: sheets used, estimated utilization, estimated cut count, unplaced parts.
- Supports kerf, margins, and rotation options (default or per-part CSV flag).
- FreeCAD geometry output with per-sheet groups; export commands remain available.

## Documentation
- https://stevenfarmer.github.io/SquatchCut/

## Installation
- Clone this repo into your FreeCAD `Mod` directory:
  - Linux/macOS: `~/.local/share/FreeCAD/Mod/`
  - Windows: `%APPDATA%\\FreeCAD\\Mod\\`
- Restart FreeCAD and choose **SquatchCut** from the Workbench selector. The main toolbar shows a single SquatchCut button to open the Task panel.

## Usage
1. Open FreeCAD and activate the SquatchCut workbench.
2. Click the main **SquatchCut** toolbar button to open the Task panel.
3. Configure sheet size, kerf, and margins (use presets or custom values).
4. Load a parts CSV (see format below). The nesting buttons enable once parts are loaded.
5. Choose optimization mode:
   - Material: prioritize yield.
   - Cuts: align parts into rows/columns to approximate fewer saw cuts.
6. Click **Preview Nesting** or **Apply to Document**.
7. Review the Results section: sheets used, utilization %, estimated cuts, and unplaced parts.

## CSV Format
- Required columns: `id`, `width`, `height`
- Optional: `qty`, `label`, `material`, `allow_rotate`
- Units: millimeters
- Invalid rows are skipped; errors are reported to the console/dialogs.

## Status & Limitations
- **Beta / in progress**: behavior and APIs may change; features may be incomplete.
- The “cuts” optimization mode is heuristic and does **not** guarantee the true minimum number of cuts.
- Error handling and edge cases are improving; please report issues you encounter.

## Testing
- Python core tests (recommended):
  - `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt`
  - `PYTHONPATH=freecad .venv/bin/pytest --cov=SquatchCut.core.nesting --cov=SquatchCut.core.session_state --cov-report=term-missing --cov-fail-under=80`
- Additional FreeCAD E2E tests exist under `freecad/testing/` for manual runs inside FreeCAD.

## Contributing / Feedback
- Issues and PRs are welcome. This project is in active development—open an issue before large changes.
- See `CONTRIBUTING.md` for guidelines, testing commands, and notes on adding new optimization strategies.
