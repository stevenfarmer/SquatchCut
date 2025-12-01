"""
Lightweight Qt compatibility layer for SquatchCut GUI modules.

This allows GUI modules to be imported in headless/test environments where
PySide/PySide2 (or FreeCAD) may not be installed by providing minimal stubs.
"""

try:
    from PySide import QtWidgets, QtCore, QtGui  # type: ignore
except ImportError:
    try:
        from PySide2 import QtWidgets, QtCore, QtGui  # type: ignore
    except ImportError:
        class _DummyQtObject:
            def __init__(self, *args, **kwargs):
                pass

            def __call__(self, *args, **kwargs):
                return self.__class__()

            def __getattr__(self, name):
                return self.__class__

        class _DummyQtEnum:
            Checked = 2
            Unchecked = 0
            TextSelectableByMouse = 1

        class _DummyAbstractItemView(_DummyQtObject):
            NoEditTriggers = 0
            SelectRows = 1
            SingleSelection = 2

        class _DummyQtModule:
            Qt = _DummyQtEnum
            QDialog = _DummyQtObject
            QWidget = _DummyQtObject
            QMessageBox = _DummyQtObject
            QFileDialog = _DummyQtObject
            QDialogButtonBox = _DummyQtObject
            QVBoxLayout = _DummyQtObject
            QHBoxLayout = _DummyQtObject
            QFormLayout = _DummyQtObject
            QPushButton = _DummyQtObject
            QLabel = _DummyQtObject
            QListWidget = _DummyQtObject
            QLineEdit = _DummyQtObject
            QComboBox = _DummyQtObject
            QDoubleSpinBox = _DummyQtObject
            QCheckBox = _DummyQtObject
            QGroupBox = _DummyQtObject
            QGridLayout = _DummyQtObject
            QAbstractItemView = _DummyAbstractItemView

            def __getattr__(self, name):
                return _DummyQtObject

        QtWidgets = _DummyQtModule()
        QtCore = _DummyQtModule()
        QtGui = _DummyQtModule()
