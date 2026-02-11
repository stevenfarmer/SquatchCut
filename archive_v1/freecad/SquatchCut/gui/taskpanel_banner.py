from __future__ import annotations

from SquatchCut.gui.qt_compat import QtWidgets


class SheetWarningBanner(QtWidgets.QFrame):
    """Banner that displays warning text about unsupported sheet combinations."""

    def __init__(self) -> None:
        super().__init__()
        if hasattr(self, "setObjectName"):
            self.setObjectName("sheet_warning_banner")
        if hasattr(self, "setFrameShape"):
            self.setFrameShape(QtWidgets.QFrame.StyledPanel)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(2)

        self.label = QtWidgets.QLabel("")
        if hasattr(self.label, "setWordWrap"):
            self.label.setWordWrap(True)
        self.label.setStyleSheet("color: #b26b00; font-size: 11px; padding: 2px;")
        layout.addWidget(self.label)

        self.setVisible(False)

    def update_warning(self, show: bool, message: str | None = None) -> None:
        """Toggle visibility and update banner text."""
        if show and message:
            self.label.setText(message)
        elif not show:
            self.label.setText("")
        self.setVisible(show)
