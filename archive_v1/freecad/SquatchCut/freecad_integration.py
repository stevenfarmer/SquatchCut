"""Centralized FreeCAD integration layer for SquatchCut.

This module is safe to import in plain Python: all FreeCAD/Qt imports are
wrapped in try/except and set to None when unavailable.
"""

from __future__ import annotations

import inspect
import os
from pathlib import Path
from typing import Any

try:  # FreeCAD core
    import FreeCAD as App  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    App = None

try:  # FreeCAD GUI
    import FreeCADGui as Gui  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Gui = None

try:  # Geom modules shipped with FreeCAD
    import Part  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Part = None

try:
    import Draft  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Draft = None

try:  # Qt bindings (FreeCAD ships PySide/PySide2)
    from PySide import QtCore, QtGui, QtWidgets  # type: ignore
except Exception:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    except Exception:  # pragma: no cover - fall back to stubs
        from SquatchCut.gui import qt_compat as _qt_compat

        QtCore = _qt_compat.QtCore
        QtGui = _qt_compat.QtGui
        QtWidgets = _qt_compat.QtWidgets

try:
    from SquatchCut.version import __version__ as _SC_VERSION
except Exception:
    _SC_VERSION = "dev"

_ICON_BASE = Path(__file__).resolve().parent / "resources" / "icons"
_initialized = False


def freecad_available() -> bool:
    """Return True when FreeCAD's App module is importable."""
    return App is not None


def freecad_gui_available() -> bool:
    """Return True when FreeCAD GUI APIs are importable."""
    return App is not None and Gui is not None


def get_version_string() -> str:
    """Return the current SquatchCut version (falls back to 'dev')."""
    return _SC_VERSION


def _print_console(message: str, level: str = "message") -> None:
    """Best-effort console logging that works inside and outside FreeCAD."""
    newline = "" if message.endswith("\n") else "\n"
    if App and getattr(App, "Console", None):
        try:
            console = App.Console
            if level == "error":
                console.PrintError(message + newline)
            elif level == "warning":
                console.PrintWarning(message + newline)
            elif level == "log":
                console.PrintLog(message + newline)
            else:
                console.PrintMessage(message + newline)
            return
        except Exception:
            pass
    try:
        print(message)
    except Exception:
        pass


def handle_init_import() -> None:
    """Mirror the legacy Init.py side effect when FreeCAD imports the module."""
    _print_console(f">>> [SquatchCut] Init.py imported (v{get_version_string()})")


def ensure_active_document(name: str = "SquatchCut"):
    """Return the active FreeCAD document, creating one if necessary."""
    if App is None:
        return None
    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument(name)
    try:
        if Gui:
            Gui.ActiveDocument = Gui.getDocument(doc.Name)
    except Exception:
        try:
            Gui.ActiveDocument = Gui.ActiveDocument or None  # type: ignore
        except Exception:
            pass
    return doc


def hydrate_settings_from_params() -> None:
    """Load persisted preferences into the in-memory session state."""
    try:
        from SquatchCut.settings import hydrate_from_params

        hydrate_from_params()
    except Exception as exc:  # pragma: no cover - best-effort bootstrap
        _print_console(f"[SquatchCut][WARN] Failed to hydrate settings: {exc}", level="warning")


def register_commands() -> None:
    """Import and register all FreeCAD GUI commands."""
    if Gui is None:
        return

    from SquatchCut.gui.commands import (
        cmd_add_shapes,
        cmd_export_report,
        cmd_import_csv,
        cmd_main_ui,
        cmd_preferences,
        cmd_reset_view,
        cmd_run_gui_tests,
        cmd_run_nesting,
        cmd_set_sheet_size,
        cmd_settings,
    )

    try:
        _print_console(f"[SquatchCut][DEBUG] cmd_import_csv loaded from: {cmd_import_csv.__file__}", level="log")
    except Exception:
        pass

    # Register core commands
    cmd_main_ui.register()
    Gui.addCommand("SquatchCut_ImportCSV", cmd_import_csv.COMMAND)
    Gui.addCommand("SquatchCut_AddShapes", cmd_add_shapes.COMMAND)
    Gui.addCommand("SquatchCut_Settings", cmd_settings.SquatchCutSettingsCommand())
    Gui.addCommand("SquatchCut_SetSheetSize", cmd_set_sheet_size.COMMAND)
    Gui.addCommand("SquatchCut_RunNesting", cmd_run_nesting.COMMAND)
    Gui.addCommand("SquatchCut_ToggleSourcePanels", cmd_run_nesting.ToggleSourcePanelsCommand())
    Gui.addCommand("SquatchCut_ExportNestingCSV", cmd_run_nesting.ExportNestingCSVCommand())
    Gui.addCommand("SquatchCut_ExportReport", cmd_export_report.COMMAND)
    Gui.addCommand("SquatchCut_Preferences", cmd_preferences.COMMAND)
    Gui.addCommand("SquatchCut_RunGUITests", cmd_run_gui_tests.COMMAND)
    Gui.addCommand("SquatchCut_ResetView", cmd_reset_view.ResetViewCommand())


_WorkbenchBase: type[Any] = Gui.Workbench if Gui else object


class SquatchCutWorkbench(_WorkbenchBase):
    """FreeCAD Workbench registration wrapper."""

    MenuText = "SquatchCut"
    ToolTip = "SquatchCut: CSV-driven sheet nesting and panel optimization (Beta – work in progress)"

    try:
        _icon_root = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        try:
            _icon_root = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # type: ignore
        except Exception:
            _icon_root = os.getcwd()
    Icon = os.path.join(_icon_root, "resources", "icons", "squatchcut_workbench.svg")

    def Initialize(self):  # noqa: N802  (FreeCAD API)
        """Called once when the workbench is first loaded."""
        global _initialized
        if _initialized:
            _print_console("[SquatchCut][DEBUG] Initialize() already ran; skipping duplicate registration", level="log")
            return
        _initialized = True

        _print_console(f"[SquatchCut] Initialize() called (v{get_version_string()})")
        hydrate_settings_from_params()
        register_commands()

        if Gui:
            primary_commands = ["SquatchCut_ShowTaskPanel", "SquatchCut_Settings", "SquatchCut_ResetView"]
            try:
                self.appendToolbar("SquatchCut", primary_commands)
                self.appendMenu("SquatchCut", primary_commands)
            except Exception:
                pass

    def GetClassName(self):  # noqa: N802  (FreeCAD API)
        return "Gui::PythonWorkbench"

    def Activated(self):  # noqa: N802  (FreeCAD API)
        """Auto-open the SquatchCut Task panel when the workbench is selected."""
        if Gui is None:
            return
        try:
            import SquatchCut.gui.taskpanel_main as tpm

            active = Gui.Control.activeDialog()
            if active and isinstance(active, tpm.SquatchCutTaskPanel):
                return
        except Exception:
            pass
        try:
            Gui.runCommand("SquatchCut_ShowTaskPanel")
        except Exception:
            pass


def register_workbench():
    """Register the SquatchCut workbench with FreeCAD."""
    if Gui is None:
        _print_console("[SquatchCut][WARN] FreeCADGui not available; workbench not registered.", level="warning")
        return None

    wb = SquatchCutWorkbench()
    Gui.addWorkbench(wb)
    _print_console("[SquatchCut][DEBUG] Workbench registered", level="log")
    return wb


__all__ = [
    "App",
    "Gui",
    "Part",
    "Draft",
    "QtCore",
    "QtGui",
    "QtWidgets",
    "freecad_available",
    "freecad_gui_available",
    "get_version_string",
    "handle_init_import",
    "hydrate_settings_from_params",
    "ensure_active_document",
    "register_commands",
    "SquatchCutWorkbench",
    "register_workbench",
]
