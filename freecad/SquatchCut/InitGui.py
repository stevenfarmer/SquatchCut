"""@codex
Workbench registration: defines SquatchCutWorkbench and registers commands with FreeCAD GUI.
- Primary entry point: SquatchCut_ShowTaskPanel (consolidated Task panel).
- Legacy commands remain available via the Advanced toolbar/menu.
Icons: resolves icons under resources/icons/.
Note: Avoid adding business logic; keep this file focused on registration/bootstrap only.
"""

import os

import FreeCAD as App
import FreeCADGui as Gui

try:
    from .version import __version__ as _SC_VERSION
except Exception:
    from SquatchCut.version import __version__ as _SC_VERSION  # type: ignore

try:
    from PySide import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets

App.Console.PrintLog("[SquatchCut][DEBUG] InitGui module imported\n")


_ICON_PATH = os.path.join(
    os.path.dirname(__file__),
    "resources",
    "icons",
    "squatchcut_workbench.svg",
)


class SquatchCutWorkbench(Gui.Workbench):
    """
    SquatchCut – sheet nesting / panel optimizer workbench.
    """

    MenuText = "SquatchCut"
    ToolTip = "SquatchCut: CSV-driven sheet nesting and panel optimization (Beta – work in progress)"
    Icon = _ICON_PATH

    def Initialize(self):
        """
        Called once when the workbench is first loaded.
        Registers all commands, toolbars, and menus.
        """
        App.Console.PrintMessage("[SquatchCut] Initialize() running\n")
        version = globals().get("_SC_VERSION", "dev")
        App.Console.PrintMessage(f"[SquatchCut] Initialize() called (v{version})\n")
        # Hydrate session state from persisted preferences before any UI/commands read it.
        try:
            from SquatchCut.settings import hydrate_from_params

            hydrate_from_params()
        except Exception as exc:  # pragma: no cover - best-effort startup
            App.Console.PrintMessage(f"[SquatchCut][WARN] Failed to hydrate settings: {exc}\n")
        # Import command modules so they register their FreeCAD commands
        from SquatchCut.gui.commands import (
            cmd_main_ui,
            cmd_import_csv,
            cmd_add_shapes,
            cmd_settings,
            cmd_set_sheet_size,
            cmd_run_nesting,
            cmd_export_report,
            cmd_preferences,
            cmd_run_gui_tests,
        )

        try:
            App.Console.PrintLog(f"[SquatchCut][DEBUG] cmd_import_csv loaded from: {cmd_import_csv.__file__}\n")
        except Exception as exc:
            App.Console.PrintError(f"[SquatchCut][ERROR] Failed to inspect cmd_import_csv module: {exc}\n")

        # Register core commands
        cmd_main_ui.register()
        Gui.addCommand("SquatchCut_ImportCSV", cmd_import_csv.COMMAND)
        Gui.addCommand("SquatchCut_AddShapes", cmd_add_shapes.COMMAND)
        Gui.addCommand("SquatchCut_Settings", cmd_settings.SquatchCutSettingsCommand())
        # Settings command registered on import
        Gui.addCommand("SquatchCut_SetSheetSize", cmd_set_sheet_size.COMMAND)
        Gui.addCommand("SquatchCut_RunNesting", cmd_run_nesting.COMMAND)
        Gui.addCommand("SquatchCut_ToggleSourcePanels", cmd_run_nesting.ToggleSourcePanelsCommand())
        Gui.addCommand("SquatchCut_ExportNestingCSV", cmd_run_nesting.ExportNestingCSVCommand())
        Gui.addCommand("SquatchCut_ExportReport", cmd_export_report.COMMAND)
        Gui.addCommand("SquatchCut_Preferences", cmd_preferences.COMMAND)
        Gui.addCommand("SquatchCut_RunGUITests", cmd_run_gui_tests.COMMAND)

        primary_commands = ["SquatchCut_ShowTaskPanel", "SquatchCut_Settings"]
        self.appendToolbar("SquatchCut", primary_commands)
        self.appendMenu("SquatchCut", primary_commands)

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Activated(self):
        """Auto-open the SquatchCut Task panel when the workbench is selected."""
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

Gui.addWorkbench(SquatchCutWorkbench())
