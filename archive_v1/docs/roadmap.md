# SquatchCut Roadmap

## Current Development (v3.4)

### Shape-Based Nesting - **IN ACTIVE DEVELOPMENT**
**Status:** Specification Complete, Implementation Starting

Enhanced FreeCAD integration with support for non-rectangular nesting:
- **Enhanced Shape Detection**: Improved FreeCAD object scanning and extraction
- **Selection Workflow**: Intuitive UI for choosing which parts to nest
- **Non-Rectangular Nesting**: True geometric nesting beyond bounding boxes
- **Cabinet Maker Workflow**: Complete FreeCAD design → cutting layout pipeline
- **Comprehensive Testing**: Property-based testing with Hypothesis framework
- **Performance Optimization**: Automatic fallback and simplification modes

**Implementation Plan:** 44 tasks across 10 major phases
**Specification Location:** `.kiro/specs/shape-based-nesting/`

This addresses the long-standing polygon nesting request with a practical, performance-conscious approach that provides real value for cabinet makers and woodworkers.

---

## Future Considerations

### Advanced Polygon Nesting (Post v3.4)
After shape-based nesting is complete and proven, consider expanding to full arbitrary polygon support:
- No-fit polygon computation
- Advanced collision detection (SAT/Minkowski sums)
- Genetic/heuristic optimization algorithms

**Note:** This remains computationally intensive and should only be pursued if there's demonstrated user need beyond the cabinet maker workflow.
