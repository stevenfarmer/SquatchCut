# SquatchCut Developer Guide

The authoritative developer guidance is the [SquatchCut Project Guide v3.3 – AI worker edition](Project_Guide_v3.3.md). Follow that document for AI worker communication rules, hydration order, UI constraints, and testing mandates (v3.2 retained for history).

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
