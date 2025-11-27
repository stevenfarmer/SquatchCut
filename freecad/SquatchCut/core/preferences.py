"""@codex
Module: Preference wrapper for SquatchCut settings stored in FreeCAD.
Boundaries: Do not perform nesting or UI work; only load/store SquatchCut preferences and expose accessors.
Primary methods: load, save, get_sheet_size, get_spacing, is_rotation_allowed, auto_detect_shapes, get_export_directory, branding_enabled.
Note: Update incrementally; do not overwrite this module when adding logic.
"""

from __future__ import annotations


class Preferences:
    """Wraps FreeCAD preference storage for SquatchCut settings."""

    PREF_PATH = "User parameter:BaseApp/Preferences/SquatchCut"
    DEFAULT_SHEET = {"width": 2440.0, "height": 1220.0}
    DEFAULT_KERF = 0.0
    DEFAULT_ROTATION = True
    DEFAULT_EXPORT_DIR = ""
    DEFAULT_BRANDING = "default"

    def __init__(self):
        self._fallback: dict[str, object] = {}

    def load(self):
        """Load preferences from FreeCAD storage."""
        return {
            "sheet_size": self.get_sheet_size(),
            "kerf": self.get_kerf(),
            "rotation_allowed": self.get_rotation_allowed(),
            "export_directory": self.get_export_directory(),
            "branding_mode": self.get_branding_mode(),
        }

    def save(self, values: dict):
        """Persist provided preference values."""
        if not isinstance(values, dict):
            return
        if "sheet_size" in values and isinstance(values["sheet_size"], dict):
            w = values["sheet_size"].get("width", self.DEFAULT_SHEET["width"])
            h = values["sheet_size"].get("height", self.DEFAULT_SHEET["height"])
            self.set_sheet_size(float(w), float(h))
        if "kerf" in values:
            self.set_kerf(float(values["kerf"]))
        if "rotation_allowed" in values:
            self.set_rotation_allowed(bool(values["rotation_allowed"]))
        if "export_directory" in values:
            self.set_export_directory(str(values["export_directory"]))
        if "branding_mode" in values:
            self.set_branding_mode(str(values["branding_mode"]))

    def get_sheet_size(self) -> dict:
        """Return default sheet width/height."""
        params = self._params()
        if params:
            w = params.GetFloat("SheetWidth", self.DEFAULT_SHEET["width"])
            h = params.GetFloat("SheetHeight", self.DEFAULT_SHEET["height"])
            return {"width": float(w), "height": float(h)}
        return self._fallback.get("sheet_size", dict(self.DEFAULT_SHEET))

    def get_spacing(self) -> float:
        """Return kerf/spacing setting."""
        return self.get_kerf()

    def is_rotation_allowed(self) -> bool:
        """Return whether panel rotation is allowed."""
        return self.get_rotation_allowed()

    def auto_detect_shapes(self) -> bool:
        """Return whether shape auto-detection is enabled."""
        return True

    def get_export_directory(self) -> str:
        """Return path where reports will be exported."""
        params = self._params()
        if params:
            return params.GetString("ExportDirectory", self.DEFAULT_EXPORT_DIR)
        return str(self._fallback.get("export_directory", self.DEFAULT_EXPORT_DIR))

    def branding_enabled(self) -> bool:
        """Return whether SquatchCut branding is enabled in outputs."""
        mode = self.get_branding_mode()
        return mode != "none"

    # New explicit getters/setters for MVP
    def set_sheet_size(self, width: float, height: float):
        params = self._params()
        if params:
            params.SetFloat("SheetWidth", float(width))
            params.SetFloat("SheetHeight", float(height))
        self._fallback["sheet_size"] = {"width": float(width), "height": float(height)}

    def get_kerf(self) -> float:
        params = self._params()
        if params:
            return float(params.GetFloat("Kerf", self.DEFAULT_KERF))
        return float(self._fallback.get("kerf", self.DEFAULT_KERF))

    def set_kerf(self, value: float):
        params = self._params()
        if params:
            params.SetFloat("Kerf", float(value))
        self._fallback["kerf"] = float(value)

    def get_rotation_allowed(self) -> bool:
        params = self._params()
        if params:
            return bool(params.GetBool("RotationAllowed", self.DEFAULT_ROTATION))
        return bool(self._fallback.get("rotation_allowed", self.DEFAULT_ROTATION))

    def set_rotation_allowed(self, flag: bool):
        params = self._params()
        if params:
            params.SetBool("RotationAllowed", bool(flag))
        self._fallback["rotation_allowed"] = bool(flag)

    def set_export_directory(self, path: str):
        params = self._params()
        if params:
            params.SetString("ExportDirectory", str(path))
        self._fallback["export_directory"] = str(path)

    def get_branding_mode(self) -> str:
        params = self._params()
        if params:
            return params.GetString("BrandingMode", self.DEFAULT_BRANDING)
        return str(self._fallback.get("branding_mode", self.DEFAULT_BRANDING))

    def set_branding_mode(self, mode: str):
        params = self._params()
        if params:
            params.SetString("BrandingMode", str(mode))
        self._fallback["branding_mode"] = str(mode)

    def _params(self):
        try:
            import FreeCAD as App  # type: ignore
        except Exception:
            return None
        try:
            return App.ParamGet(self.PREF_PATH)
        except Exception:
            return None


# Alias for clarity with documentation naming
PreferencesManager = Preferences
