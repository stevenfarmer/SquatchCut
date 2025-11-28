"""@codex
Workbench registration: defines SquatchCutWorkbench and registers commands with FreeCAD GUI.
- Primary entry point: SquatchCut_ShowTaskPanel (consolidated Task panel).
- Legacy commands remain available via the Advanced toolbar/menu.
Icons: resolves icons under resources/icons/.
Note: Avoid adding business logic; keep this file focused on registration/bootstrap only.
"""

from SquatchCut.core import logger

logger.debug("InitGui module imported")

import FreeCAD as App
import FreeCADGui as Gui
try:
    from PySide import QtWidgets
except ImportError:
    from PySide2 import QtWidgets


class SquatchCutWorkbench(Gui.Workbench):
    """
    SquatchCut – sheet nesting / panel optimizer workbench.
    """

    MenuText = "SquatchCut"
    ToolTip = "SquatchCut: CSV-driven sheet nesting and panel optimization (Beta – work in progress)"

    def Initialize(self):
        """
        Called once when the workbench is first loaded.
        Registers all commands, toolbars, and menus.
        """
        logger.info("Initialize() running")
        logger.info("Initialize() called")
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
        )

        try:
            logger.debug(f"cmd_import_csv loaded from: {cmd_import_csv.__file__}")
        except Exception as exc:
            logger.error(f"Failed to inspect cmd_import_csv module: {exc}")

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

        primary_commands = ["SquatchCut_ShowTaskPanel"]
        advanced_commands = [
            "SquatchCut_Settings",
            "SquatchCut_ImportCSV",
            "SquatchCut_AddShapes",
            "SquatchCut_SetSheetSize",
            "SquatchCut_RunNesting",
            "SquatchCut_ToggleSourcePanels",
            "SquatchCut_ExportNestingCSV",
            "SquatchCut_ExportReport",
            "SquatchCut_Preferences",
        ]

        # Primary toolbar focuses on the unified UI; keep advanced tools available separately.
        self.appendToolbar("SquatchCut", primary_commands)
        self.appendToolbar("SquatchCut Advanced", advanced_commands)

        # Menu keeps both primary and advanced entries.
        self.appendMenu("SquatchCut", primary_commands + advanced_commands)
        self._ensure_squatchcut_menu()

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

    def _ensure_squatchcut_menu(self):
        """Ensure a top-level SquatchCut menu with Preferences entry exists."""
        try:
            mw = Gui.getMainWindow()
            if mw is None:
                return
            menu_bar = mw.menuBar()
            squatch_menu = None
            for action in menu_bar.actions():
                if action.text() == "SquatchCut":
                    squatch_menu = action.menu()
                    break
            if squatch_menu is None:
                squatch_menu = QtWidgets.QMenu("SquatchCut", mw)
                menu_bar.addMenu(squatch_menu)

            # Avoid duplicate action
            existing = [act.text() for act in squatch_menu.actions()]
            if "Preferences…" not in existing:
                pref_action = squatch_menu.addAction("Preferences…")
                pref_action.setToolTip("Configure default SquatchCut sheet size, spacing, and cut options.")
                pref_action.triggered.connect(lambda: Gui.runCommand("SquatchCut_Preferences"))
        except Exception:
            return


Gui.addWorkbench(SquatchCutWorkbench())
