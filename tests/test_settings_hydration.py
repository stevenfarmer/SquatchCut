from SquatchCut import settings
from SquatchCut.core import session_state
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core import units as sc_units


def test_hydrate_from_params_syncs_session_state():
    prefs = SquatchCutPreferences()

    orig_ms = prefs.get_measurement_system()
    orig_w = prefs.get_default_sheet_width_mm()
    orig_h = prefs.get_default_sheet_height_mm()
    orig_gap = prefs.get_default_spacing_mm()
    orig_kerf = prefs.get_default_kerf_mm()
    orig_cut_opt = prefs.get_default_optimize_for_cut_path()
    orig_export_labels = prefs.get_export_include_labels()
    orig_export_dims = prefs.get_export_include_dimensions()

    try:
        prefs.set_measurement_system("imperial")
        prefs.set_default_sheet_width_mm(1219.2)
        prefs.set_default_sheet_height_mm(2438.4)
        prefs.set_default_spacing_mm(6.35)
        prefs.set_default_kerf_mm(3.175)
        prefs.set_default_optimize_for_cut_path(True)
        prefs.set_export_include_labels(False)
        prefs.set_export_include_dimensions(True)

        settings.hydrate_from_params()

        assert session_state.get_measurement_system() == "imperial"
        assert sc_units.get_units() == "in"
        w, h = session_state.get_sheet_size()
        assert abs(w - 1219.2) < 1e-6
        assert abs(h - 2438.4) < 1e-6
        assert abs(session_state.get_gap_mm() - 6.35) < 1e-6
        assert abs(session_state.get_kerf_mm() - 3.175) < 1e-6
        assert session_state.get_optimize_for_cut_path() is True
        assert session_state.get_export_include_labels() is False
        assert session_state.get_export_include_dimensions() is True
    finally:
        prefs.set_measurement_system(orig_ms)
        prefs.set_default_sheet_width_mm(orig_w)
        prefs.set_default_sheet_height_mm(orig_h)
        prefs.set_default_spacing_mm(orig_gap)
        prefs.set_default_kerf_mm(orig_kerf)
        prefs.set_default_optimize_for_cut_path(orig_cut_opt)
        prefs.set_export_include_labels(orig_export_labels)
        prefs.set_export_include_dimensions(orig_export_dims)
        settings.hydrate_from_params()
