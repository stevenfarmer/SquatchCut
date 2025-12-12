import pytest

pytest.importorskip("FreeCAD")
import FreeCAD  # type: ignore
from SquatchCut.core.sheet_model import SHEET_OBJECT_NAME, ensure_sheet_object


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


def test_ensure_sheet_object_creates_once():
    doc = _new_doc("TestSheetModelCreate")
    sheet = ensure_sheet_object(100.0, 200.0, doc)
    assert sheet is not None
    assert sheet.Name == SHEET_OBJECT_NAME
    assert sheet.Shape.BoundBox.XLength == pytest.approx(100.0)
    assert sheet.Shape.BoundBox.YLength == pytest.approx(200.0)
    _close_doc(doc)


def test_ensure_sheet_object_updates_in_place():
    doc = _new_doc("TestSheetModelUpdate")
    first = ensure_sheet_object(120.0, 240.0, doc)
    second = ensure_sheet_object(300.0, 150.0, doc)
    assert first is second
    sheets = [o for o in getattr(doc, "Objects", []) if o.Name == SHEET_OBJECT_NAME]
    assert len(sheets) == 1
    assert second.Shape.BoundBox.XLength == pytest.approx(300.0)
    assert second.Shape.BoundBox.YLength == pytest.approx(150.0)
    _close_doc(doc)
