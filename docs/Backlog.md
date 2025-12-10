# SquatchCut Backlog

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
