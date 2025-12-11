# AI Worker Workflows

**Note:** AI Workers operate as implementation agents under the direction of the Lead Developer (e.g., Jules) and Architect (Spec Owner). See `AGENTS.md` for the full protocol.

## Overview
- This repository uses `@worker` headers in each module to guide incremental development.
- Each module documents its own responsibility, boundaries, and expectations to keep changes targeted.

## Global Worker Commands

1. `@worker implement next core logic`
   - Worker should examine method stubs in core modules and fill in the next unimplemented piece.

2. `@worker update feature <X>`
   - Worker should locate the correct module(s), update logic, and avoid touching unrelated modules.

3. `@worker refactor safely`
   - Worker should refactor only the module containing the comment without changing structure or deleting headers.

4. `@worker sync architecture`
   - Worker should compare code with `docs/architecture.md` and fix inconsistencies.

5. `@worker integrate GUI`
   - Worker should update dialogs and commands to work with the current state of the core logic.

6. `@worker implementation status`
   - Worker should scan headers and list which modules have remaining TODO implementations.

## Rules for Workers
- Do not overwrite files unless instructed.
- Only modify sections relevant to the active module.
- Follow `@worker` block expectations.
- Preserve docstrings and method signatures.
- Never introduce cross-module logic unless specified.
