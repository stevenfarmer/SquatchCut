# Development Environment

This document defines the canonical SquatchCut development workflow so that local AI tooling (ChatGPT Mac app “Work With Code”, VS Code agents, etc.) can discover and operate on the same workspace as the developer.

## AI-Forward Development Environment

### A. Local Workspace Requirement
- Clone the SquatchCut repository onto the host filesystem (for example: `~/dev/SquatchCut` on macOS).
- Always open the project via `squatchcut.code-workspace` from the host. This ensures the ChatGPT Mac app and other local tools see the same workspace that VS Code uses.
- Do **not** rely on container-only or remote-only copies of the code; the host-cloned repo is the single source of truth.

### B. Dev Container Behavior
- When opening the repo in VS Code, use **File → Open Workspace… → squatchcut.code-workspace**, then choose “Reopen in Container” if you need the dev container.
- The dev container bind-mounts the host workspace at `/workspaces/SquatchCut`. Editing inside the container still operates on the host files.
- The container provides tooling and dependencies only; it is **not** the canonical storage location for the code.

### C. AI Toolchain Compatibility
- ChatGPT Mac app “Work With Code” lists the project automatically when the host workspace (squatchcut.code-workspace) is open.
- VS Code extensions (AI Assistants, Copilot, etc.) running either locally or inside the container see the same files because the container bind-mounts the host repo.
- Avoid workflows where the “real” code exists only inside opaque Docker volumes or remote filesystems that macOS cannot access.

Following this process guarantees that human developers and AI assistants operate on the same SquatchCut workspace, keeping the experience predictable and productive.
