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
