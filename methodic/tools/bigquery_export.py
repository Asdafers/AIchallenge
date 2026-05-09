"""BigQuery export - flattens ParticipantResponse to BQ rows.

Supports dry_run mode for local testing. In live mode, ensures
dataset and table exist before inserting.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from methodic.schemas import ParticipantResponse, CANONICAL_FIELDS

DATASET = os.environ.get("BIGQUERY_DATASET", "methodic_demo")
TABLE_NAME = f"{DATASET}.win_loss_responses"


def _flatten_response(response: ParticipantResponse) -> dict[str, Any]:
    row: dict[str, Any] = {
        "participant_id": response.participant_id,
        "study_id": response.study_id,
        "segment": response.segment,
        "persona_summary": response.persona_summary,
        "conversation_status": response.conversation_status,
    }
    for field in CANONICAL_FIELDS:
        row[field] = getattr(response.structured_fields, field)
    for field in CANONICAL_FIELDS:
        if field == "secondary_loss_reason":
            continue
        row[f"conf_{field}"] = response.field_confidence.get(field)
    for field in CANONICAL_FIELDS:
        if field == "secondary_loss_reason":
            continue
        row[f"cov_{field}"] = response.coverage_state.get(field)
    row["quality_variable_coverage"] = response.quality.variable_coverage
    row["quality_ambiguity_resolved"] = response.quality.ambiguity_resolved
    row["quality_evidence_linked"] = response.quality.evidence_linked
    row["quality_requires_recontact"] = response.quality.requires_recontact
    row["evidence_json"] = json.dumps([e.model_dump() for e in response.evidence])
    row["unresolved_ambiguities_json"] = json.dumps(response.unresolved_ambiguities)
    row["exported_at"] = datetime.now(timezone.utc).isoformat()
    return row


def _ensure_bigquery_table(project: str, dataset: str) -> None:
    from google.cloud import bigquery
    from pathlib import Path

    client = bigquery.Client(project=project)
    dataset_ref = bigquery.DatasetReference(project, dataset)
    try:
        client.get_dataset(dataset_ref)
    except Exception:
        ds = bigquery.Dataset(dataset_ref)
        ds.location = "US"
        client.create_dataset(ds, exists_ok=True)

    table_ref = dataset_ref.table("win_loss_responses")
    try:
        client.get_table(table_ref)
    except Exception:
        sql_path = Path(__file__).resolve().parent.parent.parent / "docs" / "schema" / "bigquery-table.sql"
        if sql_path.exists():
            client.query(sql_path.read_text()).result()


def export_to_bigquery(
    responses: list[ParticipantResponse],
    dry_run: bool | None = None,
    fail_on_error: bool = False,
) -> dict[str, Any]:
    if dry_run is None:
        dry_run = os.environ.get("BIGQUERY_DRY_RUN", "true").lower() == "true"

    rows = [_flatten_response(r) for r in responses]

    if dry_run:
        return {
            "rows_written": len(rows), "table_name": TABLE_NAME,
            "dataset": DATASET, "dry_run": True, "rows": rows,
        }

    from google.cloud import bigquery
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    _ensure_bigquery_table(project, DATASET)

    client = bigquery.Client(project=project)
    table_ref = client.dataset(DATASET).table("win_loss_responses")
    errors = client.insert_rows_json(table_ref, rows)

    if errors and fail_on_error:
        raise RuntimeError(f"BigQuery insert errors: {errors}")

    return {
        "rows_written": len(rows) if not errors else 0,
        "table_name": TABLE_NAME, "dataset": DATASET,
        "dry_run": False, "errors": errors if errors else None,
    }
