"""Nesting control section for the SquatchCut TaskPanel."""

from __future__ import annotations

from SquatchCut.core import session_state
from SquatchCut.core import units as sc_units
from SquatchCut.gui.qt_compat import QtCore, QtWidgets


class NestingGroupWidget(QtWidgets.QGroupBox):
    """
    Widget handling optimization settings and Run/Preview controls.

    Signals:
        run_requested: Emitted when 'Run Nesting' is clicked.
        preview_requested: Emitted when 'Preview' is clicked.
        settings_changed: Emitted when optimization settings change.
    """

    run_requested = QtCore.Signal()
    preview_requested = QtCore.Signal()
    settings_changed = QtCore.Signal()

    def __init__(self, prefs, parent=None):
        super().__init__("Nesting", parent)
        self._prefs = prefs
        if hasattr(self, "setObjectName"):
            self.setObjectName("nesting_group_box")
        self._build_ui()

    def _build_ui(self) -> None:
        vbox = QtWidgets.QVBoxLayout(self)

        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItem("Material (minimize waste)", "material")
        self.mode_combo.addItem("Cuts (minimize number of cuts)", "cuts")
        self.mode_combo.setToolTip(
            "Material: prioritize yield. Cuts: row/column layout to approximate fewer saw cuts."
        )
        self.mode_combo.currentIndexChanged.connect(self._on_settings_changed)

        self.cut_mode_check = QtWidgets.QCheckBox("Cut-friendly layout")
        self.cut_mode_check.setToolTip(
            "Bias nesting toward woodshop-style rips/crosscuts instead of tight packing."
        )
        self.cut_mode_check.toggled.connect(self._on_settings_changed)

        self.kerf_width_label = QtWidgets.QLabel("Kerf width (mm):")
        self.kerf_width_edit = QtWidgets.QLineEdit()
        self.kerf_width_edit.setToolTip("Blade thickness used to maintain spacing between parts.")
        self.kerf_width_edit.textChanged.connect(self._on_settings_changed)

        form = QtWidgets.QFormLayout()
        form.addRow("Optimization:", self.mode_combo)
        form.addRow(self.cut_mode_check)
        form.addRow(self.kerf_width_label, self.kerf_width_edit)

        self.job_allow_rotation_check = QtWidgets.QCheckBox("Allow rotation for this job")
        self.job_allow_rotation_check.setToolTip(
            "Allow SquatchCut to rotate panels when nesting this job."
        )
        self.job_allow_rotation_check.toggled.connect(self._on_settings_changed)
        form.addRow(self.job_allow_rotation_check)
        vbox.addLayout(form)

        button_row = QtWidgets.QHBoxLayout()
        self.preview_button = QtWidgets.QPushButton("Preview")
        self.preview_button.setToolTip("Preview the nesting layout without leaving the task panel.")
        self.preview_button.clicked.connect(self.preview_requested.emit)

        self.run_button = QtWidgets.QPushButton("Run Nesting")
        self.run_button.setToolTip("Generate nested geometry in the active document.")
        self.run_button.clicked.connect(self.run_requested.emit)

        button_row.addWidget(self.preview_button)
        button_row.addWidget(self.run_button)
        button_row.addStretch(1)
        vbox.addLayout(button_row)

        self.set_run_enabled(False)

    def apply_state(self, state: dict) -> None:
        mode_idx = self.mode_combo.findData(state.get("mode", "material"))
        if mode_idx < 0:
            mode_idx = 0
        self.mode_combo.setCurrentIndex(mode_idx)

        nesting_mode = session_state.get_nesting_mode()
        self.cut_mode_check.setChecked(nesting_mode == "cut_friendly" or bool(state.get("cut_mode")))

        self.kerf_width_edit.setText(sc_units.format_length(state.get("kerf_width_mm", 3.0), state.get("measurement_system", "metric")))
        self.job_allow_rotation_check.setChecked(bool(state.get("job_allow_rotate", False)))

        self._update_unit_labels()

    def set_run_enabled(self, enabled: bool) -> None:
        self.preview_button.setEnabled(enabled)
        self.run_button.setEnabled(enabled)

    def _on_settings_changed(self) -> None:
        # Update session state immediately
        mode = self.mode_combo.currentData() or "material"
        session_state.set_optimization_mode(mode)
        session_state.set_nesting_mode("cut_friendly" if self.cut_mode_check.isChecked() else "pack")

        try:
            kw = sc_units.parse_length(self.kerf_width_edit.text(), session_state.get_measurement_system())
            if kw > 0:
                session_state.set_kerf_width_mm(kw)
        except Exception:
            pass

        rot = self.job_allow_rotation_check.isChecked()
        session_state.set_job_allow_rotate(rot)
        session_state.set_allowed_rotations_deg((0, 90) if rot else (0,))

        self.settings_changed.emit()

    def update_unit_labels(self) -> None:
        self._update_unit_labels()
        # Refresh kerf width field format
        val = session_state.get_kerf_width_mm()
        self.kerf_width_edit.setText(sc_units.format_length(val, session_state.get_measurement_system()))

    def _update_unit_labels(self) -> None:
        unit = sc_units.unit_label_for_system(session_state.get_measurement_system())
        self.kerf_width_label.setText(f"Kerf Width ({unit}):")
