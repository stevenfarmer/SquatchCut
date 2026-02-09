"""Generate simple FreeCAD test documents for SquatchCut.

This script should be run inside FreeCAD's Python console or as a macro.
It creates basic rectangle-based documents used for SquatchCut testing.
"""

from __future__ import annotations

import FreeCADGui as Gui  # type: ignore
from Draft import makeRectangle  # type: ignore

import FreeCAD as App  # type: ignore


def create_basic_rectangles_doc():
    """
    Create a new document named 'SquatchCut_BasicRectangles' with several
    rectangular shapes (e.g. Draft rectangles) in the XY plane.
    Labels align with the small CSV fixture where possible.
    """
    doc = App.newDocument("SquatchCut_BasicRectangles")
    specs = [
        ("P1", 600, 400, (0, 0, 0)),
        ("P2", 800, 500, (700, 0, 0)),
        ("P3", 300, 300, (0, 600, 0)),
        ("P4", 1200, 600, (1000, 600, 0)),
        ("P5", 500, 700, (0, 1200, 0)),
        ("P6", 400, 200, (600, 1200, 0)),
    ]
    for label, width, height, (x, y, z) in specs:
        rect = makeRectangle(length=width, height=height)
        rect.Label = label
        rect.Placement.Base = App.Vector(x, y, z)
    doc.recompute()
    Gui.ActiveDocument = Gui.getDocument(doc.Name)
    print("Created document:", doc.Name)
    return doc


def create_multi_sheet_stress_doc():
    """
    Create a document named 'SquatchCut_MultiSheetTest' with many shapes
    that mimic the multi-sheet CSV fixture.
    """
    doc = App.newDocument("SquatchCut_MultiSheetTest")
    sizes = [
        ("L1", 1800, 900),
        ("L2", 1600, 800),
        ("L3", 1500, 700),
        ("L4", 1200, 1200),
        ("L5", 1100, 900),
        ("M1", 800, 600),
        ("M2", 750, 500),
        ("M3", 700, 400),
        ("M4", 650, 450),
        ("M5", 600, 600),
        ("M6", 550, 350),
        ("M7", 500, 500),
        ("M8", 500, 400),
        ("M9", 450, 300),
        ("M10", 400, 400),
        ("S1", 350, 250),
        ("S2", 300, 200),
        ("S3", 280, 220),
        ("S4", 260, 180),
        ("S5", 240, 160),
        ("S6", 220, 150),
        ("S7", 200, 140),
        ("S8", 180, 130),
        ("S9", 160, 120),
        ("S10", 140, 100),
    ]
    offset_x = 0
    offset_y = 0
    row_height = 0
    for _idx, (label, width, height) in enumerate(sizes):
        rect = makeRectangle(length=width, height=height)
        rect.Label = label
        rect.Placement.Base = App.Vector(offset_x, offset_y, 0)
        offset_x += width + 50
        row_height = max(row_height, height)
        if offset_x > 5000:
            offset_x = 0
            offset_y += row_height + 100
            row_height = 0
    doc.recompute()
    Gui.ActiveDocument = Gui.getDocument(doc.Name)
    print("Created document:", doc.Name)
    return doc


def main():
    create_basic_rectangles_doc()
    create_multi_sheet_stress_doc()
    print("Test documents generated.")


if __name__ == "__main__":
    main()
