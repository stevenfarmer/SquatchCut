# SquatchCut Project Guide (v3.2 – Codex-Fortified Edition)

## 0. Meta Goals of v3.2

This updated guide focuses specifically on:

### **A. Eliminating ambiguity in Codex instructions**
- Codex blocks now have strict, enforceable structure  
- No markdown, no commentary inside blocks  
- Reasoning level declarations mandatory  
- File paths and expected patterns must be explicit  
- UI behavior described unambiguously  
- Persistent behavior safeguarded from accidental overwrites  

### **B. Making YOU faster and making ME (GPT) more consistent**
- You describe requirements  
- I translate them into clear directives  
- Codex executes  

### **C. Forcing Codex to conform to SquatchCut’s architecture**
Codex should never reinvent the repo or introduce new patterns.

---

# 1. Project Purpose

SquatchCut is a FreeCAD add-on that takes CSV part lists and generates optimized sheet nests for woodworking, cabinetry, and general sheet-material workflows.

### Core Objectives
- Fast, predictable, simple  
- Minimal UI friction  
- Always mm internally, fractions if imperial  
- Stable hydration/initialization  
- Simple CSV → sheet → nest → export workflow  

---

# 2. Roles

## **You (Steven)**
- Product Owner  
- Scrum-ish Master  
- UAT wrangler  
- Requirements authority  

## **ChatGPT (Architect / PM / Spec Writer)**
- Writes requirements  
- Produces Codex instruction blocks  
- Ensures patterns and rules never drift  
- Maintains documentation  

## **Codex (Engineering Automaton)**
- Writes code  
- Must obey patterns  
- Must obey reasoning levels  
- Must never “guess”  
- Must build tests with every core change  

---

# 3. Core Principles

1. **Internal units = millimeters**  
2. **Imperial = fractional inches only**  
3. **Defaults never change unless Settings says so**  
4. **Presets never override defaults**  
5. **TaskPanel never auto-selects presets**  
6. **hydrate_from_params() ALWAYS runs before UI widgets**  
7. **Codex must use reasoning level declarations**  
8. **Every logic change must include tests**  
9. **UI must not overflow or fail to load**  
10. **Settings panel must always open**  
11. **No relative imports**  
12. **No pattern drift**  
13. **No silent behavior changes**  

---

# 4. Codex Communication Rules (Updated + Hardened)

## 4.1 Codex Block Format

Every Codex block MUST begin with:

```
Recommended Codex reasoning level: <LEVEL>
```

Followed by:

```
Codex, this task requires <LEVEL> reasoning.

<instructions>
```

- No markdown  
- No language tag  
- No commentary  
- Only instructions  
- Must be safe to paste directly into Codex  

## 4.2 Required Elements Inside Each Block
- Full file paths  
- Explicit operation lists  
- Expected behavior  
- Acceptance criteria  
- Guardrails  

## 4.3 When to Use Levels
- LOW: trivial  
- MEDIUM: single-file  
- HIGH: multi-file + UI or settings  
- EXTRA-HIGH: architecture or algorithm refactor  

---

# 5. Hydration Rules (Hard Requirements)

Hydration has caused repeated issues. These rules are absolute:

### **5.1 hydrate_from_params() must:**
- Load all persistent values  
- Guarantee type consistency  
- Normalize internal units  
- Never access GUI  
- Never import GUI modules  
- Never modify defaults except on Settings save  

### **5.2 TaskPanel Initialization Order**
This order is non-negotiable:

1. Load session_state  
2. Call hydrate_from_params()  
3. Create all UI widgets  
4. Populate UI values from hydrated state  
5. Apply measurement formatting  
6. Connect signals  
7. Render panel  

No exceptions.

---

# 6. Measurement System Architecture

### 6.1 Internal Storage
Always millimeters.

### 6.2 Display Modes
- metric → mm  
- imperial → fractional inches  

### 6.3 UI Reformatting Rules
Switching measurement system requires full reformatting of all numeric UI fields.

### 6.4 Fraction Logic
Must support:
- whole  
- fraction  
- mixed  
- hyphenated  
Must round-trip without drift.

---

# 7. Preset & Default Logic (Fortified)

### **Defaults**
- Set only via Settings panel  
- Never altered by TaskPanel  
- Hydrate_from_params loads them  

### **Presets**
- Always start blank  
- Only modify sheet width/height  
- Never modify defaults  
- Never auto-selected  

### **Imperial Default Sheet**
Exactly **48 × 96 inches**.

---

# 8. UI Behavior Rules

### 8.1 Settings Panel
- Must always open  
- Must use TaskPanel_Settings  
- Must call hydrate_from_params() before building widgets  

### 8.2 Main TaskPanel
- Must reflect hydrated defaults  
- Must not override defaults  
- Must not infer presets  
- Must not open multiple instances  

### 8.3 Sheet/Source/Nesting View Rules
- Clear groups before redraw  
- Never leave orphans  
- Auto-zoom after draw  
- Maintain consistent naming:
  - SquatchCut_Sheet  
  - SquatchCut_SourceParts  
  - SquatchCut_NestedParts  

---

# 9. Tests

### 9.1 Must Test
- Fraction parsing  
- Fraction formatting  
- CSV parsing  
- Default initialization  
- Hydration logic  
- Preset behavior  
- TaskPanel load behavior  
- Measurement-system conversions  

### 9.2 Should Test
- Sheet object creation  
- Group clearing  
- UI stability (when possible)  

---

# 10. Add-On Manager Rules

Codex must ensure:

- Correct zip structure  
- Correct metadata  
- No relative imports  
- All icons exist  
- Version increments  

---

# 11. Backlog (v3.2)

### Critical
- Settings panel stability  
- Hydration order correctness  
- TaskPanel initialization ordering  
- UI width/overflow fixes  

### Medium
- Multi-sheet nesting  
- Layout exports  
- More robust heuristics  

### Future
- Grain direction support  
- Bookmatching  
- Kerf simulation  

---

# 12. Development Rules Summary

1. Internal unit = mm  
2. Imperial UI = fractions only  
3. Defaults remain unchanged except in Settings  
4. Presets never overwrite defaults  
5. TaskPanel never auto-selects presets  
6. Hydration before UI  
7. Codex must use reasoning levels  
8. Tests accompany logic changes  
9. UI must never overflow  
10. Settings panel must open  
11. No relative imports  
12. No silent assumptions  
13. No redesigns without explicit instructions  

---

# 13. Changelog Strategy for v3.2

- Add v3.2 section  
- Note settings fixes, hydration rules, UI rules, Codex reinforcement  
- Bump version to 0.3.2  
- Include explicit references to v3.2 documentation  

---

# END OF SquatchCut Project Guide v3.2
