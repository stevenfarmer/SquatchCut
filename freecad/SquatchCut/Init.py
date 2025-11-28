"""@codex
FreeCAD module init for SquatchCut.
This is imported by FreeCAD when the SquatchCut module is discovered.
Keep this file lightweight; no GUI code here.
"""

import FreeCAD as App

from SquatchCut.version import __version__

App.Console.PrintMessage(f">>> [SquatchCut] Init.py imported (v{__version__})\n")
