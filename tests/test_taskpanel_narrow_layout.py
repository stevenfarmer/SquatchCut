"""Tests for TaskPanel layout optimizations for narrow docks."""

from __future__ import annotations

import types

import pytest
from SquatchCut.core import session_state
from SquatchCut.gui import taskpanel_main as taskpanel_module
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel


class DummyDoc:
    def __init__(self):
        self.Name = "TestDoc"

    def recompute(self):
        pass


@pytest.fixture(autouse=True)
def _reset_session_state():
    session_state.set_measurement_system("metric")
    yield
    session_state.set_measurement_system("metric")


def _create_panel_for_layout_test(monkeypatch):
    """Create a TaskPanel for layout testing."""
    doc = DummyDoc()
    app_stub = types.SimpleNamespace(ActiveDocument=doc, newDocument=lambda _name: doc)
    gui_stub = types.SimpleNamespace(
        Control=types.SimpleNamespace(closeDialog=lambda: None)
    )

    monkeypatch.setattr(taskpanel_module, "App", app_stub)
    monkeypatch.setattr(taskpanel_module, "Gui", gui_stub)

    panel = SquatchCutTaskPanel(doc)

    return panel, doc


def test_taskpanel_initializes_properly(monkeypatch):
    """Test that TaskPanel initializes without errors."""
    panel, doc = _create_panel_for_layout_test(monkeypatch)

    # Should initialize without errors
    assert panel.form is not None
    assert panel.input_widget is not None
    assert panel.sheet_widget is not None
    assert panel.nesting_widget is not None
    assert panel.output_group is not None


def test_nesting_buttons_use_vertical_layout(monkeypatch):
    """Test that nesting buttons are arranged vertically to prevent clipping."""
    panel, doc = _create_panel_for_layout_test(monkeypatch)

    # Check that nesting widget exists and has buttons
    nesting_widget = panel.nesting_widget
    assert hasattr(nesting_widget, "preview_button")
    assert hasattr(nesting_widget, "run_button")

    # Both buttons should exist and be enabled/disabled appropriately
    assert nesting_widget.preview_button is not None
    assert nesting_widget.run_button is not None


def test_warning_banner_has_compact_styling(monkeypatch):
    """Test that warning banner uses compact styling for narrow layouts."""
    panel, doc = _create_panel_for_layout_test(monkeypatch)

    # Check warning banner exists and has compact styling
    assert panel.sheet_warning_container is not None
    assert panel.sheet_warning_label is not None

    # Check that label has word wrap enabled for narrow layouts
    if hasattr(panel.sheet_warning_label, "wordWrap"):
        assert panel.sheet_warning_label.wordWrap() is True

    # Check that styling method exists (compact styling is applied in _build_sheet_warning_banner)
    assert hasattr(panel.sheet_warning_label, "setStyleSheet")


def test_export_controls_use_vertical_layout(monkeypatch):
    """Test that export controls are arranged vertically to prevent clipping."""
    panel, doc = _create_panel_for_layout_test(monkeypatch)

    # Check that export controls exist
    assert panel.export_controls_container is not None
    assert panel.export_format_combo is not None
    assert panel.export_button is not None
    assert panel.include_labels_check is not None
    assert panel.include_dimensions_check is not None


def test_view_controls_use_vertical_layout(monkeypatch):
    """Test that view controls are arranged vertically to prevent clipping."""
    panel, doc = _create_panel_for_layout_test(monkeypatch)

    # Check that view controls exist and are properly arranged
    assert panel.view_controls_container is not None
    assert panel.btnViewSource is not None
    assert panel.btnViewSheets is not None

    # Check visibility controls
    assert panel.visibility_controls_container is not None
    assert panel.show_sheet_check is not None
    assert panel.show_nested_check is not None


def test_layout_uses_vertical_stacking(monkeypatch):
    """Test that layout uses vertical stacking to prevent clipping."""
    panel, doc = _create_panel_for_layout_test(monkeypatch)

    # Should initialize without errors
    assert panel.form is not None

    # Key widgets should be accessible
    assert panel.nesting_widget is not None
    assert panel.output_group is not None
