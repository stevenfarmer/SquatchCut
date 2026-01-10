# SquatchCut User Guide

Applies to SquatchCut **0.3.x** on **FreeCAD 0.21+**. The CSV/rectangular workflow is production-ready; the shape-based workflow is an **experimental preview**. For AI/worker rules, see [`docs/Project_Guide_v3.3.md`](Project_Guide_v3.3.md).

---

## 1. What is SquatchCut?

SquatchCut is a FreeCAD add-on that helps you:

- Import a rectangular parts list from CSV
- Define your sheet/panel size
- Automatically nest those parts on the sheet
- Visualize and export the layout for the shop

---

## 2. Requirements

- FreeCAD **0.21+** installed
- SquatchCut 0.3.x ZIP installed via Add-on Manager (see `docs/getting-started/installation.md`)
- Basic familiarity with sheet goods and measurements (mm or fractional inches)

---

## 3. Core Concepts

- **Measurement system**: Choose metric (mm) or imperial (fractional inches). Internally everything is stored in millimeters.
- **Sheet defaults & presets**: Defaults are set in **Settings** and only change when you save them there. The preset dropdown starts at `None / Custom`; choosing a preset updates the sheet fields but does not overwrite your defaults.
- **Document objects**: One sheet object plus two groups:
  - `SquatchCut_SourceParts` – originals from CSV or selected shapes
  - `SquatchCut_NestedParts` – the latest layout

---

## 4. Install (quick reminder)

1. Open **FreeCAD** → **Tools → Add-on Manager → Install from ZIP**.
2. Pick the SquatchCut ZIP.
3. Restart FreeCAD; ensure the **SquatchCut** toolbar/menu appears.

Full details: `docs/getting-started/installation.md`.

---

## 5. Production Workflow (CSV / Rectangular Parts)

1. **Open the panel**
   - Click **SquatchCut** on the toolbar.

2. **Import parts from CSV**
   - In **Input**, click **Import CSV** and select your file.
   - CSV units follow your active measurement system; some builds auto-detect units and update the selector.
   - A `SquatchCut_SourceParts` group should appear with one entry per row.
   - Required columns: `width`, `height`, `id`; optional: `quantity`, `label`, `allow_rotate`.

3. **Set sheet size & presets**
   - Confirm sheet width/height fields match your panel.
   - Use the preset dropdown if you want `4′×8′`, `2′×4′`, or `5′×10′`.
   - Manual edits return the preset to `None / Custom`.

4. **Kerf & gap**
   - Kerf = blade/bit thickness; gap = spacing around parts. Set in Settings or in-panel fields (when present). Larger values reduce how many parts fit.

5. **Run nesting**
   - Click **Run Nesting**.
   - SquatchCut hides sources, builds `SquatchCut_NestedParts`, and clears previous layouts.

6. **Inspect**
   - Toggle source vs nested groups to compare.
   - Use **Show Source View** to focus on originals or **Reset View** to refit.

7. **Export**
   - Use SquatchCut commands: **Export Report** (PDF+CSV) or **Export Cutlist** (shop-friendly CSV). These use the canonical exporter.
   - Geometry is standard FreeCAD geometry, so **File → Export** (DXF/SVG/PDF) also works if you need raw geometry.

---

## 6. Shape-Based Workflow (Experimental Preview)

Use this when you have curved/non-rectangular parts modeled in FreeCAD. Expect longer runs; start with a small set of parts.

1. **Model parts as solids** in Part Design (bodies with valid Shapes).
2. **Open SquatchCut** and click **Select Shapes** in **Input**.
3. **Choose parts** in the shape selection dialog. Complexity labels help you start small.
4. **Set sheet + kerf/gap**, then click **Run Nesting**. The engine chooses a mode (rectangular/hybrid/geometric) based on detected complexity.
5. **Review results & export** using the same commands as the CSV workflow.

For deeper guidance, see the [Cabinet Maker Workflow Guide](user/cabinet-maker-workflow.md) and [Shape-Based Reference](user/shape-based-nesting-reference.md).

---

## 7. Shortcuts & Progress

- **Ctrl+I** Import CSV
- **Ctrl+R / F5** Run nesting
- **Ctrl+E** Export cutlist (CSV)
- **Ctrl+Shift+S** Open SquatchCut settings
- **Ctrl+T** Toggle source panels visibility
- **Ctrl+Shift+R** Reset view

Use the **Keyboard Shortcuts** command in the toolbar to view them in FreeCAD. Long-running CSV imports, nesting, and exports show progress dialogs in the UI.

---

## 8. Troubleshooting

- **Toolbar missing:** Check Add-on Manager, restart FreeCAD, then enable **View → Toolbars → SquatchCut**.
- **CSV import looks wrong:** Confirm `width/height/id` headers, measurement system, and that the file has no extra header rows.
- **Duplicate sheets/groups:** Only one sheet + one source + one nested group should exist. If you see extras, note the steps and share a sample file when reporting.
- **Nesting produces nothing:** Ensure parts are loaded, sheet size > 0, and check the FreeCAD report view for errors. Try a small CSV to isolate the issue.

---

## 9. Getting Help / Reporting Issues

- For UAT/volunteer testing, follow `docs/UAT_Prep_Instructions.md` and `docs/UAT_Checklist.md`.
- When reporting issues, include: what you tried, what you expected, what happened, your OS + FreeCAD version, and a small CSV (or FCStd) if possible.

Thanks for helping test SquatchCut!
