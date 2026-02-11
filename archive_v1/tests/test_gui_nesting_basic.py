"""Basic GUI tests for non-shape-based nesting workflow.

**Feature: gui-nesting-workflow**

This module tests the basic GUI components and their initialization
for the standard CSV-based nesting workflow.
"""

from unittest.mock import Mock, patch

from SquatchCut.gui.commands.cmd_run_nesting import RunNestingCommand
from SquatchCut.gui.taskpanel_input import InputGroupWidget
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel
from SquatchCut.gui.taskpanel_nesting import NestingGroupWidget
from SquatchCut.gui.taskpanel_sheet import SheetConfigWidget


class TestGUIComponentInitialization:
    """Test that GUI components initialize correctly."""

    def test_input_widget_initialization(self):
        """Test that InputGroupWidget initializes with required components."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            prefs = Mock()
            widget = InputGroupWidget(prefs)

            # Should have CSV import button
            assert hasattr(widget, "load_csv_button")
            assert widget.load_csv_button.text() == "Import CSV"

            # Should have shape selection button (for shape-based nesting)
            assert hasattr(widget, "select_shapes_button")
            assert widget.select_shapes_button.text() == "Select Shapes"

            # Should have parts table
            assert hasattr(widget, "parts_table")
            assert hasattr(widget.parts_table, "setColumnCount")

            # Should have CSV units combo
            assert hasattr(widget, "csv_units_combo")
            assert hasattr(widget.csv_units_combo, "addItem")

            # Should have required methods
            assert hasattr(widget, "_choose_csv_file")
            assert hasattr(widget, "_import_csv")
            assert hasattr(widget, "_select_shapes")
            assert hasattr(widget, "refresh_table")

    def test_sheet_config_widget_initialization(self):
        """Test that SheetConfigWidget initializes with required components."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            prefs = Mock()
            widget = SheetConfigWidget(prefs)

            # Should have sheet size inputs
            assert hasattr(widget, "sheet_width_edit")
            assert hasattr(widget, "sheet_height_edit")

            # Should have preset combo
            assert hasattr(widget, "preset_combo")

            # Should have units combo (measurement system)
            assert hasattr(widget, "units_combo")

            # Should have required methods
            assert hasattr(widget, "_on_preset_changed")
            assert hasattr(widget, "_on_units_changed")

    def test_nesting_group_widget_initialization(self):
        """Test that NestingGroupWidget initializes with required components."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            prefs = Mock()
            widget = NestingGroupWidget(prefs)

            # Should have nesting controls
            assert hasattr(widget, "kerf_width_edit")
            assert hasattr(widget, "job_allow_rotation_check")
            assert hasattr(widget, "run_button")
            assert hasattr(widget, "preview_button")

            # Should have required methods
            assert hasattr(widget, "_on_settings_changed")

    def test_main_taskpanel_initialization(self):
        """Test that main TaskPanel initializes all components."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            with patch(
                "SquatchCut.core.session.detect_document_measurement_system",
                return_value="metric",
            ):
                with patch(
                    "SquatchCut.gui.taskpanel_main.session_state"
                ) as mock_session:
                    with patch("SquatchCut.gui.taskpanel_main.settings"):
                        # Mock session state methods
                        mock_session.get_sheet_size.return_value = (1220.0, 2440.0)
                        mock_session.get_measurement_system.return_value = "metric"
                        mock_session.get_panels.return_value = []
                        mock_session.get_last_layout.return_value = []
                        mock_session.get_nesting_stats.return_value = {}

                        panel = SquatchCutTaskPanel()

                        # Should have all widget sections
                        assert hasattr(panel, "input_widget")
                        assert hasattr(panel, "sheet_widget")
                        assert hasattr(panel, "nesting_widget")

                        # Should have action buttons (via nesting widget)
                        assert hasattr(panel.nesting_widget, "run_button")
                        assert hasattr(panel.nesting_widget, "preview_button")

                        # Should have required methods
                        assert hasattr(panel, "_on_csv_imported")
                        assert hasattr(panel, "_on_shapes_selected")
                        assert hasattr(panel, "_validate_readiness")


class TestRunNestingCommand:
    """Test the RunNestingCommand for non-shape-based nesting."""

    def test_command_initialization(self):
        """Test that RunNestingCommand initializes correctly."""
        command = RunNestingCommand()

        # Should have proper resources
        resources = command.GetResources()
        assert "MenuText" in resources
        assert "ToolTip" in resources
        assert "Pixmap" in resources
        assert resources["MenuText"] == "Nest Parts"

    def test_command_active_state(self):
        """Test command active state detection."""
        command = RunNestingCommand()

        # Should have IsActive method
        assert hasattr(command, "IsActive")
        assert callable(command.IsActive)

    def test_geometric_nesting_detection(self):
        """Test detection of when to use geometric nesting."""
        command = RunNestingCommand()

        # Should have the detection method
        assert hasattr(command, "_should_use_geometric_nesting")

        # Test with regular CSV data (should return False)
        csv_panels = [{"id": "panel1", "width": 100, "height": 200}]
        assert not command._should_use_geometric_nesting(csv_panels)

        # Test with shape-based data (should return True)
        shape_panels = [
            {"id": "shape1", "width": 100, "height": 200, "source": "freecad_shape"}
        ]
        assert command._should_use_geometric_nesting(shape_panels)

        # Test with mixed data (should return True if any shape-based)
        mixed_panels = [
            {"id": "panel1", "width": 100, "height": 200},
            {"id": "shape1", "width": 150, "height": 250, "source": "freecad_shape"},
        ]
        assert command._should_use_geometric_nesting(mixed_panels)

    def test_command_has_required_methods(self):
        """Test that command has all required methods."""
        command = RunNestingCommand()

        # Should have main execution method
        assert hasattr(command, "Activated")
        assert callable(command.Activated)

        # Should have geometric nesting method
        assert hasattr(command, "_run_geometric_nesting")
        assert callable(command._run_geometric_nesting)

        # Should have validation error handling
        assert hasattr(command, "_handle_validation_error")
        assert callable(command._handle_validation_error)


class TestGUISignalConnections:
    """Test that GUI components have proper signal connections."""

    def test_input_widget_signals(self):
        """Test that InputGroupWidget has required signals."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            prefs = Mock()
            widget = InputGroupWidget(prefs)

            # Should have CSV imported signal
            assert hasattr(widget, "csv_imported")

            # Should have data changed signal
            assert hasattr(widget, "data_changed")

            # Should have shapes selected signal (for shape-based nesting)
            assert hasattr(widget, "shapes_selected")

    def test_main_taskpanel_signal_handling(self):
        """Test that main TaskPanel handles signals correctly."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            with patch(
                "SquatchCut.core.session.detect_document_measurement_system",
                return_value="metric",
            ):
                with patch(
                    "SquatchCut.gui.taskpanel_main.session_state"
                ) as mock_session:
                    with patch("SquatchCut.gui.taskpanel_main.settings"):
                        # Mock session state methods
                        mock_session.get_sheet_size.return_value = (1220.0, 2440.0)
                        mock_session.get_measurement_system.return_value = "metric"
                        mock_session.get_panels.return_value = []
                        mock_session.get_last_layout.return_value = []
                        mock_session.get_nesting_stats.return_value = {}

                        panel = SquatchCutTaskPanel()

                        # Should have signal handlers
                        assert hasattr(panel, "_on_csv_imported")
                        assert hasattr(panel, "_on_shapes_selected")
                        assert hasattr(panel, "_on_data_changed")


class TestGUIValidationState:
    """Test GUI validation state management."""

    def test_validation_state_with_no_data(self):
        """Test validation state when no data is loaded."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            with patch(
                "SquatchCut.core.session.detect_document_measurement_system",
                return_value="metric",
            ):
                with patch(
                    "SquatchCut.gui.taskpanel_main.session_state"
                ) as mock_session:
                    with patch("SquatchCut.gui.taskpanel_main.settings"):
                        # Mock session state methods - no data
                        mock_session.get_sheet_size.return_value = (1220.0, 2440.0)
                        mock_session.get_measurement_system.return_value = "metric"
                        mock_session.get_panels.return_value = []  # No panels
                        mock_session.get_last_layout.return_value = []
                        mock_session.get_nesting_stats.return_value = {}

                        panel = SquatchCutTaskPanel()

                        # Should indicate no CSV data
                        assert not panel.has_csv_data

    def test_validation_state_with_csv_data(self):
        """Test validation state when CSV data is loaded."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            with patch(
                "SquatchCut.core.session.detect_document_measurement_system",
                return_value="metric",
            ):
                with patch(
                    "SquatchCut.gui.taskpanel_main.session_state"
                ) as mock_session:
                    with patch("SquatchCut.gui.taskpanel_main.settings"):
                        # Mock session state methods - with data
                        mock_session.get_sheet_size.return_value = (1220.0, 2440.0)
                        mock_session.get_measurement_system.return_value = "metric"
                        mock_session.get_panels.return_value = [
                            {"id": "panel1", "width": 100, "height": 200}
                        ]
                        mock_session.get_last_layout.return_value = []
                        mock_session.get_nesting_stats.return_value = {}

                        panel = SquatchCutTaskPanel()

                        # Trigger data change detection
                        panel._on_data_changed()

                        # Should indicate CSV data is present
                        assert panel.has_csv_data


class TestGUIWorkflowIntegration:
    """Test complete GUI workflow integration."""

    def test_csv_to_nesting_workflow_components(self):
        """Test that all components needed for CSV to nesting workflow exist."""
        # Test that we can create all the components needed for the workflow
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            with patch(
                "SquatchCut.core.session.detect_document_measurement_system",
                return_value="metric",
            ):
                with patch(
                    "SquatchCut.gui.taskpanel_main.session_state"
                ) as mock_session:
                    with patch("SquatchCut.gui.taskpanel_main.settings"):
                        # Mock session state
                        mock_session.get_sheet_size.return_value = (1220.0, 2440.0)
                        mock_session.get_measurement_system.return_value = "metric"
                        mock_session.get_panels.return_value = []
                        mock_session.get_last_layout.return_value = []
                        mock_session.get_nesting_stats.return_value = {}

                        # Create main panel
                        panel = SquatchCutTaskPanel()

                        # Create nesting command
                        command = RunNestingCommand()

                        # Verify components exist and are properly connected
                        assert panel.input_widget is not None
                        assert panel.sheet_widget is not None
                        assert panel.nesting_widget is not None
                        assert command.GetResources() is not None

                        # Verify the workflow methods exist
                        assert hasattr(panel, "_validate_readiness")
                        assert hasattr(command, "_should_use_geometric_nesting")

    def test_shape_to_nesting_workflow_components(self):
        """Test that all components needed for shape-based nesting workflow exist."""
        with patch("SquatchCut.core.preferences.SquatchCutPreferences"):
            prefs = Mock()

            # Input widget should support shape selection
            input_widget = InputGroupWidget(prefs)
            assert hasattr(input_widget, "select_shapes_button")
            assert hasattr(input_widget, "_select_shapes")
            assert hasattr(input_widget, "shapes_selected")

            # Command should support geometric nesting
            command = RunNestingCommand()
            assert hasattr(command, "_should_use_geometric_nesting")
            assert hasattr(command, "_run_geometric_nesting")
