from SquatchCut.core import view_controller
from SquatchCut.core.sheet_model import SHEET_OBJECT_NAME


class DummyView:
    def __init__(self):
        self.Visibility = None


class DummyObject:
    def __init__(self, name):
        self.Name = name
        self.ViewObject = DummyView()


class DummyGroup(DummyObject):
    def __init__(self, name, members=None):
        super().__init__(name)
        self.Group = list(members or [])


class DummyDoc:
    def __init__(self):
        self._objects = {}
        self.removed = []

    def getObject(self, name):
        return self._objects.get(name)

    @property
    def Objects(self):
        return list(self._objects.values())

    def removeObject(self, name):
        if name in self._objects:
            self.removed.append(name)
            del self._objects[name]


def _build_doc_with_standard_groups():
    doc = DummyDoc()
    sheet = DummyObject(SHEET_OBJECT_NAME)
    source_member = DummyObject("SourceMember")
    nested_member = DummyObject("NestedMember")
    source = DummyGroup(view_controller.SOURCE_GROUP_NAME, members=[source_member])
    nested = DummyGroup(view_controller.NESTED_GROUP_NAME, members=[nested_member])
    doc._objects[sheet.Name] = sheet
    doc._objects[source.Name] = source
    doc._objects[nested.Name] = nested
    return doc, sheet, source, nested


def test_show_source_view_sets_visibility_and_zoom(monkeypatch):
    doc, sheet, source, nested = _build_doc_with_standard_groups()
    zoom_calls = []

    monkeypatch.setattr(view_controller, "_resolve_doc", lambda _doc=None: doc)
    monkeypatch.setattr(view_controller, "_resolve_view", lambda: "source-view")
    monkeypatch.setattr(
        view_controller,
        "_redraw_source_group",
        lambda resolved_doc: (source, list(source.Group)),
    )
    monkeypatch.setattr(
        view_controller,
        "auto_zoom_to_group",
        lambda view, group: zoom_calls.append((view, group)),
    )

    view_controller.show_source_view(doc)

    assert source.ViewObject.Visibility is True
    assert source.Group[0].ViewObject.Visibility is True
    assert sheet.ViewObject.Visibility is False
    assert nested.ViewObject.Visibility is False
    assert zoom_calls == [("source-view", source)]


def test_show_nesting_view_hides_sources(monkeypatch):
    doc, sheet, source, nested = _build_doc_with_standard_groups()
    zoom_calls = []

    monkeypatch.setattr(view_controller, "_resolve_doc", lambda _doc=None: doc)
    monkeypatch.setattr(view_controller, "_resolve_view", lambda: "nested-view")
    monkeypatch.setattr(
        view_controller,
        "_redraw_nested_group",
        lambda resolved_doc: (nested, list(nested.Group)),
    )
    monkeypatch.setattr(
        view_controller,
        "auto_zoom_to_group",
        lambda view, group: zoom_calls.append((view, group)),
    )

    view_controller.show_nesting_view(doc)

    assert nested.ViewObject.Visibility is True
    assert nested.Group[0].ViewObject.Visibility is True
    assert sheet.ViewObject.Visibility is False
    assert source.ViewObject.Visibility is False
    assert zoom_calls == [("nested-view", nested)]


def test_cleanup_nested_layout_removes_old_objects():
    doc = DummyDoc()
    legacy_child = DummyObject("LegacyChild")
    legacy_group = DummyGroup(view_controller.LEGACY_SHEET_GROUP_NAME, members=[legacy_child])
    nested_obj = DummyObject("SC_Nested_ghost")
    nested_group = DummyGroup(view_controller.NESTED_GROUP_NAME, members=[nested_obj])
    stray = DummyObject("SC_Nested_stray")

    doc._objects[legacy_group.Name] = legacy_group
    doc._objects[legacy_child.Name] = legacy_child
    doc._objects[nested_group.Name] = nested_group
    doc._objects[nested_obj.Name] = nested_obj
    doc._objects[stray.Name] = stray

    view_controller.cleanup_nested_layout(doc)

    assert legacy_group.Name in doc.removed
    assert nested_group.Name in doc.removed
    assert nested_obj.Name in doc.removed
    assert stray.Name in doc.removed
