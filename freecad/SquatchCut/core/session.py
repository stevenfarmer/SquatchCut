# @codex
# File: freecad/SquatchCut/core/session.py
# Summary: FreeCAD-aware adapter syncing document properties into session_state.
# Details:
#   - Ensures sheet size, kerf/gap, and default rotation flags mirror doc properties.
#   - Provides helpers to sync state to/from the active FreeCAD document.
from __future__ import annotations

from SquatchCut.freecad_integration import Gui  # noqa: F401
from SquatchCut.core import session_state

# Additional SquatchCut session-related state
_source_panel_objects = []
_sheet_objects = []
_nested_panel_objects = []
_last_csv_path = None


def update_sheet_size_from_doc(doc):
    """Read sheet size from document properties into session_state."""
    try:
        w = float(getattr(doc, "SquatchCutSheetWidth"))
        h = float(getattr(doc, "SquatchCutSheetHeight"))
        session_state.set_sheet_size(w, h)
    except Exception:
        pass


def update_kerf_gap_from_doc(doc):
    """Read kerf/gap from document properties into session_state."""
    try:
        session_state.set_kerf_mm(float(getattr(doc, "SquatchCutKerfMM")))
    except Exception:
        pass
    try:
        session_state.set_gap_mm(float(getattr(doc, "SquatchCutGapMM")))
    except Exception:
        pass
    try:
        session_state.set_default_allow_rotate(bool(getattr(doc, "SquatchCutDefaultAllowRotate")))
    except Exception:
        pass


def push_last_layout_to_state(layout):
    """Push last layout into session_state."""
    session_state.set_last_layout(layout)


def set_sheet_properties(doc, width, height, units="mm"):
    """Helper to set sheet size on doc and mirror into session_state."""
    try:
        doc.SquatchCutSheetWidth = float(width)
        doc.SquatchCutSheetHeight = float(height)
        session_state.set_sheet_size(float(width), float(height))
    except Exception:
        pass
    try:
        doc.SquatchCutSheetUnits = units or "mm"
    except Exception:
        pass
    # Also mirror current kerf/gap/default rotate into doc
    try:
        doc.SquatchCutKerfMM = float(session_state.get_kerf_mm())
    except Exception:
        pass
    try:
        doc.SquatchCutGapMM = float(session_state.get_gap_mm())
    except Exception:
        pass
    try:
        doc.SquatchCutDefaultAllowRotate = bool(session_state.get_default_allow_rotate())
    except Exception:
        pass


def ensure_doc_settings(doc):
    """
    Ensure the active document has the SquatchCut settings properties.
    """
    if not hasattr(doc, "SquatchCutSheetWidth"):
        try:
            doc.addProperty(
                "App::PropertyFloat",
                "SquatchCutSheetWidth",
                "SquatchCut",
                "Sheet width (mm)",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutSheetWidth = 1220.0
        except Exception:
            pass
    if not hasattr(doc, "SquatchCutSheetHeight"):
        try:
            doc.addProperty(
                "App::PropertyFloat",
                "SquatchCutSheetHeight",
                "SquatchCut",
                "Sheet height (mm)",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutSheetHeight = 2440.0
        except Exception:
            pass

    if not hasattr(doc, "SquatchCutKerfMM"):
        try:
            doc.addProperty(
                "App::PropertyFloat",
                "SquatchCutKerfMM",
                "SquatchCut",
                "Kerf spacing between adjacent parts (mm)",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutKerfMM = 3.0
        except Exception:
            pass
    if not hasattr(doc, "SquatchCutGapMM"):
        try:
            doc.addProperty(
                "App::PropertyFloat",
                "SquatchCutGapMM",
                "SquatchCut",
                "Gap/halo spacing around parts (mm)",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutGapMM = 0.0
        except Exception:
            pass

    if not hasattr(doc, "SquatchCutDefaultAllowRotate"):
        try:
            doc.addProperty(
                "App::PropertyBool",
                "SquatchCutDefaultAllowRotate",
                "SquatchCut",
                "Allow rotation by default when CSV does not specify allow_rotate.",
            )
        except Exception:
            pass
        try:
            doc.SquatchCutDefaultAllowRotate = False
        except Exception:
            pass


def sync_state_from_doc(doc):
    """
    Read settings from the FreeCAD document and push them into session_state.
    """
    ensure_doc_settings(doc)

    session_state.set_sheet_size(
        float(doc.SquatchCutSheetWidth),
        float(doc.SquatchCutSheetHeight),
    )
    session_state.set_kerf_mm(float(doc.SquatchCutKerfMM))
    session_state.set_gap_mm(float(doc.SquatchCutGapMM))

    default_allow = bool(doc.SquatchCutDefaultAllowRotate)
    session_state.set_default_allow_rotate(default_allow)


def sync_doc_from_state(doc):
    """
    Write current session_state values back into the document properties.
    Useful if state was changed directly.
    """
    ensure_doc_settings(doc)

    w, h = session_state.get_sheet_size()
    if w is not None:
        doc.SquatchCutSheetWidth = float(w)
    if h is not None:
        doc.SquatchCutSheetHeight = float(h)

    doc.SquatchCutKerfMM = float(session_state.get_kerf_mm())
    doc.SquatchCutGapMM = float(session_state.get_gap_mm())
    doc.SquatchCutDefaultAllowRotate = bool(session_state.get_default_allow_rotate())


# Convenience wrappers to mirror session_state panel storage -------------------

def get_panels():
    return session_state.get_panels()


def set_panels(panels):
    session_state.set_panels(panels)


# Source panel objects ---------------------------------------------------------

def get_source_panel_objects():
    return _source_panel_objects


def set_source_panel_objects(objs):
    global _source_panel_objects
    _source_panel_objects = list(objs) if objs is not None else []


def clear_source_panel_objects():
    global _source_panel_objects
    _source_panel_objects = []


# Sheet and nested objects -----------------------------------------------------

def get_sheet_objects():
    return _sheet_objects


def set_sheet_objects(objs):
    global _sheet_objects
    _sheet_objects = list(objs) if objs is not None else []


def get_nested_panel_objects():
    return _nested_panel_objects


def set_nested_panel_objects(objs):
    global _nested_panel_objects
    _nested_panel_objects = list(objs) if objs is not None else []


def clear_sheets():
    global _sheet_objects, _nested_panel_objects
    _sheet_objects = []
    _nested_panel_objects = []


# CSV path tracking ------------------------------------------------------------

def get_last_csv_path():
    return _last_csv_path


def set_last_csv_path(path):
    global _last_csv_path
    _last_csv_path = path


# General clear ---------------------------------------------------------------

def clear_all_geometry():
    clear_source_panel_objects()
    clear_sheets()
