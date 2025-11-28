# SquatchCut Roadmap

## Icebox / Long-Term Ideas

- **Polygon Nesting / Full 2D Bin Packing Support (Icebox)**  
  Consider adding support for arbitrary polygon nesting (L-shapes, concave pieces, curves, CNC contours, etc.).  
  This would involve:  
  - Extracting polygon outlines from FreeCAD shapes  
  - Computing no-fit polygons  
  - Rotation sweep tests  
  - Collision detection using SAT/Minkowski sums  
  - Optional heuristic or genetic optimization  
  This feature is extremely complex and computationally heavy and should **not** be implemented until there is a strong, real user need.  
  For now, rectangle-only nesting is sufficient for woodshop workflows, and polygon nesting is deferred indefinitely unless justified.
