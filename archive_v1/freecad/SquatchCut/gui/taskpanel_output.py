from __future__ import annotations

from SquatchCut.gui.qt_compat import QtWidgets


class TaskPanelOutputWidget(QtWidgets.QGroupBox):
    """Encapsulates the nested view, stats, and export controls."""

    def __init__(self) -> None:
        super().__init__("Output")
        if hasattr(self, "setObjectName"):
            self.setObjectName("output_group_box")
        self._build_ui()

    def _build_ui(self) -> None:
        vbox = QtWidgets.QVBoxLayout(self)

        self.view_controls_container = QtWidgets.QWidget()
        view_controls_layout = QtWidgets.QVBoxLayout(self.view_controls_container)
        view_controls_layout.setContentsMargins(0, 0, 0, 0)
        view_controls_layout.setSpacing(2)
        view_controls_layout.addWidget(QtWidgets.QLabel("View:"))

        self.btnViewSource = QtWidgets.QToolButton()
        self.btnViewSource.setText("Source")
        self.btnViewSource.setCheckable(True)
        self.btnViewSource.setAutoRaise(True)
        view_controls_layout.addWidget(self.btnViewSource)

        self.btnViewSheets = QtWidgets.QToolButton()
        self.btnViewSheets.setText("Nested")
        self.btnViewSheets.setCheckable(True)
        self.btnViewSheets.setAutoRaise(True)
        view_controls_layout.addWidget(self.btnViewSheets)

        vbox.addWidget(self.view_controls_container)

        self.visibility_controls_container = QtWidgets.QWidget()
        visibility_layout = QtWidgets.QVBoxLayout(self.visibility_controls_container)
        visibility_layout.setContentsMargins(0, 0, 0, 0)
        visibility_layout.setSpacing(2)
        self.show_sheet_check = QtWidgets.QCheckBox("Show sheet boundary")
        self.show_nested_check = QtWidgets.QCheckBox("Show nested parts")
        self.show_sheet_check.setChecked(True)
        self.show_nested_check.setChecked(True)
        visibility_layout.addWidget(self.show_sheet_check)
        visibility_layout.addWidget(self.show_nested_check)
        vbox.addWidget(self.visibility_controls_container)

        self.nesting_view_controls_container = QtWidgets.QWidget()
        nesting_view_layout = QtWidgets.QVBoxLayout(
            self.nesting_view_controls_container
        )
        nesting_view_layout.setContentsMargins(0, 0, 0, 0)
        nesting_view_layout.setSpacing(2)
        nesting_view_layout.addWidget(QtWidgets.QLabel("Nesting View:"))

        nesting_controls_row = QtWidgets.QHBoxLayout()
        nesting_controls_row.setContentsMargins(0, 0, 0, 0)
        nesting_controls_row.setSpacing(4)

        self.show_part_labels_check = QtWidgets.QCheckBox("Labels")
        self.show_part_labels_check.setToolTip("Show part ID labels on nested pieces")
        nesting_controls_row.addWidget(self.show_part_labels_check)

        self.simplified_view_check = QtWidgets.QCheckBox("Simple")
        self.simplified_view_check.setToolTip("Use simplified view for complex layouts")
        nesting_controls_row.addWidget(self.simplified_view_check)

        nesting_controls_row.addStretch()
        nesting_view_layout.addLayout(nesting_controls_row)
        vbox.addWidget(self.nesting_view_controls_container)

        self.show_source_button = QtWidgets.QPushButton("Show Source View")
        vbox.addWidget(self.show_source_button)

        stats_frame = QtWidgets.QFrame()
        stats_layout = QtWidgets.QFormLayout(stats_frame)
        self.mode_label = QtWidgets.QLabel("Mode: –")
        self.sheets_label = QtWidgets.QLabel("Sheets used: –")
        self.utilization_label = QtWidgets.QLabel("Utilization: –")
        self.cutcount_label = QtWidgets.QLabel("Estimated cuts: –")
        self.unplaced_label = QtWidgets.QLabel("Unplaced parts: –")
        self.stats_sheets_label = QtWidgets.QLabel("Number of sheets used: –")
        self.stats_complexity_label = QtWidgets.QLabel(
            "Estimated cut path complexity: –"
        )
        self.overlaps_label = QtWidgets.QLabel("Overlaps: –")
        self.sheet_utilization_label = QtWidgets.QLabel("Sheet utilization range: –")

        stats_layout.addRow("Mode:", self.mode_label)
        stats_layout.addRow("Sheets:", self.sheets_label)
        stats_layout.addRow("Utilization:", self.utilization_label)
        stats_layout.addRow("Sheet utilization:", self.sheet_utilization_label)
        stats_layout.addRow("Estimated cuts:", self.cutcount_label)
        stats_layout.addRow("Unplaced parts:", self.unplaced_label)
        stats_layout.addRow("Sheets used:", self.stats_sheets_label)
        stats_layout.addRow("Cut path complexity:", self.stats_complexity_label)
        stats_layout.addRow("Overlaps:", self.overlaps_label)
        vbox.addWidget(stats_frame)

        self.status_label = QtWidgets.QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: gray;")
        vbox.addWidget(self.status_label)

        self.export_controls_container = QtWidgets.QWidget()
        export_layout = QtWidgets.QVBoxLayout(self.export_controls_container)
        export_layout.setContentsMargins(0, 0, 0, 0)
        export_layout.setSpacing(4)

        self.export_format_combo = QtWidgets.QComboBox()
        self.export_format_combo.addItem("DXF", "dxf")
        self.export_format_combo.addItem("SVG", "svg")
        self.export_format_combo.addItem("Cut list CSV", "cutlist_csv")
        self.export_format_combo.addItem("Cut list instructions (text)", "cutlist_txt")

        self.export_button = QtWidgets.QPushButton("Export Layout")
        export_layout.addWidget(QtWidgets.QLabel("Export format:"))
        export_layout.addWidget(self.export_format_combo)
        self.include_labels_check = QtWidgets.QCheckBox("Include part labels")
        self.include_dimensions_check = QtWidgets.QCheckBox("Include dimensions")
        self.include_leader_lines_check = QtWidgets.QCheckBox("Include leader lines")
        export_layout.addWidget(self.include_labels_check)
        export_layout.addWidget(self.include_dimensions_check)
        export_layout.addWidget(self.include_leader_lines_check)
        export_layout.addWidget(self.export_button)
        vbox.addWidget(self.export_controls_container)

        self.btnExportCutlist = QtWidgets.QPushButton("Cutlist CSV")
        vbox.addWidget(self.btnExportCutlist)

    def set_status(self, message: str) -> None:
        self.status_label.setText(f"Status: {message}")
