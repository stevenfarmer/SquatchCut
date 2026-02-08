# SquatchCut Developer Guide

**Version:** 1.0 (Consolidated from AGENTS.md + Project_Guide_v3.3.md)
**Last Updated:** 2026-02-08

This is the single source of truth for SquatchCut development. It defines architecture, constraints, and workflows for both human and AI contributors.

---

## Project Overview

**SquatchCut** is a FreeCAD add-on for nesting rectangular parts on sheet goods (plywood, MDF, etc.). It reads CSV part lists and generates optimized layouts for woodworking and cabinet shops.

**Core Workflow:** CSV → Sheet Size → Nest → Export (SVG/CSV/DXF)

**Key Features:**
- CSV-driven rectangular nesting
- Metric and imperial support (fractional inches)
- Multiple nesting strategies (material-optimized, cut-optimized)
- Shape-based nesting (v3.4 experimental)

---

## Repository Structure

```
freecad/SquatchCut/
├── core/           # Pure Python logic (nesting, units, session, export)
├── gui/            # FreeCAD UI (TaskPanels, commands, dialogs)
├── resources/      # Icons and assets
└── ui/             # UI utilities (messages, progress, error handling)

tests/              # Pytest test suite
docs/               # User and developer documentation
```

**Rule:** Respect this structure. Don't move files between areas without explicit approval.

---

## Core Principles (Non-Negotiable)

1. **Internal units = millimeters** (always)
2. **Imperial display = fractional inches only** (no decimals)
3. **Defaults only change via Settings panel save**
4. **Presets never override defaults**
5. **TaskPanel never auto-selects presets**
6. **hydrate_from_params() runs before UI widgets**
7. **Every logic change requires tests**
8. **Settings panel must always open**
9. **No relative imports** (use absolute: `from SquatchCut.core import ...`)
10. **Python < 3.10 compatibility** (FreeCAD requirement)

---

## Critical Constraints

### Hydration Rules

**HYDRATION-001: Initialization Order**
```python
# CORRECT
def create_taskpanel(self):
    self.hydrate_from_params()  # Load state FIRST
    self.create_widgets()       # Then create UI

# WRONG
def create_taskpanel(self):
    self.create_widgets()       # UI before state = BAD
    self.hydrate_from_params()
```

**HYDRATION-002: Default Persistence**
- Defaults ONLY change via Settings panel save
- TaskPanel NEVER modifies defaults
- Only `Settings.save()` can write defaults

**HYDRATION-003: Preset Auto-Selection**
- Presets NEVER auto-selected on load
- Always start with "None / Custom"
- User must explicitly select a preset

### Measurement System

**MEASUREMENT-001: Internal Storage**
```python
# CORRECT - Always store mm internally
internal_width = inches_to_mm(48.0)

# WRONG - Never store imperial internally
internal_width = 48.0  # inches
```

**MEASUREMENT-002: Imperial Display**
```python
# CORRECT - Fractional inches for display
display = format_fractional_inches(mm_to_inches(width))  # "48 3/4 in"

# WRONG - Decimal inches
display = f"{mm_to_inches(width):.2f} in"  # "48.75 in"
```

### Export Architecture

**EXPORT-001: Canonical Export Path**
- All exports go through `freecad/SquatchCut/core/exporter.py`
- Use `ExportJob` → `ExportSheet` → `ExportPartPlacement` data model
- Never read FreeCAD geometry directly for exports

```python
# CORRECT
export_job = build_export_job_from_current_nesting()
export_cutlist(export_job, file_path)

# WRONG
parts = FreeCAD.ActiveDocument.getObjectsByLabel("SquatchCut_NestedParts")
# Direct geometry access
```

### Python Compatibility

**PYTHON-001: Version Compatibility**
```python
# CORRECT - Python < 3.10 compatible
from typing import Optional
def foo(x: Optional[int]) -> Optional[str]:
    ...

# WRONG - PEP 604 unions (Python 3.10+)
def foo(x: int | None) -> str | None:
    ...
```

**PYTHON-002: Import Patterns**
```python
# CORRECT - Absolute imports
from SquatchCut.core import nesting
from SquatchCut.gui.taskpanel_main import TaskPanelMain

# WRONG - Relative imports
from .core import nesting
from ..gui.taskpanel_main import TaskPanelMain
```

---

## TaskPanel Initialization Order

This order is **mandatory** for all TaskPanels:

1. Load `session_state`
2. Call `hydrate_from_params()`
3. Create all UI widgets
4. Populate UI values from hydrated state
5. Apply measurement formatting
6. Connect signals
7. Render panel

**No exceptions.** Violating this order causes UI/data mismatches.

---

## Testing Requirements

**Rule:** Every logic change requires tests in `tests/`

**Priority Test Areas:**
- mm/inch conversions
- CSV parsing
- Hydration logic
- Preset behavior
- Export functionality

**Test Execution:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=SquatchCut.core --cov-report=term-missing

# Collect tests only (fast check)
pytest --collect-only -q
```

**GUI Testing:**
- Use `qt_compat` shim for headless testing
- Manually invoke slots (signals not auto-emitted in tests)
- Mock `SquatchCutPreferences` in importer's namespace

---

## Task Specification Format

When defining work for AI agents or documenting tasks:

### Reasoning Levels

- **LOW:** Single file, trivial fix, no architectural impact
- **MEDIUM:** 1-2 files, simple feature, minor UI changes
- **HIGH:** Multi-file, UI/hydration/settings changes, complex coordination
- **EXTRA-HIGH:** Architectural refactor, algorithm changes, major changes

### Required Elements

Every task spec must include:

1. **Reasoning Level:** `Recommended reasoning level: <LEVEL>`
2. **Context:** What and why
3. **Requirements:** Bulleted functional requirements
4. **Constraints:** Which constraints apply (reference by ID)
5. **File Paths:** Explicit paths to modify
6. **Acceptance Criteria:** Testable success conditions
7. **Verification:** How to validate

### Example

```
Recommended reasoning level: HIGH

Context: Fix Settings panel hydration order bug

Requirements:
- Move hydrate_from_params() before widget creation
- Ensure defaults load before UI populates
- Add test to verify hydration order

Constraints:
- HYDRATION-001: Must call hydrate before widgets
- UI-001: Settings panel must always open
- PYTHON-001: Python < 3.10 compatible

File Paths:
- freecad/SquatchCut/gui/taskpanel_settings.py

Acceptance Criteria:
- Settings panel opens without errors
- Hydration occurs before widget creation
- Test verifies initialization order

Verification:
- Manual: Open Settings panel
- Automated: pytest tests/test_taskpanel_hydration.py
```

---

## Development Workflow

### Setup

```bash
# Clone repo
git clone <repo-url>
cd SquatchCut

# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest
```

### Making Changes

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes following constraints above
3. Run tests: `pytest`
4. Run linter: `ruff check . --fix`
5. Commit with clear message
6. Open PR with description

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation only
- `test/` - Test additions/fixes

### Commit Messages

```
type: brief description

Longer explanation if needed.

- Bullet points for details
- Reference constraints if applicable
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

---

## Common Patterns

### Adding a New Setting

1. Add to `core/preferences.py` (getter/setter)
2. Add to `core/session_state.py` (session variable)
3. Add to `gui/taskpanel_settings.py` (UI widget)
4. Follow hydration order (load before widget creation)
5. Add tests

### Adding a New Export Format

1. Add function to `core/exporter.py`
2. Use `ExportJob` data model
3. Respect `measurement_system` from ExportJob
4. Add to export format dropdown in TaskPanel
5. Add tests

### Adding a New Nesting Strategy

1. Add function to `core/nesting.py`
2. Return `list[PlacedPart]`
3. Use mm internally
4. Add to strategy selection in `cmd_run_nesting.py`
5. Add tests

---

## Troubleshooting

### Tests Failing

```bash
# See which tests failed
pytest -v

# Run specific test
pytest tests/test_nesting.py::test_specific_function

# Check test collection
pytest --collect-only -q
```

### Import Errors

- Check for relative imports (use absolute)
- Verify `PYTHONPATH` includes `freecad/` directory
- Check for circular imports

### UI Not Loading

- Check hydration order (hydrate before widgets)
- Check for exceptions in TaskPanel `__init__`
- Verify Settings panel can open

### Measurement System Issues

- Verify internal storage uses mm
- Check display formatting uses correct system
- Test round-trip conversions

---

## Resources

- **User Guide:** `docs/user_guide.md`
- **Architecture:** `docs/architecture.md`
- **Testing:** `docs/TESTING.md`
- **Backlog:** `backlog.md`
- **Changelog:** `CHANGELOG.md`

---

## Quick Reference

### Key Files

- `core/nesting.py` - Nesting algorithms
- `core/exporter.py` - Export functionality
- `core/session_state.py` - In-memory state
- `core/units.py` - Unit conversions
- `gui/taskpanel_main.py` - Main UI
- `gui/taskpanel_settings.py` - Settings UI

### Key Commands

```bash
pytest                    # Run tests
ruff check . --fix       # Lint and autofix
pytest --collect-only    # Check test collection
ruff check .             # Lint only (no fix)
```

### Key Constraints

- **Hydration:** Before widgets, never modify defaults
- **Units:** mm internal, fractional imperial display
- **Exports:** Through exporter.py, use ExportJob
- **Python:** < 3.10 compatible, no relative imports
- **Testing:** Required for logic changes

---

## Version History

- **v1.0 (2026-02-08):** Consolidated from AGENTS.md + Project_Guide_v3.3.md
  - Removed constraint framework overhead
  - Simplified to essential rules
  - Single source of truth

---

**Questions?** Check `docs/` or ask the maintainer.

