"""@codex
Workbench package metadata and bootstrap for SquatchCut.
Menu/toolbar: defined in InitGui; this file should not register commands directly.
Icons: referenced via InitGui under resources/icons/.
Note: Avoid functional logic; maintain metadata and simple initialization helpers only.
"""

from __future__ import annotations

from pathlib import Path

from .version import __version__

ICONPATH = Path(__file__).resolve().parent / "resources" / "icons"

__author__ = "SquatchCut Team"
__all__ = ["__version__", "__author__", "initialize", "ICONPATH"]


def initialize():
    """Placeholder for SquatchCut package initialization."""
    return True
