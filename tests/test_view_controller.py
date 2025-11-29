from SquatchCut.core import session, session_state, view_controller
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


def _cleanup_state():
    session.clear_all_geometry()
    session_state.set_nested_sheet_group(None)


def test_show_source_view_sets_visibility(monkeypatch):
    doc = DummyDoc()
    source = DummyObject("SourceOne")
    sheet = DummyObject(SHEET_OBJECT_NAME)
    nested = DummyObject("SC_Nested_old")
    source_group = DummyGroup(view_controller.SOURCE_GROUP_NAME, members=[source])
    nested_group = DummyGroup(view_controller.NESTED_GROUP_NAME, members=[nested])

    doc._objects[source_group.Name] = source_group
    doc._objects[nested_group.Name] = nested_group
    doc._objects[source.Name] = source
    doc._objects[sheet.Name] = sheet
    doc._objects[nested.Name] = nested

    session.set_source_panel_objects([source])
    session.set_sheet_objects([sheet])
    session.set_nested_panel_objects([nested])
    session_state.set_nested_sheet_group(nested_group)

    fit_targets = []
    monkeypatch.setattr(view_controller, "zoom_to_objects", lambda objs: fit_targets.append(list(objs)))

    view_controller.show_source_view(doc)

    assert source.ViewObject.Visibility is True
    assert sheet.ViewObject.Visibility is False
    assert nested.ViewObject.Visibility is False
    assert fit_targets == [[source]]

    _cleanup_state()


def test_show_nesting_view_hides_sources(monkeypatch):
    doc = DummyDoc()
    source = DummyObject("SourceTwo")
    sheet = DummyObject(SHEET_OBJECT_NAME)
    nested = DummyObject("SC_Nested_new")
    nested_group = DummyGroup(view_controller.NESTED_GROUP_NAME, members=[nested])

    doc._objects[source.Name] = source
    doc._objects[sheet.Name] = sheet
    doc._objects[nested_group.Name] = nested_group
    doc._objects[nested.Name] = nested

    session.set_source_panel_objects([source])
    session.set_sheet_objects([sheet])
    session.set_nested_panel_objects([nested])
    session_state.set_nested_sheet_group(nested_group)

    fit_targets = []
    monkeypatch.setattr(view_controller, "zoom_to_objects", lambda objs: fit_targets.append(list(objs)))

    view_controller.show_nesting_view(doc, active_sheet=sheet)

    assert source.ViewObject.Visibility is False
    assert sheet.ViewObject.Visibility is True
    assert nested.ViewObject.Visibility is True
    assert fit_targets == [[sheet, nested]]

    _cleanup_state()


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

    _cleanup_state()
