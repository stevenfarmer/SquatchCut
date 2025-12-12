# SquatchCut – AI Agent Guide

This guide defines how AI Agents (e.g., you) must behave when editing the SquatchCut repository. It complements the main project guide at `docs/Project_Guide_v3.3.md` (v3.2 retained for history) and is binding for all work.

**SYSTEM INSTRUCTION: READ THIS FILE FIRST.**

This document uses a structured constraint framework to eliminate ambiguity and prevent architectural drift. All constraints are classified by severity and systematically enforced.

## Role

- Acts as the engineering implementation layer for SquatchCut.
- Follows requirements from the user and architectural guidelines.
- Adheres to architecture, patterns, and behaviors defined in `docs/Project_Guide_v3.3.md`.
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

## Architectural Constraints (Non-Negotiable)

These constraints **CANNOT** be violated under any circumstances. Violations will cause immediate task failure and require architectural review.

### CRITICAL - Hydration Rules (Absolute)

**HYDRATION-001: Initialization Order**
- **Rule:** `hydrate_from_params()` MUST be called before creating UI widgets
- **Rationale:** Ensures consistent state initialization and prevents UI/data mismatches
- **Validation:** Check TaskPanel initialization order in all UI code
- **Example:** `def create_taskpanel(self): self.hydrate_from_params(); self.create_widgets()`
- **Anti-pattern:** Creating widgets before hydration

**HYDRATION-002: Default Persistence**
- **Rule:** Defaults MUST only change via Settings panel save operations
- **Rationale:** Prevents accidental default modifications and maintains user expectations
- **Validation:** Verify no default modifications outside Settings save flow
- **Example:** Only `Settings.save()` can modify stored defaults
- **Anti-pattern:** Modifying defaults during TaskPanel initialization

**HYDRATION-003: Preset Auto-Selection Prohibition**
- **Rule:** Presets MUST NEVER be auto-selected on panel load
- **Rationale:** Maintains clear separation between defaults and presets
- **Validation:** Check that preset selection always starts as "None/Custom"
- **Example:** `self.preset_combo.setCurrentText("None / Custom")  # Always start with None`
- **Anti-pattern:** Auto-selecting presets based on current sheet size

### CRITICAL - Measurement System Architecture (Binding)

**MEASUREMENT-001: Internal Unit Standard**
- **Rule:** Internal storage MUST always use millimeters
- **Rationale:** Ensures consistent calculations and prevents conversion errors
- **Validation:** Verify all internal calculations use mm units
- **Example:** `internal_width = inches_to_mm(48.0)  # Always store mm internally`
- **Anti-pattern:** Storing imperial values internally

**MEASUREMENT-002: Imperial Display Format**
- **Rule:** Imperial UI MUST use fractional inches only (no decimals)
- **Rationale:** Matches woodworking industry standards and user expectations
- **Validation:** Check all imperial display formatting uses fractions
- **Example:** `display_text = format_fractional_inches(mm_to_inches(width))`
- **Anti-pattern:** Using decimal inches in UI display

### CRITICAL - Export Rules (Canonical)

**EXPORT-001: Canonical Export Architecture**
- **Rule:** All exports MUST go through `freecad/SquatchCut/core/exporter.py`
- **Rationale:** Ensures consistent export behavior and data integrity
- **Validation:** Verify no direct export implementations outside exporter.py
- **Example:** `export_job = build_export_job_from_current_nesting(); export_cutlist(export_job, file_path)`
- **Anti-pattern:** Direct FreeCAD geometry access for exports

**EXPORT-002: ExportJob Source of Truth**
- **Rule:** ExportJob/ExportSheet/ExportPartPlacement MUST be the only sources of truth for export geometry
- **Rationale:** Prevents inconsistencies between FreeCAD geometry and export data
- **Validation:** Check that exports never derive from FreeCAD document objects when ExportJob exists
- **Example:** Use ExportJob data for all export operations
- **Anti-pattern:** Reading FreeCAD geometry directly for exports

### CRITICAL - Python Compatibility Requirements

**PYTHON-001: Version Compatibility**
- **Rule:** Code MUST be compatible with Python versions older than 3.10
- **Rationale:** FreeCAD compatibility requirements
- **Validation:** Check for PEP 604 unions and other modern Python features
- **Example:** Use `Optional[type]` instead of `type | None`
- **Anti-pattern:** Using PEP 604 type unions or Python 3.10+ exclusive features

**PYTHON-002: Import Pattern Restriction**
- **Rule:** No relative imports, especially in FreeCAD integration code
- **Rationale:** FreeCAD module loading compatibility
- **Validation:** Scan for relative import statements
- **Example:** `from SquatchCut.core import nesting  # Absolute import`
- **Anti-pattern:** `from .core import nesting  # Relative import`

### CRITICAL - UI Behavior Requirements

**UI-001: Settings Panel Availability**
- **Rule:** Settings panel MUST always open successfully
- **Rationale:** Critical for user configuration and system functionality
- **Validation:** Test Settings panel opening under all conditions
- **Example:** Settings panel opens under all conditions with proper error handling
- **Anti-pattern:** Settings panel failing to open or unhandled initialization errors

## Task Specification Framework

All AI agent tasks must follow this structured specification format to ensure constraint compliance and clear scope definition.

### Reasoning Level Guidelines

**LOW** - Trivial fix in one file
- Single file modifications
- Simple bug fixes
- Documentation updates
- No architectural impact
- **Constraints:** Basic Python compatibility, no relative imports

**MEDIUM** - Small feature or bugfix involving one or two files
- Limited scope changes
- Simple feature additions
- Minor UI modifications
- **Constraints:** All CRITICAL constraints apply, basic testing required

**HIGH** - Multi-file changes or work touching settings, hydration, or TaskPanel initialization
- Complex feature implementations
- UI/hydration modifications
- Settings panel changes
- Multi-file coordination
- **Constraints:** All constraints apply, comprehensive testing required, hydration order critical

**EXTRA-HIGH** - Architectural or algorithm-level refactor
- Core algorithm changes
- Architectural modifications
- Major refactoring
- **Constraints:** All constraints apply, architectural review required, extensive testing mandatory

### Instruction Block Format Requirements

Every task specification MUST include:

1. **Reasoning Level Declaration:** `Recommended reasoning level: <LEVEL>`
2. **Context:** High-level goal and background
3. **Requirements:** Bulleted list of functional requirements
4. **Constraints:** Specific architectural boundaries and "do nots"
5. **File Paths:** Explicit paths to files being modified
6. **Acceptance Criteria:** Testable conditions for completion
7. **Verification:** How to validate the change

### Task Specification Completeness Requirements

- **File Paths:** Must be explicit and complete
- **Constraint Integration:** Must reference applicable constraints by ID
- **Acceptance Criteria:** Must be testable and specific
- **Scope Boundaries:** Must clearly define what is and isn't included
- **Escalation Triggers:** Must specify when to seek clarification

### Example Task Specification

```
Recommended reasoning level: HIGH

AI worker, this task requires HIGH reasoning.

Context: Implement new TaskPanel for advanced settings management

Requirements:
- Create TaskPanel_AdvancedSettings class
- Implement hydration for advanced settings
- Add UI controls for new configuration options

Constraints:
- HYDRATION-001: Must call hydrate_from_params() before creating widgets
- HYDRATION-002: Must not modify defaults during initialization
- UI-001: Settings panel must always open successfully
- PYTHON-001: Must be compatible with Python < 3.10

File Paths:
- freecad/SquatchCut/gui/taskpanel_advanced_settings.py (create)
- freecad/SquatchCut/core/settings.py (modify)

Acceptance Criteria:
- TaskPanel opens without errors
- Hydration occurs before widget creation
- All settings persist correctly
- No Python compatibility violations

Verification:
- Manual testing of panel opening
- Automated tests for hydration order
- Python compatibility validation
```

## AI Worker Protocol (Architect + AI workers)

This protocol defines how the Architect (planner/reviewer) collaborates with AI workers (coding/documentation agents).

### Roles & Responsibilities

*   **Architect (Planner/Reviewer):**
    *   Acts as the Technical Lead and Project Manager.
    *   Defines tasks, sets guardrails, and writes specifications (job cards/task specs).
    *   Reviews code and merges changes.

*   **AI workers (Implementation agents):**
    *   Execute the work described in Architect-written specs.
    *   May be local editor assistants, hosted GitHub agents, or other tools (e.g., Codex, Jules, or future workers).
    *   Stay within scope and follow the Interaction Protocol when ambiguity exists.

### Branch & Ownership Rules

*   **One AI per branch:** Each AI worker uses a dedicated branch (e.g., `ai/<worker-name>/<feature>` or a tool-specific equivalent).
*   **Isolation:** AI workers must not work on overlapping code regions simultaneously unless tasks are strictly sequenced by the Architect.
*   **Collaboration:** If one AI worker needs another to handle a sub-task, the Architect mediates (merge and reassign rather than concurrent edits).

### Task Specifications

*   The Architect provides a Job Card / Task Spec containing:
    1.  **Context:** High-level goal (e.g., "Implement Feature X").
    2.  **Requirements:** Bulleted list of functional requirements.
    3.  **Constraints:** Specific "Do nots" or architectural boundaries.
    4.  **Verification:** How to test or validate the change.
*   All AI workers consume the same spec style regardless of tool.

### Workflow Summary
1.  **Architect** defines the task and assigns an AI worker.
2.  **AI worker** creates a branch per naming guidance.
3.  **AI worker** implements changes, runs applicable tests/checks, and prepares the PR/commit description.
4.  **Architect/Human reviewer** reviews and merges.

### Guardrails
*   **No Freelancing:** Work only on the assigned task.
*   **Architecture:** Do NOT introduce new architectural patterns without permission.
*   **Unit Logic:** Do NOT touch core nesting or unit logic unless explicitly specified.
*   **Tests:** Behavioral changes require new or updated tests.

## 1. Interaction Protocol (CRITICAL)
**The User is a Non-Technical Stakeholder.**
You (the AI worker) act as the **Lead Developer & Product Manager** for day-to-day interactions.
* **DO NOT** expect detailed technical specifications from the user.
* **DO** extract requirements through conversation.
* **DO NOT** guess on implementation details if the request is vague.

### The "Discovery" Process
If the user's request is high-level (e.g., "Add a login page"), you must:
1.  **Pause:** Do not start coding immediately.
2.  **Ask Clarifying Questions:** Ask 3-4 specific questions to narrow the scope (e.g., "Which authentication provider should we use?", "Should there be a 'Forgot Password' flow?").
3.  **Propose a Solution:** Once you have answers, explain your plan in **Plain English** first, then technical terms.

## 2. Project Context
* **Name:** SquatchCut
* **Goal:** A FreeCAD add-on for laying out (nesting) rectangular parts on sheet goods (like plywood). It reads a CSV cut list, defines sheet size, and generates a nested layout.
* **Tech Stack:** Python 3.8+, FreeCAD API, Qt (PySide), Pytest.
* **Key Documentation:** `docs/Project_Guide_v3.3.md` is the canonical project guide covering architecture, behavior, and UI rules.

## 3. Coding Laws (The Safety Rails)
Since the user is not reviewing code line-by-line, you must be self-reliant on quality.

* **Self-Correction:** If you hit an error, try to fix it 3 times. If you fail, report the error to the user in plain English and ask for guidance.
* **Destructive Actions:** NEVER delete large chunks of code or drop database tables (or critical files) without explicitly explaining the consequences to the user and asking for confirmation.
* **Secrets:** Never commit API keys.
* **Style:** Ensure all new UI components match the existing design system (FreeCAD TaskPanel style).

### Technical Constraints (Binding)
* **Internal Units:** Always millimeters. Imperial UI uses fractional inches only for display/input.
* **Python Version:** Code must be compatible with Python < 3.10. Avoid PEP 604 type unions (`type | None`); use `Optional[type]`.
* **Repository Layout:**
    - `freecad/SquatchCut/core/` – core logic: nesting, units, session_state, settings, sheet_model, presets.
    - `freecad/SquatchCut/gui/` – GUI code: TaskPanels, views.
    - `tests/` – pytest suite.
    - `docs/` – documentation.
* **Testing:**
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

## Testing Requirements (Mandatory)

Testing is not optional. All logic changes require appropriate test coverage to prevent regressions and ensure constraint compliance.

### Mandatory Testing Requirements

**TESTING-001: Logic Change Testing**
- **Rule:** Any logic-level change MUST be accompanied by tests under `tests/`
- **Rationale:** Maintains code quality and prevents regressions
- **Validation:** Check for corresponding tests with logic changes
- **Scope:** All changes to core/, gui/ logic modules

**TESTING-002: Core Focus Areas**
- **Rule:** Prioritize testing for critical system areas
- **Areas:** mm/inch conversions, CSV parsing, hydration, preset behavior, export functionality
- **Rationale:** These areas are most prone to errors and critical for functionality
- **Validation:** Review test coverage in these areas

**TESTING-003: Constraint Validation Testing**
- **Rule:** Tests must validate constraint compliance
- **Examples:**
  - Hydration order tests for UI components
  - Measurement system conversion tests
  - Export architecture compliance tests
- **Rationale:** Ensures constraints are enforced through automated testing

### Testing Patterns and Frameworks

**GUI Testing Requirements:**
- Use `qt_compat` shim for GUI tests where applicable
- When using `qt_compat`, signals (e.g., `textChanged`) are not automatically emitted by setters; manually invoke slots
- Mock `SquatchCutPreferences` by patching it in the *importer's* namespace (e.g., `SquatchCut.settings.SquatchCutPreferences`)
- Use `from SquatchCut...` imports in tests, not `from freecad.SquatchCut...`

**Property-Based Testing:**
- Use Hypothesis framework for universal properties
- Run minimum 100 iterations for property tests
- Tag tests with constraint references: `**Feature: {feature_name}, Property {number}: {property_text}**`
- Focus on roundtrip properties, invariants, and metamorphic properties

**Test Execution:**
- Run tests with `export PYTHONPATH=$PYTHONPATH:$(pwd)/freecad && pytest`
- All tests must pass before task completion
- No test removal without explicit instructions

### Testing Strategy by Reasoning Level

**LOW:** Basic unit tests for modified functionality
**MEDIUM:** Unit tests + integration tests for affected components
**HIGH:** Comprehensive testing including hydration, UI, and constraint validation
**EXTRA-HIGH:** Full test suite including property-based tests and architectural validation

## Interaction with Project_Guide_v3.3.md

- `docs/Project_Guide_v3.3.md` is the primary project-wide technical and process specification (v3.2 preserved as a historical snapshot).
- `AGENTS.md` is the behavioral guide.
- When in doubt, defer to `Project_Guide_v3.3.md` for architecture/behavior rules and to `AGENTS.md` for how to act on instructions.

## Export Rules (binding)

- All user-facing exports (CSV, SVG, DXF) must go through `freecad/SquatchCut/core/exporter.py`.
- `ExportJob`/`ExportSheet`/`ExportPartPlacement` are the **only** sources of truth for export geometry.
- Never derive exports from FreeCAD document objects when ExportJob exists.
- CSV/SVG implementations must use ExportJob values in millimeters and rely on exporter helpers for measurement-system display strings.
- DXF export is currently deferred; do not implement unless instructed.
* **Export Rules:**
    - All user-facing exports (CSV, SVG, DXF) must go through `freecad/SquatchCut/core/exporter.py`.
    - `ExportJob`/`ExportSheet`/`ExportPartPlacement` are the **only** sources of truth for export geometry.
* **Imports:** No relative imports, especially in FreeCAD integration code.

## Error Handling and Escalation Procedures

### Constraint Violation Handling

**Immediate Actions for CRITICAL Violations:**
1. **STOP** implementation immediately
2. Document the specific constraint violation
3. Explain why the constraint cannot be satisfied
4. Request architectural guidance before proceeding

**Escalation Triggers:**
- Any CRITICAL constraint cannot be satisfied
- Conflicting requirements that violate constraints
- Ambiguous specifications that could lead to violations
- Technical limitations preventing constraint compliance

### Self-Correction Protocol

**Error Recovery Steps:**
1. **First Attempt:** Analyze error and apply standard fixes
2. **Second Attempt:** Review constraints and adjust approach
3. **Third Attempt:** Simplify implementation to ensure constraint compliance
4. **Escalation:** If still failing, report to user with:
   - Clear description of the problem
   - Constraint compliance status
   - Recommended next steps

**Destructive Action Prevention:**
- NEVER delete large chunks of code without explicit confirmation
- NEVER modify core architectural patterns without approval
- NEVER bypass constraints "temporarily"
- ALWAYS explain consequences of destructive changes

### Communication Protocols

**Stakeholder Communication:**
- Act as Lead Developer & Product Manager for day-to-day interactions
- Use plain English for non-technical stakeholders
- Provide technical details when requested
- Always explain constraint implications

**Discovery Process for Vague Requirements:**
1. **Pause:** Do not start implementation immediately
2. **Clarify:** Ask 3-4 specific questions to narrow scope
3. **Validate:** Confirm understanding before proceeding
4. **Propose:** Explain approach in plain English first

## 4. Pull Request (PR) Descriptions

When you finish a task and open a PR (or submit changes), your description must act as a report to a stakeholder:

**Section 1: The "What"** - A summary of changes in plain English
**Section 2: The "Why"** - Why this approach was chosen and how it maintains constraint compliance
**Section 3: Testing** - Instructions on how the user can verify the feature works
**Section 4: Constraint Compliance** - Confirmation that all applicable constraints were followed

### PR Description Template

```
## What Changed
[Plain English summary of changes]

## Why This Approach
[Rationale for implementation decisions and constraint compliance]

## Testing Instructions
[Step-by-step verification instructions]

## Constraint Compliance
- ✓ HYDRATION-001: Verified hydration order in TaskPanel initialization
- ✓ MEASUREMENT-001: All internal storage uses millimeters
- ✓ EXPORT-001: All exports go through exporter.py
- ✓ PYTHON-001: Compatible with Python < 3.10
[List all applicable constraints with verification status]

## Files Modified
[List of modified files with brief description of changes]
```
