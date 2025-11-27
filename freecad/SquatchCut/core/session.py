"""@codex
Central SquatchCut session state (in-memory only for current FreeCAD session).
Pure data container; no GUI code here.
"""

from __future__ import annotations

from typing import Any

import FreeCAD as App


class SquatchCutSession:
    """
    Shared in-memory state for SquatchCut commands and workflows.
    """

    def __init__(self) -> None:
        self.panels: list[dict] = []
        self.sheets: list[dict] = []
        self.shapes: list[Any] = []
        self.active_csv_path: str | None = None
        self.last_nesting_result: Any | None = None
        self.last_layout: Any | None = None
        self.sheet_width: float | None = None
        self.sheet_height: float | None = None
        self.sheet_units: str = "mm"

    def load_csv_panels(self, panels_list: list[dict], csv_path: str | None = None) -> None:
        """
        Replace current panels with those loaded from CSV.
        """
        self.panels = list(panels_list or [])
        self.active_csv_path = csv_path
        App.Console.PrintMessage(
            f">>> [SquatchCut] Loaded {len(self.panels)} panels from CSV\n"
        )

    def clear_panels(self) -> None:
        """
        Clear only panel data.
        """
        self.panels.clear()
        self.active_csv_path = None
        App.Console.PrintMessage(">>> [SquatchCut] Cleared panels\n")

    def clear_all(self) -> None:
        """
        Reset all session state fields.
        """
        self.panels.clear()
        self.sheets.clear()
        self.shapes.clear()
        self.active_csv_path = None
        self.last_nesting_result = None
        self.last_layout = None
        self.sheet_width = None
        self.sheet_height = None
        self.sheet_units = "mm"
        App.Console.PrintMessage(">>> [SquatchCut] Cleared entire session\n")

    def set_last_layout(self, layout):
        """
        Store the most recent nesting layout.
        """
        self.last_layout = layout
        try:
            App.Console.PrintMessage(
                ">>> [SquatchCut] SessionState.set_last_layout: layout updated\n"
            )
        except Exception:
            pass

    def add_panels(self, panels: list[dict]) -> None:
        """
        Append panels to the existing list.
        """
        if not panels:
            return
        if not hasattr(self, "panels"):
            self.panels = []
        self.panels.extend(panels)

    def set_sheet_size(self, width, height, units="mm"):
        """
        Update the active sheet size in the session.
        width, height are numeric (mm or inches depending on units).
        """
        try:
            w = float(width)
            h = float(height)
        except Exception as exc:
            raise ValueError(f"Invalid sheet size values: {width!r}, {height!r}") from exc

        if w <= 0 or h <= 0:
            raise ValueError(f"Sheet dimensions must be positive, got {w} x {h}")

        self.sheet_width = w
        self.sheet_height = h
        self.sheet_units = units or "mm"

        try:
            App.Console.PrintMessage(
                f">>> [SquatchCut] SessionState.set_sheet_size: {w} x {h} {self.sheet_units}\n"
            )
        except Exception:
            pass


# Module-level singleton for shared access
SESSION = SquatchCutSession()
