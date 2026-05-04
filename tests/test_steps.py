"""Tests for custom BaseAgent workflow steps."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from methodic.schemas import CANONICAL_FIELDS


def _make_mock_ctx(state: dict):
    ctx = MagicMock()
    ctx.session.state = state
    ctx.actions = MagicMock()
    ctx.actions.escalate = False
    return ctx


def test_turn_checker_escalates_on_max_turns():
    from methodic.agents.turn_checker_step import TurnCheckerStep

    step = TurnCheckerStep(name="turn_checker", max_turns=6)
    state = {"turn_count": 6}
    ctx = _make_mock_ctx(state)
    # Synchronous check
    assert step.should_escalate(state, max_turns=6) is True


def test_turn_checker_does_not_escalate_early():
    from methodic.agents.turn_checker_step import TurnCheckerStep

    step = TurnCheckerStep(name="turn_checker", max_turns=6)
    state = {"turn_count": 3}
    assert step.should_escalate(state, max_turns=6) is False


def test_turn_checker_escalates_on_full_coverage():
    from methodic.agents.turn_checker_step import TurnCheckerStep

    step = TurnCheckerStep(name="turn_checker", max_turns=6)
    state = {
        "turn_count": 2,
        "participant_coverage": {f: "covered_high_confidence" for f in CANONICAL_FIELDS},
    }
    assert step.should_escalate(state, max_turns=6) is True


def test_coverage_step_computes_from_state():
    from methodic.agents.coverage_step import CoverageStep
    from methodic.schemas import ParticipantResponse, StructuredFields, QualityMetrics, EvidenceItem

    r = ParticipantResponse(
        participant_id="P-001", study_id="S-1", segment="lost",
        persona_summary="Test", conversation_status="complete",
        structured_fields=StructuredFields(
            primary_loss_reason="unclear_roi", secondary_loss_reason=None,
            roi_clarity="unclear", budget_timing="out_of_cycle",
            procurement_friction="unknown", security_concern="none",
            competitor_pressure="none", aha_moment_reached="no",
        ),
        field_confidence={"primary_loss_reason": 0.9},
        coverage_state={"primary_loss_reason": "covered_high_confidence"},
        quality=QualityMetrics(variable_coverage=0.5, ambiguity_resolved=True,
                                evidence_linked=True, requires_recontact=False),
        evidence=[], unresolved_ambiguities=[],
    )

    step = CoverageStep(name="coverage")
    result = step.compute({"P-001": r.model_dump()})
    assert result["per_variable"]["primary_loss_reason"] == "covered_high_confidence"


def test_bigquery_export_step_dry_run():
    from methodic.agents.bigquery_export_step import BigQueryExportStep

    step = BigQueryExportStep(name="bq_export")
    # Just verify it can be instantiated
    assert step.name == "bq_export"
