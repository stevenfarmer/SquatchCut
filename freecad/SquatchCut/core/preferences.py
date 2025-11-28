"""SquatchCut-specific preferences wrapper using FreeCAD ParamGet."""

from __future__ import annotations

try:
    import FreeCAD as App  # type: ignore
except Exception:  # pragma: no cover
    App = None


class SquatchCutPreferences:
    """Persist SquatchCut defaults under a dedicated parameter group."""

    PARAM_GROUP = "User parameter:BaseApp/Preferences/Mod/SquatchCut"

    def __init__(self):
        self._grp = App.ParamGet(self.PARAM_GROUP) if App else None
        self._local: dict[str, object] = {}

    def _float(self, key: str, fallback: float) -> float:
        if self._grp:
            try:
                return float(self._grp.GetFloat(key, fallback))
            except Exception:
                pass
        return float(self._local.get(key, fallback))

    def _set_float(self, key: str, value: float) -> None:
        if self._grp:
            try:
                self._grp.SetFloat(key, float(value))
            except Exception:
                pass
        self._local[key] = float(value)

    def _bool(self, key: str, fallback: bool) -> bool:
        if self._grp:
            try:
                return bool(self._grp.GetBool(key, fallback))
            except Exception:
                pass
        return bool(self._local.get(key, fallback))

    def _set_bool(self, key: str, value: bool) -> None:
        if self._grp:
            try:
                self._grp.SetBool(key, bool(value))
            except Exception:
                pass
        self._local[key] = bool(value)

    def get_default_sheet_width_mm(self, fallback: float = 2440.0) -> float:
        return self._float("DefaultSheetWidthMM", fallback)

    def set_default_sheet_width_mm(self, value: float) -> None:
        self._set_float("DefaultSheetWidthMM", value)

    def get_default_sheet_height_mm(self, fallback: float = 1220.0) -> float:
        return self._float("DefaultSheetHeightMM", fallback)

    def set_default_sheet_height_mm(self, value: float) -> None:
        self._set_float("DefaultSheetHeightMM", value)

    def get_default_spacing_mm(self, fallback: float = 0.0) -> float:
        return self._float("DefaultSpacingMM", fallback)

    def set_default_spacing_mm(self, value: float) -> None:
        self._set_float("DefaultSpacingMM", value)

    def get_default_kerf_mm(self, fallback: float = 3.0) -> float:
        return self._float("DefaultKerfMM", fallback)

    def set_default_kerf_mm(self, value: float) -> None:
        self._set_float("DefaultKerfMM", value)

    def get_default_optimize_for_cut_path(self, fallback: bool = False) -> bool:
        return self._bool("DefaultOptimizeForCutPath", fallback)

    def set_default_optimize_for_cut_path(self, value: bool) -> None:
        self._set_bool("DefaultOptimizeForCutPath", value)

    def get_measurement_system(self, fallback: str = "metric") -> str:
        val = fallback
        if self._grp:
            try:
                val = self._grp.GetString("MeasurementSystem", fallback)
            except Exception:
                val = fallback
        val = str(self._local.get("MeasurementSystem", val))
        if val not in ("metric", "imperial"):
            val = fallback
        return val

    def set_measurement_system(self, system: str) -> None:
        if system not in ("metric", "imperial"):
            system = "metric"
        if self._grp:
            try:
                self._grp.SetString("MeasurementSystem", system)
            except Exception:
                pass
        self._local["MeasurementSystem"] = system

    def is_metric(self) -> bool:
        return self.get_measurement_system() == "metric"

    def is_imperial(self) -> bool:
        return self.get_measurement_system() == "imperial"

    def get_csv_units(self, fallback: str = "metric") -> str:
        val = fallback
        if self._grp:
            try:
                val = self._grp.GetString("CsvUnits", fallback)
            except Exception:
                val = fallback
        val = str(self._local.get("CsvUnits", val))
        if val not in ("metric", "imperial"):
            val = fallback
        return val

    def set_csv_units(self, units: str) -> None:
        if units not in ("metric", "imperial"):
            units = "metric"
        if self._grp:
            try:
                self._grp.SetString("CsvUnits", units)
            except Exception:
                pass
        self._local["CsvUnits"] = units

    def get_export_include_labels(self, fallback: bool = True) -> bool:
        if self._grp:
            try:
                return bool(self._grp.GetBool("ExportIncludeLabels", fallback))
            except Exception:
                pass
        return bool(self._local.get("ExportIncludeLabels", fallback))

    def set_export_include_labels(self, value: bool) -> None:
        if self._grp:
            try:
                self._grp.SetBool("ExportIncludeLabels", bool(value))
            except Exception:
                pass
        self._local["ExportIncludeLabels"] = bool(value)

    def get_export_include_dimensions(self, fallback: bool = False) -> bool:
        if self._grp:
            try:
                return bool(self._grp.GetBool("ExportIncludeDimensions", fallback))
            except Exception:
                pass
        return bool(self._local.get("ExportIncludeDimensions", fallback))

    def set_export_include_dimensions(self, value: bool) -> None:
        if self._grp:
            try:
                self._grp.SetBool("ExportIncludeDimensions", bool(value))
            except Exception:
                pass
        self._local["ExportIncludeDimensions"] = bool(value)

    def get_report_view_log_level(self, fallback: str = "normal") -> str:
        val = fallback
        if self._grp:
            try:
                val = self._grp.GetString("ReportViewLogLevel", fallback)
            except Exception:
                val = fallback
        val = str(self._local.get("ReportViewLogLevel", val))
        if val not in ("none", "normal", "verbose"):
            val = fallback
        return val

    def set_report_view_log_level(self, level: str) -> None:
        if level not in ("none", "normal", "verbose"):
            level = "normal"
        if self._grp:
            try:
                self._grp.SetString("ReportViewLogLevel", level)
            except Exception:
                pass
        self._local["ReportViewLogLevel"] = level

    def get_python_console_log_level(self, fallback: str = "none") -> str:
        val = fallback
        if self._grp:
            try:
                val = self._grp.GetString("PythonConsoleLogLevel", fallback)
            except Exception:
                val = fallback
        val = str(self._local.get("PythonConsoleLogLevel", val))
        if val not in ("none", "normal", "verbose"):
            val = fallback
        return val

    def set_python_console_log_level(self, level: str) -> None:
        if level not in ("none", "normal", "verbose"):
            level = "none"
        if self._grp:
            try:
                self._grp.SetString("PythonConsoleLogLevel", level)
            except Exception:
                pass
        self._local["PythonConsoleLogLevel"] = level


# Backward-compatible alias if other modules imported Preferences
Preferences = SquatchCutPreferences
PreferencesManager = SquatchCutPreferences
