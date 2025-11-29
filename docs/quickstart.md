# SquatchCut Quick Start

> TL;DR for people who don’t want a novel.

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

## 3. Basic Workflow

1. **Open the panel**  
   - Click **SquatchCut**.

2. **Import parts from CSV**
   - In the **CSV Import** section:
     - Set **CSV Units** to **Metric** or **Imperial**.
     - Pick your CSV file.
     - Click **Import Parts**.
   - Check that a **Source Parts** group appears in the model tree.

3. **Set sheet size**
   - Confirm sheet width/height fields match your panel.
   - Optionally choose a preset:
     - `None / Custom`
     - `4′ x 8′`
     - `2′ x 4′`
     - `5′ x 10′`
   - Editing width/height manually should switch preset to `None / Custom`.

4. **Run nesting**
   - Click **Run Nesting**.
   - A **Nested Parts** group appears, containing the layout.

5. **Review and export**
   - Inspect the layout in the 3D view.
   - Save your file (**File → Save**).
   - Export as needed (**File → Export**, DXF/SVG/PDF).

---

## 4. If Something Breaks

- Note the steps you took and any errors in the FreeCAD report view.
- Take a screenshot of the model tree and the layout.
- Send your notes and files to your SquatchCut contact or follow the UAT feedback instructions.

That’s it. Import → Set Sheet → Nest → Export.
