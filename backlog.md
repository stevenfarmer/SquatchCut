# SquatchCut Backlog (v3.4+)

**Status:** v3.3 Complete - Moving to v3.4 Shape-Based Nesting
**Focus:** Enhanced FreeCAD Integration, Non-Rectangular Nesting, and Cabinet Maker Workflows.
**Versioning note:** The codebase is on the 0.3.x line (see `freecad/SquatchCut/version.py`); backlog labels keep the historical v3.x naming for roadmap grouping.

---

## Major Feature Development

### Shape-Based Nesting (v3.4) - **IN DEVELOPMENT**
- `[SPEC COMPLETE]` **Comprehensive Shape-Based Nesting System**
  - Full specification created in `.kiro/specs/shape-based-nesting/`
  - 8 user stories, 40 acceptance criteria, 44 implementation tasks
  - Enhanced FreeCAD object detection and selection workflows
  - Non-rectangular nesting with true geometric accuracy
  - Cabinet maker workflow from FreeCAD design to cutting layouts
  - *Status:* Ready for implementation - see tasks.md for execution plan
- `[AI]` **Reduce Hypothesis Filtering in Shape-Based Tests**
  - Refine `valid_complex_geometry` strategy to lower discard rate instead of suppressing health checks.
  - Goal: Keep property coverage while satisfying Hypothesis filtering thresholds.

---

## 1. Core Engine & Nesting

- `[AI]` **Refine Multi-Sheet Heuristics**
  - Current multi-sheet logic iterates sheet sizes but lacks per-sheet utilization metrics.
  - *Goal:* Improve packing density and surfacing of waste metrics.

- `[AI]` **Guillotine Optimization**
  - The guillotine engine needs better handling of sheet exhaustion edge cases.
  - *Goal:* Predictable behavior when parts exceed available sheets.

- `[MIXED]` **Kerf Simulation**
  - Model saw-specific kerf widths in packing.
  - *Goal:* Accurate "cut-ready" layouts.

## 2. Units, Sheets, & Measurement Systems

- `[AI]` **Imperial Formatting Drift**
  - Ensure fractional inch values round-trip perfectly without micro-drift.
  - *Goal:* 100% stable unit conversion tests.

- `[AI]` **Sheet Exhaustion Metrics**
  - Detect and communicate when configured sheet quantities run out.
  - *Goal:* Clear feedback in logs/UI (used vs. available).

## 3. GUI & UX

- `[AI]` **Preview vs. Apply Separation**
  - "Preview" currently mutates the document. It should be non-destructive.
  - *Goal:* Separate visual preview layer that cleans up automatically.

- `[AI]` **TaskPanel Overflow**
  - The button rows and warning banner clip on narrow docks.
  - *Goal:* Responsive layout or better grouping (e.g., scroll area).

- `[HUMAN]` **Multi-Sheet Visualization Polish**
  - Better labeling and navigation for sheet stacks in the 3D view.
  - *Goal:* User can clearly see which sheet is which.

- `[AI]` **Warning Banner Lifecycle**
  - Ensure the warning banner updates correctly when modes/units change.
  - *Goal:* Banner never gets stuck "on".

- `[HUMAN]` **Surface Build Version & Experimental Labels**
  - Users see mixed version numbers (0.3.x vs v3.x) and no in-product indicator that shape-based nesting is preview-only.
  - *Goal:* Show the installed build version in the UI (toolbar/settings) and mark shape-based flows as **Experimental** to set expectations.

## 4. Exports (CSV/SVG/DXF)

- `[AI]` **CRITICAL: Export Measurement System Issues**
  - SVG and CSV exports default to metric even when project is in imperial
  - CSV export ignores project measurement system setting
  - *Goal:* All exports respect project measurement system consistently

- `[AI]` **CRITICAL: SVG Export Label Issues**
  - Labels appear all over shapes instead of centered/organized
  - Text sizing is inconsistent (some huge, some tiny)
  - Label positioning overlaps with shape geometry
  - *Goal:* Clean, readable SVG exports with proper label placement

- `[AI]` **Cutlist Script Export Format**
  - Currently exports as .script file instead of .txt
  - Instructions are too technical and difficult for humans to follow
  - *Goal:* Export as .txt with human-friendly cutting instructions

- `[AI]` **CSV Export & Cutlist Determinism**
  - Finalize the `export_cutlist` function to produce stable, readable CSVs.
  - *Goal:* Production-ready cutlists.

- `[MIXED]` **DXF Export (Deferred)**
  - Future work. Not blocking v3.3.

## 5. CI/CD & Infrastructure

- `[AI]` **CRITICAL: Fix Ruff GitHub Action**
  - Current ruff fix action is misconfigured for this project
  - Fails with every commit, breaking CI pipeline
  - *Goal:* Working automated code formatting in CI

## 6. Documentation & AI Workflow

- `[HUMAN]` **User Guide Update**
  - Update for v3.3 features (Preview behavior, multi-sheet).

- `[AI]` **Sample Data**
  - specific metric and imperial CSV examples.

- `[AI]` **Test Suite Expansion**
  - Add coverage for Preview lifecycle and GUI hydration.

---

## Legend
- `[AI]`: Task suitable for an AI worker (Codex/Jules) with a clear spec.
- `[HUMAN]`: Requires design judgment, physical testing, or subjective polish.
- `[MIXED]`: AI can implement, but Human must define the "feel" or specific requirements.
