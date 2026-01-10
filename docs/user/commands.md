# Commands & Tools

## Add Shapes
- Extracts selected rectangles/shapes from the active document into panels.
- Use when you have geometry in FreeCAD to convert into panel data.
- Caveats: Works on supported planar shapes; skips unsupported objects.

## Import CSV
- Loads panel data from a CSV file.
- Use when panel dimensions are defined externally.
- Caveats: Ensure required columns (id, width, height; optional grain_direction; optional allow_rotate). Missing `allow_rotate` defaults to no rotation. Invalid rows are skipped with warnings. CSV units follow your measurement system (some builds auto-detect and update it); adjust measurement system in Settings before importing. Internally everything is stored in mm.

## Run Nesting
- Executes multi-sheet rectangular nesting for current panels.
- Use after panels are gathered and sheet size is set.
- Caveats: Panels must have valid dimensions; uses simple Skyline/Guillotine hybrid with per-part 0°/90° rotation. Kerf applies between parts; gap/halo pushes parts off sheet edges. If nothing is selected, all tagged panels are used; if a subset is selected, only that subset nests.

## Sheet Size
- Configures sheet dimensions and spacing.
- Use before nesting to define material size.
- Caveats: Defaults to 2440 x 1220 if not set. Kerf (between parts) and gap/halo (around parts/edges) default to 0 and can be set on the document. Sheet size spin boxes display the current units preference (mm or in).

## Export Report
- Generates PDF/CSV reports from the last nesting run.
- Use after nesting completes.
- Caveats: Requires a completed nesting run in the current session.

## Export Nesting CSV
- Saves the most recent nesting layout as a CSV (choose path via save dialog).
- Use after nesting completes.
- Caveats: Writes sheet index, part id, true width/height, x/y, and angle (0/90). Kerf/gap are layout-only and not exported.

## Export Cutlist (CSV)
- Generates a shop-friendly cutlist from the current nested sheets and lets you save it as CSV.
- Use after nesting completes to hand a rip/crosscut plan to the shop floor.
- Caveats: Cut lines are de-duplicated within a 4 mm tolerance and only emitted when they cross at least one panel.

## Toggle Source Panels
- Shows/hides the original SourcePanels group.
- Use to reveal or hide the originals that were offset left when nesting.
- Caveats: SourcePanels remains unchanged; clones on sheets are independent.

## Preferences
- Accesses SquatchCut preference options.
- Use to adjust default behaviors, including units preference (metric/imperial).
- Caveats: Minimal UI in MVP; sheet size dialog handles key settings.
