import FreeCADGui
from PySide2 import QtWidgets


def _parent_window():
    try:
        return FreeCADGui.getMainWindow()
    except Exception:
        return None


def show_error(message: str, title: str = "SquatchCut Error") -> None:
    parent = _parent_window()
    QtWidgets.QMessageBox.critical(parent, title, message)


def show_warning(message: str, title: str = "SquatchCut Warning") -> None:
    parent = _parent_window()
    QtWidgets.QMessageBox.warning(parent, title, message)


def show_info(message: str, title: str = "SquatchCut") -> None:
    parent = _parent_window()
    QtWidgets.QMessageBox.information(parent, title, message)
