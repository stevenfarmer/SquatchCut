import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure we can import SquatchCut
sys.path.append(os.getcwd())

# Mock FreeCAD dependencies only. Do NOT mock PySide/PySide2.
with patch.dict(sys.modules, {
    "FreeCAD": MagicMock(),
    "FreeCADGui": MagicMock(),
}):
    # Import relevant SquatchCut modules
    from SquatchCut.gui import qt_compat
    from SquatchCut.gui.taskpanel_settings import SquatchCutSettingsPanel
    import SquatchCut.core.preferences as sc_prefs
    from SquatchCut.core.preferences import SquatchCutPreferences
    from SquatchCut import settings

class TestSettingsDevMode(unittest.TestCase):

    def setUp(self):
        # Reset preferences for each test
        SquatchCutPreferences._local_shared = {}

        # Manually force App to None in preferences module
        self.original_app = sc_prefs.App
        sc_prefs.App = None

        # Instantiate the panel
        with patch('SquatchCut.settings.hydrate_from_params'):
            self.panel = SquatchCutSettingsPanel()

    def tearDown(self):
        # Restore App
        sc_prefs.App = self.original_app
        # Clean up preferences
        SquatchCutPreferences._local_shared = {}

    def test_developer_mode_checkbox_exists(self):
        """Verify the Developer Mode checkbox exists and is initially unchecked (default)."""
        self.assertTrue(hasattr(self.panel, "developer_mode_check"), "Developer mode checkbox should exist")
        self.assertFalse(self.panel.developer_mode_check.isChecked(), "Should be unchecked by default")

    def test_developer_tools_group_visibility(self):
        """Verify Developer tools group visibility follows the checkbox."""
        if not hasattr(self.panel, "developer_group_box"):
            self.skipTest("self.developer_group_box not implemented yet")

        # Initial state (Dev mode OFF) -> Group Hidden
        self.assertFalse(self.panel.developer_group_box.isVisible(), "Developer group should be hidden when Dev Mode is OFF")

        # Toggle ON
        self.panel.developer_mode_check.setChecked(True)
        # Manually trigger signal logic if needed (it is needed for shim)
        if hasattr(self.panel, "_on_developer_mode_toggled"):
             self.panel._on_developer_mode_toggled()

        self.assertTrue(self.panel.developer_group_box.isVisible(), "Developer group should be visible when Dev Mode is ON")

        # Toggle OFF
        self.panel.developer_mode_check.setChecked(False)
        if hasattr(self.panel, "_on_developer_mode_toggled"):
             self.panel._on_developer_mode_toggled()

        self.assertFalse(self.panel.developer_group_box.isVisible(), "Developer group should be hidden when Dev Mode is OFF")

    def test_logging_controls_existence(self):
        """Verify logging controls exist."""
        self.assertTrue(hasattr(self.panel, "log_level_report_combo"), "Report view log combo should exist")
        self.assertTrue(hasattr(self.panel, "log_level_console_combo"), "Python console log combo should exist")

    def test_persistence_logic(self):
        """Verify that UI changes write to preferences."""
        prefs = SquatchCutPreferences()

        # 1. Developer Mode
        if hasattr(self.panel, "developer_mode_check"):
            self.panel.developer_mode_check.setChecked(True)
            self.panel._apply_changes()
            self.assertTrue(prefs.get_developer_mode(), "Developer mode should be persisted as True")

            self.panel.developer_mode_check.setChecked(False)
            self.panel._apply_changes()
            self.assertFalse(prefs.get_developer_mode(), "Developer mode should be persisted as False")

        # 2. Log Levels
        if hasattr(self.panel, "log_level_report_combo"):
            idx = self.panel.log_level_report_combo.findData("verbose")
            if idx >= 0:
                self.panel.log_level_report_combo.setCurrentIndex(idx)
                self.panel._apply_changes()
                self.assertEqual(prefs.get_report_view_log_level(), "verbose")
