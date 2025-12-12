# SquatchCut User Guide

Version: v0.1 (UAT Build)
Applies to: FreeCAD 1.0+ and the SquatchCut add-on
Refer to [`docs/Project_Guide_v3.3.md`](Project_Guide_v3.3.md) for the authoritative AI worker, UI, and hydration principles (v3.2 retained for history).

---

## 1. What is SquatchCut?

SquatchCut is a FreeCAD add-on that helps you:

- Import a rectangular parts list (from CSV)
- Define your sheet / panel size
- Automatically nest those parts on the sheet
- Visualize the layout so you can cut it in the shop

It’s designed for:

- Woodworkers
- Cabinet shops
- Makers
- Anyone who hates wasting plywood

You do **not** need to know how to code or use GitHub to use SquatchCut.

---

## 2. Requirements

To use SquatchCut, you’ll need:

- **FreeCAD 1.0+** installed
- The **SquatchCut add-on ZIP** file provided to you
- (Optional) A basic understanding of:
  - Sheet goods (plywood, MDF, etc.)
  - Width/height measurements
  - Metric (mm) or Imperial (inches)

---

## 3. Installing SquatchCut

1. Open **FreeCAD**.
2. Go to **Tools → Add-on Manager**.
3. Click **Install from ZIP**.
4. Browse to and select the SquatchCut ZIP you were given.
5. Wait for the installation to complete.
6. Restart FreeCAD.

After restart, you should see a **SquatchCut** toolbar or menu with:

- A main **SquatchCut** button
- A **Settings** button

If you do not see these, make sure the add-on is enabled in the Add-on Manager.

---

## 4. Basic Concepts

There are three main things SquatchCut manages:

1. **Sheet**
   - The panel or plywood sheet you are cutting from.
   - Example: 4′ × 8′ (1220 × 2440 mm).

2. **Source Parts**
   - Rectangular parts defined in your CSV file.
   - These are the requested pieces you want to cut.

3. **Nested Parts**
   - The placed parts on the sheet after you run nesting.
   - This is the layout you’ll actually cut.

SquatchCut keeps these organized in the FreeCAD document as:

- One sheet object (e.g. `SquatchCut_Sheet`)
- One group containing **source parts**
- One group containing **nested parts**

---

## 5. CSV Format

SquatchCut expects your CSV to have at least the following columns:

- `width`   – numeric value (either mm or inches)
- `height`  – numeric value (either mm or inches)
- `id`      – an identifier (part name or ID)

Optional columns:

- `quantity` – how many of that part (defaults to 1 if missing)
- `label`    – text label for display

### Units

The **CSV units** are controlled in the SquatchCut UI:

- If set to **Metric**, CSV values are treated as **millimeters**.
- If set to **Imperial**, CSV values are treated as **inches**.

Imperial values may support fractional notation depending on your current build (e.g., `48`, `48.5`, `48 3/4`).

---

## 6. First-Time Setup (Settings Panel)

Before your first real nesting session, configure SquatchCut:

1. Click the **Settings** button on the SquatchCut toolbar.
2. Choose your **Measurement System**:
   - **Metric** → all sheet and gap values in mm
   - **Imperial** → sheet and gap values in inches (often fractional)
3. Set your **default sheet size**, for example:
   - 1220 × 2440 mm
   - or 48 × 96 in
4. Set:
   - **Kerf width** – thickness of your saw blade (e.g. 3 mm or ~1/8")
   - **Gap** – spacing between parts (e.g. 2 mm or 1/16")
5. Click the **Save / Apply** button in the settings.

These defaults will be used when you open the main SquatchCut panel.

You can change them later at any time.

---

## 7. Typical Workflow

### Step 1 – Open the SquatchCut Panel

1. Click the **SquatchCut** button in the toolbar.
2. The main Task Panel will appear (usually on the left side).

You’ll see sections for:

- CSV Import
- Sheet & Presets
- Nesting / Results

---

### Step 2 – Set CSV Units & Import Parts

1. In the **CSV Import** section:
   - Select **CSV Units** (Metric or Imperial) to match your file.
2. Choose your CSV file:
   - Use the **Browse** or **Select File** button (exact label may vary).
   - Confirm that the file path appears in the UI.
3. Click **Import Parts**.

What should happen:

- The CSV is parsed.
- A **Source Parts** group is created or rebuilt in the FreeCAD document.
- Rectangles are created for each part.
- The 3D view updates to show the parts (depending on your current camera).

If anything fails, check the on-screen status message and the FreeCAD report view.

---

### Step 3 – Check Parts in the Model

After import:

- Look for a group called something like `SquatchCut_SourceParts`.
- Expand it in the **Model** tree to see individual part rectangles.
- Optionally, select a few parts and check their **Data** properties to confirm:
  - width
  - height
  - label or id

If widths/heights look wrong, double-check:

- CSV units (Metric vs Imperial)
- The CSV columns and formatting

---

### Step 4 – Set Sheet Size & Presets

In the **Sheet & Presets** section:

1. Check that the **Sheet Width** and **Sheet Height** fields match your panel size.
   - On first run, these may come from your saved defaults (e.g. 4′ × 8′).
2. Use the **Preset** combo box if desired:
   - `None / Custom`
   - `4′ x 8′`
   - `2′ x 4′`
   - `5′ x 10′`
3. Behavior:
   - When you pick a preset:
     - The sheet width/height fields update to that preset.
     - Defaults in settings **do not** change.
   - When you manually edit width/height:
     - The preset selection resets to `None / Custom`.

After changing sheet size, the sheet object in the 3D view should resize accordingly.

---

### Step 5 – Adjust Kerf & Gaps (if available in UI)

If the main panel exposes **kerf** and **gap** fields:

- **Kerf** – saw blade thickness:
  - Larger kerf means fewer parts may fit on a sheet.
- **Gap** – spacing between parts:
  - Prevents paper-thin slivers between cuts.

Set these according to your tool and comfort level.

---

### Step 6 – Run Nesting

1. In the **Nesting** section, click **Run Nesting**.
2. SquatchCut will:
   - Read your sheet size and all source parts.
   - Run the nesting algorithm.
   - Place rectangles onto the sheet as **nested parts**.

In the FreeCAD document:

- A `SquatchCut_NestedParts` group should appear or be rebuilt.
- Only the **most recent** nesting run should be visible in that group:
  - Old nested layouts are cleared each run.

---

### Step 7 – Inspect the Layout

Use the 3D view to verify:

- Parts are all inside the sheet.
- No obvious overlaps (rectangles shouldn’t be on top of each other).
- Orientation and sizing look correct.

You can:

- Toggle visibility of the **Source Parts** group to see just the nested layout.
- Select individual nested parts to inspect their properties.

---

### Step 8 – Save / Export

SquatchCut uses ordinary FreeCAD geometry, so you can:

- Save the entire FreeCAD document as usual:
  **File → Save**
- Export to DXF/SVG/PDF using:
  **File → Export**

Recommended workflow:

- Save a “layout copy” of your file before heavy editing.
- Use **File → Export** to create:
  - DXF for CAD/CAM
  - SVG or PDF for printing and shop drawings

---

## 8. New UI Features & Keyboard Shortcuts

### Keyboard Shortcuts

SquatchCut now includes keyboard shortcuts for faster workflow:

- **Ctrl+I** - Import CSV file
- **Ctrl+R** or **F5** - Run nesting algorithm
- **Ctrl+E** - Export cutlist to CSV
- **Ctrl+Shift+S** - Open SquatchCut settings
- **Ctrl+T** - Toggle source panels visibility
- **Ctrl+Shift+R** - Reset view to fit all objects

To see all available shortcuts, use the **Help → Keyboard Shortcuts** menu in SquatchCut.

### Progress Indicators

Long-running operations now show progress indicators:

- **CSV Import** - Shows progress while reading and validating large files
- **Nesting Operations** - Displays progress during complex nesting calculations
- **Shape Creation** - Progress bar when creating many panel shapes
- **Export Operations** - Progress feedback during file exports

These indicators help you understand when operations are working and provide estimated completion times for large datasets.

## Advanced Features

SquatchCut includes several advanced features for professional workflows:

### Genetic Algorithm Optimization
For complex layouts requiring maximum material utilization:
- **Intelligent Evolution**: Uses genetic algorithms to find optimal part arrangements
- **Grain Direction Support**: Respects wood grain orientation for structural integrity
- **Configurable Parameters**: Adjust population size, generations, and optimization time
- **Automatic Activation**: Enabled through settings for challenging layouts

### Enhanced Export Capabilities
Professional export options for various workflows:
- **SVG with Cut Lines**: Visual cutting guides for manual operations
- **DXF Export**: CAD-compatible format for CNC and automated cutting
- **Waste Area Highlighting**: Identify unused material for future projects
- **Multi-Sheet Layouts**: Organized output for complex projects

### Smart Cut Optimization
Automated cutting sequence planning:
- **Optimal Cut Order**: Minimizes material handling and setup time
- **Rip and Crosscut Planning**: Follows woodworking best practices
- **Time Estimation**: Realistic cutting time predictions
- **Cut Length Optimization**: Reduces unnecessary cuts

### Quality Assurance
Comprehensive layout validation:
- **Overlap Detection**: Identifies conflicting part placements
- **Bounds Checking**: Ensures all parts fit within sheet boundaries
- **Spacing Validation**: Verifies minimum spacing requirements
- **Quality Scoring**: Overall layout quality assessment (0-100)
- **Detailed Reports**: Actionable feedback for improvements

### Performance Enhancements
Optimizations for large datasets:
- **Intelligent Caching**: Avoids redundant calculations
- **Multi-threading**: Parallel processing for complex operations
- **Memory Optimization**: Efficient handling of large part lists
- **Progress Tracking**: Real-time feedback for long operations

### Accessing Advanced Features
Most advanced features are automatically enabled when beneficial:
- **Genetic Algorithm**: Enable in Settings → Advanced → Use Genetic Optimization
- **Cut Sequences**: Enable in Settings → Advanced → Generate Cut Sequences
- **Quality Reports**: Automatically generated after nesting operations
- **Enhanced Exports**: Available through standard export commands

For detailed information about advanced features, see the [Advanced Features Guide](advanced_features.md).

### Enhanced Error Messages

SquatchCut now provides clearer, more helpful error messages:

- **Validation Errors** - Specific guidance on fixing input problems
- **File Errors** - Clear explanations of file format or path issues
- **Nesting Errors** - Detailed information about why nesting failed
- **Recovery Actions** - Step-by-step instructions to resolve problems

When errors occur, look for:
- A clear description of what went wrong
- Specific details about the problem
- Actionable steps to fix the issue

### Performance Improvements

For large datasets (1000+ parts), SquatchCut now includes:

- **Memory Optimization** - Efficient handling of large CSV files
- **Performance Monitoring** - Automatic detection of slow operations
- **Resource Warnings** - Alerts when working with very large datasets
- **Batch Processing** - Improved handling of complex nesting jobs

You'll see performance information in the FreeCAD Report View for operations that take longer than expected.

### Enhanced Nesting View

The nesting visualization has been improved with:

- **Color Schemes** - Multiple color palettes including high-contrast options
- **Display Options** - Choose between transparent, wireframe, or solid part display
- **Sheet Layouts** - Options for side-by-side or stacked sheet arrangements
- **Part Labels** - Optional display of part IDs and names on nested pieces
- **Quick Toggles** - Easy controls for common view adjustments

Access these options through the nesting view preferences in the Settings panel.

---

## 9. Troubleshooting

### I don’t see the SquatchCut toolbar

- Make sure the add-on is installed via the Add-on Manager.
- Restart FreeCAD after installation.
- Check **View → Toolbars** and ensure **SquatchCut** is enabled.

### CSV import fails or parts look wrong

- Confirm the CSV has `width`, `height`, and `id` columns.
- Check that you selected the correct **CSV Units** (Metric vs Imperial).
- Make sure there are no extra header rows or strange formatting.

### I get multiple sheets or random junk in the tree

- In a current UAT build, there should only be:
  - One sheet object,
  - One Source group,
  - One Nested group.
- If you see duplicates, note:
  - The steps that caused it,
  - FreeCAD version, OS, and CSV file,
  - Then report it back using the UAT Feedback instructions.

### Nesting runs but nothing appears

- Verify that there are:
  - Imported source parts,
  - A non-zero sheet size.
- Check the FreeCAD report view for error messages.
- Try with a small, simple CSV (e.g. a few parts) to isolate issues.

---

## 10. Getting Help / Reporting Issues

If you’re part of a UAT or volunteer test group:

- Follow the instructions in `UAT_Prep_Instructions.md` and `UAT_Checklist.md`.
- Use the provided **feedback form or instructions** from your test coordinator.
- Include:
  - What you were trying to do
  - What you expected
  - What actually happened
  - Screenshots if possible

---

Thanks for helping test SquatchCut!
