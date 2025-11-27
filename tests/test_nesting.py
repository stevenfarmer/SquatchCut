"""@codex
Tests for the core nesting algorithm (overlaps, rotation, multi-sheet behavior).
"""

import pytest

from SquatchCut.core.nesting import (
    Part,
    PlacedPart,
    nest_on_multiple_sheets,
    run_shelf_nesting,
)


def _rects_overlap(a: PlacedPart, b: PlacedPart) -> bool:
    """Axis-aligned bounding box overlap check in 2D."""
    if a.sheet_index != b.sheet_index:
        return False

    ax1, ay1 = a.x, a.y
    ax2, ay2 = a.x + a.width, a.y + a.height

    bx1, by1 = b.x, b.y
    bx2, by2 = b.x + b.width, b.y + b.height

    # No overlap if one is completely to one side
    if ax2 <= bx1 or bx2 <= ax1:
        return False
    if ay2 <= by1 or by2 <= ay1:
        return False
    return True


def test_nesting_no_overlap_simple():
    """Basic sanity: multiple small rectangles on one sheet must not overlap."""
    parts = [
        Part(id="p1", width=200, height=100),
        Part(id="p2", width=150, height=150),
        Part(id="p3", width=100, height=200),
        Part(id="p4", width=300, height=100),
    ]
    sheet_w = 1000
    sheet_h = 1000

    placed = nest_on_multiple_sheets(parts, sheet_w, sheet_h)

    # same number of placed parts as input
    assert len(placed) == len(parts)

    # No two parts overlap on the same sheet
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            assert not _rects_overlap(placed[i], placed[j]), (
                f"Overlap detected between {placed[i].id} and {placed[j].id}"
            )


def test_nesting_respects_can_rotate():
    """Parts that can rotate may be placed with width/height swapped."""
    # Create a part that only fits if rotated on a narrow sheet
    sheet_w = 300
    sheet_h = 1000

    tall = Part(id="tall", width=400, height=200, can_rotate=True)
    small = Part(id="small", width=100, height=100, can_rotate=False)

    placed = nest_on_multiple_sheets([tall, small], sheet_w, sheet_h)

    # Find the 'tall' placement
    tall_placed = next(p for p in placed if p.id == "tall")

    # It should have been rotated to width <= sheet_w
    assert tall_placed.width <= sheet_w
    assert tall_placed.rotation_deg in (0, 90)


def test_nesting_multiple_sheets():
    """Verify that multiple sheets are used when necessary."""
    parts = [
        Part(id=f"p{i}", width=600, height=600)
        for i in range(6)
    ]
    sheet_w = 1000
    sheet_h = 1000

    placed = nest_on_multiple_sheets(parts, sheet_w, sheet_h)
    assert len(placed) == len(parts)

    sheets_used = {p.sheet_index for p in placed}
    # At least 2 sheets should be used
    assert len(sheets_used) >= 2


def test_nesting_rotation_flag_preserved():
    """Check that rotation_deg = 90 only occurs when can_rotate=True."""
    parts = [
        Part(id="rot_ok", width=400, height=200, can_rotate=True),
        Part(id="rot_no", width=400, height=200, can_rotate=False),
    ]
    sheet_w = 500
    sheet_h = 1000

    placed = nest_on_multiple_sheets(parts, sheet_w, sheet_h)

    rot_ok = next(p for p in placed if p.id == "rot_ok")
    rot_no = next(p for p in placed if p.id == "rot_no")

    assert rot_ok.rotation_deg in (0, 90)
    # rot_no must never be rotated by the algorithm
    assert rot_no.rotation_deg == 0


def test_nesting_rejects_unfittable_part():
    """Parts that cannot fit a sheet in any orientation should raise ValueError."""
    too_big = Part(id="huge", width=5000, height=5000, can_rotate=False)
    with pytest.raises(ValueError):
        nest_on_multiple_sheets([too_big], sheet_width=1000, sheet_height=1000)


def test_run_shelf_nesting_handles_empty_and_invalid():
    """run_shelf_nesting should filter bad input and expand quantities."""
    assert run_shelf_nesting(200, 200, None) == []

    panels = [
        {"width": 500, "height": 500},        # too large for usable area → skipped
        {"width": "oops", "height": 50},  # parsing fails → skipped
        {"width": 0, "height": 10},         # zero dims → skipped
        {"width": 10, "height": -1},        # negative dims → skipped
        {"width": 50, "height": 50, "qty": 2},
    ]

    placements = run_shelf_nesting(200, 200, panels, margin=5)
    assert len(placements) == 2
    assert placements[0]["panel_index"] == len(panels) - 1
    assert placements[0]["instance_index"] == 0
    assert placements[1]["instance_index"] == 1


def test_run_shelf_nesting_wraps_rows_and_stops_on_height_limit():
    """Ensure row wrapping occurs and stops when height is exceeded."""
    panels = [
        {"width": 120, "height": 140},
        {"width": 150, "height": 60},
        {"width": 200, "height": 60},  # forces wrap, then triggers height stop
    ]

    placements = run_shelf_nesting(260, 200, panels, margin=10)

    # Only the first should place; wrap on second triggers height stop for the rest
    assert len(placements) == 1
    assert placements[0]["y"] == 10  # first row at top margin
