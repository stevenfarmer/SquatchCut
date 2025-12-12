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
4. [Communication & Collaboration Protocols](#communication--collaboration-protocols)
5. [Code Examples and Patterns](#code-examples-and-patterns)
6. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
7. [Testing Requirements](#testing-requirements)
8. [Error Handling and Escalation](#error-handling-and-escalation)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Validation Tools](#validation-tools)
11. [Appendices](#appendices)

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

### Interaction & Collaboration Quick Checks

- Lead Developer & Product Manager framing; explain in plain English before technical details.
- Discovery sequence for vague asks: Pause -> Ask 3-4 clarifying questions -> Validate -> Propose.
- Branch naming: `ai/<worker-name>/<feature>`; one AI per branch with Architect-mediated merges.
- Never force-push over another worker; escalate on conflicts and capture impacted files.
- Commit and PRs use the stakeholder template and list tests plus constraints touched.

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

## Communication & Collaboration Protocols

### Stakeholder Communication (Requirements 5.1–5.5)
- Lead with the **Lead Developer & Product Manager** role; assume the user is a non-technical stakeholder.
- Run the discovery sequence for vague asks: pause, ask 3-4 clarifying questions, then restate the goal.
- Confirm scope, constraints, acceptance criteria, and tests before editing files.
- Escalate immediately when requirements conflict, are incomplete, or risk violating CRITICAL constraints.
- Provide short, stakeholder-ready updates that list progress, risks, and constraint implications.

#### Discovery Script
1. Pause and avoid coding until the ask is clear.
2. Ask 3-4 clarifying questions that narrow scope and surface constraints.
3. Restate the user's goal in plain English; list the constraints you will respect.
4. Outline the plan and tests you will run; ask for confirmation.
5. Proceed only after confirmation or explicit acceptance of the plan.

#### Stakeholder Communication Example
> Plain-English summary of the goal, the plan in one or two bullets, the constraints you will honor, and the tests you will run. Close with a yes/no confirmation request before executing.

### Collaboration Workflow (Requirements 10.1–10.5)
- One AI per branch with naming `ai/<worker-name>/<feature>`; do not reuse another worker's branch.
- Architect/human reviewer mediates handoffs and merges; align before merging across workers.
- Commit messages summarize scope and constraints touched; PRs must use the stakeholder template and list tests run.
- On merge conflicts or overlapping edits: stop, capture the conflicting files/branches, notify the Architect/human reviewer, and never force-push over another worker.
- Keep changes small and in-scope; record the plan and test outcomes in the PR for auditability.

#### Merge Conflict Protocol
1. Stop work when a conflict or overlap is detected.
2. Note the branches/files involved and the decisions at risk.
3. Escalate to the Architect/human reviewer with a short summary and preferred resolution; wait for guidance.

---
## Code Examples and Patterns

### Hydration Patterns

#### Complete TaskPanel Initialization Pattern
```python
class TaskPanel_Example:
    """Complete example of correct TaskPanel initialization"""

    def __init__(self):
        # 1. Initialize basic attributes ONLY
        self.form = None
        self.session = None
        self.settings = None

        # Initialize UI references to None
        self.width_input = None
        self.height_input = None
        self.kerf_input = None
        self.preset_combo = None

        # 2. CRITICAL: Hydrate before anything else
        self.hydrate_from_params()

        # 3. Create UI after hydration
        self.create_widgets()

        # 4. Populate with hydrated values
        self.populate_ui_values()

        # 5. Apply measurement formatting
        self.apply_measurement_formatting()

        # 6. Connect signals last
        self.connect_signals()

        # 7. Final UI setup
        self.finalize_ui()

    def hydrate_from_params(self):
        """Load persistent values - ABSOLUTELY NO GUI ACCESS"""
        # Load session state
        self.session = get_session_state()

        # Load settings
        self.settings = SquatchCutPreferences()

        # Hydrate all persistent values
        self.sheet_width = self.session.get_sheet_width()
        self.sheet_height = self.session.get_sheet_height()
        self.kerf_width = self.session.get_kerf_width()
        self.measurement_system = self.session.get_measurement_system()

        # Load defaults (not current values)
        self.default_width = self.settings.get_default_sheet_width()
        self.default_height = self.settings.get_default_sheet_height()

        # CRITICAL: Never access self.form, self.width_input, or any GUI elements
        # CRITICAL: Never call setText(), setCurrentText(), or any GUI methods
        # CRITICAL: Never create widgets here

    def create_widgets(self):
        """Create UI widgets after hydration - ONLY widget creation"""
        self.form = QtWidgets.QWidget()

        # Create layout
        layout = QtWidgets.QVBoxLayout(self.form)

        # Create input widgets
        self.width_input = QtWidgets.QLineEdit()
        self.height_input = QtWidgets.QLineEdit()
        self.kerf_input = QtWidgets.QLineEdit()

        # Create combo boxes
        self.preset_combo = QtWidgets.QComboBox()
        self.measurement_combo = QtWidgets.QComboBox()

        # Create labels
        self.width_label = QtWidgets.QLabel("Width:")
        self.height_label = QtWidgets.QLabel("Height:")

        # Add to layout
        layout.addWidget(self.width_label)
        layout.addWidget(self.width_input)
        layout.addWidget(self.height_label)
        layout.addWidget(self.height_input)

        # CRITICAL: Do NOT populate values here
        # CRITICAL: Do NOT connect signals here

    def populate_ui_values(self):
        """Populate widgets with hydrated values"""
        # Populate preset combo (always start with None)
        self.preset_combo.addItems(["None / Custom", "4' x 8'", "4' x 4'", "2' x 4'"])
        self.preset_combo.setCurrentText("None / Custom")  # ALWAYS None

        # Populate measurement system
        self.measurement_combo.addItems(["metric", "imperial"])
        self.measurement_combo.setCurrentText(self.measurement_system)

        # Populate input fields with current values (not defaults)
        self.width_input.setText(str(self.sheet_width))
        self.height_input.setText(str(self.sheet_height))
        self.kerf_input.setText(str(self.kerf_width))

    def apply_measurement_formatting(self):
        """Apply measurement system formatting to all numeric fields"""
        if self.measurement_system == "imperial":
            # Convert mm to fractional inches for display
            width_inches = mm_to_inches(self.sheet_width)
            height_inches = mm_to_inches(self.sheet_height)
            kerf_inches = mm_to_inches(self.kerf_width)

            self.width_input.setText(format_fractional_inches(width_inches))
            self.height_input.setText(format_fractional_inches(height_inches))
            self.kerf_input.setText(format_fractional_inches(kerf_inches))

            # Update labels
            self.width_label.setText("Width (inches):")
            self.height_label.setText("Height (inches):")
        else:
            # Already in mm, just format
            self.width_input.setText(f"{self.sheet_width:.1f}")
            self.height_input.setText(f"{self.sheet_height:.1f}")
            self.kerf_input.setText(f"{self.kerf_width:.2f}")

            # Update labels
            self.width_label.setText("Width (mm):")
            self.height_label.setText("Height (mm):")

    def connect_signals(self):
        """Connect all signals after widgets are populated"""
        self.width_input.textChanged.connect(self.on_width_changed)
        self.height_input.textChanged.connect(self.on_height_changed)
        self.preset_combo.currentTextChanged.connect(self.on_preset_selected)
        self.measurement_combo.currentTextChanged.connect(self.on_measurement_system_changed)

    def finalize_ui(self):
        """Final UI setup and validation"""
        # Validate all inputs
        self.validate_inputs()

        # Set focus to first input
        self.width_input.setFocus()

        # Apply any final styling
        self.apply_ui_styling()
```

#### Advanced Hydration Patterns

##### Multi-Source Hydration
```python
def hydrate_from_params(self):
    """Hydrate from multiple sources with fallback hierarchy"""
    # 1. Load session state (current values)
    self.session = get_session_state()

    # 2. Load user preferences (defaults)
    self.settings = SquatchCutPreferences()

    # 3. Load project-specific settings if available
    self.project_settings = load_project_settings()  # May return None

    # 4. Hydrate with fallback hierarchy: session -> project -> user -> system
    self.sheet_width = (
        self.session.get_sheet_width() or
        (self.project_settings.get_sheet_width() if self.project_settings else None) or
        self.settings.get_default_sheet_width() or
        1220.0  # System default
    )

    self.sheet_height = (
        self.session.get_sheet_height() or
        (self.project_settings.get_sheet_height() if self.project_settings else None) or
        self.settings.get_default_sheet_height() or
        2440.0  # System default
    )

    # 5. Validate hydrated values
    self.validate_hydrated_values()

def validate_hydrated_values(self):
    """Validate hydrated values and apply constraints"""
    # Ensure positive dimensions
    if self.sheet_width <= 0:
        self.sheet_width = 1220.0  # Fallback to system default

    if self.sheet_height <= 0:
        self.sheet_height = 2440.0  # Fallback to system default

    # Ensure reasonable limits
    self.sheet_width = max(100.0, min(10000.0, self.sheet_width))
    self.sheet_height = max(100.0, min(10000.0, self.sheet_height))
```

##### Conditional Hydration
```python
def hydrate_from_params(self):
    """Hydrate with conditional logic based on context"""
    self.session = get_session_state()
    self.settings = SquatchCutPreferences()

    # Check if we're in a specific context
    if self.is_new_project():
        # New project: use defaults
        self.sheet_width = self.settings.get_default_sheet_width()
        self.sheet_height = self.settings.get_default_sheet_height()
        self.kerf_width = self.settings.get_default_kerf_width()
    elif self.is_importing_csv():
        # CSV import: try to detect from CSV, fallback to session
        csv_dimensions = self.detect_csv_dimensions()
        if csv_dimensions:
            self.sheet_width = csv_dimensions.width
            self.sheet_height = csv_dimensions.height
        else:
            self.sheet_width = self.session.get_sheet_width()
            self.sheet_height = self.session.get_sheet_height()
    else:
        # Normal operation: use session values
        self.sheet_width = self.session.get_sheet_width()
        self.sheet_height = self.session.get_sheet_height()
        self.kerf_width = self.session.get_kerf_width()

    # Always load measurement system from session
    self.measurement_system = self.session.get_measurement_system()
```

#### Preset Handling Patterns

##### Complete Preset Management
```python
def initialize_presets(self):
    """Initialize preset system - called during widget creation"""
    # Define available presets
    self.presets = {
        "None / Custom": None,  # Special case - no preset
        "4' x 8'": {"width": inches_to_mm(48), "height": inches_to_mm(96)},
        "4' x 4'": {"width": inches_to_mm(48), "height": inches_to_mm(48)},
        "2' x 4'": {"width": inches_to_mm(24), "height": inches_to_mm(48)},
        "1220 x 2440": {"width": 1220.0, "height": 2440.0},
        "1220 x 1220": {"width": 1220.0, "height": 1220.0},
    }

    # Populate combo box
    self.preset_combo.addItems(list(self.presets.keys()))

    # CRITICAL: Always start with None / Custom
    self.preset_combo.setCurrentText("None / Custom")

def on_preset_selected(self, preset_name):
    """Handle preset selection without modifying defaults"""
    if preset_name == "None / Custom":
        # Don't change anything - user is in custom mode
        return

    preset_data = self.presets.get(preset_name)
    if not preset_data:
        return

    # Update UI fields (not internal storage yet)
    if self.measurement_system == "imperial":
        width_inches = mm_to_inches(preset_data["width"])
        height_inches = mm_to_inches(preset_data["height"])
        self.width_input.setText(format_fractional_inches(width_inches))
        self.height_input.setText(format_fractional_inches(height_inches))
    else:
        self.width_input.setText(f"{preset_data['width']:.1f}")
        self.height_input.setText(f"{preset_data['height']:.1f}")

    # CRITICAL: Never modify defaults
    # NEVER: self.settings.set_default_width(preset_data["width"])
    # NEVER: self.session.set_sheet_width(preset_data["width"])

def on_manual_input_changed(self):
    """Handle manual input changes - switch to custom mode"""
    # When user manually changes values, switch to custom
    if self.preset_combo.currentText() != "None / Custom":
        # Temporarily disconnect to avoid recursion
        self.preset_combo.currentTextChanged.disconnect()
        self.preset_combo.setCurrentText("None / Custom")
        self.preset_combo.currentTextChanged.connect(self.on_preset_selected)

def detect_current_preset(self):
    """Detect if current values match a preset (for display only)"""
    current_width = self.sheet_width
    current_height = self.sheet_height

    for preset_name, preset_data in self.presets.items():
        if preset_data is None:  # Skip "None / Custom"
            continue

        if (abs(current_width - preset_data["width"]) < 0.1 and
            abs(current_height - preset_data["height"]) < 0.1):
            return preset_name

    return "None / Custom"
```

### Measurement System Patterns

#### Complete Unit Conversion System
```python
def handle_user_input(self, user_value, measurement_system):
    """Always convert to mm for internal storage with comprehensive validation"""
    try:
        if measurement_system == "imperial":
            # Parse fractional inches with validation
            inches_value = parse_fractional_inches(user_value)

            # Validate reasonable range (0.1" to 1000")
            if not (0.1 <= inches_value <= 1000.0):
                raise ValueError(f"Imperial value {inches_value} out of range")

            # Convert to mm for internal storage
            mm_value = inches_to_mm(inches_value)
        else:
            # Parse metric with validation
            mm_value = float(user_value)

            # Validate reasonable range (1mm to 25000mm)
            if not (1.0 <= mm_value <= 25000.0):
                raise ValueError(f"Metric value {mm_value} out of range")

        # Store internally in mm (ALWAYS)
        self.internal_width = mm_value

        # Update session state
        self.session.set_sheet_width(mm_value)

        return mm_value

    except ValueError as e:
        # Handle parsing errors gracefully
        self.show_input_error(f"Invalid input: {e}")
        return None

def format_for_display(self, mm_value, measurement_system):
    """Format for UI display with proper precision"""
    if measurement_system == "imperial":
        inches_value = mm_to_inches(mm_value)
        return format_fractional_inches(inches_value)
    else:
        # Use appropriate precision for metric
        if mm_value >= 1000:
            return f"{mm_value:.0f} mm"  # No decimals for large values
        elif mm_value >= 10:
            return f"{mm_value:.1f} mm"  # One decimal for medium values
        else:
            return f"{mm_value:.2f} mm"  # Two decimals for small values

def parse_fractional_inches(self, input_str):
    """Parse fractional inches with comprehensive format support"""
    input_str = input_str.strip()

    # Handle empty input
    if not input_str:
        raise ValueError("Empty input")

    # Handle whole numbers: "48", "12"
    if input_str.isdigit():
        return float(input_str)

    # Handle decimal inches: "48.5", "12.25" (convert to fractional)
    try:
        decimal_value = float(input_str)
        return decimal_value
    except ValueError:
        pass

    # Handle fractions: "3/4", "1/2", "7/8"
    if '/' in input_str and ' ' not in input_str:
        parts = input_str.split('/')
        if len(parts) == 2:
            numerator = float(parts[0])
            denominator = float(parts[1])
            if denominator != 0:
                return numerator / denominator

    # Handle mixed fractions: "48 3/4", "12 1/2"
    if ' ' in input_str:
        parts = input_str.split(' ')
        if len(parts) == 2:
            whole_part = float(parts[0])
            fraction_part = parts[1]

            if '/' in fraction_part:
                frac_parts = fraction_part.split('/')
                if len(frac_parts) == 2:
                    numerator = float(frac_parts[0])
                    denominator = float(frac_parts[1])
                    if denominator != 0:
                        return whole_part + (numerator / denominator)

    raise ValueError(f"Cannot parse fractional inches: {input_str}")

def format_fractional_inches(self, inches_value):
    """Format decimal inches as fractional inches"""
    # Handle negative values
    if inches_value < 0:
        return f"-{self.format_fractional_inches(-inches_value)}"

    # Extract whole and fractional parts
    whole_part = int(inches_value)
    fractional_part = inches_value - whole_part

    # If no fractional part, return whole number
    if fractional_part < 0.001:  # Account for floating point precision
        return str(whole_part)

    # Convert to common fractions (1/16 precision)
    sixteenths = round(fractional_part * 16)

    # Simplify fraction
    if sixteenths == 0:
        return str(whole_part)
    elif sixteenths == 16:
        return str(whole_part + 1)
    else:
        # Simplify the fraction
        numerator = sixteenths
        denominator = 16

        # Find GCD to simplify
        while denominator != 0:
            numerator, denominator = denominator, numerator % denominator
        gcd = numerator

        simplified_num = sixteenths // gcd
        simplified_den = 16 // gcd

        if whole_part == 0:
            return f"{simplified_num}/{simplified_den}"
        else:
            return f"{whole_part} {simplified_num}/{simplified_den}"
```

#### Advanced Measurement System Switching
```python
def on_measurement_system_changed(self, new_system):
    """Comprehensive measurement system switching with validation"""
    old_system = self.measurement_system

    # Validate the change is actually needed
    if old_system == new_system:
        return

    # Store the new system
    self.measurement_system = new_system

    # Get all current values in mm (internal storage)
    width_mm = self.sheet_width  # Always stored in mm
    height_mm = self.sheet_height  # Always stored in mm
    kerf_mm = self.kerf_width  # Always stored in mm

    # Temporarily disconnect signals to avoid recursion
    self.disconnect_input_signals()

    try:
        # Reformat all numeric input fields
        self.width_input.setText(self.format_for_display(width_mm, new_system))
        self.height_input.setText(self.format_for_display(height_mm, new_system))
        self.kerf_input.setText(self.format_for_display(kerf_mm, new_system))

        # Update all unit labels
        self.update_unit_labels(new_system)

        # Update input field placeholders
        self.update_input_placeholders(new_system)

        # Update validation patterns
        self.update_input_validators(new_system)

        # Save the preference
        self.session.set_measurement_system(new_system)

    finally:
        # Reconnect signals
        self.connect_input_signals()

def update_unit_labels(self, measurement_system):
    """Update all labels to show correct units"""
    if measurement_system == "imperial":
        self.width_label.setText("Width (inches):")
        self.height_label.setText("Height (inches):")
        self.kerf_label.setText("Kerf (inches):")
    else:
        self.width_label.setText("Width (mm):")
        self.height_label.setText("Height (mm):")
        self.kerf_label.setText("Kerf (mm):")

def update_input_placeholders(self, measurement_system):
    """Update input field placeholders with examples"""
    if measurement_system == "imperial":
        self.width_input.setPlaceholderText("e.g., 48 or 48 3/4")
        self.height_input.setPlaceholderText("e.g., 96 or 96 1/2")
        self.kerf_input.setPlaceholderText("e.g., 1/8 or 0.125")
    else:
        self.width_input.setPlaceholderText("e.g., 1220.0")
        self.height_input.setPlaceholderText("e.g., 2440.0")
        self.kerf_input.setPlaceholderText("e.g., 3.2")

def update_input_validators(self, measurement_system):
    """Update input field validators for the measurement system"""
    if measurement_system == "imperial":
        # Allow fractional input: digits, spaces, and forward slashes
        imperial_regex = QtCore.QRegExp(r"[0-9 /\.]+")
        imperial_validator = QtGui.QRegExpValidator(imperial_regex)

        self.width_input.setValidator(imperial_validator)
        self.height_input.setValidator(imperial_validator)
        self.kerf_input.setValidator(imperial_validator)
    else:
        # Allow decimal numbers
        metric_validator = QtGui.QDoubleValidator(0.1, 25000.0, 2)
        metric_validator.setNotation(QtGui.QDoubleValidator.StandardNotation)

        self.width_input.setValidator(metric_validator)
        self.height_input.setValidator(metric_validator)
        self.kerf_input.setValidator(metric_validator)
```

#### Measurement Conversion Utilities
```python
def inches_to_mm(self, inches):
    """Convert inches to millimeters with high precision"""
    return inches * 25.4

def mm_to_inches(self, mm):
    """Convert millimeters to inches with high precision"""
    return mm / 25.4

def validate_measurement_input(self, input_text, measurement_system):
    """Validate user input before conversion"""
    if not input_text or input_text.isspace():
        return False, "Input cannot be empty"

    try:
        if measurement_system == "imperial":
            value = self.parse_fractional_inches(input_text)
            if value <= 0:
                return False, "Value must be positive"
            if value > 1000:  # 1000 inches = ~25 meters
                return False, "Value too large (max 1000 inches)"
        else:
            value = float(input_text)
            if value <= 0:
                return False, "Value must be positive"
            if value > 25000:  # 25 meters
                return False, "Value too large (max 25000 mm)"

        return True, None

    except ValueError as e:
        return False, f"Invalid format: {e}"

def get_measurement_precision(self, measurement_system):
    """Get appropriate precision for calculations"""
    if measurement_system == "imperial":
        return 1/16  # 1/16 inch precision
    else:
        return 0.1   # 0.1 mm precision

def round_to_precision(self, value, measurement_system):
    """Round value to appropriate precision for the measurement system"""
    precision = self.get_measurement_precision(measurement_system)
    return round(value / precision) * precision
```

### UI Component Patterns

#### Complete TaskPanel Implementation
```python
class TaskPanel_Complete:
    """Complete example of proper TaskPanel implementation"""

    def __init__(self):
        # 1. Initialize attributes
        self.form = None
        self.session = None
        self.settings = None

        # 2. Hydrate first
        self.hydrate_from_params()

        # 3. Create UI
        self.create_widgets()

        # 4. Populate and connect
        self.populate_ui_values()
        self.connect_signals()

        # 5. Final setup
        self.finalize_ui()

    def create_widgets(self):
        """Create responsive UI that works in narrow docks"""
        self.form = QtWidgets.QWidget()

        # Use QVBoxLayout for narrow dock compatibility
        main_layout = QtWidgets.QVBoxLayout(self.form)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        # Create sections with proper spacing
        self.create_dimensions_section(main_layout)
        self.create_options_section(main_layout)
        self.create_actions_section(main_layout)

        # Add stretch to push content to top
        main_layout.addStretch()

    def create_dimensions_section(self, parent_layout):
        """Create dimensions input section"""
        # Section header
        header = QtWidgets.QLabel("Sheet Dimensions")
        header.setStyleSheet("font-weight: bold; margin-top: 8px;")
        parent_layout.addWidget(header)

        # Dimensions grid
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.setSpacing(4)

        # Width input
        self.width_label = QtWidgets.QLabel("Width:")
        self.width_input = QtWidgets.QLineEdit()
        self.width_input.setMinimumWidth(80)
        grid_layout.addWidget(self.width_label, 0, 0)
        grid_layout.addWidget(self.width_input, 0, 1)

        # Height input
        self.height_label = QtWidgets.QLabel("Height:")
        self.height_input = QtWidgets.QLineEdit()
        self.height_input.setMinimumWidth(80)
        grid_layout.addWidget(self.height_label, 1, 0)
        grid_layout.addWidget(self.height_input, 1, 1)

        # Kerf input
        self.kerf_label = QtWidgets.QLabel("Kerf:")
        self.kerf_input = QtWidgets.QLineEdit()
        self.kerf_input.setMinimumWidth(80)
        grid_layout.addWidget(self.kerf_label, 2, 0)
        grid_layout.addWidget(self.kerf_input, 2, 1)

        parent_layout.addLayout(grid_layout)

    def create_options_section(self, parent_layout):
        """Create options section"""
        # Section header
        header = QtWidgets.QLabel("Options")
        header.setStyleSheet("font-weight: bold; margin-top: 8px;")
        parent_layout.addWidget(header)

        # Measurement system
        measurement_layout = QtWidgets.QHBoxLayout()
        measurement_layout.addWidget(QtWidgets.QLabel("Units:"))
        self.measurement_combo = QtWidgets.QComboBox()
        self.measurement_combo.addItems(["metric", "imperial"])
        measurement_layout.addWidget(self.measurement_combo)
        measurement_layout.addStretch()
        parent_layout.addLayout(measurement_layout)

        # Presets
        preset_layout = QtWidgets.QHBoxLayout()
        preset_layout.addWidget(QtWidgets.QLabel("Preset:"))
        self.preset_combo = QtWidgets.QComboBox()
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        parent_layout.addLayout(preset_layout)

    def create_actions_section(self, parent_layout):
        """Create action buttons section"""
        # Section header
        header = QtWidgets.QLabel("Actions")
        header.setStyleSheet("font-weight: bold; margin-top: 8px;")
        parent_layout.addWidget(header)

        # Button layout
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing(4)

        # Primary actions
        self.apply_button = QtWidgets.QPushButton("Apply Settings")
        self.apply_button.setMinimumHeight(28)
        button_layout.addWidget(self.apply_button)

        self.reset_button = QtWidgets.QPushButton("Reset to Defaults")
        button_layout.addWidget(self.reset_button)

        parent_layout.addLayout(button_layout)

    def connect_signals(self):
        """Connect all signals after UI is fully created"""
        # Input field signals
        self.width_input.textChanged.connect(self.on_width_changed)
        self.height_input.textChanged.connect(self.on_height_changed)
        self.kerf_input.textChanged.connect(self.on_kerf_changed)

        # Combo box signals
        self.measurement_combo.currentTextChanged.connect(self.on_measurement_system_changed)
        self.preset_combo.currentTextChanged.connect(self.on_preset_selected)

        # Button signals
        self.apply_button.clicked.connect(self.on_apply_clicked)
        self.reset_button.clicked.connect(self.on_reset_clicked)

    def finalize_ui(self):
        """Final UI setup and validation"""
        # Set tab order
        self.form.setTabOrder(self.width_input, self.height_input)
        self.form.setTabOrder(self.height_input, self.kerf_input)
        self.form.setTabOrder(self.kerf_input, self.measurement_combo)

        # Set focus to first input
        self.width_input.setFocus()

        # Validate initial state
        self.validate_all_inputs()
```

#### Responsive Layout Patterns
```python
def create_responsive_layout(self):
    """Create layout that adapts to narrow docks"""
    # Use QVBoxLayout as primary layout (stacks vertically)
    main_layout = QtWidgets.QVBoxLayout(self.form)

    # Set margins appropriate for dock panels
    main_layout.setContentsMargins(6, 6, 6, 6)
    main_layout.setSpacing(4)

    # For input pairs, use QGridLayout with proper column stretching
    input_grid = QtWidgets.QGridLayout()
    input_grid.setColumnStretch(1, 1)  # Make input column stretch

    # Labels in column 0, inputs in column 1
    input_grid.addWidget(QtWidgets.QLabel("Width:"), 0, 0)
    input_grid.addWidget(self.width_input, 0, 1)

    # Avoid QHBoxLayout for label-input pairs in narrow spaces
    # WRONG: label_input_layout = QtWidgets.QHBoxLayout()
    # RIGHT: Use QGridLayout as shown above

def handle_narrow_dock(self):
    """Adapt UI for narrow dock panels"""
    # Use minimum widths instead of fixed widths
    self.width_input.setMinimumWidth(60)  # Not setFixedWidth(200)

    # Use elided text for long labels
    self.long_label.setText(self.elide_text("Very Long Label Text", 100))

    # Stack buttons vertically in narrow spaces
    if self.form.width() < 200:
        self.button_layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
    else:
        self.button_layout.setDirection(QtWidgets.QBoxLayout.LeftToRight)

def elide_text(self, text, max_width):
    """Elide text to fit in available space"""
    font_metrics = QtGui.QFontMetrics(self.form.font())
    return font_metrics.elidedText(text, QtCore.Qt.ElideRight, max_width)
```

#### Signal Connection Patterns
```python
def connect_signals(self):
    """Proper signal connection with error handling"""
    try:
        # Connect input signals
        self.width_input.textChanged.connect(self.on_width_changed)
        self.height_input.textChanged.connect(self.on_height_changed)

        # Connect with lambda for parameterized slots
        self.preset_combo.currentTextChanged.connect(
            lambda preset: self.on_preset_selected(preset)
        )

        # Connect button signals
        self.apply_button.clicked.connect(self.on_apply_clicked)

    except Exception as e:
        print(f"Error connecting signals: {e}")
        # Don't let signal connection errors crash the panel

def disconnect_signals(self):
    """Safely disconnect all signals"""
    try:
        # Disconnect input signals
        self.width_input.textChanged.disconnect()
        self.height_input.textChanged.disconnect()

        # Disconnect combo signals
        self.preset_combo.currentTextChanged.disconnect()

        # Disconnect button signals
        self.apply_button.clicked.disconnect()

    except Exception:
        # Ignore errors during disconnection
        pass

def temporarily_disconnect_signals(self):
    """Context manager for temporary signal disconnection"""
    class SignalBlocker:
        def __init__(self, panel):
            self.panel = panel

        def __enter__(self):
            self.panel.disconnect_signals()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.panel.connect_signals()

    return SignalBlocker(self)

# Usage:
def update_ui_without_signals(self):
    with self.temporarily_disconnect_signals():
        self.width_input.setText("1220")
        self.height_input.setText("2440")
        # No signals fired during this block
```

#### Input Validation Patterns
```python
def setup_input_validation(self):
    """Set up comprehensive input validation"""
    # Set up validators based on measurement system
    self.update_input_validators(self.measurement_system)

    # Connect validation signals
    self.width_input.textChanged.connect(self.validate_width_input)
    self.height_input.textChanged.connect(self.validate_height_input)

    # Set up visual feedback
    self.setup_validation_styling()

def validate_width_input(self, text):
    """Validate width input with visual feedback"""
    is_valid, error_message = self.validate_measurement_input(text, self.measurement_system)

    if is_valid:
        self.clear_input_error(self.width_input)
        self.enable_apply_button()
    else:
        self.show_input_error(self.width_input, error_message)
        self.disable_apply_button()

def show_input_error(self, input_widget, message):
    """Show input error with visual feedback"""
    # Apply error styling
    input_widget.setStyleSheet("QLineEdit { border: 2px solid red; }")

    # Show tooltip with error message
    input_widget.setToolTip(f"Error: {message}")

    # Update status
    self.status_label.setText(f"Error: {message}")
    self.status_label.setStyleSheet("color: red;")

def clear_input_error(self, input_widget):
    """Clear input error styling"""
    input_widget.setStyleSheet("")
    input_widget.setToolTip("")
    self.status_label.setText("Ready")
    self.status_label.setStyleSheet("color: green;")

def setup_validation_styling(self):
    """Set up CSS styles for validation feedback"""
    self.error_style = """
        QLineEdit {
            border: 2px solid #ff6b6b;
            background-color: #ffe0e0;
        }
    """

    self.success_style = """
        QLineEdit {
            border: 2px solid #51cf66;
            background-color: #e0ffe0;
        }
    """

    self.normal_style = """
        QLineEdit {
            border: 1px solid #ccc;
            background-color: white;
        }
    """
```

### Preset and Default Separation Patterns

#### Understanding the Distinction
```python
"""
CRITICAL CONCEPT: Presets vs Defaults

DEFAULTS:
- User's personal preferences stored in settings
- Changed only through Settings panel save operations
- Persist across FreeCAD sessions
- Apply when starting new projects

PRESETS:
- Predefined common configurations
- Temporary selections that populate UI fields
- Never modify stored defaults
- Always start with "None / Custom" selected
"""

class PresetDefaultManager:
    """Proper separation of presets and defaults"""

    def __init__(self):
        # Load user's personal defaults (persistent)
        self.settings = SquatchCutPreferences()
        self.default_width = self.settings.get_default_sheet_width()
        self.default_height = self.settings.get_default_sheet_height()

        # Define available presets (static configurations)
        self.presets = {
            "None / Custom": None,  # Special case - no preset active
            "4' x 8' Plywood": {"width": inches_to_mm(48), "height": inches_to_mm(96)},
            "4' x 4' Plywood": {"width": inches_to_mm(48), "height": inches_to_mm(48)},
            "2' x 4' Lumber": {"width": inches_to_mm(24), "height": inches_to_mm(48)},
            "Standard Metric": {"width": 1220.0, "height": 2440.0},
        }

        # Current working values (may differ from defaults)
        self.current_width = self.default_width
        self.current_height = self.default_height

    def load_panel_initial_state(self):
        """Load panel with defaults, never auto-select presets"""
        # ALWAYS start with None / Custom preset
        self.preset_combo.setCurrentText("None / Custom")

        # Populate with user's defaults (not preset values)
        self.width_input.setText(str(self.default_width))
        self.height_input.setText(str(self.default_height))

        # Set current working values to defaults
        self.current_width = self.default_width
        self.current_height = self.default_height

    def on_preset_selected(self, preset_name):
        """Handle preset selection without modifying defaults"""
        if preset_name == "None / Custom":
            # User switched to custom mode - don't change values
            return

        preset_data = self.presets.get(preset_name)
        if not preset_data:
            return

        # Update current working values (NOT defaults)
        self.current_width = preset_data["width"]
        self.current_height = preset_data["height"]

        # Update UI to show preset values
        self.width_input.setText(str(self.current_width))
        self.height_input.setText(str(self.current_height))

        # CRITICAL: Never modify defaults
        # NEVER: self.settings.set_default_sheet_width(preset_data["width"])
        # NEVER: self.default_width = preset_data["width"]

    def on_manual_input_change(self):
        """Handle manual input - switch to custom mode"""
        # When user manually changes values, switch to None / Custom
        if self.preset_combo.currentText() != "None / Custom":
            # Temporarily disconnect to avoid recursion
            self.preset_combo.currentTextChanged.disconnect()
            self.preset_combo.setCurrentText("None / Custom")
            self.preset_combo.currentTextChanged.connect(self.on_preset_selected)

        # Update current working values from UI
        try:
            self.current_width = float(self.width_input.text())
            self.current_height = float(self.height_input.text())
        except ValueError:
            pass  # Invalid input - keep previous values

    def save_as_new_defaults(self):
        """Save current values as new defaults - ONLY through Settings panel"""
        # This should ONLY be called from Settings panel save operation
        self.settings.set_default_sheet_width(self.current_width)
        self.settings.set_default_sheet_height(self.current_height)
        self.settings.save()

        # Update local default values
        self.default_width = self.current_width
        self.default_height = self.current_height

    def reset_to_defaults(self):
        """Reset current values to user's defaults"""
        self.current_width = self.default_width
        self.current_height = self.default_height

        # Update UI
        self.width_input.setText(str(self.current_width))
        self.height_input.setText(str(self.current_height))

        # Switch to None / Custom
        self.preset_combo.setCurrentText("None / Custom")
```

#### Advanced Preset Management
```python
class AdvancedPresetManager:
    """Advanced preset management with validation and feedback"""

    def __init__(self):
        self.setup_presets()
        self.setup_defaults()
        self.current_preset = "None / Custom"

    def setup_presets(self):
        """Define presets with metadata"""
        self.presets = {
            "None / Custom": {
                "data": None,
                "description": "Custom dimensions",
                "category": "custom"
            },
            "4' x 8' Plywood": {
                "data": {"width": inches_to_mm(48), "height": inches_to_mm(96)},
                "description": "Standard plywood sheet",
                "category": "plywood"
            },
            "4' x 4' Plywood": {
                "data": {"width": inches_to_mm(48), "height": inches_to_mm(48)},
                "description": "Square plywood sheet",
                "category": "plywood"
            },
            "2' x 4' Lumber": {
                "data": {"width": inches_to_mm(24), "height": inches_to_mm(48)},
                "description": "Standard lumber dimensions",
                "category": "lumber"
            }
        }

    def populate_preset_combo(self):
        """Populate preset combo with categories"""
        self.preset_combo.clear()

        # Add None / Custom first
        self.preset_combo.addItem("None / Custom")

        # Group by category
        categories = {}
        for name, preset in self.presets.items():
            if name == "None / Custom":
                continue
            category = preset["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(name)

        # Add categorized items
        for category, items in categories.items():
            for item in items:
                self.preset_combo.addItem(f"  {item}")  # Indent for visual grouping

    def detect_matching_preset(self):
        """Detect if current values match a preset (for display only)"""
        current_width = self.current_width
        current_height = self.current_height

        for preset_name, preset_info in self.presets.items():
            if preset_info["data"] is None:
                continue

            preset_data = preset_info["data"]
            if (abs(current_width - preset_data["width"]) < 0.1 and
                abs(current_height - preset_data["height"]) < 0.1):
                return preset_name

        return "None / Custom"

    def validate_preset_compatibility(self, preset_name):
        """Validate if preset is compatible with current settings"""
        preset_info = self.presets.get(preset_name)
        if not preset_info or not preset_info["data"]:
            return True, ""

        preset_data = preset_info["data"]

        # Check if dimensions are reasonable for current kerf
        if self.kerf_width * 2 >= min(preset_data["width"], preset_data["height"]):
            return False, "Kerf too large for preset dimensions"

        # Check if preset fits current part requirements
        if hasattr(self, 'parts') and self.parts:
            max_part_width = max(part.width for part in self.parts)
            max_part_height = max(part.height for part in self.parts)

            if (max_part_width > preset_data["width"] or
                max_part_height > preset_data["height"]):
                return False, "Preset too small for current parts"

        return True, ""

    def apply_preset_with_validation(self, preset_name):
        """Apply preset with validation and user feedback"""
        # Validate compatibility
        is_valid, error_message = self.validate_preset_compatibility(preset_name)

        if not is_valid:
            # Show warning dialog
            reply = QtWidgets.QMessageBox.question(
                self.form,
                "Preset Compatibility Warning",
                f"Warning: {error_message}\n\nApply preset anyway?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.No:
                # Revert preset selection
                self.preset_combo.setCurrentText(self.current_preset)
                return

        # Apply the preset
        self.on_preset_selected(preset_name)
        self.current_preset = preset_name
```

#### Settings Panel Integration
```python
class SettingsPanel:
    """Settings panel that properly manages defaults"""

    def __init__(self):
        self.settings = SquatchCutPreferences()
        self.load_current_defaults()

    def load_current_defaults(self):
        """Load current defaults for editing"""
        self.default_width = self.settings.get_default_sheet_width()
        self.default_height = self.settings.get_default_sheet_height()
        self.default_kerf = self.settings.get_default_kerf_width()

        # Populate UI with current defaults
        self.width_input.setText(str(self.default_width))
        self.height_input.setText(str(self.default_height))
        self.kerf_input.setText(str(self.default_kerf))

    def on_save_defaults(self):
        """Save new defaults - ONLY place defaults can change"""
        try:
            # Validate inputs
            new_width = float(self.width_input.text())
            new_height = float(self.height_input.text())
            new_kerf = float(self.kerf_input.text())

            # Validate ranges
            if not (100 <= new_width <= 10000):
                raise ValueError("Width must be between 100 and 10000 mm")
            if not (100 <= new_height <= 10000):
                raise ValueError("Height must be between 100 and 10000 mm")
            if not (0.1 <= new_kerf <= 50):
                raise ValueError("Kerf must be between 0.1 and 50 mm")

            # Save to settings
            self.settings.set_default_sheet_width(new_width)
            self.settings.set_default_sheet_height(new_height)
            self.settings.set_default_kerf_width(new_kerf)
            self.settings.save()

            # Update local values
            self.default_width = new_width
            self.default_height = new_height
            self.default_kerf = new_kerf

            # Show success message
            QtWidgets.QMessageBox.information(
                self.form,
                "Settings Saved",
                "Default values have been saved successfully."
            )

        except ValueError as e:
            QtWidgets.QMessageBox.warning(
                self.form,
                "Invalid Input",
                str(e)
            )

    def on_reset_to_factory(self):
        """Reset to factory defaults"""
        reply = QtWidgets.QMessageBox.question(
            self.form,
            "Reset to Factory Defaults",
            "This will reset all settings to factory defaults. Continue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            # Reset to factory defaults
            self.settings.reset_to_factory_defaults()
            self.settings.save()

            # Reload UI
            self.load_current_defaults()
```

### Export Architecture Patterns

#### Complete Export Architecture Implementation
```python
def export_cutlist(self, file_path):
    """Complete CSV export using canonical architecture"""
    try:
        # 1. Build ExportJob from current nesting state
        export_job = build_export_job_from_current_nesting()

        # 2. Validate export job
        if not export_job or not export_job.sheets:
            raise ValueError("No nesting data available for export")

        # 3. Use canonical exporter
        from SquatchCut.core.exporter import export_cutlist
        export_cutlist(export_job, file_path)

        # 4. Log successful export
        print(f"Cutlist exported successfully to {file_path}")

    except Exception as e:
        # Handle export errors gracefully
        QtWidgets.QMessageBox.critical(
            None,
            "Export Error",
            f"Failed to export cutlist: {str(e)}"
        )
        raise

def export_svg(self, file_path):
    """Complete SVG export using canonical architecture"""
    try:
        # 1. Build ExportJob from current nesting
        export_job = build_export_job_from_current_nesting()

        # 2. Validate export data
        self.validate_export_job(export_job)

        # 3. Use canonical SVG exporter
        from SquatchCut.core.exporter import export_nesting_to_svg
        export_nesting_to_svg(export_job, file_path)

        # 4. Verify export file was created
        if not os.path.exists(file_path):
            raise RuntimeError("SVG file was not created")

        print(f"SVG exported successfully to {file_path}")

    except Exception as e:
        QtWidgets.QMessageBox.critical(
            None,
            "SVG Export Error",
            f"Failed to export SVG: {str(e)}"
        )
        raise

def validate_export_job(self, export_job):
    """Validate ExportJob data integrity"""
    if not export_job:
        raise ValueError("ExportJob is None")

    if not export_job.sheets:
        raise ValueError("No sheets in ExportJob")

    for i, sheet in enumerate(export_job.sheets):
        if sheet.width_mm <= 0 or sheet.height_mm <= 0:
            raise ValueError(f"Sheet {i} has invalid dimensions")

        if not sheet.parts:
            print(f"Warning: Sheet {i} has no parts")

        for j, part in enumerate(sheet.parts):
            if part.width_mm <= 0 or part.height_mm <= 0:
                raise ValueError(f"Part {j} on sheet {i} has invalid dimensions")

def build_export_job_from_current_nesting(self):
    """Build ExportJob from current nesting state"""
    # Get current session state
    session = get_session_state()

    # Create ExportJob
    export_job = ExportJob(
        measurement_system=session.get_measurement_system(),
        timestamp=datetime.now(),
        source_file=session.get_source_csv_path()
    )

    # Get nesting results
    nesting_results = session.get_nesting_results()
    if not nesting_results:
        raise ValueError("No nesting results available")

    # Convert nesting results to ExportSheets
    for sheet_index, sheet_result in enumerate(nesting_results.sheets):
        export_sheet = ExportSheet(
            sheet_id=f"Sheet_{sheet_index + 1}",
            width_mm=sheet_result.width_mm,
            height_mm=sheet_result.height_mm,
            kerf_mm=sheet_result.kerf_mm
        )

        # Add parts to sheet
        for part_result in sheet_result.placed_parts:
            export_part = ExportPartPlacement(
                part_id=part_result.part_id,
                label=part_result.label,
                width_mm=part_result.width_mm,
                height_mm=part_result.height_mm,
                x_mm=part_result.x_mm,
                y_mm=part_result.y_mm,
                rotation_degrees=part_result.rotation_degrees
            )
            export_sheet.parts.append(export_part)

        export_job.sheets.append(export_sheet)

    return export_job
```

#### Advanced Export Patterns
```python
class ExportManager:
    """Centralized export management"""

    def __init__(self):
        self.supported_formats = ["csv", "svg"]  # DXF deferred
        self.export_history = []

    def export_with_format_detection(self, file_path):
        """Export with automatic format detection"""
        # Detect format from file extension
        _, ext = os.path.splitext(file_path.lower())

        if ext == ".csv":
            return self.export_cutlist(file_path)
        elif ext == ".svg":
            return self.export_svg(file_path)
        elif ext == ".dxf":
            raise NotImplementedError("DXF export is deferred - use CSV or SVG instead")
        else:
            raise ValueError(f"Unsupported export format: {ext}")

    def export_with_progress(self, file_path, format_type):
        """Export with progress dialog"""
        progress = QtWidgets.QProgressDialog(
            f"Exporting {format_type.upper()}...",
            "Cancel",
            0, 100
        )
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.show()

        try:
            # Update progress
            progress.setValue(25)
            QtCore.QCoreApplication.processEvents()

            # Build export job
            export_job = build_export_job_from_current_nesting()

            progress.setValue(50)
            QtCore.QCoreApplication.processEvents()

            # Perform export
            if format_type == "csv":
                from SquatchCut.core.exporter import export_cutlist
                export_cutlist(export_job, file_path)
            elif format_type == "svg":
                from SquatchCut.core.exporter import export_nesting_to_svg
                export_nesting_to_svg(export_job, file_path)

            progress.setValue(100)

            # Record export in history
            self.export_history.append({
                "file_path": file_path,
                "format": format_type,
                "timestamp": datetime.now(),
                "sheet_count": len(export_job.sheets)
            })

        finally:
            progress.close()

    def batch_export(self, base_path, formats):
        """Export multiple formats simultaneously"""
        export_job = build_export_job_from_current_nesting()

        results = {}
        for format_type in formats:
            if format_type not in self.supported_formats:
                results[format_type] = f"Error: Unsupported format {format_type}"
                continue

            try:
                # Generate file path
                file_path = f"{base_path}.{format_type}"

                # Export using canonical architecture
                if format_type == "csv":
                    from SquatchCut.core.exporter import export_cutlist
                    export_cutlist(export_job, file_path)
                elif format_type == "svg":
                    from SquatchCut.core.exporter import export_nesting_to_svg
                    export_nesting_to_svg(export_job, file_path)

                results[format_type] = f"Success: {file_path}"

            except Exception as e:
                results[format_type] = f"Error: {str(e)}"

        return results
```

#### Export Data Model Patterns
```python
class ExportJob:
    """Canonical export data model"""

    def __init__(self, measurement_system, timestamp=None, source_file=None):
        self.measurement_system = measurement_system  # "metric" or "imperial"
        self.timestamp = timestamp or datetime.now()
        self.source_file = source_file
        self.sheets = []  # List of ExportSheet objects

    def get_total_parts(self):
        """Get total number of parts across all sheets"""
        return sum(len(sheet.parts) for sheet in self.sheets)

    def get_total_area_mm2(self):
        """Get total sheet area in mm²"""
        return sum(sheet.width_mm * sheet.height_mm for sheet in self.sheets)

    def get_utilization_percentage(self):
        """Calculate material utilization percentage"""
        total_sheet_area = self.get_total_area_mm2()
        if total_sheet_area == 0:
            return 0.0

        total_part_area = sum(
            part.width_mm * part.height_mm
            for sheet in self.sheets
            for part in sheet.parts
        )

        return (total_part_area / total_sheet_area) * 100

class ExportSheet:
    """Canonical sheet data model"""

    def __init__(self, sheet_id, width_mm, height_mm, kerf_mm=0.0):
        self.sheet_id = sheet_id
        self.width_mm = float(width_mm)  # Always store in mm
        self.height_mm = float(height_mm)  # Always store in mm
        self.kerf_mm = float(kerf_mm)  # Always store in mm
        self.parts = []  # List of ExportPartPlacement objects

    def get_part_count(self):
        """Get number of parts on this sheet"""
        return len(self.parts)

    def get_utilization(self):
        """Get utilization percentage for this sheet"""
        sheet_area = self.width_mm * self.height_mm
        if sheet_area == 0:
            return 0.0

        part_area = sum(part.width_mm * part.height_mm for part in self.parts)
        return (part_area / sheet_area) * 100

class ExportPartPlacement:
    """Canonical part placement data model"""

    def __init__(self, part_id, label, width_mm, height_mm, x_mm, y_mm, rotation_degrees=0):
        self.part_id = part_id
        self.label = label
        self.width_mm = float(width_mm)  # Always store in mm
        self.height_mm = float(height_mm)  # Always store in mm
        self.x_mm = float(x_mm)  # Always store in mm
        self.y_mm = float(y_mm)  # Always store in mm
        self.rotation_degrees = float(rotation_degrees)

    def get_bounds(self):
        """Get bounding box of the part"""
        return {
            "min_x": self.x_mm,
            "min_y": self.y_mm,
            "max_x": self.x_mm + self.width_mm,
            "max_y": self.y_mm + self.height_mm
        }

    def overlaps_with(self, other_part):
        """Check if this part overlaps with another part"""
        bounds1 = self.get_bounds()
        bounds2 = other_part.get_bounds()

        return not (bounds1["max_x"] <= bounds2["min_x"] or
                   bounds2["max_x"] <= bounds1["min_x"] or
                   bounds1["max_y"] <= bounds2["min_y"] or
                   bounds2["max_y"] <= bounds1["min_y"])
```

#### Export Format Handlers
```python
def export_cutlist_csv(export_job, file_path):
    """Export cutlist to CSV format using ExportJob data"""
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow([
            "Sheet", "Part ID", "Label", "Width", "Height",
            "X Position", "Y Position", "Rotation"
        ])

        # Write data from ExportJob (canonical source)
        for sheet in export_job.sheets:
            for part in sheet.parts:
                # Format dimensions according to measurement system
                if export_job.measurement_system == "imperial":
                    width = format_fractional_inches(mm_to_inches(part.width_mm))
                    height = format_fractional_inches(mm_to_inches(part.height_mm))
                    x_pos = format_fractional_inches(mm_to_inches(part.x_mm))
                    y_pos = format_fractional_inches(mm_to_inches(part.y_mm))
                else:
                    width = f"{part.width_mm:.1f} mm"
                    height = f"{part.height_mm:.1f} mm"
                    x_pos = f"{part.x_mm:.1f} mm"
                    y_pos = f"{part.y_mm:.1f} mm"

                writer.writerow([
                    sheet.sheet_id,
                    part.part_id,
                    part.label,
                    width,
                    height,
                    x_pos,
                    y_pos,
                    f"{part.rotation_degrees:.1f}°"
                ])

def export_nesting_svg(export_job, file_path):
    """Export nesting layout to SVG using ExportJob data"""
    # SVG header
    svg_content = ['<?xml version="1.0" encoding="UTF-8"?>']

    # Calculate total SVG dimensions
    max_width = max(sheet.width_mm for sheet in export_job.sheets) if export_job.sheets else 1220
    total_height = sum(sheet.height_mm + 50 for sheet in export_job.sheets)  # 50mm spacing

    svg_content.append(f'<svg width="{max_width}" height="{total_height}" '
                      f'viewBox="0 0 {max_width} {total_height}" '
                      f'xmlns="http://www.w3.org/2000/svg">')

    # Add styles
    svg_content.append('<style>')
    svg_content.append('.sheet { fill: none; stroke: black; stroke-width: 2; }')
    svg_content.append('.part { fill: lightblue; stroke: blue; stroke-width: 1; }')
    svg_content.append('.label { font-family: Arial; font-size: 12px; text-anchor: middle; }')
    svg_content.append('</style>')

    # Draw sheets and parts from ExportJob (canonical source)
    y_offset = 0
    for sheet in export_job.sheets:
        # Draw sheet outline
        svg_content.append(f'<rect class="sheet" x="0" y="{y_offset}" '
                          f'width="{sheet.width_mm}" height="{sheet.height_mm}"/>')

        # Draw parts
        for part in sheet.parts:
            part_x = part.x_mm
            part_y = y_offset + part.y_mm

            # Draw part rectangle
            svg_content.append(f'<rect class="part" x="{part_x}" y="{part_y}" '
                              f'width="{part.width_mm}" height="{part.height_mm}"/>')

            # Add part label
            label_x = part_x + part.width_mm / 2
            label_y = part_y + part.height_mm / 2
            svg_content.append(f'<text class="label" x="{label_x}" y="{label_y}">'
                              f'{part.label}</text>')

        y_offset += sheet.height_mm + 50  # Add spacing between sheets

    svg_content.append('</svg>')

    # Write SVG file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_content))
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
- May cause AttributeError if hydration tries to access widgets

**Consequences:**
- UI shows wrong values on first load
- Settings don't persist correctly
- Unpredictable behavior across sessions

#### ❌ GUI Access During Hydration
```python
# WRONG - Accessing GUI during hydration
def hydrate_from_params(self):
    self.session = get_session_state()
    self.sheet_width = self.session.get_sheet_width()

    # WRONG: GUI access during hydration
    self.width_input.setText(str(self.sheet_width))  # Widgets don't exist yet!
    self.preset_combo.setCurrentText("None / Custom")  # Will crash!

    # WRONG: Creating widgets during hydration
    if not self.form:
        self.form = QtWidgets.QWidget()  # Violates initialization order
```

**Why This Fails:**
- Widgets may not exist yet (AttributeError)
- Violates separation of concerns
- Makes testing difficult
- Breaks the initialization contract

**Consequences:**
- Runtime crashes with AttributeError
- Impossible to unit test hydration logic
- Tight coupling between data and UI

#### ❌ Preset Auto-Selection
```python
# WRONG - Auto-selecting presets based on current values
def load_panel(self):
    # WRONG: Auto-detecting and selecting presets
    if self.sheet_width == 1220 and self.sheet_height == 2440:
        self.preset_combo.setCurrentText("4' x 8'")
    elif self.sheet_width == inches_to_mm(48) and self.sheet_height == inches_to_mm(96):
        self.preset_combo.setCurrentText("4' x 8'")

    # WRONG: Selecting preset during hydration
    def hydrate_from_params(self):
        self.sheet_width = self.session.get_sheet_width()
        # Auto-select matching preset
        matching_preset = self.find_matching_preset(self.sheet_width, self.sheet_height)
        self.current_preset = matching_preset  # Violates preset/default separation
```

**Why This Fails:**
- Violates preset/default separation
- Confuses users about what's a default vs preset
- Makes behavior unpredictable
- Breaks the "None / Custom" default rule

**Consequences:**
- Users can't distinguish between defaults and presets
- Unexpected preset selection confuses workflow
- Breaks user mental model of presets vs defaults

#### ❌ Default Modification During Hydration
```python
# WRONG - Modifying defaults during TaskPanel initialization
def hydrate_from_params(self):
    self.session = get_session_state()
    self.settings = SquatchCutPreferences()

    # Load current values
    self.sheet_width = self.session.get_sheet_width()

    # WRONG: Modifying defaults during hydration
    if self.sheet_width != self.settings.get_default_sheet_width():
        # "Update" defaults to match current values
        self.settings.set_default_sheet_width(self.sheet_width)  # VIOLATION!
        self.settings.save()  # VIOLATION!

    # WRONG: Auto-saving current state as defaults
    self.settings.set_default_sheet_height(self.sheet_height)  # VIOLATION!
```

**Why This Fails:**
- Violates HYDRATION-002 constraint
- Defaults should only change via Settings panel
- Creates unpredictable default behavior
- Breaks user expectations about persistence

**Consequences:**
- Defaults change without user knowledge
- Settings panel becomes unreliable
- User loses control over their preferences

#### ❌ Circular Hydration Dependencies
```python
# WRONG - Creating circular dependencies during hydration
def hydrate_from_params(self):
    self.session = get_session_state()

    # WRONG: Hydration depends on UI state
    if hasattr(self, 'measurement_combo') and self.measurement_combo:
        current_system = self.measurement_combo.currentText()  # UI dependency!
        self.measurement_system = current_system
    else:
        self.measurement_system = self.session.get_measurement_system()

    # WRONG: Hydration triggers other hydration
    self.sheet_width = self.session.get_sheet_width()
    self.update_related_values()  # May trigger more hydration

def update_related_values(self):
    # WRONG: Called during hydration, but accesses UI
    if self.measurement_system == "imperial":
        self.width_input.setText(format_fractional_inches(mm_to_inches(self.sheet_width)))
```

**Why This Fails:**
- Creates circular dependencies
- Makes initialization order unpredictable
- Violates single responsibility principle
- Makes debugging extremely difficult

#### ❌ Exception Handling That Masks Problems
```python
# WRONG - Catching exceptions that hide hydration problems
def hydrate_from_params(self):
    try:
        self.session = get_session_state()
        self.sheet_width = self.session.get_sheet_width()

        # WRONG: Accessing GUI during hydration, but catching the error
        self.width_input.setText(str(self.sheet_width))  # Will fail
    except AttributeError:
        # WRONG: Silently ignoring the architectural violation
        pass  # This hides the real problem!
    except Exception as e:
        # WRONG: Generic exception handling that masks issues
        print(f"Hydration failed: {e}")  # Doesn't fix the root cause
        self.sheet_width = 1220.0  # Band-aid solution
```

**Why This Fails:**
- Masks architectural violations
- Makes debugging impossible
- Hides the real problem
- Creates unreliable behavior

#### ❌ Lazy Hydration
```python
# WRONG - Lazy hydration that happens on-demand
def get_sheet_width(self):
    # WRONG: Hydrating on first access
    if not hasattr(self, '_sheet_width'):
        self.hydrate_from_params()  # Too late!
    return self._sheet_width

def create_widgets(self):
    self.form = QtWidgets.QWidget()
    self.width_input = QtWidgets.QLineEdit()

    # WRONG: Accessing values that trigger lazy hydration
    current_width = self.get_sheet_width()  # Triggers hydration after widgets exist
    self.width_input.setText(str(current_width))
```

**Why This Fails:**
- Violates initialization order
- Makes behavior unpredictable
- Can trigger hydration at wrong times
- Breaks the explicit initialization contract

#### ❌ Partial Hydration
```python
# WRONG - Only hydrating some values
def hydrate_from_params(self):
    self.session = get_session_state()

    # WRONG: Only hydrating width, forgetting height
    self.sheet_width = self.session.get_sheet_width()
    # Missing: self.sheet_height = self.session.get_sheet_height()

    # WRONG: Conditional hydration that skips values
    if self.is_advanced_mode():
        self.kerf_width = self.session.get_kerf_width()
    # Missing kerf_width for non-advanced mode

def populate_ui_values(self):
    self.width_input.setText(str(self.sheet_width))
    # CRASH: self.sheet_height is not defined!
    self.height_input.setText(str(self.sheet_height))  # AttributeError!
```

**Why This Fails:**
- Creates incomplete state
- Leads to AttributeError crashes
- Makes behavior inconsistent
- Violates the complete initialization principle

### Measurement System Anti-Patterns

#### ❌ Imperial Internal Storage
```python
# WRONG - Storing imperial values internally
def set_width(self, inches_value):
    self.width = inches_value  # Should be mm!
    self.internal_dimensions = {"width": inches_value, "height": 96}  # Mixed units!

# WRONG - Conditional internal storage
def store_dimension(self, value, measurement_system):
    if measurement_system == "imperial":
        self.sheet_width = value  # Storing inches internally!
    else:
        self.sheet_width = value  # Storing mm internally!
    # Now self.sheet_width could be in either unit!

# WRONG - Storing original input format
def handle_input(self, user_input):
    self.raw_width = user_input  # Could be "48 3/4" or "1220.5"
    # Later code has to guess the format and units
```

**Why This Fails:**
- Inconsistent with FreeCAD internal units
- Causes conversion errors in calculations
- Makes calculations unreliable
- Creates ambiguity about what units values represent
- Breaks interoperability with FreeCAD geometry

**Consequences:**
- Nesting calculations produce wrong results
- Export data has incorrect dimensions
- FreeCAD geometry creation fails
- Cross-module communication breaks

#### ❌ Decimal Inch Display
```python
# WRONG - Using decimal inches in UI
def format_imperial(self, mm_value):
    inches = mm_to_inches(mm_value)
    return f"{inches:.2f} in"  # Decimal inches violate woodworking standards!

# WRONG - Inconsistent decimal precision
def format_dimensions(self, width_mm, height_mm):
    width_inches = mm_to_inches(width_mm)
    height_inches = mm_to_inches(height_mm)
    return f"{width_inches:.3f}\" x {height_inches:.1f}\""  # Different precisions!

# WRONG - Scientific notation for inches
def format_large_imperial(self, mm_value):
    inches = mm_to_inches(mm_value)
    return f"{inches:.2e} in"  # 4.80e+01 instead of 48"
```

**Why This Fails:**
- Doesn't match woodworking industry standards
- Users expect fractional inches (1/2, 3/4, etc.)
- Inconsistent with project requirements
- Confuses users familiar with fractional measurements
- Makes manual verification difficult

**Consequences:**
- Users can't easily verify measurements
- Doesn't match physical measuring tools
- Breaks user mental model of woodworking
- Inconsistent with cut list expectations

#### ❌ Mixed Unit Calculations
```python
# WRONG - Mixing units in calculations
def calculate_area(self):
    width_inches = float(self.width_input.text())  # Could be inches
    height_mm = self.height_mm                     # Definitely mm
    return width_inches * height_mm  # Mixed units = wrong result!

# WRONG - Assuming input units
def calculate_perimeter(self):
    # Assumes input is always in mm, but could be inches
    width = float(self.width_input.text())
    height = float(self.height_input.text())
    return 2 * (width + height)  # Wrong if inputs are inches!

# WRONG - Unit-dependent calculations
def validate_dimensions(self):
    width = float(self.width_input.text())
    if self.measurement_system == "imperial":
        return width > 1  # Assumes inches, but what if it's mm?
    else:
        return width > 25  # Assumes mm, but what if it's inches?
```

**Why This Fails:**
- Creates incorrect calculations
- Results depend on current UI state
- Makes code unreliable and unpredictable
- Violates the internal mm storage rule

#### ❌ Conversion Chain Errors
```python
# WRONG - Multiple conversions that accumulate errors
def process_measurement(self, user_input):
    # Convert to inches first
    inches = parse_fractional_inches(user_input)

    # Convert to cm for some reason
    cm = inches * 2.54

    # Convert to mm
    mm = cm * 10

    # Convert back to inches for validation
    validation_inches = mm / 25.4

    # Each conversion introduces floating point errors!
    return mm

# WRONG - Unnecessary round-trip conversions
def format_and_parse(self, mm_value):
    # Convert to display format
    inches = mm_to_inches(mm_value)
    display_text = format_fractional_inches(inches)

    # Immediately parse it back (why?)
    parsed_inches = parse_fractional_inches(display_text)
    return inches_to_mm(parsed_inches)  # Lost precision!
```

**Why This Fails:**
- Accumulates floating point errors
- Unnecessary precision loss
- Makes calculations unreliable
- Violates the "convert once, store in mm" principle

#### ❌ Unit System State Confusion
```python
# WRONG - Storing measurement system in multiple places
def __init__(self):
    self.measurement_system = "metric"  # In TaskPanel
    self.session.measurement_system = "imperial"  # In session
    self.settings.default_units = "metric"  # In settings
    # Which one is correct?

# WRONG - UI-dependent unit detection
def get_current_units(self):
    # Guessing units from UI state
    if "inches" in self.width_label.text():
        return "imperial"
    elif "mm" in self.width_label.text():
        return "metric"
    else:
        return "unknown"  # Unreliable!

# WRONG - Inconsistent unit switching
def switch_to_imperial(self):
    self.measurement_system = "imperial"
    # Forgot to update UI labels!
    # Forgot to reformat input fields!
    # Forgot to update session state!
```

**Why This Fails:**
- Creates inconsistent state across components
- Makes unit system unreliable
- UI and data can get out of sync
- Violates single source of truth principle

#### ❌ Precision Loss and Rounding Errors
```python
# WRONG - Premature rounding
def handle_input(self, user_input):
    inches = parse_fractional_inches(user_input)
    rounded_inches = round(inches, 2)  # Premature rounding!
    mm = inches_to_mm(rounded_inches)
    return round(mm, 1)  # More rounding!

# WRONG - Inconsistent precision
def format_measurements(self, values):
    results = []
    for i, mm_value in enumerate(values):
        if i % 2 == 0:
            # Even indices get more precision
            results.append(f"{mm_value:.3f} mm")
        else:
            # Odd indices get less precision
            results.append(f"{mm_value:.1f} mm")
    return results

# WRONG - Precision depends on measurement system
def store_value(self, value, system):
    if system == "imperial":
        # Store with inch precision
        self.value = round(value, 3)
    else:
        # Store with mm precision
        self.value = round(value, 1)
    # Different precision for same internal value!
```

**Why This Fails:**
- Loses precision unnecessarily
- Creates inconsistent behavior
- Makes calculations less accurate
- Violates the high-precision internal storage principle

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

### Preset and Default Separation Anti-Patterns

#### ❌ Auto-Selecting Presets Based on Current Values
```python
# WRONG - Auto-detecting and selecting presets
def load_panel(self):
    # Load current values
    self.current_width = self.session.get_sheet_width()
    self.current_height = self.session.get_sheet_height()

    # WRONG: Auto-select matching preset
    if self.current_width == 1220 and self.current_height == 2440:
        self.preset_combo.setCurrentText("Standard Metric")  # Auto-selection!
    elif self.current_width == inches_to_mm(48) and self.current_height == inches_to_mm(96):
        self.preset_combo.setCurrentText("4' x 8' Plywood")  # Auto-selection!

# WRONG - Preset selection during hydration
def hydrate_from_params(self):
    self.sheet_width = self.session.get_sheet_width()
    self.sheet_height = self.session.get_sheet_height()

    # WRONG: Determining preset during hydration
    matching_preset = self.find_matching_preset(self.sheet_width, self.sheet_height)
    self.current_preset = matching_preset  # Violates preset/default separation
```

**Why This Fails:**
- Violates the "None / Custom" default rule
- Confuses users about what's a default vs preset
- Makes behavior unpredictable
- Breaks user mental model of presets

**Consequences:**
- Users can't distinguish between their defaults and presets
- Unexpected preset selection disrupts workflow
- Makes it unclear when defaults vs presets are active

#### ❌ Modifying Defaults Through Preset Selection
```python
# WRONG - Preset selection modifies stored defaults
def on_preset_selected(self, preset_name):
    preset_data = self.presets[preset_name]

    # Update UI
    self.width_input.setText(str(preset_data["width"]))
    self.height_input.setText(str(preset_data["height"]))

    # WRONG: Modifying defaults when preset is selected
    self.settings.set_default_sheet_width(preset_data["width"])  # VIOLATION!
    self.settings.set_default_sheet_height(preset_data["height"])  # VIOLATION!
    self.settings.save()  # VIOLATION!

# WRONG - "Apply as Default" functionality in main panel
def on_apply_preset_as_default(self):
    current_preset = self.preset_combo.currentText()
    if current_preset != "None / Custom":
        preset_data = self.presets[current_preset]

        # WRONG: Changing defaults outside Settings panel
        self.settings.set_default_sheet_width(preset_data["width"])  # VIOLATION!
        self.settings.save()  # VIOLATION!
```

**Why This Fails:**
- Violates HYDRATION-002 constraint
- Defaults should only change via Settings panel
- Creates unpredictable default behavior
- Breaks user expectations about persistence

#### ❌ Blurred Preset/Default Boundaries
```python
# WRONG - Mixing preset and default concepts
def __init__(self):
    # WRONG: Treating presets as defaults
    self.default_presets = {
        "user_default": {"width": 1220, "height": 2440},  # Is this a preset or default?
        "project_default": {"width": 1200, "height": 2400}  # Confusing terminology
    }

# WRONG - Saving "current preset" as persistent state
def save_session_state(self):
    # WRONG: Persisting preset selection
    self.session.set_current_preset(self.preset_combo.currentText())  # Violates separation

    # Should only persist actual values, not preset names
    self.session.set_sheet_width(self.current_width)  # CORRECT
    self.session.set_sheet_height(self.current_height)  # CORRECT

# WRONG - Loading preset selection from session
def load_session_state(self):
    # WRONG: Restoring preset selection
    saved_preset = self.session.get_current_preset()
    if saved_preset:
        self.preset_combo.setCurrentText(saved_preset)  # Violates "None / Custom" rule
```

**Why This Fails:**
- Creates confusion between temporary and permanent settings
- Violates the clear separation of concerns
- Makes behavior unpredictable
- Breaks the preset selection model

#### ❌ Preset-Dependent Default Behavior
```python
# WRONG - Default behavior that depends on preset selection
def get_default_kerf(self):
    current_preset = self.preset_combo.currentText()

    # WRONG: Defaults depend on preset selection
    if current_preset == "4' x 8' Plywood":
        return 3.2  # Plywood kerf
    elif current_preset == "2' x 4' Lumber":
        return 2.4  # Lumber kerf
    else:
        return self.settings.get_default_kerf_width()

# WRONG - Validation rules that change based on preset
def validate_dimensions(self):
    current_preset = self.preset_combo.currentText()

    # WRONG: Different validation for different presets
    if "Plywood" in current_preset:
        max_width = inches_to_mm(48)  # Plywood-specific limit
    elif "Lumber" in current_preset:
        max_width = inches_to_mm(24)  # Lumber-specific limit
    else:
        max_width = 10000  # No limit for custom

    return self.current_width <= max_width
```

**Why This Fails:**
- Creates inconsistent behavior
- Makes presets more than just UI convenience
- Violates the principle that presets are just value templates
- Creates complex interdependencies

#### ❌ Incomplete Preset Implementation
```python
# WRONG - Presets that don't cover all relevant values
def on_preset_selected(self, preset_name):
    preset_data = self.presets[preset_name]

    # WRONG: Only updating some values
    self.width_input.setText(str(preset_data["width"]))
    self.height_input.setText(str(preset_data["height"]))
    # Missing: kerf, measurement system, other related settings

# WRONG - Presets with inconsistent data
def setup_presets(self):
    self.presets = {
        "4' x 8'": {"width": inches_to_mm(48), "height": inches_to_mm(96)},
        "Metric Standard": {"width": 1220, "height": 2440, "kerf": 3.2},  # Inconsistent fields
        "Small Sheet": {"width": 600}  # Missing height
    }

# WRONG - Preset selection that leaves UI in inconsistent state
def apply_partial_preset(self, preset_name):
    # Updates some fields but not others
    self.width_input.setText("1220")
    # Forgot to update height, kerf, measurement system
    # UI is now in inconsistent state
```

**Why This Fails:**
- Creates incomplete or inconsistent state
- Confuses users about what the preset actually sets
- Leads to unexpected behavior
- Makes presets unreliable

#### ❌ Settings Panel That Doesn't Control Defaults
```python
# WRONG - Settings panel that can't actually change defaults
class SettingsPanel:
    def __init__(self):
        # WRONG: Loading current values instead of defaults
        self.width_input.setText(str(self.session.get_sheet_width()))  # Current, not default
        self.height_input.setText(str(self.session.get_sheet_height()))  # Current, not default

    def on_save(self):
        # WRONG: Saving to session instead of defaults
        self.session.set_sheet_width(float(self.width_input.text()))  # Wrong target!
        # Should be: self.settings.set_default_sheet_width(...)

# WRONG - Multiple ways to change defaults
def save_current_as_default(self):
    # WRONG: Changing defaults outside Settings panel
    self.settings.set_default_sheet_width(self.current_width)  # Should only happen in Settings

def quick_save_defaults(self):
    # WRONG: Shortcut that bypasses Settings panel
    self.settings.set_default_sheet_width(self.width_input.text())  # Violates single point of control
```

**Why This Fails:**
- Settings panel becomes meaningless
- Multiple ways to change defaults creates confusion
- Violates single point of control principle
- Makes default management unpredictable

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
    # Creates new instance each time - memory leak!
    new_panel = TaskPanel_Settings()
    return new_panel

# WRONG - Not tracking panel instances
def open_advanced_settings(self):
    # Creates new panel every time
    panel = TaskPanel_AdvancedSettings()
    panel.show()  # Multiple panels can be open simultaneously

# WRONG - Circular references
def create_nested_panels(self):
    self.main_panel = TaskPanel_Main()
    self.settings_panel = TaskPanel_Settings()

    # Circular reference - prevents garbage collection
    self.main_panel.settings_ref = self.settings_panel
    self.settings_panel.main_ref = self.main_panel
```

**Why This Fails:**
- Wastes memory and resources
- Can cause conflicts between instances
- Violates singleton pattern for UI panels
- Creates memory leaks
- Makes state management impossible

**Consequences:**
- FreeCAD becomes slow and unresponsive
- Multiple conflicting panels confuse users
- Memory usage grows continuously
- Panel state becomes inconsistent

#### ❌ UI Overflow and Fixed Layouts
```python
# WRONG - Fixed width layouts that overflow narrow docks
def create_layout(self):
    self.setFixedWidth(800)  # Too wide for narrow docks

    # WRONG - Horizontal layout for many controls
    layout = QtWidgets.QHBoxLayout()
    layout.addWidget(QtWidgets.QLabel("Very Long Label Text"))
    layout.addWidget(self.input1)
    layout.addWidget(QtWidgets.QLabel("Another Long Label"))
    layout.addWidget(self.input2)
    # This will overflow in narrow docks

# WRONG - Not considering minimum sizes
def create_inputs(self):
    self.width_input = QtWidgets.QLineEdit()
    self.width_input.setFixedWidth(200)  # Too wide for narrow docks

    # WRONG - Long text without eliding
    self.status_label = QtWidgets.QLabel("This is a very long status message that will overflow")

# WRONG - Grid layouts with too many columns
def create_grid(self):
    grid = QtWidgets.QGridLayout()
    # Too many columns for narrow spaces
    grid.addWidget(QtWidgets.QLabel("Width:"), 0, 0)
    grid.addWidget(self.width_input, 0, 1)
    grid.addWidget(QtWidgets.QLabel("Height:"), 0, 2)
    grid.addWidget(self.height_input, 0, 3)
    grid.addWidget(QtWidgets.QLabel("Kerf:"), 0, 4)
    grid.addWidget(self.kerf_input, 0, 5)
```

**Why This Fails:**
- Makes UI unusable on narrow docks
- Poor user experience in constrained spaces
- Violates responsive design principles
- Forces horizontal scrolling
- Makes text unreadable

#### ❌ Signal Connection Problems
```python
# WRONG - Connecting signals before widgets exist
def __init__(self):
    self.connect_signals()  # Widgets don't exist yet!
    self.create_widgets()

# WRONG - Not disconnecting signals during updates
def update_all_values(self):
    # This will trigger signals and cause recursion
    self.width_input.setText("1220")  # Triggers textChanged
    self.height_input.setText("2440")  # Triggers textChanged
    # Each signal handler tries to update other fields

# WRONG - Connecting the same signal multiple times
def setup_ui(self):
    self.width_input.textChanged.connect(self.on_width_changed)
    # Later in the code...
    self.width_input.textChanged.connect(self.on_width_changed)  # Connected twice!

# WRONG - Lambda functions that capture self
def connect_dynamic_signals(self):
    for i, button in enumerate(self.buttons):
        # This creates a closure that captures the loop variable
        button.clicked.connect(lambda: self.on_button_clicked(i))  # Wrong i value!
```

**Why This Fails:**
- Causes AttributeError crashes
- Creates infinite recursion loops
- Leads to duplicate signal handling
- Memory leaks from unclosed lambdas
- Unpredictable behavior

#### ❌ Widget Lifecycle Problems
```python
# WRONG - Not properly cleaning up widgets
def close_panel(self):
    self.form.hide()  # Widget still exists in memory
    # Should call self.form.deleteLater()

# WRONG - Accessing deleted widgets
def update_ui_later(self):
    # Widget might have been deleted
    self.width_input.setText("1220")  # RuntimeError: wrapped C/C++ object deleted

# WRONG - Creating widgets in wrong thread
def background_task(self):
    # WRONG - Creating GUI widgets in background thread
    self.progress_dialog = QtWidgets.QProgressDialog()  # GUI in wrong thread!

# WRONG - Modifying UI from non-GUI thread
def worker_thread_function(self):
    # WRONG - Updating GUI from worker thread
    self.status_label.setText("Processing...")  # Thread safety violation!
```

**Why This Fails:**
- Memory leaks from undestroyed widgets
- Runtime crashes from deleted widget access
- Thread safety violations
- Unpredictable Qt behavior

#### ❌ Input Validation Problems
```python
# WRONG - No input validation
def on_width_changed(self, text):
    # Directly using user input without validation
    self.sheet_width = float(text)  # Will crash on invalid input!

# WRONG - Inconsistent validation
def validate_inputs(self):
    # Different validation for similar inputs
    if self.width_input.text():
        width = float(self.width_input.text())  # May crash

    height_text = self.height_input.text()
    if height_text and height_text.isdigit():  # Different validation logic
        height = int(height_text)

# WRONG - Validation that prevents user input
def strict_validation(self, text):
    # Prevents user from typing intermediate values
    try:
        value = float(text)
        if value <= 0:
            self.width_input.setText("")  # Clears input while typing!
    except ValueError:
        self.width_input.setText("")  # Clears input on any invalid character!

# WRONG - No visual feedback for errors
def validate_silently(self, text):
    try:
        value = float(text)
        self.sheet_width = value
    except ValueError:
        pass  # Silent failure - user has no idea what's wrong
```

**Why This Fails:**
- Crashes on invalid user input
- Inconsistent user experience
- Prevents normal typing workflow
- No feedback about what's wrong
- Makes debugging impossible

#### ❌ State Management Problems
```python
# WRONG - UI state not synchronized with data
def on_preset_selected(self, preset_name):
    # Updates UI but not internal state
    self.width_input.setText("1220")
    self.height_input.setText("2440")
    # Forgot: self.sheet_width = 1220, self.sheet_height = 2440

# WRONG - Multiple sources of truth
def __init__(self):
    self.ui_width = 1220      # UI state
    self.data_width = 1220    # Data state
    self.session_width = 1220 # Session state
    # Which one is correct?

# WRONG - State updates that don't persist
def apply_temporary_changes(self):
    # Updates UI but doesn't save to session
    self.width_input.setText("2440")
    self.height_input.setText("1220")
    # Changes lost when panel reopens

# WRONG - Inconsistent state during updates
def update_measurement_system(self, new_system):
    self.measurement_system = new_system
    # UI still shows old units while updating
    self.width_input.setText(self.convert_width(new_system))
    # Brief moment where system and UI are inconsistent
```

**Why This Fails:**
- UI and data get out of sync
- Multiple conflicting states
- Changes don't persist
- Inconsistent behavior
- User confusion about current state

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

## Quality and Performance Guidelines



For detailed requirements on performance, self-correction, destructive changes, and error handling, refer to the [Quality and Performance Guidelines](docs/quality_and_performance.md).



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
