# SquatchCut AI Agent Handbook

**Comprehensive Reference Guide for AI Agents Working on SquatchCut**

Version: 1.0
Last Updated: December 2025
Applies to: All AI agents (local assistants, hosted agents, coding tools)

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Architectural Constraints](#architectural-constraints)
3. [Task Specification Guidelines](#task-specification-guidelines)
4. [Code Examples and Patterns](#code-examples-and-patterns)
5. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
6. [Testing Requirements](#testing-requirements)
7. [Error Handling and Escalation](#error-handling-and-escalation)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Validation Tools](#validation-tools)
10. [Appendices](#appendices)

---

## Quick Reference

### Critical Constraints Checklist

**Before starting ANY task, verify:**

- [ ] **HYDRATION-001**: Will call `hydrate_from_params()` before creating UI widgets
- [ ] **MEASUREMENT-001**: Will store all values internally in millimeters
- [ ] **EXPORT-001**: Will use `freecad/SquatchCut/core/exporter.py` for all exports
- [ ] **PYTHON-001**: Will maintain compatibility with Python < 3.10
- [ ] **UI-001**: Will ensure Settings panel can always open

### Reasoning Level Quick Guide

| Level | Scope | Key Constraints | Testing Required |
|-------|-------|----------------|------------------|
| **LOW** | Single file, trivial | Python compatibility | Basic unit tests |
| **MEDIUM** | 1-2 files, simple feature | All CRITICAL | Unit + integration |
| **HIGH** | Multi-file, UI/hydration | All constraints | Comprehensive testing |
| **EXTRA-HIGH** | Architectural changes | All + review | Full test suite |

### Emergency Escalation Triggers

**STOP and escalate immediately if:**
- Any CRITICAL constraint cannot be satisfied
- Requirements conflict with existing constraints
- Architectural changes are needed to meet requirements
- Technical limitations prevent constraint compliance

---
## Architectural Constraints

### CRITICAL Constraints (Cannot Be Violated)

#### HYDRATION-001: Initialization Order
**Rule:** `hydrate_from_params()` MUST be called before creating UI widgets

**Why This Matters:**
- Ensures consistent state initialization
- Prevents UI/data mismatches
- Maintains predictable behavior across all TaskPanels

**How to Validate:**
```python
# Check TaskPanel initialization order
def __init__(self):
    # 1. Load session state
    self.session = get_session_state()

    # 2. CRITICAL: Call hydration FIRST
    self.hydrate_from_params()

    # 3. THEN create widgets
    self.create_widgets()

    # 4. Populate with hydrated values
    self.populate_ui_values()
```

**Common Violations:**
- Creating widgets before hydration
- Accessing GUI modules from hydration functions
- Modifying defaults during hydration

---

#### HYDRATION-002: Default Persistence
**Rule:** Defaults MUST only change via Settings panel save operations

**Why This Matters:**
- Prevents accidental default modifications
- Maintains user expectations about settings persistence
- Ensures clear separation between temporary and permanent changes

**How to Validate:**
```python
# CORRECT: Only Settings.save() modifies defaults
def save_settings(self):
    self.settings.set_default_sheet_width(self.width_value)
    self.settings.save()  # Only place defaults change

# WRONG: TaskPanel modifying defaults
def load_taskpanel(self):
    # Never do this - modifies stored defaults
    self.settings.set_default_sheet_width(new_value)
```

---

#### MEASUREMENT-001: Internal Unit Standard
**Rule:** Internal storage MUST always use millimeters

**Why This Matters:**
- Ensures consistent calculations across all modules
- Prevents conversion errors and precision loss
- Maintains compatibility with FreeCAD's internal units

**How to Validate:**
```python
# CORRECT: Always convert to mm for internal storage
def set_sheet_width(self, user_input, units_system):
    if units_system == "imperial":
        width_mm = inches_to_mm(parse_fractional_inches(user_input))
    else:
        width_mm = float(user_input)  # Already in mm

    self.sheet_width = width_mm  # Store in mm

# WRONG: Storing imperial values internally
def set_sheet_width(self, user_input):
    self.sheet_width = user_input  # Could be inches!
```

---

#### EXPORT-001: Canonical Export Architecture
**Rule:** All exports MUST go through `freecad/SquatchCut/core/exporter.py`

**Why This Matters:**
- Ensures consistent export behavior across all formats
- Maintains data integrity between FreeCAD geometry and exports
- Provides single source of truth for export logic

**How to Validate:**
```python
# CORRECT: Use canonical export architecture
def export_cutlist(self, file_path):
    export_job = build_export_job_from_current_nesting()
    export_cutlist(export_job, file_path)

# WRONG: Direct FreeCAD geometry access
def export_cutlist(self, file_path):
    parts = FreeCAD.ActiveDocument.getObjectsByLabel("SquatchCut_NestedParts")
    # Direct geometry access violates architecture
```

---

### IMPORTANT Constraints (Require Approval to Violate)

#### UI-002: TaskPanel Initialization Pattern
**Rule:** Follow specific TaskPanel initialization order

**Required Order:**
1. Load session_state
2. Call hydrate_from_params()
3. Create all UI widgets
4. Populate UI values from hydrated state
5. Apply measurement formatting
6. Connect signals
7. Render panel

#### REPOSITORY-001: Directory Structure
**Rule:** Maintain established directory structure

**Structure:**
- `freecad/SquatchCut/core/` – Pure logic, no GUI dependencies
- `freecad/SquatchCut/gui/` – UI components, TaskPanels, commands
- `freecad/SquatchCut/resources/` – Icons, templates, static files
- `tests/` – All test files
- `docs/` – Documentation

---
## Task Specification Guidelines

### Complete Task Specification Template

Every AI agent task must include all of these elements:

```markdown
**Reasoning Level:** [LOW|MEDIUM|HIGH|EXTRA-HIGH]

**Context:**
[High-level goal and background - minimum 20 characters]

**Requirements:**
- [Specific functional requirement 1]
- [Specific functional requirement 2]
- [Additional requirements as needed]

**File Paths:**
- [Exact path to file 1] (create/modify/delete)
- [Exact path to file 2] (create/modify/delete)

**Constraints:**
- [CONSTRAINT-ID]: [Brief description of how it applies]
- [Additional applicable constraints]

**Acceptance Criteria:**
- [Testable condition 1 - must be verifiable]
- [Testable condition 2 - must be verifiable]
- [Additional criteria as needed]

**Verification:**
- [How to test/validate the change]
- [Specific steps to confirm success]
```

### Reasoning Level Selection Guide

#### LOW Reasoning Tasks
**Characteristics:**
- Single file modifications
- Simple bug fixes
- Documentation updates
- No architectural impact

**Example:**
```markdown
**Reasoning Level:** LOW

**Context:** Fix typo in user documentation

**Requirements:**
- Correct spelling error in docs/user_guide.md
- Maintain existing formatting

**File Paths:**
- docs/user_guide.md (modify)

**Constraints:**
- PYTHON-001: N/A (documentation only)

**Acceptance Criteria:**
- Typo is corrected
- No formatting changes
- Document remains readable

**Verification:**
- Visual inspection of corrected text
- Markdown renders correctly
```

#### HIGH Reasoning Tasks
**Characteristics:**
- Multi-file changes
- UI/hydration modifications
- Settings panel changes
- Complex feature implementations

**Example:**
```markdown
**Reasoning Level:** HIGH

**Context:** Implement new advanced settings TaskPanel

**Requirements:**
- Create TaskPanel_AdvancedSettings class
- Implement proper hydration order
- Add UI controls for advanced options
- Integrate with existing settings system

**File Paths:**
- freecad/SquatchCut/gui/taskpanel_advanced_settings.py (create)
- freecad/SquatchCut/core/settings.py (modify)
- tests/test_taskpanel_advanced_settings.py (create)

**Constraints:**
- HYDRATION-001: Must call hydrate_from_params() before creating widgets
- HYDRATION-002: Must not modify defaults during initialization
- UI-001: Settings panel must always open successfully
- PYTHON-001: Must be compatible with Python < 3.10

**Acceptance Criteria:**
- TaskPanel opens without errors
- Hydration occurs before widget creation
- All settings persist correctly
- No Python compatibility violations
- Comprehensive test coverage

**Verification:**
- Manual testing of panel opening
- Automated tests for hydration order
- Python compatibility validation
- Test suite passes
```

### Constraint Integration Requirements

**For every task, you must:**

1. **Identify Applicable Constraints**
   - Review file paths to determine relevant constraint areas
   - Check reasoning level for constraint scope
   - Include all CRITICAL constraints that apply

2. **Reference Constraints Explicitly**
   - Use constraint IDs (e.g., HYDRATION-001)
   - Explain how each constraint applies to your task
   - Include validation steps for each constraint

3. **Plan Constraint Validation**
   - Specify how you'll verify constraint compliance
   - Include constraint checks in acceptance criteria
   - Plan testing that validates constraint adherence

---
## Code Examples and Patterns

### Hydration Patterns

#### Correct TaskPanel Initialization
```python
class TaskPanel_Example:
    def __init__(self):
        # 1. Initialize basic attributes
        self.form = None
        self.session = None

        # 2. CRITICAL: Hydrate before anything else
        self.hydrate_from_params()

        # 3. Create UI after hydration
        self.create_widgets()

        # 4. Populate with hydrated values
        self.populate_ui_values()

        # 5. Connect signals last
        self.connect_signals()

    def hydrate_from_params(self):
        """Load persistent values - NO GUI ACCESS"""
        self.session = get_session_state()
        self.sheet_width = self.session.get_sheet_width()
        self.sheet_height = self.session.get_sheet_height()
        # Never access self.form or GUI elements here

    def create_widgets(self):
        """Create UI widgets after hydration"""
        self.form = QtWidgets.QWidget()
        self.width_input = QtWidgets.QLineEdit()
        self.height_input = QtWidgets.QLineEdit()
        # Widget creation happens here

    def populate_ui_values(self):
        """Populate widgets with hydrated values"""
        self.width_input.setText(str(self.sheet_width))
        self.height_input.setText(str(self.sheet_height))
```

#### Correct Preset Handling
```python
def load_taskpanel(self):
    """Always start with None preset, never auto-select"""
    # CORRECT: Always start with None
    self.preset_combo.setCurrentText("None / Custom")

    # Load defaults (not presets)
    self.width_input.setText(str(self.default_width))
    self.height_input.setText(str(self.default_height))

def on_preset_selected(self, preset_name):
    """Handle preset selection without modifying defaults"""
    if preset_name == "4' x 8'":
        # Update UI fields (not defaults)
        self.width_input.setText("48")
        self.height_input.setText("96")
        # NEVER: self.settings.set_default_width(48)
```

### Measurement System Patterns

#### Correct Unit Conversion
```python
def handle_user_input(self, user_value, measurement_system):
    """Always convert to mm for internal storage"""
    if measurement_system == "imperial":
        # Parse fractional inches
        inches_value = parse_fractional_inches(user_value)
        # Convert to mm for internal storage
        mm_value = inches_to_mm(inches_value)
    else:
        # Already in mm
        mm_value = float(user_value)

    # Store internally in mm
    self.internal_width = mm_value
    return mm_value

def format_for_display(self, mm_value, measurement_system):
    """Format for UI display"""
    if measurement_system == "imperial":
        inches_value = mm_to_inches(mm_value)
        return format_fractional_inches(inches_value)
    else:
        return f"{mm_value:.1f} mm"
```

#### Correct Measurement System Switching
```python
def on_measurement_system_changed(self, new_system):
    """Reformat all UI fields when system changes"""
    # Get current values in mm (internal storage)
    width_mm = self.get_internal_width()
    height_mm = self.get_internal_height()

    # Reformat all numeric fields
    self.width_input.setText(self.format_for_display(width_mm, new_system))
    self.height_input.setText(self.format_for_display(height_mm, new_system))
    self.kerf_input.setText(self.format_for_display(self.kerf_mm, new_system))

    # Update labels
    self.update_unit_labels(new_system)
```

### Export Architecture Patterns

#### Correct Export Implementation
```python
def export_cutlist(self, file_path):
    """Use canonical export architecture"""
    # 1. Build ExportJob from current nesting
    export_job = build_export_job_from_current_nesting()

    # 2. Use exporter.py functions
    from SquatchCut.core.exporter import export_cutlist
    export_cutlist(export_job, file_path)

    # Never access FreeCAD geometry directly

def export_svg(self, file_path):
    """SVG export through canonical architecture"""
    export_job = build_export_job_from_current_nesting()

    from SquatchCut.core.exporter import export_nesting_to_svg
    export_nesting_to_svg(export_job, file_path)
```

### Testing Patterns

#### Unit Test Pattern
```python
def test_hydration_order():
    """Test that hydration occurs before widget creation"""
    # Create mock TaskPanel
    panel = TaskPanel_Test()

    # Verify hydration happened first
    assert panel.session is not None
    assert panel.sheet_width > 0

    # Verify widgets were created after
    assert panel.form is not None
    assert panel.width_input.text() == str(panel.sheet_width)
```

#### Property-Based Test Pattern
```python
@given(st.floats(min_value=0.1, max_value=10000.0))
def test_measurement_conversion_roundtrip(mm_value):
    """Property: mm -> inches -> mm should preserve value"""
    inches = mm_to_inches(mm_value)
    back_to_mm = inches_to_mm(inches)
    assert abs(mm_value - back_to_mm) < 0.001
```

---
## Anti-Patterns to Avoid

### Hydration Anti-Patterns

#### ❌ Widget Creation Before Hydration
```python
# WRONG - Creates widgets before hydration
def __init__(self):
    self.create_widgets()  # Too early!
    self.hydrate_from_params()  # Too late!
```

**Why This Fails:**
- Widgets may be populated with stale data
- Hydration can't properly initialize UI state
- Leads to inconsistent behavior

**Correct Approach:**
```python
def __init__(self):
    self.hydrate_from_params()  # First!
    self.create_widgets()       # Then widgets
```

#### ❌ GUI Access During Hydration
```python
# WRONG - Accessing GUI during hydration
def hydrate_from_params(self):
    self.sheet_width = get_default_width()
    self.width_input.setText(str(self.sheet_width))  # GUI access!
```

**Why This Fails:**
- Widgets may not exist yet
- Violates separation of concerns
- Makes testing difficult

#### ❌ Preset Auto-Selection
```python
# WRONG - Auto-selecting presets
def load_panel(self):
    if self.sheet_width == 1220 and self.sheet_height == 2440:
        self.preset_combo.setCurrentText("4' x 8'")  # Auto-selection!
```

**Why This Fails:**
- Violates preset/default separation
- Confuses users about what's a default vs preset
- Makes behavior unpredictable

### Measurement System Anti-Patterns

#### ❌ Imperial Internal Storage
```python
# WRONG - Storing imperial values internally
def set_width(self, inches_value):
    self.width = inches_value  # Should be mm!
```

**Why This Fails:**
- Inconsistent with FreeCAD internal units
- Causes conversion errors
- Makes calculations unreliable

#### ❌ Decimal Inch Display
```python
# WRONG - Using decimal inches in UI
def format_imperial(self, mm_value):
    inches = mm_to_inches(mm_value)
    return f"{inches:.2f} in"  # Decimal inches!
```

**Why This Fails:**
- Doesn't match woodworking standards
- Users expect fractional inches
- Inconsistent with project requirements

#### ❌ Mixed Unit Calculations
```python
# WRONG - Mixing units in calculations
def calculate_area(self):
    width_inches = self.width_input.text()  # Could be inches
    height_mm = self.height_mm              # Definitely mm
    return float(width_inches) * height_mm  # Mixed units!
```

### Export Anti-Patterns

#### ❌ Direct FreeCAD Geometry Access
```python
# WRONG - Bypassing export architecture
def export_parts(self):
    doc = FreeCAD.ActiveDocument
    parts = doc.getObjectsByLabel("SquatchCut_NestedParts")
    for part in parts:
        # Direct geometry access violates architecture
        write_to_csv(part.Shape.BoundBox)
```

**Why This Fails:**
- Bypasses canonical export data model
- Creates inconsistencies between exports
- Makes export behavior unpredictable

#### ❌ Custom Export Functions
```python
# WRONG - Creating custom export outside exporter.py
def my_custom_export(self, file_path):
    # Custom export logic outside canonical architecture
    pass
```

**Why This Fails:**
- Violates single source of truth principle
- Creates maintenance burden
- Leads to inconsistent export behavior

### Python Compatibility Anti-Patterns

#### ❌ PEP 604 Type Unions
```python
# WRONG - Using modern Python syntax
def process_value(self, value: str | None) -> int | None:
    pass
```

**Why This Fails:**
- Not compatible with Python < 3.10
- Causes syntax errors in FreeCAD
- Breaks compatibility requirements

**Correct Approach:**
```python
from typing import Optional

def process_value(self, value: Optional[str]) -> Optional[int]:
    pass
```

#### ❌ Relative Imports
```python
# WRONG - Using relative imports
from .core import nesting
from ..gui import commands
```

**Why This Fails:**
- Incompatible with FreeCAD module loading
- Causes import errors
- Violates project requirements

### UI Anti-Patterns

#### ❌ Multiple TaskPanel Instances
```python
# WRONG - Creating multiple instances
def show_settings(self):
    if not hasattr(self, 'settings_panel'):
        self.settings_panel = TaskPanel_Settings()
    # Creates new instance each time
    new_panel = TaskPanel_Settings()
```

**Why This Fails:**
- Wastes resources
- Can cause conflicts
- Violates singleton pattern

#### ❌ UI Overflow Ignorance
```python
# WRONG - Not considering narrow docks
def create_layout(self):
    # Fixed width layout that overflows
    self.setFixedWidth(800)  # Too wide for narrow docks
```

**Why This Fails:**
- Makes UI unusable on narrow docks
- Poor user experience
- Violates responsive design principles

---
## Testing Requirements

### Mandatory Testing by Reasoning Level

#### LOW Reasoning - Basic Testing
**Required:**
- Unit tests for modified functions
- Python compatibility validation

**Example:**
```python
def test_simple_function():
    """Test the modified function works correctly"""
    result = simple_function("input")
    assert result == "expected_output"

def test_python_compatibility():
    """Ensure no modern Python features used"""
    # Check for PEP 604 unions, etc.
    pass
```

#### MEDIUM Reasoning - Standard Testing
**Required:**
- Unit tests for all modified logic
- Integration tests for component interactions
- Constraint compliance validation

#### HIGH Reasoning - Comprehensive Testing
**Required:**
- Unit tests for all logic changes
- Integration tests for multi-component changes
- GUI tests using qt_compat patterns
- Hydration order validation tests
- Constraint compliance tests
- Property-based tests for universal properties

**Example GUI Test:**
```python
def test_taskpanel_hydration_order():
    """Test hydration occurs before widget creation"""
    with patch('SquatchCut.core.session_state.get_session_state') as mock_session:
        mock_session.return_value = MockSession()

        panel = TaskPanel_Test()

        # Verify hydration happened
        assert panel.session is not None
        assert panel.sheet_width > 0

        # Verify widgets exist and are populated
        assert panel.form is not None
        assert panel.width_input.text() == str(panel.sheet_width)
```

#### EXTRA-HIGH Reasoning - Full Test Suite
**Required:**
- All previous testing requirements
- Architectural validation tests
- Performance regression tests
- Cross-platform compatibility tests
- Property-based tests with high iteration counts

### Core Testing Areas

#### Measurement System Testing
**Always Required When:**
- Modifying units.py or text_helpers.py
- Changing measurement display logic
- Adding new unit conversion functions

**Test Pattern:**
```python
@given(st.floats(min_value=0.1, max_value=10000.0))
def test_measurement_roundtrip(mm_value):
    """Property: mm -> inches -> mm preserves value"""
    inches = mm_to_inches(mm_value)
    back_to_mm = inches_to_mm(inches)
    assert abs(mm_value - back_to_mm) < 0.001

def test_fractional_parsing():
    """Test fractional inch parsing"""
    assert parse_fractional_inches("48 3/4") == 48.75
    assert parse_fractional_inches("1/2") == 0.5
    assert parse_fractional_inches("12") == 12.0
```

#### Hydration Testing
**Always Required When:**
- Modifying TaskPanel initialization
- Changing session_state or settings
- Adding new persistent values

**Test Pattern:**
```python
def test_hydration_before_widgets():
    """Ensure hydration occurs before widget creation"""
    panel = TaskPanel_Test()

    # Hydration should have occurred
    assert hasattr(panel, 'session')
    assert panel.session is not None

    # Widgets should be created after
    assert hasattr(panel, 'form')
    assert panel.form is not None

def test_preset_never_auto_selected():
    """Ensure presets are never auto-selected"""
    panel = TaskPanel_Test()

    # Should always start with None/Custom
    assert panel.preset_combo.currentText() == "None / Custom"
```

#### Export Testing
**Always Required When:**
- Modifying exporter.py
- Adding new export formats
- Changing export data models

**Test Pattern:**
```python
def test_export_uses_canonical_architecture():
    """Ensure exports go through exporter.py"""
    with patch('SquatchCut.core.exporter.export_cutlist') as mock_export:
        export_cutlist_command()

        # Should call canonical export function
        mock_export.assert_called_once()

def test_export_job_data_integrity():
    """Test ExportJob contains correct data"""
    export_job = build_export_job_from_current_nesting()

    assert export_job.measurement_system in ["metric", "imperial"]
    assert len(export_job.sheets) > 0
    assert all(sheet.width_mm > 0 for sheet in export_job.sheets)
```

### Property-Based Testing Guidelines

**Use Property Tests For:**
- Universal mathematical properties (roundtrip, invariants)
- Algorithm correctness across many inputs
- Data integrity across transformations
- Constraint validation across scenarios

**Property Test Template:**
```python
@given(st.lists(valid_parts(), min_size=1, max_size=20))
@settings(max_examples=100, deadline=5000)
def test_nesting_no_overlaps(parts):
    """Property: Nested parts should never overlap"""
    **Feature: constraint-validation, Property 1: No Overlaps**

    layout = nest_parts(parts, sheet_size=(1220, 2440))

    # Check no overlaps
    for i, part1 in enumerate(layout):
        for part2 in layout[i+1:]:
            assert not parts_overlap(part1, part2)
```

### Testing Tools and Patterns

#### qt_compat Usage
```python
from SquatchCut.gui.qt_compat import QtWidgets

def test_gui_component():
    """Test GUI component using qt_compat"""
    widget = QtWidgets.QLineEdit()
    widget.setText("test")

    # Manually trigger signal (qt_compat doesn't auto-emit)
    widget.textChanged.emit("test")

    assert widget.text() == "test"
```

#### Mock Patterns
```python
# Mock preferences in importer's namespace
@patch('SquatchCut.settings.SquatchCutPreferences')
def test_settings_behavior(mock_prefs):
    mock_prefs.return_value.get_sheet_width.return_value = 1220

    # Test code that uses preferences
    result = function_that_uses_preferences()
    assert result == expected_value
```

---
## Error Handling and Escalation

### Escalation Decision Tree

```
┌─ Constraint Violation Detected ─┐
│                                  │
├─ CRITICAL Constraint? ──────────┼─ YES ─► STOP ─► Escalate Immediately
│                                  │
├─ NO ─► IMPORTANT Constraint? ───┼─ YES ─► Document ─► Request Approval
│                                  │
├─ NO ─► RECOMMENDED? ────────────┼─ YES ─► Note in PR ─► Continue
│                                  │
└─ NO ─► Continue ────────────────┘
```

### Immediate Escalation Scenarios

**STOP and escalate immediately when:**

1. **CRITICAL Constraint Cannot Be Satisfied**
   ```
   Scenario: Task requires modifying hydration order
   Action: STOP - Document why HYDRATION-001 cannot be satisfied
   Escalation: Request architectural guidance
   ```

2. **Conflicting Requirements**
   ```
   Scenario: Requirement conflicts with MEASUREMENT-001
   Action: STOP - Document the conflict clearly
   Escalation: Request requirement clarification
   ```

3. **Technical Limitations**
   ```
   Scenario: Python < 3.10 prevents required functionality
   Action: STOP - Document technical limitation
   Escalation: Request alternative approach or constraint exception
   ```

4. **Architectural Changes Needed**
   ```
   Scenario: Task requires changing core export architecture
   Action: STOP - Document required architectural changes
   Escalation: Request architectural review and approval
   ```

### Self-Correction Protocol

#### First Attempt - Standard Fixes
- Review constraint requirements
- Check for common anti-patterns
- Verify Python compatibility
- Run basic validation tests

#### Second Attempt - Constraint-Focused
- Re-read applicable constraints carefully
- Validate each constraint individually
- Simplify approach to ensure compliance
- Focus on minimal viable implementation

#### Third Attempt - Minimal Compliance
- Strip down to absolute minimum requirements
- Ensure all CRITICAL constraints are satisfied
- Document any IMPORTANT constraints that cannot be met
- Prepare for escalation if still failing

#### Escalation After Three Attempts
**Required Information:**
- Clear description of the problem
- Constraint compliance status for each applicable constraint
- What was attempted and why it failed
- Recommended next steps or alternative approaches

### Error Communication Templates

#### Constraint Violation Report
```markdown
## Constraint Violation Report

**Constraint ID:** HYDRATION-001
**Severity:** CRITICAL
**Task:** [Brief task description]

**Problem:**
[Clear description of why constraint cannot be satisfied]

**Attempted Solutions:**
1. [First attempt and why it failed]
2. [Second attempt and why it failed]
3. [Third attempt and why it failed]

**Impact:**
[What happens if constraint is violated]

**Recommended Action:**
[Suggested next steps - architectural review, requirement change, etc.]
```

#### Technical Limitation Report
```markdown
## Technical Limitation Report

**Task:** [Brief task description]
**Limitation:** [Specific technical constraint]

**Problem:**
[Detailed explanation of the technical limitation]

**Constraint Impact:**
- PYTHON-001: [How Python < 3.10 prevents solution]
- [Other affected constraints]

**Alternative Approaches:**
1. [Alternative 1 with pros/cons]
2. [Alternative 2 with pros/cons]

**Recommendation:**
[Preferred alternative or request for guidance]
```

### Communication Protocols

#### Stakeholder Communication
**For Non-Technical Users:**
- Use plain English explanations
- Focus on impact and solutions, not technical details
- Provide clear next steps
- Explain timeline implications

**Example:**
```
The new settings panel cannot be implemented as requested because it would
break the way SquatchCut initializes its interface. This could cause the
settings to not save properly or the panel to fail to open.

I recommend we modify the approach to work within SquatchCut's architecture.
This will take an additional day but ensures the feature works reliably.

Would you like me to proceed with the modified approach, or would you prefer
to discuss alternative solutions?
```

#### Technical Communication
**For Architects/Developers:**
- Include specific constraint IDs and technical details
- Provide code examples where relevant
- Reference specific files and line numbers
- Include proposed technical solutions

### Recovery Procedures

#### After Constraint Violation
1. **Document the violation** - What constraint, why it happened
2. **Assess impact** - What functionality is affected
3. **Plan remediation** - How to fix while maintaining compliance
4. **Implement fix** - Make minimal changes to restore compliance
5. **Validate compliance** - Verify all constraints are satisfied
6. **Update tests** - Ensure tests catch similar violations

#### After Technical Failure
1. **Isolate the problem** - Identify root cause
2. **Check constraints** - Verify no constraints were violated during failure
3. **Simplify approach** - Reduce complexity to essential requirements
4. **Implement incrementally** - Build up functionality step by step
5. **Test thoroughly** - Validate each step before proceeding

---
## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: TaskPanel Won't Open
**Symptoms:**
- Settings panel fails to load
- Error messages about missing attributes
- UI components not appearing

**Diagnosis Checklist:**
- [ ] Is `hydrate_from_params()` called before widget creation?
- [ ] Are all required session_state values available?
- [ ] Are there any Python compatibility issues?
- [ ] Is the UI layout causing overflow?

**Solution Steps:**
1. Check hydration order in `__init__` method
2. Verify session_state initialization
3. Test with minimal UI layout
4. Check for Python < 3.10 compatibility

**Code Fix Example:**
```python
# BEFORE (broken)
def __init__(self):
    self.create_widgets()  # Too early
    self.hydrate_from_params()

# AFTER (fixed)
def __init__(self):
    self.hydrate_from_params()  # First
    self.create_widgets()       # Then widgets
```

#### Issue: Measurement Conversion Errors
**Symptoms:**
- Parts appear wrong size in nesting
- Export values don't match UI display
- Precision loss in calculations

**Diagnosis Checklist:**
- [ ] Are all internal values stored in mm?
- [ ] Is conversion happening at UI boundary only?
- [ ] Are fractional inches parsed correctly?
- [ ] Is display formatting consistent?

**Solution Steps:**
1. Verify all internal storage uses mm
2. Check conversion functions for precision
3. Validate fractional inch parsing
4. Test roundtrip conversions

#### Issue: Export Files Are Wrong
**Symptoms:**
- CSV contains incorrect values
- SVG doesn't match FreeCAD display
- Export fails silently

**Diagnosis Checklist:**
- [ ] Is export going through `exporter.py`?
- [ ] Is `ExportJob` being used as data source?
- [ ] Are measurement units consistent in export?
- [ ] Is export architecture being bypassed?

**Solution Steps:**
1. Verify export uses canonical architecture
2. Check `ExportJob` data integrity
3. Validate measurement system handling
4. Test export with known good data

#### Issue: Tests Are Failing
**Symptoms:**
- Unit tests fail after changes
- Property tests find counterexamples
- GUI tests can't find widgets

**Diagnosis Checklist:**
- [ ] Do tests reflect actual requirements?
- [ ] Are mocks set up correctly?
- [ ] Is qt_compat being used properly?
- [ ] Are property test assumptions valid?

**Solution Steps:**
1. Review test requirements vs implementation
2. Check mock setup and patching
3. Verify qt_compat signal handling
4. Validate property test generators

### Debugging Techniques

#### Constraint Validation Debugging
```python
# Add constraint checking to your code
from constraint_validation_tools import check_file_compliance

def debug_constraint_compliance():
    result = check_file_compliance("path/to/your/file.py")
    print(f"Violations found: {result['total_violations']}")
    for violation in result['violations']:
        print(f"- {violation['constraint_id']}: {violation['message']}")
```

#### Hydration Order Debugging
```python
class TaskPanel_Debug:
    def __init__(self):
        print("1. Starting initialization")

        print("2. Calling hydration")
        self.hydrate_from_params()
        print(f"   Hydrated width: {getattr(self, 'sheet_width', 'NOT SET')}")

        print("3. Creating widgets")
        self.create_widgets()
        print(f"   Widget created: {hasattr(self, 'form')}")

        print("4. Populating UI")
        self.populate_ui_values()
```

#### Measurement System Debugging
```python
def debug_measurement_conversion(value, system):
    print(f"Input: {value} ({system})")

    if system == "imperial":
        parsed = parse_fractional_inches(value)
        print(f"Parsed inches: {parsed}")

        mm_value = inches_to_mm(parsed)
        print(f"Converted to mm: {mm_value}")

        back_to_inches = mm_to_inches(mm_value)
        print(f"Back to inches: {back_to_inches}")

        formatted = format_fractional_inches(back_to_inches)
        print(f"Formatted: {formatted}")

    return mm_value
```

### Performance Troubleshooting

#### Slow TaskPanel Loading
**Common Causes:**
- Heavy computation during hydration
- Excessive widget creation
- Inefficient layout algorithms

**Solutions:**
- Move heavy computation out of `__init__`
- Use lazy widget creation
- Optimize layout algorithms
- Cache expensive calculations

#### Memory Issues
**Common Causes:**
- Not cleaning up FreeCAD objects
- Circular references in UI
- Large data structures in session

**Solutions:**
- Explicitly clean up FreeCAD groups
- Break circular references
- Use weak references where appropriate
- Implement proper cleanup methods

### Integration Issues

#### FreeCAD Compatibility
**Common Problems:**
- Import errors with relative imports
- Python version incompatibilities
- Qt version mismatches

**Solutions:**
- Use absolute imports only
- Test with Python < 3.10
- Use qt_compat for GUI tests
- Check FreeCAD API compatibility

#### Cross-Platform Issues
**Common Problems:**
- Path separator differences
- Font rendering variations
- File permission issues

**Solutions:**
- Use `pathlib.Path` for paths
- Test on multiple platforms
- Handle permission errors gracefully
- Use platform-appropriate defaults

---
## Validation Tools

### Automated Constraint Checking

#### File-Level Validation
```python
from constraint_validation_tools import check_file_compliance

# Check a single file
result = check_file_compliance("freecad/SquatchCut/gui/taskpanel_main.py")

print(f"Total violations: {result['total_violations']}")
print(f"Critical violations: {result['critical_violations']}")

for violation in result['violations']:
    print(f"- {violation['constraint_id']}: {violation['message']}")
```

#### Project-Level Validation
```python
from constraint_validation_tools import ConstraintChecker

checker = ConstraintChecker()
report = checker.check_project_compliance(".")

print(f"Files analyzed: {report['files_analyzed']}")
print(f"Compliance score: {report['compliance_score']:.1f}%")
print(f"Critical violations: {report['critical_violations']}")

# Show top violations
for violation in report['top_violations'][:5]:
    print(f"- {violation['constraint_id']}: {violation['count']} occurrences")
```

#### Task Specification Validation
```python
from constraint_validation_tools import validate_task_spec

task_spec = {
    "reasoning_level": "HIGH",
    "context": "Implement new TaskPanel",
    "requirements": ["Create UI", "Handle hydration"],
    "file_paths": ["freecad/SquatchCut/gui/taskpanel_new.py"],
    "acceptance_criteria": ["Panel opens", "Hydration works"]
}

result = validate_task_spec(task_spec)

print(f"Valid: {result['is_valid']}")
print(f"Compliance score: {result['constraint_compliance_score']:.1f}%")

for warning in result['warnings']:
    print(f"Warning: {warning}")

for recommendation in result['recommendations']:
    print(f"Recommendation: {recommendation}")
```

### Manual Validation Checklists

#### Pre-Implementation Checklist
**Before starting any task:**

- [ ] **Task Specification Complete**
  - [ ] Reasoning level declared
  - [ ] File paths specified
  - [ ] Constraints identified
  - [ ] Acceptance criteria defined

- [ ] **Constraint Analysis**
  - [ ] All applicable constraints identified
  - [ ] Constraint compliance plan created
  - [ ] Validation methods specified

- [ ] **Testing Plan**
  - [ ] Required test types identified
  - [ ] Test coverage planned
  - [ ] Validation procedures defined

#### Implementation Checklist
**During implementation:**

- [ ] **CRITICAL Constraints**
  - [ ] HYDRATION-001: Hydration before widgets ✓
  - [ ] MEASUREMENT-001: Internal mm storage ✓
  - [ ] EXPORT-001: Use exporter.py ✓
  - [ ] PYTHON-001: Python < 3.10 compatible ✓
  - [ ] UI-001: Settings panel opens ✓

- [ ] **Code Quality**
  - [ ] No relative imports
  - [ ] Proper error handling
  - [ ] Consistent naming conventions
  - [ ] Adequate documentation

- [ ] **Testing Implementation**
  - [ ] Unit tests written
  - [ ] Integration tests added
  - [ ] Property tests for universal properties
  - [ ] GUI tests using qt_compat

#### Post-Implementation Checklist
**Before submitting:**

- [ ] **Validation Complete**
  - [ ] All tests pass
  - [ ] Constraint compliance verified
  - [ ] Manual testing completed
  - [ ] Performance acceptable

- [ ] **Documentation Updated**
  - [ ] Code comments added
  - [ ] API documentation updated
  - [ ] User documentation revised (if needed)

- [ ] **PR Preparation**
  - [ ] Clear description written
  - [ ] Constraint compliance documented
  - [ ] Testing instructions provided
  - [ ] Breaking changes noted

### Testing Validation Tools

#### Property Test Validation
```python
# Run property tests with statistics
pytest test_property_based.py -v --hypothesis-show-statistics

# Check for specific property coverage
pytest -k "property" --hypothesis-show-statistics
```

#### GUI Test Validation
```python
# Run GUI tests with qt_compat
pytest tests/test_gui_*.py -v

# Check for GUI test coverage
pytest --cov=SquatchCut.gui tests/test_gui_*.py
```

#### Constraint Test Validation
```python
# Run constraint-specific tests
pytest tests/test_constraint_*.py -v

# Validate constraint framework itself
pytest test_constraint_framework.py --hypothesis-show-statistics
```

### Continuous Validation

#### Pre-Commit Validation
```bash
# Add to pre-commit hook
python -c "
from constraint_validation_tools import check_file_compliance
import sys
import subprocess

# Get modified Python files
result = subprocess.run(['git', 'diff', '--cached', '--name-only', '--diff-filter=AM'],
                       capture_output=True, text=True)
files = [f for f in result.stdout.strip().split('\n') if f.endswith('.py')]

violations = 0
for file in files:
    if file:
        result = check_file_compliance(file)
        if result.get('critical_violations', 0) > 0:
            print(f'CRITICAL violations in {file}')
            violations += 1

if violations > 0:
    print('Commit blocked due to CRITICAL constraint violations')
    sys.exit(1)
"
```

#### CI/CD Integration
```yaml
# GitHub Actions example
- name: Validate Constraints
  run: |
    python -c "
    from constraint_validation_tools import ConstraintChecker
    checker = ConstraintChecker()
    report = checker.check_project_compliance('.')

    if report['critical_violations'] > 0:
        print(f'CRITICAL violations found: {report[\"critical_violations\"]}')
        exit(1)

    if report['compliance_score'] < 80.0:
        print(f'Compliance score too low: {report[\"compliance_score\"]}%')
        exit(1)
    "
```

---
## Appendices

### Appendix A: Complete Constraint Reference

#### CRITICAL Constraints (Cannot Be Violated)

| ID | Area | Rule | Validation |
|----|------|------|------------|
| HYDRATION-001 | Hydration | `hydrate_from_params()` before widgets | Check TaskPanel init order |
| HYDRATION-002 | Hydration | Defaults only change via Settings save | Verify no default mods outside Settings |
| HYDRATION-003 | Hydration | Never auto-select presets | Check preset starts as "None/Custom" |
| MEASUREMENT-001 | Measurement | Internal storage always mm | Verify all calculations use mm |
| MEASUREMENT-002 | Measurement | Imperial UI uses fractional inches | Check display formatting |
| EXPORT-001 | Export | All exports through exporter.py | Verify no direct export implementations |
| EXPORT-002 | Export | ExportJob is source of truth | Check no FreeCAD geometry access |
| PYTHON-001 | Python | Compatible with Python < 3.10 | Check for modern Python features |
| PYTHON-002 | Python | No relative imports | Scan for relative import statements |
| UI-001 | UI | Settings panel always opens | Test Settings panel under all conditions |

#### IMPORTANT Constraints (Require Approval to Violate)

| ID | Area | Rule | Validation |
|----|------|------|------------|
| REPOSITORY-001 | Repository | Maintain directory structure | Check file placement |
| REPOSITORY-002 | Repository | Respect module responsibilities | Verify code placement |
| UI-002 | UI | Follow TaskPanel init pattern | Check initialization sequence |
| UI-003 | UI | Clear groups before redraw | Check group management |
| MEASUREMENT-003 | Measurement | Full UI reformat on system change | Test measurement switching |
| TESTING-001 | Testing | Logic changes require tests | Check for corresponding tests |
| COMMUNICATION-001 | Communication | Act as Lead Developer/PM | Review interaction patterns |
| COMMUNICATION-002 | Communication | One AI per branch | Check branch usage patterns |

### Appendix B: File Organization Reference

#### Core Module Responsibilities
```
freecad/SquatchCut/core/
├── nesting.py              # Nesting algorithms and optimization
├── units.py                # Unit conversion and formatting
├── session_state.py        # In-memory state management
├── session.py              # FreeCAD document integration
├── settings.py             # Configuration and defaults
├── presets.py              # Preset management
├── csv_import.py           # CSV validation and import
├── csv_loader.py           # Low-level CSV parsing
├── exporter.py             # Canonical export architecture
├── cutlist.py              # Cutlist generation
├── report_generator.py     # Report generation
├── geometry_output.py      # FreeCAD geometry creation
├── geometry_sync.py        # Document synchronization
├── view_controller.py      # View management helpers
├── sheet_model.py          # Sheet object management
├── overlap_check.py        # Overlap detection utilities
├── cut_optimization.py     # Cut sequence optimization
├── multi_sheet_optimizer.py # Multi-sheet algorithms
├── nesting_engine.py       # Core nesting engine
├── shape_extractor.py      # FreeCAD shape processing
├── logger.py               # Centralized logging
└── gui_tests.py            # GUI smoke tests
```

#### GUI Module Responsibilities
```
freecad/SquatchCut/gui/
├── taskpanel_main.py       # Main TaskPanel controller
├── taskpanel_settings.py   # Settings TaskPanel
├── taskpanel_nesting.py    # Nesting controls
├── taskpanel_sheet.py      # Sheet configuration
├── taskpanel_input.py      # Input controls
├── source_view.py          # Source parts visualization
├── nesting_view.py         # Nesting results visualization
├── view_helpers.py         # View utility functions
├── view_utils.py           # Additional view utilities
├── qt_compat.py            # Qt compatibility layer
├── icons.py                # Icon management
├── commands/               # FreeCAD command implementations
│   ├── cmd_run_nesting.py
│   ├── cmd_export_report.py
│   ├── cmd_import_csv.py
│   ├── cmd_set_sheet_size.py
│   ├── cmd_preferences.py
│   ├── cmd_run_gui_tests.py
│   └── cmd_add_shapes.py
└── dialogs/                # Dialog implementations
    ├── csv_import_dialog.py
    ├── export_report_dialog.py
    ├── run_nesting_dialog.py
    ├── select_shapes_dialog.py
    └── sheet_size_dialog.py
```

### Appendix C: Testing Framework Reference

#### Test Categories and Locations
```
tests/
├── test_nesting.py                    # Core nesting algorithm tests
├── test_units.py                      # Unit conversion tests
├── test_session_state.py              # State management tests
├── test_taskpanel_hydration.py        # Hydration order tests
├── test_measurement_system.py         # Measurement system tests
├── test_export_architecture.py        # Export compliance tests
├── test_constraint_framework.py       # Constraint validation tests
├── test_task_specification.py         # Task spec validation tests
├── test_property_based.py             # Property-based tests
├── test_property_based_advanced.py    # Advanced property tests
├── test_gui_*.py                      # GUI component tests
└── integration/                       # Integration tests
    ├── test_csv_to_nesting.py
    ├── test_export_workflows.py
    └── test_ui_workflows.py
```

#### Property Test Categories
- **Roundtrip Properties**: `f(g(x)) == x`
- **Invariant Properties**: Properties that never change
- **Metamorphic Properties**: Relationships between inputs
- **Model-Based Properties**: Compare against reference implementation

### Appendix D: Common Error Messages and Solutions

#### "ModuleNotFoundError: No module named 'SquatchCut'"
**Cause:** Incorrect import path or PYTHONPATH
**Solution:** Use absolute imports and set PYTHONPATH correctly
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/freecad
```

#### "AttributeError: 'NoneType' object has no attribute 'get_sheet_width'"
**Cause:** Hydration not called or session_state not initialized
**Solution:** Ensure `hydrate_from_params()` is called first in TaskPanel init

#### "SyntaxError: invalid syntax" (Python compatibility)
**Cause:** Using Python 3.10+ features
**Solution:** Replace with compatible alternatives:
- `type | None` → `Optional[type]`
- `match` statements → `if/elif` chains

#### "RuntimeError: wrapped C/C++ object has been deleted"
**Cause:** Qt object lifecycle issues
**Solution:** Use proper object cleanup and avoid circular references

### Appendix E: Quick Reference Cards

#### Constraint Quick Check
```python
# Before any change, ask:
1. Does this affect hydration? → Check HYDRATION-* constraints
2. Does this handle measurements? → Check MEASUREMENT-* constraints
3. Does this export data? → Check EXPORT-* constraints
4. Does this use modern Python? → Check PYTHON-* constraints
5. Does this modify UI? → Check UI-* constraints
```

#### Testing Quick Check
```python
# For any logic change, ensure:
1. Unit tests for modified functions
2. Integration tests for multi-component changes
3. Property tests for universal properties
4. GUI tests for UI changes (using qt_compat)
5. Constraint compliance tests
```

#### Escalation Quick Check
```python
# Escalate immediately if:
1. CRITICAL constraint cannot be satisfied
2. Requirements conflict with constraints
3. Technical limitations prevent compliance
4. Architectural changes are needed
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | December 2025 | Initial comprehensive handbook |

---

## Feedback and Updates

This handbook is a living document. If you encounter:
- Missing information
- Unclear instructions
- Outdated examples
- New constraint requirements

Please document the issue and escalate for handbook updates.

**Remember:** This handbook exists to make you more effective while preventing architectural drift. When in doubt, follow the constraints and escalate for clarification.

---

*End of SquatchCut AI Agent Handbook v1.0*
