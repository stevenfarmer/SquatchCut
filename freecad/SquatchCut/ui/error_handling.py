"""Standardized error handling and messaging for SquatchCut."""

import traceback

from SquatchCut.core import logger
from SquatchCut.freecad_integration import Gui
from SquatchCut.gui.qt_compat import QtWidgets


class SquatchCutError(Exception):
    """Base exception for SquatchCut-specific errors."""

    def __init__(
        self,
        message: str,
        details: str | None = None,
        user_action: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.details = details
        self.user_action = user_action


class ValidationError(SquatchCutError):
    """Error for validation failures (user input, data validation, etc.)."""

    pass


class ProcessingError(SquatchCutError):
    """Error for processing failures (nesting, export, etc.)."""

    pass


class ConfigurationError(SquatchCutError):
    """Error for configuration issues (missing settings, invalid preferences, etc.)."""

    pass


def show_error_dialog(
    title: str,
    message: str,
    details: str | None = None,
    user_action: str | None = None,
    parent: QtWidgets.QWidget | None = None,
) -> None:
    """Show a standardized error dialog."""
    if parent is None and Gui is not None:
        try:
            parent = Gui.getMainWindow()
        except Exception:
            pass

    msg_box = QtWidgets.QMessageBox(parent)
    msg_box.setWindowTitle(f"SquatchCut - {title}")
    msg_box.setIcon(QtWidgets.QMessageBox.Critical)

    # Main message
    full_message = message

    # Add user action if provided
    if user_action:
        full_message += f"\n\n{user_action}"

    msg_box.setText(full_message)

    # Add details if provided
    if details:
        msg_box.setDetailedText(details)

    msg_box.exec_()


def show_warning_dialog(
    title: str,
    message: str,
    details: str | None = None,
    user_action: str | None = None,
    parent: QtWidgets.QWidget | None = None,
) -> None:
    """Show a standardized warning dialog."""
    if parent is None and Gui is not None:
        try:
            parent = Gui.getMainWindow()
        except Exception:
            pass

    msg_box = QtWidgets.QMessageBox(parent)
    msg_box.setWindowTitle(f"SquatchCut - {title}")
    msg_box.setIcon(QtWidgets.QMessageBox.Warning)

    # Main message
    full_message = message

    # Add user action if provided
    if user_action:
        full_message += f"\n\n{user_action}"

    msg_box.setText(full_message)

    # Add details if provided
    if details:
        msg_box.setDetailedText(details)

    msg_box.exec_()


def show_info_dialog(
    title: str,
    message: str,
    details: str | None = None,
    parent: QtWidgets.QWidget | None = None,
) -> None:
    """Show a standardized information dialog."""
    if parent is None and Gui is not None:
        try:
            parent = Gui.getMainWindow()
        except Exception:
            pass

    msg_box = QtWidgets.QMessageBox(parent)
    msg_box.setWindowTitle(f"SquatchCut - {title}")
    msg_box.setIcon(QtWidgets.QMessageBox.Information)
    msg_box.setText(message)

    # Add details if provided
    if details:
        msg_box.setDetailedText(details)

    msg_box.exec_()


def handle_command_error(
    command_name: str,
    error: Exception,
    user_message: str | None = None,
    user_action: str | None = None,
) -> None:
    """Standardized error handling for FreeCAD commands."""
    # Log the full error with traceback
    logger.error(f"Error in {command_name}: {error}")
    logger.debug(traceback.format_exc())

    # Determine user-friendly message
    if isinstance(error, SquatchCutError):
        title = "Operation Failed"
        message = error.message
        details = error.details
        action = error.user_action or user_action
    else:
        title = "Unexpected Error"
        message = user_message or f"An unexpected error occurred in {command_name}."
        details = str(error)
        action = (
            user_action
            or "Please check the Report View for more details and try again."
        )

    show_error_dialog(title, message, details, action)


def handle_validation_error(
    field_name: str, value: str, expected: str, user_action: str | None = None
) -> None:
    """Handle validation errors with standardized messaging."""
    message = f"Invalid value for {field_name}: '{value}'"
    details = f"Expected: {expected}"
    action = user_action or f"Please correct the {field_name} and try again."

    show_error_dialog("Validation Error", message, details, action)


def confirm_destructive_action(
    title: str,
    message: str,
    details: str | None = None,
    parent: QtWidgets.QWidget | None = None,
) -> bool:
    """Show a confirmation dialog for destructive actions."""
    if parent is None and Gui is not None:
        try:
            parent = Gui.getMainWindow()
        except Exception:
            pass

    msg_box = QtWidgets.QMessageBox(parent)
    msg_box.setWindowTitle(f"SquatchCut - {title}")
    msg_box.setIcon(QtWidgets.QMessageBox.Question)
    msg_box.setText(message)

    if details:
        msg_box.setDetailedText(details)

    msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    msg_box.setDefaultButton(QtWidgets.QMessageBox.No)

    return msg_box.exec_() == QtWidgets.QMessageBox.Yes


# Common error messages and actions
class ErrorMessages:
    """Common error messages and user actions."""

    NO_DOCUMENT = "No active document found."
    NO_DOCUMENT_ACTION = "Please create or open a FreeCAD document and try again."

    NO_PANELS = "No panels are loaded."
    NO_PANELS_ACTION = "Please import a CSV file with panel definitions first."

    NO_NESTING = "No nesting layout found."
    NO_NESTING_ACTION = "Please run the nesting algorithm first."

    INVALID_SHEET_SIZE = "Invalid sheet size configuration."
    INVALID_SHEET_SIZE_ACTION = "Please check your sheet dimensions in the settings."

    FILE_NOT_FOUND = "The specified file could not be found."
    FILE_NOT_FOUND_ACTION = "Please check the file path and try again."

    EXPORT_FAILED = "Export operation failed."
    EXPORT_FAILED_ACTION = "Please check the destination path and file permissions."

    IMPORT_FAILED = "Import operation failed."
    IMPORT_FAILED_ACTION = "Please check the file format and content."
