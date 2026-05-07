"""Tests for Pydantic schema models."""

import pytest
from methodic.schemas import (
    ParticipantResponse,
    StructuredFields,
    QualityMetrics,
    EvidenceItem,
    GuardrailEvent,
    GuardrailTrigger,
    CoverageState,
)


def test_structured_fields_valid():
    sf = StructuredFields(
        primary_loss_reason="unclear_roi",
        secondary_loss_reason="budget_timing",
        roi_clarity="unclear",
        budget_timing="out_of_cycle",
        procurement_friction="none",
        security_concern="none",
        competitor_pressure="none",
        aha_moment_reached="no",
    )
    assert sf.primary_loss_reason == "unclear_roi"


def test_structured_fields_invalid_enum():
    with pytest.raises(Exception):
        StructuredFields(
            primary_loss_reason="invalid_value",
            secondary_loss_reason=None,
            roi_clarity="clear",
            budget_timing="in_cycle",
            procurement_friction="none",
            security_concern="none",
            competitor_pressure="none",
            aha_moment_reached="yes",
        )


def test_participant_response_minimal():
    resp = ParticipantResponse(
        participant_id="P-001",
        study_id="STUDY-001",
        segment="lost_deal_economic_buyer",
        persona_summary="VP Finance",
        conversation_status="complete",
        structured_fields=StructuredFields(
            primary_loss_reason="unclear_roi",
            secondary_loss_reason=None,
            roi_clarity="unclear",
            budget_timing="out_of_cycle",
            procurement_friction="none",
            security_concern="none",
            competitor_pressure="none",
            aha_moment_reached="no",
        ),
        field_confidence={"primary_loss_reason": 0.9, "roi_clarity": 0.85},
        coverage_state={"primary_loss_reason": "covered_high_confidence"},
        quality=QualityMetrics(
            variable_coverage=0.75,
            ambiguity_resolved=True,
            evidence_linked=True,
            requires_recontact=False,
        ),
        evidence=[
            EvidenceItem(
                field="primary_loss_reason",
                quote="We could never prove the ROI internally",
                transcript_turn_id="turn-003",
                context_used=["crm_notes"],
            )
        ],
        unresolved_ambiguities=[],
    )
    assert resp.participant_id == "P-001"
    assert resp.quality.variable_coverage == 0.75


def test_coverage_state_enum_validation():
    with pytest.raises(Exception):
        ParticipantResponse(
            participant_id="P-001",
            study_id="STUDY-001",
            segment="lost_deal",
            persona_summary="Test",
            conversation_status="complete",
            structured_fields=StructuredFields(
                primary_loss_reason="unclear_roi",
                secondary_loss_reason=None,
                roi_clarity="clear",
                budget_timing="in_cycle",
                procurement_friction="none",
                security_concern="none",
                competitor_pressure="none",
                aha_moment_reached="yes",
            ),
            field_confidence={},
            coverage_state={"primary_loss_reason": "invalid_state"},
            quality=QualityMetrics(
                variable_coverage=1.0,
                ambiguity_resolved=True,
                evidence_linked=True,
                requires_recontact=False,
            ),
            evidence=[],
            unresolved_ambiguities=[],
        )


def test_guardrail_event():
    event = GuardrailEvent(
        event_id="EVT-001",
        study_id="STUDY-001",
        participant_id="P-002",
        event_type="participant_vague_answer",
        trigger=GuardrailTrigger(
            transcript_turn_id="turn-005",
            trigger_text="It was complicated",
        ),
        action_taken="clarifying_followup",
        measurement_intent_preserved=True,
        variable_affected="procurement_friction",
        timestamp="2026-05-15T10:30:00Z",
    )
    assert event.event_type == "participant_vague_answer"
    assert event.action_taken == "clarifying_followup"


def test_field_confidence_bounds():
    with pytest.raises(Exception):
        ParticipantResponse(
            participant_id="P-001",
            study_id="STUDY-001",
            segment="lost_deal",
            persona_summary="Test",
            conversation_status="complete",
            structured_fields=StructuredFields(
                primary_loss_reason="unclear_roi",
                secondary_loss_reason=None,
                roi_clarity="clear",
                budget_timing="in_cycle",
                procurement_friction="none",
                security_concern="none",
                competitor_pressure="none",
                aha_moment_reached="yes",
            ),
            field_confidence={"primary_loss_reason": 1.5},
            coverage_state={},
            quality=QualityMetrics(
                variable_coverage=1.0,
                ambiguity_resolved=True,
                evidence_linked=True,
                requires_recontact=False,
            ),
            evidence=[],
            unresolved_ambiguities=[],
        )
