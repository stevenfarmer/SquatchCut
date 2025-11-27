# Commands & Tools

## Add Shapes
- Extracts selected rectangles/shapes from the active document into panels.
- Use when you have geometry in FreeCAD to convert into panel data.
- Caveats: Works on supported planar shapes; skips unsupported objects.

## Import CSV
- Loads panel data from a CSV file.
- Use when panel dimensions are defined externally.
- Caveats: Ensure required columns (id, width, height, optional grain_direction).

## Run Nesting
- Executes multi-sheet rectangular nesting for current panels.
- Use after panels are gathered and sheet size is set.
- Caveats: Panels must have valid dimensions; uses simple Skyline/Guillotine hybrid.

## Sheet Size
- Configures sheet dimensions and kerf.
- Use before nesting to define material size.
- Caveats: Defaults to 2440 x 1220 if not set.

## Export Report
- Generates PDF/CSV reports from the last nesting run.
- Use after nesting completes.
- Caveats: Requires a completed nesting run in the current session.

## Preferences
- Accesses SquatchCut preference options.
- Use to adjust default behaviors.
- Caveats: Minimal UI in MVP; sheet size dialog handles key settings.
