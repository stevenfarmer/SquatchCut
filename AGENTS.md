# SquatchCut – AI Agent Guide

This guide defines how AI Agents (e.g., you) must behave when editing the SquatchCut repository. It complements the main project guide at `docs/Project_Guide_v3.2.md` and is binding for all work.

## Role

- Acts as the engineering implementation layer for SquatchCut.
- Follows requirements from the user and architectural guidelines.
- Adheres to architecture, patterns, and behaviors defined in `docs/Project_Guide_v3.2.md`.
- Avoids “improving” or refactoring architecture without explicit instruction.
- Produces small, targeted changes unless told otherwise.
- Does not decide product direction or UX, and does not change defaults or preset behavior without explicit instruction.

## Repository Layout Summary

- `freecad/SquatchCut/core/` – core logic: nesting, units, session_state, settings, sheet_model, presets.
- `freecad/SquatchCut/gui/` – GUI code: TaskPanel_Main, TaskPanel_Settings, source_view, nesting_view, view_utils, commands.
- `freecad/SquatchCut/resources/` – icons and other resources.
- `tests/` – pytest suite.
- `docs/` – documentation.
- `AGENTS.md` – (this file) Behavioral guide.

Agents must respect this layout and must not move files between these areas unless explicitly instructed.

## Behavior and Constraints

- Internal unit is always millimeters.
- Imperial UI uses fractional inches only.
- Defaults are loaded via `hydrate_from_params()` and are not changed by TaskPanel load.
- Presets never override defaults and are never auto-selected on panel load.
- TaskPanel creation must call `hydrate_from_params()` before building widgets.
- Do not change default values, auto-select presets, change measurement system logic, add or remove presets, introduce new dependencies, restructure directories, or rename TaskPanel/core classes unless explicitly instructed.
- No relative imports, especially in FreeCAD integration code.
- No silent behavioral changes; any change must tie directly to an explicit requirement.

## Compatibility and Testing

- **Python Version:** Code must be compatible with Python versions older than 3.10. Avoid PEP 604 type unions (`type | None`); use `Optional[type]`.
- **Testing:**
    - Run tests with `export PYTHONPATH=$PYTHONPATH:$(pwd)/freecad && pytest`.
    - Use `qt_compat` shim for GUI tests where applicable.
    - When using `qt_compat`, signals (e.g., `textChanged`) are not automatically emitted by setters; manually invoke slots.
    - Mock `SquatchCutPreferences` by patching it in the *importer's* namespace (e.g., `SquatchCut.settings.SquatchCutPreferences`).
    - Use `from SquatchCut...` imports in tests, not `from freecad.SquatchCut...`.

## Reasoning Levels

- **LOW** – trivial fix in one file.
- **MEDIUM** – small feature or bugfix involving one or two files.
- **HIGH** – multi-file changes or work touching settings, hydration, or TaskPanel initialization.
- **EXTRA-HIGH** – architectural or algorithm-level refactor.

## Testing Expectations

- Any logic-level change must be accompanied by tests under `tests/`.
- Add tests for new behaviors, update tests when behavior changes.
- Core focus areas: mm/inch conversions and fractions, CSV parsing, hydration and default initialization, preset behavior.
- Do not remove tests without explicit instructions.

## Interaction with Project_Guide_v3.2.md

- `docs/Project_Guide_v3.2.md` is the primary project-wide technical and process specification.
- `AGENTS.md` is the behavioral guide.
- When in doubt, defer to `Project_Guide_v3.2.md` for architecture/behavior rules and to `AGENTS.md` for how to act on instructions.

## Export Rules (binding)

- All user-facing exports (CSV, SVG, DXF) must go through `freecad/SquatchCut/core/exporter.py`.
- `ExportJob`/`ExportSheet`/`ExportPartPlacement` are the **only** sources of truth for export geometry.
- Never derive exports from FreeCAD document objects when ExportJob exists.
- CSV/SVG implementations must use ExportJob values in millimeters and rely on exporter helpers for measurement-system display strings.
- DXF export is currently deferred; do not implement unless instructed.
