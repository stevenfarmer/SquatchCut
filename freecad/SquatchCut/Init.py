"""@codex
FreeCAD module init for SquatchCut.
This is imported by FreeCAD when the SquatchCut module is discovered.
Keep this file lightweight; no GUI code here.
"""

import FreeCAD as App
_SC_VERSION = "dev"
try:
    from .version import __version__ as _SC_VERSION
except Exception:
    try:
        from SquatchCut.version import __version__ as _SC_VERSION  # type: ignore
    except Exception:
        pass

App.Console.PrintMessage(f">>> [SquatchCut] Init.py imported (v{_SC_VERSION})\n")
