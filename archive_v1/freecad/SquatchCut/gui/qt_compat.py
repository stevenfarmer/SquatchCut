"""
Lightweight Qt compatibility layer for SquatchCut GUI modules.

This allows GUI modules to be imported in headless/test environments where
PySide/PySide2 (or FreeCAD) may not be installed by providing minimal stubs.
"""

try:
    from PySide import QtCore, QtGui, QtWidgets  # type: ignore
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    except ImportError:

        class _Signal:
            def __init__(self, *args, **kwargs):
                pass

            def connect(self, *args, **kwargs):
                return None

            def emit(self, *args, **kwargs):
                pass

        class _Widget:
            # QDialog constants
            Accepted = 1
            Rejected = 0

            def __init__(self, *args, **kwargs):
                self._signals_blocked = False
                self._visible = True
                self._tool_tip = ""

            def blockSignals(self, value: bool):
                self._signals_blocked = bool(value)

            def setVisible(self, visible: bool):
                self._visible = bool(visible)

            def isVisible(self):
                return self._visible

            def show(self):
                self.setVisible(True)

            def hide(self):
                self.setVisible(False)

            def setToolTip(self, text: str):
                self._tool_tip = str(text)

            def toolTip(self):
                return self._tool_tip

            def setWindowTitle(self, title: str):
                self._window_title = str(title)

            def windowTitle(self):
                return getattr(self, "_window_title", "")

            @staticmethod
            def information(*args, **kwargs):
                return None

            @staticmethod
            def getItem(*args, **kwargs):
                return ("", True)

            def setLabelText(self, text: str):
                self._label_text = str(text)

            def labelText(self):
                return getattr(self, "_label_text", "")

            def setIcon(self, icon):
                self._icon = icon

            def icon(self):
                return getattr(self, "_icon", None)

        class _DummyQtEnum:
            Checked = 2
            Unchecked = 0
            TextSelectableByMouse = 1

        class _Label(_Widget):
            def __init__(self, text: str = ""):
                super().__init__()
                self._text = text

            def setText(self, text: str):
                self._text = text

            def text(self):
                return self._text

            def setStyleSheet(self, *_):
                return None

            def setTextInteractionFlags(self, *_):
                return None

        class _LineEdit(_Widget):
            textChanged = _Signal()

            def __init__(self):
                super().__init__()
                self._text = ""

            def setText(self, text: str):
                self._text = str(text)

            def text(self):
                return self._text

            def clear(self):
                self._text = ""

            def setStyleSheet(self, *_):
                return None

        class _ComboBox(_Widget):
            currentIndexChanged = _Signal()
            stateChanged = _Signal()

            def __init__(self):
                super().__init__()
                self._items = []
                self._data = []
                self._index = 0

            def addItem(self, label: str, userData=None):
                self._items.append(label)
                self._data.append(userData)

            def addItems(self, items):
                for item in items:
                    self.addItem(item)

            def clear(self):
                self._items = []
                self._data = []
                self._index = 0

            def setCurrentIndex(self, index: int):
                self._index = max(0, min(index, len(self._items) - 1))

            def currentIndex(self):
                return self._index

            def currentData(self):
                if 0 <= self._index < len(self._data):
                    return self._data[self._index]
                return None

            def findData(self, value):
                try:
                    return self._data.index(value)
                except ValueError:
                    return -1

        class _CheckBox(_Widget):
            stateChanged = _Signal()
            toggled = _Signal()

            def __init__(self, text: str = ""):
                super().__init__()
                self._checked = False
                self._text = text

            def setChecked(self, value: bool):
                self._checked = bool(value)

            def isChecked(self):
                return self._checked

        class _PushButton(_Widget):
            clicked = _Signal()

            def __init__(self, text: str = ""):
                super().__init__()
                self._text = text
                self._checkable = False

            def setText(self, text: str):
                self._text = text

            def text(self):
                return self._text

            def setFlat(self, *_):
                return None

            def setCheckable(self, value: bool):
                self._checkable = bool(value)

            def setAutoRaise(self, *_):
                return None

            def setEnabled(self, value: bool):
                self._enabled = bool(value)

            def isEnabled(self):
                return getattr(self, "_enabled", True)

            def setChecked(self, value: bool):
                self._checked = bool(value)

            def isChecked(self):
                return getattr(self, "_checked", False)

        class _Layout:
            def __init__(self, *args, **kwargs):
                pass

            def addWidget(self, *args, **kwargs):
                return None

            def addLayout(self, *args, **kwargs):
                return None

            def addRow(self, *args, **kwargs):
                return None

            def addStretch(self, *args, **kwargs):
                return None

            def setContentsMargins(self, *args, **kwargs):
                return None

            def setSpacing(self, *args, **kwargs):
                return None

            def setColumnStretch(self, *args, **kwargs):
                return None

        class _GroupBox(_Widget):
            def __init__(self, *args, **kwargs):
                super().__init__()

        class _TableWidgetItem:
            def __init__(self, text=""):
                self._text = text

            def setFlags(self, *_):
                return None

            def row(self):
                return 0

            def column(self):
                return 0

            def text(self):
                return self._text

        class _Header:
            def setStretchLastSection(self, *_):
                return None

            def setSectionResizeMode(self, *_):
                return None

        class _TableWidget(_Widget):
            def __init__(self):
                super().__init__()
                self._row_count = 0
                self._col_count = 0
                self._items = {}

            def setColumnCount(self, count: int):
                self._col_count = count

            def setRowCount(self, count: int):
                self._row_count = count

            def setHorizontalHeaderLabels(self, *_):
                return None

            def horizontalHeader(self):
                return _Header()

            def setEditTriggers(self, *_):
                return None

            def setSelectionBehavior(self, *_):
                return None

            def setSelectionMode(self, *_):
                return None

            def setItem(self, row, col, item):
                self._items[(row, col)] = item

            def resizeColumnsToContents(self):
                return None

            def setSizePolicy(self, *_):
                return None

        class _DummyAbstractItemView:
            NoEditTriggers = 0
            SelectRows = 1
            SingleSelection = 2

        class _DummySizePolicy:
            Expanding = 1
            Preferred = 2

        class _DummyQHeaderView:
            Stretch = 1
            ResizeToContents = 2

        class _FileDialog(_Widget):
            @staticmethod
            def getOpenFileName(*args, **kwargs):
                return ("", "")

            @staticmethod
            def getSaveFileName(*args, **kwargs):
                return ("", "")

        class _MessageBox(_Widget):
            @staticmethod
            def information(*args, **kwargs):
                return None

            @staticmethod
            def warning(*args, **kwargs):
                return None

            @staticmethod
            def critical(*args, **kwargs):
                return None

            def setIcon(self, icon):
                self._icon = icon

        class _DummyQtModule:
            Qt = _DummyQtEnum
            QDialog = _Widget
            QWidget = _Widget
            QMessageBox = _MessageBox
            QFileDialog = _FileDialog
            QDialogButtonBox = _Widget
            QVBoxLayout = _Layout
            QHBoxLayout = _Layout
            QFormLayout = _Layout
            QPushButton = _PushButton
            QToolButton = _PushButton
            QLabel = _Label
            QListWidget = _Widget
            QLineEdit = _LineEdit
            QComboBox = _ComboBox
            QDoubleSpinBox = _Widget
            QCheckBox = _CheckBox
            QGroupBox = _GroupBox
            QGridLayout = _Layout
            QAbstractItemView = _DummyAbstractItemView
            QTableWidget = _TableWidget
            QTableWidgetItem = _TableWidgetItem
            Signal = _Signal
            QSizePolicy = _DummySizePolicy
            QHeaderView = _DummyQHeaderView

            def __getattr__(self, name):
                return _Widget

        QtWidgets = _DummyQtModule()
        QtCore = _DummyQtModule()
        QtGui = _DummyQtModule()
