"""@codex
FreeCAD module init for SquatchCut.
This is imported by FreeCAD when the SquatchCut module is discovered.
Keep this file lightweight; no GUI code here.
"""

import FreeCAD as App
try:
    from SquatchCut.version import __version__ as _SC_VERSION
except Exception:
    _SC_VERSION = "0.0.0"

App.Console.PrintMessage(f">>> [SquatchCut] Init.py imported (v{_SC_VERSION})\n")
