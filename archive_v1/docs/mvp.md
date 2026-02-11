# MVP Scope

FreeCAD Nesting Workbench
Version: MVP Specification
Author: Steven + ChatGPT

---

# 🎯 MVP Overview

SquatchCut is a FreeCAD Workbench that extracts 2D shapes from a user's active project, nests them across multiple sheets using rectangular optimization, generates layout geometry inside FreeCAD, and exports a full PDF/CSV report. CSV import is supported as a fallback, but the primary workflow is extracting geometry from FreeCAD.

This document defines the locked, non-negotiable MVP requirements.

---

# 🟩 1. Shape Extraction From FreeCAD (Primary Input)

MVP must extract panel geometry directly from the active FreeCAD document.

Supported sources:

- Sketcher sketches (closed profiles)
- Draft rectangles, polygons, and shapes
- Part::Box (projected to 2D bounding rectangle)
- Part::Feature objects with planar faces

Extract for each shape:

- Width and height
- Bounding box in global XY
- Rotation allowed (true/false)
- Unique ID
- Naming from label or auto-generated

User workflow:

- Select shapes → Click “Add Selected to Nesting”
- Or auto-detect 2D shapes → present selectable list

CSV is a fallback, not the primary method.

---

# 🟩 2. CSV Import (Fallback Mode)

CSV must support:

Required fields:

- id
- width
- height

Optional fields:

- allow_rotate (1/true/yes to permit 90° rotation)

CSV validation:

- Reject zero or negative values
- Reject missing fields
- Human-readable error messages

Users may optionally combine CSV-defined panels with FreeCAD geometry.

---

# 🟩 3. Multi-Sheet Nesting (Mandatory)

The MVP must support **multi-sheet optimization**.

Required behaviors:

- User defines sheet size (width, height)
- Algorithm places as many panels per sheet as possible
- Generates new sheets when full
- Continues until all panels are placed

Algorithm:

- Skyline or Guillotine rectangular nesting
- Rotation allowed only at 0° or 90°
- Sorting strategies to reduce waste:
  - Largest-first
  - Height-first
  - Width-first
    (Meta-optimization optional: random shuffles for better pack)

Output per placement:

- panel_id
- sheet_id
- x, y position
- rotation (0 or 90)

---

# 🟩 4. FreeCAD GUI Integration (Workbench)

The SquatchCut Workbench must add a toolbar with the following commands:

- **Add Shapes to Nesting**
- **Import CSV**
- **Set Sheet Size**
- **Run Nesting**
- **Preferences**
- **Export Report**

Required dialogs:

- Shape selection dialog
- CSV import dialog
- Sheet size dialog
- Nesting results dialog
- Report export dialog

Design: simple but functional, no fancy styling required.

---

# 🟩 5. Preferences Pane (Mandatory)

FreeCAD preferences window must include:

- Default sheet width/height
- Default kerf/spacing between panels
- Auto-detect shapes on open (yes/no)
- Allow rotations (yes/no)
- Default export directory
- Branding toggle (Sasquatch mode on/off)

Preferences must persist across sessions.

---

# 🟩 6. Nesting Report Export (Mandatory)

After nesting, SquatchCut must export a structured report.

Report includes:

- Date/time
- FreeCAD project name (if available)
- Total number of sheets used
- Total panels
- Total material area
- Total waste (%)
- Efficiency (%)

Per sheet:

- Sheet number
- Sheet dimensions
- List of placements:
  - panel_id
  - width
  - height
  - rotation
  - x, y placement

Output formats:

- **PDF** (primary)
- CSV summary (per-panel table)
- JSON optional but not required

PDF may use ReportLab or FreeCAD’s own export mechanisms.

---

# 🟩 7. Nesting Geometry Output in FreeCAD

For each sheet produced, SquatchCut must:

- Create a new FreeCAD group (Sheet_1, Sheet_2, etc.)
- Add Draft rectangles (or Sketch Rectangles) representing final panel positions
- Apply rotation, placement, and IDs
- Maintain consistent units (mm)
- Maintain accurate geometry

Optional but helpful:

- Color code rectangles

---

# 🟩 8. Branding (Required)

MVP must include:

- Workbench icon (Squatch/wood ape theme)
- Toolbar icons
- “SquatchCut” name visible in UI
- Optional “Sasquatch Mode” toggle in preferences

Branding is a first-class MVP requirement.

---

# 🟥 Excluded From MVP

The following features are intentionally **excluded**:

- Curved or arbitrary-shape polygon nesting
- FreeCAD Path Workbench integration (CAM, G-code)
- Grain direction optimization
- Bookmatching
- Advanced optimization algorithms (GA, deep nesting)
- Drag-and-drop sheet editor
- Material libraries
- Collaborative/cloud features

These belong in post-MVP roadmap releases.

---

# 🟩 MVP Summary in One Sentence

SquatchCut MVP provides a FreeCAD workbench that extracts 2D shapes from the active project (or CSV fallback), nests them across multiple sheets using rectangular optimization, generates corresponding geometry inside FreeCAD, and exports a full PDF report with sheets, placements, and efficiency metrics.

---

# End of MVP Document
