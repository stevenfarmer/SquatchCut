import types

from SquatchCut.gui.commands import cmd_main_ui


class _Recorder:
    def __init__(self):
        self.info_messages = []
        self.warning_messages = []

    def info(self, message, *args):
        if args:
            message = message % args
        self.info_messages.append(message)

    def warning(self, message, *args):
        if args:
            message = message % args
        self.warning_messages.append(message)


class _StubPanel:
    def __init__(self, doc=None):
        self.doc = doc
        self._close_callback = None

    def set_close_callback(self, callback):
        self._close_callback = callback

    def reject(self):
        if self._close_callback:
            self._close_callback()


def _setup_freecad_stubs(monkeypatch):
    dummy_control = types.SimpleNamespace()

    def _show_dialog(panel):
        dummy_control.active = panel

    def _close_dialog():
        dummy_control.active = None

    dummy_control.showDialog = _show_dialog
    dummy_control.closeDialog = _close_dialog

    dummy_gui = types.SimpleNamespace(Control=dummy_control)
    dummy_app = types.SimpleNamespace(ActiveDocument=None)

    def _new_doc(name):
        doc = types.SimpleNamespace(Name=name)
        dummy_app.ActiveDocument = doc
        return doc

    dummy_app.newDocument = _new_doc
    monkeypatch.setattr(cmd_main_ui, "Gui", dummy_gui)
    monkeypatch.setattr(cmd_main_ui, "App", dummy_app)
    return dummy_app


def test_taskpanel_logging_sequence(monkeypatch):
    cmd_main_ui._clear_main_panel()
    recorder = _Recorder()
    monkeypatch.setattr(cmd_main_ui, "logger", recorder)
    _setup_freecad_stubs(monkeypatch)
    monkeypatch.setattr(cmd_main_ui, "SquatchCutTaskPanel", _StubPanel)

    command = cmd_main_ui.SquatchCutMainUICommand()
    command.Activated()

    assert recorder.info_messages.count("Opening main task panel.") == 1
    assert recorder.info_messages.count("Task panel opened.") == 1
    assert all("[SquatchCut]" not in msg for msg in recorder.info_messages)


def test_taskpanel_logging_reuse_message(monkeypatch):
    cmd_main_ui._clear_main_panel()
    recorder = _Recorder()
    monkeypatch.setattr(cmd_main_ui, "logger", recorder)
    _setup_freecad_stubs(monkeypatch)
    monkeypatch.setattr(cmd_main_ui, "SquatchCutTaskPanel", _StubPanel)

    command = cmd_main_ui.SquatchCutMainUICommand()
    command.Activated()
    assert recorder.info_messages[-1] == "Task panel opened."

    command.Activated()
    assert recorder.info_messages[-1] == "Reusing existing main task panel."
