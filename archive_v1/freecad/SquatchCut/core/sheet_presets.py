"""Sheet preset definitions and helpers shared across SquatchCut UIs."""

from __future__ import annotations

from typing import Optional, TypedDict, cast

from SquatchCut.core.units import inches_to_mm

DEFAULT_MATCH_TOLERANCE_MM = 1e-3


def _normalize_measurement_system(system: str) -> str:
    return "imperial" if system == "imperial" else "metric"


class Preset(TypedDict):
    id: str
    width_mm: float
    height_mm: float
    nickname: Optional[str]


class PresetEntry(TypedDict):
    id: Optional[str]
    label: str
    size: Optional[tuple[float, float]]
    nickname: Optional[str]


IMPERIAL_PRESETS: list[Preset] = [
    {
        "id": "4x8",
        "width_mm": inches_to_mm(48.0),
        "height_mm": inches_to_mm(96.0),
        "nickname": "4x8 ft",
    },
    {
        "id": "2x4",
        "width_mm": inches_to_mm(24.0),
        "height_mm": inches_to_mm(48.0),
        "nickname": "2x4 ft",
    },
    {
        "id": "5x10",
        "width_mm": inches_to_mm(60.0),
        "height_mm": inches_to_mm(120.0),
        "nickname": "5x10 ft",
    },
]

METRIC_PRESETS: list[Preset] = [
    {"id": "1220x2440", "width_mm": 1220.0, "height_mm": 2440.0, "nickname": None},
    {"id": "1220x3050", "width_mm": 1220.0, "height_mm": 3050.0, "nickname": None},
    {"id": "1500x3000", "width_mm": 1500.0, "height_mm": 3000.0, "nickname": None},
]

PRESETS_BY_SYSTEM: dict[str, list[Preset]] = {
    "imperial": IMPERIAL_PRESETS,
    "metric": METRIC_PRESETS,
}

FACTORY_DEFAULTS: dict[str, dict[str, float]] = {
    "metric": {"width_mm": 1220.0, "height_mm": 2440.0},
    "imperial": {"width_mm": inches_to_mm(48.0), "height_mm": inches_to_mm(96.0)},
}


def get_presets_for_system(system: str) -> list[Preset]:
    """Return editable copies of the presets associated with the requested system."""
    normalized = _normalize_measurement_system(system)
    presets = PRESETS_BY_SYSTEM.get(normalized, PRESETS_BY_SYSTEM["metric"])
    return [cast(Preset, dict(preset)) for preset in presets]


def get_preset_entries(system: str) -> list[PresetEntry]:
    """Return combo entries that include a leading blank/None selection and preset data."""
    entries: list[PresetEntry] = [
        {"id": None, "label": "", "size": None, "nickname": None}
    ]
    for preset in get_presets_for_system(system):
        label = preset.get("nickname") or preset["id"]
        entries.append(
            {
                "id": preset["id"],
                "label": label,
                "size": (preset["width_mm"], preset["height_mm"]),
                "nickname": preset.get("nickname"),
            }
        )
    return entries


def get_factory_default_sheet_size(system: str) -> tuple[float, float]:
    """Return the factory-default sheet size in millimeters for the given system."""
    normalized = _normalize_measurement_system(system)
    default = FACTORY_DEFAULTS.get(normalized, FACTORY_DEFAULTS["metric"])
    return default["width_mm"], default["height_mm"]


def get_initial_sheet_size(
    system: str,
    session_size: tuple[Optional[float], Optional[float]],
    user_default_size: tuple[Optional[float], Optional[float]],
) -> tuple[float, float]:
    """
    Choose the size to show when the tasks panel loads, preferring existing session data,
    then user defaults, and finally the factory defaults for the measurement system.
    """
    session_w, session_h = session_size
    if session_w is not None and session_h is not None:
        return session_w, session_h
    user_w, user_h = user_default_size
    if user_w is not None and user_h is not None:
        return user_w, user_h
    return get_factory_default_sheet_size(system)


def find_matching_preset(
    system: str,
    width_mm: Optional[float],
    height_mm: Optional[float],
    tolerance_mm: float = DEFAULT_MATCH_TOLERANCE_MM,
) -> Optional[Preset]:
    """Return the matching preset for the system if the dimensions match within tolerance."""
    if width_mm is None or height_mm is None:
        return None
    normalized = _normalize_measurement_system(system)
    presets = PRESETS_BY_SYSTEM.get(normalized, PRESETS_BY_SYSTEM["metric"])
    for preset in presets:
        if (
            abs(preset["width_mm"] - width_mm) <= tolerance_mm
            and abs(preset["height_mm"] - height_mm) <= tolerance_mm
        ):
            return preset
    return None


def apply_preset(system: str, preset_id: str) -> Optional[tuple[float, float]]:
    """Return the width/height for the preset identified by `preset_id` in the given system."""
    normalized = _normalize_measurement_system(system)
    presets = PRESETS_BY_SYSTEM.get(normalized, PRESETS_BY_SYSTEM["metric"])
    for preset in presets:
        if preset["id"] == preset_id:
            return preset["width_mm"], preset["height_mm"]
    return None


class PresetSelectionState:
    """Track preset combo selection while keeping a distinct 'None' entry."""

    def __init__(self):
        self.current_index = 0
        self.current_id: Optional[str] = None

    def set_index(self, index: int, entries: list[PresetEntry]) -> int:
        if not entries:
            self.current_index = 0
            self.current_id = None
            return 0
        idx = max(0, min(index, len(entries) - 1))
        self.current_index = idx
        self.current_id = entries[idx].get("id")
        return idx

    def clear(self) -> None:
        self.current_index = 0
        self.current_id = None

    def ensure_valid(self, length: int) -> None:
        if length <= 0 or self.current_index >= length:
            self.clear()
