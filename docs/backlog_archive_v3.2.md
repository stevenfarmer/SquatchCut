# SquatchCut Backlog (v3.3 – Addon Manager Readiness)

This backlog targets “ready for FreeCAD Addon Manager” status and aligns with Project_Guide_v3.3.md and SQUATCHCUT_SYNC_REPORT_V4.

**Tag legend:** `[AI]` = AI-worker-friendly, `[HUMAN]` = human-only, `[MIXED]` = AI-assisted with human judgment.

## 1. High Priority – Required for Addon Manager

### Core engine & multi-sheet behavior
- [MIXED] Keep nesting pipeline deterministic across multi-sheet jobs and cut-friendly heuristics; avoid drift in sheet_index ordering.

### Units, sheets, and measurement systems
- [AI] Ensure measurement-system defaults remain split per system during hydration/settings flows; prevent hidden unit drift.

### TaskPanels & UI/UX
- [MIXED] Reflow TaskPanel controls for narrow docks (~300–350 px) and ensure warning banner coexists without clipping.

### Preview/apply lifecycle
- [MIXED] Implement non-destructive preview path with deterministic cleanup of `SquatchCut_*` groups before/after preview/apply.

### Sheet exhaustion & utilization
- [MIXED] Detect sheet exhaustion during nesting, surface user-visible feedback (logs/UI), and prevent silent truncation.

### Export (cutlist/report/DXF)
- [MIXED] Wire cutlist/export commands end-to-end with deterministic outputs from ExportJob; remove stub paths and confirm UI triggers succeed.

### Logging & Developer Mode
- [MIXED] Ensure developer-mode/logging controls are available without impacting UAT flows; keep logging consistent across commands.

### Integration tests & GUI tests
- [AI] Add integration coverage for preview→apply sequencing and multi-sheet exhaustion edge cases (qt_compat where possible).

### Docs, UAT & packaging
- [MIXED] Validate packaging/addon ZIP and command registration for Addon Manager; confirm package.xml/egg-info/Makefile output installs cleanly.

## 2. Medium Priority – Should Have Soon

### Core engine & multi-sheet behavior
- [AI] Add per-sheet utilization metrics and log/UI summaries after nesting.

### Units, sheets, and measurement systems
- [AI] Strengthen fractional-inch and measurement toggle tests to guard against formatting drift during edits/hydration.

### TaskPanels & UI/UX
- [AI] Add warning/banner lifecycle tests and polish interactions when nesting mode, job sheets, or units change.

### Preview/apply lifecycle
- [AI] Expand integration tests around preview→apply flows to ensure preview is non-destructive once implemented.

### Sheet exhaustion & utilization
- [MIXED] Provide basic utilization/exhaustion summaries in the TaskPanel/logs once detection is in place.

### Export (cutlist/report/DXF)
- [AI] Document export formats (CSV/SVG/cutlist) with sample outputs for metric/imperial; keep DXF deferred but scoped.

### Logging & Developer Mode
- [MIXED] Test and refine logging/dev-mode persistence and UX so toggles are discoverable yet unobtrusive.

### Integration tests & GUI tests
- [AI] Broaden GUI smoke tests for TaskPanel layout at narrow widths and warning banner states.

### Docs, UAT & packaging
- [AI] Refresh UAT checklist/prep docs and sample CSVs to match v3.3 preview/apply and multi-sheet behavior.

## 3. Low Priority – Nice to Have / v3.4+

### Core engine & multi-sheet behavior
- [MIXED] Polish multi-sheet visualization (labels, spacing) and eliminate ghost objects after reruns.

### Export (cutlist/report/DXF)
- [AI] Implement DXF export via ExportJob once CSV/SVG are locked.

### Logging & Developer Mode
- [AI] Add enhanced developer diagnostics (utilization summaries, optional verbose logging) controllable from settings.

### Docs, UAT & packaging
- [AI] Provide additional AI-worker job card templates and contributor guidance for AI-assisted development.

---

# Legacy Backlog (v3.2 archive)

The content below preserves the previous backlog for historical reference and for any checks that still target v3.2-era milestones.

## SquatchCut Backlog (v3.3)

This backlog reflects the current architecture (multi-sheet jobs, per-job measurement system, settings/dev-mode, logging controls) and supports a multi-AI workflow.

**Tag legend:** `[AI]` = AI-worker-friendly, `[HUMAN]` = human-only, `[MIXED]` = AI-assisted with human judgment.

## Core engine & nesting
- [MIXED] Preview determinism & cleanup – Separate preview from apply, keep `SquatchCut_Sheet_*`, `SquatchCut_SourceParts_*`, and `SquatchCut_NestedParts_*` synchronized/cleared across Preview/Apply runs, and leave the document clean between runs.
- [MIXED] Sheet exhaustion metrics & feedback – Detect exhausted sheet stacks, log/flag usage stats per sheet, and surface user-visible hints instead of silent truncation.
- [AI] ExportJob determinism verification – Expand coverage for `build_export_job_from_current_nesting` to lock raw mm geometry vs formatted strings for metric/imperial jobs.
- [MIXED] Cut-friendly multi-sheet heuristics – Stabilize lane/guillotine ordering and spacing for advanced sheet stacks while honoring `sheet_index` fidelity.

## Units, sheets, and measurement systems
- [AI] Fractional-inch stability – Strengthen formatting/parsing tests to prevent drift across hydration, sheet edits, and CSV import/export.
- [AI] Per-job measurement system persistence – Verify that measurement toggles and defaults travel through hydration/TaskPanel flows without mutating stored defaults.
- [MIXED] Sheet presets & imperial defaults review – Validate imperial defaults (48 × 96) and preset selection rules under multi-sheet jobs without auto-selection.

## GUI & UX
- [MIXED] TaskPanel overflow & ergonomics – Reflow dense button/checkbox rows so narrow docks (~300–350 px) do not clip controls or warning banners.
- [MIXED] Multi-sheet visualization polish – Improve per-sheet labeling, spacing, and navigation; ensure ghost objects never linger after reruns.
- [AI] Warning banner lifecycle tests – Cover `_sheet_warning_active` state changes across nesting modes, job sheet edits, and unit-system toggles.
- [MIXED] Dev-mode & logging controls – Keep developer tools/logging toggles discoverable without impacting normal UAT flows.

## AI workflow & tooling
- [HUMAN] Branch governance for multiple AI workers – Define branch naming/assignment norms so parallel AI tasks avoid overlapping core files.
- [AI] Task spec/job card templates – Publish examples for Architect-written specs consumable by any AI worker (local editor or hosted agent).
- [AI] CI and lint reliability – Keep lint/test workflows tool-agnostic; document any AI-specific pre-flight checks when running locally.

## Docs & onboarding
- [AI] v3.3 documentation sweep – Align user/dev docs, MkDocs nav, and samples with v3.3 behavior (multi-sheet jobs, measurement handling, preview/apply flow).
- [AI] Sample data refresh – Ship metric and imperial CSV samples with expected outputs for Preview/Apply and exports.
- [MIXED] UAT collateral – Update prep/checklist docs to reflect current UI labels, warning banner expectations, and developer mode/logging guidance.

## Archive / Legacy backlog (pre-v3.3)
The sections below preserve the v3.2 backlog for historical reference and validation.

## Completed Since v3.2
- **Settings Panel Behavior** – Settings TaskPanel opens reliably, hydrates before widgets, and only persists defaults on explicit save (`freecad/SquatchCut/gui/taskpanel_settings.py`, hydration helpers).
- **Unified Job-Sheet Normalization** – `_normalize_sheet_definition` + helper pipeline now feeds every nesting strategy with the same validated sheet list (`freecad/SquatchCut/core/nesting.py`).
- **Baseline Multi-Sheet Support** – Standard, cut-friendly, and guillotine strategies accept multi-sheet jobs with `sheet_index` fidelity (`freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/core/cut_optimization.py`).
- **Warning Banner Infrastructure** – TaskPanel warning banner warns when cut modes may ignore sheets; `_sheet_warning_active` wiring covered by hydration tests (`freecad/SquatchCut/gui/taskpanel_main.py`, `tests/test_taskpanel_hydration.py`).
- **Documentation & Backlog Sync** – v3.2 guide and this backlog reflect the shared job-sheet pipeline, warning banner, and current priorities (`docs/Project_Guide_v3.2.md`).
- **AI-Friendly Dev Environment** – Host-cloned repo, bind-mounted dev container, and `squatchcut.code-workspace` defined for ChatGPT/Codex compatibility (`.devcontainer/devcontainer.json`, `squatchcut.code-workspace`, `docs/Development_Environment.md`).
- **Canonical ExportJob Model** – `ExportJob`, `ExportSheet`, and `ExportPartPlacement` defined/tested in `freecad/SquatchCut/core/exporter.py`; `build_export_job_from_current_nesting` is the sole bridge from nesting to exports.
- **CSV Cutlist Export from ExportJob** – `export_cutlist` now writes deterministic CSV rows (raw mm + formatted strings) using ExportJob; TaskPanel routes CSV flows exclusively through exporter.py.
- **SVG 2D Export from ExportJob** – `export_nesting_to_svg` renders one sheet-per-file SVG with sheet borders, part rectangles, and labels without touching FreeCAD geometry; TaskPanel uses this gateway for SVG.
- **Centralized Export Gateway** – All TaskPanel exports call `build_export_job_from_current_nesting` + `exporter.export_*`; no other module writes CSV/SVG files directly.

## Active Backlog (High Priority)

- **P1 – Preview Determinism & Cleanup** – Separate preview from apply so preview is non-destructive, and keep `SquatchCut_Sheet_*`, `SquatchCut_SourceParts_*`, and `SquatchCut_NestedParts_*` groups synchronized/cleared across Preview/Apply runs.  
  _Scope_: `freecad/SquatchCut/gui/taskpanel_main.py`, `freecad/SquatchCut/core/view_controller.py`, `freecad/SquatchCut/core/session.py`

- **P1 – TaskPanel Overflow & Ergonomics** – Rework dense button/checkbox rows (Preview/Run/Show Source, warning banner, sheet controls) to prevent clipping on narrow docks, and add/update minimal UI smoke checks to ensure the TaskPanel initializes cleanly at narrow dock widths (~300–350 px).  
  _Scope_: `freecad/SquatchCut/gui/taskpanel_main.py`, `tests/test_taskpanel_hydration.py` (and/or lightweight GUI smoke tests)

- **P1 – Multi-Sheet Visualization Polish** – Improve per-sheet labeling, spacing, and navigation inside the 3D view so advanced sheet stacks are obvious and ghost objects never remain after reruns.  
  _Scope_: `freecad/SquatchCut/gui/nesting_view.py`, `freecad/SquatchCut/core/view_controller.py`

- **P1 – Test Suite Expansion (Hydration, Units, Preview)** – Add coverage for measurement toggles, fractional-inch formatting drift, preview lifecycle (Preview → Preview → Apply vs Apply-only), `sheet_index` propagation, and basic sheet exhaustion scenarios.  
  _Scope_: `tests/test_taskpanel_hydration.py`, `tests/test_nesting.py`, new preview/exhaustion-focused suites

- **P2 – CSV Export & Cutlist Determinism** – Replace the placeholder export command with a working, deterministic cutlist writer that orders rows by sheet index and cut order and emits stable, documented fields.  
  _Scope_: `freecad/SquatchCut/gui/commands/cmd_run_nesting.py` + helpers

- **P2 – DXF Export from ExportJob (Deferred)** – Implement DXF generation from the same 2D sheet/part representation once CSV/SVG pipelines are locked. Until then, DXF remains non-blocking.  
  _Scope_: `freecad/SquatchCut/core/exporter.py` (future work)

- **P2 – Documentation & Sample Data Updates** – Update user-facing docs and examples to match the v3.3 UX, including Preview vs Apply workflow, multi-sheet nesting behavior, and shipping both metric and imperial sample CSVs with expected results.  
  _Scope_: `docs/Project_Guide_v3.2.md`, `docs/user_guide.md`, `docs/samples/*`

- **P2 – Warning Banner Lifecycle Tests** – Ensure `_sheet_warning_active` and banner text update correctly when nesting mode, job sheets, or unit systems change so the banner never gets stuck “on” or “off”.  
  _Scope_: `freecad/SquatchCut/gui/taskpanel_main.py`, `tests/test_taskpanel_hydration.py`

- **P2 – Sheet Exhaustion Metrics & Feedback** – Detect and communicate when configured sheet quantities run out, ideally via simple usage stats (used vs available) and clear UI/log hints rather than silent truncation.  
  _Scope_: `freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/gui/taskpanel_main.py`

## Future / Longer-Term Items

- **Per-Sheet Cut-Order Visualization** – Highlight rip/crosscut sequences and provide per-sheet cut-order visualization guidance in the viewer once core v3.3 visuals are stable.  
  _Scope_: `freecad/SquatchCut/gui/nesting_view.py`, `freecad/SquatchCut/core/cut_optimization.py`

- **Enhanced Sheet Exhaustion Metrics** – Provide utilization percentages and unused/used counts after baseline exhaustion warnings are in place, to help users tune their sheet configurations.  
  _Scope_: `freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/gui/taskpanel_main.py`

- **Multi-Sheet Presets** – Save/load named sheet stacks that respect measurement rules and provide quick-select for common configurations (e.g., 4×8 plywood stacks).  
  _Scope_: `freecad/SquatchCut/gui/taskpanel_main.py`, `freecad/SquatchCut/core/session_state.py`, `docs/user_guide.md`

- **Kerf Simulation** – Model saw-specific kerf widths in both packing and cut-friendly heuristics, and expose configuration in the UI and documentation.  
  _Scope_: `freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/core/cut_optimization.py`, `docs/user_guide.md`

- **Grain Direction & Bookmatching** – Add metadata/constraints for honoring grain orientation or mirrored/bookmatched layouts, with UI toggles and clear export semantics.  
  _Scope_: `freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/gui/taskpanel_main.py`
