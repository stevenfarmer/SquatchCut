"""
Property-based tests for SquatchCut communication protocol adherence.

**Feature: ai-agent-documentation, Property 5: Communication Protocol Adherence**
*For any* AI agent interaction, communication rules must enforce role framing,
discovery, escalation, and stakeholder-ready updates.
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
"""

import pathlib
from hypothesis import given, strategies as st, settings
from constraint_framework import ConstraintFramework, ConstraintArea


DOC_PATHS = [
    pathlib.Path(__file__).resolve().parents[1] / "AGENTS.md",
    pathlib.Path(__file__).resolve().parents[1] / "AI_AGENT_HANDBOOK.md",
]

# Load documentation once to keep property iterations fast
DOC_CONTENT = "\n".join(
    path.read_text(encoding="utf-8").lower() for path in DOC_PATHS
)

# Required phrases that must appear across documentation for communication protocols
REQUIRED_COMMUNICATION_PHRASES = [
    "lead developer & product manager",
    "user is a non-technical stakeholder",
    "pause, ask 3-4 clarifying questions",
    "explain your plan in plain english",
    "stop and escalate when instructions conflict",
    "stakeholder-ready check-ins",
]


@given(st.sampled_from(REQUIRED_COMMUNICATION_PHRASES))
@settings(max_examples=100, deadline=2000)
def test_communication_protocol_language_present(required_phrase: str) -> None:
    """
    Property: Communication protocols must be documented with required phrases.
    **Feature: ai-agent-documentation, Property 5: Communication Protocol Adherence**
    """
    assert (
        required_phrase in DOC_CONTENT
    ), "Missing required communication guidance phrase: %s" % required_phrase


def test_communication_constraints_defined() -> None:
    """
    Ensure communication constraints are present in the framework.
    **Feature: ai-agent-documentation, Property 5: Communication Protocol Adherence**
    """
    framework = ConstraintFramework()
    communication_ids = [
        constraint.id
        for constraint in framework.get_constraints_by_area(
            ConstraintArea.COMMUNICATION
        )
    ]
    expected_ids = [
        "COMMUNICATION-001",
        "COMMUNICATION-002",
        "COMMUNICATION-003",
        "COMMUNICATION-004",
        "COMMUNICATION-005",
    ]

    for expected_id in expected_ids:
        assert (
            expected_id in communication_ids
        ), "Expected communication constraint %s to be defined" % expected_id
