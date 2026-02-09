# Contributing to SquatchCut

Thanks for helping improve SquatchCut! This is an active beta project—please open an issue to discuss significant changes before submitting a PR.

## CI/CD expectations

Before pushing code, review `docs/CI_HEALTH.md` for a summary of the GitHub Actions flows, required pre-flight commands, and troubleshooting tips. Running the local lint/test/docs commands listed there eliminates most sources of CI failure.

## Getting Started
1. Create a virtualenv and install dev deps:
   ```bash
   make setup-env
   ```
   The target creates `./.venv`, upgrades `pip`, and installs the dev dependencies used by the lint/test tooling. After the venv exists, `make lint`/`make format` automatically use it instead of looking for a global `python` executable.
2. Optionally activate the virtualenv for ad-hoc commands:
   ```bash
   source .venv/bin/activate
   ```
   Once activated, `python`, `ruff`, and other tooling resolve to the sandboxed interpreter.
3. Run the core tests:
   ```bash
   PYTHONPATH=freecad .venv/bin/pytest --cov=SquatchCut.core.nesting --cov=SquatchCut.core.session_state --cov-report=term-missing --cov-fail-under=80
   ```
   **Note**: `PYTHONPATH=freecad` is required because the codebase imports modules as `from SquatchCut...` rather than `from freecad.SquatchCut...`. This ensures compatibility with both the FreeCAD internal module loader and external test runners.

3. Optional: run FreeCAD E2E scripts inside FreeCAD (see `freecad/testing/`).

## Style & Expectations
- Keep modules focused: core logic stays headless; GUI code lives under `gui/`.
- Prefer small, well-documented helpers over large inline blocks.
- Add or update docstrings for public functions/classes; note beta/heuristic behavior where relevant.
- Maintain existing commands for compatibility; new UI goes through `SquatchCut_ShowTaskPanel`.

## Ruff Linting & Autofix
Ruff (`ruff check .`) runs in CI and will fail any PR that introduces lint violations. If CI reports Ruff errors, you can trigger the **Ruff autofix** workflow from the GitHub Actions tab for the affected branch. The workflow runs `ruff check . --fix`, commits any changes with `chore: apply ruff autofix`, and pushes them back to the branch. After it finishes, re-run CI to confirm the lint errors are resolved or address any remaining issues manually.

## AI Workers & Detailed Architecture
If you are an AI worker or need detailed architectural/behavioral rules, please refer to:
- `AGENTS.md` (in the root directory) for strict behavioral guidelines and the AI worker protocol.
- `docs/developer_guide.md` for the comprehensive project guide and architecture (v3.2 retained for history).

The workflow involves multiple AI roles (Architect + AI assistants such as Codex, Jules, or future tools); all tasks must originate from Architect specs.

## Adding a New Optimization Strategy (High Level)
1. Implement a pure-Python strategy in `freecad/SquatchCut/core/nesting.py`.
2. Provide summary helpers if needed (utilization, cut counts, etc.).
3. Expose selection in session state/UI via `set_optimization_mode` and the Task panel.
4. Add unit tests covering overlaps, rotation handling, and basic metrics.

## Reporting Issues
Please include:
- FreeCAD version and OS
- Steps to reproduce
- Sample CSV or document if applicable
- Expected vs actual behavior
