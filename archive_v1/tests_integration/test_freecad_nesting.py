"""@codex
Integration tests inside FreeCAD verifying nesting command output and robustness.
Creates real geometry, runs RunNestingCommand, and inspects Sheet_* groups/clones.
"""

import pytest

# Skip these tests entirely if FreeCAD is not importable
pytest.importorskip("FreeCAD")

import FreeCAD  # type: ignore


def _get_squatchcut_run_nesting():
    """
    Import and return the RunNestingCommand class from SquatchCut.

    Adjust the import path here if RunNestingCommand lives in a different module.
    """
    from SquatchCut.commands.run_nesting import RunNestingCommand
    return RunNestingCommand


def _get_sheet_groups(doc):
    """Return all Sheet_* groups in the active document."""
    return [obj for obj in doc.Objects if obj.Name.startswith("Sheet_")]


def test_run_nesting_creates_sheet_groups_and_clones():
    """
    Basic integration test:
    - Create a document.
    - Add a few rectangles.
    - Select them and run RunNestingCommand.
    - Expect at least one Sheet_* group with clones.
    """
    FreeCAD.Console.PrintMessage("[SquatchCut QA] Running test_run_nesting_creates_sheet_groups_and_clones\n")
    print("[SquatchCut QA] Running test_run_nesting_creates_sheet_groups_and_clones")
    # Import Draft inside FreeCAD environment
    import Draft
    import FreeCADGui as Gui

    # New document
    doc = FreeCAD.newDocument("TestSquatchCutNesting")

    # Create some simple panels
    r1 = Draft.makeRectangle(length=300, height=200)
    r2 = Draft.makeRectangle(length=400, height=150)
    r3 = Draft.makeRectangle(length=250, height=250)
    doc.recompute()

    # Select them as input
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(r1)
    Gui.Selection.addSelection(r2)
    Gui.Selection.addSelection(r3)

    # Run the SquatchCut nesting command
    RunNestingCommand = _get_squatchcut_run_nesting()
    cmd = RunNestingCommand()
    cmd.Activated()
    doc.recompute()

    # Verify sheets were created
    sheet_groups = _get_sheet_groups(doc)
    assert sheet_groups, "No Sheet_* groups were created by RunNestingCommand"

    # Count clones inside sheet groups
    clone_count = 0
    for g in sheet_groups:
        # Some groups may contain a boundary rectangle plus clones
        clone_count += len(getattr(g, "Group", []))

    assert clone_count >= 3, (
        f"Expected at least 3 placed panel objects, found {clone_count}"
    )

    # Close the document to avoid polluting FreeCAD session
    FreeCAD.closeDocument(doc.Name)


def test_run_nesting_no_selection_shows_no_crash():
    """
    Ensure that running nesting with no selection does not crash.
    The command should return gracefully and not create any sheets.
    """
    FreeCAD.Console.PrintMessage("[SquatchCut QA] Running test_run_nesting_no_selection_shows_no_crash\n")
    print("[SquatchCut QA] Running test_run_nesting_no_selection_shows_no_crash")
    import FreeCADGui as Gui

    doc = FreeCAD.newDocument("TestSquatchCutNoSelection")
    Gui.Selection.clearSelection()

    RunNestingCommand = _get_squatchcut_run_nesting()
    cmd = RunNestingCommand()
    cmd.Activated()
    doc.recompute()

    sheet_groups = _get_sheet_groups(doc)
    # No selection => no sheets should be created
    assert not sheet_groups, "Sheets were created even though nothing was selected"

    FreeCAD.closeDocument(doc.Name)
