# Architecture

This document defines the technical architecture of the SquatchCut FreeCAD Nesting Workbench MVP. It outlines the project structure, module responsibilities, data flow, and Codex conventions to ensure consistent implementation.

---

# 1. Project Structure

The repository is organized as follows:

root/
│
├── freecad/
│ └── SquatchCut/
│ ├── InitGui.py
│ ├── init.py
│ ├── gui/
│ │ ├── commands/
│ │ │ ├── cmd_add_shapes.py
│ │ │ ├── cmd_import_csv.py
│ │ │ ├── cmd_run_nesting.py
│ │ │ ├── cmd_set_sheet_size.py
│ │ │ ├── cmd_export_report.py
│ │ │ └── cmd_preferences.py
│ │ └── dialogs/
│ │ ├── dlg_select_shapes.py
│ │ ├── dlg_csv_import.py
│ │ ├── dlg_sheet_size.py
│ │ ├── dlg_run_nesting.py
│ │ └── dlg_export_report.py
│ │
│ ├── core/
│ │ ├── shape_extractor.py
│ │ ├── csv_loader.py
│ │ ├── nesting_engine.py
│ │ ├── multi_sheet_optimizer.py
│ │ ├── geometry_output.py
│ │ ├── report_generator.py
│ │ └── preferences.py
│ └── resources/
│ ├── icons/
│ └── ui/
│
└── docs/
├── mvp.md
├── architecture.md
└── roadmap.md

---

# 2. Module Responsibilities

## 2.1 `/core` modules

### **shape_extractor.py**

- Scans FreeCAD document for valid shapes
- Extracts bounding boxes (width, height)
- Converts shapes to panel objects
- Enforces rotation rules
- Filters by user selection

### **csv_loader.py**

- Loads CSV into panel objects
- Validates fields
- Normalizes types and units
- Produces list of panels

### **nesting_engine.py**

- Implements rectangular nesting (Skyline or Guillotine)
- Places panels at (x, y) with rotation
- Detects collisions + boundaries
- Produces placements for one sheet

### **multi_sheet_optimizer.py**

- Uses nesting_engine repeatedly
- Allocates panels across sheets
- Stops when all panels placed
- Returns a list of sheets + placements

### **geometry_output.py**

- Creates FreeCAD geometry for each sheet
- Adds groups and rectangles
- Applies x, y placement, rotation, and labeling

### **report_generator.py**

- Builds a PDF summary:
  - Sheet count
  - Panel placements
  - Efficiency / waste %
  - Timestamp
- Builds CSV summary

### **preferences.py**

- Wraps FreeCAD preference system
- Stores:
  - Default sheet size
  - Kerf/spacing
  - Rotation allowed
  - Auto-detect shapes
  - Export directory
  - Branding toggle

---

# 3. GUI Layer

## 3.1 Workbench Setup

### `InitGui.py`

- Registers SquatchCut workbench
- Adds toolbar buttons
- Loads icons

### `__init__.py`

- Metadata
- Bootstrapping

## 3.2 Commands

Each command lives inside `/gui/commands`:

- `cmd_add_shapes.py`
- `cmd_import_csv.py`
- `cmd_run_nesting.py`
- `cmd_set_sheet_size.py`
- `cmd_export_report.py`
- `cmd_preferences.py`

Commands:

- Call dialogs
- Trigger core functions
- Update UI

## 3.3 Dialogs

Each dialog in `/gui/dialogs` handles user input:

- Select shapes
- Import CSV
- Sheet size configuration
- Nesting run settings
- Export settings

Dialogs emit structured data for core modules.

---

# 4. Data Model

### Panel Object

{
"id": str,
"width": float,
"height": float,
"rotation_allowed": bool,
}

### Placement Object

{
"panel_id": str,
"x": float,
"y": float,
"rotation": int, # 0 or 90
"sheet_id": int
}

### Sheet Object

{
"sheet_id": int,
"width": float,
"height": float,
"placements": list[Placement]
}

---

# 5. Data Flow

FreeCAD Shapes ──────► shape_extractor
CSV File ──────► csv_loader

Extracted Panels
▼
multi_sheet_optimizer
▼
nesting_engine (per sheet)
▼
Sheet Placement Sets
▼
geometry_output ──► FreeCAD Document
report_generator ──► PDF / CSV

---

# 6. Codex Conventions

Codex must follow these rules when generating code:

### 6.1 Use `@codex` blocks

Example:

```python
"""
@codex
Implement the NestingEngine class.
Requirements:
- Do not use recursion.
- Accept list of panels + sheet size.
- Return list of placements.
"""
6.2 Avoid global state
Modules must be pure where possible.

6.3 Small functions
Break complex logic into testable units.

6.4 FreeCAD imports must be lazy
import FreeCAD as App
import FreeCADGui as Gui

6.5 Use unified logging
from .preferences import log

7. Future Expansion (Post-MVP Hooks)
Architecture reserves space for:
Bookmatching
Grain direction optimization
Curved/polygon nesting
Advanced nesting heuristics
Path Workbench integration
Material libraries
Drag-and-drop sheet editing
These will attach cleanly onto existing modules without rewriting MVP code.
```
