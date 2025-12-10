# Contributing to SquatchCut

Thanks for helping improve SquatchCut! This is an active beta project—please open an issue to discuss significant changes before submitting a PR.

## Getting Started
1. Create a virtualenv and install dev deps:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements-dev.txt
   ```
2. Run the core tests:
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

## AI Agents & Detailed Architecture
If you are an AI Agent or need detailed architectural/behavioral rules, please refer to:
- `AGENTS.md` (in the root directory) for strict behavioral guidelines.
- `docs/Project_Guide_v3.2.md` for the comprehensive project guide and architecture.

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
