# SquatchCut Backlog (v3.3)

**Status:** v3.3 - Preparation for FreeCAD Add-On Manager
**Focus:** Stability, Determinism, Documentation, and AI-Agnostic Workflow.

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

## 4. Exports (CSV/SVG/DXF)

- `[AI]` **CSV Export & Cutlist Determinism**
  - Finalize the `export_cutlist` function to produce stable, readable CSVs.
  - *Goal:* Production-ready cutlists.

- `[AI]` **SVG Export Polish**
  - Ensure SVG output is consistent with `ExportJob` model.
  - *Goal:* Reliable 2D output.

- `[MIXED]` **DXF Export (Deferred)**
  - Future work. Not blocking v3.3.

## 5. Documentation & AI Workflow

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
