import csv
import os

import pytest

pytest.importorskip("FreeCAD")
import FreeCAD  # type: ignore

from SquatchCut.core.sheet_model import SHEET_OBJECT_NAME, ensure_sheet_object
from SquatchCut.gui.commands.cmd_import_csv import run_csv_import
from SquatchCut.gui.nesting_view import rebuild_nested_geometry, NESTED_GROUP_NAME


def _new_doc(name):
    try:
        FreeCAD.closeDocument(name)
    except Exception:
        pass
    return FreeCAD.newDocument(name)


def _close_doc(doc):
    try:
        FreeCAD.closeDocument(doc.Name)
    except Exception:
        pass


def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "width", "height"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_single_sheet_object_is_reused():
    doc = _new_doc("DocSingleSheet")
    first = ensure_sheet_object(100.0, 150.0, doc)
    second = ensure_sheet_object(200.0, 250.0, doc)
    assert first is second
    sheets = [obj for obj in getattr(doc, "Objects", []) if obj.Name == SHEET_OBJECT_NAME]
    assert len(sheets) == 1
    bbox = second.Shape.BoundBox
    assert bbox.XLength == pytest.approx(200.0)
    assert bbox.YLength == pytest.approx(250.0)
    _close_doc(doc)


def test_source_group_rebuilt_on_reimport(tmp_path):
    doc = _new_doc("DocSourceGroup")
    csv1 = tmp_path / "parts1.csv"
    _write_csv(csv1, [{"id": "P1", "width": 100, "height": 200}, {"id": "P2", "width": 150, "height": 250}, {"id": "P3", "width": 200, "height": 300}])
    run_csv_import(doc, str(csv1), csv_units="metric")
    source_group = doc.getObject("SquatchCut_SourceParts")
    assert source_group is not None
    initial_children = list(getattr(source_group, "Group", []))
    assert len(initial_children) == 3
    csv2 = tmp_path / "parts2.csv"
    _write_csv(csv2, [{"id": "A", "width": 80, "height": 60}, {"id": "B", "width": 120, "height": 90}])
    run_csv_import(doc, str(csv2), csv_units="metric")
    source_group2 = doc.getObject("SquatchCut_SourceParts")
    assert source_group2 is source_group
    children = list(getattr(source_group2, "Group", []))
    assert len(children) == 2
    stray_root = [obj for obj in getattr(doc, "Objects", []) if obj not in children and obj is not source_group2 and obj.Name.startswith("SC_Source_")]
    assert not stray_root
    _close_doc(doc)


class _DummyPlacement:
    def __init__(self, part_id, width, height, x=0.0, y=0.0, sheet_index=0, rotation_deg=0.0):
        self.id = part_id
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.sheet_index = sheet_index
        self.rotation_deg = rotation_deg


def test_nested_group_rebuilt_on_rerun():
    doc = _new_doc("DocNestedGroup")
    placements = [
        _DummyPlacement("P1", 100.0, 200.0),
        _DummyPlacement("P2", 120.0, 150.0),
    ]
    group, objs = rebuild_nested_geometry(doc, placements, sheet_w=2440.0, sheet_h=1220.0)
    assert group is not None
    initial_count = len(list(getattr(group, "Group", [])))
    assert initial_count == 2
    group2, objs2 = rebuild_nested_geometry(doc, placements, sheet_w=2440.0, sheet_h=1220.0)
    assert group2 is group
    latest_children = list(getattr(group, "Group", []))
    assert len(latest_children) == initial_count
    stray = [obj for obj in getattr(doc, "Objects", []) if obj not in latest_children and obj is not group and obj.Name.startswith("SC_Nested_")]
    assert not stray
    _close_doc(doc)
