# Architecture

This document snapshots how SquatchCut is organized so new work streams (AI agents or humans) stay aligned with the existing structure, data flow, and helper layers.

---

## 1. Project Layout

- `root/`
  - `freecad/SquatchCut/`
    - `InitGui.py`: workbench registration, toolbar/menu hooks, icon loading.
    - `__init__.py`: module metadata, lazy-bundled imports for FreeCAD.
    - `gui/`: Qt widgets, commands, dialogs, and view helpers.
    - `core/`: pure-Python algorithms, session plumbing, exporters, and utilities.
    - `resources/`: icons, templates, and static UI helpers.
  - `docs/`: architecture/roadmap/backlog, developer guidance, UAT + testing instructions.
  - `tests/`: pytest regression suite exercising hydration, nesting, exports, and docs.
  - `assets/` & `blog/`: site collateral (screenshots, articles) that support docs.
  - Top-level helpers: README, `AGENTS.md`, `squatchcut.code-workspace`, and CI config files.

This layout keeps FreeCAD integrations under `freecad/SquatchCut` while leaving tests/docs at the repo root for easy access by automation and documentation flows.

---

## 2. Core Modules

The `core/` package is the heart of the nesting logic and keeps FreeCAD dependencies confined to integration points.

- **Session + settings**
  - `session_state.py`: in-memory defaults, job sheets, panels, measurement system, and export flags used by all UI wiring.
  - `session.py`: mirrors `session_state` into the active FreeCAD document, tracks FreeCAD objects, and clears/chases Group nodes.
  - `preferences.py` & `presets.py`: wrap FreeCAD preferences, expose defaults per measurement system, and manage preset metadata used by the TaskPanel.
  - `settings.py`: hydrates defaults, exposes the configuration API, and guards persistence rules described in `docs/Project_Guide_v3.2.md`.

- **Unit conversion & logging**
  - `units.py` + `text_helpers.py`: convert between millimeters and fractional inches, format preset labels, and share helper text strings.
  - `logger.py`: centralized logger with SquatchCut-friendly prefixes for reporting and GUI tests.

- **CSV ingestion**
  - `csv_import.py`: high-level validation harness used by GUI commands and CLI integrations (includes measurement overrides).
  - `csv_loader.py`: low-level importer that normalizes rows, enforces required headers, and converts everything into panel dictionaries.

- **Panel discovery + validation**
  - `shape_extractor.py`: reads selected FreeCAD objects, enforces `SquatchCutCanRotate`, and exposes clean panel metadata.
  - `overlap_check.py`: utility to ensure placements do not overlap when verifying layouts.

- **Nesting & optimization**
  - `nesting.py`: orchestrates the multi-sheet workflow (sheet iteration, job sheet handling, compute_utilization, estimate_cut_counts).
  - `cut_optimization.py`: solver that does guillotine/shelf packing against free rectangles.
  - `nesting_engine.py`: encapsulates the algorithm that `cut_optimization` relies on; supports both “material” and “cuts” optimization modes.
  - `multi_sheet_optimizer.py`: spreads panels across multiple sheets, stopping when all parts are placed or sheets are exhausted.

- **Geometry & exports**
  - `geometry_output.py`: turns placements into FreeCAD rectangles, groups, and sources/nested sheet hierarchies.
  - `geometry_sync.py`: keeps the document in sync after imports/nesting by rebuilding views and logging stale-reference issues.
  - `view_controller.py`: TaskPanel-driven helpers to show source vs. nesting views, clear groups, and zoom to objects.
  - `gui_tests.py`: GUI-level smoke checks invoked from the Settings panel and the developer toolbar.
  - `cutlist.py`, `exporter.py`, `report_generator.py`: build deterministic exports (CSV cutlists, SVG maps, PDF reports) from `ExportJob`/`ExportSheet` state instead of FreeCAD objects.

- **Sheet helpers**
  - `sheet_model.py`: manages FreeCAD Group/Boundary helpers and ensures canonical names/clear/rebuild flows.
  - `sheet_presets.py`: provides factory presets for metric/imperial defaults that never auto-select themselves.

The `core` package intentionally minimizes FreeCAD API surface, enabling the python-only tests to run inside the Docker/devcontainer environment described in `docs/TESTING.md`.

---

## 3. GUI Layer

`gui/` wraps commands, dialogs, and widgets for user interaction.

- `gui/commands/`: entry points that plug into the FreeCAD GUI.
  - `cmd_run_nesting.py`, `cmd_export_report.py`, `cmd_import_csv.py`, `cmd_set_sheet_size.py`, `cmd_preferences.py`, `cmd_run_gui_tests.py`, `cmd_add_shapes.py`.
  - Commands import `core` helpers, show dialogs, and set `session_state` before running logic.

- Dialogs: `gui/dialogs/*.py` (CSV import, export report, run nesting, select shapes, sheet size) gather structured input before deferring to commands.

- TaskPanel widgets: 
  - `taskpanel_main.py` (main TaskPanel + summary stats + new developer tools section), 
  - `taskpanel_settings.py` (settings UI with GUI test launcher/status), 
  - `taskpanel_nesting.py`, `taskpanel_sheet.py`, `taskpanel_input.py`.
  - `qt_compat.py` provides lightweight Qt stubs so tests can instantiate widgets headlessly.

- Views/helpers: `source_view.py`, `nesting_view.py`, `view_helpers.py`, `view_utils.py` coordinate FreeCAD object visibility.

- `icons.py` resolves bundled icon names for commands and panels (no new icon dependencies allowed without review).

---

## 4. Data Flow

1. **CSV import or FreeCAD shape selection** feeds panel metadata into `session_state`.
2. The TaskPanel (main + settings) hydrates defaults via `settings.hydrate_from_params()` and populates widgets/sheets.
3. `session_state` + `nesting.py` assemble panels, job sheets, kerf/spacing, and routing (optimize-for-cut vs material). This includes `nesting_engine`, `cut_optimization`, and `multi_sheet_optimizer`.
4. `geometry_output` + `view_controller` rebuild the FreeCAD scene (source vs nested) and log visual diagnostics.
5. `Exporter`, `cutlist`, and `report_generator` read `ExportJob`/`ExportSheet` state to write deterministic CSV/SVG reports; FreeCAD geometry is never directly traversed when exports exist.
6. Developer-facing GUI tests (`core/gui_tests.py`, TaskPanel developer group) run a lean import + nesting cycle and log formatted results for Report view visibility.

---

## 5. Supporting Documentation & Tools

- Docs: `docs/Project_Guide_v3.2.md`, `docs/Backlog.md`, `docs/TESTING.md`, `docs/Development_Environment.md`, `docs/user_guide.md`, and the root `AGENTS.md` describe policies every change must obey.
- Testing: `docs/TESTING.md` and the Docker/devcontainer instructions explain how to run `pytest` (pure Python and FreeCAD-aware) plus `FreeCADCmd` GUI flows.
- Developer tooling: `gui/taskpanel_settings.py` and `core/gui_tests.py` surface the GUI test launcher, while `docs/TESTING.md` explains the Docker workflow for matching CI.
- Markdown assets (roadmap/backlog) live under `docs/`; they are validated by `tests/test_docs_backlog_structure.py` so future edits stay aligned with stated priorities.

Keeping this document synchronized with the real file tree prevents misconceptions about where logic lives and what responsibilities each module bears.
