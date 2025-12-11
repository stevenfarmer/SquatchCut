# Contributing to SquatchCut

Thank you for your interest in contributing to SquatchCut!

## Workflow

We use a structured workflow involving an **Architect** (who plans the work) and **AI Workers** (who implement the work).

### For Human Contributors
1.  **Open an Issue:** Describe the bug or feature.
2.  **Wait for Architecture:** If the change is significant, we will generate a "Task Spec" (Job Card).
3.  **Implement:** You (or an AI agent) can pick up the task.
4.  **Submit PR:** Follow the PR template.

### For AI Workers
If you are an AI agent (Codex, Jules, etc.):
1.  Read `AGENTS.md` in the root.
2.  Follow the **AI Worker Protocol**.
3.  Look for `@worker` blocks in issues or task files.

## Guidelines
- **Tests:** All logic changes must have tests.
- **Style:** We use `ruff` for linting.
- **Architecture:** Do not break the Core vs. GUI separation. See `docs/Project_Guide_v3.3.md`.
