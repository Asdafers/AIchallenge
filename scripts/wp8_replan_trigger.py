#!/usr/bin/env python3
"""WP8 Autonomous Re-Plan Trigger — detects unresolved coverage gaps after
primary sessions and adds exactly one targeted reserve participant.

Reads WP5 coverage summary, checks the replan_signal, and if
procurement_friction is ambiguous/unresolved, adds P-005 (Procurement Lead)
as a targeted session. Records the trigger rationale, P-005 response, and
final coverage state showing procurement_friction resolved.

Usage:
    python3 scripts/wp8_replan_trigger.py
    python3 scripts/wp8_replan_trigger.py --output fixtures/wp8_replan_trace.json

Exits 0 on success.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WP5_COVERAGE = REPO_ROOT / "fixtures" / "wp5_coverage_summary.json"
WP5_RESPONSES = REPO_ROOT / "fixtures" / "wp5_participant_responses.json"
PERSONA_DIR = REPO_ROOT / "fixtures" / "personas"
DEFAULT_OUTPUT = REPO_ROOT / "fixtures" / "wp8_replan_trace.json"

CANONICAL_FIELDS = [
    "primary_loss_reason", "secondary_loss_reason", "roi_clarity",
    "budget_timing", "procurement_friction", "security_concern",
    "competitor_pressure", "aha_moment_reached",
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_replan_signal(coverage: dict) -> dict:
    """Check whether the replan signal is triggered and return details."""
    signal = coverage.get("replan_signal", {})
    triggered = signal.get("triggered", False)
    unresolved = signal.get("unresolved_variables", [])

    per_var = coverage.get("per_variable_aggregate", {})
    unresolved_details = {}
    for var in unresolved:
        var_data = per_var.get(var, {})
        unresolved_details[var] = {
            "aggregate_state": var_data.get("state", "unknown"),
            "contributing_personas": var_data.get("contributing_personas", {}),
        }

    return {
        "triggered": triggered,
        "unresolved_variables": unresolved,
        "unresolved_details": unresolved_details,
        "recommended_action": signal.get("recommended_action", ""),
    }


def _find_reserve_persona(unresolved_vars: list[str]) -> dict | None:
    """Find a reserve persona targeting the unresolved variables."""
    for path in sorted(PERSONA_DIR.glob("P-*.json")):
        persona = _load_json(path)
        meta = persona.get("metadata", {})
        if not meta.get("replan_persona", False):
            continue
        scope_vars = meta.get("replan_scope_variables", [])
        if any(v in unresolved_vars for v in scope_vars):
            return persona
    return None


def _replay_persona_session(persona: dict) -> dict:
    """Extract the expected_response from the persona fixture."""
    return persona["expected_response"]


def _compute_final_coverage(
    primary_coverage: dict,
    replan_response: dict,
) -> dict:
    """Merge the replan participant's coverage into the aggregate."""
    per_var = primary_coverage.get("per_variable_aggregate", {})
    replan_coverage = replan_response.get("coverage_state", {})
    replan_fields = replan_response.get("structured_fields", {})
    pid = replan_response["participant_id"]

    final: dict[str, dict] = {}
    for var in CANONICAL_FIELDS:
        primary_state = per_var.get(var, {}).get("state", "missing")
        primary_personas = dict(per_var.get(var, {}).get("contributing_personas", {}))

        replan_state = replan_coverage.get(var, "missing")
        replan_value = replan_fields.get(var)

        primary_personas[pid] = {
            "state": replan_state,
            "value": replan_value,
        }

        if replan_state == "covered_high_confidence" and replan_value != "unknown":
            new_aggregate = "covered_high_confidence"
        else:
            new_aggregate = primary_state

        final[var] = {
            "state": new_aggregate,
            "previous_state": primary_state,
            "changed": new_aggregate != primary_state,
            "contributing_personas": primary_personas,
        }

    return final


def _build_trace(
    replan_check: dict,
    persona: dict,
    replan_response: dict,
    final_coverage: dict,
    primary_participants: list[str],
) -> dict:
    pid = persona["persona_id"]
    meta = persona["metadata"]

    resolved_vars = [v for v, d in final_coverage.items() if d["changed"]]
    still_unresolved = [
        v for v in replan_check["unresolved_variables"]
        if not final_coverage.get(v, {}).get("changed", False)
    ]

    return {
        "study_id": "WL-2026-Q2-MM",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine_label": "autonomous_replan_trigger",
        "honest_label": (
            "Autonomous re-plan triggered by unresolved coverage gap in "
            "primary sessions. Reserve participant added from fixture data "
            "using deterministic replay. This demonstrates the re-plan "
            "mechanism, not live participant recruitment."
        ),
        "primary_sessions": {
            "participants": primary_participants,
            "coverage_check": replan_check,
        },
        "replan_decision": {
            "triggered": True,
            "trigger_variable": replan_check["unresolved_variables"],
            "rationale": (
                f"After {len(primary_participants)} primary sessions, "
                f"{', '.join(replan_check['unresolved_variables'])} remained "
                f"ambiguous/unresolved. The coverage loop identified "
                f"{pid} ({meta['role']}, segment: {meta['segment']}) as a "
                f"reserve participant scoped to "
                f"{', '.join(meta.get('replan_scope_variables', []))}. "
                f"Adding exactly one targeted session to resolve the gap."
            ),
            "reserve_participant": {
                "participant_id": pid,
                "role": meta["role"],
                "segment": meta["segment"],
                "replan_scope_variables": meta.get("replan_scope_variables", []),
            },
            "added_before_trigger": False,
            "added_count": 1,
        },
        "replan_session": {
            "participant_id": pid,
            "response": replan_response,
            "transcript_turns": len(persona.get("transcript", [])),
        },
        "final_coverage": final_coverage,
        "resolution_summary": {
            "resolved_variables": resolved_vars,
            "still_unresolved": still_unresolved,
            "procurement_friction_final": final_coverage.get("procurement_friction", {}).get("state"),
            "all_target_variables_resolved": len(still_unresolved) == 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WP8: Autonomous Re-Plan Trigger",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help=f"Output trace (default: {DEFAULT_OUTPUT.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()
    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    coverage = _load_json(WP5_COVERAGE)
    primary_participants = coverage.get("participants_processed", [])

    replan_check = _check_replan_signal(coverage)

    if not replan_check["triggered"]:
        trace = {
            "study_id": "WL-2026-Q2-MM",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "engine_label": "autonomous_replan_trigger",
            "replan_decision": {"triggered": False},
            "reason": "No unresolved variables — all coverage gaps resolved in primary sessions.",
        }
        output_path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
        print("OK: WP8 re-plan trigger — no re-plan needed")
        print(f"    trace written to: {output_path}")
        return 0

    persona = _find_reserve_persona(replan_check["unresolved_variables"])
    if persona is None:
        print(f"ERROR: No reserve persona found for {replan_check['unresolved_variables']}")
        return 1

    replan_response = _replay_persona_session(persona)
    final_coverage = _compute_final_coverage(coverage, replan_response)

    trace = _build_trace(
        replan_check, persona, replan_response,
        final_coverage, primary_participants,
    )

    output_path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")

    rs = trace["resolution_summary"]
    rd = trace["replan_decision"]
    print("OK: WP8 autonomous re-plan trigger complete")
    print(f"    primary sessions: {len(primary_participants)}")
    print(f"    trigger: {', '.join(replan_check['unresolved_variables'])} unresolved")
    print(f"    reserve added: {rd['reserve_participant']['participant_id']} ({rd['reserve_participant']['role']})")
    print(f"    resolved: {', '.join(rs['resolved_variables'])}")
    print(f"    procurement_friction final: {rs['procurement_friction_final']}")
    print(f"    all targets resolved: {rs['all_target_variables_resolved']}")
    print(f"    trace written to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
