import os
from types import SimpleNamespace

import pytest
from SquatchCut.gui.commands import cmd_settings


class _DummyControl:
    def __init__(self):
        self.shown = []

    def showDialog(self, panel):
        self.shown.append(panel)


class _DummyWorkbench:
    pass


_DummyWorkbench.__name__ = "SquatchCutWorkbench"


class _DummyGui:
    def __init__(self, control):
        self.Control = control

    def activeWorkbench(self):
        return _DummyWorkbench()


@pytest.fixture(autouse=True)
def clear_settings_panel():
    cmd_settings._clear_settings_panel()
    yield
    cmd_settings._clear_settings_panel()


def test_settings_icon_path_points_to_squatchcut_resource():
    command = cmd_settings.SquatchCutSettingsCommand()
    resources = command.GetResources()
    icon_path = resources.get("Pixmap", "")
    if hasattr(icon_path, "isNull"):
        assert icon_path.isNull() is False
    else:
        assert icon_path.endswith("sasquatch_settings.svg")
        assert os.path.isfile(icon_path)


def test_settings_command_reuses_panel(monkeypatch):
    dummy_control = _DummyControl()
    dummy_gui = _DummyGui(dummy_control)
    dummy_app = SimpleNamespace(
        Console=SimpleNamespace(PrintError=lambda *args, **kwargs: None)
    )

    monkeypatch.setattr(cmd_settings, "Gui", dummy_gui)
    monkeypatch.setattr(cmd_settings, "App", dummy_app)

    class DummyPanel:
        def __init__(self):
            self.set_close_callback_called = False
            self._callback = None

        def set_close_callback(self, callback):
            self.set_close_callback_called = True
            self._callback = callback

    monkeypatch.setattr(cmd_settings, "TaskPanel_Settings", DummyPanel)

    command = cmd_settings.SquatchCutSettingsCommand()
    command.Activated()
    command.Activated()

    assert len(dummy_control.shown) == 2
    assert dummy_control.shown[0] is dummy_control.shown[1]
    assert cmd_settings._current_settings_panel() is dummy_control.shown[-1]


def test_settings_command_closes_existing_dialog(monkeypatch):
    """Ensure Settings closes any active TaskPanel before opening."""
    dummy_control = _DummyControl()
    dummy_control.active = True
    dummy_control.closed = 0

    def _active_dialog():
        return object() if dummy_control.active else None

    def _close_dialog():
        dummy_control.closed += 1
        dummy_control.active = False

    dummy_control.activeDialog = _active_dialog
    dummy_control.closeDialog = _close_dialog

    dummy_gui = _DummyGui(dummy_control)
    dummy_app = SimpleNamespace(
        Console=SimpleNamespace(PrintError=lambda *args, **kwargs: None)
    )

    monkeypatch.setattr(cmd_settings, "Gui", dummy_gui)
    monkeypatch.setattr(cmd_settings, "App", dummy_app)

    class DummyPanel:
        def __init__(self):
            self._callback = None

        def set_close_callback(self, callback):
            self._callback = callback

    monkeypatch.setattr(cmd_settings, "TaskPanel_Settings", DummyPanel)

    cmd_settings._clear_settings_panel()
    command = cmd_settings.SquatchCutSettingsCommand()
    command.Activated()

    # Existing dialog should be closed once, and a new panel shown
    assert dummy_control.closed == 1
    assert len(dummy_control.shown) == 1
