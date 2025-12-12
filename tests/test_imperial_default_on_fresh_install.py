"""Test that SquatchCut defaults to imperial units on fresh installations."""

from unittest.mock import MagicMock, patch

from SquatchCut.core import session_state, units
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.settings import hydrate_from_params


class TestImperialDefaultOnFreshInstall:
    """Test that fresh installations default to imperial measurement system."""

    def test_fresh_install_defaults_to_imperial(self):
        """Test that a fresh installation (no FreeCAD params) defaults to imperial."""
        # Mock no FreeCAD parameter group (fresh install scenario)
        with patch("SquatchCut.core.preferences.App", None):
            prefs = SquatchCutPreferences()

            # Should default to imperial on fresh install
            measurement_system = prefs.get_measurement_system()
            assert measurement_system == "imperial"

    def test_fresh_install_hydration_sets_imperial_units(self):
        """Test that hydration on fresh install sets imperial units."""
        # Mock no FreeCAD parameter group
        with patch("SquatchCut.core.preferences.App", None):
            with patch("SquatchCut.core.units.App", None):
                # Clear any existing state
                session_state._measurement_system = None
                units._fallback_units = "mm"

                # Hydrate from params (fresh install)
                hydrate_from_params()

                # Should be set to imperial
                assert session_state.get_measurement_system() == "imperial"
                assert units.get_units() == "in"

    def test_existing_metric_preference_preserved(self):
        """Test that existing metric preferences are preserved."""
        # Mock FreeCAD parameter group with existing metric setting
        mock_grp = MagicMock()
        mock_grp.GetString.return_value = "metric"

        with patch("SquatchCut.core.preferences.App") as mock_app:
            mock_app.ParamGet.return_value = mock_grp

            prefs = SquatchCutPreferences()
            measurement_system = prefs.get_measurement_system()

            # Should preserve existing metric setting
            assert measurement_system == "metric"

    def test_existing_imperial_preference_preserved(self):
        """Test that existing imperial preferences are preserved."""
        # Mock FreeCAD parameter group with existing imperial setting
        mock_grp = MagicMock()
        mock_grp.GetString.return_value = "imperial"

        with patch("SquatchCut.core.preferences.App") as mock_app:
            mock_app.ParamGet.return_value = mock_grp

            prefs = SquatchCutPreferences()
            measurement_system = prefs.get_measurement_system()

            # Should preserve existing imperial setting
            assert measurement_system == "imperial"

    def test_workbench_initialization_respects_imperial_default(self):
        """Test that workbench initialization respects imperial default."""
        # Mock fresh install scenario
        with patch("SquatchCut.core.preferences.App", None):
            with patch("SquatchCut.core.units.App", None):
                # Clear state
                session_state._measurement_system = None
                units._fallback_units = "mm"

                # Simulate workbench initialization
                from SquatchCut.freecad_integration import hydrate_settings_from_params

                hydrate_settings_from_params()

                # Should default to imperial
                assert session_state.get_measurement_system() == "imperial"
                assert units.get_units() == "in"

    def test_imperial_sheet_defaults_on_fresh_install(self):
        """Test that fresh install gets imperial sheet size defaults."""
        with patch("SquatchCut.core.preferences.App", None):
            prefs = SquatchCutPreferences()

            # Should get imperial defaults (48" x 96")
            width_in, height_in = prefs.get_default_sheet_size("imperial")
            assert width_in == 48.0
            assert height_in == 96.0

            # Measurement system should be imperial
            assert prefs.get_measurement_system() == "imperial"
