# Cabinet Maker Workflow Guide

**Shape-Based Nesting with FreeCAD and SquatchCut**

Version: 0.3.x (experimental preview)
Feature: Shape-Based Nesting
Applies to: FreeCAD 0.21+ with SquatchCut 0.3.x
Note: Shape-based nesting is still evolving; workflows and UI labels may change.

---

## Overview

This guide walks cabinet makers through the complete workflow of designing furniture parts in FreeCAD and using SquatchCut's shape-based nesting to optimize material usage on sheet goods. Unlike traditional CSV-based workflows that use rectangular approximations, shape-based nesting considers the actual geometry of your parts for maximum material efficiency.

**What You'll Learn:**
- How to design cabinet parts in FreeCAD for optimal nesting
- Using SquatchCut's shape selection interface
- Understanding the difference between rectangular and geometric nesting
- Exporting cutting layouts with accurate shape outlines
- Troubleshooting common shape extraction issues

---

## Prerequisites

Before starting, ensure you have:

- **FreeCAD 0.21+** installed
- **SquatchCut v3.4+** add-on installed
- Basic familiarity with FreeCAD's Part Design workbench
- Understanding of cabinet construction and sheet goods
- Knowledge of your cutting tools (kerf width, capabilities)

---

## Part 1: Designing Cabinet Parts in FreeCAD

### 1.1 Setting Up Your FreeCAD Document

1. **Create a New Document**
   - Open FreeCAD
   - File → New to create a new document
   - Save immediately with a descriptive name (e.g., "Kitchen_Cabinet_Doors.FCStd")

2. **Choose Your Measurement System**
   - Go to Edit → Preferences → General → Units
   - Select your preferred system:
     - **Metric**: Millimeters for precise measurements
     - **Imperial**: Inches for traditional woodworking
   - SquatchCut will automatically detect and use your document's measurement system

3. **Switch to Part Design Workbench**
   - Use the workbench dropdown to select "Part Design"
   - This provides the tools needed for creating solid cabinet parts

### 1.2 Creating Cabinet Parts

**Best Practices for Shape-Based Nesting:**

1. **Create Real 3D Parts**
   - Use Pad operations to create parts with actual thickness
   - Avoid sketches or 2D shapes - SquatchCut needs solid objects
   - Typical cabinet part thickness: 18-25mm (3/4" - 1")

2. **Design for Nesting Efficiency**
   ```
   Good Practices:
   ✓ Create parts as separate Body objects
   ✓ Use consistent thickness across similar parts
   ✓ Plan part orientation for consistent appearance
   ✓ Consider kerf compensation in your design

   Avoid:
   ✗ Compound objects or assemblies
   ✗ Parts with internal voids that won't nest well
   ✗ Extremely complex curves that slow processing
   ```

3. **Naming Convention**
   - Use descriptive labels: "Door_Left_Upper", "Shelf_Fixed_Middle"
   - Include dimensions if helpful: "Panel_600x400x18"
   - Avoid special characters that might cause export issues

### 1.3 Example: Kitchen Cabinet Door

Let's create a simple raised panel door:

1. **Create the Main Panel**
   - Create new Body
   - Sketch a rectangle: 600mm × 400mm
   - Pad to 18mm thickness
   - Label: "Door_Main_Panel"

2. **Add Raised Center**
   - Create new sketch on the front face
   - Draw rectangle 500mm × 300mm (centered)
   - Pad 3mm for raised effect
   - Label: "Door_Raised_Center"

3. **Create Handle Cutout** (Optional)
   - Sketch circle or rectangle for handle
   - Use Pocket to cut through
   - Label: "Door_Handle_Cutout"

**Result:** You now have a cabinet door that SquatchCut can extract as a complex shape, accounting for the raised panel and any cutouts.

---

## Part 2: Using SquatchCut's Shape Selection

### 2.1 Opening the Shape Selection Interface

1. **Launch SquatchCut**
   - Click the SquatchCut button in the toolbar
   - The main TaskPanel opens on the left side

2. **Access Shape Selection**
   - In the "Input" section, you'll see two options:
     - **Load CSV** (traditional rectangular parts)
     - **Select Shapes** (new shape-based workflow)
   - Click **Select Shapes**

### 2.2 Shape Detection and Selection

When you click "Select Shapes", SquatchCut will:

1. **Scan Your Document**
   - Automatically detect all objects with valid Shape properties
   - Analyze geometry complexity for each part
   - Extract dimensional and geometric data

2. **Display the Selection Dialog**
   - Shows a list of all detected shapes
   - Displays preview information for each part:
     - Part name and dimensions
     - Geometry type (Rectangular/Complex)
     - Complexity level (Low/Medium/High)
     - Estimated processing time

3. **Selection Controls**
   - **Checkboxes**: Select which parts to include in nesting
   - **Select All/None**: Quick selection controls
   - **Preview**: Shows shape thumbnails or descriptions
   - **Dimensions**: Displays bounding box dimensions

### 2.3 Understanding Shape Classifications

SquatchCut classifies your parts into categories:

**Rectangular Parts:**
- Simple boxes or panels
- Fast processing
- Uses traditional nesting algorithms
- Example: Basic cabinet shelves

**Complex Geometry:**
- Non-rectangular shapes
- Curved edges, cutouts, or raised features
- Uses advanced geometric nesting
- Example: Raised panel doors, curved aprons

**Complexity Levels:**
- **Low**: Simple shapes, fast processing
- **Medium**: Moderate complexity, good balance
- **High**: Complex shapes, longer processing time
- **Extreme**: Very complex, may trigger automatic simplification

### 2.4 Making Your Selection

**Selection Strategy:**
1. **Start Small**: For your first attempt, select 3-5 similar parts
2. **Group by Type**: Select parts of similar complexity together
3. **Consider Material**: Group parts that will use the same sheet material
4. **Check Dimensions**: Ensure selected parts will fit on your sheet size

**Selection Tips:**
- Parts with similar thickness nest better together
- Consider appearance and orientation requirements
- Account for your cutting tool capabilities
- Leave complex parts for separate nesting runs if needed

---

## Part 3: Nesting Configuration and Execution

### 3.1 Sheet Configuration

After selecting your shapes:

1. **Set Sheet Dimensions**
   - Width and Height in your document's units
   - Common sizes:
     - **Metric**: 1220×2440mm, 1525×3050mm
     - **Imperial**: 48"×96", 60"×120"

2. **Configure Cutting Parameters**
   - **Kerf Width**: Your saw blade thickness
     - Circular saw: ~3mm (1/8")
     - Table saw: ~2.5mm (3/32")
     - CNC router: 1-6mm depending on bit
   - **Margin**: Minimum spacing between parts
     - Hand cutting: 5-10mm (1/4"-3/8")
     - CNC cutting: 2-5mm (1/16"-3/16")

### 3.2 Nesting Mode Selection

SquatchCut automatically chooses the best nesting mode:

**Rectangular Mode:**
- Used when all selected parts are simple rectangles
- Fastest processing
- Traditional bin-packing algorithms

**Geometric Mode:**
- Used when complex shapes are detected
- Considers actual part geometry
- Prevents overlaps between true shape contours
- Longer processing time but better material utilization

**Hybrid Mode:**
- Mixes rectangular and geometric approaches
- Optimizes based on part complexity
- Balances speed and accuracy

### 3.3 Running the Nesting

1. **Click "Run Nesting"**
   - SquatchCut processes your selected shapes
   - Progress feedback shows current operation
   - Processing time varies with complexity

2. **Monitor Progress**
   - Shape extraction and validation
   - Nesting algorithm execution
   - Layout optimization
   - Result generation

3. **Review Results**
   - New "Nested Parts" group appears in model tree
   - 3D view shows optimized layout
   - Utilization statistics displayed

---

## Part 4: Understanding Nesting Results

### 4.1 Interpreting the Layout

**Visual Elements:**
- **Sheet Outline**: Shows your material boundaries
- **Nested Parts**: Parts positioned for cutting
- **Spacing**: Visible gaps for kerf and margins
- **Rotation**: Parts may be rotated for better fit

**Quality Indicators:**
- **Utilization Percentage**: Material efficiency (aim for 70-85%)
- **Parts Placed**: How many parts fit on the sheet
- **Unplaced Parts**: Parts that didn't fit (if any)
- **Waste Areas**: Unused material regions

### 4.2 Layout Validation

**Check for Issues:**
1. **Overlaps**: Parts shouldn't intersect (red highlighting if detected)
2. **Boundaries**: All parts should be within sheet edges
3. **Spacing**: Adequate gaps for your cutting method
4. **Orientation**: Grain direction considerations
5. **Access**: Can you actually cut the layout with your tools?

**Common Problems and Solutions:**
- **Low Utilization**: Try different sheet sizes or add more parts
- **Parts Don't Fit**: Reduce margins, check part dimensions, or use larger sheet
- **Complex Layout**: Consider simplifying some parts or using multiple sheets

---

## Part 5: Exporting for Production

### 5.1 Export Options

SquatchCut provides multiple export formats for different workflows:

**SVG Export (Visual Cutting Guides):**
- Accurate shape outlines for manual cutting
- Includes part labels and dimensions
- Suitable for printing cutting templates
- Shows kerf-compensated geometry

**DXF Export (CAD/CNC Compatible):**
- Precise vector geometry for automated cutting
- Separate layers for original and kerf-compensated shapes
- Compatible with most CAM software
- Maintains dimensional accuracy

**Enhanced Cutlist (Production Planning):**
- Detailed part information with actual areas
- Geometry complexity indicators
- Material utilization statistics
- Cutting sequence recommendations

### 5.2 Export Workflow

1. **Choose Export Type**
   - Right-click on the nested layout
   - Select "Export Nesting" from context menu
   - Choose your desired format

2. **Configure Export Settings**
   - **SVG**: Choose label placement, line weights, colors
   - **DXF**: Select layers, precision, units
   - **Cutlist**: Pick format (simple/enhanced), include statistics

3. **Save and Use**
   - Save to appropriate location
   - Import into your CAM software or print for shop use
   - Verify dimensions match your expectations

### 5.3 Production Tips

**For Manual Cutting:**
- Print SVG exports at actual size
- Use spray adhesive to attach templates to material
- Cut slightly outside lines, then sand to final dimension
- Account for kerf by cutting on the waste side of lines

**For CNC/Automated Cutting:**
- Import DXF into your CAM software
- Use kerf-compensated layer for tool paths
- Verify tool diameter matches kerf settings
- Run simulation before cutting expensive material

---

## Part 6: Advanced Techniques

### 6.1 Optimizing Complex Shapes

**Simplification Strategies:**
- Use "Simplified Nesting" mode for very complex parts
- Consider breaking complex assemblies into simpler components
- Use bounding box nesting for extremely detailed parts

**Performance Tuning:**
- Group similar complexity parts together
- Process large jobs in smaller batches
- Use performance monitoring to identify bottlenecks

### 6.2 Multi-Sheet Projects

**Planning Large Projects:**
1. Group parts by material type and thickness
2. Prioritize critical parts for first sheets
3. Use remaining material efficiently for smaller parts
4. Plan cutting sequence across multiple sheets

**Workflow:**
- Create separate nesting runs for each sheet
- Export each layout with clear sheet numbering
- Maintain cutting sequence documentation

### 6.3 Quality Control

**Pre-Nesting Checklist:**
- [ ] All parts have appropriate thickness
- [ ] Part names are clear and descriptive
- [ ] Sheet size matches available material
- [ ] Kerf and margin settings match cutting tools
- [ ] Grain direction requirements considered

**Post-Nesting Validation:**
- [ ] No overlapping parts
- [ ] All parts within sheet boundaries
- [ ] Adequate spacing for cutting access
- [ ] Utilization meets efficiency targets
- [ ] Export files are dimensionally accurate

---

## Part 7: Troubleshooting

### 7.1 Common Shape Detection Issues

**Problem: Parts Not Detected**
- **Cause**: Objects lack valid Shape property
- **Solution**: Ensure parts are solid bodies, not sketches or assemblies

**Problem: Incorrect Dimensions**
- **Cause**: Measurement system mismatch
- **Solution**: Check FreeCAD document units match SquatchCut settings

**Problem: Complex Parts Cause Slow Processing**
- **Cause**: High geometry complexity
- **Solution**: Use simplified nesting mode or reduce part detail

### 7.2 Nesting Problems

**Problem: Poor Material Utilization**
- **Causes**:
  - Parts too large for sheet
  - Excessive margins or kerf settings
  - Incompatible part shapes
- **Solutions**:
  - Try different sheet sizes
  - Reduce margins if cutting method allows
  - Group similar parts together

**Problem: Parts Don't Fit**
- **Causes**:
  - Sheet too small
  - Parts larger than expected
  - Kerf compensation too aggressive
- **Solutions**:
  - Verify part dimensions
  - Check sheet size settings
  - Reduce kerf if appropriate

### 7.3 Export Issues

**Problem: SVG Labels Overlap or Missing**
- **Cause**: Label placement algorithm conflicts
- **Solution**: Adjust label settings or use DXF export instead

**Problem: DXF Dimensions Incorrect**
- **Cause**: Unit conversion errors
- **Solution**: Verify measurement system consistency throughout workflow

**Problem: Cutlist Information Incomplete**
- **Cause**: Shape analysis incomplete
- **Solution**: Ensure all parts are properly formed solid bodies

---

## Part 8: Best Practices Summary

### 8.1 Design Phase
- Create parts as solid bodies with consistent thickness
- Use descriptive naming conventions
- Consider nesting efficiency in your design
- Design with your cutting tools in mind

### 8.2 Selection Phase
- Start with simple parts to learn the workflow
- Group similar complexity parts together
- Consider material requirements and orientation
- Review shape classifications before proceeding

### 8.3 Nesting Phase
- Set accurate kerf and margin values
- Choose appropriate sheet sizes for your material
- Monitor processing time and complexity warnings
- Validate results before proceeding to export

### 8.4 Export Phase
- Choose the right export format for your workflow
- Verify dimensional accuracy in exported files
- Test with small projects before large production runs
- Maintain clear documentation for production

---

## Part 9: Example Project Walkthrough

### 9.1 Project: Kitchen Cabinet Face Frames

**Goal:** Create nesting layout for face frame components

**Parts List:**
- 4 Stiles: 800mm × 50mm × 18mm
- 6 Rails: 400mm × 50mm × 18mm
- 2 Center Stiles: 600mm × 50mm × 18mm

**Step-by-Step:**

1. **Design in FreeCAD**
   - Create each component as separate Body
   - Use consistent 18mm thickness
   - Label clearly: "Stile_Left_Upper", "Rail_Top_Door1", etc.

2. **Shape Selection**
   - Open SquatchCut and click "Select Shapes"
   - All parts detected as "Rectangular - Low Complexity"
   - Select all 12 parts for nesting

3. **Configure Nesting**
   - Sheet: 1220mm × 2440mm (standard plywood)
   - Kerf: 3mm (circular saw blade)
   - Margin: 5mm (hand cutting tolerance)

4. **Run Nesting**
   - SquatchCut uses rectangular mode (all parts are simple)
   - Processing completes in seconds
   - Result: 85% utilization, all parts fit

5. **Export for Production**
   - Export SVG for cutting templates
   - Export enhanced cutlist for material planning
   - Print SVG at actual size for shop use

**Result:** Efficient layout ready for production with minimal waste.

### 9.2 Project: Curved Cabinet Doors

**Goal:** Nest raised panel doors with curved tops

**Parts List:**
- 2 Curved doors: 600mm × 800mm with arch top
- 4 Straight doors: 400mm × 600mm rectangular

**Step-by-Step:**

1. **Design Curved Doors**
   - Create base rectangle 600mm × 800mm
   - Add curved top using arc and trim operations
   - Pad to 18mm thickness
   - Add raised panel detail

2. **Shape Selection**
   - Curved doors: "Complex Geometry - Medium Complexity"
   - Straight doors: "Rectangular - Low Complexity"
   - Select all 6 doors

3. **Configure for Complex Shapes**
   - Sheet: 1525mm × 3050mm (larger sheet for complex shapes)
   - Kerf: 2mm (router bit for curves)
   - Margin: 8mm (extra clearance for complex cutting)

4. **Run Geometric Nesting**
   - SquatchCut automatically uses geometric mode
   - Processing takes 30-45 seconds
   - Result: 78% utilization, optimal arrangement

5. **Export DXF for CNC**
   - Export DXF with kerf compensation
   - Import into CAM software
   - Generate tool paths for router cutting

**Result:** Complex shapes nested efficiently with accurate cutting geometry.

---

## Conclusion

Shape-based nesting in SquatchCut represents a significant advancement for cabinet makers working with FreeCAD. By considering actual part geometry rather than simple rectangles, you can achieve better material utilization, more accurate cutting layouts, and ultimately more efficient production.

**Key Benefits:**
- **Higher Material Utilization**: True shape nesting reduces waste
- **Accurate Cutting Guides**: Export files match actual part geometry
- **Flexible Workflows**: Handles both simple and complex parts
- **Professional Results**: Production-ready layouts with proper kerf compensation

**Next Steps:**
- Practice with simple projects first
- Experiment with different sheet sizes and configurations
- Develop your own design standards for optimal nesting
- Integrate shape-based nesting into your regular production workflow

For additional help, see:
- [Technical Reference Guide](shape-based-nesting-reference.md)
- [Troubleshooting Guide](troubleshooting-shape-nesting.md)
- [Sample Projects](../examples/cabinet-projects/face-frame-example.md)

---

*This guide covers SquatchCut v3.4+ shape-based nesting features. For traditional CSV workflows, see the [Standard User Guide](../user_guide.md).*
