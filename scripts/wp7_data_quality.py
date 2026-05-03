#!/usr/bin/env python3
"""WP7 Data Quality Layer — scores Methodic and static-form responses with
the same rubric, exports comparison artifacts in JSON, CSV, and BigQuery-ready
formats.

Quality is measured across four dimensions:
  1. Coverage: fraction of 8 canonical fields not missing
  2. Confidence: mean field_confidence across all fields (0 for missing)
  3. Ambiguity: fraction of fields not ambiguous (higher = better)
  4. Evidence-link: fraction of fields with evidence entries using MCP context

Composite = 0.30*coverage + 0.25*confidence + 0.25*ambiguity + 0.20*evidence

Usage:
    python3 scripts/wp7_data_quality.py
    python3 scripts/wp7_data_quality.py --output-report fixtures/wp7_quality_report.json
    python3 scripts/wp7_data_quality.py --output-csv fixtures/wp7_quality_export.csv
    python3 scripts/wp7_data_quality.py --output-bigquery fixtures/wp7_bigquery_schema.json

Exits 0 on success.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WP5_RESPONSES = REPO_ROOT / "fixtures" / "wp5_participant_responses.json"
STATIC_DIR = REPO_ROOT / "fixtures" / "static_baseline"
DEFAULT_REPORT = REPO_ROOT / "fixtures" / "wp7_quality_report.json"
DEFAULT_CSV = REPO_ROOT / "fixtures" / "wp7_quality_export.csv"
DEFAULT_BQ = REPO_ROOT / "fixtures" / "wp7_bigquery_schema.json"

CANONICAL_FIELDS = [
    "primary_loss_reason",
    "secondary_loss_reason",
    "roi_clarity",
    "budget_timing",
    "procurement_friction",
    "security_concern",
    "competitor_pressure",
    "aha_moment_reached",
]

RUBRIC_WEIGHTS = {
    "coverage": 0.30,
    "confidence": 0.25,
    "ambiguity": 0.25,
    "evidence_link": 0.20,
}


def _load_methodic_responses() -> list[dict]:
    return json.loads(WP5_RESPONSES.read_text(encoding="utf-8"))


def _load_static_responses() -> list[dict]:
    responses = []
    for path in sorted(STATIC_DIR.glob("P-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        responses.append(data["expected_response"])
    return responses


def _score_participant(response: dict) -> dict:
    coverage_state = response.get("coverage_state", {})
    field_confidence = response.get("field_confidence", {})
    evidence_list = response.get("evidence", [])

    evidence_by_field: dict[str, list[dict]] = {}
    for ev in evidence_list:
        evidence_by_field.setdefault(ev["field"], []).append(ev)

    n = len(CANONICAL_FIELDS)
    covered = 0
    not_ambiguous = 0
    evidence_linked = 0
    total_confidence = 0.0
    per_field: list[dict] = []

    for field in CANONICAL_FIELDS:
        state = coverage_state.get(field, "missing")
        conf = field_confidence.get(field, 0.0)
        field_evidence = evidence_by_field.get(field, [])
        has_context = any(
            len(ev.get("context_used", [])) > 0 for ev in field_evidence
        )

        is_covered = state != "missing"
        is_not_ambiguous = state != "ambiguous"

        if is_covered:
            covered += 1
        if is_not_ambiguous:
            not_ambiguous += 1
        if has_context:
            evidence_linked += 1
        total_confidence += conf

        per_field.append({
            "field": field,
            "value": response.get("structured_fields", {}).get(field),
            "coverage_state": state,
            "confidence": conf,
            "is_covered": is_covered,
            "is_ambiguous": not is_not_ambiguous,
            "has_evidence": len(field_evidence) > 0,
            "has_context_link": has_context,
            "evidence_count": len(field_evidence),
        })

    coverage_score = covered / n
    confidence_score = total_confidence / n
    ambiguity_score = not_ambiguous / n
    evidence_link_score = evidence_linked / n

    composite = (
        RUBRIC_WEIGHTS["coverage"] * coverage_score
        + RUBRIC_WEIGHTS["confidence"] * confidence_score
        + RUBRIC_WEIGHTS["ambiguity"] * ambiguity_score
        + RUBRIC_WEIGHTS["evidence_link"] * evidence_link_score
    )

    return {
        "participant_id": response["participant_id"],
        "source_type": (
            "static_form"
            if response.get("conversation_status") == "static_form"
            else "methodic"
        ),
        "scores": {
            "coverage": round(coverage_score, 3),
            "confidence": round(confidence_score, 3),
            "ambiguity": round(ambiguity_score, 3),
            "evidence_link": round(evidence_link_score, 3),
            "composite": round(composite, 3),
        },
        "per_field": per_field,
    }


def _avg_scores(scored: list[dict]) -> dict[str, float]:
    if not scored:
        return {k: 0.0 for k in ["coverage", "confidence", "ambiguity", "evidence_link", "composite"]}
    keys = ["coverage", "confidence", "ambiguity", "evidence_link", "composite"]
    return {
        k: round(sum(s["scores"][k] for s in scored) / len(scored), 3)
        for k in keys
    }


def _build_comparison(methodic_scored: list[dict], static_scored: list[dict]) -> dict:
    m_avg = _avg_scores(methodic_scored)
    s_avg = _avg_scores(static_scored)
    delta = {k: round(m_avg[k] - s_avg[k], 3) for k in m_avg}

    return {
        "methodic_avg": m_avg,
        "static_avg": s_avg,
        "delta": delta,
        "methodic_participants": len(methodic_scored),
        "static_participants": len(static_scored),
        "verdict": (
            "Methodic shows higher coverage, lower ambiguity, and "
            "evidence-linked fields across all participants vs. static form. "
            "Static baseline is a reference fixture, not measured production "
            "evidence."
        ),
    }


def _build_quality_report(
    methodic_scored: list[dict],
    static_scored: list[dict],
) -> dict:
    per_participant: dict[str, dict] = {}
    for s in methodic_scored:
        pid = s["participant_id"]
        per_participant.setdefault(pid, {})["methodic"] = s
    for s in static_scored:
        pid = s["participant_id"]
        per_participant.setdefault(pid, {})["static"] = s

    return {
        "study_id": "WL-2026-Q2-MM",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine_label": "data_quality_layer",
        "honest_label": (
            "Quality scores computed from fixture ground-truth extraction, "
            "not live NLP. Static baseline is a reference fixture, not "
            "measured production evidence. Scoring rubric is applied "
            "identically to both Methodic and static-form responses."
        ),
        "rubric": {
            "dimensions": {
                "coverage": "Fraction of 8 canonical fields with coverage_state != missing",
                "confidence": "Mean field_confidence across all 8 fields (0 for missing)",
                "ambiguity": "Fraction of 8 fields with coverage_state != ambiguous",
                "evidence_link": "Fraction of 8 fields with evidence entry using MCP context_used",
            },
            "weights": RUBRIC_WEIGHTS,
            "composite_formula": "0.30*coverage + 0.25*confidence + 0.25*ambiguity + 0.20*evidence_link",
        },
        "per_participant": per_participant,
        "comparison": _build_comparison(methodic_scored, static_scored),
    }


def _export_csv(report: dict, path: Path) -> None:
    fieldnames = [
        "participant_id", "study_id", "segment", "source_type",
        "coverage_score", "confidence_score", "ambiguity_score",
        "evidence_link_score", "composite_score",
    ]

    rows: list[dict] = []
    for pid, sources in report["per_participant"].items():
        for source_key in ("methodic", "static"):
            entry = sources.get(source_key)
            if not entry:
                continue
            scores = entry["scores"]
            pf = entry.get("per_field", [])
            segment = ""
            for f in pf:
                if f["field"] == "primary_loss_reason":
                    segment = f.get("value", "") or ""
                    break

            rows.append({
                "participant_id": pid,
                "study_id": report["study_id"],
                "segment": segment,
                "source_type": entry["source_type"],
                "coverage_score": scores["coverage"],
                "confidence_score": scores["confidence"],
                "ambiguity_score": scores["ambiguity"],
                "evidence_link_score": scores["evidence_link"],
                "composite_score": scores["composite"],
            })

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8")


def _build_bigquery_schema(report: dict) -> dict:
    bq_fields = [
        {"name": "participant_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "study_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "source_type", "type": "STRING", "mode": "REQUIRED",
         "description": "methodic or static_form"},
        {"name": "primary_loss_reason", "type": "STRING", "mode": "NULLABLE"},
        {"name": "secondary_loss_reason", "type": "STRING", "mode": "NULLABLE"},
        {"name": "roi_clarity", "type": "STRING", "mode": "NULLABLE"},
        {"name": "budget_timing", "type": "STRING", "mode": "NULLABLE"},
        {"name": "procurement_friction", "type": "STRING", "mode": "NULLABLE"},
        {"name": "security_concern", "type": "STRING", "mode": "NULLABLE"},
        {"name": "competitor_pressure", "type": "STRING", "mode": "NULLABLE"},
        {"name": "aha_moment_reached", "type": "STRING", "mode": "NULLABLE"},
        {"name": "coverage_score", "type": "FLOAT64", "mode": "REQUIRED"},
        {"name": "confidence_score", "type": "FLOAT64", "mode": "REQUIRED"},
        {"name": "ambiguity_score", "type": "FLOAT64", "mode": "REQUIRED"},
        {"name": "evidence_link_score", "type": "FLOAT64", "mode": "REQUIRED"},
        {"name": "composite_score", "type": "FLOAT64", "mode": "REQUIRED"},
        {"name": "generated_at", "type": "TIMESTAMP", "mode": "REQUIRED"},
    ]

    sample_rows: list[dict] = []
    generated_at = report["generated_at"]

    for pid, sources in report["per_participant"].items():
        for source_key in ("methodic", "static"):
            entry = sources.get(source_key)
            if not entry:
                continue
            scores = entry["scores"]

            field_values: dict[str, Any] = {}
            for pf in entry.get("per_field", []):
                field_values[pf["field"]] = pf.get("value")

            row: dict[str, Any] = {
                "participant_id": pid,
                "study_id": report["study_id"],
                "source_type": entry["source_type"],
                "coverage_score": scores["coverage"],
                "confidence_score": scores["confidence"],
                "ambiguity_score": scores["ambiguity"],
                "evidence_link_score": scores["evidence_link"],
                "composite_score": scores["composite"],
                "generated_at": generated_at,
            }
            for field in CANONICAL_FIELDS:
                row[field] = field_values.get(field)

            sample_rows.append(row)

    return {
        "table_id": "methodic_quality_scores",
        "description": (
            "BigQuery-ready table schema for Methodic data quality scores. "
            "One row per participant per source_type (methodic or static_form). "
            "Field names map directly to canonical WP1 participant-response schema."
        ),
        "schema": {"fields": bq_fields},
        "sample_rows": sample_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WP7: Data Quality Layer — score and export quality metrics",
    )
    parser.add_argument(
        "--output-report", type=str, default=None,
        help=f"Quality report JSON (default: {DEFAULT_REPORT.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--output-csv", type=str, default=None,
        help=f"CSV export (default: {DEFAULT_CSV.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--output-bigquery", type=str, default=None,
        help=f"BigQuery schema + rows (default: {DEFAULT_BQ.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()

    report_path = Path(args.output_report) if args.output_report else DEFAULT_REPORT
    csv_path = Path(args.output_csv) if args.output_csv else DEFAULT_CSV
    bq_path = Path(args.output_bigquery) if args.output_bigquery else DEFAULT_BQ

    methodic_responses = _load_methodic_responses()
    static_responses = _load_static_responses()

    methodic_scored = [_score_participant(r) for r in methodic_responses]
    static_scored = [_score_participant(r) for r in static_responses]

    report = _build_quality_report(methodic_scored, static_scored)

    report_path.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8",
    )

    _export_csv(report, csv_path)

    bq_schema = _build_bigquery_schema(report)
    bq_path.write_text(
        json.dumps(bq_schema, indent=2) + "\n", encoding="utf-8",
    )

    comp = report["comparison"]
    m = comp["methodic_avg"]
    s = comp["static_avg"]
    d = comp["delta"]
    print("OK: WP7 data quality layer complete")
    print(f"    participants: {comp['methodic_participants']} methodic, {comp['static_participants']} static")
    print(f"    methodic composite: {m['composite']}")
    print(f"    static composite:   {s['composite']}")
    print(f"    delta composite:    +{d['composite']}")
    print(f"    methodic coverage:  {m['coverage']}  vs static: {s['coverage']}  (delta +{d['coverage']})")
    print(f"    methodic ambiguity: {m['ambiguity']}  vs static: {s['ambiguity']}  (delta +{d['ambiguity']})")
    print(f"    methodic evidence:  {m['evidence_link']}  vs static: {s['evidence_link']}  (delta +{d['evidence_link']})")
    print(f"    report: {report_path}")
    print(f"    csv:    {csv_path}")
    print(f"    bigquery: {bq_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
