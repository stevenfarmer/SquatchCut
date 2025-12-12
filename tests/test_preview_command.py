"""Tests for the PreviewNestingCommand."""

from SquatchCut.gui.commands.cmd_run_nesting import PreviewNestingCommand


class TestPreviewNestingCommand:
    """Test the preview nesting command functionality."""

    def test_command_resources(self):
        """Test command metadata."""
        cmd = PreviewNestingCommand()
        resources = cmd.GetResources()

        assert "Preview Nesting" in resources["MenuText"]
        assert "preview" in resources["ToolTip"].lower()

    def test_command_is_active_with_document(self):
        """Test that command is active when document exists."""
        from unittest.mock import patch, MagicMock

        cmd = PreviewNestingCommand()

        # Mock App and Gui availability
        with (
            patch("SquatchCut.gui.commands.cmd_run_nesting.App") as mock_app,
            patch("SquatchCut.gui.commands.cmd_run_nesting.Gui") as mock_gui,
        ):

            # No active document
            mock_app.ActiveDocument = None
            mock_gui.return_value = MagicMock()
            assert not cmd.IsActive()

            # With active document
            mock_app.ActiveDocument = MagicMock()
            assert cmd.IsActive()
