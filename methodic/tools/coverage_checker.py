"""Coverage checker - deterministic variable coverage computation. No LLM calls."""

from __future__ import annotations
from methodic.schemas import ParticipantResponse, CoverageState, CANONICAL_FIELDS

COVERAGE_RANK = {
    "missing": 0, "ambiguous": 1,
    "covered_low_confidence": 2, "covered_high_confidence": 3,
}


def check_coverage(responses: list[ParticipantResponse]) -> dict:
    best: dict[str, CoverageState] = {f: "missing" for f in CANONICAL_FIELDS}
    for response in responses:
        for field, state in response.coverage_state.items():
            if field in best and COVERAGE_RANK.get(state, 0) > COVERAGE_RANK.get(best[field], 0):
                best[field] = state

    high_count = sum(1 for v in best.values() if v == "covered_high_confidence")
    return {
        "per_variable": best,
        "overall_coverage": high_count / len(CANONICAL_FIELDS) if CANONICAL_FIELDS else 0.0,
        "ambiguous_variables": [f for f, v in best.items() if v == "ambiguous"],
        "missing_variables": [f for f, v in best.items() if v == "missing"],
    }
