"""Workbench registration entrypoint for SquatchCut."""
from __future__ import annotations

import importlib
from types import ModuleType
from typing import Callable, Optional

try:
    import FreeCADGui as Gui
except ImportError:  # pragma: no cover - allow python-level imports
    Gui = None

_workbench_module: Optional[ModuleType] = None
_workbench_names = ("SquatchCut.Workbench", "Workbench")
SquatchCutWorkbench: type | None = None
register_load_csv_command: Optional[Callable[[object], None]] = None
for name in _workbench_names:
    try:
        _workbench_module = importlib.import_module(name)
        break
    except ModuleNotFoundError:
        continue

if _workbench_module is not None:
    SquatchCutWorkbench = getattr(_workbench_module, "SquatchCutWorkbench")
    register_load_csv_command = getattr(_workbench_module, "register_load_csv_command")
else:
    SquatchCutWorkbench = None  # type: ignore[assignment]
    register_load_csv_command = None  # type: ignore[assignment]

_workbench_instance: Optional["SquatchCutWorkbench"] = None
_registered = False


def register_workbench() -> None:
    """Register the SquatchCut workbench with FreeCAD's GUI host."""
    global _registered, _workbench_instance
    if (
        _registered
        or Gui is None
        or not hasattr(Gui, "addWorkbench")
        or SquatchCutWorkbench is None
        or register_load_csv_command is None
    ):
        return
    register_load_csv_command(Gui)
    _workbench_instance = SquatchCutWorkbench()
    Gui.addWorkbench(_workbench_instance)
    _registered = True


if Gui is not None:
    register_workbench()
