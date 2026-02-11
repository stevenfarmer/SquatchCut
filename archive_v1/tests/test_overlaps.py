"""Tests for overlap detection helper."""

from SquatchCut.core.nesting import PlacedPart
from SquatchCut.core.overlap_check import detect_overlaps


def test_detect_overlaps_finds_overlap():
    a = PlacedPart(id="a", sheet_index=0, x=0, y=0, width=10, height=10)
    b = PlacedPart(id="b", sheet_index=0, x=5, y=5, width=10, height=10)
    conflicts = detect_overlaps([a, b])
    assert conflicts, "Expected overlap to be detected"


def test_detect_overlaps_ignores_adjacent_edges():
    a = PlacedPart(id="a", sheet_index=0, x=0, y=0, width=10, height=10)
    b = PlacedPart(id="b", sheet_index=0, x=10, y=0, width=5, height=10)
    conflicts = detect_overlaps([a, b])
    assert not conflicts
