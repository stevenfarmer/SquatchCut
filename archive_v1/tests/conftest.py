import importlib
import os
import sys


def _ensure_repo_core_on_path():
    """Ensure SquatchCut package under freecad/ is importable when not installed."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    core_path = os.path.join(repo_root, "freecad")
    if core_path not in sys.path:
        sys.path.insert(0, core_path)


_ensure_repo_core_on_path()

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
