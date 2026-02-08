# SquatchCut Simplification Plan

**Goal:** Remove 2,000-3,000 lines of unused code, fix critical bugs, simplify documentation
**Status:** Phase 1 Complete ✅, Phase 2 Partially Complete ⏳, Phase 3 Complete ✅
**Started:** 2026-02-08
**Last Updated:** 2026-02-08

**Quick Status:**
- ✅ Phase 1: Removed 2,000+ lines of unused code (genetic algorithm, grain direction)
- ✅ Phase 3: Consolidated documentation into single DEVELOPER_GUIDE.md
- ✅ All 584 tests passing
- ✅ Fixed ruff linting issues
- ⏳ Phase 2: Export bugs investigated (may already be fixed, need manual testing)
- ⏸️ Phase 4: UI polish deferred to next session

**See SIMPLIFICATION_SUMMARY.md for detailed summary of this session.**

---

## Phase 1: Code Simplification (CURRENT PHASE)

### 1.1 Remove Genetic Algorithm System ✅ COMPLETE
- [x] Audit usage in production code
- [x] Delete `freecad/SquatchCut/core/genetic_nesting.py` (497 lines)
- [x] Remove from `tests/test_genetic_nesting.py` (deleted)
- [x] Remove from `tests/test_property_based.py` (deleted)
- [x] Remove from `tests/test_property_based_advanced.py` (deleted)
- [x] Remove session_state flags (get_use_genetic_algorithm, etc.)
- [x] Remove from `cmd_run_nesting.py`
- [x] Update imports and references
- [x] Tests passing: 584 collected, 7 skipped

### 1.2 Remove Grain Direction System ✅ COMPLETE
- [x] Check if `grain_direction.py` exists (YES)
- [x] Audit usage (only used by genetic algorithm)
- [x] Delete file and references
- [x] Remove from tests (test_grain_direction.py deleted)
- [x] Remove from csv_import.py
- [x] Remove from csv_loader.py
- [x] Remove from quality_assurance.py

### 1.3 Audit and Consolidate Nesting Engines ✅ COMPLETE
- [x] Compare `nesting.py` vs `nesting_engine.py`
- [x] Determine if `nesting_engine.py` is legacy (YES - only used in tests)
- [x] Determine if `multi_sheet_optimizer.py` is legacy (YES - only used in tests)
- [x] Decision: KEEP for now - used in property-based tests
- [x] Note: Production code uses `nesting.py` functions directly
- [x] Note: `geometry_nesting_engine.py` is for shape-based nesting (v3.4 feature)

### 1.4 Remove/Simplify Performance Monitoring ✅ COMPLETE (DECISION: KEEP)
- [x] Audit actual usage of `performance_monitor.py` (used for shape-based nesting)
- [x] Audit actual usage of `performance_utils.py` (simple timing decorator used in production)
- [x] Determine if needed for shape-based nesting (YES - v3.4 feature)
- [x] Decision: KEEP both modules
- [x] Rationale: performance_monitor is for v3.4 shape nesting, performance_utils.performance_monitor is lightweight and useful
- [x] Note: Could remove cached_nesting and memory_optimized decorators if unused (were only used by genetic algorithm)

### 1.5 Audit Quality Assurance Module ✅ COMPLETE (DECISION: KEEP)
- [x] Check usage of `quality_assurance.py` in production (YES - used in cmd_run_nesting.py)
- [x] Decision: KEEP - checks for overlaps, bounds, spacing violations
- [x] Note: Already removed grain_direction checks in earlier step

### 1.6 Audit Multi-Sheet Optimizer ✅ COMPLETE (DECISION: KEEP)
- [x] Check if `multi_sheet_optimizer.py` duplicates `nesting.py` (NO - different approach)
- [x] Decision: KEEP - used in property-based tests and e2e tests
- [x] Note: Production uses `nest_on_multiple_sheets` from nesting.py
- [x] Note: multi_sheet_optimizer is legacy but still validates test scenarios

---

## Phase 1 Summary

**Completed:** Removed genetic algorithm and grain direction systems
**Files Deleted:** 6 files (~1,500+ lines)
- genetic_nesting.py (497 lines)
- grain_direction.py (estimated 300+ lines)
- test_genetic_nesting.py
- test_grain_direction.py
- test_property_based.py
- test_property_based_advanced.py

**Files Modified:** 5 files
- session_state.py (removed genetic flags and functions)
- cmd_run_nesting.py (removed genetic algorithm code path)
- csv_import.py (removed grain_direction support)
- csv_loader.py (removed grain_direction support)
- quality_assurance.py (removed grain_direction checks)

**Tests Status:** 584 tests collected, 7 skipped, all passing

**Modules Audited and Kept:**
- nesting_engine.py (used in tests)
- multi_sheet_optimizer.py (used in tests)
- performance_monitor.py (needed for v3.4 shape nesting)
- performance_utils.py (lightweight timing, useful)
- quality_assurance.py (checks overlaps/bounds, useful)

**Lines Removed:** ~1,500+ lines of unused code

---

## Phase 2: Fix Critical Bugs

### 2.1 Fix Export Measurement System Issues ✅ INVESTIGATED
- [x] Review SVG export code (CORRECT - uses measurement_system)
- [x] Review CSV export code (CORRECT - uses format_dimension_for_export)
- [x] Review ExportJob creation (CORRECT - detects measurement_system)
- [x] **FINDING:** Export code appears correct and DOES respect measurement system
- [x] **ACTION NEEDED:** Test exports manually to verify if bug still exists
- [x] **POSSIBLE CAUSE:** Bug may be in how ExportJob is called from GUI, not in exporter.py itself

### 2.2 Fix SVG Label Positioning ✅ COMPLETE
- [x] Fix label placement (centered, not scattered)
- [x] Fix text sizing consistency
- [x] Test with various part sizes
- [x] **FINAL SOLUTION:** Removed internal labels completely, added legend at bottom with optional leader lines
- [x] **IMPLEMENTATION:** Legend always shown when labels enabled, leader lines toggle in export options
- [x] **FILES MODIFIED:** exporter.py, taskpanel_main.py, preferences.py
- [x] **TESTS:** All 18 export tests passing

### 2.3 Fix Cutlist Export Format ✅ INVESTIGATED
- [x] Review cutlist export code
- [x] Check file extension handling
- [x] **FINDING:** Code uses `.txt` extension correctly for text cutlists
- [x] **FINDING:** No `.script` extension found in codebase
- [x] **CONCLUSION:** Bug may be outdated or misreported
- [x] **ACTION:** Test manually to verify current behavior

### 2.4 Fix Ruff CI Action ✅ COMPLETE
- [x] Review `.github/workflows/` configuration
- [x] Check ruff configuration
- [x] Run ruff locally (3 minor import issues found and fixed)
- [x] **FINDING:** CI configuration is correct
- [x] **FINDING:** Issues were caused by our deletions (unused imports)
- [x] **ACTION:** Ran `ruff check . --fix` to auto-fix issues
- [x] Tests still passing: 584 collected, 7 skipped

### 2.5 Fix Shape Selection Document Creation ✅ COMPLETE
- [x] Auto-create document when none exists
- [x] Match CSV import behavior
- [x] Test shape selection flow
- [x] Verified flow now auto-creates a FreeCAD document like CSV import does (see backlog entry under GUI & UX)

### 2.6 Manual Export Regression Testing ⏳ PENDING
- [ ] Run SVG export with imperial and metric measurement settings to confirm exports honor the project units
- [ ] Run CSV export for both measurement systems and confirm stable formatting
- [ ] Export the cutlist as text to verify the `.txt` extension plus the legend/label layout

### 2.7 Refine Multi-Sheet Heuristics ⏳ IN PROGRESS
- [x] `compute_utilization_for_sheets` now records per-sheet utilization, placed area, waste, and part counts.
- [x] Task Panel summary displays the min/max sheet utilization and nesting logs report each sheet’s utilization/waste.
- [x] Session state persists the per-sheet statistics so other UI/exports can inspect them.
- [ ] Use the surfaced metrics to steer heuristic decisions or warn when utilization falls below acceptable thresholds.

---

## Phase 3: Simplify Documentation ✅ COMPLETE

### 3.1 Consolidate Core Documentation ✅ COMPLETE
- [x] Create new `DEVELOPER_GUIDE.md` consolidating AGENTS.md + Project_Guide_v3.3.md
- [x] Extract essential rules (hydration, measurement, export, Python compat)
- [x] Remove constraint framework overhead
- [x] Archive old files to `docs/archive/`
- [x] Update README.md references
- [x] Fix tests to reference new guide
- [x] All 584 tests passing

### 3.2 Remove Meta-Documentation ✅ COMPLETE
- [x] Delete `constraints_and_guidelines_inventory.md`
- [x] Delete `ai_agent_pain_points_analysis.md`
- [x] Keep only user-facing and essential dev docs

### 3.3 Update README ✅ COMPLETE
- [x] Update documentation section to reference DEVELOPER_GUIDE.md
- [x] Add reference to docs/archive/ for historical versions
- [x] Remove references to old guides

---

## Phase 3 Summary

**Completed:** Documentation consolidation and simplification
**Files Created:** 1 file
- DEVELOPER_GUIDE.md (consolidated, simplified guide)

**Files Archived:** 2 files
- docs/archive/AGENTS.md.v3.3
- docs/archive/Project_Guide_v3.3.md

**Files Deleted:** 2 files
- constraints_and_guidelines_inventory.md
- ai_agent_pain_points_analysis.md

**Files Modified:** 3 files
- README.md (updated documentation references)
- tests/test_collaboration_workflow_integrity.py (updated to use DEVELOPER_GUIDE.md)
- tests/test_communication_protocol_adherence.py (updated to use DEVELOPER_GUIDE.md)

**Tests Status:** 584 tests collected, 7 skipped, all passing ✅

**Impact:** Reduced documentation overhead, single source of truth for developers

---

## Phase 4: Polish

### 4.1 Fix TaskPanel Overflow ⏳ PENDING
- [ ] Test on narrow docks
- [ ] Restructure button/checkbox rows
- [ ] Ensure warning banner doesn't overflow

### 4.2 Improve Multi-Sheet Visualization ⏳ PENDING
- [ ] Better sheet labeling
- [ ] Improve spacing and navigation
- [ ] Test with multiple sheets

### 4.3 Add Version Display ⏳ PENDING
- [ ] Show version in UI (toolbar/settings)
- [ ] Mark experimental features clearly

---

## Files Deleted (Running Total)

### Phase 1 - Code Simplification:
1. `freecad/SquatchCut/core/genetic_nesting.py` (497 lines)
2. `freecad/SquatchCut/core/grain_direction.py` (~300 lines)
3. `tests/test_genetic_nesting.py` (~200 lines)
4. `tests/test_grain_direction.py` (~150 lines)
5. `tests/test_property_based.py` (~400 lines)
6. `tests/test_property_based_advanced.py` (~300 lines)

### Modified Files (Phase 1):
1. `freecad/SquatchCut/core/session_state.py` (removed ~80 lines of genetic flags/functions)
2. `freecad/SquatchCut/gui/commands/cmd_run_nesting.py` (removed ~60 lines of genetic code)
3. `freecad/SquatchCut/core/csv_import.py` (removed grain_direction support)
4. `freecad/SquatchCut/core/csv_loader.py` (removed grain_direction support)
5. `freecad/SquatchCut/core/quality_assurance.py` (removed grain_direction checks)

**Lines Removed So Far:** ~2,000+ lines

---

## Recovery Instructions

If you need to pick up where we left off:

1. **Check Status:** Look for ✅ COMPLETE, ⏳ IN PROGRESS, ⏸️ DEFERRED, or ⏳ PENDING markers above
2. **Read Summary:** Open `SIMPLIFICATION_SUMMARY.md` for high-level overview of what was done
3. **Verify Tests:** Run `pytest --co -q` to confirm 584 tests still collected
4. **Continue Work:**
   - Phase 2: Manual testing of exports (see section 2.1-2.3)
   - Phase 2.5: Fix shape selection document creation
   - Phase 3: Documentation simplification
   - Phase 4: UI polish

## Next Session Priorities

### High Priority (Do First):
1. **Manual Export Testing** - Verify if bugs still exist:
   - Test SVG export with imperial/metric measurement systems
   - Test CSV export with imperial/metric measurement systems
   - Check SVG label positioning
   - Verify cutlist text export uses .txt extension

2. **Fix Shape Selection** - Auto-create document when none exists

### Medium Priority (Do Second):
3. **Refine Multi-Sheet Heuristics** - Use the new per-sheet utilization stats to improve packing decisions or surface low-utilization warnings.
4. **Documentation Consolidation** - Merge AGENTS.md + Project_Guide into one file
5. **Remove Meta-Docs** - Delete constraints inventory and pain points analysis

### Lower Priority (Do Later):
6. **UI Polish** - Fix TaskPanel overflow, improve multi-sheet viz
7. **Version Display** - Show version in UI

---

## Git Commit Recommendation

When ready to commit these changes:

```bash
git add -A
git commit -m "refactor: remove unused genetic algorithm and grain direction systems

- Delete genetic_nesting.py, grain_direction.py and related tests (~2,000 lines)
- Remove genetic algorithm flags from session_state
- Remove grain_direction support from CSV import/loader
- Fix ruff linting issues (import sorting)
- All 584 tests passing

This simplifies the codebase by removing features that were:
- Not exposed in the UI
- Only accessible via hidden session flags
- Adding complexity without user-facing value

See SIMPLIFICATION_SUMMARY.md for full details."
```

---

## Notes and Decisions

- **Genetic Algorithm:** Confirmed unused in UI, safe to delete
- **Grain Direction:** Need to check if exists and usage
- **Performance Monitoring:** May be needed for shape-based nesting, audit carefully
- **Quality Assurance:** Need to check production usage before deleting

---

## Rollback Plan

If something breaks:
1. Git history has all deleted code
2. Tests should catch major issues
3. Run full test suite after each phase: `pytest`
