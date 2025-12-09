from SquatchCut.core import logger


class StubPrefs:
    def __init__(self, rv="normal", pc="none"):
        self.rv = rv
        self.pc = pc

    def get_report_view_log_level(self):
        return self.rv

    def get_python_console_log_level(self):
        return self.pc


def test_logger_levels_do_not_crash(monkeypatch):
    # Stub preferences to verbose for both channels
    monkeypatch.setattr(logger, "SquatchCutPreferences", lambda: StubPrefs(rv="verbose", pc="verbose"))
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")


def test_logger_none_level(monkeypatch):
    # Stub preferences to none; should still not crash on info/debug/warn
    monkeypatch.setattr(logger, "SquatchCutPreferences", lambda: StubPrefs(rv="none", pc="none"))
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")


def test_logger_printf_support(monkeypatch):
    monkeypatch.setattr(logger, "SquatchCutPreferences", lambda: StubPrefs(rv="verbose", pc="verbose"))
    logger.info("Cleaned %d sheet(s) with %s", 3, "preview")
    logger.warning("Removed %s objects (%d failures)", "nested", 0)
    logger.error("Export failed for %s: %s", "svg", "permission denied")
