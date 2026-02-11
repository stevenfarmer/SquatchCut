# ruff: noqa: E402
import uuid

import pytest

FreeCAD = pytest.importorskip("FreeCAD")  # type: ignore
Part = pytest.importorskip("Part")  # type: ignore

from SquatchCut.core import session, session_state, view_controller
from SquatchCut.core.sheet_model import ensure_sheet_object


class _DummyPlacement:
    def __init__(self, part_id, width, height, x=0.0, y=0.0, sheet_index=0, rotation_deg=0.0):
        self.id = part_id
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.sheet_index = sheet_index
        self.rotation_deg = rotation_deg


def _reset_state():
    session.clear_all_geometry()
    session_state.clear_panels()
    session_state.set_last_layout(None)
    session_state.set_nested_sheet_group(None)
    session_state.set_source_panel_objects([])
    session_state.set_sheet_size(200.0, 100.0)


def _new_doc():
    name = f"Hybrid_{uuid.uuid4().hex[:8]}"
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


def _prepare_document():
    _reset_state()
    doc = _new_doc()
    sheet = ensure_sheet_object(200.0, 100.0, doc)
    source_group = doc.addObject("App::DocumentObjectGroup", "SquatchCut_SourceParts")
    source_child = doc.addObject("Part::Box", "SC_Source_Seed")
    source_group.addObject(source_child)
    nested_group = doc.addObject("App::DocumentObjectGroup", "SquatchCut_NestedParts")
    nested_child = doc.addObject("Part::Box", "SC_Nested_Seed")
    nested_group.addObject(nested_child)
    for obj in (sheet, source_group, nested_group, source_child, nested_child):
        try:
            obj.ViewObject.Visibility = True
        except Exception:
            pass
    try:
        doc.recompute()
    except Exception:
        pass
    return doc, sheet, source_group, nested_group, source_child, nested_child


def _visible(obj):
    view = getattr(obj, "ViewObject", None)
    return None if view is None else bool(view.Visibility)


def _assert_visibility(obj, expected):
    vis = _visible(obj)
    if vis is not None:
        assert vis is expected


def test_sheet_view_hybrid_mode():
    doc, sheet, source_group, nested_group, source_child, nested_child = _prepare_document()
    source_child_name = source_child.Name
    nested_child_name = nested_child.Name
    try:
        original_source_children = [obj.Name for obj in source_group.Group]
        original_nested_children = [obj.Name for obj in nested_group.Group]
        session_state.set_sheet_size(320.0, 160.0)

        view_controller.show_sheet_view(doc)

        sheet_obj = doc.getObject("SquatchCut_Sheet")
        assert sheet_obj is not None
        bbox = sheet_obj.Shape.BoundBox
        positive_lengths = sorted(length for length in (bbox.XLength, bbox.YLength, bbox.ZLength) if length > 0)
        assert positive_lengths == pytest.approx(sorted([320.0, 160.0]))
        assert [obj.Name for obj in source_group.Group] == original_source_children
        assert [obj.Name for obj in nested_group.Group] == original_nested_children
        _assert_visibility(sheet_obj, True)
        _assert_visibility(source_group, False)
        _assert_visibility(nested_group, False)
        assert doc.getObject(source_child_name) is not None
        assert doc.getObject(nested_child_name) is not None
    finally:
        _close_doc(doc)


def test_source_view_hybrid_mode():
    doc, sheet, source_group, nested_group, source_child, nested_child = _prepare_document()
    source_child_name = source_child.Name
    nested_child_name = nested_child.Name
    try:
        session.set_panels([{"id": "P1", "width": 40.0, "height": 20.0}])

        view_controller.show_source_view(doc)

        new_children = [obj.Name for obj in source_group.Group]
        assert source_child_name not in new_children
        assert doc.getObject(source_child_name) is None
        assert new_children, "source group should contain regenerated children"
        _assert_visibility(source_group, True)
        _assert_visibility(sheet, False)
        _assert_visibility(nested_group, False)
        assert doc.getObject(nested_child_name) is not None
    finally:
        _close_doc(doc)


def test_nesting_view_hybrid_mode():
    doc, sheet, source_group, nested_group, source_child, nested_child = _prepare_document()
    source_child_name = source_child.Name
    nested_child_name = nested_child.Name
    try:
        placements = [
            _DummyPlacement("P1", 30.0, 15.0, x=5.0, y=5.0, sheet_index=0, rotation_deg=0.0),
            _DummyPlacement("P2", 25.0, 10.0, x=40.0, y=5.0, sheet_index=0, rotation_deg=90.0),
        ]
        session_state.set_last_layout(placements)

        view_controller.show_nesting_view(doc)

        new_nested_children = [obj.Name for obj in nested_group.Group]
        assert nested_child_name not in new_nested_children
        assert doc.getObject(nested_child_name) is None
        assert new_nested_children, "nested group should be rebuilt with placements"
        _assert_visibility(nested_group, True)
        _assert_visibility(source_group, False)
        sheet_obj = doc.getObject("SquatchCut_Sheet")
        _assert_visibility(sheet_obj, False)
        assert doc.getObject(source_child_name) is not None
    finally:
        _close_doc(doc)


def test_view_switch_sequence_preserves_all_groups():
    doc, sheet, source_group, nested_group, _, _ = _prepare_document()
    try:
        session.set_panels([{"id": "P1", "width": 40.0, "height": 20.0}])
        session_state.set_last_layout([_DummyPlacement("P1", 40.0, 20.0)])

        view_controller.show_sheet_view(doc)
        view_controller.show_source_view(doc)
        view_controller.show_nesting_view(doc)

        sheet_obj = doc.getObject("SquatchCut_Sheet")
        source_group_obj = doc.getObject("SquatchCut_SourceParts")
        nested_group_obj = doc.getObject("SquatchCut_NestedParts")
        assert sheet_obj is not None
        assert source_group_obj is not None
        assert nested_group_obj is not None
        assert len(source_group_obj.Group) > 0
        assert len(nested_group_obj.Group) > 0
        _assert_visibility(sheet_obj, False)
        _assert_visibility(source_group_obj, False)
        _assert_visibility(nested_group_obj, True)
        sc_named = {obj.Name for obj in getattr(doc, "Objects", []) if obj.Name.startswith("SquatchCut_")}
        expected = {"SquatchCut_Sheet", "SquatchCut_SourceParts", "SquatchCut_NestedParts"}
        assert sc_named <= expected
    finally:
        _close_doc(doc)
