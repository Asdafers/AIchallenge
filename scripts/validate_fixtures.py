#!/usr/bin/env python3
"""WP2 fixture validator for the Methodic AI Agent Challenge.

Mission strategy linkage (mission_strategy['aichallenge']):
- thesis "no useful insights without good data": fixture personas demonstrate
  which variables Methodic resolves vs. the static baseline path. The
  per-participant and aggregate coverage matrices encoded here are the
  measurable surface of the data-quality claim.
- demo_must_show "measurable data quality improvement vs. static-survey
  baseline": the same fixture personas drive both paths (Methodic
  conversation transcripts and static_baseline raw answers), so coverage
  deltas are computed against identical inputs.
- non_goals "over-claiming statistical rigor": three primary participants
  (P-001/P-002/P-003) plus one reserve (P-005) are qualitative depth, not a
  statistical sample. The aggregate rule produces descriptive coverage
  states only -- never significance tests.
- stack_alignment: WP2 fixtures are static JSON; this validator does not
  require a live MCP, Cloud Run service, or BigQuery client. Live MCP wiring
  arrives in WP6.

Usage:
    python scripts/validate_fixtures.py

Exits 0 on success. Exits non-zero with a clear message naming the persona,
variable/field, and rule violated on any failure.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

try:
    from jsonschema import Draft7Validator, FormatChecker
except ImportError:  # pragma: no cover - import guard
    print(
        "ERROR: 'jsonschema' is not installed. Run: pip install jsonschema",
        file=sys.stderr,
    )
    sys.exit(2)


# ---- Locations -------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "docs" / "schema"
PR_SCHEMA_PATH = SCHEMA_DIR / "participant-response.schema.json"
GE_SCHEMA_PATH = SCHEMA_DIR / "guardrail-event.schema.json"
FIXTURES_DIR = REPO_ROOT / "fixtures"
PERSONAS_DIR = FIXTURES_DIR / "personas"
STATIC_DIR = FIXTURES_DIR / "static_baseline"

PRIMARY_PERSONAS = ["P-001", "P-002", "P-003"]
ALL_METHODIC_PERSONAS = ["P-001", "P-002", "P-003", "P-005"]
STATIC_PERSONAS = ["P-001", "P-002", "P-003"]

REQUIRED_VARIABLES = [
    "primary_loss_reason",
    "secondary_loss_reason",
    "roi_clarity",
    "budget_timing",
    "procurement_friction",
    "security_concern",
    "competitor_pressure",
    "aha_moment_reached",
]


# ---- Per-participant coverage matrix (binding spec, WP2 doc) ---------------
# Cells are (coverage_state, structured_field_value). Used by assertion 3.

PER_PARTICIPANT_MATRIX: dict[str, dict[str, tuple[str, Any]]] = {
    "P-001": {
        "primary_loss_reason": ("covered_high_confidence", "unclear_roi"),
        "secondary_loss_reason": ("covered_low_confidence", "budget_timing"),
        "roi_clarity": ("covered_high_confidence", "unclear"),
        "budget_timing": ("covered_high_confidence", "out_of_cycle"),
        "procurement_friction": ("covered_low_confidence", "unknown"),
        "security_concern": ("covered_high_confidence", "none"),
        "competitor_pressure": ("covered_high_confidence", "none"),
        "aha_moment_reached": ("covered_high_confidence", "no"),
    },
    "P-002": {
        "primary_loss_reason": ("covered_low_confidence", "competitor_pressure"),
        "secondary_loss_reason": ("covered_low_confidence", "procurement_friction"),
        "roi_clarity": ("covered_low_confidence", "partially_clear"),
        "budget_timing": ("covered_low_confidence", "unknown"),
        "procurement_friction": ("ambiguous", "unknown"),
        "security_concern": ("covered_high_confidence", "low"),
        "competitor_pressure": ("covered_low_confidence", "named_competitor"),
        "aha_moment_reached": ("covered_low_confidence", "no"),
    },
    "P-003": {
        "primary_loss_reason": ("covered_high_confidence", "unclear_roi"),
        "secondary_loss_reason": ("covered_high_confidence", "economic_buyer_gap"),
        "roi_clarity": ("covered_high_confidence", "unclear"),
        "budget_timing": ("covered_low_confidence", "unknown"),
        "procurement_friction": ("ambiguous", "unknown"),
        "security_concern": ("covered_high_confidence", "none"),
        "competitor_pressure": ("covered_high_confidence", "none"),
        "aha_moment_reached": ("covered_high_confidence", "no"),
    },
    "P-005": {
        # Re-plan persona: scope restricted to procurement_friction (and
        # supporting secondary_loss_reason). Other variables stay missing
        # so they cannot disturb the existing aggregate states.
        "primary_loss_reason": ("missing", "unknown"),
        "secondary_loss_reason": ("covered_low_confidence", "unclear_roi"),
        "roi_clarity": ("missing", "unknown"),
        "budget_timing": ("missing", "unknown"),
        "procurement_friction": ("covered_high_confidence", "high"),
        "security_concern": ("missing", "unknown"),
        "competitor_pressure": ("missing", "unknown"),
        "aha_moment_reached": ("missing", "unknown"),
    },
}


# Aggregate states after the primary three sessions (pre-replan).
PRIMARY_AGGREGATE_EXPECTED: dict[str, str] = {
    "primary_loss_reason": "covered_high_confidence",
    "secondary_loss_reason": "covered_high_confidence",
    "roi_clarity": "covered_high_confidence",
    "budget_timing": "covered_high_confidence",
    "procurement_friction": "ambiguous",  # the trigger
    "security_concern": "covered_high_confidence",
    "competitor_pressure": "covered_high_confidence",
    "aha_moment_reached": "covered_high_confidence",
}

# Aggregate states after re-plan (P-005 added). Only procurement_friction
# changes; all other aggregates remain identical to the primary set.
POST_REPLAN_AGGREGATE_EXPECTED: dict[str, str] = {
    **PRIMARY_AGGREGATE_EXPECTED,
    "procurement_friction": "covered_high_confidence",
}


# Static-baseline matrix (WP2 doc).
STATIC_BASELINE_MATRIX: dict[str, dict[str, str]] = {
    "P-001": {
        "primary_loss_reason": "ambiguous",
        "secondary_loss_reason": "missing",
        "roi_clarity": "missing",
        "budget_timing": "covered_low_confidence",
        "procurement_friction": "missing",
        "security_concern": "missing",
        "competitor_pressure": "missing",
        "aha_moment_reached": "missing",
    },
    "P-002": {
        "primary_loss_reason": "ambiguous",
        "secondary_loss_reason": "missing",
        "roi_clarity": "missing",
        "budget_timing": "missing",
        "procurement_friction": "missing",
        "security_concern": "covered_low_confidence",
        "competitor_pressure": "missing",
        "aha_moment_reached": "missing",
    },
    "P-003": {
        "primary_loss_reason": "missing",
        "secondary_loss_reason": "missing",
        "roi_clarity": "missing",
        "budget_timing": "missing",
        "procurement_friction": "missing",
        "security_concern": "missing",
        "competitor_pressure": "missing",
        "aha_moment_reached": "missing",
    },
}


# Coverage rank for "best wins" (rule 2).
COVERAGE_RANK = {
    "missing": 0,
    "ambiguous": 1,  # distinct branch; only used by rule 1 trump
    "covered_low_confidence": 2,
    "covered_high_confidence": 3,
}


# ---- jsonschema setup ------------------------------------------------------

_ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})$"
)

_FORMAT_CHECKER = FormatChecker()


def _check_iso8601(instance: Any) -> bool:
    if not isinstance(instance, str):
        return True
    if not _ISO8601_RE.match(instance):
        raise ValueError(f"{instance!r} is not a valid ISO-8601 date-time")
    try:
        datetime.fromisoformat(instance.replace("Z", "+00:00"))
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"{instance!r} is not a valid ISO-8601 date-time") from exc
    return True


_FORMAT_CHECKER.checks("date-time", raises=ValueError)(_check_iso8601)


def _fail(message: str) -> NoReturn:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def _load_json(path: Path, label: str) -> Any:
    if not path.exists():
        _fail(f"{label}: file not found at {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(f"{label}: invalid JSON in {path}: {exc}")


def _validate_against_schema(
    instance: Any, schema: dict, label: str
) -> None:
    validator = Draft7Validator(schema, format_checker=_FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        path = "/".join(str(p) for p in first.absolute_path) or "<root>"
        _fail(f"{label}: schema violation at '{path}': {first.message}")


# ---- Aggregate computation -------------------------------------------------


def _aggregate_state(
    persona_states: list[tuple[str, Any]],
) -> str:
    """Apply WP2 aggregate rule.

    Each entry is (coverage_state, structured_field_value). Rule:

    1. Ambiguity trump: if any persona has coverage_state == "ambiguous" AND
       no persona has coverage_state == "covered_high_confidence" with a
       non-"unknown" structured_field value, return "ambiguous".
    2. Best wins: else return the highest-rank coverage_state observed.
    """
    any_ambiguous = any(cs == "ambiguous" for cs, _ in persona_states)
    has_actionable_high = any(
        cs == "covered_high_confidence" and val != "unknown"
        for cs, val in persona_states
    )
    if any_ambiguous and not has_actionable_high:
        return "ambiguous"
    # Best wins. Filter out ambiguous (it loses to any covered_*) and pick max.
    candidates = [cs for cs, _ in persona_states if cs != "ambiguous"]
    if not candidates:
        # All ambiguous and no high-actionable -> handled above. Defensive.
        return "ambiguous"
    return max(candidates, key=lambda cs: COVERAGE_RANK[cs])


# ---- Main checks -----------------------------------------------------------


def _load_persona(persona_id: str) -> dict:
    path = PERSONAS_DIR / f"{persona_id}.json"
    return _load_json(path, f"persona fixture {persona_id}")


def _load_static(persona_id: str) -> dict:
    path = STATIC_DIR / f"{persona_id}.json"
    return _load_json(path, f"static_baseline fixture {persona_id}")


def main() -> int:
    pr_schema = _load_json(PR_SCHEMA_PATH, "participant-response.schema.json")
    ge_schema = _load_json(GE_SCHEMA_PATH, "guardrail-event.schema.json")
    Draft7Validator.check_schema(pr_schema)
    Draft7Validator.check_schema(ge_schema)

    # Load all persona fixtures up front so failures are deterministic.
    methodic_personas: dict[str, dict] = {
        pid: _load_persona(pid) for pid in ALL_METHODIC_PERSONAS
    }
    static_personas: dict[str, dict] = {
        pid: _load_static(pid) for pid in STATIC_PERSONAS
    }

    # ---------- Assertion 1: every Methodic + static expected_response
    # validates against participant-response.schema.json.
    for pid, persona in methodic_personas.items():
        if "expected_response" not in persona:
            _fail(f"persona {pid}: missing 'expected_response' block")
        _validate_against_schema(
            persona["expected_response"],
            pr_schema,
            f"persona {pid} expected_response",
        )
    for pid, fixture in static_personas.items():
        if "expected_response" not in fixture:
            _fail(f"static_baseline {pid}: missing 'expected_response' block")
        _validate_against_schema(
            fixture["expected_response"],
            pr_schema,
            f"static_baseline {pid} expected_response",
        )

    # ---------- Assertion 2: every guardrail event validates.
    for pid, persona in methodic_personas.items():
        events = persona.get("expected_guardrail_events", [])
        if not isinstance(events, list):
            _fail(f"persona {pid}: 'expected_guardrail_events' must be a list")
        for idx, event in enumerate(events):
            _validate_against_schema(
                event,
                ge_schema,
                f"persona {pid} expected_guardrail_events[{idx}]",
            )

    # ---------- Assertion 3: per-participant matrix check.
    for pid in ALL_METHODIC_PERSONAS:
        persona = methodic_personas[pid]
        er = persona["expected_response"]
        cov = er.get("coverage_state", {})
        sf = er.get("structured_fields", {})
        for var, (expected_cs, expected_val) in PER_PARTICIPANT_MATRIX[pid].items():
            actual_cs = cov.get(var)
            actual_val = sf.get(var)
            if actual_cs != expected_cs:
                _fail(
                    f"persona {pid} variable '{var}': coverage_state "
                    f"'{actual_cs}' != expected '{expected_cs}' "
                    "(WP2 per-participant matrix, assertion 3)"
                )
            if actual_val != expected_val:
                _fail(
                    f"persona {pid} variable '{var}': structured_fields value "
                    f"{actual_val!r} != expected {expected_val!r} "
                    "(WP2 per-participant matrix, assertion 3)"
                )

    # ---------- Assertion 4: aggregate over P-001/P-002/P-003.
    for var in REQUIRED_VARIABLES:
        contributions = []
        for pid in PRIMARY_PERSONAS:
            er = methodic_personas[pid]["expected_response"]
            cs = er["coverage_state"][var]
            val = er["structured_fields"][var]
            contributions.append((cs, val))
        actual = _aggregate_state(contributions)
        expected = PRIMARY_AGGREGATE_EXPECTED[var]
        if actual != expected:
            _fail(
                f"aggregate (primary three) variable '{var}': computed "
                f"'{actual}' != expected '{expected}' "
                "(WP2 aggregate rule, assertion 4)"
            )
    # Spot-check the procurement_friction trump.
    pf_primary = _aggregate_state([
        (
            methodic_personas[pid]["expected_response"]["coverage_state"][
                "procurement_friction"
            ],
            methodic_personas[pid]["expected_response"]["structured_fields"][
                "procurement_friction"
            ],
        )
        for pid in PRIMARY_PERSONAS
    ])
    if pf_primary != "ambiguous":
        _fail(
            "aggregate (primary three) procurement_friction must be "
            f"'ambiguous' but is '{pf_primary}' (assertion 4)"
        )
    # Other required-variable aggregates must be in {covered_low,covered_high}.
    for var in REQUIRED_VARIABLES:
        if var == "procurement_friction":
            continue
        agg = PRIMARY_AGGREGATE_EXPECTED[var]
        if agg not in {"covered_low_confidence", "covered_high_confidence"}:
            _fail(
                f"aggregate (primary three) variable '{var}' is '{agg}' "
                "but must be covered_low_confidence or covered_high_confidence "
                "(assertion 4)"
            )

    # ---------- Assertion 5: aggregate including P-005 (post-replan).
    for var in REQUIRED_VARIABLES:
        contributions = []
        for pid in ALL_METHODIC_PERSONAS:
            er = methodic_personas[pid]["expected_response"]
            cs = er["coverage_state"][var]
            val = er["structured_fields"][var]
            contributions.append((cs, val))
        actual = _aggregate_state(contributions)
        expected = POST_REPLAN_AGGREGATE_EXPECTED[var]
        if actual != expected:
            _fail(
                f"aggregate (post-replan) variable '{var}': computed "
                f"'{actual}' != expected '{expected}' "
                "(WP2 aggregate rule, assertion 5)"
            )
    # Procurement_friction must now be covered_high_confidence.
    pf_post = _aggregate_state([
        (
            methodic_personas[pid]["expected_response"]["coverage_state"][
                "procurement_friction"
            ],
            methodic_personas[pid]["expected_response"]["structured_fields"][
                "procurement_friction"
            ],
        )
        for pid in ALL_METHODIC_PERSONAS
    ])
    if pf_post != "covered_high_confidence":
        _fail(
            "aggregate (post-replan) procurement_friction must be "
            f"'covered_high_confidence' but is '{pf_post}' (assertion 5)"
        )
    # Confirm no other aggregate state changed between primary and post-replan.
    for var in REQUIRED_VARIABLES:
        if var == "procurement_friction":
            continue
        if PRIMARY_AGGREGATE_EXPECTED[var] != POST_REPLAN_AGGREGATE_EXPECTED[var]:
            _fail(
                f"aggregate state for '{var}' changed between primary and "
                "post-replan; only procurement_friction may change "
                "(assertion 5)"
            )

    # ---------- Assertion 6: P-002 guardrail timing.
    p002 = methodic_personas["P-002"]
    p002_events = p002.get("expected_guardrail_events", [])
    if len(p002_events) != 1:
        _fail(
            f"persona P-002: expected exactly 1 guardrail event, got "
            f"{len(p002_events)} (assertion 6, sign-off #1)"
        )
    ev = p002_events[0]
    if ev.get("event_type") != "participant_vague_answer":
        _fail(
            "persona P-002 guardrail event: event_type must be "
            f"'participant_vague_answer' but is {ev.get('event_type')!r} "
            "(assertion 6, sign-off #1)"
        )
    if ev.get("variable_affected") != "procurement_friction":
        _fail(
            "persona P-002 guardrail event: variable_affected must be "
            f"'procurement_friction' but is {ev.get('variable_affected')!r} "
            "(assertion 6, sign-off #1)"
        )
    trig = ev.get("trigger") or {}
    if trig.get("transcript_turn_id") != "T-002-07":
        _fail(
            "persona P-002 guardrail event: trigger.transcript_turn_id must "
            f"be 'T-002-07' but is {trig.get('transcript_turn_id')!r} "
            "(assertion 6, sign-off #1)"
        )
    if ev.get("action_taken") != "mark_ambiguous":
        _fail(
            "persona P-002 guardrail event: action_taken must be "
            f"'mark_ambiguous' but is {ev.get('action_taken')!r} "
            "(assertion 6, sign-off #1)"
        )
    if ev.get("measurement_intent_preserved") is not True:
        _fail(
            "persona P-002 guardrail event: measurement_intent_preserved must "
            f"be True but is {ev.get('measurement_intent_preserved')!r} "
            "(assertion 6, sign-off #1)"
        )

    # ---------- Assertion 7: P-001 procurement evidence.
    p001 = methodic_personas["P-001"]
    p001_evidence = p001["expected_response"]["evidence"]
    procurement_entries = [
        e for e in p001_evidence if e.get("field") == "procurement_friction"
    ]
    if len(procurement_entries) != 1:
        _fail(
            "persona P-001 evidence: expected exactly 1 entry with "
            f"field=='procurement_friction' but found {len(procurement_entries)} "
            "(assertion 7, sign-off #3)"
        )
    if procurement_entries[0].get("context_used") != []:
        _fail(
            "persona P-001 evidence for procurement_friction: context_used "
            "must be the empty list [] (no MCP corroboration) "
            "(assertion 7, sign-off #3)"
        )

    # ---------- Assertion 8: static baseline matrix.
    for pid, expected_map in STATIC_BASELINE_MATRIX.items():
        fixture = static_personas[pid]
        er = fixture["expected_response"]
        if er.get("conversation_status") != "static_form":
            _fail(
                f"static_baseline {pid}: conversation_status must be "
                f"'static_form' but is {er.get('conversation_status')!r} "
                "(assertion 8)"
            )
        cov = er.get("coverage_state", {})
        for var, expected_cs in expected_map.items():
            actual_cs = cov.get(var)
            if actual_cs != expected_cs:
                _fail(
                    f"static_baseline {pid} variable '{var}': coverage_state "
                    f"'{actual_cs}' != expected '{expected_cs}' "
                    "(WP2 static-baseline matrix, assertion 8)"
                )
    # Static ambiguity_resolved must be False for at least P-001 and P-002.
    for pid in ("P-001", "P-002"):
        ar = static_personas[pid]["expected_response"]["quality"][
            "ambiguity_resolved"
        ]
        if ar is not False:
            _fail(
                f"static_baseline {pid}: quality.ambiguity_resolved must be "
                f"False but is {ar!r} (assertion 8)"
            )

    # ---------- Assertion 9: schema invariant restated as boundary check.
    # All Methodic expected_response objects + all static expected_response
    # objects + all guardrail events were validated above. Restate explicitly
    # as a final pass so a failure here is unambiguous.
    boundary_failures = []
    pr_validator = Draft7Validator(pr_schema, format_checker=_FORMAT_CHECKER)
    ge_validator = Draft7Validator(ge_schema, format_checker=_FORMAT_CHECKER)
    for pid, persona in methodic_personas.items():
        for err in pr_validator.iter_errors(persona["expected_response"]):
            boundary_failures.append(
                f"persona {pid} expected_response: {err.message}"
            )
        for idx, event in enumerate(persona.get("expected_guardrail_events", [])):
            for err in ge_validator.iter_errors(event):
                boundary_failures.append(
                    f"persona {pid} expected_guardrail_events[{idx}]: {err.message}"
                )
    for pid, fixture in static_personas.items():
        for err in pr_validator.iter_errors(fixture["expected_response"]):
            boundary_failures.append(
                f"static_baseline {pid} expected_response: {err.message}"
            )
    if boundary_failures:
        _fail(
            "schema boundary check (assertion 9) found violations: "
            + boundary_failures[0]
        )

    print(
        "OK: 4 personas + 3 static baselines + guardrail events validated; "
        "primary aggregate procurement_friction=ambiguous, post-replan="
        "covered_high_confidence."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
