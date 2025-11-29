class DummyView:
    def __init__(self):
        self.Visibility = False


class DummyObject:
    def __init__(self, name):
        self.Name = name
        self.ViewObject = DummyView()
        self.Group = []


class DummyDoc:
    def __init__(self, objects=None):
        self._objects = {obj.Name: obj for obj in (objects or [])}

    @property
    def Objects(self):
        return list(self._objects.values())

    def getObject(self, name):
        return self._objects.get(name)

    def addObject(self, obj):
        self._objects[obj.Name] = obj


def _build_doc():
    sheet = DummyObject("SquatchCut_Sheet")
    source_group = DummyObject("SquatchCut_SourceParts")
    nested_group = DummyObject("SquatchCut_NestedParts")
    # add child objects
    child_source = DummyObject("SC_Source_A")
    child_nested = DummyObject("SC_Nested_A")
    source_group.Group = [child_source]
    nested_group.Group = [child_nested]
    others = [sheet, source_group, nested_group, child_source, child_nested]
    return DummyDoc(others)


def test_show_sheet_only():
    from SquatchCut.gui.view_helpers import show_sheet_only

    doc = _build_doc()
    show_sheet_only(doc)
    sheet = doc.getObject("SquatchCut_Sheet")
    assert sheet.ViewObject.Visibility is True
    assert doc.getObject("SC_Source_A").ViewObject.Visibility is False
    assert doc.getObject("SC_Nested_A").ViewObject.Visibility is False


def test_show_source_and_sheet():
    from SquatchCut.gui.view_helpers import show_source_and_sheet

    doc = _build_doc()
    show_source_and_sheet(doc)
    assert doc.getObject("SquatchCut_Sheet").ViewObject.Visibility is True
    assert doc.getObject("SC_Source_A").ViewObject.Visibility is True
    assert doc.getObject("SC_Nested_A").ViewObject.Visibility is False


def test_show_nested_only():
    from SquatchCut.gui.view_helpers import show_nested_only

    doc = _build_doc()
    show_nested_only(doc)
    assert doc.getObject("SquatchCut_Sheet").ViewObject.Visibility is True
    assert doc.getObject("SC_Source_A").ViewObject.Visibility is False
    assert doc.getObject("SC_Nested_A").ViewObject.Visibility is True
