# SquatchCut UAT – UI Navigation & Core Features

This checklist verifies that SquatchCut works correctly for end-users who don’t write code.  
Please follow the steps in order and mark **Pass** or **Fail** for each item.

If something fails or confuses you, leave a short note.

## Instructions

- Open FreeCAD.
- Make sure SquatchCut is installed.
- Keep this checklist open while performing each step.
- Do **not** skip steps.
- Do **not** fix anything — just observe and record.

---

## UAT Checklist Table

| #  | Action                                                                 | Expected Result                                                                 | Pass/Fail | Notes |
|----|------------------------------------------------------------------------|---------------------------------------------------------------------------------|-----------|-------|
| 1  | Open FreeCAD and load a new or existing document.                      | FreeCAD opens normally.                                                         |           |       |
| 2  | Locate the SquatchCut toolbar/menu/command.                            | SquatchCut commands are visible (Settings, Import CSV, Set Sheet Size).         |           |       |
| 3  | Click **SquatchCut Settings**.                                         | The Tasks panel opens, displaying all settings.                                 |           |       |
| 4  | Review the Settings panel UI.                                          | All fields are readable and not cut off.                                        |           |       |
| 5  | Change a setting (e.g., spacing or sheet default).                     | Setting updates without error.                                                  |           |       |
| 6  | Close and reopen the Settings panel.                                   | Values persist or reset as designed (no errors).                                |           |       |
| 7  | Click **Import CSV**.                                                  | File chooser opens.                                                             |           |       |
| 8  | Select the provided `test_parts.csv`.                                  | CSV imports without errors.                                                     |           |       |
| 9  | Verify imported parts list (if shown).                                 | Data matches the CSV; formatting is correct.                                    |           |       |
| 10 | Click **Set Sheet Size**.                                              | Sheet size dialog or panel appears.                                             |           |       |
| 11 | Enter a valid sheet size.                                              | Size accepted without error.                                                    |           |       |
| 12 | Enter an invalid sheet size (0 or negative).                           | UI blocks the value or shows a clear warning.                                   |           |       |
| 13 | Click **Run Nesting**.                                                 | Nesting runs and completes without crashing.                                    |           |       |
| 14 | Look at the nesting result view.                                       | Parts appear on the sheet successfully.                                         |           |       |
| 15 | Visually inspect for overlapping parts.                                | No parts overlap; spacing looks correct.                                        |           |       |
| 16 | Compare part count to the CSV.                                         | Number of parts placed matches CSV.                                             |           |       |
| 17 | If multiple sheets were used, switch between them.                     | Navigation between sheets works.                                                |           |       |
| 18 | Zoom and pan around the layout.                                        | Smooth interaction; parts stay visible.                                         |           |       |
| 19 | Export the layout (if available).                                      | File exports without error.                                                     |           |       |
| 20 | Open the exported file.                                                | File opens and matches the on-screen result.                                    |           |       |
| 21 | Close FreeCAD without saving.                                          | App closes cleanly.                                                             |           |       |
| 22 | Reopen FreeCAD and repeat steps 2–4.                                   | SquatchCut remains available and functional.                                    |           |       |

---

## Completion

When finished:

- Save this checklist (PDF or exported text)
- Send it along with your notes and screenshots to Steven

Thank you for testing SquatchCut!
