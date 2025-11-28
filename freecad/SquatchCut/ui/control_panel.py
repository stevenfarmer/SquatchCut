import os

import FreeCAD
import FreeCADGui
from PySide2 import QtWidgets

from SquatchCut.core import session, session_state
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.ui.messages import show_info, show_error
from SquatchCut.gui.commands.cmd_import_csv import run_csv_import
from SquatchCut.gui.commands import cmd_run_nesting


class SquatchCutControlPanel:
    """
    Unified control panel for SquatchCut:

    - Sheet size (mm)
    - Cutting parameters (kerf, gap)
    - Default rotation behavior
    - CSV path selection
    - Import + Nest button
    """

    def __init__(self, doc=None):
        if doc is None:
            doc = FreeCAD.ActiveDocument
        self.doc = doc

        if self.doc is not None:
            session.sync_state_from_doc(self.doc)

        # Build root widget + layout
        self.form = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(self.form)

        # Fetch current state
        sheet_w, sheet_h = session_state.get_sheet_size()
        kerf_mm = session_state.get_kerf_mm()
        gap_mm = session_state.get_gap_mm()
        default_allow = session_state.get_default_allow_rotate()

        if sheet_w is None:
            sheet_w = 1220.0
        if sheet_h is None:
            sheet_h = 2440.0

        # ---------------- Sheet Size group ----------------
        sheet_group = QtWidgets.QGroupBox("Sheet Size (mm)")
        sheet_layout = QtWidgets.QFormLayout(sheet_group)

        self.sheet_width_spin = QtWidgets.QDoubleSpinBox()
        self.sheet_width_spin.setRange(1.0, 100000.0)
        self.sheet_width_spin.setDecimals(1)
        self.sheet_width_spin.setSingleStep(10.0)
        self.sheet_width_spin.setValue(sheet_w)

        self.sheet_height_spin = QtWidgets.QDoubleSpinBox()
        self.sheet_height_spin.setRange(1.0, 100000.0)
        self.sheet_height_spin.setDecimals(1)
        self.sheet_height_spin.setSingleStep(10.0)
        self.sheet_height_spin.setValue(sheet_h)

        sheet_layout.addRow("Width:", self.sheet_width_spin)
        sheet_layout.addRow("Height:", self.sheet_height_spin)

        main_layout.addWidget(sheet_group)

        # ---------------- Cutting Parameters group ----------------
        cut_group = QtWidgets.QGroupBox("Cutting Parameters")
        cut_layout = QtWidgets.QFormLayout(cut_group)

        self.kerf_spin = QtWidgets.QDoubleSpinBox()
        self.kerf_spin.setRange(0.0, 100.0)
        self.kerf_spin.setDecimals(2)
        self.kerf_spin.setSingleStep(0.1)
        self.kerf_spin.setValue(kerf_mm)

        self.gap_spin = QtWidgets.QDoubleSpinBox()
        self.gap_spin.setRange(0.0, 100.0)
        self.gap_spin.setDecimals(2)
        self.gap_spin.setSingleStep(0.1)
        self.gap_spin.setValue(gap_mm)

        cut_layout.addRow("Kerf (mm):", self.kerf_spin)
        cut_layout.addRow("Additional gap (mm):", self.gap_spin)

        main_layout.addWidget(cut_group)

        # ---------------- Rotation group ----------------
        rot_group = QtWidgets.QGroupBox("Rotation")
        rot_layout = QtWidgets.QVBoxLayout(rot_group)

        self.default_rotate_check = QtWidgets.QCheckBox("Allow rotation by default")
        self.default_rotate_check.setChecked(default_allow)
        rot_layout.addWidget(self.default_rotate_check)

        rot_helper = QtWidgets.QLabel(
            "If a CSV does not specify per-part rotation, this default will be used."
        )
        rot_helper.setWordWrap(True)
        rot_layout.addWidget(rot_helper)

        main_layout.addWidget(rot_group)

        # ---------------- CSV Import & Nest group ----------------
        csv_group = QtWidgets.QGroupBox("CSV Import & Nesting")
        csv_layout = QtWidgets.QGridLayout(csv_group)

        self.csv_path_edit = QtWidgets.QLineEdit()
        self.csv_browse_button = QtWidgets.QPushButton("Browse…")
        self.import_and_nest_button = QtWidgets.QPushButton("Import CSV && Nest")

        csv_layout.addWidget(QtWidgets.QLabel("CSV file:"), 0, 0)
        csv_layout.addWidget(self.csv_path_edit, 0, 1)
        csv_layout.addWidget(self.csv_browse_button, 0, 2)
        csv_layout.addWidget(self.import_and_nest_button, 1, 1, 1, 2)

        main_layout.addWidget(csv_group)

        # ---------------- Footer info ----------------
        footer_label = QtWidgets.QLabel(
            "These settings are stored with this FreeCAD document and used for all SquatchCut nesting operations."
        )
        footer_label.setWordWrap(True)
        footer_label.setStyleSheet("color: gray; font-size: 10pt;")
        main_layout.addWidget(footer_label)

        main_layout.addStretch()

        # Wire up buttons
        self.csv_browse_button.clicked.connect(self._on_browse_clicked)
        self.import_and_nest_button.clicked.connect(self._on_import_and_nest_clicked)

    # ---------- Internal helpers ----------

    def _apply_settings_to_state_and_doc(self):
        """Apply current UI values to session_state and the document."""
        if self.doc is None:
            FreeCAD.Console.PrintError("[SquatchCut] No active document in ControlPanel._apply_settings_to_state_and_doc().\n")
            return

        sheet_w = float(self.sheet_width_spin.value())
        sheet_h = float(self.sheet_height_spin.value())
        kerf_mm = float(self.kerf_spin.value())
        gap_mm = float(self.gap_spin.value())
        default_allow = bool(self.default_rotate_check.isChecked())

        session_state.set_sheet_size(sheet_w, sheet_h)
        session_state.set_kerf_mm(kerf_mm)
        session_state.set_gap_mm(gap_mm)
        session_state.set_default_allow_rotate(default_allow)

        session.sync_doc_from_state(self.doc)
        self.doc.recompute()

        FreeCAD.Console.PrintMessage(
            f"[SquatchCut] Updated settings: sheet {sheet_w} x {sheet_h} mm, "
            f"kerf={kerf_mm} mm, gap={gap_mm} mm, default_allow_rotate={default_allow}\n"
        )

    def _on_browse_clicked(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dlg.setNameFilter("CSV files (*.csv)")
        dlg.setWindowTitle("Select panels CSV for SquatchCut")

        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        files = dlg.selectedFiles()
        if not files:
            return

        self.csv_path_edit.setText(files[0])

    def _on_import_and_nest_clicked(self):
        if self.doc is None:
            show_error("No active document for CSV import and nesting.", title="SquatchCut")
            return

        csv_path = self.csv_path_edit.text().strip()
        if not csv_path:
            show_error("Please choose a CSV file first.", title="SquatchCut")
            return

        if not os.path.isfile(csv_path):
            show_error(f"CSV file not found:\n{csv_path}", title="SquatchCut")
            return

        # Apply settings before import & nest
        self._apply_settings_to_state_and_doc()

        # Run CSV import
        try:
            prefs = SquatchCutPreferences()
            csv_units = prefs.get_csv_units(prefs.get_measurement_system())
            run_csv_import(self.doc, csv_path, csv_units=csv_units)
            prefs.set_csv_units(csv_units)
        except Exception as e:
            FreeCAD.Console.PrintError(f"[SquatchCut] CSV import failed: {e}\n")
            show_error(f"CSV import failed:\n{e}", title="SquatchCut")
            return

        # Run nesting using the existing command
        try:
            cmd = cmd_run_nesting.RunNestingCommand()
            cmd.Activated()
        except Exception as e:
            FreeCAD.Console.PrintError(f"[SquatchCut] Nesting failed after CSV import: {e}\n")
            show_error(f"Nesting failed after CSV import:\n{e}", title="SquatchCut")
            return

        show_info("CSV imported and nesting completed.", title="SquatchCut")
        FreeCAD.Console.PrintMessage("[SquatchCut] Import + Nest completed from control panel.\n")

    # ---------- FreeCAD TaskPanel API ----------

    def accept(self):
        """Called when user clicks OK on the TaskPanel wrapper."""
        if self.doc is None:
            FreeCAD.Console.PrintError("[SquatchCut] No active document in ControlPanel.accept().\n")
            FreeCADGui.Control.closeDialog()
            return

        self._apply_settings_to_state_and_doc()
        FreeCADGui.Control.closeDialog()

    def reject(self):
        """Called when user clicks Cancel/Close in the TaskPanel wrapper."""
        FreeCADGui.Control.closeDialog()
