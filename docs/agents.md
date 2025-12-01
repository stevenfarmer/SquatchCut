# SquatchCut – Codex Agent Guide

This guide defines how Codex must behave when editing the SquatchCut repository. It complements the main project guide at `docs/Project_Guide_v3.2.md` and is binding for all Codex work.

## Codex Role

- Acts as the engineering implementation layer for SquatchCut.
- Follows requirements from Steven and ChatGPT.
- Adheres to architecture, patterns, and behaviors defined in `docs/Project_Guide_v3.2.md`.
- Avoids “improving” or refactoring architecture without explicit instruction.
- Produces small, targeted changes unless told otherwise.
- Does not decide product direction or UX, and does not change defaults or preset behavior without explicit instruction.

## Repository Layout Summary

- `SquatchCut/core/` – core logic: nesting, units, session_state, settings, sheet_model, presets.
- `SquatchCut/gui/` – GUI code: TaskPanel_Main, TaskPanel_Settings, source_view, nesting_view, view_utils, commands.
- `SquatchCut/resources/` – icons and other resources.
- `tests/` – pytest suite.
- `docs/` – documentation: `Project_Guide_v3.2.md` (main guide), `agents.md` (this file), and other user/developer docs.

Codex must respect this layout and must not move files between these areas unless explicitly instructed.

## Behavior and Constraints

- Internal unit is always millimeters.
- Imperial UI uses fractional inches only.
- Defaults are loaded via `hydrate_from_params()` and are not changed by TaskPanel load.
- Presets never override defaults and are never auto-selected on panel load.
- TaskPanel creation must call `hydrate_from_params()` before building widgets.
- Codex must not change default values, auto-select presets, change measurement system logic, add or remove presets, introduce new dependencies, restructure directories, or rename TaskPanel/core classes unless explicitly instructed.
- No relative imports, especially in FreeCAD integration code.
- No silent behavioral changes; any change must tie directly to an explicit requirement in an instruction block.

## Reasoning Levels and Instruction Blocks

- LOW – trivial fix in one file.
- MEDIUM – small feature or bugfix involving one or two files.
- HIGH – multi-file changes or work touching settings, hydration, or TaskPanel initialization.
- EXTRA-HIGH – architectural or algorithm-level refactor.

Instruction block structure:
- Begins with `Recommended Codex reasoning level: <LEVEL>`.
- First line inside: `Codex, this task requires <LEVEL> reasoning.`
- Includes file paths to touch, requirements, acceptance criteria, and guardrails.
- Codex must not infer missing requirements and must obey guardrails even if another pattern seems “better.”

## Testing Expectations

- Any logic-level change must be accompanied by tests under `tests/`.
- Codex must add tests for new behaviors, update tests when behavior changes, and ensure pytest passes.
- Core focus areas: mm/inch conversions and fractions, CSV parsing, hydration and default initialization, preset behavior, TaskPanel load behavior and measurement-system formatting.
- Do not remove tests without explicit instructions.

## Interaction with Project_Guide_v3.2.md

- `docs/Project_Guide_v3.2.md` is the primary project-wide technical and process specification.
- `docs/agents.md` is the behavioral guide for Codex.
- When in doubt, defer to `Project_Guide_v3.2.md` for architecture/behavior rules and to `agents.md` for how Codex should act on instructions. Neither document may be ignored.

## Guardrails Summary

- Do not refactor or reorganize the project unless explicitly instructed.
- Do not auto-change defaults, presets, or measurement-system behavior.
- Do not invent new patterns or modules.
- Do not widen scope; only change what the task requires.
- Do not reduce test coverage or remove tests without explicit approval in instructions.
