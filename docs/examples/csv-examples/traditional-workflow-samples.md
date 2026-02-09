# Traditional CSV Workflow Examples

**Sample CSV files and workflows for standard rectangular nesting**

## Overview

This collection provides sample CSV files and complete workflows for traditional rectangular part nesting in SquatchCut. These examples demonstrate best practices for CSV-based workflows and serve as templates for common woodworking projects.

## Sample CSV Files

### 1. Basic Kitchen Cabinet Parts

**File:** `kitchen_cabinet_basic.csv`

```csv
id,width,height,quantity,label,material
door_upper_1,24,30,2,Upper Cabinet Door,Maple Plywood
door_upper_2,30,30,4,Upper Cabinet Door,Maple Plywood
door_base_1,24,30,3,Base Cabinet Door,Maple Plywood
door_base_2,18,30,2,Base Cabinet Door,Maple Plywood
shelf_upper,23,12,6,Upper Shelf,Maple Plywood
shelf_base,23,24,4,Base Shelf,Maple Plywood
back_panel_upper,24,30,2,Upper Back Panel,Birch Plywood
back_panel_base,24,30,3,Base Back Panel,Birch Plywood
drawer_front,18,6,4,Drawer Front,Maple Plywood
drawer_side,22,6,8,Drawer Side,Birch Plywood
drawer_back,17,6,4,Drawer Back,Birch Plywood
drawer_bottom,17,22,4,Drawer Bottom,Birch Plywood
```

**Project Details:**
- **Parts:** 12 different components, 42 total pieces
- **Material:** Mixed plywood types
- **Thickness:** 3/4" (18mm) assumed
- **Expected Sheets:** 2-3 sheets of 4'×8' plywood
- **Utilization Target:** 75-85%

### 2. Bookshelf Project

**File:** `bookshelf_project.csv`

```csv
id,width,height,quantity,label,notes
side_panel,12,72,2,Side Panel,Full height sides
top_bottom,36,12,2,Top/Bottom Panel,Horizontal spans
shelf_fixed,34.5,12,2,Fixed Shelf,Dadoed into sides
shelf_adjustable,34.5,12,4,Adjustable Shelf,Shelf pin holes
back_panel,36,72,1,Back Panel,1/4 inch plywood
face_frame_stile,2,72,2,Face Frame Stile,Solid wood
face_frame_rail,32,2,3,Face Frame Rail,Solid wood
```

**Project Details:**
- **Parts:** 7 different components, 16 total pieces
- **Style:** Traditional face frame bookshelf
- **Material:** Mixed (plywood + solid wood)
- **Expected Sheets:** 1 sheet 4'×8' + solid wood boards
- **Utilization Target:** 80-90%

### 3. Workshop Storage Cabinet

**File:** `workshop_storage.csv`

```csv
id,width,height,quantity,label,material,thickness
case_side,24,84,2,Case Side,Birch Plywood,0.75
case_top,48,24,1,Case Top,Birch Plywood,0.75
case_bottom,48,24,1,Case Bottom,Birch Plywood,0.75
case_back,48,84,1,Case Back,Birch Plywood,0.25
shelf_large,46.5,23.25,4,Large Shelf,Birch Plywood,0.75
shelf_small,22.5,23.25,2,Small Shelf,Birch Plywood,0.75
door_large,24,42,2,Large Door,Birch Plywood,0.75
door_small,24,20,2,Small Door,Birch Plywood,0.75
drawer_front,22,8,3,Drawer Front,Birch Plywood,0.75
drawer_side,22,8,6,Drawer Side,Birch Plywood,0.5
drawer_back,21,8,3,Drawer Back,Birch Plywood,0.5
drawer_bottom,21,21,3,Drawer Bottom,Birch Plywood,0.25
```

**Project Details:**
- **Parts:** 12 different components, 30 total pieces
- **Features:** Mixed door sizes, drawers, adjustable shelves
- **Materials:** Multiple plywood thicknesses
- **Expected Sheets:** 2-3 sheets various thicknesses
- **Utilization Target:** 70-80%

## Workflow Examples

### Workflow 1: Basic Kitchen Cabinet

**Step-by-Step Process:**

1. **Prepare CSV File**
   ```
   - Create kitchen_cabinet_basic.csv
   - Verify all dimensions are in consistent units
   - Include quantity for multiple identical parts
   - Add descriptive labels for shop identification
   ```

2. **SquatchCut Setup**
   ```
   - Open SquatchCut TaskPanel
   - Set CSV Units to match your file (Imperial/Metric)
   - Import kitchen_cabinet_basic.csv
   - Verify 42 parts detected correctly
   ```

3. **Configure Sheet and Cutting**
   ```
   Sheet Size: 48" × 96" (1220mm × 2440mm)
   Kerf Width: 1/8" (3.2mm) - table saw blade
   Gap/Margin: 1/4" (6.4mm) - safe cutting clearance
   ```

4. **Run Nesting**
   ```
   - Click "Run Nesting"
   - Review layout for efficiency
   - Check that all parts fit within sheet boundaries
   - Verify no overlapping parts
   ```

5. **Export Results**
   ```
   - Export SVG for cutting templates
   - Export CSV cutlist for shop documentation
   - Save FreeCAD file for future reference
   ```

**Expected Results:**
- **Utilization:** 78-85%
- **Sheets Required:** 2-3 sheets
- **Processing Time:** < 5 seconds
- **Parts Placed:** All 42 parts

### Workflow 2: Multi-Thickness Project

**Challenge:** Workshop storage cabinet with multiple plywood thicknesses

**Solution:** Separate nesting runs by thickness

1. **Separate by Thickness**
   ```
   Create separate CSV files:
   - workshop_storage_3_4.csv (3/4" parts)
   - workshop_storage_1_2.csv (1/2" parts)
   - workshop_storage_1_4.csv (1/4" parts)
   ```

2. **Nest Each Thickness Separately**
   ```
   Run 1: 3/4" parts (main structure)
   - 18 parts total
   - 1-2 sheets of 3/4" plywood

   Run 2: 1/2" parts (drawer components)
   - 9 parts total
   - 1 sheet of 1/2" plywood

   Run 3: 1/4" parts (backs and bottoms)
   - 4 parts total
   - 1 sheet of 1/4" plywood
   ```

3. **Coordinate Cutting**
   ```
   - Plan cutting sequence across thicknesses
   - Group similar operations (all rip cuts, then crosscuts)
   - Consider setup time between thickness changes
   ```

### Workflow 3: Large Production Run

**Scenario:** 10 identical kitchen cabinets (420 total parts)

**Strategy:** Batch processing for efficiency

1. **Scale Up Quantities**
   ```
   Original: door_upper_1,24,30,2,Upper Cabinet Door
   Scaled:   door_upper_1,24,30,20,Upper Cabinet Door
   ```

2. **Optimize Sheet Usage**
  ```
  - Try different sheet sizes (5'×10' vs 4'×8')
  - Adjust margins for production cutting methods
  - Consider appearance requirements for visible faces
  ```

3. **Production Planning**
   ```
   - Group identical parts for batch cutting
   - Plan material ordering (number of sheets needed)
   - Coordinate with delivery schedules
   - Plan shop workflow and setup changes
   ```

## CSV Format Guidelines

### Required Columns

**Minimum Required:**
```csv
id,width,height
part_001,24,30
part_002,18,24
```

**Recommended Format:**
```csv
id,width,height,quantity,label,material
part_001,24,30,2,Upper Door,Maple Plywood
part_002,18,24,1,Side Panel,Birch Plywood
```

### Optional Columns

**Extended Format:**
```csv
id,width,height,quantity,label,material,thickness,allow_rotate,notes
door_1,24,30,2,Cabinet Door,Maple,0.75,1,Raised panel style
shelf_1,23,12,4,Shelf,Birch,0.75,0,Adjustable shelf pins
```

**Column Descriptions:**
- **id**: Unique identifier (required)
- **width**: Part width in current units (required)
- **height**: Part height in current units (required)
- **quantity**: Number of identical parts (default: 1)
- **label**: Descriptive name for shop use
- **material**: Wood species or material type
- **thickness**: Material thickness (for reference)
- **allow_rotate**: Use 1/true/yes to allow 90° rotations
- **notes**: Additional manufacturing notes

### Units and Formatting

**Imperial Format:**
```csv
id,width,height,label
door,24,30,Cabinet Door
shelf,23.5,12,Shelf
rail,32.25,2,Face Frame Rail
```

**Metric Format:**
```csv
id,width,height,label
door,610,762,Cabinet Door
shelf,597,305,Shelf
rail,819,51,Face Frame Rail
```

**Fractional Inches (if supported):**
```csv
id,width,height,label
door,24,30,Cabinet Door
shelf,23 1/2,12,Shelf
rail,32 1/4,2,Face Frame Rail
```

## Common Issues and Solutions

### Issue 1: Parts Don't Fit

**Symptoms:**
- Some parts marked as "unplaced"
- Warning messages about sheet size
- Poor utilization with large waste areas

**Solutions:**
```
1. Check sheet size settings
   - Verify width/height are correct
   - Try larger standard sizes (5'×10')

2. Reduce margins if appropriate
   - Decrease kerf width if using thinner blade
   - Reduce gap for more precise cutting methods

3. Split into multiple sheets
   - Group similar-sized parts
   - Prioritize critical parts for first sheet
```

### Issue 2: Poor Material Utilization

**Symptoms:**
- Utilization below 70%
- Large unused areas on sheet
- Inefficient part arrangement

**Solutions:**
```
1. Optimize part mix
   - Add smaller parts to fill gaps
   - Remove oversized parts for separate cutting

2. Try different sheet orientations
   - Rotate sheet dimensions (48×96 vs 96×48)
   - Consider non-standard sheet sizes

3. Adjust cutting parameters
   - Reduce margins if cutting method allows
   - Use thinner kerf blade if available
```

### Issue 3: CSV Import Errors

**Symptoms:**
- "File format error" messages
- Missing parts after import
- Incorrect dimensions displayed

**Solutions:**
```
1. Check CSV format
   - Ensure comma separation (not semicolon)
   - Verify column headers match expected format
   - Remove extra spaces or special characters

2. Verify units consistency
   - All dimensions in same units (inches or mm)
   - CSV units setting matches file content

3. Validate data
   - No negative dimensions
   - Reasonable part sizes for material
   - Quantities are positive integers
```

## Performance Optimization

### For Large Part Counts (500+ parts)

**Strategies:**
1. **Batch Processing**
   - Process in groups of 100-200 parts
   - Separate by size categories
   - Use multiple sheets as needed

2. **Simplify Data**
   - Remove unnecessary columns
   - Round dimensions to reasonable precision
   - Combine identical parts with quantities

3. **System Optimization**
   - Close other applications
   - Use SSD storage for better I/O
   - Ensure adequate RAM (8GB+ recommended)

### For Complex Projects

**Approaches:**
1. **Hierarchical Planning**
   - Separate by material type/thickness
   - Group by cutting method requirements
   - Prioritize by project timeline

2. **Iterative Refinement**
   - Start with rough layout
   - Refine margins and kerf settings
   - Optimize sheet sizes based on results

## Quality Control Checklist

### Pre-Nesting Validation
- [ ] CSV file opens correctly in spreadsheet software
- [ ] All required columns present (id, width, height)
- [ ] Dimensions are reasonable for material type
- [ ] Quantities are positive integers
- [ ] No duplicate part IDs (unless intentional)
- [ ] Units are consistent throughout file

### Post-Nesting Validation
- [ ] All parts placed within sheet boundaries
- [ ] No overlapping parts visible
- [ ] Utilization meets project targets (>70%)
- [ ] Cutting sequence is practical
- [ ] Export files are dimensionally accurate

### Production Readiness
- [ ] Material quantities calculated and ordered
- [ ] Cutting sequence planned and documented
- [ ] Tool setup requirements identified
- [ ] Quality control measures established
- [ ] Backup plans for material shortages

## Files Included

This example collection includes:

**CSV Files:**
- `kitchen_cabinet_basic.csv` - Basic kitchen cabinet parts
- `bookshelf_project.csv` - Traditional bookshelf components
- `workshop_storage.csv` - Multi-thickness storage cabinet
- `production_run_example.csv` - Large quantity production example

**Documentation:**
- `csv_format_guide.md` - Detailed CSV formatting guidelines
- `troubleshooting_guide.md` - Common issues and solutions
- `optimization_tips.md` - Performance and efficiency tips

**Templates:**
- `project_template.csv` - Blank template with all columns
- `simple_template.csv` - Minimal required columns only
- `production_template.csv` - Extended format for production use

## Next Steps

After working through these examples:

1. **Try Shape-Based Nesting**: Explore [Cabinet Maker Workflow](../cabinet-projects/face-frame-example.md)
2. **Advanced Features**: Learn about [Performance Optimization](../performance-benchmarks/complexity-test-suite.md)
3. **Custom Workflows**: Develop your own project templates
4. **Integration**: Combine CSV and shape-based approaches

---

*These examples demonstrate traditional CSV-based workflows in SquatchCut. For advanced shape-based nesting, see the [Shape-Based Nesting Guide](../../user/cabinet-maker-workflow.md).*
