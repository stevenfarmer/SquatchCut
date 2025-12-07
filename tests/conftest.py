import importlib

try:
    _gui = importlib.import_module("FreeCADGui")
except Exception:  # pragma: no cover - FreeCADGui unavailable outside tests
    _gui = None
else:
    if not hasattr(_gui, "Workbench"):
        class _DummyWorkbench:  # pragma: no cover - trivial shim
            pass

        _gui.Workbench = _DummyWorkbench

    if not hasattr(_gui, "addCommand"):
        def _noop_command(name, command):  # pragma: no cover - simple shim
            return None

        _gui.addCommand = _noop_command
