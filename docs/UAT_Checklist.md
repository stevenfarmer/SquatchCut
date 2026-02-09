# SquatchCut UAT Checklist

Version: UAT v0.1  
Audience: Volunteer / UAT testers  
Refer to [`docs/developer_guide.md`](developer_guide.md) for the authoritative testing, UI, and AI worker expectations (v3.2 retained for history).

Instructions:

- Follow each step in order.
- For each step, mark **Pass** (✅) or **Fail** (❌) in the table.
- Add notes if anything is confusing, broken, or unexpected.

You may print this page or fill it in digitally.

---

## Tester Info

- **Name:**  
- **Date:**  
- **OS & Version (e.g., Windows 11, macOS 15):**  
- **FreeCAD Version:**  
- **SquatchCut Build / ZIP Name:**  

---

## Legend

- ✅ = Worked as expected
- ❌ = Didn’t work or was confusing
- N/A = Not applicable or skipped

---

## Checklist

| # | Step                                                                                              | Result (✅/❌/N/A) | Notes (what happened?) |
|---|---------------------------------------------------------------------------------------------------|--------------------|------------------------|
| 1 | Start FreeCAD.                                                                                   |                    |                        |
| 2 | Confirm you see a **SquatchCut** toolbar/menu with **SquatchCut** and **Settings** buttons.      |                    |                        |
| 3 | Click **Settings**. Verify the settings panel opens without errors.                              |                    |                        |
| 4 | In Settings, set your measurement system (Metric or Imperial) and a default sheet size.          |                    |                        |
| 5 | Save/apply settings and close the Settings panel.                                                |                    |                        |
| 6 | Click the main **SquatchCut** button. Confirm the main panel opens without errors.               |                    |                        |
| 7 | In the main panel, confirm you see sections for CSV import, sheet/presets, and nesting.          |                    |                        |
| 8 | Set **CSV Units** to match `test_parts.csv` (as instructed).                                     |                    |                        |
| 9 | Use the file picker to select `test_parts.csv`.                                                  |                    |                        |
|10 | Click **Import Parts**. No error dialog should appear.                                           |                    |                        |
|11 | In the FreeCAD **Model** tree, confirm a **Source Parts** group appears and contains part items. |                    |                        |
|12 | Change the sheet size using the sheet width/height fields (without using a preset).              |                    |                        |
|13 | Verify that the visible sheet in the 3D view updates to the new size.                            |                    |                        |
|14 | Select a sheet **preset** (e.g., 4′ x 8′). Confirm the sheet fields update to match the preset.  |                    |                        |
|15 | Manually change the sheet width or height again and confirm the preset selection returns to "None/Custom". |          |                        |
|16 | Click **Run Nesting**.                                                                           |                    |                        |
|17 | In the **Model** tree, confirm a **Nested Parts** group appears or is rebuilt.                   |                    |                        |
|18 | Confirm nested parts appear on top of the sheet in the 3D view (no parts obviously off-sheet).   |                    |                        |
|19 | Run nesting a second time without changing the CSV. Confirm the Nested Parts group updates rather than duplicating parts. |     |                        |
|20 | Hide the Source Parts group, leaving only sheet + nested layout visible.                          |                    |                        |
|21 | Save the FreeCAD document without errors.                                                        |                    |                        |
|22 | (Optional) Use **File → Export** to export the layout (DXF/SVG/PDF) and confirm the export works. |                   |                        |

---

## Overall Experience

Please briefly describe:

- What worked well?
- What was confusing?
- Any crashes or serious bugs?

---

## Additional Comments

(Use as much space as you need.)

---

End of checklist.
