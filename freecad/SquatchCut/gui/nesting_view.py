"""Helpers to build and manage the nested layout geometry in FreeCAD."""

from __future__ import annotations

from typing import Optional

from SquatchCut.core import logger
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.core.sheet_model import clear_group_children, get_or_create_group
from SquatchCut.freecad_integration import App, Part
from SquatchCut.gui.nesting_colors import (
    get_freecad_color,
    get_transparency_for_display_mode,
)

NESTED_Z_OFFSET = 0.1
SHEET_Z_OFFSET = -0.1  # Sheets render below parts

NESTED_GROUP_NAME = "SquatchCut_NestedParts"
SHEET_GROUP_NAME = "SquatchCut_SheetBoundaries"


def ensure_nested_group(doc):
    """Ensure the nested parts group exists and return it."""
    if App is None:
        logger.warning("ensure_nested_group() skipped: FreeCAD not available.")
        return None
    if doc is None:
        doc = App.newDocument("SquatchCut")
    return get_or_create_group(doc, NESTED_GROUP_NAME)


def ensure_sheet_group(doc):
    """Ensure the sheet boundaries group exists and return it."""
    if App is None:
        logger.warning("ensure_sheet_group() skipped: FreeCAD not available.")
        return None
    if doc is None:
        doc = App.newDocument("SquatchCut")
    return get_or_create_group(doc, SHEET_GROUP_NAME)


def create_sheet_boundary(
    doc,
    sheet_index: int,
    width: float,
    height: float,
    x_offset: float = 0.0,
    prefs: Optional[SquatchCutPreferences] = None,
):
    """Create a sheet boundary object with user-configured appearance."""
    if App is None or Part is None:
        return None

    if prefs is None:
        prefs = SquatchCutPreferences()

    # Get user preferences
    display_mode = prefs.get_nesting_sheet_display_mode()
    color_scheme = prefs.get_nesting_color_scheme()

    # Create sheet boundary object
    name = f"SC_Sheet_{sheet_index}_Boundary"
    sheet_obj = doc.addObject("Part::Box", name)
    sheet_obj.Width = width
    sheet_obj.Length = height
    sheet_obj.Height = 0.1  # Very thin sheet

    # Position the sheet
    placement = sheet_obj.Placement
    placement.Base = App.Vector(x_offset, 0, SHEET_Z_OFFSET)
    sheet_obj.Placement = placement

    # Apply visual styling
    try:
        if hasattr(sheet_obj, "ViewObject"):
            view_obj = sheet_obj.ViewObject

            # Set colors based on scheme
            outline_color = get_freecad_color(color_scheme, "sheet_outline")
            fill_color = get_freecad_color(color_scheme, "sheet_fill")

            if display_mode == "wireframe":
                view_obj.DisplayMode = "Wireframe"
                view_obj.LineColor = outline_color
                view_obj.LineWidth = 2.0
            else:
                view_obj.DisplayMode = "Flat Lines"
                view_obj.ShapeColor = fill_color
                view_obj.LineColor = outline_color
                view_obj.LineWidth = 2.0

                # Set transparency
                transparency = get_transparency_for_display_mode(display_mode)
                view_obj.Transparency = int(transparency * 100)  # FreeCAD uses 0-100

    except Exception as e:
        logger.warning(f"Failed to set sheet boundary appearance: {e}")

    return sheet_obj


def create_sheet_label(
    doc,
    sheet_index: int,
    width: float,
    height: float,
    x_offset: float = 0.0,
    label_text: Optional[str] = None,
    prefs: Optional[SquatchCutPreferences] = None,
):
    """Create a text label for the sheet."""
    if App is None:
        return None

    if prefs is None:
        prefs = SquatchCutPreferences()

    # Create text object with fallbacks
    name = f"SC_Sheet_{sheet_index}_Label"
    text_obj = None

    if label_text is None:
        label_text = f"Sheet {sheet_index + 1}"

    # Try different text object types based on what's available
    try:
        # Try Draft::Text first (most common)
        text_obj = doc.addObject("Draft::Text", name)
        text_obj.Text = [label_text]
        text_obj.Height = min(width, height) * 0.05  # 5% of smaller dimension
    except (TypeError, AttributeError):
        try:
            # Try App::Annotation as fallback
            text_obj = doc.addObject("App::Annotation", name)
            text_obj.LabelText = [label_text]
        except (TypeError, AttributeError):
            try:
                # If no text objects work, create a small box as visual placeholder
                text_obj = doc.addObject("Part::Box", name)
                text_obj.Width = min(
                    width * 0.1, 50.0
                )  # Small box as label placeholder
                text_obj.Length = 10.0
                text_obj.Height = 2.0
            except Exception:
                # If all else fails, return None - labels are optional
                logger.warning(
                    f"Could not create sheet label {name}: no suitable object types available"
                )
                return None

    if text_obj is None:
        return None

    # Position at top-left corner of sheet
    placement = text_obj.Placement
    placement.Base = App.Vector(x_offset + 10, height - 20, NESTED_Z_OFFSET + 0.1)
    text_obj.Placement = placement

    # Apply styling
    try:
        if hasattr(text_obj, "ViewObject"):
            color_scheme = prefs.get_nesting_color_scheme()
            label_color = get_freecad_color(color_scheme, "sheet_label")
            text_obj.ViewObject.TextColor = label_color
    except Exception as e:
        logger.warning(f"Failed to set sheet label appearance: {e}")

    return text_obj


def create_part_label(
    doc,
    placement_part,
    x: float,
    y: float,
    width: float,
    height: float,
    prefs: Optional[SquatchCutPreferences] = None,
):
    """Create a text label for a nested part."""
    if App is None:
        return None

    if prefs is None:
        prefs = SquatchCutPreferences()

    # Create text object with fallbacks
    part_id = getattr(placement_part, "id", "Unknown")
    name = f"SC_PartLabel_{part_id}"
    text_obj = None

    label_text = str(part_id)

    # Try different text object types based on what's available
    try:
        # Try Draft::Text first (most common)
        text_obj = doc.addObject("Draft::Text", name)
        text_obj.Text = [label_text]
        text_obj.Height = min(width, height) * 0.1  # 10% of smaller dimension, min 5mm
        text_obj.Height = max(text_obj.Height, 5.0)
    except (TypeError, AttributeError):
        try:
            # Try App::Annotation as fallback
            text_obj = doc.addObject("App::Annotation", name)
            text_obj.LabelText = [label_text]
        except (TypeError, AttributeError):
            try:
                # If no text objects work, create a small box as visual placeholder
                text_obj = doc.addObject("Part::Box", name)
                text_obj.Width = min(
                    width * 0.2, 20.0
                )  # Small box as label placeholder
                text_obj.Length = min(height * 0.2, 20.0)
                text_obj.Height = 1.0
            except Exception:
                # If all else fails, return None - labels are optional
                logger.warning(
                    f"Could not create part label {name}: no suitable object types available"
                )
                return None

    if text_obj is None:
        return None

    # Position at center of part
    placement = text_obj.Placement
    center_x = x + width / 2
    center_y = y + height / 2
    placement.Base = App.Vector(center_x, center_y, NESTED_Z_OFFSET + 0.2)
    text_obj.Placement = placement

    # Apply styling
    try:
        if hasattr(text_obj, "ViewObject"):
            color_scheme = prefs.get_nesting_color_scheme()
            label_color = get_freecad_color(color_scheme, "part_label")
            text_obj.ViewObject.TextColor = label_color
    except Exception as e:
        logger.warning(f"Failed to set part label appearance: {e}")

    return text_obj


def rebuild_nested_geometry(
    doc,
    placements,
    sheet_w=None,
    sheet_h=None,
    sheet_sizes=None,
    spacing=None,
    source_objects=None,
    prefs=None,
):
    """
    Clear existing nested geometry and rebuild from placements.

    Returns (group, nested_objects).
    """
    if App is None or Part is None:
        logger.warning("rebuild_nested_geometry() skipped: FreeCAD/Part unavailable.")
        return None, []

    if prefs is None:
        prefs = SquatchCutPreferences()

    # Clear and rebuild nested parts group
    group = ensure_nested_group(doc)
    if group is None:
        return None, []
    removed = clear_group_children(group)
    logger.info(
        f">>> [SquatchCut] Nested group cleared and rebuilt with {removed} parts"
    )

    # Clear and rebuild sheet boundaries group
    sheet_group = ensure_sheet_group(doc)
    if sheet_group is not None:
        sheet_removed = clear_group_children(sheet_group)
        logger.info(
            f">>> [SquatchCut] Sheet boundaries cleared and rebuilt with {sheet_removed} objects"
        )

    source_objects = source_objects or []
    source_map = _build_source_map(source_objects, doc)
    if not source_map and placements:
        logger.warning(
            "[SquatchCut][WARN] No valid source objects found for nesting; using fallback boxes."
        )

    def _find_source(part_id):
        return (
            source_map.get(part_id)
            or doc.getObject(part_id)
            or doc.getObject(f"SC_Source_{part_id}")
        )

    nested_objs = []
    size_list = sheet_sizes or []
    if not size_list and sheet_w and sheet_h:
        size_list = [(sheet_w, sheet_h)]
    if not size_list:
        if sheet_w and sheet_h:
            size_list = [(sheet_w, sheet_h)]
        else:
            size_list = [(0.0, 0.0)]
    sheet_spacing = (
        float(spacing)
        if spacing is not None
        else (float(size_list[0][0]) * 0.25 if size_list and size_list[0][0] else 0.0)
    )
    # Calculate sheet offsets and create sheet boundaries
    sheet_offsets = []
    current_offset = 0.0
    sheet_objects = []

    for sheet_idx, (width, height) in enumerate(size_list):
        sheet_offsets.append(current_offset)

        # Create sheet boundary if user preferences allow
        if sheet_group is not None and width > 0 and height > 0:
            # Create sheet boundary
            sheet_boundary = create_sheet_boundary(
                doc, sheet_idx, width, height, current_offset, prefs
            )
            if sheet_boundary:
                sheet_group.addObject(sheet_boundary)
                sheet_objects.append(sheet_boundary)

            # Create sheet label if enabled
            if (
                prefs.get_nesting_show_part_labels()
            ):  # Reuse part labels setting for sheet labels
                sheet_label = create_sheet_label(
                    doc, sheet_idx, width, height, current_offset, None, prefs
                )
                if sheet_label:
                    sheet_group.addObject(sheet_label)
                    sheet_objects.append(sheet_label)

        current_offset += width + sheet_spacing

    for idx, pp in enumerate(placements or []):
        try:
            sheet_index = int(getattr(pp, "sheet_index", 0) or 0)
            x = float(getattr(pp, "x", 0.0))
            y = float(getattr(pp, "y", 0.0))
            w = float(getattr(pp, "width", 0.0))
            h = float(getattr(pp, "height", 0.0))
        except Exception:
            continue
        if w <= 0 or h <= 0:
            continue

        name = f"SC_Nested_{pp.id}_{sheet_index}_{idx}"
        src = _find_source(getattr(pp, "id", ""))
        if src and hasattr(src, "Shape"):
            obj = doc.addObject("Part::Feature", name)
            obj.Shape = src.Shape.copy()
        else:
            obj = doc.addObject("Part::Box", name)
            obj.Width = w
            obj.Length = h
            obj.Height = 1.0

        placement = obj.Placement
        idx = min(sheet_index, len(sheet_offsets) - 1 if sheet_offsets else 0)
        if idx < 0:
            idx = 0
        base_x = sheet_offsets[idx] + x
        base_y = y
        placement.Base = App.Vector(base_x, base_y, NESTED_Z_OFFSET)
        try:
            placement.Rotation = App.Rotation(
                App.Vector(0, 0, 1), float(getattr(pp, "rotation_deg", 0))
            )
        except Exception:
            pass
        obj.Placement = placement

        # Apply visual styling based on user preferences
        try:
            if hasattr(obj, "ViewObject"):
                view_obj = obj.ViewObject
                view_obj.DisplayMode = "Flat Lines"

                # Get color scheme
                color_scheme = prefs.get_nesting_color_scheme()

                # Determine if part is rotated
                rotation_deg = float(getattr(pp, "rotation_deg", 0))
                is_rotated = abs(rotation_deg % 180) > 1  # Allow small tolerance

                # Set part color based on rotation
                if is_rotated:
                    part_color = get_freecad_color(color_scheme, "part_rotated")
                else:
                    part_color = get_freecad_color(color_scheme, "part_default")

                view_obj.ShapeColor = part_color

                # Use simplified view if enabled and we have many parts
                if prefs.get_nesting_simplified_view() and len(placements or []) > 20:
                    view_obj.DisplayMode = "Wireframe"

        except Exception as e:
            logger.warning(f"Failed to set part appearance for {name}: {e}")

        group.addObject(obj)
        nested_objs.append(obj)

        # Create part label if enabled
        if prefs.get_nesting_show_part_labels():
            try:
                part_label = create_part_label(doc, pp, base_x, base_y, w, h, prefs)
                if part_label:
                    group.addObject(part_label)
                    nested_objs.append(part_label)
            except Exception as e:
                logger.warning(f"Failed to create part label for {name}: {e}")

    try:
        doc.recompute()
    except Exception:
        pass

    logger.info(
        f">>> [SquatchCut] Rebuilt nesting view with {len(nested_objs)} object(s)."
    )
    return group, nested_objs


def _safe_object_name(obj):
    if obj is None:
        return ""
    try:
        return getattr(obj, "Name", "") or ""
    except ReferenceError:
        return ""


def _build_source_map(source_objects, doc):
    valid = {}
    for obj in source_objects or []:
        name = _safe_object_name(obj)
        if name:
            valid[name] = obj
    if doc is not None:
        source_group = doc.getObject("SquatchCut_SourceParts")
        if source_group is not None:
            for member in getattr(source_group, "Group", []) or []:
                name = _safe_object_name(member)
                if name:
                    valid[name] = member
        for obj in getattr(doc, "Objects", []) or []:
            try:
                name = getattr(obj, "Name", "") or ""
            except ReferenceError:
                continue
            if not name or not name.startswith("SC_Source_"):
                continue
            key = name.replace("SC_Source_", "", 1) or name
            if key not in valid:
                valid[key] = obj
    return valid
