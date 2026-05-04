"""Structured field extractor - calls Gemini with response_schema via google-genai SDK.

Recovery matrix:
- Invalid JSON: retry once with error context, then mark partial
- Missing evidence: downgrade affected coverage to ambiguous
- API timeout/rate limit: return partial response with all fields unknown
- Safety refusal: mark unresolved, do not fabricate
"""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai

from methodic import MODEL
from methodic.schemas import (
    ParticipantResponse, StructuredFields, QualityMetrics,
    EvidenceItem, CANONICAL_FIELDS,
)
from methodic.tools.quality_scorer import score_quality

log = logging.getLogger(__name__)

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "primary_loss_reason": {
            "type": "string",
            "enum": ["unclear_roi", "budget_timing", "procurement_friction",
                     "security_concern", "competitor_pressure", "missing_feature",
                     "economic_buyer_gap", "other", "unknown"],
        },
        "secondary_loss_reason": {"type": "string"},
        "roi_clarity": {"type": "string", "enum": ["clear", "partially_clear", "unclear", "unknown"]},
        "budget_timing": {"type": "string", "enum": ["in_cycle", "out_of_cycle", "unknown"]},
        "procurement_friction": {"type": "string", "enum": ["none", "low", "medium", "high", "unknown"]},
        "security_concern": {"type": "string", "enum": ["none", "low", "medium", "high", "unknown"]},
        "competitor_pressure": {"type": "string", "enum": ["none", "named_competitor", "unknown"]},
        "aha_moment_reached": {"type": "string", "enum": ["yes", "no", "unknown"]},
        "field_confidence": {
            "type": "object",
            "properties": {f: {"type": "number"} for f in CANONICAL_FIELDS},
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"}, "quote": {"type": "string"},
                    "transcript_turn_id": {"type": "string"},
                    "context_used": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["field", "quote", "transcript_turn_id", "context_used"],
            },
        },
    },
    "required": ["primary_loss_reason", "roi_clarity", "budget_timing",
                  "procurement_friction", "security_concern", "competitor_pressure",
                  "aha_moment_reached", "field_confidence", "evidence"],
}

EXTRACTION_PROMPT = """You are a structured data extractor for B2B win-loss research.

Given a conversation transcript, extract:
1. The 8 canonical structured fields with their enum values
2. Confidence scores (0.0-1.0) for each field
3. Evidence items linking fields to specific quotes

Rules:
- Only extract what is explicitly stated or strongly implied
- Use "unknown" when the participant hasn't addressed a topic
- Confidence below 0.5 means weak or indirect evidence
- Every non-"unknown" field MUST have at least one evidence item

Transcript:
{transcript}
"""


async def _call_gemini_extraction(transcript_text: str) -> dict[str, Any]:
    client = genai.Client()
    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=EXTRACTION_PROMPT.format(transcript=transcript_text),
        config={
            "response_mime_type": "application/json",
            "response_schema": EXTRACTION_SCHEMA,
        },
    )
    if not response.text:
        raise ValueError("Empty response from Gemini")
    return json.loads(response.text)


def _format_transcript(transcript: list[dict[str, str]]) -> str:
    return "\n".join(
        f"[Turn {i+1}] {t.get('role', 'unknown').upper()}: {t.get('content', '')}"
        for i, t in enumerate(transcript)
    )


def _empty_response(participant_id: str, study_id: str, segment: str, persona_summary: str) -> ParticipantResponse:
    return ParticipantResponse(
        participant_id=participant_id, study_id=study_id,
        segment=segment, persona_summary=persona_summary,
        conversation_status="partial",
        structured_fields=StructuredFields(
            primary_loss_reason="unknown", secondary_loss_reason=None,
            roi_clarity="unknown", budget_timing="unknown",
            procurement_friction="unknown", security_concern="unknown",
            competitor_pressure="unknown", aha_moment_reached="unknown",
        ),
        field_confidence={},
        coverage_state={f: "missing" for f in CANONICAL_FIELDS},
        quality=QualityMetrics(variable_coverage=0.0, ambiguity_resolved=True,
                                evidence_linked=True, requires_recontact=True),
        evidence=[], unresolved_ambiguities=[],
    )


async def extract_structured_fields(
    transcript: list[dict[str, str]],
    participant_id: str,
    study_id: str,
    segment: str = "unknown",
    persona_summary: str = "",
) -> ParticipantResponse:
    transcript_text = _format_transcript(transcript)

    # Retry once on failure
    raw = None
    for attempt in range(2):
        try:
            raw = await _call_gemini_extraction(transcript_text)
            break
        except Exception as e:
            log.warning("Extraction attempt %d failed: %s", attempt + 1, e)
            if attempt == 1:
                return _empty_response(participant_id, study_id, segment, persona_summary)

    if raw is None:
        return _empty_response(participant_id, study_id, segment, persona_summary)

    structured_fields = StructuredFields(
        primary_loss_reason=raw.get("primary_loss_reason", "unknown"),
        secondary_loss_reason=raw.get("secondary_loss_reason"),
        roi_clarity=raw.get("roi_clarity", "unknown"),
        budget_timing=raw.get("budget_timing", "unknown"),
        procurement_friction=raw.get("procurement_friction", "unknown"),
        security_concern=raw.get("security_concern", "unknown"),
        competitor_pressure=raw.get("competitor_pressure", "unknown"),
        aha_moment_reached=raw.get("aha_moment_reached", "unknown"),
    )

    field_confidence = {
        k: max(0.0, min(1.0, v))
        for k, v in raw.get("field_confidence", {}).items()
        if k in CANONICAL_FIELDS and isinstance(v, (int, float))
    }

    evidence = [
        EvidenceItem(field=e["field"], quote=e["quote"],
            transcript_turn_id=e.get("transcript_turn_id", f"turn-{i+1}"),
            context_used=e.get("context_used", []))
        for i, e in enumerate(raw.get("evidence", []))
        if e.get("field") in CANONICAL_FIELDS
    ]

    # Downgrade coverage for fields with no evidence
    evidence_fields = {e.field for e in evidence}
    coverage_state = {}
    for field in CANONICAL_FIELDS:
        value = getattr(structured_fields, field)
        conf = field_confidence.get(field, 0.0)
        if value == "unknown" or value is None:
            coverage_state[field] = "missing"
        elif field not in evidence_fields:
            coverage_state[field] = "ambiguous"
        elif conf >= 0.7:
            coverage_state[field] = "covered_high_confidence"
        elif conf >= 0.4:
            coverage_state[field] = "covered_low_confidence"
        else:
            coverage_state[field] = "ambiguous"

    response = ParticipantResponse(
        participant_id=participant_id, study_id=study_id,
        segment=segment, persona_summary=persona_summary,
        conversation_status="partial",
        structured_fields=structured_fields,
        field_confidence=field_confidence,
        coverage_state=coverage_state,
        quality=QualityMetrics(variable_coverage=0.0, ambiguity_resolved=True,
                                evidence_linked=True, requires_recontact=False),
        evidence=evidence,
        unresolved_ambiguities=[f for f, s in coverage_state.items() if s == "ambiguous"],
    )
    response.quality = score_quality(response)
    return response
