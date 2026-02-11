from SquatchCut.core import session
from SquatchCut.gui.commands.cmd_run_nesting import RunNestingCommand


class DummyObject:
    def __init__(self, name):
        self.Name = name
        self.Group = []


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

    def addObject(self, _type, name):
        obj = DummyGroup(name) if name.startswith("SquatchCut_") else DummyObject(name)
        self._objects[name] = obj
        return obj


def _create_run_geometry(doc, child_suffix):
    sheet = doc.addObject("App::DocumentObjectGroup", session.SHEET_OBJECT_NAME)
    source = doc.addObject("App::DocumentObjectGroup", session.SOURCE_GROUP_NAME)
    nested = doc.addObject("App::DocumentObjectGroup", session.NESTED_GROUP_NAME)
    child = DummyObject(f"{session.NESTED_PREFIX}{child_suffix}")
    doc._objects[child.Name] = child
    nested.Group.append(child)
    return sheet, source, nested


def test_clear_all_squatchcut_geometry_removes_every_group():
    doc = DummyDoc()
    doc._objects[session.SHEET_OBJECT_NAME] = DummyObject(session.SHEET_OBJECT_NAME)
    doc._objects["SheetChild"] = DummyObject("SheetChild")
    doc._objects[session.SOURCE_GROUP_NAME] = DummyGroup(session.SOURCE_GROUP_NAME, members=[DummyObject("SourceChild")])
    doc._objects[session.NESTED_GROUP_NAME] = DummyGroup(session.NESTED_GROUP_NAME, members=[DummyObject("NestedChild")])
    doc._objects[f"{session.SOURCE_PREFIX}foo"] = DummyObject(f"{session.SOURCE_PREFIX}foo")
    doc._objects[f"{session.NESTED_PREFIX}bar"] = DummyObject(f"{session.NESTED_PREFIX}bar")

    session.clear_all_squatchcut_geometry(doc)

    assert doc.getObject(session.SHEET_OBJECT_NAME) is None
    assert doc.getObject(session.SOURCE_GROUP_NAME) is None
    assert doc.getObject(session.NESTED_GROUP_NAME) is None
    assert all(not name.startswith(session.SOURCE_PREFIX) for name in doc.removed) or any(
        name.startswith(session.SOURCE_PREFIX) for name in doc.removed
    )
    assert any(name.startswith(session.NESTED_PREFIX) for name in doc.removed)


def test_cleanup_runs_leave_single_group_each_time():
    doc = DummyDoc()

    _create_run_geometry(doc, "first")
    assert doc.getObject(session.SHEET_OBJECT_NAME) is not None
    assert doc.getObject(session.SOURCE_GROUP_NAME) is not None
    assert doc.getObject(session.NESTED_GROUP_NAME) is not None

    session.clear_all_squatchcut_geometry(doc)
    assert doc.getObject(session.SHEET_OBJECT_NAME) is None
    assert doc.getObject(session.SOURCE_GROUP_NAME) is None
    assert doc.getObject(session.NESTED_GROUP_NAME) is None

    _create_run_geometry(doc, "second")
    assert doc.getObject(session.SHEET_OBJECT_NAME) is not None
    assert doc.getObject(session.SOURCE_GROUP_NAME) is not None
    nested = doc.getObject(session.NESTED_GROUP_NAME)
    assert nested is not None
    assert len(nested.Group) == 1


def test_clear_nested_layout_preserves_sources():
    doc = DummyDoc()
    sheet = DummyObject(session.SHEET_OBJECT_NAME)
    source_child = DummyObject("SourceChild")
    source_group = DummyGroup(session.SOURCE_GROUP_NAME, members=[source_child])
    nested = DummyGroup(session.NESTED_GROUP_NAME, members=[DummyObject("NestedChild")])
    doc._objects[sheet.Name] = sheet
    doc._objects[source_group.Name] = source_group
    doc._objects[nested.Name] = nested

    session.clear_nested_layout(doc)

    assert doc.getObject(session.SHEET_OBJECT_NAME) is None
    assert doc.getObject(session.NESTED_GROUP_NAME) is None
    remaining_source = doc.getObject(session.SOURCE_GROUP_NAME)
    assert remaining_source is source_group
    assert remaining_source.Group == [source_child]


class DeletedDummy:
    def __init__(self, name):
        self._name = name

    @property
    def Name(self):
        raise ReferenceError("deleted object")


def test_resolve_live_source_objects_prefers_doc_group():
    doc = DummyDoc()
    group_obj = DummyGroup(session.SOURCE_GROUP_NAME, members=[DummyObject("P1"), DummyObject("P2")])
    doc._objects[group_obj.Name] = group_obj
    cmd = RunNestingCommand()
    live = cmd._resolve_live_source_objects(doc, [])
    assert [obj.Name for obj in live] == ["P1", "P2"]


def test_resolve_live_source_objects_fallback_with_deleted_handles():
    doc = DummyDoc()
    stale = DeletedDummy("StaleP3")
    cmd = RunNestingCommand()
    live = cmd._resolve_live_source_objects(doc, [stale])
    assert live == []


def test_resolve_live_source_objects_reuses_fallback_when_doc_empty():
    doc = DummyDoc()
    fallback = DummyObject("P4")
    cmd = RunNestingCommand()
    live = cmd._resolve_live_source_objects(doc, [fallback])
    assert live == [fallback]
