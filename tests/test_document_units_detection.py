from SquatchCut.core import session
from SquatchCut.core.preferences import SquatchCutPreferences


class DummyDoc:
    def __init__(self, metadata=None):
        self.Metadata = metadata
        self.Meta = None
        self.DocumentMetadata = None
        self.SquatchCutSheetUnits = None


def _snapshot_prefs(prefs: SquatchCutPreferences) -> str:
    return prefs.get_measurement_system()


def _restore_prefs(prefs: SquatchCutPreferences, value: str) -> None:
    prefs.set_measurement_system(value)


def test_detect_document_measurement_system_missing_metadata_uses_default():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("metric")
        doc = DummyDoc()
        result = session.detect_document_measurement_system(doc)
        assert result == "metric"
    finally:
        _restore_prefs(prefs, snap)


def test_detect_document_measurement_system_handles_metric():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("imperial")
        doc = DummyDoc(metadata={"UnitSystem": "Metric"})
        result = session.detect_document_measurement_system(doc)
        assert result == "metric"
    finally:
        _restore_prefs(prefs, snap)


def test_detect_document_measurement_system_handles_imperial():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("metric")
        doc = DummyDoc(metadata={"UnitSchema": "Imperial (in)"})
        result = session.detect_document_measurement_system(doc)
        assert result == "imperial"
    finally:
        _restore_prefs(prefs, snap)


def test_detect_document_measurement_system_handles_garbage():
    prefs = SquatchCutPreferences()
    snap = _snapshot_prefs(prefs)
    try:
        prefs.set_measurement_system("imperial")
        doc = DummyDoc(metadata={"UnitSystem": "unknown"})
        result = session.detect_document_measurement_system(doc)
        assert result == "metric"
    finally:
        _restore_prefs(prefs, snap)
