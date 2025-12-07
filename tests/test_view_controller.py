from SquatchCut.core import view_controller


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
