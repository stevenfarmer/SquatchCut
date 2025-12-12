import pytest

pytest.importorskip("FreeCAD")
from SquatchCut.core import session_state
from SquatchCut.core.geometry_sync import ensure_sheet_object

import FreeCAD  # type: ignore


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


def test_ensure_sheet_object_creates_when_missing():
    doc = _new_doc("TestSheetCreate")
    session_state.set_sheet_size(100.0, 200.0)

    sheet = ensure_sheet_object(doc)

    assert sheet is not None
    assert sheet.Name == "SquatchCut_Sheet"
    bbox = sheet.Shape.BoundBox
    assert bbox.XLength == pytest.approx(100.0)
    assert bbox.YLength == pytest.approx(200.0)
    _close_doc(doc)


def test_ensure_sheet_object_updates_existing():
    doc = _new_doc("TestSheetUpdate")
    session_state.set_sheet_size(120.0, 240.0)
    first = ensure_sheet_object(doc)

    session_state.set_sheet_size(300.0, 150.0)
    second = ensure_sheet_object(doc)

    assert first is second
    sheets = [o for o in getattr(doc, "Objects", []) if o.Name == "SquatchCut_Sheet"]
    assert len(sheets) == 1
    bbox = second.Shape.BoundBox
    assert bbox.XLength == pytest.approx(300.0)
    assert bbox.YLength == pytest.approx(150.0)
    _close_doc(doc)
