"""Tests for progress indicator functionality."""

from unittest.mock import MagicMock, patch

from SquatchCut.ui.progress import ProgressDialog, SimpleProgressContext


def test_progress_dialog_basic_functionality():
    """Test basic ProgressDialog functionality."""
    with patch("SquatchCut.ui.progress.QtWidgets") as mock_qt:
        mock_dialog = MagicMock()
        mock_qt.QProgressDialog.return_value = mock_dialog

        progress = ProgressDialog("Test Title")

        # Test initialization
        mock_qt.QProgressDialog.assert_called_once_with(None)
        mock_dialog.setWindowTitle.assert_called_with("Test Title")
        mock_dialog.setModal.assert_called_with(True)
        mock_dialog.setMinimumDuration.assert_called_with(500)
        mock_dialog.setCancelButton.assert_called_with(None)

        # Test range setting
        progress.set_range(0, 100)
        mock_dialog.setRange.assert_called_with(0, 100)

        # Test value setting
        progress.set_value(50)
        mock_dialog.setValue.assert_called_with(50)

        # Test label setting
        progress.set_label("Processing...")
        mock_dialog.setLabelText.assert_called_with("Processing...")

        # Test close
        progress.close()
        mock_dialog.close.assert_called_once()


def test_progress_dialog_context_manager():
    """Test ProgressDialog as context manager."""
    with patch("SquatchCut.ui.progress.QtWidgets") as mock_qt:
        mock_dialog = MagicMock()
        mock_qt.QProgressDialog.return_value = mock_dialog

        with ProgressDialog("Test") as progress:
            assert progress is not None
            progress.set_value(25)
            mock_dialog.setValue.assert_called_with(25)

        # Should close automatically
        mock_dialog.close.assert_called_once()


def test_simple_progress_context():
    """Test SimpleProgressContext functionality."""
    with patch("SquatchCut.ui.progress.QtWidgets") as mock_qt:
        mock_dialog = MagicMock()
        mock_qt.QProgressDialog.return_value = mock_dialog

        with SimpleProgressContext("Loading...", "Test App"):
            # Dialog should be created and shown
            mock_qt.QProgressDialog.assert_called_once()
            mock_dialog.setWindowTitle.assert_called_with("Test App")
            mock_dialog.setLabelText.assert_called_with("Loading...")
            mock_dialog.setRange.assert_called_with(0, 0)  # Indeterminate
            mock_dialog.setModal.assert_called_with(True)
            mock_dialog.setCancelButton.assert_called_with(None)
            mock_dialog.show.assert_called_once()

        # Should close automatically
        mock_dialog.close.assert_called_once()


def test_simple_progress_context_with_exception():
    """Test SimpleProgressContext handles exceptions properly."""
    with patch("SquatchCut.ui.progress.QtWidgets") as mock_qt:
        mock_dialog = MagicMock()
        mock_qt.QProgressDialog.return_value = mock_dialog

        try:
            with SimpleProgressContext("Loading...", "Test App"):
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected

        # Should still close even with exception
        mock_dialog.close.assert_called_once()


def test_progress_dialog_with_parent():
    """Test ProgressDialog with parent widget."""
    with patch("SquatchCut.ui.progress.QtWidgets") as mock_qt:
        mock_dialog = MagicMock()
        mock_qt.QProgressDialog.return_value = mock_dialog
        mock_parent = MagicMock()

        ProgressDialog("Test", parent=mock_parent)

        mock_qt.QProgressDialog.assert_called_once_with(mock_parent)


def test_simple_progress_context_defaults():
    """Test SimpleProgressContext with default parameters."""
    with patch("SquatchCut.ui.progress.QtWidgets") as mock_qt:
        mock_dialog = MagicMock()
        mock_qt.QProgressDialog.return_value = mock_dialog

        with SimpleProgressContext():
            mock_dialog.setWindowTitle.assert_called_with("SquatchCut")
            mock_dialog.setLabelText.assert_called_with("Processing...")
