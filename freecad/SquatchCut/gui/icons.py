"""Icon helper for SquatchCut GUI commands."""

from __future__ import annotations

import os

from SquatchCut.core import logger

ICON_DIR = os.path.join(os.path.dirname(__file__), "..", "resources", "icons")
ICON_MAP = {
    "main": "squatchcut.svg",
    "settings": "settings.svg",
    "preferences": "preferences.svg",
    "run_nesting": "run_nesting.svg",
    "import_csv": "import_csv.svg",
    "export_report": "export_report.svg",
    "set_sheet_size": "set_sheet_size.svg",
    "add_shapes": "add_shapes.svg",
    "toggle_visibility": "toggle_visibility.svg",
    "tool_settings": "squatchcut-settings.svg",
}
FALLBACK_ICON_NAME = "squatchcut.svg"
ICON_KEYS = tuple(ICON_MAP.keys())


def _icon_path(name: str) -> str:
    key = name if name in ICON_MAP else "main"
    target = ICON_MAP.get(key, FALLBACK_ICON_NAME)
    return os.path.join(ICON_DIR, target)


def _log_missing(name: str, path: str) -> None:
    logger.warning(f"Icon '{name}' missing at {path}; falling back to default.")


def get_icon(name: str) -> str:
    """Return the file path for the logical icon name, falling back gracefully."""
    path = _icon_path(name)
    if os.path.exists(path):
        return path
    _log_missing(name, path)
    fallback = os.path.join(ICON_DIR, FALLBACK_ICON_NAME)
    return fallback if os.path.exists(fallback) else path
