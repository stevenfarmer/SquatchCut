"""Overlap detection helpers for SquatchCut placements."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable


def detect_overlaps(placements: Iterable, epsilon: float = 1e-6) -> list[tuple]:
    """
    Given a sequence of placed parts, returns a list of overlap conflicts.

    Each placement must have:
        - sheet_index
        - x, y
        - width, height
    Returns:
        list of (placement_a, placement_b) tuples that overlap.
    """
    by_sheet = defaultdict(list)
    for p in placements or []:
        by_sheet[getattr(p, "sheet_index", 0)].append(p)

    conflicts: list[tuple] = []

    for _sheet_index, plist in by_sheet.items():
        n = len(plist)
        for i in range(n):
            a = plist[i]
            a_left = getattr(a, "x", 0.0)
            a_right = a_left + getattr(a, "width", 0.0)
            a_bottom = getattr(a, "y", 0.0)
            a_top = a_bottom + getattr(a, "height", 0.0)

            for j in range(i + 1, n):
                b = plist[j]
                b_left = getattr(b, "x", 0.0)
                b_right = b_left + getattr(b, "width", 0.0)
                b_bottom = getattr(b, "y", 0.0)
                b_top = b_bottom + getattr(b, "height", 0.0)

                if (
                    a_left < b_right - epsilon
                    and a_right > b_left + epsilon
                    and a_bottom < b_top - epsilon
                    and a_top > b_bottom + epsilon
                ):
                    conflicts.append((a, b))
    return conflicts
