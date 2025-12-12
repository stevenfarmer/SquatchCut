import importlib
import sys
from unittest.mock import MagicMock

import pytest
import SquatchCut.freecad_integration
from SquatchCut.core import session, sheet_model
from SquatchCut.core.nesting import PlacedPart
from SquatchCut.gui import nesting_view

# Define Mocks
mock_App = MagicMock()
mock_Gui = MagicMock()
mock_Part = MagicMock()


# Setup Vector
def vector_side_effect(x, y, z):
    v = MagicMock()
    v.x = x
    v.y = y
    v.z = z
    v.__iter__ = lambda self: iter((self.x, self.y, self.z))
    v.__eq__ = lambda self, other: (
        (self.x, self.y, self.z) == (other.x, other.y, other.z)
        if hasattr(other, "x")
        else False
    )
    return v


mock_App.Vector = MagicMock(side_effect=vector_side_effect)

# Setup Rotation
mock_App.Rotation = MagicMock()

# Setup Document
mock_doc = MagicMock()
mock_App.ActiveDocument = mock_doc
mock_App.newDocument.return_value = mock_doc


# Setup Objects
def addObject_side_effect(type, name):
    obj = MagicMock()
    obj.Name = name
    # ViewObject
    obj.ViewObject = MagicMock()
    obj.ViewObject.DisplayMode = ""
    obj.ViewObject.ShapeColor = (0.0, 0.0, 0.0)
    # Placement
    obj.Placement = MagicMock()
    obj.Placement.Base = mock_App.Vector(0, 0, 0)
    obj.Placement.Rotation = MagicMock()
    # Shape
    obj.Shape = MagicMock()
    obj.Shape.BoundBox = MagicMock()
    return obj


mock_doc.addObject.side_effect = addObject_side_effect
mock_doc.getObject.return_value = None

# Setup Part.makePlane
mock_Part.makePlane = MagicMock()


@pytest.fixture(scope="module", autouse=True)
def setup_integration():
    """
    Inject mocks into sys.modules and reload SquatchCut modules so they use the mocks.
    Clean up afterwards so other tests are not affected.
    """
    # Inject mocks
    sys.modules["FreeCAD"] = mock_App
    sys.modules["FreeCADGui"] = mock_Gui
    sys.modules["Part"] = mock_Part

    # Reload modules to pick up the mocks
    importlib.reload(SquatchCut.freecad_integration)
    importlib.reload(session)
    importlib.reload(sheet_model)
    importlib.reload(nesting_view)

    yield

    # Remove mocks
    if "FreeCAD" in sys.modules:
        del sys.modules["FreeCAD"]
    if "FreeCADGui" in sys.modules:
        del sys.modules["FreeCADGui"]
    if "Part" in sys.modules:
        del sys.modules["Part"]

    # Reload modules to reset to "missing FreeCAD" state
    importlib.reload(SquatchCut.freecad_integration)
    importlib.reload(session)
    importlib.reload(sheet_model)
    importlib.reload(nesting_view)


def test_ensure_sheet_object_orientation_and_color():
    # Reset mocks
    mock_Part.makePlane.reset_mock()
    mock_doc.getObject.return_value = None

    # Run
    sheet = sheet_model.ensure_sheet_object(200.0, 100.0, mock_doc)

    # Check if makePlane was called with correct arguments
    assert mock_Part.makePlane.call_count == 1
    args = mock_Part.makePlane.call_args[0]
    # args: length, width, start_pnt, normal, dir_pnt
    assert args[0] == 200.0
    assert args[1] == 100.0

    # Check vectors
    # Normal (4th arg) should be (0, 0, 1) -> Z
    normal = args[3]
    assert normal.x == 0 and normal.y == 0 and normal.z == 1

    # Dir (5th arg) should be (1, 0, 0) -> X
    direction = args[4]
    assert direction.x == 1 and direction.y == 0 and direction.z == 0

    # Check Color
    assert sheet.ViewObject.ShapeColor == (0.5, 0.5, 0.5)


def test_nested_parts_z_placement_mocked():
    placements = [
        PlacedPart(id="P1", sheet_index=0, x=10.0, y=10.0, width=50.0, height=50.0),
    ]

    group, objs = nesting_view.rebuild_nested_geometry(
        mock_doc, placements, sheet_sizes=[(200.0, 100.0)], prefs=None
    )

    assert len(objs) == 1
    part = objs[0]

    # Check Placement Z
    # Expected: Z = 0.1
    base = part.Placement.Base
    assert base.z == 0.1


def test_sheet_boundary_creation():
    mock_Part.makePlane.reset_mock()

    sheet_sizes = [(100.0, 100.0), (100.0, 100.0)]
    spacing = 10.0

    boundaries, offsets = sheet_model.build_sheet_boundaries(
        mock_doc, sheet_sizes, spacing
    )

    assert mock_Part.makePlane.call_count == 2

    # check 2nd call (for _create_sheet_feature)
    args2 = mock_Part.makePlane.call_args_list[1][0]

    # Normal (4th arg) should be (0, 0, 1)
    normal = args2[3]
    assert normal.x == 0 and normal.y == 0 and normal.z == 1
