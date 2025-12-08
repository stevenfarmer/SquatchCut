# SquatchCut Backlog

## Completed Since v3.2
- **Settings Panel Behavior** – Settings TaskPanel opens reliably, hydrates before widgets, and only persists defaults on explicit save (`freecad/SquatchCut/gui/taskpanel_settings.py`, hydration helpers).
- **Unified Job-Sheet Normalization** – `_normalize_sheet_definition` + helper pipeline now feeds every nesting strategy with the same validated sheet list (`freecad/SquatchCut/core/nesting.py`).
- **Baseline Multi-Sheet Support** – Standard, cut-friendly, and guillotine strategies accept multi-sheet jobs with `sheet_index` fidelity (`freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/core/cut_optimization.py`).
- **Warning Banner Infrastructure** – TaskPanel warning banner warns when cut modes may ignore sheets; `_sheet_warning_active` wiring covered by hydration tests (`freecad/SquatchCut/gui/taskpanel_main.py`, `tests/test_taskpanel_hydration.py`).
- **Documentation & Backlog Sync** – v3.2 guide and this backlog reflect the shared job-sheet pipeline, warning banner, and current priorities (`docs/Project_Guide_v3.2.md`).
- **AI-Friendly Dev Environment** – Host-cloned repo, bind-mounted dev container, and `squatchcut.code-workspace` defined for ChatGPT/Codex compatibility (`.devcontainer/devcontainer.json`, `squatchcut.code-workspace`, `docs/Development_Environment.md`).

## Active Backlog (High Priority)
- **P1 – Preview Determinism & Cleanup** – Separate preview from apply so preview is non-destructive, and keep `SquatchCut_Sheet_*`, `SquatchCut_SourceParts_*`, and `SquatchCut_NestedParts_*` groups synchronized/cleared.  
  _Scope_: `freecad/SquatchCut/gui/taskpanel_main.py`, `freecad/SquatchCut/core/view_controller.py`, `freecad/SquatchCut/core/session.py`

- **P1 – TaskPanel Overflow & Ergonomics** – Rework dense button/checkbox rows (Preview/Run/Show Source, warning banner, sheet controls) to prevent clipping on narrow docks.  
  _Scope_: `freecad/SquatchCut/gui/taskpanel_main.py`

- **P1 – Multi-Sheet Visualization Polish** – Improve per-sheet labeling, spacing, and navigation inside the 3D view so advanced sheet stacks are obvious and ghost objects never remain.  
  _Scope_: `freecad/SquatchCut/gui/nesting_view.py`, `freecad/SquatchCut/core/view_controller.py`

- **P1 – Cut-Friendly Multi-Sheet Heuristics** – Refine lane/guillotine handling of sheet order, spacing, and exhaustion so parts aren’t silently dropped or restarted unpredictably.  
  _Scope_: `freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/core/cut_optimization.py`

- **P1 – Test Suite Expansion (Hydration, Units, Preview)** – Add coverage for measurement toggles, fractional-inch formatting drift, preview lifecycle, sheet_index propagation, and basic exhaustion scenarios.  
  _Scope_: `tests/test_taskpanel_hydration.py`, `tests/test_nesting.py`, new preview/exhaustion suites

- **P2 – CSV Export & Cutlist Determinism** – Replace the placeholder export command with a working, deterministic cutlist writer.  
  _Scope_: `freecad/SquatchCut/gui/commands/cmd_run_nesting.py` + helpers

- **P2 – Warning Banner Lifecycle Tests** – Ensure `_sheet_warning_active` and banner text update correctly when nesting mode, job sheets, or unit systems change.  
  _Scope_: `freecad/SquatchCut/gui/taskpanel_main.py`, `tests/test_taskpanel_hydration.py`

- **P2 – Sheet Exhaustion Metrics & Feedback** – Detect and communicate when configured sheet quantities run out, ideally via stats and UI/log hints.  
  _Scope_: `freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/gui/taskpanel_main.py`

## Future / Longer-Term Items
- **Per-Sheet Cut-Order Visualization** – Highlight rip/crosscut sequences and provide per-sheet cut-order visualization guidance in the viewer (`freecad/SquatchCut/gui/nesting_view.py`, `freecad/SquatchCut/core/cut_optimization.py`).
- **Enhanced Sheet Exhaustion Metrics** – Provide utilization percentages and unused/used counts once baseline exhaustion warnings exist (`freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/gui/taskpanel_main.py`).
- **Multi-Sheet Presets** – Save/load named sheet stacks that respect measurement rules (`freecad/SquatchCut/gui/taskpanel_main.py`, `freecad/SquatchCut/core/session_state.py`, `docs/user_guide.md`).
- **Kerf Simulation** – Model saw-specific kerf widths in both packing and cut-friendly heuristics (`freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/core/cut_optimization.py`, `docs/user_guide.md`).
- **Grain Direction & Bookmatching** – Add metadata/constraints for honoring grain orientation or mirrored layouts (`freecad/SquatchCut/core/nesting.py`, `freecad/SquatchCut/gui/taskpanel_main.py`).
