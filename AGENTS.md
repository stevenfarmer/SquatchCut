# AI Worker Protocol

**Scope:** This protocol applies to all AI workers (e.g., Codex, Jules, or other agents) contributing to the SquatchCut repository.

## 1. Roles & Responsibilities

### **Architect (The Planner)**
- **Who:** Human (Steven) + Upstream Planner (e.g., ChatGPT).
- **Duties:**
  - Writes high-level requirements.
  - Generates "Task Specs" (Job Cards).
  - Owns the documentation and architectural vision.

### **AI Workers (The Builders)**
- **Who:** Any code-generation agent (e.g., Codex in VS Code, Jules, GitHub Copilot agents).
- **Duties:**
  - Reads Task Specs.
  - Implements code changes.
  - Updates tests.
  - Verifies work locally.
- **Constraints:**
  - Must NOT invent new architecture without permission.
  - Must NOT modify files outside the scope of the Task Spec.

---

## 2. Task Spec Format (Job Cards)

All work assigned to an AI worker must come in a structured block format.

**Example:**
```
@worker
Title: Update Hydration Logic
File: freecad/SquatchCut/gui/taskpanel_main.py
Action: Refactor
Context: The hydration logic is skipping the sheet widget defaults.
Rules:
- Ensure hydrate_from_params() is called before widget creation.
- Do not change the function signature.
```

Workers must look for these blocks (or similar structured instructions) to know what to do.

---

## 3. Worker Rules

1.  **Reasoning Level:** Always state your reasoning level (LOW/MEDIUM/HIGH) before starting.
2.  **Test First:** If possible, create or identify a test case that reproduces the issue or verifies the feature.
3.  **Scope Containment:** Do not touch files not listed in the Spec unless absolutely necessary for imports/dependencies.
4.  **No Hallucinations:** Do not import libraries that are not in `requirements.txt` or standard FreeCAD modules.
5.  **Verify:** Run `pytest` or relevant checks before finishing.

## 4. Workflow

1.  **Receive Spec:** Architect provides a Task Spec.
2.  **Plan:** Worker analyzes the request and checks files.
3.  **Implement:** Worker edits code.
4.  **Test:** Worker runs tests.
5.  **Submit:** Worker commits changes with a semantic message (e.g., `feat: ...`, `fix: ...`).

---

## 5. Specific Tool Examples

- **Codex:** A VS Code-based agent used for implementation.
- **Jules:** A lead developer agent used for planning and complex refactors.
- **GitHub Agents:** Future agents running in CI/CD or PR workflows.

*All tools must follow this same protocol.*
