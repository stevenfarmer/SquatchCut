"""Keyboard shortcuts for SquatchCut operations."""


from typing import Optional

from SquatchCut.freecad_integration import Gui
from SquatchCut.gui.qt_compat import QtCore, QtWidgets


class SquatchCutShortcuts:
    """Manages keyboard shortcuts for SquatchCut commands."""

    def __init__(self):
        self.shortcuts: dict[str, QtWidgets.QShortcut] = {}
        self.main_window = None

    def setup_shortcuts(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """Set up keyboard shortcuts for SquatchCut commands."""
        if parent is None and Gui is not None:
            try:
                parent = Gui.getMainWindow()
            except Exception:
                return

        if parent is None:
            return

        self.main_window = parent

        # Define shortcuts
        shortcuts_config = {
            "Ctrl+I": "SquatchCut_ImportCSV",  # Import CSV
            "Ctrl+R": "SquatchCut_RunNesting",  # Run Nesting
            "Ctrl+E": "SquatchCut_ExportCutlist",  # Export Cutlist
            "Ctrl+Shift+S": "SquatchCut_ShowTaskPanel",  # Show Settings
            "F5": "SquatchCut_RunNesting",  # Alternative for Run Nesting
            "Ctrl+T": "SquatchCut_ToggleSourcePanels",  # Toggle Source Visibility
            "Ctrl+Shift+R": "SquatchCut_ResetView",  # Reset View
        }

        # Create shortcuts
        for key_sequence, command_name in shortcuts_config.items():
            try:
                shortcut = QtWidgets.QShortcut(
                    QtCore.QKeySequence(key_sequence), parent
                )
                shortcut.activated.connect(
                    lambda cmd=command_name: self._execute_command(cmd)
                )
                self.shortcuts[key_sequence] = shortcut
            except Exception:
                # Skip if shortcut creation fails
                continue

    def _execute_command(self, command_name: str) -> None:
        """Execute a FreeCAD command by name."""
        if Gui is not None:
            try:
                Gui.runCommand(command_name)
            except Exception:
                # Command might not be available or active
                pass

    def cleanup_shortcuts(self) -> None:
        """Clean up all registered shortcuts."""
        for shortcut in self.shortcuts.values():
            try:
                shortcut.setParent(None)
                shortcut.deleteLater()
            except Exception:
                pass
        self.shortcuts.clear()

    def get_shortcuts_help(self) -> str:
        """Return a formatted string describing available shortcuts."""
        help_text = "SquatchCut Keyboard Shortcuts:\n\n"
        shortcuts_help = {
            "Ctrl+I": "Import CSV file",
            "Ctrl+R / F5": "Run nesting algorithm",
            "Ctrl+E": "Export cutlist to CSV",
            "Ctrl+Shift+S": "Open SquatchCut settings",
            "Ctrl+T": "Toggle source panels visibility",
            "Ctrl+Shift+R": "Reset view to fit all objects",
        }

        for shortcut, description in shortcuts_help.items():
            help_text += f"  {shortcut:<15} - {description}\n"

        return help_text


# Global instance
_shortcuts_manager: Optional[SquatchCutShortcuts] = None


def get_shortcuts_manager() -> SquatchCutShortcuts:
    """Get the global shortcuts manager instance."""
    global _shortcuts_manager
    if _shortcuts_manager is None:
        _shortcuts_manager = SquatchCutShortcuts()
    return _shortcuts_manager


def setup_global_shortcuts() -> None:
    """Set up global SquatchCut keyboard shortcuts."""
    manager = get_shortcuts_manager()
    manager.setup_shortcuts()


def cleanup_global_shortcuts() -> None:
    """Clean up global SquatchCut keyboard shortcuts."""
    global _shortcuts_manager
    if _shortcuts_manager is not None:
        _shortcuts_manager.cleanup_shortcuts()
        _shortcuts_manager = None


def show_shortcuts_help() -> None:
    """Show a dialog with available keyboard shortcuts."""
    if Gui is None:
        return

    try:
        manager = get_shortcuts_manager()
        help_text = manager.get_shortcuts_help()

        msg_box = QtWidgets.QMessageBox(Gui.getMainWindow())
        msg_box.setWindowTitle("SquatchCut Keyboard Shortcuts")
        msg_box.setText(help_text)
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.exec_()
    except Exception:
        pass
