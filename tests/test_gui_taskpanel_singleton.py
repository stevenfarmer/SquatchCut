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
