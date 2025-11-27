"""@codex
Workbench registration: defines SquatchCutWorkbench and registers commands with FreeCAD GUI.
Menu/toolbar: loads SC_* commands into 'SquatchCut Tools' toolbar and 'SquatchCut' menu.
Icons: resolves icons under resources/icons/.
Note: Avoid adding business logic; keep this file focused on registration/bootstrap only.
"""

print(">>> [SquatchCut] InitGui module imported")

import FreeCAD as App
import FreeCADGui as Gui


class SquatchCutWorkbench(Gui.Workbench):
    """
    SquatchCut – sheet nesting / panel optimizer workbench.
    """

    MenuText = "SquatchCut"
    ToolTip = "SquatchCut: CSV-driven sheet nesting and panel optimization"

    def Initialize(self):
        """
        Called once when the workbench is first loaded.
        Registers all commands, toolbars, and menus.
        """
        print(">>> [SquatchCut] Initialize() running")
        App.Console.PrintMessage(">>> [SquatchCut] Initialize() called\n")
        # Import command modules so they register their FreeCAD commands
        from SquatchCut.gui.commands import (
            cmd_import_csv,
            cmd_add_shapes,
            cmd_set_sheet_size,
            cmd_run_nesting,
            cmd_export_report,
            cmd_preferences,
        )

        try:
            App.Console.PrintMessage(
                f">>> [SquatchCut] cmd_import_csv loaded from: {cmd_import_csv.__file__}\n"
            )
        except Exception as exc:
            App.Console.PrintError(
                f">>> [SquatchCut] Failed to inspect cmd_import_csv module: {exc}\n"
            )

        # Command names as registered in each cmd_*.py module
        commands = [
            "SquatchCut_ImportCSV",
            "SquatchCut_AddShapes",
            "SquatchCut_SetSheetSize",
            "SquatchCut_RunNesting",
            "SquatchCut_ToggleSourcePanels",
            "SquatchCut_ExportNestingCSV",
            "SquatchCut_ExportReport",
            "SquatchCut_Preferences",
        ]

        Gui.addCommand("SquatchCut_ImportCSV", cmd_import_csv.COMMAND)
        Gui.addCommand("SquatchCut_AddShapes", cmd_add_shapes.COMMAND)
        Gui.addCommand("SquatchCut_SetSheetSize", cmd_set_sheet_size.COMMAND)
        Gui.addCommand("SquatchCut_RunNesting", cmd_run_nesting.COMMAND)
        Gui.addCommand("SquatchCut_ToggleSourcePanels", cmd_run_nesting.ToggleSourcePanelsCommand())
        Gui.addCommand("SquatchCut_ExportNestingCSV", cmd_run_nesting.ExportNestingCSVCommand())
        Gui.addCommand("SquatchCut_ExportReport", cmd_export_report.COMMAND)
        Gui.addCommand("SquatchCut_Preferences", cmd_preferences.COMMAND)

        # One toolbar for now
        self.appendToolbar("SquatchCut", commands)

        # And a menu
        self.appendMenu("SquatchCut", commands)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(SquatchCutWorkbench())
