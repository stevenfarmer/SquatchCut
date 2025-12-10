"""@codex
Module: Shape extraction utilities for building SquatchCut panels from FreeCAD documents.
Boundaries: Do not load CSV files or perform nesting optimization; only inspect FreeCAD shapes and convert to panel objects.
Primary methods: scan_document, extract_bounding_boxes, to_panel_objects, apply_rotation_rules, filter_selection.
Note: Update incrementally; do not overwrite this module when adding logic.
"""

from __future__ import annotations

from SquatchCut.freecad_integration import Gui


class ShapeExtractor:
    """Scans a FreeCAD document and produces panel objects for nesting."""

    def scan_document(self, document, selection_only: bool = False):
        """Scan the document for valid shapes; optionally limit to user selection."""
        if selection_only:
            return self.extract_from_selection(None)
        return self.extract_from_document(document)

    def extract_bounding_boxes(self, shapes):
        """Return bounding boxes (width, height) for each shape."""
        results = []
        for shape in shapes:
            bbox = self.extract_bounding_box(shape)
            if bbox:
                results.append(bbox)
        return results

    def to_panel_objects(self, shapes):
        """Convert shapes into normalized panel objects."""
        panels = []
        for shape in shapes:
            panel = self.to_panel_object(shape)
            if panel:
                panels.append(panel)
        return panels

    def apply_rotation_rules(self, panels):
        """Apply rotation rules to panels and annotate rotation allowances."""
        for panel in panels:
            panel.setdefault("rotation_allowed", True)
        return panels

    def filter_selection(self, document):
        """Return shapes filtered to the current user selection."""
        return self.extract_from_selection(None)

    def extract_from_document(self, document):
        """Iterate over document objects and extract panels."""
        if document is None:
            return []
        panels = []
        for obj in getattr(document, "Objects", []):
            panel = self.to_panel_object(obj)
            if panel:
                panels.append(panel)
        return panels

    def extract_from_selection(self, selection):
        """Process the current selection (or provided selection list) into panels."""
        selected_objects = []
        if selection is not None:
            selected_objects = selection
        elif Gui and hasattr(Gui, "Selection"):
            selected_objects = Gui.Selection.getSelection()

        panels = []
        for obj in selected_objects or []:
            panel = self.to_panel_object(obj)
            if panel:
                panels.append(panel)
        return panels

    def extract_bounding_box(self, shape):
        """Compute axis-aligned bounding box for a shape or object in mm."""
        bound = None
        if hasattr(shape, "Shape") and hasattr(shape.Shape, "BoundBox"):
            bound = shape.Shape.BoundBox
        elif hasattr(shape, "BoundBox"):
            bound = shape.BoundBox

        if bound is None:
            return None

        width = float(bound.XLength)
        height = float(bound.YLength)
        return width, height

    def to_panel_object(self, shape_or_obj):
        """Convert a FreeCAD object or shape to a panel dict."""
        bbox = self.extract_bounding_box(shape_or_obj)
        if not bbox:
            return None

        width, height = bbox
        if width <= 0 or height <= 0:
            return None

        label = getattr(shape_or_obj, "Label", None) or getattr(
            shape_or_obj, "Name", "panel"
        )
        return {
            "id": str(label),
            "width": width,
            "height": height,
            "rotation_allowed": True,
        }
