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


from methodic.tools.quality_scorer import score_quality


def test_score_quality_complete():
    r = _make_response(
        coverage={f: "covered_high_confidence" for f in CANONICAL_FIELDS},
        confidence={f: 0.9 for f in CANONICAL_FIELDS},
    )
    r.evidence = [EvidenceItem(field=f, quote="Q", transcript_turn_id="t-1", context_used=[]) for f in CANONICAL_FIELDS]
    r.unresolved_ambiguities = []
    q = score_quality(r)
    assert q.variable_coverage == 1.0
    assert q.ambiguity_resolved is True
    assert q.requires_recontact is False


def test_score_quality_partial():
    r = _make_response(coverage={
        "primary_loss_reason": "covered_high_confidence",
        "procurement_friction": "ambiguous",
    })
    r.evidence = [EvidenceItem(field="primary_loss_reason", quote="Q", transcript_turn_id="t-1", context_used=[])]
    r.unresolved_ambiguities = ["procurement_friction"]
    q = score_quality(r)
    assert q.variable_coverage < 1.0
    assert q.ambiguity_resolved is False
    assert q.requires_recontact is True


from unittest.mock import patch
from methodic.tools.extractor import extract_structured_fields


@pytest.mark.asyncio
async def test_extract_structured_fields_mock():
    mock_extraction = {
        "primary_loss_reason": "unclear_roi",
        "secondary_loss_reason": None,
        "roi_clarity": "unclear",
        "budget_timing": "out_of_cycle",
        "procurement_friction": "none",
        "security_concern": "none",
        "competitor_pressure": "none",
        "aha_moment_reached": "no",
        "field_confidence": {"primary_loss_reason": 0.92, "roi_clarity": 0.85},
        "evidence": [{
            "field": "primary_loss_reason",
            "quote": "We could never prove the ROI",
            "transcript_turn_id": "turn-003",
            "context_used": ["crm_notes"],
        }],
    }

    with patch("methodic.tools.extractor._call_gemini_extraction") as mock:
        mock.return_value = mock_extraction
        result = await extract_structured_fields(
            transcript=[
                {"role": "interviewer", "content": "What led to the decision?"},
                {"role": "participant", "content": "We could never prove the ROI internally."},
            ],
            participant_id="P-001",
            study_id="STUDY-001",
        )
    assert result.structured_fields.primary_loss_reason == "unclear_roi"
    assert result.field_confidence["primary_loss_reason"] == pytest.approx(0.92)
    assert len(result.evidence) == 1


@pytest.mark.asyncio
async def test_extract_handles_invalid_json():
    with patch("methodic.tools.extractor._call_gemini_extraction") as mock:
        mock.side_effect = [ValueError("Invalid JSON"), {
            "primary_loss_reason": "unknown", "secondary_loss_reason": None,
            "roi_clarity": "unknown", "budget_timing": "unknown",
            "procurement_friction": "unknown", "security_concern": "unknown",
            "competitor_pressure": "unknown", "aha_moment_reached": "unknown",
            "field_confidence": {}, "evidence": [],
        }]
        result = await extract_structured_fields(
            transcript=[{"role": "interviewer", "content": "Hello"}],
            participant_id="P-001", study_id="STUDY-001",
        )
    assert result.conversation_status == "partial"


@pytest.mark.asyncio
async def test_extract_marks_partial_on_total_failure():
    with patch("methodic.tools.extractor._call_gemini_extraction") as mock:
        mock.side_effect = Exception("API timeout")
        result = await extract_structured_fields(
            transcript=[{"role": "interviewer", "content": "Hello"}],
            participant_id="P-001", study_id="STUDY-001",
        )
    assert result.conversation_status == "partial"
    assert all(v == "missing" for v in result.coverage_state.values())


from methodic.tools.bigquery_export import export_to_bigquery, _flatten_response


def test_export_dry_run():
    result = export_to_bigquery([_make_response()], dry_run=True)
    assert result["rows_written"] == 1
    assert result["dry_run"] is True


def test_export_flattens_fields():
    r = _make_response(
        coverage={f: "covered_high_confidence" for f in CANONICAL_FIELDS},
        confidence={"primary_loss_reason": 0.95, "roi_clarity": 0.8},
    )
    row = _flatten_response(r)
    assert row["primary_loss_reason"] == "unclear_roi"
    assert row["conf_primary_loss_reason"] == 0.95
    assert row["cov_primary_loss_reason"] == "covered_high_confidence"
    assert "exported_at" in row


def test_export_dry_run_fail_on_error():
    result = export_to_bigquery([_make_response()], dry_run=True, fail_on_error=True)
    assert result["rows_written"] == 1
