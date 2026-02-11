"""@codex
Workbench registration: defines SquatchCutWorkbench and registers commands with FreeCAD GUI.
- Primary entry point: SquatchCut_ShowTaskPanel (consolidated Task panel).
- Legacy commands remain available via the Advanced toolbar/menu.
Icons: resolves icons under resources/icons/.
Note: Avoid adding business logic; keep this file focused on registration/bootstrap only.
"""

from SquatchCut.freecad_integration import SquatchCutWorkbench, register_workbench

# Expose the workbench class for compatibility with any legacy imports
__all__ = ["SquatchCutWorkbench"]

# Register with FreeCAD at import time (as expected by FreeCAD workbench discovery)
register_workbench()
