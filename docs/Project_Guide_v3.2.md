# SquatchCut Project Guide (v3.2 – AI Agent Edition)

## 0. Meta Goals of v3.2

This updated guide focuses specifically on:

### **A. Eliminating ambiguity in AI Agent instructions**
- Instruction blocks now have strict, enforceable structure
- No markdown, no commentary inside blocks  
- Reasoning level declarations mandatory  
- File paths and expected patterns must be explicit  
- UI behavior described unambiguously  
- Persistent behavior safeguarded from accidental overwrites  

### **B. Making YOU faster and making ME (The User) more consistent**
- You describe requirements  
- I translate them into clear directives  
- The Agent executes

### **C. Forcing AI Agents to conform to SquatchCut’s architecture**
Agents should never reinvent the repo or introduce new patterns.

### AI Tooling & Workspace Layout
- Developers clone SquatchCut on the host and open `squatchcut.code-workspace`; this host-visible workspace is what AI tools discover.
- When “Reopen in Container” is used, VS Code bind-mounts the host repo at `/workspaces/SquatchCut`, so the container simply provides tooling while the canonical code stays on the host.
- See `docs/Development_Environment.md` for full AI-forward workflow details.
- **See also `AGENTS.md` in the root directory for strict behavioral rules.**

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

## **Architect (AI/Human)**
- Writes requirements  
- Produces Agent instruction blocks
- Ensures patterns and rules never drift  
- Maintains documentation  

## **AI Agent (Engineering Automaton)**
- Writes code  
- Must obey patterns  
- Must obey reasoning levels  
- Must never “guess”  
- Must build tests with every core change  
- **Must follow rules in `AGENTS.md`**

---

# 3. Core Principles

1. **Internal units = millimeters**  
2. **Imperial = fractional inches only**  
3. **Defaults never change unless Settings says so**  
4. **Presets never override defaults**  
5. **TaskPanel never auto-selects presets**  
6. **hydrate_from_params() ALWAYS runs before UI widgets**  
7. **Agents must use reasoning level declarations**
8. **Every logic change must include tests**  
9. **UI must not overflow or fail to load**  
10. **Settings panel must always open**  
11. **No relative imports**  
12. **No pattern drift**  
13. **No silent behavior changes**  

---

# 4. AI Agent Communication Rules (Updated + Hardened)

## 4.1 Instruction Block Format

Every instruction block MUST begin with:

```
Recommended reasoning level: <LEVEL>
```

Followed by:

```
Agent, this task requires <LEVEL> reasoning.

<instructions>
```

- No markdown  
- No language tag  
- No commentary  
- Only instructions  
- Must be safe to paste directly into the Agent

## 4.2 Required Elements Inside Each Block
- Full file paths  
- Explicit operation lists  
- Expected behavior  
- Acceptance criteria  
- Guardrails  

## 4.3 When to Use Levels
- LOW: trivial  
- MEDIUM: single-file  
- HIGH: multi-file + UI or settings  
- EXTRA-HIGH: architectural or algorithm refactor

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

Agents must ensure:

- Correct zip structure  
- Correct metadata  
- No relative imports  
- All icons exist  
- Version increments  

---

# 11. Export Architecture (v3.3 preparation)

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

# 12. Status & Backlog Addendum (Dec 2025)

> **NOTE**  
> This addendum does **not** change any core architectural rules.  
> It supersedes the older backlog-alignment section that followed the post-nesting fixes, providing a reconciled, status-aware view.  
> The information below reflects the current codebase (CSV ingestion, session-state hydration, multi-sheet helpers, guillotine engine, TaskPanel warning banner, and existing tests/backlog files).

---

## A. STATUS SNAPSHOT (DEC 2025)

### 1. Features & Stability
- Core CSV ingestion and session-state hydration flows remain stable and predictable.
- All four nesting strategies (default optimized, shelf, cut-friendly, guillotine) operate reliably under normal conditions.
- The normalized job-sheet helper in `freecad/SquatchCut/core/nesting.py` (~115–210) is the unified source of truth consumed by every strategy.
- The TaskPanel warning banner in `freecad/SquatchCut/gui/taskpanel_main.py` (~323–354) alerts users when cut-oriented modes may ignore additional sheets.
- Overall CSV → session → sheet normalization → nesting pipelines are cohesive and predictable.

### 2. Recently Refactored / Fragile Areas
- Multi-sheet heuristics (`freecad/SquatchCut/core/nesting.py` ~524–779) iterate sheet sizes but still lack per-sheet utilization metrics and user-visible exhaustion handling.
- The guillotine runner (`freecad/SquatchCut/core/cut_optimization.py` ~34–151) honors multi-sheet jobs yet has no per-sheet stats and can behave unexpectedly under aggressive exhaustion.
- Hydration/UI wiring integrated `_sheet_warning_active` via `_build_nesting_group` and `_update_cut_mode_sheet_warning`; changes must respect the hydration order.

### 3. Known or Likely Regressions
- **Preview vs Apply** (`freecad/SquatchCut/gui/taskpanel_main.py` ~840–869): Preview and Apply share the same destructive command path. Preview can mutate the document; TODO already notes need for a non-destructive channel.
- **CSV Export** (`freecad/SquatchCut/gui/commands/cmd_run_nesting.py` ~585–614): Export remains a stub. Menu items exist without producing real artifacts, potentially misleading users.

### 4. UI / UX Issues
- TaskPanel layout is crowded (Preview/Run/Show Source row + checkbox clusters, `freecad/SquatchCut/gui/taskpanel_main.py` ~333–353) causing clipping on narrow docks.
- The warning banner consumes full width with no adaptive fallback, increasing overflow risk in constrained layouts.

### 5. Testing Coverage & Gaps
- Full `pytest` sweeps collect ~171 tests but can time out (~120 s) in limited environments.
- Critical suites (`tests/test_nesting.py`, `tests/test_taskpanel_hydration.py`) pass, covering baseline nesting correctness and hydration behavior.
- Gaps remain for preview lifecycle vs apply, imperial formatting drift, sheet exhaustion behavior, warning-banner state transitions across permutations, and deep multi-sheet exhaustion edge cases.

### 6. Technical Debt & Documentation
- CSV export requires a complete implementation and deterministic cutlist output.
- Preview determinism needs a non-destructive workflow and clear cleanup of `SquatchCut_*` groups.
- Per-sheet visualization needs better labeling, spacing, and navigation aids.
- Documentation: v3.2 guide and `docs/Backlog.md` now track Completed/Active/Future work; this addendum aligns both with the live code.

---

## B. BACKLOG ALIGNMENT (SUPERSEDES OLD SECTION 11)

### 1. Completed Since v3.2
- **Settings Panel Behavior** – Opens reliably, hydrates before widget construction, leaves defaults untouched until explicit save.
- **Unified Job-Sheet Normalization** – `_normalize_sheet_definition` feeds every nesting strategy with the same sheet list.
- **Multi-Sheet Support Baseline** – Standard, cut-friendly, and guillotine strategies honor advanced job sheets with correct `sheet_index` tracking.
- **Warning Banner Infrastructure** – TaskPanel warning banner with `_sheet_warning_active` surfaces when cut-oriented modes ignore additional sheets.
- **Documentation & Backlog Files** – v3.2 guide and `docs/Backlog.md` were aligned to reflect the unified pipeline and warning logic.

### 2. Active Backlog (High Priority First)
- **P1 – Preview Determinism & Cleanup**  
  Separate preview from apply so preview is non-destructive; ensure `SquatchCut_Sheet_*`, `SquatchCut_SourceParts_*`, and `SquatchCut_NestedParts_*` stay consistent and cleaned up.  
  _Scope_: `freecad/SquatchCut/gui/taskpanel_main.py`, preview helpers/tests.

- **P1 – TaskPanel Overflow & Ergonomics**  
  Restructure crowded button/checkbox rows to prevent clipping on narrow docks, ensuring the warning banner coexists without overflow.  
  _Scope_: `freecad/SquatchCut/gui/taskpanel_main.py`.

- **P1 – Multi-Sheet Visualization Polish**  
  Improve per-sheet labeling, spacing, and navigation within the viewer; keep sheet/source/nested groups synchronized without ghosts.  
  _Scope_: `freecad/SquatchCut/gui/nesting_view.py`, `freecad/SquatchCut/core/view_controller.py`.

- **P1 – Cut-Friendly Multi-Sheet Heuristics**  
  Refine lane/guillotine behavior so sheet order, exhaustion, and spacing are predictable.  
  _Scope_: `freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/core/cut_optimization.py`.

- **P1 – Test Suite Expansion (Hydration, Units, Preview)**  
  Add tests for measurement toggles, fractional-inch formatting, preview lifecycle, sheet_index propagation, and basic exhaustion scenarios.  
  _Scope_: `tests/test_taskpanel_hydration.py`, new multi-sheet/preview suites.

- **P2 – CSV Export & Cutlist Determinism**  
  Replace the export stub with real cutlist generation and document the format.  
  _Scope_: `freecad/SquatchCut/gui/commands/cmd_run_nesting.py` + helpers.

- **P2 – Warning Banner Lifecycle Tests**  
  Ensure banner visibility/text reacts to nesting-mode, job-sheet, and unit-system changes.  
  _Scope_: `freecad/SquatchCut/gui/taskpanel_main.py`, UI tests.

- **P2 – Sheet Exhaustion Metrics & Feedback**  
  Surface when sheet quantities run out (logs/UI) and avoid silent truncation.  
  _Scope_: nesting core + TaskPanel feedback.

### 3. Future / Longer-Term
- **Per-Sheet Cut-Order Visualization** – Visual guide for rip/crosscut sequences per sheet.
- **Enhanced Sheet Exhaustion Metrics** – Utilization percentages and unused vs used counts.
- **Multi-Sheet Presets** – Configurable sheet stacks as presets compatible with measurement rules.
- **Kerf Simulation** – Saw-specific kerf modeling tied into both packing and cut-friendly heuristics.

---

## C. HOW TO USE THIS ADDENDUM
- The core v3.2 architectural rules remain authoritative.
- This addendum synchronizes the v3.2 guide and `docs/Backlog.md` with real status/backlog data.
- Future architectural or backlog changes must update both the main guide (or successor) and this alignment layer, keeping architecture, status, and backlog clearly separated.

---

# 13. Development Rules Summary

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

# 13. Changelog Strategy for v3.2

- Add v3.2 section
- Note settings fixes, hydration rules, UI rules, Agent reinforcement
- Bump version to 0.3.2
- Include explicit references to v3.2 documentation
- Record that backlog/status alignment was refreshed (Completed vs. Active vs. Future) and mirrored into docs/Backlog.md
- Document the AI-forward development workflow (host-cloned repo, bind-mounted dev container, canonical `.code-workspace`)
- Added v3.3 Roadmap section describing required deliverables for FreeCAD Add-On Manager readiness and release planning.

---

# 14. Roadmap for v3.3 – FreeCAD Add-On Release Candidate

v3.3 is a stabilization and polish release aimed at making SquatchCut ready for the FreeCAD Add-On Manager.
No new “hero features” are allowed unless they directly support stability, usability, or Add-On compliance.

## 14.1 v3.3 Goals
- Deliver a non-destructive, deterministic nesting workflow.
- Eliminate UI overflow issues in the TaskPanel.
- Polish multi-sheet visualization and eliminate ghost objects.
- Implement a fully functional CSV export path.
- Surface sheet-exhaustion metrics and warnings.
- Achieve full Add-On Manager compliance.
- Update user docs and include example CSVs.

## 14.2 Phase 1 – Critical Completion (Release Blockers)
[INSERT ALL SUBSECTIONS EXACTLY AS PROVIDED BY ARCHITECT AI]

## 14.3 Phase 2 – Core Features Required for Release
[INSERT ALL SUBSECTIONS EXACTLY AS PROVIDED BY ARCHITECT AI]

## 14.4 Phase 3 – Add-On Manager Readiness
[INSERT ALL SUBSECTIONS EXACTLY AS PROVIDED BY ARCHITECT AI]

## 14.5 Phase 4 – Optional Items (Candidates for v3.4)
[INSERT ALL SUBSECTIONS EXACTLY AS PROVIDED BY ARCHITECT AI]

## 14.6 v3.3 Exit Criteria
[INSERT ALL SUBSECTIONS EXACTLY AS PROVIDED BY ARCHITECT AI]

# END OF SquatchCut Project Guide v3.2
