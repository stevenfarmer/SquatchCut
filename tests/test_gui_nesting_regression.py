import csv

import pytest

pytest.importorskip("FreeCAD")
from SquatchCut.core import session_state
from SquatchCut.gui.commands.cmd_import_csv import run_csv_import
from SquatchCut.gui.commands.cmd_run_nesting import RunNestingCommand

import FreeCAD  # type: ignore


def _write_test_csv(path):
    header = ["id", "width", "height", "qty", "allow_rotate"]
    rows = [
        {"id": "P1", "width": "100", "height": "200", "qty": "1", "allow_rotate": "yes"},
        {"id": "P2", "width": "800", "height": "500", "qty": "1", "allow_rotate": "yes"},
        {"id": "P3", "width": "150", "height": "150", "qty": "1", "allow_rotate": "yes"},
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_oversize_part_fits_after_rotation(tmp_path):
    session_state.set_panels([])
    session_state.set_sheet_size(609.6, 1219.2)
    session_state.set_gap_mm(0.0)
    doc_name = "TestNestingRegression"
    try:
        FreeCAD.closeDocument(doc_name)
    except Exception:
        pass
    doc = FreeCAD.newDocument(doc_name)
    csv_path = tmp_path / "regression.csv"
    _write_test_csv(csv_path)
    run_csv_import(doc, str(csv_path), csv_units="metric")
    cmd = RunNestingCommand()
    cmd.Activated()
    assert cmd.validation_error is None
    # Ensure nested group exists
    nested_group = doc.getObject("SquatchCut_NestedParts")
    assert nested_group is not None
    nested_children = getattr(nested_group, "Group", []) or []
    assert nested_children
    layout = session_state.get_last_layout()
    assert layout
    try:
        FreeCAD.closeDocument(doc.Name)
    except Exception:
        pass
