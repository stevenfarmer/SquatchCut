"""SquatchCut-specific preferences wrapper using FreeCAD ParamGet."""

from __future__ import annotations

import math

from SquatchCut.core.units import inches_to_mm, mm_to_inches
from SquatchCut.freecad_integration import App


class SquatchCutPreferences:
    """Persist SquatchCut defaults under a dedicated parameter group."""

    PARAM_GROUP = "User parameter:BaseApp/Preferences/Mod/SquatchCut"
    _local_shared: dict[str, object] = {}

    DEFAULT_SHEET_FLAG_TEMPLATE = "DefaultSheetSizeIsSet_{system}"
    METRIC_WIDTH_KEY = "DefaultSheetWidthMM"
    METRIC_HEIGHT_KEY = "DefaultSheetHeightMM"
    IMPERIAL_WIDTH_KEY = "DefaultSheetWidthIn"
    IMPERIAL_HEIGHT_KEY = "DefaultSheetHeightIn"

    METRIC_KERF_KEY = "MetricKerfMM"
    IMPERIAL_KERF_KEY = "ImperialKerfIn"
    METRIC_SPACING_KEY = "MetricSpacingMM"
    IMPERIAL_SPACING_KEY = "ImperialSpacingIn"

    IMPERIAL_DEFAULT_WIDTH_IN = 48.0
    IMPERIAL_DEFAULT_HEIGHT_IN = 96.0
    METRIC_DEFAULT_WIDTH_MM = 1220.0
    METRIC_DEFAULT_HEIGHT_MM = 2440.0

    METRIC_DEFAULT_KERF_MM = 3.0
    IMPERIAL_DEFAULT_KERF_IN = 0.125  # 1/8"
    METRIC_DEFAULT_SPACING_MM = 0.0
    IMPERIAL_DEFAULT_SPACING_IN = 0.0
    SEPARATE_DEFAULTS_MIGRATED_KEY = "SeparateDefaultsMigrated"
    KERF_DEFAULTS_MIGRATED_KEY = "KerfDefaultsMigrated"

    def __init__(self):
        self._grp = App.ParamGet(self.PARAM_GROUP) if App else None
        self._local = self.__class__._local_shared
        self._migrate_legacy_defaults()
        self._ensure_default_storage()

    # ---------------- Internal helpers ----------------

    def _metric_defaults_exist(self) -> bool:
        has_w, _ = self._get_float_entry(self.METRIC_WIDTH_KEY)
        has_h, _ = self._get_float_entry(self.METRIC_HEIGHT_KEY)
        return has_w and has_h

    def _imperial_defaults_exist(self) -> bool:
        has_w, _ = self._get_float_entry(self.IMPERIAL_WIDTH_KEY)
        has_h, _ = self._get_float_entry(self.IMPERIAL_HEIGHT_KEY)
        return has_w and has_h

    def _set_metric_defaults(self, width_mm: float, height_mm: float, mark: bool = True) -> None:
        self._set_float(self.METRIC_WIDTH_KEY, width_mm)
        self._set_float(self.METRIC_HEIGHT_KEY, height_mm)
        if mark:
            self._mark_sheet_defaults("metric")

    def _set_imperial_defaults(self, width_in: float, height_in: float, mark: bool = True) -> None:
        self._set_float(self.IMPERIAL_WIDTH_KEY, width_in)
        self._set_float(self.IMPERIAL_HEIGHT_KEY, height_in)
        if mark:
            self._mark_sheet_defaults("imperial")

    def _migrate_legacy_defaults(self) -> None:
        if not self._bool(self.SEPARATE_DEFAULTS_MIGRATED_KEY, False):
            metric_exists = self._metric_defaults_exist()
            imperial_exists = self._imperial_defaults_exist()
            if metric_exists and not imperial_exists:
                width_mm = self._float(self.METRIC_WIDTH_KEY, self.METRIC_DEFAULT_WIDTH_MM)
                height_mm = self._float(self.METRIC_HEIGHT_KEY, self.METRIC_DEFAULT_HEIGHT_MM)
                self._set_imperial_defaults(mm_to_inches(width_mm), mm_to_inches(height_mm), mark=False)
            elif imperial_exists and not metric_exists:
                width_in = self._float(self.IMPERIAL_WIDTH_KEY, self.IMPERIAL_DEFAULT_WIDTH_IN)
                height_in = self._float(self.IMPERIAL_HEIGHT_KEY, self.IMPERIAL_DEFAULT_HEIGHT_IN)
                self._set_metric_defaults(inches_to_mm(width_in), inches_to_mm(height_in), mark=False)
            self._set_bool(self.SEPARATE_DEFAULTS_MIGRATED_KEY, True)

        if not self._bool(self.KERF_DEFAULTS_MIGRATED_KEY, False):
            legacy_kerf_key = "DefaultKerfMM"
            has_legacy_kerf, legacy_kerf_val = self._get_float_entry(legacy_kerf_key)
            if has_legacy_kerf:
                self._set_float(self.METRIC_KERF_KEY, legacy_kerf_val)
                self._set_float(self.IMPERIAL_KERF_KEY, mm_to_inches(legacy_kerf_val))
            self._set_bool(self.KERF_DEFAULTS_MIGRATED_KEY, True)

    def _ensure_default_storage(self) -> None:
        metric_exists = self._metric_defaults_exist()
        imperial_exists = self._imperial_defaults_exist()
        if not metric_exists:
            self._set_metric_defaults(self.METRIC_DEFAULT_WIDTH_MM, self.METRIC_DEFAULT_HEIGHT_MM)
        if not imperial_exists:
            self._set_imperial_defaults(self.IMPERIAL_DEFAULT_WIDTH_IN, self.IMPERIAL_DEFAULT_HEIGHT_IN)

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
        normalized = "imperial" if system == "imperial" else "metric"
        if normalized == "imperial":
            return self._imperial_defaults_exist()
        return self._metric_defaults_exist()

    def _mark_sheet_defaults(self, system: str) -> None:
        flag_key = self._default_flag_key(system)
        self._set_bool(flag_key, True)

    def get_default_sheet_width_mm(self, fallback: float | None = None) -> float:
        if fallback is None:
            fallback = self.METRIC_DEFAULT_WIDTH_MM
        return self._float(self.METRIC_WIDTH_KEY, fallback)

    def set_default_sheet_width_mm(self, value: float) -> None:
        self._set_float(self.METRIC_WIDTH_KEY, value)
        self._mark_sheet_defaults("metric")

    def get_default_sheet_height_mm(self, fallback: float | None = None) -> float:
        if fallback is None:
            fallback = self.METRIC_DEFAULT_HEIGHT_MM
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
        return fallback

    def set_default_sheet_width_in(self, value: float) -> None:
        self._set_float(self.IMPERIAL_WIDTH_KEY, value)
        self._mark_sheet_defaults("imperial")

    def get_default_sheet_height_in(self, fallback: float | None = None) -> float:
        if fallback is None:
            fallback = self.IMPERIAL_DEFAULT_HEIGHT_IN
        has_value, value = self._get_float_entry(self.IMPERIAL_HEIGHT_KEY)
        if has_value:
            return value
        return fallback

    def set_default_sheet_height_in(self, value: float) -> None:
        self._set_float(self.IMPERIAL_HEIGHT_KEY, value)
        self._mark_sheet_defaults("imperial")

    def clear_default_sheet_size_for_system(self, system: str) -> None:
        """Clear defaults for a specific measurement system."""
        normalized = "imperial" if system == "imperial" else "metric"
        if normalized == "imperial":
            width_key = self.IMPERIAL_WIDTH_KEY
            height_key = self.IMPERIAL_HEIGHT_KEY
            default_width = self.IMPERIAL_DEFAULT_WIDTH_IN
            default_height = self.IMPERIAL_DEFAULT_HEIGHT_IN
            setter = self._set_imperial_defaults
        else:
            width_key = self.METRIC_WIDTH_KEY
            height_key = self.METRIC_HEIGHT_KEY
            default_width = self.METRIC_DEFAULT_WIDTH_MM
            default_height = self.METRIC_DEFAULT_HEIGHT_MM
            setter = self._set_metric_defaults

        for key in (width_key, height_key):
            if key in self._local:
                try:
                    del self._local[key]
                except Exception:
                    pass
        flag_key = self._default_flag_key(normalized)
        if flag_key in self._local:
            self._local.pop(flag_key, None)
        if self._grp:
            try:
                self._grp.SetBool(flag_key, False)
                self._grp.RemFloat(width_key)
                self._grp.RemFloat(height_key)
            except Exception:
                pass
        setter(default_width, default_height)

    def clear_default_sheet_size(self) -> None:
        """Clear stored sheet defaults so UIs fall back to factory values."""
        self.clear_default_sheet_size_for_system("metric")
        self.clear_default_sheet_size_for_system("imperial")

    def get_default_sheet_size(self, system: str) -> tuple[float, float]:
        if system == "imperial":
            return self.get_default_sheet_width_in(), self.get_default_sheet_height_in()
        return self.get_default_sheet_width_mm(), self.get_default_sheet_height_mm()

    def get_default_sheet_size_mm(self, system: str) -> tuple[float, float]:
        """Return the default sheet size in millimeters for the requested system."""
        if system == "imperial":
            width_in = self.get_default_sheet_width_in()
            height_in = self.get_default_sheet_height_in()
            return inches_to_mm(width_in), inches_to_mm(height_in)
        return self.get_default_sheet_width_mm(), self.get_default_sheet_height_mm()

    def get_default_sheet_size_in(self, system: str) -> tuple[float, float]:
        """Return the default sheet size in inches for the requested system."""
        if system == "imperial":
            return self.get_default_sheet_width_in(), self.get_default_sheet_height_in()
        width_mm = self.get_default_sheet_width_mm()
        height_mm = self.get_default_sheet_height_mm()
        return mm_to_inches(width_mm), mm_to_inches(height_mm)

    def get_default_spacing_mm(self, fallback: float = 0.0, system: str | None = None) -> float:
        """
        Return default spacing in mm.
        If system is None, uses the current preferred measurement system.
        """
        sys = system or self.get_measurement_system()
        if sys == "imperial":
             val_in = self._float(self.IMPERIAL_SPACING_KEY, self.IMPERIAL_DEFAULT_SPACING_IN)
             return inches_to_mm(val_in)
        return self._float(self.METRIC_SPACING_KEY, fallback or self.METRIC_DEFAULT_SPACING_MM)

    def set_default_spacing_mm(self, value: float, system: str | None = None) -> None:
        """
        Set default spacing from mm input.
        If system is Imperial, converts mm -> inches and stores in Imperial key.
        """
        sys = system or self.get_measurement_system()
        if sys == "imperial":
            self._set_float(self.IMPERIAL_SPACING_KEY, mm_to_inches(value))
        else:
            self._set_float(self.METRIC_SPACING_KEY, value)

    def get_default_kerf_mm(self, fallback: float = 3.0, system: str = None) -> float:
        """
        Return default kerf in mm.
        If system is None, uses the current preferred measurement system.
        """
        sys = system or self.get_measurement_system()
        if sys == "imperial":
            val_in = self._float(self.IMPERIAL_KERF_KEY, self.IMPERIAL_DEFAULT_KERF_IN)
            return inches_to_mm(val_in)

        # For metric, prefer the specific key, fallback to legacy
        has_metric, val = self._get_float_entry(self.METRIC_KERF_KEY)
        if has_metric:
            return val
        return self._float("DefaultKerfMM", fallback or self.METRIC_DEFAULT_KERF_MM)

    def set_default_kerf_mm(self, value: float, system: str = None) -> None:
        """
        Set default kerf from mm input.
        If system is Imperial, converts mm -> inches and stores in Imperial key.
        """
        sys = system or self.get_measurement_system()
        if sys == "imperial":
            self._set_float(self.IMPERIAL_KERF_KEY, mm_to_inches(value))
        else:
            self._set_float(self.METRIC_KERF_KEY, value)
            # Update legacy key for backward compatibility
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

    def get_measurement_system(self, fallback: str = "imperial") -> str:
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
            system = "imperial"
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

    def get_csv_units(self, fallback: str = "imperial") -> str:
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
            units = "imperial"
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
