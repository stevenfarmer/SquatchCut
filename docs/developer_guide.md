# SquatchCut Developer Guide

This is the authoritative developer guidance for AI and human contributors. It consolidates `AGENTS.md` and the archived [SquatchCut Project Guide v3.3 – AI worker edition](archive/Project_Guide_v3.3.md), and it defines the AI worker communication rules, hydration order, UI constraints, and testing mandates (v3.2 retained for history).

## New Developer Utilities

### Performance Monitoring (`freecad/SquatchCut/core/performance_utils.py`)

#### Performance Decorators

Use the `@performance_monitor` decorator to track slow operations:

```python
from SquatchCut.core.performance_utils import performance_monitor

@performance_monitor("CSV Import", threshold_seconds=2.0)
def import_large_csv(file_path):
    # Your implementation here
    pass
```

#### Large Dataset Optimization

Use the `@optimize_for_large_datasets` decorator for functions that process many items:

```python
from SquatchCut.core.performance_utils import optimize_for_large_datasets

@optimize_for_large_datasets
def process_parts(parts_list):
    # Automatically checks system resources for large datasets
    # Validates dataset size limits
    # Logs performance warnings for very large datasets
    pass
```

#### Progress Tracking

For long-running operations with known progress:

```python
from SquatchCut.core.performance_utils import ProgressTracker

def process_many_items(items):
    tracker = ProgressTracker(len(items), "Processing Items")

    for item in items:
        # Process item
        tracker.update(1)  # Update progress

    tracker.finish()  # Log completion
```

#### Batch Processing

For memory-efficient processing of large datasets:

```python
from SquatchCut.core.performance_utils import batch_process

def process_large_dataset(items):
    for batch in batch_process(items, batch_size=100):
        # Process batch of up to 100 items
        process_batch(batch)
```

### Input Validation (`freecad/SquatchCut/core/input_validation.py`)

#### Basic Validation

```python
from SquatchCut.core.input_validation import validate_positive_number

try:
    width = validate_positive_number(user_input, "width")
except ValidationError as e:
    # Handle validation error with user-friendly message
    show_error_dialog(e.message, e.details, e.user_action)
```

#### Sheet Dimensions

```python
from SquatchCut.core.input_validation import validate_sheet_dimensions

try:
    width_mm, height_mm = validate_sheet_dimensions(
        width_input, height_input, "imperial"
    )
except ValidationError as e:
    handle_validation_error(e)
```

#### Panel Data Validation

```python
from SquatchCut.core.input_validation import validate_panel_data

try:
    panel = validate_panel_data(
        panel_id="P001",
        width="12 1/2",
        height="24",
        quantity=2,
        units_system="imperial"
    )
    # Returns: {"id": "P001", "width": 317.5, "height": 609.6, "qty": 2}
except ValidationError as e:
    handle_validation_error(e)
```

#### File Path Validation

```python
from SquatchCut.core.input_validation import validate_csv_file_path, validate_export_path

# CSV import validation
try:
    validated_path = validate_csv_file_path(user_selected_path)
except ValidationError as e:
    show_error_dialog(e.message, e.details, e.user_action)

# Export path validation
try:
    safe_path = validate_export_path(user_path, ".csv")
except ValidationError as e:
    handle_validation_error(e)
```

### Error Handling (`freecad/SquatchCut/ui/error_handling.py`)

#### Standardized Error Dialogs

```python
from SquatchCut.ui.error_handling import show_error_dialog, show_warning_dialog

# Error with details and user action
show_error_dialog(
    title="Import Failed",
    message="Could not read CSV file",
    details="File format is invalid or corrupted",
    user_action="Please check the file format and try again"
)

# Warning dialog
show_warning_dialog(
    title="Large Dataset",
    message="Processing 5000+ parts may take several minutes",
    user_action="Consider splitting into smaller files for better performance"
)
```

#### Command Error Handling

```python
from SquatchCut.ui.error_handling import handle_command_error

def Activated(self):
    try:
        # Command implementation
        pass
    except Exception as e:
        handle_command_error(
            "Import CSV",
            e,
            "Failed to import CSV file",
            "Please check the file format and try again"
        )
```

#### Custom Error Types

```python
from SquatchCut.ui.error_handling import ValidationError, ProcessingError

# Validation errors (user input issues)
raise ValidationError(
    "Invalid Sheet Size",
    "Width must be positive",
    "Please enter a width greater than 0"
)

# Processing errors (algorithm/system issues)
raise ProcessingError(
    "Nesting Failed",
    "Parts do not fit on sheet",
    "Try using a larger sheet or smaller parts"
)
```

### Progress Indicators (`freecad/SquatchCut/ui/progress.py`)

#### Simple Progress Context

For operations without specific progress tracking:

```python
from SquatchCut.ui.progress import SimpleProgressContext

def long_operation():
    with SimpleProgressContext("Processing...", "SquatchCut"):
        # Long-running operation
        time.sleep(5)
    # Progress dialog automatically closes
```

#### Detailed Progress Dialog

For operations with known progress steps:

```python
from SquatchCut.ui.progress import ProgressDialog

def process_items(items):
    with ProgressDialog("Processing Items") as progress:
        progress.set_range(0, len(items))

        for i, item in enumerate(items):
            progress.set_value(i)
            progress.set_label(f"Processing item {i+1} of {len(items)}")
            # Process item

        progress.set_value(len(items))
        progress.set_label("Complete")
```

## Best Practices

### Performance Considerations

1. **Use performance monitoring** for operations that might be slow
2. **Validate dataset sizes** before processing large amounts of data
3. **Implement progress indicators** for operations taking >500ms
4. **Use batch processing** for memory-intensive operations

## Communication Protocol

AI workers must follow the communication protocol directed by the **lead developer & product manager**. Always remember the **user is a non-technical stakeholder**, so stay high level and avoid jargon. When details are fuzzy, **pause, ask 3-4 clarifying questions** before agreeing to a plan. Once the path forward is clear, **explain your plan in plain english** and deliver **stakeholder-ready check-ins** that summarize progress and next steps. If requirements conflict with each other or with existing constraints, **stop and escalate when instructions conflict** rather than guessing.

### Error Handling Guidelines

1. **Always use ValidationError** for user input problems
2. **Provide specific error messages** with actionable guidance
3. **Include user actions** in error dialogs
4. **Log technical details** while showing user-friendly messages

### Input Validation Rules

1. **Validate all user inputs** before processing
2. **Use appropriate validation functions** for different data types
3. **Handle edge cases** (zero values, empty strings, etc.)
4. **Provide clear feedback** on validation failures

### UI Integration

1. **Add progress indicators** to all long-running commands
2. **Use standardized error dialogs** for consistent UX
3. **Implement keyboard shortcuts** for common operations
4. **Follow FreeCAD TaskPanel patterns** for UI consistency

## Testing New Features

When adding new utilities or features:

1. **Write comprehensive tests** covering normal and edge cases
2. **Test error conditions** and validation failures
3. **Verify performance** with large datasets
4. **Check UI responsiveness** during long operations
5. **Test keyboard shortcuts** and accessibility features

Example test structure:

```python
def test_validation_function():
    # Test valid inputs
    result = validate_function("valid_input")
    assert result == expected_value

    # Test invalid inputs
    with pytest.raises(ValidationError) as exc_info:
        validate_function("invalid_input")

    assert "expected error message" in str(exc_info.value.message)
    assert exc_info.value.user_action is not None
```

## Property-Based Testing with Hypothesis

SquatchCut uses property-based testing (PBT) with the Hypothesis framework to automatically generate test cases and find edge cases that traditional unit tests might miss.

### What is Property-Based Testing?

Instead of writing specific test cases with fixed inputs, property-based testing:

1. **Defines properties** that should always be true
2. **Generates random inputs** automatically
3. **Finds counterexamples** when properties fail
4. **Shrinks failures** to minimal failing cases

### Running Property-Based Tests

```bash
# Run all property-based tests
export PYTHONPATH=$PYTHONPATH:$(pwd)/freecad && pytest tests/test_property_based*.py -v

# Run with more examples (slower but more thorough)
export PYTHONPATH=$PYTHONPATH:$(pwd)/freecad && pytest tests/test_property_based*.py --hypothesis-show-statistics
```

### Core Property Tests (`tests/test_property_based.py`)

#### Unit Conversion Properties

```python
@given(st.floats(min_value=0.001, max_value=10000.0))
def test_mm_to_inches_roundtrip(self, mm_value):
    """Property: Converting mm to inches and back should preserve the value."""
    inches = mm_to_inches(mm_value)
    back_to_mm = inches_to_mm(inches)
    assert abs(mm_value - back_to_mm) < 0.001
```

#### Nesting Algorithm Properties

```python
@given(valid_parts(max_parts=20), valid_sheet_size())
def test_nesting_no_overlaps(self, parts, sheet_size):
    """Property: Nested parts should never overlap on the same sheet."""
    # Automatically tests with thousands of random part configurations
```

#### Stateful Testing

Uses `RuleBasedStateMachine` to test complex sequences of operations:

```python
class NestingStateMachine(RuleBasedStateMachine):
    @rule(part_width=st.floats(min_value=10, max_value=200))
    def add_part(self, part_width, part_height, can_rotate):
        """Add a part to the collection."""

    @rule()
    def run_nesting(self):
        """Run nesting on current parts."""

    @invariant()
    def no_overlaps_invariant(self):
        """Invariant: Placed parts should never overlap."""
```

### Advanced Feature Properties (`tests/test_property_based_advanced.py`)

#### Performance Enhancement Properties

```python
@given(valid_parts_list, sheet_dimensions)
def test_caching_consistency(self, parts, sheet_width, sheet_height):
    """Property: Caching should return identical results for identical inputs."""
    # Tests that caching doesn't change functional behavior
```

### Writing New Property Tests

#### 1. Define Custom Strategies

```python
@st.composite
def valid_parts(draw, max_parts=50):
    """Generate valid Part objects."""
    num_parts = draw(st.integers(min_value=1, max_value=max_parts))
    parts = []
    for i in range(num_parts):
        part = Part(
            id=f"Part_{i}",
            width=draw(st.floats(min_value=1.0, max_value=5000.0)),
            height=draw(st.floats(min_value=1.0, max_value=5000.0)),
            can_rotate=draw(st.booleans()),
        )
        parts.append(part)
    return parts
```

#### 2. Write Property Tests

```python
@given(valid_parts(max_parts=10))
@settings(max_examples=50, deadline=5000)  # Control test parameters
def test_my_property(self, parts):
    """Property: Description of what should always be true."""
    assume(len(parts) > 0)  # Add assumptions to filter inputs

    result = my_function(parts)

    # Assert properties that should always hold
    assert len(result) <= len(parts)
    assert all(r.id in [p.id for p in parts] for r in result)
```

#### 3. Handle Edge Cases

```python
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_robust_function(self, value):
    """Property: Function should handle all valid float inputs."""
    assume(value > 0)  # Filter to valid domain

    try:
        result = my_function(value)
        assert result >= 0  # Property that should hold
    except ValueError:
        # Some inputs may legitimately fail - that's OK
        pass
```

### Property Test Guidelines

#### Best Practices

1. **Start simple** - Test basic properties first
2. **Use assumptions** to filter inputs to valid domains
3. **Allow legitimate failures** - Not all random inputs should succeed
4. **Test invariants** - Properties that should always hold
5. **Use appropriate timeouts** - Complex algorithms need longer deadlines

#### Common Property Types

1. **Roundtrip properties** - `f(g(x)) == x`
2. **Invariant properties** - Something that never changes
3. **Postcondition properties** - Output always satisfies conditions
4. **Metamorphic properties** - Relationship between different inputs
5. **Model-based properties** - Compare against simpler reference implementation

#### Debugging Failed Properties

When Hypothesis finds a failing case:

1. **Look at the minimal example** - Hypothesis shrinks to simplest failure
2. **Add logging** to understand what's happening
3. **Use `@example` decorator** to add the failing case as a regression test
4. **Fix the underlying issue** or adjust the property if it's too strict

```python
@given(st.integers())
@example(42)  # Add specific failing case as regression test
def test_my_property(self, value):
    # Property test implementation
```

### Integration with CI/CD

Property-based tests run automatically in the test suite and help catch:

- **Edge cases** in unit conversions and measurements
- **Algorithmic bugs** in nesting and optimization
- **Performance regressions** with large datasets
- **Data integrity issues** in export/import functions
- **UI state inconsistencies** in complex workflows

The comprehensive property test suite provides confidence that SquatchCut handles the wide variety of real-world inputs users will provide.

## Collaboration Workflow

- Follow the **one ai per branch** rule so tasks stay isolated per branch.
- Name branches `ai/<worker-name>/<feature>` to signal who owns the work.
- Include an **architect/human reviewer** before merging AI-generated changes.
- Ensure **commit messages summarize scope and constraints** for every change.
- PRs must use the **stakeholder-facing template** so reviewers can see intent, tests, and risks.
- **Never force-push over someone else's work**; create a new branch when you need to rebase shared history.
- **Record the plan and test outcomes** in the PR description or linked notes so stakeholders can trace what happened.
