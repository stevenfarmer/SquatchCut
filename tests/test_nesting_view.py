import pytest

pytest.importorskip("FreeCAD")
import FreeCAD  # type: ignore
from SquatchCut.core.nesting import PlacedPart
from SquatchCut.gui.nesting_view import NESTED_GROUP_NAME, rebuild_nested_geometry


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


def test_rebuild_nested_geometry_creates_group_and_children():
    doc = _new_doc("TestNestedView")
    placements = [
        PlacedPart(id="P1", sheet_index=0, x=0.0, y=0.0, width=100.0, height=50.0, rotation_deg=0),
        PlacedPart(id="P2", sheet_index=0, x=120.0, y=0.0, width=80.0, height=60.0, rotation_deg=90),
    ]

    group, objs = rebuild_nested_geometry(
        doc,
        placements,
        sheet_sizes=[(300.0, 150.0)],
    )

    assert group is not None
    assert group.Name == NESTED_GROUP_NAME
    assert len(objs) == 2
    assert all(o in getattr(group, "Group", []) for o in objs)

    _close_doc(doc)


def test_rebuild_nested_geometry_skips_deleted_source_objects():
    doc = _new_doc("TestNestedDeleted")
    src = doc.addObject("Part::Box", "P_del")
    doc.recompute()
    placements = [
        PlacedPart(id="P_del", sheet_index=0, x=10.0, y=5.0, width=40.0, height=20.0, rotation_deg=0),
    ]
    doc.removeObject("P_del")

    group, objs = rebuild_nested_geometry(
        doc,
        placements,
        sheet_sizes=[(200.0, 100.0)],
        source_objects=[src],
    )

    assert group is not None
    assert len(objs) == 1
    _close_doc(doc)
