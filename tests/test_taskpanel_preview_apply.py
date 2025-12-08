from __future__ import annotations

import types

import pytest

from SquatchCut.core import session, session_state
from SquatchCut.gui import taskpanel_main as taskpanel_module
from SquatchCut.gui.commands import cmd_run_nesting
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel


class DummyObject:
    def __init__(self, name, doc):
        self.Name = name
        self.Document = doc


class DummyGroup(DummyObject):
    def __init__(self, name, doc):
        super().__init__(name, doc)
        self.Group: list[DummyObject] = []

    def addObject(self, obj):
        if obj not in self.Group:
            self.Group.append(obj)


class DummyDoc:
    def __init__(self):
        self._objects: dict[str, DummyObject] = {}
        self.removed: list[str] = []

    def getObject(self, name):
        return self._objects.get(name)

    @property
    def Objects(self):
        return list(self._objects.values())

    def addObject(self, obj_type, name):
        if name in self._objects:
            self.removeObject(name)
        if obj_type == "App::DocumentObjectGroup":
            obj = DummyGroup(name, self)
        else:
            obj = DummyObject(name, self)
        self._objects[name] = obj
        return obj

    def removeObject(self, name):
        obj = self._objects.pop(name, None)
        if obj is None:
            return
        self.removed.append(name)
        for other in self._objects.values():
            group = getattr(other, "Group", None)
            if isinstance(group, list):
                other.Group = [child for child in group if getattr(child, "Name", None) != name]

    def recompute(self):
        return None

    def object_names(self):
        return list(self._objects.keys())


def _ensure_group_with_child(doc, group_name, child_name):
    group = doc.getObject(group_name)
    if group is None:
        group = doc.addObject("App::DocumentObjectGroup", group_name)
    members = list(getattr(group, "Group", []) or [])
    for member in members:
        doc.removeObject(member.Name)
    group.Group = []
    child = doc.addObject("Part::Feature", child_name)
    group.addObject(child)
    return group


class DummyRunCommand:
    def __init__(self):
        self.validation_error = None

    def Activated(self):
        doc = cmd_run_nesting.App.ActiveDocument
        if doc is None:
            raise RuntimeError("DummyRunCommand requires an active document.")
        _ensure_group_with_child(doc, "SquatchCut_SourceParts", "SC_Source_item")
        _ensure_group_with_child(doc, "SquatchCut_NestedParts", "SC_Nested_part")
        doc.addObject("Part::Feature", "SquatchCut_Sheet")
        doc.addObject("Part::Feature", "SquatchCut_Sheet_1")
        session_state.set_last_layout([{"id": "demo"}])
        session_state.set_nesting_stats(1, None, 0)


@pytest.fixture(autouse=True)
def _reset_session_state():
    session_state.set_measurement_system("metric")
    session_state.set_last_layout([])
    session_state.set_nesting_stats(None, None, 0)
    session.clear_all_geometry()
    yield
    session_state.set_last_layout([])
    session_state.set_nesting_stats(None, None, 0)
    session.clear_all_geometry()


@pytest.fixture(autouse=True)
def _patch_run_command(monkeypatch):
    monkeypatch.setattr(cmd_run_nesting, "RunNestingCommand", DummyRunCommand)


def _create_panel(monkeypatch):
    doc = DummyDoc()
    app_stub = types.SimpleNamespace(ActiveDocument=doc, newDocument=lambda _name: doc)
    gui_stub = types.SimpleNamespace(Control=types.SimpleNamespace(closeDialog=lambda: None))
    monkeypatch.setattr(cmd_run_nesting, "App", app_stub)
    monkeypatch.setattr(cmd_run_nesting, "Gui", gui_stub)
    monkeypatch.setattr(taskpanel_module, "App", app_stub)
    monkeypatch.setattr(taskpanel_module, "Gui", gui_stub)

    panel = SquatchCutTaskPanel.__new__(SquatchCutTaskPanel)
    panel.doc = doc
    panel.measurement_system = "metric"
    panel._apply_settings_to_session = lambda: None
    panel._ensure_shapes_exist = lambda _doc: None
    panel._refresh_summary = lambda: None
    panel.update_run_button_state = lambda: None
    panel.set_status = lambda _msg: None
    panel._set_run_buttons_enabled = lambda _flag: None
    panel.status_label = types.SimpleNamespace(setText=lambda _text: None, setStyleSheet=lambda _style: None)
    return panel, doc, app_stub


def _collect_prefixed_names(doc, prefix):
    return sorted(name for name in doc.object_names() if name.startswith(prefix))


def _snapshot(doc):
    nested = doc.getObject("SquatchCut_NestedParts")
    source = doc.getObject("SquatchCut_SourceParts")
    return {
        "names": sorted(doc.object_names()),
        "nested_children": sorted(
            getattr(child, "Name", "")
            for child in (getattr(nested, "Group", []) or [])
        ),
        "source_children": sorted(
            getattr(child, "Name", "")
            for child in (getattr(source, "Group", []) or [])
        ),
    }


def _run_preview(panel, app_stub):
    app_stub.ActiveDocument = panel.doc
    assert panel._run_preview_nesting()


def _run_apply(panel, app_stub):
    app_stub.ActiveDocument = panel.doc
    assert panel._run_apply_nesting()


def test_preview_run_builds_canonical_groups(monkeypatch):
    panel, doc, app_stub = _create_panel(monkeypatch)
    _run_preview(panel, app_stub)
    assert doc.getObject("SquatchCut_NestedParts") is not None
    assert doc.getObject("SquatchCut_SourceParts") is not None
    assert _collect_prefixed_names(doc, "SquatchCut_Sheet") == ["SquatchCut_Sheet", "SquatchCut_Sheet_1"]
    nested_children = _collect_prefixed_names(doc, "SC_Nested_")
    assert nested_children == ["SC_Nested_part"]
    assert session_state.get_measurement_system() == "metric"


def test_preview_twice_removes_old_geometry(monkeypatch):
    panel, doc, app_stub = _create_panel(monkeypatch)
    _run_preview(panel, app_stub)
    first_snapshot = _snapshot(doc)
    _run_preview(panel, app_stub)
    second_snapshot = _snapshot(doc)
    assert first_snapshot == second_snapshot
    assert _collect_prefixed_names(doc, "SC_Nested_") == ["SC_Nested_part"]


def test_preview_then_apply_clears_preview_artifacts(monkeypatch):
    panel, doc, app_stub = _create_panel(monkeypatch)
    _run_preview(panel, app_stub)
    assert "SquatchCut_NestedParts" in _snapshot(doc)["names"]
    _run_apply(panel, app_stub)
    snap = _snapshot(doc)
    assert snap["nested_children"] == ["SC_Nested_part"]
    assert snap["names"].count("SquatchCut_NestedParts") == 1
    assert _collect_prefixed_names(doc, "SquatchCut_Sheet") == ["SquatchCut_Sheet", "SquatchCut_Sheet_1"]


def test_apply_without_preview_matches_preview_then_apply(monkeypatch):
    panel_preview, doc_preview, app_stub_preview = _create_panel(monkeypatch)
    _run_preview(panel_preview, app_stub_preview)
    _run_apply(panel_preview, app_stub_preview)
    preview_snapshot = _snapshot(doc_preview)

    session_state.set_last_layout([])
    session_state.set_nesting_stats(None, None, 0)
    session.clear_all_geometry()

    panel_apply, doc_apply, app_stub_apply = _create_panel(monkeypatch)
    _run_apply(panel_apply, app_stub_apply)
    apply_snapshot = _snapshot(doc_apply)

    assert preview_snapshot == apply_snapshot
