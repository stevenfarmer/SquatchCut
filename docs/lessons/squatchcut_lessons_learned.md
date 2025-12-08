---
title: "SquatchCut Lessons Learned"
summary: "Key patterns, practices, and safeguards discovered while building SquatchCut with LLM-assisted development."
---

![SquatchCut Lessons](../assets/images/lessons/squatchcut-lessons-learned-hero.svg)

# SquatchCut Lessons Learned

This document summarizes the key technical and process insights gained while building and evolving the SquatchCut FreeCAD add-on using an agentic LLM coding model under structured architectural guidance.

SquatchCut serves as a practical case study in AI-assisted engineering, demonstrating repeatable patterns for FreeCAD plugin development, unit-handling design, and multi-agent collaboration between human roles and AI systems.

---

## 1. Use Explicit, Unambiguous Requirements

LLM coding agents rely on probabilistic inference. Any ambiguity in requirements increases the risk of architectural drift and unintended behavior.

### Key Practices

- Use strict, structured instruction blocks for the coding agent.  
- Always specify file paths and target modules explicitly.  
- Describe expected behavior, including edge cases, not just “what to change.”  
- Include acceptance criteria for success and failure.  
- Avoid implied behavior—if it matters, write it down.

---

## 2. Architect Before You Automate

AI models do not design architecture; they follow it.

### Best Practices

- Define a clear hydration lifecycle (load state, normalize, then render UI).  
- Choose a single internal unit system (millimeters in SquatchCut) and keep it consistent.  
- Separate persisted defaults, selectable presets, and active runtime values.  
- Define how UI components map to internal state before asking an AI to modify them.  
- Document invariants: behavior that must never change without explicit approval.

When architecture is explicit, AI becomes an accelerator instead of a source of silent redesigns.

---

## 3. Treat Unit Handling as a High-Risk Component

Mixed measurement systems (metric and imperial) introduce complexity across storage, computation, and display layers.

In SquatchCut, the following conventions proved effective:

### Effective Architecture

- Internal units are always millimeters.  
- Display units (metric vs imperial) are a formatting concern only.  
- Defaults are not auto-converted between systems behind the scenes.  
- Presets never overwrite defaults silently.  
- Switching measurement systems triggers full UI rehydration.  
- Fractional inches must round-trip without drift or loss of precision.

Unit logic should be treated as a first-class architectural concern, especially when AI is allowed to modify related code.

---

## 4. Use Tests to Constrain AI Behavior

Tests in this context do more than validate correctness—they constrain the possible behaviors of the coding agent.

### Required Test Areas

- Hydration lifecycle: order, idempotence, and determinism.  
- Measurement conversion: metric to imperial and back, including edge cases.  
- UI initialization: correct default and active values.  
- Default vs preset behavior: interactions and override boundaries.  
- FreeCAD object creation and grouping: stable naming and arrangement.

With sufficient test coverage, AI-generated changes are less likely to unintentionally alter established behavior.

---

## 5. Adopt a Three-Layer Collaboration Model

The SquatchCut workflow naturally evolved into a three-layer structure that scales well:

1. **Product Owner (Human)**  
   - Defines intent, priorities, and requirements.  
   - Provides domain and user-level context.  
   - Validates whether the resulting behavior matches real-world needs.

2. **Architect AI (GPT)**  
   - Converts intent into deterministic implementation directives.  
   - Enforces architectural patterns and invariants.  
   - Maintains consistency across modules and features.  
   - Specifies what the coding agent may and may not change.

3. **Coding Agent (Codex or similar)**  
   - Writes and edits the actual code.  
   - Implements the instructions verbatim.  
   - Does not redesign architecture or introduce new patterns on its own.

This separation of roles reduces confusion and supports scaled-agile practices where Product Owners, architects, and implementers remain clearly distinguished—even when some of those roles are AI.

---

## 6. Preserve Determinism in UI and Initialization

AI-generated modifications can introduce non-deterministic or order-dependent behavior unless initialization rules are clearly defined and enforced.

### Required Behaviors

- Hydration runs before UI elements are created.  
- UI widgets are populated from hydrated, normalized state—not raw persistence.  
- The UI does not auto-select presets without explicit user action.  
- Default values are not overwritten by presets or transient state.  
- FreeCAD objects use consistent naming and grouping conventions.

Deterministic initialization makes future AI-driven changes safer and easier to validate.

---

## 7. Document Patterns, Rules, and Standards

Patterns drift over time unless documented and reinforced.

The SquatchCut project uses a dedicated guide to codify:

- measurement architecture and unit rules  
- UI lifecycle and panel behavior  
- testing expectations for logic changes  
- Codex instruction formatting and reasoning levels  
- FreeCAD object naming and grouping standards  

By centralizing these rules, every subsequent AI interaction can reference them, reducing the risk of regressions or architectural fragmentation.

---

## 8. Integrate AI Into Scaled Agile, Not the Other Way Around

The SquatchCut experience supports several conclusions relevant to scaled-agile product management:

- AI should plug into existing roles and workflows, not replace them.  
- Product Owners still own value, direction, and prioritization.  
- Architecture (whether human-driven or AI-assisted) must remain explicit and stable.  
- Coding agents are best treated as powerful executors operating within predefined constraints.  
- Backlogs should reflect both functional stories and architectural guardrails.

When AI is treated as an integrated part of the agile ecosystem, it reinforces discipline instead of eroding it.

---

# Conclusion

The SquatchCut project demonstrates that AI-assisted development is not only feasible but highly effective when supported by:

- explicit and unambiguous requirements  
- well-defined architecture and invariants  
- tests that constrain and validate behavior  
- a three-layer collaboration model separating intent, specification, and execution  
- deterministic initialization and unit-handling logic  
- clear documentation of patterns and rules  

These practices form a reusable toolkit for teams building complex systems with LLM-driven engineering, particularly in environments that demand reliability, determinism, and long-term maintainability.

End of file.
