"""Tests for sheet exhaustion detection and reporting."""

from SquatchCut.core.nesting import PlacedPart, analyze_sheet_exhaustion


def test_analyze_sheet_exhaustion_no_placements():
    """Test sheet exhaustion analysis with no placements."""
    result = analyze_sheet_exhaustion([], [(600, 1200), (600, 1200)])

    assert result["sheets_available"] == 2
    assert result["sheets_used"] == 0
    assert result["sheets_exhausted"] is False
    assert result["max_sheet_index"] == -1


def test_analyze_sheet_exhaustion_within_limits():
    """Test sheet exhaustion analysis when within available sheet limits."""
    placements = [
        PlacedPart(
            id="P1", sheet_index=0, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
        PlacedPart(
            id="P2", sheet_index=1, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
    ]
    sheet_sizes = [(600, 1200), (600, 1200), (800, 1200)]  # 3 sheets available

    result = analyze_sheet_exhaustion(placements, sheet_sizes)

    assert result["sheets_available"] == 3
    assert result["sheets_used"] == 2
    assert result["sheets_exhausted"] is False
    assert result["max_sheet_index"] == 1


def test_analyze_sheet_exhaustion_exactly_at_limit():
    """Test sheet exhaustion analysis when exactly at the sheet limit."""
    placements = [
        PlacedPart(
            id="P1", sheet_index=0, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
        PlacedPart(
            id="P2", sheet_index=1, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
    ]
    sheet_sizes = [(600, 1200), (600, 1200)]  # Exactly 2 sheets available

    result = analyze_sheet_exhaustion(placements, sheet_sizes)

    assert result["sheets_available"] == 2
    assert result["sheets_used"] == 2
    assert result["sheets_exhausted"] is False  # Not exhausted, exactly at limit
    assert result["max_sheet_index"] == 1


def test_analyze_sheet_exhaustion_exceeded():
    """Test sheet exhaustion analysis when sheet quantities are exceeded."""
    placements = [
        PlacedPart(
            id="P1", sheet_index=0, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
        PlacedPart(
            id="P2", sheet_index=1, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
        PlacedPart(
            id="P3", sheet_index=2, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
    ]
    sheet_sizes = [
        (600, 1200),
        (600, 1200),
    ]  # Only 2 sheets available, but using sheet index 2

    result = analyze_sheet_exhaustion(placements, sheet_sizes)

    assert result["sheets_available"] == 2
    assert result["sheets_used"] == 3
    assert result["sheets_exhausted"] is True  # Exhausted - using more than available
    assert result["max_sheet_index"] == 2


def test_analyze_sheet_exhaustion_no_sheet_sizes():
    """Test sheet exhaustion analysis with no sheet size constraints (simple mode)."""
    placements = [
        PlacedPart(
            id="P1", sheet_index=0, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
        PlacedPart(
            id="P2", sheet_index=1, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
    ]

    result = analyze_sheet_exhaustion(placements, None)

    assert result["sheets_available"] == 0  # No constraints in simple mode
    assert result["sheets_used"] == 2
    assert result["sheets_exhausted"] is False  # Can't be exhausted without constraints
    assert result["max_sheet_index"] == 1


def test_analyze_sheet_exhaustion_empty_sheet_sizes():
    """Test sheet exhaustion analysis with empty sheet sizes list."""
    placements = [
        PlacedPart(
            id="P1", sheet_index=0, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
    ]

    result = analyze_sheet_exhaustion(placements, [])

    assert result["sheets_available"] == 0
    assert result["sheets_used"] == 1
    assert result["sheets_exhausted"] is False
    assert result["max_sheet_index"] == 0


def test_analyze_sheet_exhaustion_single_sheet_multiple_parts():
    """Test sheet exhaustion analysis with multiple parts on a single sheet."""
    placements = [
        PlacedPart(
            id="P1", sheet_index=0, x=0, y=0, width=100, height=100, rotation_deg=0
        ),
        PlacedPart(
            id="P2", sheet_index=0, x=100, y=0, width=100, height=100, rotation_deg=0
        ),
        PlacedPart(
            id="P3", sheet_index=0, x=0, y=100, width=100, height=100, rotation_deg=0
        ),
    ]
    sheet_sizes = [(600, 1200)]  # Only 1 sheet available

    result = analyze_sheet_exhaustion(placements, sheet_sizes)

    assert result["sheets_available"] == 1
    assert result["sheets_used"] == 1  # All parts on same sheet
    assert result["sheets_exhausted"] is False
    assert result["max_sheet_index"] == 0
