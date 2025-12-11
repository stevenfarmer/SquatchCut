from SquatchCut.gui.qt_compat import QtWidgets
from SquatchCut.gui.taskpanel_main import SquatchCutTaskPanel


def test_taskpanel_layout_sections_are_stacked_widgets():
    panel = SquatchCutTaskPanel()
    for attr in ("view_controls_container", "visibility_controls_container", "export_controls_container"):
        container = getattr(panel, attr, None)
        assert container is not None
        assert isinstance(container, QtWidgets.QWidget)
    assert panel.output_group is not None


def test_taskpanel_builds_status_label_once():
    panel = SquatchCutTaskPanel()
    assert panel.form is not None
    text_fn = getattr(panel.status_label, "text", None)
    status_text = text_fn() if callable(text_fn) else ""
    assert status_text.startswith("Status:")
