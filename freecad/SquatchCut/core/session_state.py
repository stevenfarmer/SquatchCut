from __future__ import annotations

"""Compatibility wrapper around core.session for legacy call sites.

All real state now lives on SquatchCut.core.session.SESSION.
This module just forwards to that singleton.
"""

from typing import Any, List

try:
    from SquatchCut.core.nesting import PlacedPart
except Exception:  # pragma: no cover - fallback for environments without the module
    PlacedPart = Any

from . import session as _session


class SessionState:
    def __init__(self):
        self._backend = _session.SESSION

        # Ensure canonical fields exist on the backend
        if not hasattr(self._backend, "panels"):
            self._backend.panels = []
        if not hasattr(self._backend, "active_csv_path"):
            self._backend.active_csv_path = ""
        if not hasattr(self._backend, "sheet_width"):
            self._backend.sheet_width = None
        if not hasattr(self._backend, "sheet_height"):
            self._backend.sheet_height = None
        if not hasattr(self._backend, "sheet_units"):
            self._backend.sheet_units = "mm"
        if not hasattr(self._backend, "last_layout"):
            self._backend.last_layout = None

    def __getattr__(self, name):
        return getattr(self._backend, name)

    def set_sheet_size(self, width, height, units="mm"):
        """Delegate sheet size update to backend."""
        if hasattr(self._backend, "set_sheet_size"):
            return self._backend.set_sheet_size(width, height, units)
        try:
            w = float(width)
            h = float(height)
        except Exception as exc:
            raise ValueError(f"Invalid sheet size values: {width!r}, {height!r}") from exc
        if w <= 0 or h <= 0:
            raise ValueError(f"Sheet dimensions must be positive, got {w} x {h}")
        self._backend.sheet_width = w
        self._backend.sheet_height = h
        self._backend.sheet_units = units or "mm"


def get_sheet_size() -> tuple[float | None, float | None]:
    """Return (sheet_width, sheet_height) from the session backend."""
    return getattr(SESSION, "sheet_width", None), getattr(SESSION, "sheet_height", None)


# Global session object used across commands
SESSION = SessionState()


def get_panels() -> list[dict]:
    """Return a shallow copy of the current panels list."""
    return list(getattr(SESSION, "panels", []))


def add_panels(panels: list[dict]) -> None:
    """Append panels into the current session, if any."""
    if not panels:
        return

    # Prefer a dedicated method if available
    if hasattr(SESSION, "add_panels"):
        SESSION.add_panels(panels)  # type: ignore[attr-defined]
    elif hasattr(SESSION, "load_csv_panels"):
        # If SESSION uses load_csv_panels to ingest panel lists, call that
        active_path = getattr(SESSION, "active_csv_path", None)
        SESSION.load_csv_panels(panels, csv_path=active_path)  # type: ignore[attr-defined]
    else:
        # Fallback: operate on a "panels" list attribute
        if not hasattr(SESSION, "panels"):
            SESSION.panels = []  # type: ignore[attr-defined]
        SESSION.panels.extend(panels)


def clear_panels() -> None:
    """Remove all panels from the current session."""
    if hasattr(SESSION, "clear_panels"):
        SESSION.clear_panels()  # type: ignore[attr-defined]
    else:
        panels = getattr(SESSION, "panels", None)
        if panels is not None:
            panels.clear()


def has_panels() -> bool:
    """Return True if there are any panels loaded."""
    return bool(getattr(SESSION, "panels", []))


def set_last_report_data(data: dict | None) -> None:
    """Store the last generated report payload on the session."""
    if hasattr(SESSION, "last_report_data"):
        SESSION.last_report_data = data  # type: ignore[assignment]


def get_last_report_data() -> dict | None:
    """Return the last generated report payload, if any."""
    return getattr(SESSION, "last_report_data", None)


_last_layout: List[PlacedPart] = []

_kerf_mm = 0.0
_gap_mm = 0.0


def set_last_layout(layout: List[PlacedPart]) -> None:
    """Store the last computed nesting layout."""
    global _last_layout
    # make a shallow copy so callers can reuse their list safely
    _last_layout = list(layout)


def get_last_layout() -> List[PlacedPart]:
    """Return a copy of the last nesting layout, or an empty list if none."""
    return list(_last_layout)


def set_kerf_mm(value: float) -> None:
    """Set kerf spacing (mm) applied between adjacent parts."""
    global _kerf_mm
    _kerf_mm = float(value)


def get_kerf_mm() -> float:
    """Return kerf spacing (mm)."""
    return float(_kerf_mm)


def set_gap_mm(value: float) -> None:
    """Set gap/halo spacing (mm) applied around parts (and sheet edges)."""
    global _gap_mm
    _gap_mm = float(value)


def get_gap_mm() -> float:
    """Return gap/halo spacing (mm)."""
    return float(_gap_mm)
