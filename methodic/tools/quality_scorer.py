"""Quality scorer - deterministic quality metrics. No LLM calls."""

from __future__ import annotations
from methodic.schemas import ParticipantResponse, QualityMetrics, CANONICAL_FIELDS


def score_quality(response: ParticipantResponse) -> QualityMetrics:
    covered_high = sum(1 for f in CANONICAL_FIELDS
        if response.coverage_state.get(f) == "covered_high_confidence")
    variable_coverage = covered_high / len(CANONICAL_FIELDS)
    ambiguity_resolved = len(response.unresolved_ambiguities) == 0
    evidence_fields = {e.field for e in response.evidence}
    covered_fields = {f for f in CANONICAL_FIELDS
        if response.coverage_state.get(f) in ("covered_high_confidence", "covered_low_confidence")}
    evidence_linked = covered_fields.issubset(evidence_fields) if covered_fields else True
    requires_recontact = len(response.unresolved_ambiguities) > 0 or variable_coverage < 0.5
    return QualityMetrics(
        variable_coverage=variable_coverage, ambiguity_resolved=ambiguity_resolved,
        evidence_linked=evidence_linked, requires_recontact=requires_recontact,
    )
