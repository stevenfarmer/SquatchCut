# SquatchCut Quick Start

> TL;DR for people who don’t want a novel. Applies to SquatchCut 0.3.x on FreeCAD 0.21+. Shape-based nesting is available as an **experimental** flow; use the CSV/rectangular workflow for production jobs.

---

## 1. Install

1. Open **FreeCAD**.
2. Go to **Tools → Add-on Manager → Install from ZIP**.
3. Select the SquatchCut ZIP you were given.
4. Restart FreeCAD.

You should now see a **SquatchCut** toolbar with:

- **SquatchCut** (main panel)
- **Settings**

---

## 2. Configure Defaults (One Time)

1. Click **Settings** on the SquatchCut toolbar.
2. Choose:
   - Measurement system (Metric or Imperial)
   - Default sheet size (e.g. 48" × 96" or 1220 × 2440 mm)
   - Kerf and gap
3. Click **Save / Apply**.

---

## 3. Basic Workflows

SquatchCut supports two main workflows:

### 3A. Traditional CSV Workflow (Rectangular Parts – recommended)

1. **Open the panel**
   - Click **SquatchCut**.

2. **Import parts from CSV**
   - In the **Input** section:
     - Confirm **CSV Units** matches your file (follows your measurement system).
     - Click **Import CSV** and pick your CSV file.
   - Check that a **Source Parts** group appears in the model tree after the file loads.

3. **Set sheet size and run nesting**
   - Confirm sheet width/height fields match your panel.
   - Click **Run Nesting**.
   - A **Nested Parts** group appears, containing the layout.

4. **Review and export**
   - Inspect the layout in the 3D view.
   - Save your file (**File → Save**).
   - Export as needed (**File → Export**, DXF/SVG/PDF).

### 3B. Shape-Based Nesting (Complex Parts – experimental)

1. **Design parts in FreeCAD**
   - Use Part Design workbench to create solid bodies.
   - Give parts descriptive names.

2. **Select shapes**
   - Click **SquatchCut** to open the panel.
   - In the **Input** section, click **Select Shapes**.
   - Choose which parts to nest from the dialog.

3. **Configure and nest**
   - Set sheet size and cutting parameters.
   - Click **Run Nesting**.
   - SquatchCut automatically chooses a nesting mode; complex shapes take longer.

4. **Export for production**
   - Use **Export Report** (PDF/CSV) or **Export Cutlist** from the SquatchCut toolbar.
   - Geometry is standard FreeCAD geometry; you can also use **File → Export** if needed.

**For detailed shape-based workflows, see the [Cabinet Maker Guide](user/cabinet-maker-workflow.md).**

---

## 4. If Something Breaks

- Note the steps you took and any errors in the FreeCAD report view.
- Take a screenshot of the model tree and the layout.
- Send your notes and files to your SquatchCut contact or follow the UAT feedback instructions.

That’s it. Import → Set Sheet → Nest → Export.
