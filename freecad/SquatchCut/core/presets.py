"""Legacy sheet preset helpers preserved for backward compatibility."""

from __future__ import annotations

from SquatchCut.core.sheet_presets import (
    find_matching_preset,
    get_presets_for_system,
)

PRESET_SHEETS = get_presets_for_system("imperial")
