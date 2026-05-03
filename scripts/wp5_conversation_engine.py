#!/usr/bin/env python3
"""WP5 Participant Conversation Engine + Coverage Loop — deterministic fixture replay.

This is NOT a production conversation engine. It is an honestly labeled
prototype that demonstrates the participant conversation pipeline (question,
probe, tool call, extraction, coverage check, stop condition, guardrail
recovery) using deterministic fixture data.

Structured field extraction uses fixture ground truth — the expected_response
from each persona fixture is the extraction output. The pipeline events show
WHAT a production engine would do at each step; the fixture oracle shows the
RESULT it would produce.

MCP tool calls are simulated from fixture CRM/telemetry data. Live MCP
wiring arrives in WP6.

Mission strategy linkage (mission_strategy['aichallenge']):
- demo_must_show[3] "interactive participant conversations": this script
  processes 3 fixture transcripts through the conversation pipeline,
  demonstrating adaptive probing, MCP triangulation, and guardrail recovery.
- demo_must_show[4] "measurable data quality improvement": the coverage
  summary includes a side-by-side baseline comparison (Methodic 7/8 high-
  confidence vs Static 0/8).
- thesis "no useful insights without good data": the coverage loop shows
  procurement_friction remaining ambiguous after 3 sessions, triggering
  re-plan signal for WP6.

Usage:
    python scripts/wp5_conversation_engine.py
    python scripts/wp5_conversation_engine.py --output-responses r.json --output-coverage c.json

Exits 0 on success.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "fixtures" / "personas"
CRM_DIR = REPO_ROOT / "fixtures" / "crm"
TELEMETRY_DIR = REPO_ROOT / "fixtures" / "telemetry"
STATIC_DIR = REPO_ROOT / "fixtures" / "static_baseline"
WP4_PACKAGE = REPO_ROOT / "fixtures" / "wp4_methodology_package.json"
DEFAULT_RESPONSES_OUTPUT = REPO_ROOT / "fixtures" / "wp5_participant_responses.json"
DEFAULT_COVERAGE_OUTPUT = REPO_ROOT / "fixtures" / "wp5_coverage_summary.json"

PRIMARY_PERSONAS = ["P-001", "P-002", "P-003"]

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

COVERAGE_RANK = {
    "missing": 0,
    "ambiguous": 1,
    "covered_low_confidence": 2,
    "covered_high_confidence": 3,
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_optional(path: Path) -> dict | None:
    if path.exists():
        return _load_json(path)
    return None


def _event(index: int, event_type: str, persona_id: str, payload: dict) -> dict:
    return {
        "index": index,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "persona_id": persona_id,
        "payload": payload,
    }


# ---------------------------------------------------------------------------
# Question pool matching
# ---------------------------------------------------------------------------

def _map_turn_to_question(
    turn_text: str, question_pool: list[dict],
) -> dict | None:
    turn_lower = turn_text.lower()
    best_match = None
    best_overlap = 0
    for q in question_pool:
        prompt_lower = q["prompt"].lower()
        words = set(prompt_lower.split())
        overlap = sum(1 for w in words if w in turn_lower)
        if overlap > best_overlap and overlap >= 3:
            best_overlap = overlap
            best_match = q
    return best_match


# ---------------------------------------------------------------------------
# MCP tool call simulation
# ---------------------------------------------------------------------------

def _simulate_tool_call(
    tool_call: dict,
    crm_data: dict | None,
    telemetry_data: dict | None,
) -> dict:
    context_sources = []
    if crm_data is not None:
        context_sources.append("crm")
    if telemetry_data is not None:
        context_sources.append("telemetry")
    return {
        "tool_name": tool_call.get("tool_name", "unknown"),
        "input_summary": tool_call.get("input_summary", ""),
        "output_summary": tool_call.get("output_summary", ""),
        "context_source": "+".join(context_sources) if context_sources else "none",
        "context_available": len(context_sources) > 0,
        "note": (
            "Deterministic replay — MCP tool call simulated from "
            "fixture data. Live MCP wiring arrives in WP6."
        ),
    }


# ---------------------------------------------------------------------------
# Stop conditions
# ---------------------------------------------------------------------------

def _derive_stop_conditions(coverage_state: dict[str, str]) -> list[dict]:
    stops = []
    for var, state in coverage_state.items():
        if state == "covered_high_confidence":
            stops.append({
                "variable": var,
                "state": state,
                "reason": "Variable reached covered_high_confidence threshold.",
            })
    return stops


# ---------------------------------------------------------------------------
# Aggregate coverage (reimplementation of validate_fixtures.py rule)
# ---------------------------------------------------------------------------

def _aggregate_state(persona_states: list[tuple[str, Any]]) -> str:
    """Rule 1 (ambiguity trump): if any persona has "ambiguous" AND no persona
    has covered_high_confidence with non-"unknown" value, return "ambiguous".
    Rule 2 (best wins): else return highest-rank coverage_state."""
    any_ambiguous = any(cs == "ambiguous" for cs, _ in persona_states)
    has_actionable_high = any(
        cs == "covered_high_confidence" and val != "unknown"
        for cs, val in persona_states
    )
    if any_ambiguous and not has_actionable_high:
        return "ambiguous"
    candidates = [cs for cs, _ in persona_states if cs != "ambiguous"]
    if not candidates:
        return "ambiguous"
    return max(candidates, key=lambda cs: COVERAGE_RANK[cs])


# ---------------------------------------------------------------------------
# Per-persona pipeline
# ---------------------------------------------------------------------------

def process_persona(
    persona_id: str,
    persona_data: dict,
    question_pool: list[dict],
    crm_data: dict | None,
    telemetry_data: dict | None,
) -> tuple[dict, list[dict], list[dict]]:
    """Process one persona through the conversation pipeline.

    Returns (response_record, conversation_events, guardrail_events).
    """
    meta = persona_data["metadata"]
    transcript = persona_data["transcript"]
    expected = persona_data["expected_response"]
    expected_guardrails = persona_data.get("expected_guardrail_events", [])

    events: list[dict] = []
    idx = 0

    events.append(_event(idx, "conversation_started", persona_id, {
        "segment": meta["segment"],
        "role": meta["role"],
        "context_sources": meta.get("context_sources", []),
        "transcript_turns": len(transcript),
    }))
    idx += 1

    guardrail_events_emitted: list[dict] = []

    for turn in transcript:
        speaker = turn["speaker"]
        turn_id = turn["turn_id"]

        if speaker == "methodic":
            matched = _map_turn_to_question(turn["text"], question_pool)
            events.append(_event(idx, "question_asked", persona_id, {
                "turn_id": turn_id,
                "text": turn["text"],
                "matched_question_id": matched["question_id"] if matched else None,
                "maps_to": matched["maps_to"] if matched else [],
                "follow_up_policy": matched["follow_up_policy"] if matched else None,
            }))
            idx += 1

        elif speaker == "participant":
            events.append(_event(idx, "participant_response", persona_id, {
                "turn_id": turn_id,
                "text": turn["text"],
            }))
            idx += 1

        elif speaker == "system":
            if "tool_call" in turn:
                sim = _simulate_tool_call(
                    turn["tool_call"], crm_data, telemetry_data,
                )
                events.append(_event(idx, "tool_call_executed", persona_id, {
                    "turn_id": turn_id,
                    **sim,
                }))
                idx += 1

            if "guardrail" in turn.get("text", "").lower():
                for ge in expected_guardrails:
                    guardrail_events_emitted.append(ge)
                    events.append(_event(idx, "guardrail_triggered", persona_id, {
                        "event_id": ge["event_id"],
                        "event_type": ge["event_type"],
                        "variable_affected": ge.get("variable_affected"),
                        "trigger_turn_id": ge["trigger"]["transcript_turn_id"],
                        "trigger_text": ge["trigger"]["trigger_text"],
                        "action_taken": ge["action_taken"],
                        "measurement_intent_preserved": ge["measurement_intent_preserved"],
                    }))
                    idx += 1

    for ev_entry in expected["evidence"]:
        events.append(_event(idx, "field_extracted", persona_id, {
            "field": ev_entry["field"],
            "value": expected["structured_fields"][ev_entry["field"]],
            "confidence": expected["field_confidence"].get(ev_entry["field"]),
            "coverage_state": expected["coverage_state"][ev_entry["field"]],
            "source_turn_id": ev_entry["transcript_turn_id"],
            "quote": ev_entry["quote"],
            "context_used": ev_entry["context_used"],
            "extraction_source": "fixture_ground_truth",
        }))
        idx += 1

    covered_vars = {
        state: [] for state in [
            "covered_high_confidence", "covered_low_confidence",
            "ambiguous", "missing",
        ]
    }
    for var, state in expected["coverage_state"].items():
        covered_vars[state].append(var)

    events.append(_event(idx, "coverage_check", persona_id, {
        "variables_covered_high": covered_vars["covered_high_confidence"],
        "variables_covered_low": covered_vars["covered_low_confidence"],
        "variables_ambiguous": covered_vars["ambiguous"],
        "variables_missing": covered_vars["missing"],
        "coverage_fraction": expected["quality"]["variable_coverage"],
    }))
    idx += 1

    stops = _derive_stop_conditions(expected["coverage_state"])
    for stop in stops:
        events.append(_event(idx, "stop_condition_met", persona_id, {
            **stop,
            "note": (
                "Stop conditions derived from fixture coverage_state values, "
                "not evaluated at conversation runtime."
            ),
        }))
        idx += 1

    events.append(_event(idx, "conversation_complete", persona_id, {
        "conversation_status": expected["conversation_status"],
        "variables_at_stop": len(stops),
        "variables_total": len(REQUIRED_VARIABLES),
        "guardrail_events_emitted": len(guardrail_events_emitted),
        "variable_coverage": expected["quality"]["variable_coverage"],
        "ambiguity_resolved": expected["quality"]["ambiguity_resolved"],
    }))

    response_record = copy.deepcopy(expected)
    return response_record, events, guardrail_events_emitted


# ---------------------------------------------------------------------------
# Baseline comparison
# ---------------------------------------------------------------------------

def _build_baseline_comparison(
    responses: list[dict],
    static_baselines: dict[str, dict],
) -> dict:
    per_participant = {}
    for resp in responses:
        pid = resp["participant_id"]
        static = static_baselines.get(pid)
        if not static:
            continue
        s_er = static["expected_response"]
        per_participant[pid] = {
            "methodic_variable_coverage": resp["quality"]["variable_coverage"],
            "static_variable_coverage": s_er["quality"]["variable_coverage"],
            "delta": round(
                resp["quality"]["variable_coverage"]
                - s_er["quality"]["variable_coverage"], 3,
            ),
            "methodic_ambiguity_resolved": resp["quality"]["ambiguity_resolved"],
            "static_ambiguity_resolved": s_er["quality"]["ambiguity_resolved"],
            "methodic_evidence_linked": resp["quality"]["evidence_linked"],
            "static_evidence_linked": s_er["quality"]["evidence_linked"],
        }

    static_agg: dict[str, str] = {}
    for var in REQUIRED_VARIABLES:
        contributions = []
        for pid in PRIMARY_PERSONAS:
            static = static_baselines.get(pid)
            if not static:
                continue
            s_er = static["expected_response"]
            cs = s_er["coverage_state"][var]
            val = s_er["structured_fields"][var]
            if val is None:
                val = "unknown"
            contributions.append((cs, val))
        if contributions:
            static_agg[var] = _aggregate_state(contributions)

    static_high = sum(
        1 for v in static_agg.values() if v == "covered_high_confidence"
    )
    static_missing = sum(1 for v in static_agg.values() if v == "missing")

    return {
        "per_participant": per_participant,
        "study_level": {
            "methodic_high_confidence_variables": None,
            "static_high_confidence_variables": static_high,
            "static_missing_variables": static_missing,
            "static_aggregate": static_agg,
        },
    }


# ---------------------------------------------------------------------------
# Coverage summary
# ---------------------------------------------------------------------------

def build_coverage_summary(
    responses: list[dict],
    events_by_persona: dict[str, list[dict]],
    all_guardrails: list[dict],
    static_baselines: dict[str, dict],
) -> dict:
    per_variable: dict[str, dict] = {}
    for var in REQUIRED_VARIABLES:
        contributions: dict[str, dict] = {}
        agg_inputs: list[tuple[str, Any]] = []
        for resp in responses:
            pid = resp["participant_id"]
            cs = resp["coverage_state"][var]
            val = resp["structured_fields"][var]
            contributions[pid] = {"state": cs, "value": val}
            agg_inputs.append((cs, val))
        agg = _aggregate_state(agg_inputs)
        entry: dict[str, Any] = {
            "state": agg,
            "contributing_personas": contributions,
        }
        if agg == "ambiguous":
            entry["replan_trigger"] = True
            entry["replan_reason"] = (
                f"Ambiguity trump: aggregate state is 'ambiguous' because "
                f"no persona provides covered_high_confidence with a "
                f"non-'unknown' value for {var}."
            )
        per_variable[var] = entry

    unresolved = [v for v, d in per_variable.items() if d["state"] == "ambiguous"]
    methodic_high = sum(
        1 for d in per_variable.values() if d["state"] == "covered_high_confidence"
    )

    baseline = _build_baseline_comparison(responses, static_baselines)
    baseline["study_level"]["methodic_high_confidence_variables"] = methodic_high

    methodic_avg_coverage = (
        sum(r["quality"]["variable_coverage"] for r in responses) / len(responses)
        if responses else 0
    )
    static_avg_coverage = 0.0
    static_count = 0
    for pid in PRIMARY_PERSONAS:
        sb = static_baselines.get(pid)
        if sb:
            static_avg_coverage += sb["expected_response"]["quality"]["variable_coverage"]
            static_count += 1
    if static_count:
        static_avg_coverage /= static_count

    return {
        "study_id": "WL-2026-Q2-MM",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine_label": "deterministic_fixture_replay",
        "extraction_source": "fixture_ground_truth",
        "honest_label": (
            "This is NOT a production conversation engine. It is an honestly "
            "labeled prototype that demonstrates the conversation pipeline "
            "using deterministic fixture data. Structured field extraction uses "
            "fixture ground truth, not NLP."
        ),
        "inputs": {
            "persona_fixtures": [
                f"fixtures/personas/{pid}.json" for pid in PRIMARY_PERSONAS
            ],
            "question_pool": "fixtures/wp4_methodology_package.json",
            "crm_fixtures": [
                f"fixtures/crm/{pid}.json" for pid in PRIMARY_PERSONAS
            ],
            "telemetry_fixtures": [
                f"fixtures/telemetry/{pid}.json"
                for pid in PRIMARY_PERSONAS
                if (TELEMETRY_DIR / f"{pid}.json").exists()
            ],
            "static_baselines": [
                f"fixtures/static_baseline/{pid}.json" for pid in PRIMARY_PERSONAS
            ],
        },
        "participants_processed": PRIMARY_PERSONAS,
        "participants_excluded": ["P-005"],
        "exclusion_reason": (
            "P-005 is the re-plan reserve persona, processed in WP6 "
            "after the coverage gap triggers autonomous re-plan."
        ),
        "per_variable_aggregate": per_variable,
        "replan_signal": {
            "triggered": len(unresolved) > 0,
            "unresolved_variables": unresolved,
            "recommended_action": (
                "Add P-005 (slipping_deal_procurement, Procurement Lead) to "
                "resolve procurement_friction with a targeted session."
                if unresolved else "No re-plan needed."
            ),
            "note": "This signal is consumed by WP6 autonomous re-plan.",
        },
        "quality_summary": {
            "methodic": {
                "participants": len(responses),
                "variables_covered_high": methodic_high,
                "variables_ambiguous": len(unresolved),
                "aggregate_coverage_high_fraction": round(
                    methodic_high / len(REQUIRED_VARIABLES), 3,
                ),
                "guardrail_events": len(all_guardrails),
                "avg_variable_coverage": round(methodic_avg_coverage, 3),
            },
            "static_baseline": {
                "participants": static_count,
                "variables_covered_high": baseline["study_level"][
                    "static_high_confidence_variables"
                ],
                "variables_missing": baseline["study_level"][
                    "static_missing_variables"
                ],
                "aggregate_coverage_high_fraction": 0.0,
                "guardrail_events": 0,
                "avg_variable_coverage": round(static_avg_coverage, 3),
            },
        },
        "baseline_comparison": baseline,
        "processing_events": events_by_persona,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "WP5: Participant Conversation Engine + Coverage Loop "
            "(deterministic fixture replay)"
        ),
    )
    parser.add_argument(
        "--output-responses", type=str, default=None,
        help="Output path for participant responses (default: fixtures/wp5_participant_responses.json)",
    )
    parser.add_argument(
        "--output-coverage", type=str, default=None,
        help="Output path for coverage summary (default: fixtures/wp5_coverage_summary.json)",
    )
    args = parser.parse_args()

    resp_path = Path(args.output_responses) if args.output_responses else DEFAULT_RESPONSES_OUTPUT
    cov_path = Path(args.output_coverage) if args.output_coverage else DEFAULT_COVERAGE_OUTPUT

    wp4 = _load_json(WP4_PACKAGE)
    question_pool = wp4["question_pool"]

    responses: list[dict] = []
    events_by_persona: dict[str, list[dict]] = {}
    all_guardrails: list[dict] = []

    for pid in PRIMARY_PERSONAS:
        persona = _load_json(PERSONAS_DIR / f"{pid}.json")
        crm = _load_json_optional(CRM_DIR / f"{pid}.json")
        telemetry = _load_json_optional(TELEMETRY_DIR / f"{pid}.json")

        resp, events, guardrails = process_persona(
            pid, persona, question_pool, crm, telemetry,
        )
        responses.append(resp)
        events_by_persona[pid] = events
        all_guardrails.extend(guardrails)

    static_baselines: dict[str, dict] = {}
    for pid in PRIMARY_PERSONAS:
        sb = _load_json_optional(STATIC_DIR / f"{pid}.json")
        if sb:
            static_baselines[pid] = sb

    coverage = build_coverage_summary(
        responses, events_by_persona, all_guardrails, static_baselines,
    )

    resp_path.write_text(
        json.dumps(responses, indent=2) + "\n", encoding="utf-8",
    )
    cov_path.write_text(
        json.dumps(coverage, indent=2) + "\n", encoding="utf-8",
    )

    pf_state = coverage["per_variable_aggregate"]["procurement_friction"]["state"]
    print(f"OK: WP5 conversation engine complete")
    print(f"    participants: {len(responses)}")
    print(f"    responses written to: {resp_path}")
    print(f"    coverage written to: {cov_path}")
    print(f"    aggregate procurement_friction: {pf_state}")
    print(f"    replan triggered: {coverage['replan_signal']['triggered']}")
    print(f"    guardrail events: {len(all_guardrails)}")
    print(f"    methodic avg coverage: {coverage['quality_summary']['methodic']['avg_variable_coverage']}")
    print(f"    static avg coverage: {coverage['quality_summary']['static_baseline']['avg_variable_coverage']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
