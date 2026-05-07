"""Pydantic models mirroring canonical JSON schemas.

Source of truth: docs/schema/participant-response.schema.json
                 docs/schema/guardrail-event.schema.json
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


PrimaryLossReason = Literal[
    "unclear_roi", "budget_timing", "procurement_friction",
    "security_concern", "competitor_pressure", "missing_feature",
    "economic_buyer_gap", "other", "unknown",
]

RoiClarity = Literal["clear", "partially_clear", "unclear", "unknown"]
BudgetTiming = Literal["in_cycle", "out_of_cycle", "unknown"]
FrictionLevel = Literal["none", "low", "medium", "high", "unknown"]
CompetitorPressure = Literal["none", "named_competitor", "unknown"]
AhaMoment = Literal["yes", "no", "unknown"]
ConversationStatus = Literal["complete", "partial", "excluded", "static_form"]

CoverageState = Literal[
    "missing", "ambiguous", "covered_low_confidence", "covered_high_confidence",
]

CANONICAL_FIELDS = [
    "primary_loss_reason", "secondary_loss_reason", "roi_clarity",
    "budget_timing", "procurement_friction", "security_concern",
    "competitor_pressure", "aha_moment_reached",
]

CanonicalField = Literal[
    "primary_loss_reason", "secondary_loss_reason", "roi_clarity",
    "budget_timing", "procurement_friction", "security_concern",
    "competitor_pressure", "aha_moment_reached",
]

# Confidence float constrained to [0.0, 1.0]
ConfidenceFloat = Annotated[float, Field(ge=0.0, le=1.0)]


class StructuredFields(BaseModel):
    primary_loss_reason: PrimaryLossReason
    secondary_loss_reason: str | None
    roi_clarity: RoiClarity
    budget_timing: BudgetTiming
    procurement_friction: FrictionLevel
    security_concern: FrictionLevel
    competitor_pressure: CompetitorPressure
    aha_moment_reached: AhaMoment


class QualityMetrics(BaseModel):
    variable_coverage: float = Field(ge=0.0, le=1.0)
    ambiguity_resolved: bool
    evidence_linked: bool
    requires_recontact: bool


class EvidenceItem(BaseModel):
    field: CanonicalField
    quote: str
    transcript_turn_id: str = Field(min_length=1)
    context_used: list[str]


class ParticipantResponse(BaseModel):
    participant_id: str = Field(min_length=1)
    study_id: str = Field(min_length=1)
    segment: str = Field(min_length=1)
    persona_summary: str
    conversation_status: ConversationStatus
    structured_fields: StructuredFields
    field_confidence: dict[CanonicalField, ConfidenceFloat] = Field(default_factory=dict)
    coverage_state: dict[CanonicalField, CoverageState] = Field(default_factory=dict)
    quality: QualityMetrics
    evidence: list[EvidenceItem]
    unresolved_ambiguities: list[CanonicalField]


GuardrailEventType = Literal[
    "participant_misunderstanding", "participant_contradiction",
    "participant_frustration", "participant_vague_answer",
]

GuardrailAction = Literal[
    "rephrase_once", "clarifying_followup", "mark_ambiguous", "graceful_end",
]


class GuardrailTrigger(BaseModel):
    transcript_turn_id: str = Field(min_length=1)
    trigger_text: str


class GuardrailEvent(BaseModel):
    event_id: str = Field(min_length=1)
    study_id: str = Field(min_length=1)
    participant_id: str = Field(min_length=1)
    event_type: GuardrailEventType
    trigger: GuardrailTrigger
    action_taken: GuardrailAction
    measurement_intent_preserved: bool
    variable_affected: CanonicalField | None
    timestamp: str
