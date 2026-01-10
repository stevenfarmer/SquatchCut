from types import SimpleNamespace

import pytest

pytest.importorskip("FreeCAD")

from SquatchCut.gui.commands import cmd_main_ui


def test_task_panel_command_reuses_instance():
    cmd_main_ui._clear_main_panel()
    command = cmd_main_ui.SquatchCutMainUICommand()
    command.Activated()
    first = cmd_main_ui._current_main_panel()
    assert first is not None
    command.Activated()
    assert cmd_main_ui._current_main_panel() is first
    first.reject()
    assert cmd_main_ui._current_main_panel() is None


def test_task_panel_unique_import_and_nest_buttons():
    cmd_main_ui._clear_main_panel()
    command = cmd_main_ui.SquatchCutMainUICommand()
    command.Activated()
    panel = cmd_main_ui._current_main_panel()
    assert panel is not None
    assert getattr(panel, "import_button", None) is not None
    assert getattr(panel, "nest_button", None) is not None
    assert panel.import_button.text() == "Import Parts"
    assert panel.nest_button.text() == "Nest Parts"
    assert not hasattr(panel, "import_and_nest_button")
    panel.reject()


def test_main_panel_closes_other_active_dialog(monkeypatch):
    """Ensure main panel activation closes an existing TaskPanel (e.g., Settings)."""
    cmd_main_ui._clear_main_panel()

    dummy_control = type(
        "DummyControl",
        (),
        {
            "shown": [],
            "closed": 0,
            "activeDialog": lambda self=None: "other_panel",
            "closeDialog": lambda self=None: None,
            "showDialog": lambda self, panel=None: self.shown.append(panel),
        },
    )()

    def _close_dialog():
        dummy_control.closed += 1
        return None

    dummy_control.closeDialog = _close_dialog

    dummy_gui = SimpleNamespace(Control=dummy_control)
    dummy_app = SimpleNamespace(newDocument=lambda name: SimpleNamespace(Name=name))

    monkeypatch.setattr(cmd_main_ui, "Gui", dummy_gui)
    monkeypatch.setattr(cmd_main_ui, "App", dummy_app)
    monkeypatch.setattr(cmd_main_ui, "SquatchCutTaskPanel", lambda doc=None: SimpleNamespace())

    command = cmd_main_ui.SquatchCutMainUICommand()
    command.Activated()

    assert dummy_control.closed == 1  # existing dialog closed
    assert len(dummy_control.shown) == 1  # new panel shown
