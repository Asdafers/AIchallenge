"""Tests for pure function tools."""

import pytest
from methodic.tools.coverage_checker import check_coverage
from methodic.schemas import (
    ParticipantResponse, StructuredFields, QualityMetrics,
    EvidenceItem, CANONICAL_FIELDS,
)


def _make_response(
    participant_id: str = "P-001",
    coverage: dict | None = None,
    confidence: dict | None = None,
) -> ParticipantResponse:
    return ParticipantResponse(
        participant_id=participant_id,
        study_id="STUDY-001",
        segment="lost_deal",
        persona_summary="Test persona",
        conversation_status="complete",
        structured_fields=StructuredFields(
            primary_loss_reason="unclear_roi",
            secondary_loss_reason=None,
            roi_clarity="unclear",
            budget_timing="out_of_cycle",
            procurement_friction="unknown",
            security_concern="none",
            competitor_pressure="none",
            aha_moment_reached="no",
        ),
        field_confidence=confidence or {"primary_loss_reason": 0.9},
        coverage_state=coverage or {"primary_loss_reason": "covered_high_confidence"},
        quality=QualityMetrics(
            variable_coverage=0.5, ambiguity_resolved=False,
            evidence_linked=True, requires_recontact=False,
        ),
        evidence=[
            EvidenceItem(
                field="primary_loss_reason", quote="Test quote",
                transcript_turn_id="turn-001", context_used=[],
            )
        ],
        unresolved_ambiguities=["procurement_friction"],
    )


def test_check_coverage_single_response():
    responses = [_make_response(coverage={
        "primary_loss_reason": "covered_high_confidence",
        "roi_clarity": "covered_high_confidence",
        "budget_timing": "covered_low_confidence",
        "procurement_friction": "ambiguous",
        "security_concern": "missing",
        "competitor_pressure": "missing",
        "aha_moment_reached": "missing",
    })]
    result = check_coverage(responses)
    assert result["overall_coverage"] == pytest.approx(2 / 8)
    assert result["per_variable"]["procurement_friction"] == "ambiguous"
    assert "procurement_friction" in result["ambiguous_variables"]


def test_check_coverage_aggregates_multiple():
    r1 = _make_response(participant_id="P-001",
        coverage={"primary_loss_reason": "covered_high_confidence"})
    r2 = _make_response(participant_id="P-002",
        coverage={"primary_loss_reason": "covered_high_confidence",
                   "procurement_friction": "covered_high_confidence"})
    result = check_coverage([r1, r2])
    assert result["per_variable"]["procurement_friction"] == "covered_high_confidence"


def test_check_coverage_empty():
    result = check_coverage([])
    assert result["overall_coverage"] == 0.0
    assert all(v == "missing" for v in result["per_variable"].values())


def test_check_coverage_all_covered():
    full = {f: "covered_high_confidence" for f in CANONICAL_FIELDS}
    result = check_coverage([_make_response(coverage=full)])
    assert result["overall_coverage"] == 1.0
    assert result["ambiguous_variables"] == []
    assert result["missing_variables"] == []
