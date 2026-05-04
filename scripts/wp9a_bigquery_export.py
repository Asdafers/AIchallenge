#!/usr/bin/env python3
"""WP9a BigQuery Export Setup — proves the BigQuery write path before
Cloud Run deployment day.

Validates WP7 sample rows against the BigQuery schema, attempts a live
write if google-cloud-bigquery is installed and credentials are available,
and falls back to an honest dry-run otherwise.  Records the exact mode,
validation results, and operator next-steps in a trace artifact.

Usage:
    python3 scripts/wp9a_bigquery_export.py                  # auto-detect mode
    python3 scripts/wp9a_bigquery_export.py --dry-run        # force dry-run
    python3 scripts/wp9a_bigquery_export.py --output out.json # custom output

Environment variables for live mode:
    GOOGLE_CLOUD_PROJECT       — GCP project ID
    BIGQUERY_DATASET           — dataset name (default: methodic)
    BIGQUERY_TABLE             — table name (default: quality_scores)
    GOOGLE_APPLICATION_CREDENTIALS — path to service-account key JSON

Exits 0 on success (including honest dry-run).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WP7_BQ_SCHEMA = REPO_ROOT / "fixtures" / "wp7_bigquery_schema.json"
DEFAULT_OUTPUT = REPO_ROOT / "fixtures" / "wp9a_bigquery_export_trace.json"

TYPE_MAP = {
    "STRING": str,
    "FLOAT64": (int, float),
    "TIMESTAMP": str,
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_rows(schema_fields: list[dict], rows: list[dict]) -> list[dict]:
    """Validate each sample row against the BigQuery schema definition.

    Returns a list of per-row validation results with field-level detail.
    """
    results: list[dict] = []
    field_specs = {f["name"]: f for f in schema_fields}

    for i, row in enumerate(rows):
        field_results: list[dict] = []
        row_ok = True

        for name, spec in field_specs.items():
            value = row.get(name)
            mode = spec.get("mode", "NULLABLE")
            bq_type = spec["type"]
            expected_types = TYPE_MAP.get(bq_type)

            errors: list[str] = []

            if value is None:
                if mode == "REQUIRED":
                    errors.append(f"REQUIRED field is null/missing")
                    row_ok = False
            elif expected_types is not None:
                if not isinstance(value, expected_types):
                    errors.append(
                        f"expected {bq_type} (Python {expected_types}), "
                        f"got {type(value).__name__}: {value!r}"
                    )
                    row_ok = False

            field_results.append({
                "field": name,
                "value_type": type(value).__name__ if value is not None else "null",
                "bq_type": bq_type,
                "mode": mode,
                "valid": len(errors) == 0,
                "errors": errors if errors else None,
            })

        extra_fields = sorted(set(row.keys()) - set(field_specs.keys()))
        results.append({
            "row_index": i,
            "participant_id": row.get("participant_id"),
            "source_type": row.get("source_type"),
            "valid": row_ok and len(extra_fields) == 0,
            "field_count": len(field_specs),
            "fields_checked": len(field_results),
            "extra_fields": extra_fields if extra_fields else None,
            "field_detail": field_results,
        })

    return results


def _generate_ddl(table_id: str, schema_fields: list[dict]) -> str:
    """Generate a BigQuery SQL DDL statement from schema fields."""
    lines = []
    for f in schema_fields:
        col = f["name"]
        bq_type = f["type"]
        mode = f.get("mode", "NULLABLE")
        not_null = " NOT NULL" if mode == "REQUIRED" else ""
        lines.append(f"  {col} {bq_type}{not_null}")
    cols = ",\n".join(lines)
    return f"CREATE TABLE IF NOT EXISTS `{{project}}.{{dataset}}.{table_id}` (\n{cols}\n);"


def _detect_mode(force_dry_run: bool) -> dict:
    """Detect whether live BigQuery write is possible."""
    if force_dry_run:
        return {"mode": "dry_run_forced", "reason": "--dry-run flag set by operator"}

    try:
        from google.cloud import bigquery as _bq  # noqa: F401
    except ImportError:
        return {
            "mode": "dry_run_no_sdk",
            "reason": "google-cloud-bigquery not installed (pip install google-cloud-bigquery)",
        }

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        return {
            "mode": "dry_run_no_credentials",
            "reason": "GOOGLE_CLOUD_PROJECT not set",
        }

    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project)
        _ = client.project
        return {
            "mode": "live",
            "reason": "BigQuery SDK installed and client authenticated",
            "client": client,
            "project": project,
        }
    except Exception as e:
        return {
            "mode": "dry_run_auth_failed",
            "reason": f"BigQuery client creation failed: {e}",
        }


def _attempt_live_write(
    client: Any,
    project: str,
    dataset_name: str,
    table_name: str,
    schema_fields: list[dict],
    rows: list[dict],
) -> dict:
    """Attempt to write rows to a real BigQuery table."""
    from google.cloud import bigquery

    dataset_ref = f"{project}.{dataset_name}"
    table_ref = f"{dataset_ref}.{table_name}"

    try:
        client.get_dataset(dataset_ref)
        dataset_created = False
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset, exists_ok=True)
        dataset_created = True

    bq_schema = []
    for f in schema_fields:
        bq_schema.append(bigquery.SchemaField(
            f["name"], f["type"], mode=f.get("mode", "NULLABLE"),
        ))

    table = bigquery.Table(table_ref, schema=bq_schema)
    table = client.create_table(table, exists_ok=True)

    errors = client.insert_rows_json(table_ref, rows)

    if errors:
        return {
            "success": False,
            "dataset_created": dataset_created,
            "table_ref": table_ref,
            "rows_attempted": len(rows),
            "insert_errors": errors,
        }

    query = f"SELECT COUNT(*) as cnt FROM `{table_ref}`"
    result = list(client.query(query).result())
    row_count = result[0]["cnt"] if result else 0

    return {
        "success": True,
        "dataset_created": dataset_created,
        "table_ref": table_ref,
        "rows_attempted": len(rows),
        "rows_written": len(rows),
        "verification_query": query,
        "verification_row_count": row_count,
    }


def _operator_steps() -> dict:
    """Return concrete operator steps for live BigQuery setup."""
    return {
        "description": (
            "Steps to enable live BigQuery export from Cloud Run or local."
        ),
        "prerequisites": [
            "A GCP project with BigQuery API enabled",
            "gcloud CLI authenticated (gcloud auth login)",
        ],
        "environment_variables": {
            "GOOGLE_CLOUD_PROJECT": {
                "description": "GCP project ID for BigQuery",
                "example": "my-project-id",
                "required": True,
            },
            "BIGQUERY_DATASET": {
                "description": "BigQuery dataset name",
                "default": "methodic",
                "required": False,
            },
            "BIGQUERY_TABLE": {
                "description": "BigQuery table name",
                "default": "quality_scores",
                "required": False,
            },
            "GOOGLE_APPLICATION_CREDENTIALS": {
                "description": "Path to service-account JSON key file",
                "example": "/path/to/service-account.json",
                "required_for": "Cloud Run / non-interactive environments",
            },
        },
        "iam_roles": {
            "service_account_roles": [
                {
                    "role": "roles/bigquery.dataEditor",
                    "scope": "dataset",
                    "reason": "Insert rows into the quality_scores table",
                },
                {
                    "role": "roles/bigquery.jobUser",
                    "scope": "project",
                    "reason": "Run verification queries after insert",
                },
            ],
            "gcloud_commands": [
                (
                    "gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT "
                    "--member=serviceAccount:$SA_EMAIL "
                    "--role=roles/bigquery.dataEditor"
                ),
                (
                    "gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT "
                    "--member=serviceAccount:$SA_EMAIL "
                    "--role=roles/bigquery.jobUser"
                ),
            ],
        },
        "install_sdk": "pip install google-cloud-bigquery",
        "run_live": (
            "GOOGLE_CLOUD_PROJECT=my-proj python3 scripts/wp9a_bigquery_export.py"
        ),
        "run_dry": "python3 scripts/wp9a_bigquery_export.py --dry-run",
    }


def _build_trace(
    mode_info: dict,
    bq_schema: dict,
    validation_results: list[dict],
    ddl: str,
    live_result: dict | None,
) -> dict:
    mode = mode_info["mode"]
    all_valid = all(r["valid"] for r in validation_results)

    honest_labels = {
        "dry_run_no_sdk": (
            "Dry-run mode: google-cloud-bigquery SDK is not installed. "
            "Schema validation passed against WP7 sample rows. "
            "No rows were written to BigQuery. See operator_steps for setup."
        ),
        "dry_run_no_credentials": (
            "Dry-run mode: BigQuery SDK is installed but GOOGLE_CLOUD_PROJECT "
            "is not set. Schema validation passed. No rows were written. "
            "See operator_steps for credential setup."
        ),
        "dry_run_auth_failed": (
            "Dry-run mode: BigQuery SDK is installed but authentication failed. "
            "Schema validation passed. No rows were written. "
            "See operator_steps for credential setup."
        ),
        "dry_run_forced": (
            "Dry-run mode: operator passed --dry-run flag. "
            "Schema validation passed. No rows were written."
        ),
        "live": (
            "Live mode: rows were written to a real BigQuery table "
            "and verified with a COUNT(*) query."
            if live_result and live_result.get("success")
            else "Live mode attempted but write failed. See live_result for errors."
        ),
    }

    return {
        "study_id": "WL-2026-Q2-MM",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine_label": "bigquery_export_setup",
        "honest_label": honest_labels.get(mode, f"Unknown mode: {mode}"),
        "mode": mode,
        "mode_reason": mode_info["reason"],
        "schema": {
            "table_id": bq_schema["table_id"],
            "field_count": len(bq_schema["schema"]["fields"]),
            "fields": [f["name"] for f in bq_schema["schema"]["fields"]],
            "ddl": ddl,
        },
        "row_validation": {
            "rows_checked": len(validation_results),
            "all_valid": all_valid,
            "per_row": validation_results,
        },
        "live_result": live_result,
        "operator_steps": _operator_steps(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WP9a: BigQuery Export Setup — validate and optionally write",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Force dry-run mode even if credentials are available",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help=f"Output trace (default: {DEFAULT_OUTPUT.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()
    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    bq_schema = _load_json(WP7_BQ_SCHEMA)
    schema_fields = bq_schema["schema"]["fields"]
    sample_rows = bq_schema["sample_rows"]

    validation_results = _validate_rows(schema_fields, sample_rows)
    all_valid = all(r["valid"] for r in validation_results)

    if not all_valid:
        print("ERROR: Schema validation failed — sample rows do not match BigQuery schema")
        for r in validation_results:
            if not r["valid"]:
                print(f"  row {r['row_index']} ({r['participant_id']}/{r['source_type']}): INVALID")
                for fd in r["field_detail"]:
                    if not fd["valid"]:
                        print(f"    {fd['field']}: {fd['errors']}")
        return 1

    ddl = _generate_ddl(bq_schema["table_id"], schema_fields)
    mode_info = _detect_mode(args.dry_run)
    live_result = None

    if mode_info["mode"] == "live":
        dataset_name = os.environ.get("BIGQUERY_DATASET", "methodic")
        table_name = os.environ.get("BIGQUERY_TABLE", "quality_scores")
        live_result = _attempt_live_write(
            mode_info["client"], mode_info["project"],
            dataset_name, table_name,
            schema_fields, sample_rows,
        )

    trace = _build_trace(mode_info, bq_schema, validation_results, ddl, live_result)
    output_path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")

    print(f"OK: WP9a BigQuery export setup complete")
    print(f"    mode: {mode_info['mode']}")
    print(f"    reason: {mode_info['reason']}")
    print(f"    schema fields: {len(schema_fields)}")
    print(f"    rows validated: {len(validation_results)}")
    print(f"    all rows valid: {all_valid}")
    print(f"    DDL generated: {len(ddl)} chars")
    if live_result:
        print(f"    live write success: {live_result.get('success')}")
        if live_result.get("success"):
            print(f"    table: {live_result['table_ref']}")
            print(f"    rows written: {live_result['rows_written']}")
            print(f"    verification count: {live_result['verification_row_count']}")
    print(f"    trace written to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
