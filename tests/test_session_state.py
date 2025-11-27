"""@codex
Tests for pure session_state helpers (sheet size, kerf/gap, last layout copies).
"""

from SquatchCut.core.session_state import (
    set_sheet_size,
    get_sheet_size,
    set_kerf_mm,
    get_kerf_mm,
    set_gap_mm,
    get_gap_mm,
    set_last_layout,
    get_last_layout,
)
from SquatchCut.core.nesting import PlacedPart


def test_sheet_size_roundtrip():
    set_sheet_size(123.0, 456.0)
    w, h = get_sheet_size()
    assert w == 123.0
    assert h == 456.0


def test_kerf_and_gap_roundtrip():
    set_kerf_mm(3.5)
    set_gap_mm(1.25)
    assert get_kerf_mm() == 3.5
    assert get_gap_mm() == 1.25


def test_last_layout_roundtrip_is_copy():
    layout = [
        PlacedPart(
            id="p1",
            sheet_index=0,
            x=0.0,
            y=0.0,
            width=100.0,
            height=50.0,
            rotation_deg=0,
        )
    ]
    set_last_layout(layout)
    got = get_last_layout()
    # Contents equal
    assert len(got) == 1
    assert got[0].id == "p1"
    # But list should be a copy, not the same reference
    assert got is not layout
