"""Centralized logging for SquatchCut."""

from __future__ import annotations

from SquatchCut.freecad_integration import App
from SquatchCut.core.preferences import SquatchCutPreferences


class LogLevel:
    NONE = 0
    NORMAL = 1
    VERBOSE = 2


LEVEL_MAP = {
    "none": LogLevel.NONE,
    "normal": LogLevel.NORMAL,
    "verbose": LogLevel.VERBOSE,
}


def _get_levels():
    prefs = SquatchCutPreferences()
    report_level_str = prefs.get_report_view_log_level()
    console_level_str = prefs.get_python_console_log_level()
    report_level = LEVEL_MAP.get(report_level_str, LogLevel.NORMAL)
    console_level = LEVEL_MAP.get(console_level_str, LogLevel.NONE)
    return report_level, console_level


def _emit_report(message: str, minimum_level: int, report_level: int, kind: str):
    if report_level < minimum_level:
        return
    if App is None:
        return
    if kind == "error":
        App.Console.PrintError(message + "\n")
    elif kind == "warning":
        App.Console.PrintWarning(message + "\n")
    elif kind == "debug":
        App.Console.PrintLog(message + "\n")
    else:
        App.Console.PrintMessage(message + "\n")


def _emit_console(message: str, minimum_level: int, console_level: int):
    if console_level < minimum_level:
        return
    try:
        print(message)
    except Exception:
        pass


def debug(msg: str):
    report_level, console_level = _get_levels()
    minimum = LogLevel.VERBOSE
    _emit_report(f"[SquatchCut][DEBUG] {msg}", minimum, report_level, "debug")
    _emit_console(f"[SquatchCut][DEBUG] {msg}", minimum, console_level)


def info(msg: str):
    report_level, console_level = _get_levels()
    minimum = LogLevel.NORMAL
    _emit_report(f"[SquatchCut] {msg}", minimum, report_level, "info")
    _emit_console(f"[SquatchCut] {msg}", minimum, console_level)


def warning(msg: str):
    report_level, console_level = _get_levels()
    minimum = LogLevel.NORMAL
    _emit_report(f"[SquatchCut][WARN] {msg}", minimum, report_level, "warning")
    _emit_console(f"[SquatchCut][WARN] {msg}", minimum, console_level)


def error(msg: str):
    report_level, console_level = _get_levels()
    _emit_report(f"[SquatchCut][ERROR] {msg}", LogLevel.NONE, report_level, "error")
    _emit_console(f"[SquatchCut][ERROR] {msg}", LogLevel.NONE, console_level)
