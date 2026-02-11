import pytest
from SquatchCut.gui import icons
from SquatchCut.gui.qt_compat import QtWidgets
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel


def test_icon_helper_resolves_all_keys():
    for key in icons.ICON_KEYS:
        icon = icons.get_icon(key)
        assert icon is not None


def test_parts_table_header_modes():
    panel = SquatchCutTaskPanel()
    header = panel.input_widget.parts_table.horizontalHeader()
    header_view_cls = getattr(QtWidgets, "QHeaderView", None)
    section_resize = getattr(header, "sectionResizeMode", None)
    if header_view_cls is None or section_resize is None:
        pytest.skip("Qt header view not available in this test environment.")

    stretch_mode = getattr(header_view_cls, "Stretch", None)
    resize_mode = getattr(header_view_cls, "ResizeToContents", None)
    assert stretch_mode is not None
    assert resize_mode is not None
    assert section_resize(0) == stretch_mode
    for column in range(1, panel.input_widget.parts_table.columnCount()):
        mode = section_resize(column)
        assert mode in (resize_mode, stretch_mode)
