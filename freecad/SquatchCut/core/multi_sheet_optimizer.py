"""@codex
Module: Multi-sheet optimization layer that repeatedly runs the nesting engine.
Boundaries: Do not implement single-sheet placement internals or geometry; orchestrate nesting_engine across multiple sheets only.
Primary methods: optimize, _init_sheets, _allocate_panels, _next_sheet.
Note: Update incrementally; do not overwrite this module when adding logic.
"""

from __future__ import annotations


class MultiSheetOptimizer:
    """Runs the nesting engine repeatedly to fill multiple sheets."""

    def optimize(self, panels: list[dict], sheet_size: dict) -> list[dict]:
        """Allocate panels across sheets and return placements per sheet."""
        from .nesting_engine import NestingEngine

        panels_remaining = list(panels)
        sheets: list[dict] = []
        engine = NestingEngine()
        sheet_counter = 0

        width = (
            sheet_size.get("width", 0) if isinstance(sheet_size, dict) else float(sheet_size)
        )
        height = sheet_size.get("height", 0) if isinstance(sheet_size, dict) else 0

        while panels_remaining:
            sheet_counter += 1
            placements, leftovers = engine.nest_panels(
                panels_remaining, float(width), float(height)
            )
            sheet = {
                "sheet_id": sheet_counter,
                "width": float(width),
                "height": float(height),
                "placements": [],
            }
            for placement in placements:
                placement["sheet_id"] = sheet_counter
                sheet["placements"].append(placement)
            sheets.append(sheet)

            if len(leftovers) == len(panels_remaining):
                # No progress; break to avoid infinite loop.
                break
            panels_remaining = leftovers
        return sheets

    def _init_sheets(self, sheet_size: dict):
        """Prepare initial sheet structures."""
        return []

    def _allocate_panels(self, panels: list[dict], sheet_size: dict):
        """Loop through panels and allocate them to sheets using the nesting engine."""
        return self.optimize(panels, sheet_size)

    def _next_sheet(self, sheet_size: dict):
        """Create the next sheet when existing ones are full."""
        return {
            "width": float(sheet_size.get("width", 0)),
            "height": float(sheet_size.get("height", 0)),
            "placements": [],
        }
