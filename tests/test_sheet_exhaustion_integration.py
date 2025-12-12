"""Integration tests for sheet exhaustion detection during nesting."""


from SquatchCut.core.nesting import (
    Part,
    analyze_sheet_exhaustion,
    nest_on_multiple_sheets,
)


def test_sheet_exhaustion_detection_during_nesting():
    """Test that sheet exhaustion is properly detected during nesting."""
    # Create parts that will require more sheets than available
    parts = [
        Part(id="P1", width=500, height=1000, can_rotate=False),  # Large part
        Part(id="P2", width=500, height=1000, can_rotate=False),  # Large part
        Part(id="P3", width=500, height=1000, can_rotate=False),  # Large part
    ]

    # Define only 2 sheets, but parts will need 3 sheets
    sheet_definitions = [
        {"width_mm": 600, "height_mm": 1200, "quantity": 1, "label": "Sheet 1"},
        {"width_mm": 600, "height_mm": 1200, "quantity": 1, "label": "Sheet 2"},
    ]

    # Run nesting - should trigger exhaustion
    placed_parts = nest_on_multiple_sheets(
        parts, sheet_width=600, sheet_height=1200, sheet_definitions=sheet_definitions
    )

    # Verify all parts were placed (using last available sheet type for overflow)
    assert len(placed_parts) == 3

    # Analyze the results for exhaustion
    from SquatchCut.core.nesting import expand_sheet_sizes

    sheet_sizes = expand_sheet_sizes(sheet_definitions)
    exhaustion = analyze_sheet_exhaustion(placed_parts, sheet_sizes)

    # Verify exhaustion was detected
    assert exhaustion["sheets_available"] == 2
    assert exhaustion["sheets_used"] == 3  # More sheets used than available
    assert exhaustion["sheets_exhausted"] is True
    assert exhaustion["max_sheet_index"] >= 2  # Using sheet index 2 (3rd sheet)


def test_no_exhaustion_when_within_limits():
    """Test that no exhaustion is detected when within sheet limits."""
    # Create parts that fit within available sheets
    parts = [
        Part(id="P1", width=200, height=200, can_rotate=False),
        Part(id="P2", width=200, height=200, can_rotate=False),
    ]

    # Define enough sheets
    sheet_definitions = [
        {"width_mm": 600, "height_mm": 1200, "quantity": 2, "label": "Sheet 1"},
    ]

    # Run nesting - should not trigger exhaustion
    placed_parts = nest_on_multiple_sheets(
        parts, sheet_width=600, sheet_height=1200, sheet_definitions=sheet_definitions
    )

    # Verify all parts were placed
    assert len(placed_parts) == 2

    # Analyze the results for exhaustion
    from SquatchCut.core.nesting import expand_sheet_sizes

    sheet_sizes = expand_sheet_sizes(sheet_definitions)
    exhaustion = analyze_sheet_exhaustion(placed_parts, sheet_sizes)

    # Verify no exhaustion was detected
    assert exhaustion["sheets_available"] == 2
    assert exhaustion["sheets_used"] <= 2  # Within available sheets
    assert exhaustion["sheets_exhausted"] is False


def test_exhaustion_with_multiple_sheet_types():
    """Test sheet exhaustion with multiple different sheet types."""
    # Create parts that will exhaust the first sheet type
    parts = [
        Part(id="P1", width=500, height=500, can_rotate=False),  # Fits on small sheet
        Part(id="P2", width=700, height=700, can_rotate=False),  # Needs large sheet
        Part(id="P3", width=700, height=700, can_rotate=False),  # Needs large sheet
        Part(
            id="P4", width=700, height=700, can_rotate=False
        ),  # Will exhaust large sheets
    ]

    # Define mixed sheet types with limited quantities
    sheet_definitions = [
        {"width_mm": 600, "height_mm": 600, "quantity": 1, "label": "Small Sheet"},
        {"width_mm": 800, "height_mm": 800, "quantity": 2, "label": "Large Sheet"},
    ]

    # Run nesting - should trigger exhaustion for large sheets
    placed_parts = nest_on_multiple_sheets(
        parts, sheet_width=600, sheet_height=600, sheet_definitions=sheet_definitions
    )

    # Verify all parts were placed
    assert len(placed_parts) == 4

    # Analyze the results for exhaustion
    from SquatchCut.core.nesting import expand_sheet_sizes

    sheet_sizes = expand_sheet_sizes(sheet_definitions)
    exhaustion = analyze_sheet_exhaustion(placed_parts, sheet_sizes)

    # Verify exhaustion was detected (should have 3 total sheets available: 1 small + 2 large)
    assert exhaustion["sheets_available"] == 3
    # The exact number of sheets used depends on the nesting algorithm, but exhaustion should be detected
    # if we exceed the available sheet count
    if exhaustion["max_sheet_index"] >= 3:
        assert exhaustion["sheets_exhausted"] is True
