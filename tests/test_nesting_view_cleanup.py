from SquatchCut.gui.nesting_view import _build_source_map, _safe_object_name


class _StubObject:
    def __init__(self, name, deleted=False):
        self._name = name
        self._deleted = deleted

    @property
    def Name(self):
        if self._deleted:
            raise ReferenceError("Object deleted")
        return self._name


class _DocStub:
    def __init__(self):
        self._objects = {}

    def getObject(self, name):
        return self._objects.get(name)

    def register_group(self, name, members):
        group = type("Group", (), {"Group": list(members)})
        self._objects[name] = group
        return group


def test_safe_object_name_handles_reference_error():
    obj = _StubObject("valid")
    assert _safe_object_name(obj) == "valid"
    deleted = _StubObject("gone", deleted=True)
    assert _safe_object_name(deleted) == ""


def test_build_source_map_skips_deleted_objects():
    doc = _DocStub()
    doc.register_group("SquatchCut_SourceParts", [_StubObject("A"), _StubObject("B", deleted=True)])
    source_map = _build_source_map([_StubObject("C"), _StubObject("D", deleted=True)], doc)
    assert "A" in source_map
    assert "C" in source_map
    assert "B" not in source_map
    assert "D" not in source_map
