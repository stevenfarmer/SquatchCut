"""Progress indicator utilities for SquatchCut operations."""


from SquatchCut.gui.qt_compat import QtWidgets


class ProgressDialog:
    """Simple progress dialog for long-running operations."""

    def __init__(
        self, title: str = "SquatchCut", parent: QtWidgets.QWidget | None = None
    ):
        self.dialog = QtWidgets.QProgressDialog(parent)
        self.dialog.setWindowTitle(title)
        self.dialog.setModal(True)
        self.dialog.setMinimumDuration(500)  # Show after 500ms
        self.dialog.setCancelButton(None)  # No cancel for now
        self.dialog.setAutoClose(True)
        self.dialog.setAutoReset(True)

    def set_range(self, minimum: int, maximum: int) -> None:
        """Set the progress range."""
        self.dialog.setRange(minimum, maximum)

    def set_value(self, value: int) -> None:
        """Update progress value."""
        self.dialog.setValue(value)
        QtWidgets.QApplication.processEvents()  # Keep UI responsive

    def set_label(self, text: str) -> None:
        """Set the progress label text."""
        self.dialog.setLabelText(text)

    def close(self) -> None:
        """Close the progress dialog."""
        self.dialog.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class SimpleProgressContext:
    """Simple progress context for operations without specific progress tracking."""

    def __init__(self, message: str = "Processing...", title: str = "SquatchCut"):
        self.message = message
        self.title = title
        self.dialog = None

    def __enter__(self):
        """Show indeterminate progress."""
        self.dialog = QtWidgets.QProgressDialog()
        self.dialog.setWindowTitle(self.title)
        self.dialog.setLabelText(self.message)
        self.dialog.setRange(0, 0)  # Indeterminate progress
        self.dialog.setModal(True)
        self.dialog.setCancelButton(None)
        self.dialog.setMinimumDuration(500)
        self.dialog.show()
        QtWidgets.QApplication.processEvents()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Hide progress."""
        if self.dialog:
            self.dialog.close()
            self.dialog = None
