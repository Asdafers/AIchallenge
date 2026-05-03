#!/usr/bin/env python3
"""WP4 Methodology Pushback & Question Design — live Gemini + deterministic fallback.

Proves Beat 2 from spec.md: given a biased champion-only sample plan, the
Methodology Agent pushes back with concrete revision and the Question Design
Agent produces an 8-question pool mapped to the canonical structured_fields.

Usage:
    python scripts/wp4_methodology_review.py                     # live Gemini call
    python scripts/wp4_methodology_review.py --mode fallback     # deterministic only
    python scripts/wp4_methodology_review.py --output out.json   # custom output path

Output: fixtures/wp4_methodology_package.json (default).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
REQUEST_FIXTURE = REPO_ROOT / "fixtures" / "request_study.json"
BIASED_PLAN_FIXTURE = REPO_ROOT / "fixtures" / "sample_plan_biased.json"
EVENT_LOG_FIXTURE = REPO_ROOT / "fixtures" / "wp3_event_log.json"
ACP_DRIVER = REPO_ROOT / "scripts" / "gemini_acp_driver.py"
DEFAULT_OUTPUT = REPO_ROOT / "fixtures" / "wp4_methodology_package.json"

CANONICAL_VARIABLES = [
    "primary_loss_reason",
    "secondary_loss_reason",
    "roi_clarity",
    "budget_timing",
    "procurement_friction",
    "security_concern",
    "competitor_pressure",
    "aha_moment_reached",
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_brief(event_log: list[dict]) -> dict:
    for ev in event_log:
        if ev.get("event_type") == "organizer_brief_drafted":
            return ev["payload"]["brief"]
    raise ValueError("No organizer_brief_drafted event in event log")


# ---------------------------------------------------------------------------
# Deterministic fallback
# ---------------------------------------------------------------------------

def _deterministic_methodology_review(
    biased_plan: dict, brief: dict,
) -> dict:
    """Rule-based methodology critique matching spec § Beat 2."""
    pushbacks = []
    segments = biased_plan.get("sample_plan", {}).get("segments", [])
    segment_names = [s["segment"] for s in segments]

    has_economic_buyer = any("economic_buyer" in s for s in segment_names)
    has_lost_deal = any("lost_deal" in s for s in segment_names)
    all_champions = all("champion" in s for s in segment_names)
    total = biased_plan.get("sample_plan", {}).get("total_participants", 0)

    if all_champions and not has_economic_buyer:
        pushbacks.append({
            "type": "sample_mismatch",
            "severity": "high",
            "message": (
                "Champions alone cannot support a pricing or packaging decision. "
                "Economic buyers decide budget and procurement. Include economic "
                "buyers from lost and slipping deals, plus a smaller control group "
                "of recent wins."
            ),
        })

    if total < 5:
        pushbacks.append({
            "type": "sample_mismatch",
            "severity": "medium",
            "message": (
                f"Total participants ({total}) is below the minimum for "
                "decision-grade qualitative evidence. Recommend at least 5–8 "
                "across segments."
            ),
        })

    if not has_lost_deal:
        pushbacks.append({
            "type": "sample_mismatch",
            "severity": "high",
            "message": (
                "No lost-deal participants in sample. Win-loss studies require "
                "loss-side perspectives to surface root causes."
            ),
        })

    decision = brief.get("decision", "")
    decision_lower = decision.lower()
    if ("packaging" in decision_lower or "roi" in decision_lower) and not has_economic_buyer:
        pushbacks.append({
            "type": "overclaim_risk",
            "severity": "high",
            "message": (
                f"Decision '{decision}' involves pricing/packaging, but no "
                "economic buyer segment is included. Do not claim "
                "representativeness from champion-only data."
            ),
        })

    status = "requires_revision" if pushbacks else "approved"
    return {
        "status": status,
        "pushbacks": pushbacks,
        "allowed_claims": [
            "directional qualitative evidence",
            "decision-critical variable coverage",
            "ambiguity reduction",
        ],
        "disallowed_claims": [
            "statistically representative",
            "causal",
        ],
    }


def _deterministic_sample_revision(biased_plan: dict) -> dict:
    """Generate a corrected sample plan referencing locked fixture/persona segments."""
    return {
        "study_id": biased_plan.get("sample_plan", {}).get(
            "study_id", biased_plan.get("study_id", "WL-2026-Q2-MM")
        ),
        "description": (
            "Revised sample: economic-buyer, champion, procurement, and "
            "recent-win contrast coverage for the win-loss decision"
        ),
        "segments": [
            {
                "segment": "lost_deal_economic_buyer",
                "role": "VP Finance / Budget Owner",
                "count": 2,
                "rationale": (
                    "Economic buyers decide budget and procurement — essential "
                    "for packaging/ROI decisions"
                ),
            },
            {
                "segment": "lost_deal_champion",
                "role": "RevOps / Product Champion",
                "count": 2,
                "rationale": (
                    "Champions provide context on internal advocacy failure "
                    "and product-market fit signals"
                ),
            },
            {
                "segment": "slipping_deal_champion",
                "role": "Sales Operations Lead",
                "count": 1,
                "rationale": (
                    "Slipping-deal champions expose executive-sponsor and "
                    "ROI-proof gaps before the deal is fully lost"
                ),
            },
            {
                "segment": "slipping_deal_procurement",
                "role": "Procurement Lead",
                "count": 1,
                "rationale": (
                    "Procurement stakeholders test packaging and vendor-"
                    "consolidation friction directly, supporting the reserve "
                    "re-plan path"
                ),
            },
            {
                "segment": "recent_win_economic_buyer",
                "role": "COO / Economic Buyer (contrast)",
                "count": 1,
                "rationale": (
                    "Control group from recent wins to contrast loss-side "
                    "findings and identify what made ROI proof credible"
                ),
            },
        ],
        "total_participants": 7,
        "bias_note": (
            "Original champion-only plan revised per methodology pushback. "
            "Mixed segments provide decision-grade qualitative evidence without "
            "claiming statistical representativeness."
        ),
    }


def _deterministic_question_pool() -> list[dict]:
    """8 questions, one per canonical structured_field variable."""
    return [
        {
            "question_id": "Q-loss-reason-open",
            "prompt": (
                "What changed between initial interest and the decision "
                "not to move forward?"
            ),
            "maps_to": ["primary_loss_reason"],
            "follow_up_policy": "clarify_vague_reason",
            "risk_flags": [],
        },
        {
            "question_id": "Q-secondary-loss",
            "prompt": (
                "Beyond the primary factor, was there a secondary issue "
                "that contributed to the outcome?"
            ),
            "maps_to": ["secondary_loss_reason"],
            "follow_up_policy": "probe_if_vague",
            "risk_flags": [],
        },
        {
            "question_id": "Q-roi-clarity",
            "prompt": (
                "What evidence would your team have needed to feel "
                "confident in the ROI?"
            ),
            "maps_to": ["roi_clarity"],
            "follow_up_policy": "probe_missing_evidence",
            "risk_flags": [],
        },
        {
            "question_id": "Q-budget-timing",
            "prompt": (
                "Was budget timing or fiscal-cycle alignment a factor "
                "in the decision?"
            ),
            "maps_to": ["budget_timing"],
            "follow_up_policy": "confirm_or_deny",
            "risk_flags": ["leading_if_unprompted"],
        },
        {
            "question_id": "Q-procurement-friction",
            "prompt": (
                "Walk me through the procurement process — where, if "
                "anywhere, did it slow down or create friction?"
            ),
            "maps_to": ["procurement_friction"],
            "follow_up_policy": "probe_specific_stage",
            "risk_flags": [],
        },
        {
            "question_id": "Q-security-concern",
            "prompt": (
                "Did security review or compliance requirements affect "
                "the timeline or outcome?"
            ),
            "maps_to": ["security_concern"],
            "follow_up_policy": "confirm_or_deny",
            "risk_flags": [],
        },
        {
            "question_id": "Q-competitor-pressure",
            "prompt": (
                "Were you evaluating alternatives or did a competitor "
                "offer influence the decision?"
            ),
            "maps_to": ["competitor_pressure"],
            "follow_up_policy": "identify_named_competitor",
            "risk_flags": [],
        },
        {
            "question_id": "Q-aha-moment",
            "prompt": (
                "Was there a moment during the evaluation where the "
                "core value clicked — or did that never happen?"
            ),
            "maps_to": ["aha_moment_reached"],
            "follow_up_policy": "probe_trial_experience",
            "risk_flags": ["double_barreled_risk"],
        },
    ]


# ---------------------------------------------------------------------------
# Live Gemini path
# ---------------------------------------------------------------------------

_GEMINI_PROMPT_TEMPLATE = """You are a research methodology reviewer for a B2B SaaS win-loss study.

STUDY BRIEF:
{brief_json}

BIASED SAMPLE PLAN (submitted by organizer):
{biased_plan_json}

TASK: Review this sample plan for methodological soundness. The study decision is about packaging and ROI messaging for mid-market enterprise deals.

You must evaluate:
1. Whether the sample can answer the stated decision
2. Sample bias (segment coverage, role diversity)
3. Claim boundaries (what can and cannot be claimed from this sample)

Output ONLY a JSON object with this exact structure (no markdown, no explanation, no commentary):
{{
  "methodology_review": {{
    "status": "requires_revision" or "approved",
    "pushbacks": [
      {{
        "type": "sample_mismatch" or "overclaim_risk" or "leading_question" or "cognitive_overload",
        "severity": "high" or "medium" or "low",
        "message": "specific critique with concrete revision"
      }}
    ],
    "allowed_claims": ["list of valid claim types"],
    "disallowed_claims": ["list of invalid claim types"]
  }},
  "sample_revision": {{
    "description": "revised plan description",
    "segments": [
      {{
        "segment": "segment_id",
        "role": "role title",
        "count": number,
        "rationale": "why this segment is needed"
      }}
    ],
    "total_participants": number,
    "bias_note": "what changed and why"
  }}
}}"""


def _try_live_gemini(brief: dict, biased_plan: dict) -> tuple[dict | None, dict]:
    """Attempt live Gemini call via ACP driver. Returns (parsed_result, metadata)."""
    metadata: dict[str, Any] = {
        "attempted": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if not ACP_DRIVER.exists():
        metadata["error"] = "gemini_acp_driver.py not found"
        metadata["success"] = False
        return None, metadata

    prompt = _GEMINI_PROMPT_TEMPLATE.format(
        brief_json=json.dumps(brief, indent=2),
        biased_plan_json=json.dumps(biased_plan, indent=2),
    )

    try:
        result = subprocess.run(
            [
                sys.executable, str(ACP_DRIVER),
                "--cwd", str(REPO_ROOT),
                "--prompt", prompt,
                "--timeout", "120",
            ],
            capture_output=True, text=True, timeout=150,
        )
        metadata["exit_code"] = result.returncode
        metadata["stderr_length"] = len(result.stderr)

        if result.returncode != 0:
            metadata["error"] = f"driver exited {result.returncode}"
            metadata["success"] = False
            return None, metadata

        driver_output = json.loads(result.stdout)
        metadata["driver_ok"] = driver_output.get("ok", False)

        if not driver_output.get("ok"):
            metadata["error"] = "driver reported failure"
            metadata["success"] = False
            return None, metadata

        response_text = driver_output.get("response_text", "")
        metadata["response_length"] = len(response_text)

        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        parsed = json.loads(cleaned)
        metadata["success"] = True
        metadata["stop_reason"] = driver_output.get("stop_reason")
        return parsed, metadata

    except subprocess.TimeoutExpired:
        metadata["error"] = "subprocess timeout"
        metadata["success"] = False
        return None, metadata
    except json.JSONDecodeError as e:
        metadata["error"] = f"JSON parse error: {e}"
        metadata["success"] = False
        return None, metadata
    except Exception as e:
        metadata["error"] = str(e)
        metadata["success"] = False
        return None, metadata


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def build_methodology_package(mode: str = "live") -> dict:
    """Build the full WP4 methodology package."""
    request = _load_json(REQUEST_FIXTURE)
    biased_plan = _load_json(BIASED_PLAN_FIXTURE)
    event_log = _load_json(EVENT_LOG_FIXTURE)
    brief = _extract_brief(event_log)

    source = "deterministic_fallback"
    live_metadata: dict[str, Any] = {"attempted": False}
    live_review = None
    live_revision = None

    if mode == "live":
        live_result, live_metadata = _try_live_gemini(brief, biased_plan)
        if live_result:
            live_review = live_result.get("methodology_review")
            live_revision = live_result.get("sample_revision")
            if live_review and live_revision:
                source = "live_gemini"

    if source == "deterministic_fallback":
        methodology_review = _deterministic_methodology_review(
            biased_plan, brief,
        )
        sample_revision = _deterministic_sample_revision(biased_plan)
    else:
        methodology_review = live_review
        sample_revision = live_revision

    question_pool = _deterministic_question_pool()

    return {
        "study_id": request["study_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology_review_source": source,
        "question_pool_source": "deterministic",
        "mode_requested": mode,
        "live_call_metadata": live_metadata,
        "inputs": {
            "request_fixture": str(REQUEST_FIXTURE.relative_to(REPO_ROOT)),
            "biased_plan_fixture": str(BIASED_PLAN_FIXTURE.relative_to(REPO_ROOT)),
            "organizer_brief_source": str(EVENT_LOG_FIXTURE.relative_to(REPO_ROOT)),
        },
        "biased_sample_plan": biased_plan["sample_plan"],
        "methodology_review": methodology_review,
        "sample_revision": sample_revision,
        "question_pool": question_pool,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WP4: Methodology Pushback & Question Design (live Gemini + fallback)",
    )
    parser.add_argument(
        "--mode", choices=["live", "fallback"], default="live",
        help="live = attempt Gemini ACP call first; fallback = deterministic only",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Write output to file (default: fixtures/wp4_methodology_package.json)",
    )
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    package = build_methodology_package(mode=args.mode)

    output_text = json.dumps(package, indent=2) + "\n"
    output_path.write_text(output_text, encoding="utf-8")
    print(f"OK: WP4 methodology package written to {output_path}")
    print(f"    source: {package['methodology_review_source']}")
    print(f"    pushbacks: {len(package['methodology_review'].get('pushbacks', []))}")
    print(f"    questions: {len(package['question_pool'])}")
    print(f"    revised participants: {package['sample_revision'].get('total_participants', '?')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
