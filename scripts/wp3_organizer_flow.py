#!/usr/bin/env python3
"""WP3 External Request and Organizer Flow — A2A-pattern prototype (HTTP/stub).

This is NOT a production A2A implementation. It is an honestly labeled prototype
that demonstrates the external-request → clarification → organizer-brief →
approval flow using deterministic fixture data.

Mission strategy linkage (mission_strategy['aichallenge']):
- demo_must_show[1] "External Agent Request beat": this script proves a
  mocked Sales Insights agent can send a structured request, receive a
  clarification question, respond, and trigger an organizer brief.
- thesis "no useful insights without good data": the organizer brief maps the
  business decision to 7 canonical research variables before any participant
  conversation starts.

Usage:
    python scripts/wp3_organizer_flow.py
    python scripts/wp3_organizer_flow.py --output fixtures/wp3_event_log.json

Exits 0 on success. Prints the ordered event log as JSON to stdout (or writes
to --output). Each event carries a sequential index, timestamp, event_type,
state, and payload.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
REQUEST_FIXTURE = REPO_ROOT / "fixtures" / "request_study.json"
CLARIFICATION_FIXTURE = REPO_ROOT / "fixtures" / "clarification_response.json"

STATES = [
    "awaiting_clarification",
    "clarified",
    "brief_drafted",
    "approved",
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _event(index: int, event_type: str, state: str, payload: dict) -> dict:
    return {
        "index": index,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "state": state,
        "payload": payload,
    }


def _build_organizer_brief(request: dict, clarification: dict) -> dict:
    """Build the organizer brief from request + clarification fixtures.

    The 7 required_variables come from spec.md § Organizer Agent output.
    secondary_loss_reason is intentionally absent — it is a participant-response
    field derived during conversations, not a study-level variable.
    """
    selected = None
    rationale = None
    for turn in clarification.get("turns", []):
        if turn.get("type") == "clarification_response":
            selected = turn.get("selected_option")
            rationale = turn.get("rationale")
            break

    bctx = request.get("business_context", {})
    decision = request["decision"]
    if selected == "both":
        decision = "Adjust packaging and ROI messaging for mid-market enterprise deals"
    elif selected == "packaging":
        decision = "Adjust mid-market enterprise packaging"
    elif selected == "roi_messaging":
        decision = "Adjust mid-market enterprise ROI messaging"

    return {
        "study_id": request["study_id"],
        "decision": decision,
        "audience": request["target_segments"],
        "required_variables": [
            "primary_loss_reason",
            "roi_clarity",
            "budget_timing",
            "procurement_friction",
            "security_concern",
            "competitor_pressure",
            "aha_moment_reached",
        ],
        "constraints": {
            "deadline": request["deadline"],
            "no_sensitive_customer_data_in_demo": True,
        },
        "business_context": {
            "quarter": bctx.get("quarter"),
            "pipeline_at_risk_usd": bctx.get("pipeline_at_risk_usd"),
            "suspected_reasons": bctx.get("suspected_reasons", []),
        },
        "clarification_outcome": {
            "selected_option": selected,
            "rationale": rationale,
        },
    }


def run_organizer_flow(
    request_path: Path = REQUEST_FIXTURE,
    clarification_path: Path = CLARIFICATION_FIXTURE,
) -> list[dict]:
    """Execute the full organizer flow and return the ordered event log."""
    events: list[dict] = []
    idx = 0

    request = _load_json(request_path)
    events.append(_event(
        idx, "external_request_received", "awaiting_clarification",
        {"study_id": request["study_id"], "requesting_agent": request["requesting_agent"],
         "decision": request["decision"], "deadline": request["deadline"]},
    ))
    idx += 1

    clarification = _load_json(clarification_path)
    clarification_turn = None
    response_turn = None
    for turn in clarification.get("turns", []):
        if turn.get("type") == "clarification_request":
            clarification_turn = turn
        elif turn.get("type") == "clarification_response":
            response_turn = turn

    if clarification_turn:
        events.append(_event(
            idx, "clarification_request_sent", "awaiting_clarification",
            {"from": clarification_turn["from"], "to": clarification_turn["to"],
             "question": clarification_turn["question"],
             "options": clarification_turn["options"]},
        ))
        idx += 1

    if response_turn:
        events.append(_event(
            idx, "clarification_response_received", "clarified",
            {"from": response_turn["from"], "to": response_turn["to"],
             "selected_option": response_turn["selected_option"],
             "rationale": response_turn["rationale"]},
        ))
        idx += 1

    brief = _build_organizer_brief(request, clarification)
    events.append(_event(
        idx, "organizer_brief_drafted", "brief_drafted",
        {"brief": brief},
    ))
    idx += 1

    events.append(_event(
        idx, "brief_approved", "approved",
        {"study_id": brief["study_id"],
         "approval": "auto_approved_prototype",
         "note": "A2A-pattern prototype — auto-approved for demo flow"},
    ))
    idx += 1

    return events


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WP3: External Request and Organizer Flow (A2A-pattern prototype)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Write event log to file instead of stdout",
    )
    args = parser.parse_args()

    events = run_organizer_flow()

    output = json.dumps(events, indent=2)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"OK: {len(events)} events written to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
