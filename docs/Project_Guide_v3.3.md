# SquatchCut Project Guide (v3.3 – AI Tool-Agnostic Edition)

## 0. Meta Goals of v3.3

This updated guide focuses on:

### **A. AI-Tool Agnosticism**
- Removes dependencies on specific AI brands (e.g., "Codex").
- Defines roles generically (Architect, AI Worker).
- Clarifies that ANY AI tool (VS Code assistant, GitHub agent, etc.) must follow the specs.

### **B. Eliminating ambiguity in AI Worker instructions**
- Instruction blocks now have strict, enforceable structure.
- No markdown, no commentary inside blocks.
- Reasoning level declarations mandatory.
- File paths and expected patterns must be explicit.
- UI behavior described unambiguously.
- Persistent behavior safeguarded from accidental overwrites.

### **C. Making YOU faster and making ME (The User) more consistent**
- You describe requirements.
- I translate them into clear directives.
- The AI Worker executes.

### **D. Forcing AI Workers to conform to SquatchCut’s architecture**
Workers should never reinvent the repo or introduce new patterns.

---

# 1. Project Purpose

SquatchCut is a FreeCAD add-on that takes CSV part lists and generates optimized sheet nests for woodworking, cabinetry, and general sheet-material workflows.

### Core Objectives
- Fast, predictable, simple
- Minimal UI friction
- Always mm internally, fractions if imperial
- Stable hydration/initialization
- Simple CSV → sheet → nest → export workflow

---

# 2. Roles

## **User (Steven)**
- Product Owner
- Scrum-ish Master
- UAT wrangler
- Requirements authority

## **Architect (Human + Planner)**
- Writes requirements
- Produces Task Specs (Job Cards); all tasks must originate here
- Ensures patterns and rules never drift
- Maintains documentation

## **Lead Developer (e.g., Jules)**
- Plans implementation from Architect specs
- Manages the repository and branch strategy
- Reviews code from other workers

## **AI Workers (Implementation Agents)**
- Implement code changes based on strict specs
- Can be any tool (e.g., Codex, GitHub Copilot, custom agents)
- **Branching:** Each worker gets its own branch (e.g., `worker/<feature>`); no two workers modify the same core file set in parallel.
- Must obey patterns and reasoning levels
- Must build tests with every core change
- **See `AGENTS.md` → AI Worker Protocol for full details**

---

# 3. Core Principles

1. **Internal units = millimeters**
2. **Imperial = fractional inches only**
3. **Defaults never change unless Settings says so**
4. **Presets never override defaults**
5. **TaskPanel never auto-selects presets**
6. **hydrate_from_params() ALWAYS runs before UI widgets**
7. **Workers must use reasoning level declarations**
8. **Every logic change must include tests**
9. **UI must not overflow or fail to load**
10. **Settings panel must always open**
11. **No relative imports**
12. **No pattern drift**
13. **No silent behavior changes**

---

# 4. AI Worker Communication Rules

## 4.1 Task Spec Format

Every task spec assigned to an AI worker must follow a clear block format (often called a "Job Card" or "Codex Block"):

```
@worker
Title: <Short Task Name>
File: <Target File Path>
Action: <Implement/Refactor/Fix>
Context: <Brief explanation of what to do>
Rules:
- <Constraint 1>
- <Constraint 2>
```

- No markdown inside the block
- Only instructions
- Must be safe to paste directly into the AI tool

## 4.2 Required Elements Inside Each Block
- Full file paths
- Explicit operation lists
- Expected behavior
- Acceptance criteria
- Guardrails

## 4.3 Reasoning Levels
- **LOW:** Trivial changes (typos, small fixes).
- **MEDIUM:** Single-file logic changes.
- **HIGH:** Multi-file changes, UI updates, or settings logic.
- **EXTRA-HIGH:** Architectural refactors or algorithm changes.

## 4.4 Git Workflow
- **Branching:**
  - Lead Developer: `jules/<feature>` (or similar)
  - AI Workers: `worker/<feature>`, `codex/<feature>`, or `agent/<feature>`
  - **Rule:** Each worker must use a unique branch. Do not share branches between active workers.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`)
- **PRs:** Required for all changes. Must be reviewed by the Lead Developer.

---

# 5. Hydration Rules (Hard Requirements)

Hydration has caused repeated issues. These rules are absolute:

### **5.1 hydrate_from_params() must:**
- Load all persistent values
- Guarantee type consistency
- Normalize internal units
- Never access GUI
- Never import GUI modules
- Never modify defaults except on Settings save

### **5.2 TaskPanel Initialization Order**
This order is non-negotiable:

1. Load session_state
2. Call hydrate_from_params()
3. Create all UI widgets
4. Populate UI values from hydrated state
5. Apply measurement formatting
6. Connect signals
7. Render panel

No exceptions.

---

# 6. Measurement System Architecture

### 6.1 Internal Storage
Always millimeters.

### 6.2 Display Modes
- metric → mm
- imperial → fractional inches

### 6.3 UI Reformatting Rules
Switching measurement system requires full reformatting of all numeric UI fields.

### 6.5 Split Defaults (New)
To prevent drift from rounding errors:
- User-configurable defaults (Sheet size, Kerf, Gap) must be stored separately for Metric and Imperial.
- Switching systems in Settings swaps the loaded default, it does not convert/overwrite the existing one.

### 6.4 Fraction Logic
Must support:
- whole
- fraction
- mixed
- hyphenated
Must round-trip without drift.

---

# 7. Preset & Default Logic (Fortified)

### **Defaults**
- Set only via Settings panel
- Never altered by TaskPanel
- Hydrate_from_params loads them

### **Presets**
- Always start blank
- Only modify sheet width/height
- Never modify defaults
- Never auto-selected

### **Imperial Default Sheet**
Exactly **48 × 96 inches**.

---

# 8. UI Behavior Rules

### 8.1 Settings Panel
- Must always open
- Must use TaskPanel_Settings
- Must call hydrate_from_params() before building widgets

### 8.2 Main TaskPanel
- Acts as a Controller for sub-widgets (`Input`, `Sheet`, `Nesting`).
- Must reflect hydrated defaults.
- Must not override defaults.
- Must not infer presets.
- Must not open multiple instances.

### 8.3 Sheet/Source/Nesting View Rules
- Clear groups before redraw
- Never leave orphans
- Auto-zoom after draw
- Maintain consistent naming:
  - SquatchCut_Sheet
  - SquatchCut_SourceParts
  - SquatchCut_NestedParts

---

# 9. Tests

### 9.1 Must Test
- Fraction parsing
- Fraction formatting
- CSV parsing
- Default initialization
- Hydration logic
- Preset behavior
- TaskPanel load behavior
- Measurement-system conversions

### 9.2 Should Test
- Sheet object creation
- Group clearing
- UI stability (when possible)

---

# 10. Add-On Manager Rules

Workers must ensure:

- Correct zip structure
- Correct metadata
- No relative imports
- All icons exist
- Version increments

---

# 11. Export Architecture

## 11.1 Canonical Export Data Model
- `freecad/SquatchCut/core/exporter.py` defines the only valid export model:
  - `ExportJob` – job-wide metadata + sheets, measurement system, job name.
  - `ExportSheet` – sheet index, width/height in mm, list of part placements.
  - `ExportPartPlacement` – per-part geometry (x_mm, y_mm, width_mm, height_mm, rotation_deg) and part_id.
- ExportJob is built from the latest nesting layout + sheet config via `build_export_job_from_current_nesting`.
- **All geometry is stored in millimeters.** Measurement system only affects formatted strings.

## 11.2 Deterministic Export Behavior
- **CSV export (`export_cutlist`)**
  - Emits stable header columns (sheet_index, mm geometry, formatted strings).
  - Raw mm values are untouched. `width_display/height_display` respect ExportJob.measurement_system.
  - Tests cover both metric and imperial output.
- **SVG export (`export_nesting_to_svg`)**
  - Generates one 2D SVG per sheet; filenames include `_S{n}` suffix.
  - Draws sheet border, stroke-only part rectangles, deterministic labels (ID + dimensions), and header “Sheet i of N – WxH units”.
  - No FreeCAD 3D/export calls; everything is generated from ExportJob data.
- **Design Principle:** Export behavior must be deterministic and driven solely by ExportJob. FreeCAD document geometry is never a source of truth for exported artifacts.

## 11.3 Out-of-scope
- DXF export remains deferred. Implementing DXF is explicitly out of scope for the current release cycle and cannot block delivery.

---

# 12. Development Rules Summary

1. Internal unit = mm
2. Imperial UI = fractions only
3. Defaults remain unchanged except in Settings
4. Presets never overwrite defaults
5. TaskPanel never auto-selects presets
6. Hydration before UI
7. Agents must use reasoning levels
8. Tests accompany logic changes
9. UI must never overflow
10. Settings panel must open
11. No relative imports
12. No silent assumptions
13. No redesigns without explicit instructions

---

# 13. Changelog Strategy for v3.3

- **v3.3 (Current):**
  - Introduces AI-tool-agnostic worker model (Architect + AI Workers).
  - Clarifies AI workflow and refreshes backlog guidance.
  - Resets backlog to align with current architecture.
- **v3.2:**
  - Multi-sheet nesting & production readiness.
  - Settings fixes, hydration rules, UI rules.
