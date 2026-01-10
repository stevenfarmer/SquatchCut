"""GUI workflow coverage for user-facing paths."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from SquatchCut.core import session_state
from SquatchCut.gui.taskpanel_input import InputGroupWidget
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel
from SquatchCut.gui.taskpanel_sheet import SheetConfigWidget


def _stub_settings_module():
    """Return a lightweight stub for SquatchCut.settings."""

    class _StubSettings:
        @staticmethod
        def hydrate_from_params(measurement_override=None):
            return None

    return _StubSettings()


def test_csv_workflow_ready_status_enables_run_button():
    """CSV flow: import -> sheet valid -> run button enabled and status ready."""
    session_state.set_measurement_system("metric")
    session_state.set_panels([])
    session_state.set_sheet_size(1200.0, 2400.0)
    session_state.set_gap_mm(2.0)
    session_state.set_kerf_mm(3.0)

    with patch(
        "SquatchCut.core.session.detect_document_measurement_system",
        return_value="metric",
    ), patch("SquatchCut.gui.taskpanel_main.settings", _stub_settings_module()):
        panel = SquatchCutTaskPanel()

    session_state.set_panels([{"id": "p1", "width": 100, "height": 200}])
    panel._on_data_changed()
    panel._on_sheet_validation_changed(True)

    assert panel.nesting_widget.run_button.isEnabled()
    assert panel.nesting_widget.preview_button.isEnabled()
    assert panel.status_label.text().endswith("Ready.")
    session_state.set_panels([])


def test_shape_selection_flow_sets_panels_and_status(monkeypatch):
    """Shape-based flow: selecting shapes updates panels and status."""
    session_state.set_panels([])

    # Fake FreeCAD document with Shape-bearing objects
    shape_obj = SimpleNamespace(Label="ShapeA", Shape=SimpleNamespace(BoundBox=SimpleNamespace(ZLength=12.0)))
    dummy_doc = SimpleNamespace(Objects=[shape_obj])
    monkeypatch.setattr(
        "SquatchCut.gui.taskpanel_input.App",
        SimpleNamespace(ActiveDocument=dummy_doc),
    )

    # Stub QApplication/processEvents used in shape loop
    class _DummyApp:
        @staticmethod
        def processEvents():
            return None

    monkeypatch.setattr(
        "SquatchCut.gui.taskpanel_input.QtWidgets.QApplication",
        _DummyApp,
    )

    # Stub progress dialog context manager
    class _DummyProgress:
        def __init__(self, *_, **__):
            self._label = ""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_range(self, *_):
            return None

        def set_label(self, text):
            self._label = text

        def set_value(self, *_):
            return None

        def set_text(self, text):
            self._label = text

    monkeypatch.setattr("SquatchCut.gui.taskpanel_input.ProgressDialog", _DummyProgress)

    # Stub extractor to avoid real geometry work
    class _DummyGeometry:
        geometry_type = "complex"
        complexity_level = "medium"
        area = 123.0

        @staticmethod
        def get_width():
            return 400.0

        @staticmethod
        def get_height():
            return 200.0

    monkeypatch.setattr(
        "SquatchCut.gui.taskpanel_input.ShapeExtractor",
        MagicMock(return_value=MagicMock(extract_with_fallback=lambda obj: (_DummyGeometry(), "fallback", None))),
    )

    widget = InputGroupWidget(prefs=MagicMock())
    widget.shapes_selected.emit = MagicMock()

    widget._select_shapes()

    panels = session_state.get_panels()
    assert len(panels) == 1
    assert panels[0]["source"] == "freecad_shape"
    assert panels[0]["width"] == 400.0
    assert "shapes selected" in widget.csv_path_label.text().lower()
    widget.shapes_selected.emit.assert_called_once()
    session_state.set_panels([])


class _DummyPrefs:
    def __init__(self):
        self.measurement_system = "metric"

    def set_measurement_system(self, system):
        self.measurement_system = system

    def set_csv_units(self, system):
        self.measurement_system = system

    def get_default_sheet_size_mm(self, system):
        return (1220.0, 2440.0) if system == "metric" else (1219.2, 2438.4)

    def get_default_kerf_mm(self, system="metric"):
        return 3.0

    def get_default_spacing_mm(self, system="metric"):
        return 2.0


def test_manual_sheet_edit_resets_preset_and_updates_state():
    """Manual sheet edit should drop preset selection and sync session_state."""
    session_state.set_measurement_system("metric")
    prefs = _DummyPrefs()
    widget = SheetConfigWidget(prefs)

    state = {
        "measurement_system": "metric",
        "sheet_width_mm": 1220.0,
        "sheet_height_mm": 2440.0,
        "kerf_mm": 3.0,
        "margin_mm": 2.0,
    }
    widget.apply_state(state)

    # Select a preset (e.g., 4x8) then manually edit the width
    widget._on_preset_changed(1)
    widget.sheet_width_edit.setText("999")
    widget._validate_and_sync()

    assert widget.preset_combo.currentIndex() == 0  # Reset to None / Custom
    assert session_state.get_sheet_size() == (999.0, state["sheet_height_mm"])
    session_state.set_panels([])
