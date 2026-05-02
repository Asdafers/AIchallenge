#!/usr/bin/env python3
"""WP1 schema validator for the Methodic AI Agent Challenge.

Mission strategy linkage (mission_strategy['aichallenge']):
- thesis "no useful insights without good data": this validator enforces a
  single canonical record shape so the static-vs-Methodic data-quality delta
  is computable from the same fields on both paths.
- demo_must_show "measurable data quality improvement vs. static-survey
  baseline": Examples A (static) and B (Methodic) share one schema so the
  rubric scores both uniformly.
- non_goals "over-claiming statistical rigor": the validator checks shape
  and field coverage only; it makes no statistical-significance claims.
- stack_alignment "BigQuery": Example D is checked against the BigQuery DDL
  in docs/schema/bigquery-table.sql so WP9a inherits a verified contract.

Usage:
    python scripts/validate_schemas.py docs/schema/

Exits 0 on success. Exits non-zero with a clear message naming the failing
example and field on any mismatch.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, NoReturn

try:
    from jsonschema import Draft7Validator, FormatChecker
except ImportError:  # pragma: no cover - import guard
    print(
        "ERROR: 'jsonschema' is not installed. Run: pip install jsonschema",
        file=sys.stderr,
    )
    sys.exit(2)


_ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})$"
)


_FORMAT_CHECKER = FormatChecker()


def _parse_iso8601(value: Any) -> datetime | None:
    """Return a datetime if value is a valid ISO-8601 string, else None."""
    if not isinstance(value, str):
        return None
    if not _ISO8601_RE.match(value):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _check_iso8601(instance: Any) -> bool:
    """jsonschema format-checker hook: raises on invalid ISO-8601 strings."""
    if not isinstance(instance, str):
        return True  # only constrain strings; non-strings caught by `type`.
    if _parse_iso8601(instance) is None:
        raise ValueError(f"{instance!r} is not a valid ISO-8601 date-time")
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
    instance: Any, schema: dict, example_label: str
) -> None:
    validator = Draft7Validator(schema, format_checker=_FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        path = "/".join(str(p) for p in first.absolute_path) or "<root>"
        _fail(f"{example_label}: schema violation at '{path}': {first.message}")


# ---- BigQuery DDL parsing -------------------------------------------------


_DDL_COLUMN_TYPES = {"STRING", "FLOAT64", "BOOL", "TIMESTAMP"}


def _parse_ddl(ddl_text: str) -> dict[str, dict[str, bool | str]]:
    """Return {column_name: {"type": str, "not_null": bool}}.

    Lightweight regex parser: accepts the CREATE TABLE block and pulls each
    column declaration. Comment lines (--) and blank lines are skipped.
    """
    match = re.search(
        r"CREATE\s+TABLE[^(]*\((?P<body>.*?)\)\s*;", ddl_text, re.DOTALL | re.IGNORECASE
    )
    if not match:
        _fail("BigQuery DDL: could not locate CREATE TABLE (...) block")
    body = match.group("body")

    columns: dict[str, dict[str, bool | str]] = {}
    line_pattern = re.compile(
        r"^\s*(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s+"
        r"(?P<type>[A-Z0-9]+)"
        r"(?P<rest>[^,]*)$"
    )
    for raw_line in body.splitlines():
        line = raw_line.split("--", 1)[0].strip().rstrip(",")
        if not line:
            continue
        m = line_pattern.match(line)
        if not m:
            continue
        col_type = m.group("type").upper()
        if col_type not in _DDL_COLUMN_TYPES:
            continue
        not_null = "NOT NULL" in m.group("rest").upper()
        columns[m.group("name")] = {"type": col_type, "not_null": not_null}
    if not columns:
        _fail("BigQuery DDL: no recognizable columns parsed")
    return columns


def _value_matches_type(value: Any, bq_type: str) -> bool:
    if value is None:
        return True  # NOT NULL handled separately
    if bq_type == "STRING":
        return isinstance(value, str)
    if bq_type == "FLOAT64":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if bq_type == "BOOL":
        return isinstance(value, bool)
    if bq_type == "TIMESTAMP":
        return _parse_iso8601(value) is not None
    return False


def _validate_bigquery_row(
    row: dict, ddl_columns: dict[str, dict[str, bool | str]], example_label: str
) -> None:
    # Every DDL column must be present (or nullable in DDL and absent/None).
    for col, meta in ddl_columns.items():
        if col not in row:
            if meta["not_null"]:
                _fail(
                    f"{example_label}: missing required DDL column '{col}'"
                )
            # nullable column may be absent
            continue
        value = row[col]
        if value is None and meta["not_null"]:
            _fail(f"{example_label}: column '{col}' is NOT NULL but value is null")
        if not _value_matches_type(value, str(meta["type"])):
            _fail(
                f"{example_label}: column '{col}' value {value!r} not compatible "
                f"with DDL type {meta['type']}"
            )

    # Every key in the example must map to a DDL column.
    for key in row.keys():
        if key not in ddl_columns:
            _fail(
                f"{example_label}: key '{key}' has no matching DDL column"
            )


# ---- Main ------------------------------------------------------------------


def main(argv: Iterable[str]) -> int:
    args = list(argv)
    if len(args) != 1:
        print(
            "Usage: python scripts/validate_schemas.py <schema_dir>",
            file=sys.stderr,
        )
        return 2
    schema_dir = Path(args[0]).resolve()
    if not schema_dir.is_dir():
        _fail(f"schema directory not found: {schema_dir}")

    pr_schema_path = schema_dir / "participant-response.schema.json"
    ge_schema_path = schema_dir / "guardrail-event.schema.json"
    ddl_path = schema_dir / "bigquery-table.sql"
    examples_dir = schema_dir / "examples"
    example_a = examples_dir / "static-baseline.json"
    example_b = examples_dir / "methodic-output.json"
    example_c = examples_dir / "guardrail-event.json"
    example_d = examples_dir / "bigquery-row.json"

    pr_schema = _load_json(pr_schema_path, "participant-response.schema.json")
    ge_schema = _load_json(ge_schema_path, "guardrail-event.schema.json")

    if not ddl_path.exists():
        _fail(f"bigquery-table.sql: file not found at {ddl_path}")
    ddl_text = ddl_path.read_text(encoding="utf-8")
    ddl_columns = _parse_ddl(ddl_text)

    # Schema-level structural checks (ensures the schemas themselves are valid).
    Draft7Validator.check_schema(pr_schema)
    Draft7Validator.check_schema(ge_schema)

    # Example A — static baseline → Participant Response schema
    a = _load_json(example_a, "Example A (static-baseline.json)")
    _validate_against_schema(a, pr_schema, "Example A (static-baseline.json)")

    # Example B — Methodic output → Participant Response schema
    b = _load_json(example_b, "Example B (methodic-output.json)")
    _validate_against_schema(b, pr_schema, "Example B (methodic-output.json)")

    # Extra sanity: Example B must contain all 7 evidence fields per WP1 sign-off.
    required_evidence_fields = {
        "primary_loss_reason",
        "roi_clarity",
        "budget_timing",
        "aha_moment_reached",
        "security_concern",
        "competitor_pressure",
        "procurement_friction",
    }
    fields_seen = {e.get("field") for e in b.get("evidence", []) if isinstance(e, dict)}
    missing = required_evidence_fields - fields_seen
    if missing:
        _fail(
            "Example B (methodic-output.json): evidence array missing required "
            f"field entries: {sorted(missing)}"
        )
    # Procurement_friction entry must have context_used: [] per locked sign-off.
    for entry in b.get("evidence", []):
        if isinstance(entry, dict) and entry.get("field") == "procurement_friction":
            if entry.get("context_used") != []:
                _fail(
                    "Example B (methodic-output.json): evidence entry for "
                    "procurement_friction must have context_used == [] "
                    "(WP2 sign-off resolution #3)"
                )

    # Example C — guardrail event → Guardrail Event schema
    c = _load_json(example_c, "Example C (guardrail-event.json)")
    _validate_against_schema(c, ge_schema, "Example C (guardrail-event.json)")

    # Example D — BigQuery row → DDL contract
    d = _load_json(example_d, "Example D (bigquery-row.json)")
    if not isinstance(d, dict):
        _fail("Example D (bigquery-row.json): top-level value must be a JSON object")
    _validate_bigquery_row(d, ddl_columns, "Example D (bigquery-row.json)")

    # Nested-JSON contract: evidence_json and unresolved_ambiguities_json must
    # round-trip parse and conform to the corresponding participant-response
    # sub-schemas. Without this check, the BQ string columns could drift from
    # the canonical schema (WP9a "BigQuery inherits a verified contract").
    pr_props = pr_schema.get("properties", {})
    evidence_subschema = pr_props.get("evidence")
    if evidence_subschema is not None and "evidence_json" in d:
        try:
            evidence_array = json.loads(d["evidence_json"])
        except json.JSONDecodeError as exc:
            _fail(
                "Example D (bigquery-row.json): evidence_json is not valid JSON: "
                f"{exc}"
            )
        _validate_against_schema(
            evidence_array,
            evidence_subschema,
            "Example D (bigquery-row.json) evidence_json",
        )

    ua_subschema = pr_props.get("unresolved_ambiguities")
    if ua_subschema is not None and "unresolved_ambiguities_json" in d:
        try:
            ua_array = json.loads(d["unresolved_ambiguities_json"])
        except json.JSONDecodeError as exc:
            _fail(
                "Example D (bigquery-row.json): unresolved_ambiguities_json is "
                f"not valid JSON: {exc}"
            )
        _validate_against_schema(
            ua_array,
            ua_subschema,
            "Example D (bigquery-row.json) unresolved_ambiguities_json",
        )

    print("OK: all four examples validate against the canonical schemas + DDL.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
