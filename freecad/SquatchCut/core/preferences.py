"""SquatchCut-specific preferences wrapper using FreeCAD ParamGet."""

from __future__ import annotations

try:
    import FreeCAD as App  # type: ignore
except Exception:  # pragma: no cover
    App = None

import math

from SquatchCut.core import sheet_presets
from SquatchCut.core.units import inches_to_mm, mm_to_inches


class SquatchCutPreferences:
    """Persist SquatchCut defaults under a dedicated parameter group."""

    PARAM_GROUP = "User parameter:BaseApp/Preferences/Mod/SquatchCut"
    _local_shared: dict[str, object] = {}

    DEFAULT_SHEET_FLAG_TEMPLATE = "DefaultSheetSizeIsSet_{system}"
    METRIC_WIDTH_KEY = "DefaultSheetWidthMM"
    METRIC_HEIGHT_KEY = "DefaultSheetHeightMM"
    IMPERIAL_WIDTH_KEY = "DefaultSheetWidthIn"
    IMPERIAL_HEIGHT_KEY = "DefaultSheetHeightIn"
    IMPERIAL_DEFAULT_WIDTH_IN = 48.0
    IMPERIAL_DEFAULT_HEIGHT_IN = 96.0
    METRIC_DEFAULT_WIDTH_MM = 1220.0
    METRIC_DEFAULT_HEIGHT_MM = 2440.0

    def __init__(self):
        self._grp = App.ParamGet(self.PARAM_GROUP) if App else None
        self._local = self.__class__._local_shared

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

    def _get_float_entry(self, key: str) -> tuple[bool, float]:
        sentinel = float("nan")
        if self._grp:
            try:
                value = float(self._grp.GetFloat(key, sentinel))
            except Exception:
                value = sentinel
            if not math.isnan(value):
                return True, value
        if key in self._local:
            try:
                return True, float(self._local[key])
            except Exception:
                pass
        return False, sentinel

    def _default_flag_key(self, system: str) -> str:
        return self.DEFAULT_SHEET_FLAG_TEMPLATE.format(system=system)

    def has_default_sheet_size(self, system: str) -> bool:
        flag_key = self._default_flag_key(system)
        if self._bool(flag_key, False):
            return True
        if system == "imperial":
            width_key = self.IMPERIAL_WIDTH_KEY
            height_key = self.IMPERIAL_HEIGHT_KEY
        else:
            width_key = self.METRIC_WIDTH_KEY
            height_key = self.METRIC_HEIGHT_KEY
        has_width, _ = self._get_float_entry(width_key)
        has_height, _ = self._get_float_entry(height_key)
        if has_width and has_height:
            return True
        if system == "imperial":
            has_metric_w, _ = self._get_float_entry(self.METRIC_WIDTH_KEY)
            has_metric_h, _ = self._get_float_entry(self.METRIC_HEIGHT_KEY)
            if has_metric_w and has_metric_h:
                return True
        return False

    def _mark_sheet_defaults(self, system: str) -> None:
        flag_key = self._default_flag_key(system)
        self._set_bool(flag_key, True)

    def get_default_sheet_width_mm(self, fallback: float | None = None) -> float:
        if fallback is None:
            fallback = sheet_presets.get_factory_default_sheet_size(self.get_measurement_system())[0]
        return self._float(self.METRIC_WIDTH_KEY, fallback)

    def set_default_sheet_width_mm(self, value: float) -> None:
        self._set_float(self.METRIC_WIDTH_KEY, value)
        self._mark_sheet_defaults("metric")

    def get_default_sheet_height_mm(self, fallback: float | None = None) -> float:
        if fallback is None:
            fallback = sheet_presets.get_factory_default_sheet_size(self.get_measurement_system())[1]
        return self._float(self.METRIC_HEIGHT_KEY, fallback)

    def set_default_sheet_height_mm(self, value: float) -> None:
        self._set_float(self.METRIC_HEIGHT_KEY, value)
        self._mark_sheet_defaults("metric")

    def get_default_sheet_width_in(self, fallback: float | None = None) -> float:
        if fallback is None:
            fallback = self.IMPERIAL_DEFAULT_WIDTH_IN
        has_value, value = self._get_float_entry(self.IMPERIAL_WIDTH_KEY)
        if has_value:
            return value
        has_metric, mm_value = self._get_float_entry(self.METRIC_WIDTH_KEY)
        if has_metric:
            return mm_to_inches(mm_value)
        return fallback

    def set_default_sheet_width_in(self, value: float) -> None:
        self._set_float(self.IMPERIAL_WIDTH_KEY, value)
        self._set_float(self.METRIC_WIDTH_KEY, inches_to_mm(value))
        self._mark_sheet_defaults("imperial")

    def get_default_sheet_height_in(self, fallback: float | None = None) -> float:
        if fallback is None:
            fallback = self.IMPERIAL_DEFAULT_HEIGHT_IN
        has_value, value = self._get_float_entry(self.IMPERIAL_HEIGHT_KEY)
        if has_value:
            return value
        has_metric, mm_value = self._get_float_entry(self.METRIC_HEIGHT_KEY)
        if has_metric:
            return mm_to_inches(mm_value)
        return fallback

    def set_default_sheet_height_in(self, value: float) -> None:
        self._set_float(self.IMPERIAL_HEIGHT_KEY, value)
        self._set_float(self.METRIC_HEIGHT_KEY, inches_to_mm(value))
        self._mark_sheet_defaults("imperial")

    def clear_default_sheet_size(self) -> None:
        """Clear stored sheet defaults so UIs can render empty fields."""
        for key in (
            self.METRIC_WIDTH_KEY,
            self.METRIC_HEIGHT_KEY,
            self.IMPERIAL_WIDTH_KEY,
            self.IMPERIAL_HEIGHT_KEY,
            self._default_flag_key("metric"),
            self._default_flag_key("imperial"),
        ):
            if key in self._local:
                try:
                    del self._local[key]
                except Exception:
                    pass
        if self._grp:
            try:
                self._grp.SetBool(self._default_flag_key("metric"), False)
                self._grp.SetBool(self._default_flag_key("imperial"), False)
            except Exception:
                pass

    def get_default_sheet_size(self, system: str) -> tuple[float, float]:
        if system == "imperial":
            return self.get_default_sheet_width_in(), self.get_default_sheet_height_in()
        return self.get_default_sheet_width_mm(), self.get_default_sheet_height_mm()

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

    def get_default_allow_rotate(self, fallback: bool = False) -> bool:
        if self._grp:
            try:
                return bool(self._grp.GetBool("DefaultAllowRotate", fallback))
            except Exception:
                pass
        return bool(self._local.get("DefaultAllowRotate", fallback))

    def set_default_allow_rotate(self, value: bool) -> None:
        if self._grp:
            try:
                self._grp.SetBool("DefaultAllowRotate", bool(value))
            except Exception:
                pass
        self._local["DefaultAllowRotate"] = bool(value)

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

    def get_developer_mode(self, fallback: bool = False) -> bool:
        return self._bool("DeveloperModeEnabled", fallback)

    def set_developer_mode(self, value: bool) -> None:
        self._set_bool("DeveloperModeEnabled", value)


# Backward-compatible alias if other modules imported Preferences
Preferences = SquatchCutPreferences
PreferencesManager = SquatchCutPreferences
