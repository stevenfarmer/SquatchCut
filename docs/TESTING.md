# SquatchCut Testing & QA Guide

This document explains how to test the SquatchCut workbench, both automatically
(pytest and integration tests) and manually inside FreeCAD.

It is written assuming:
- You have this repository cloned.
- You have Python and FreeCAD installed.
- You are comfortable using a terminal (e.g., VS Code terminal).


## 1. Core Tests (No FreeCAD Required)

These tests cover the pure Python core logic under `SquatchCut/core`:
- Nesting algorithm (no overlaps, rotation, multiple sheets).
- Session state storage (sheet size, kerf, gap, last layout).

### 1.1. Setup (first time)

Create and activate a virtual environment:

```
python3 -m venv .venv
source .venv/bin/activate
```

Install test dependencies:

```
pip install pytest pytest-cov
```

### 1.2. Run core tests

From the repository root:

```
pytest -v
```

Or with coverage:

```
pytest --cov=SquatchCut/core --cov-report=term-missing -v
```

Expected results:

- All tests in `tests/` should pass.
- For `test_nesting.py` you should see test names such as:
  - `test_nesting_no_overlap_simple`
  - `test_nesting_respects_can_rotate`
  - `test_nesting_multiple_sheets`
  - `test_nesting_rotation_flag_preserved`

If any test fails, pytest will show:
- The test name.
- The failing assertion.
- The inputs that caused the failure.

Use this output to debug the core logic before touching FreeCAD.


## 2. FreeCAD Integration Tests

These tests run **inside FreeCAD** and exercise real commands:
- Creating rectangles in a document.
- Running `RunNestingCommand`.
- Verifying that `Sheet_*` groups and clones exist.
- Verifying that running nesting with no selection does not crash.

### 2.1. Ensure pytest is installed in FreeCAD

You only need to do this once per FreeCAD Python environment:

```
FreeCADCmd -c "import sys, subprocess; subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytest'])"
```

On macOS with the official FreeCAD .app, `FreeCADCmd` is usually:

```
/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd
```

So the command becomes:

```
/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd -c "import sys, subprocess; subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytest'])"
```

### 2.2. Run integration tests

From the repository root:

```
FreeCADCmd -c "import run_freecad_tests"
```

(Or using the full path to `FreeCADCmd` as above.)

This will run the tests in `tests_integration/`.

Expected results:

- `test_run_nesting_creates_sheet_groups_and_clones` passes:
  - At least one `Sheet_*` group exists.
  - There are at least as many clones as input panels.
- `test_run_nesting_no_selection_shows_no_crash` passes:
  - Running nesting with no selection does not create any `Sheet_*` groups.
  - No exception bubbles out of the command.

Integration tests are a quick sanity check that the workbench actually
behaves correctly inside FreeCAD with real documents.


## 3. Manual QA Checklist in FreeCAD

Use this checklist when doing manual QA in FreeCAD.
This is especially important before a release or when major changes
are made to nesting, CSV import, or settings.

### 3.1. Settings panel

1. Open FreeCAD.
2. Create or open a document.
3. From the SquatchCut workbench, run the **SquatchCut Settings** command.
4. In the settings panel:
   - Change sheet width and height.
   - Change kerf (mm) and gap (mm).
   - Toggle "Allow rotation by default".
5. Click OK.
6. Verify:
   - The Report View shows an updated settings message.
   - Re-opening the Settings panel shows the same values you entered.
   - Sheet size values are respected by the next nesting operation.

### 3.2. CSV import with rotation specified

1. Prepare a CSV with:
   - `id,width_mm,height_mm,allow_rotate`
   - Some rows with `allow_rotate=1`, some with `allow_rotate=0`.
2. Use the SquatchCut CSV import command to load this file.
3. Verify:
   - Panels are created in the document.
   - Each imported panel has a `SquatchCutCanRotate` property:
     - `True` for `allow_rotate=1`.
     - `False` for `allow_rotate=0`.
4. Run nesting:
   - Check that some panels are rotated (those allowed).
   - Panels with `allow_rotate=0` must never be rotated.

### 3.3. CSV import without rotation column (default behavior)

1. Prepare a CSV without `allow_rotate` column.
2. In the Settings panel, set:
   - "Allow rotation by default" = ON.
3. Import the CSV and run nesting.
4. Verify:
   - Panels are allowed to rotate and will rotate when beneficial.

5. Set "Allow rotation by default" = OFF.
6. Import the same CSV again and run nesting.
7. Verify:
   - No panels are rotated (all rotation_deg = 0 in the export).

### 3.4. Nesting placement (no overlaps, multiple sheets)

1. Create multiple rectangles of varying sizes in a document.
2. Run nesting.
3. Verify:
   - `Sheet_*` groups are created.
   - No shapes overlap visually.
   - If the total area is large, more than one sheet is used.

### 3.5. CSV export of nesting

1. Perform a nesting as above.
2. Run the **Export Nesting CSV** command.
3. Choose a filename and save.
4. Open the CSV in a spreadsheet viewer.
5. Verify:
   - Header includes: `sheet_index,part_id,width_mm,height_mm,x_mm,y_mm,angle_deg`.
   - Each input part appears exactly once in the CSV output.
   - `sheet_index` values correspond to the FreeCAD `Sheet_*` groups.
   - `angle_deg` is 0 for non-rotated parts and 90 for rotated parts.

### 3.6. Error handling

1. Try to import a CSV missing required columns (e.g., no id or width).
   - Expect: a friendly error dialog explaining missing columns.
2. Try running nesting with no panels selected.
   - Expect: a warning dialog and no sheets created.
3. Try exporting CSV before any nesting has been run.
   - Expect: a message that no layout is available to export.


## 4. Useful pytest options

For deeper debugging, use:

```
pytest -vv
```

This prints each test name and makes it easier to see exactly which
scenario passed or failed.

To focus on a single test file:

```
pytest -vv tests/test_nesting.py
```

Or a single test within that file:

```
pytest -vv tests/test_nesting.py::test_nesting_no_overlap_simple
```


## 5. Summary

- Run core tests regularly during development (`pytest -v`).
- Run FreeCAD integration tests before major changes or releases.
- Use the manual QA checklist when you need to validate end-to-end
  behavior in a FreeCAD GUI session.
- If any step above fails, capture:
  - The exact test command you ran.
  - The console/Report View output.
  - A copy of the CSV or file that triggered the issue.
  And open a bug ticket with this information.
