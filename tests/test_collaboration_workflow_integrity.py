"""
Property-based tests for SquatchCut collaboration workflow integrity.

**Feature: ai-agent-documentation, Property 10: Collaboration Workflow Integrity**
*For any* collaborative task, branch isolation, mediation, commit/PR standards,
and conflict handling must be documented and enforced.
**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
"""

import pathlib
from hypothesis import given, strategies as st, settings
from constraint_framework import ConstraintFramework, ConstraintArea


DOC_PATHS = [
    pathlib.Path(__file__).resolve().parents[1] / "AGENTS.md",
    pathlib.Path(__file__).resolve().parents[1] / "AI_AGENT_HANDBOOK.md",
]

DOC_CONTENT = "\n".join(
    path.read_text(encoding="utf-8").lower() for path in DOC_PATHS
)

REQUIRED_COLLABORATION_PHRASES = [
    "one ai per branch",
    "ai/<worker-name>/<feature>",
    "architect/human reviewer",
    "commit messages summarize scope and constraints",
    "prs must use the stakeholder-facing template",
    "never force-push over someone else's work",
    "record the plan and test outcomes",
]


@given(st.sampled_from(REQUIRED_COLLABORATION_PHRASES))
@settings(max_examples=100, deadline=2000)
def test_collaboration_workflow_language_present(required_phrase: str) -> None:
    """
    Property: Collaboration workflow rules must be documented with required phrases.
    **Feature: ai-agent-documentation, Property 10: Collaboration Workflow Integrity**
    """
    assert (
        required_phrase in DOC_CONTENT
    ), "Missing required collaboration workflow phrase: %s" % required_phrase


def test_collaboration_constraints_present() -> None:
    """
    Ensure collaboration-focused communication constraints are present.
    **Feature: ai-agent-documentation, Property 10: Collaboration Workflow Integrity**
    """
    framework = ConstraintFramework()
    communication_ids = [
        constraint.id
        for constraint in framework.get_constraints_by_area(
            ConstraintArea.COMMUNICATION
        )
    ]
    expected_ids = [
        "COMMUNICATION-004",
        "COMMUNICATION-005",
    ]

    for expected_id in expected_ids:
        assert (
            expected_id in communication_ids
        ), "Expected collaboration constraint %s to be defined" % expected_id
