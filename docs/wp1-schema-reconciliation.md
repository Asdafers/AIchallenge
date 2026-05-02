# WP1 Schema And Quality Rubric — Pre-Implementation Reconciliation Draft

Status: **pre-implementation design**. This document is the planning approval that authorises the WP1 mission task to lock the canonical schema, rubric, and validation tooling. The WP1 subagent should treat the decisions below as binding and execute the file edits and creations listed in the final two sections.

This draft does NOT itself modify `docs/spec.md` or `docs/methodic-vertical-slice.md`; those edits are part of WP1 execution. Reviewers should sign off on the decisions here before WP1 is claimed.

## Mission strategy linkage

- `aichallenge.thesis` — "No useful insights without good data; data capture is the weakest link in the analytics pipeline." Locking schema + rubric is the precondition for measurable data-quality claims; without a single canonical record shape, the static-vs-Methodic delta cannot be computed.
- `aichallenge.demo_must_show.measurable data quality improvement vs. static-survey baseline` — the rubric below scores both paths against the same Participant Response shape (with `conversation_status: "static_form"` enabling shared scoring).
- `aichallenge.non_goals.over-claiming statistical rigor` — rubric measures operational/qualitative quality (variable coverage, ambiguity resolution, evidence linkage). No statistical-significance term is introduced.
- `aichallenge.stack_alignment.MCP/Cloud Run/BigQuery` — BigQuery DDL below pins the export shape so WP9a (BigQuery setup) can proceed deterministically and WP9 (Cloud Run) inherits a verified contract.

## Source of truth

`docs/spec.md > Data Schema > Participant Response` is canonical for participant-level records. Where `docs/methodic-vertical-slice.md > Canonical Data Quality Schema > Minimum output record` disagrees, **spec.md wins**. WP1 must edit vertical-slice to align.

The schema is extended in this reconciliation to add three blocks not formally defined in spec.md but referenced elsewhere:

1. `coverage_state.<variable>` — already required by spec.md Beat 4 and the Metrics section, but missing from the Participant Response example. Promoted to a formal block.
2. Guardrail event type — referenced in spec.md Guardrails section but no structured event shape exists.
3. Per-record `quality` block — vertical-slice introduced new fields (`completion_score`, `ambiguity_count`, `evidence_link_count`). These are KEPT but as **study-level rollup** metrics inside `Data Quality Agent` output, NOT per-record. Per-record `quality` retains the spec.md shape.

## Drift resolution table

| # | Drift | spec.md (canonical) | vertical-slice (must change) | Resolution |
| --- | --- | --- | --- | --- |
| 1 | `evidence[].quote` field name | `quote` | `evidence_quote` | Use `quote`. Edit vertical-slice example. |
| 2 | `evidence[].context_used` field name | `context_used` | `context_refs` | Use `context_used`. Edit vertical-slice example. |
| 3 | `evidence[].transcript_turn_id` | present | absent in vertical-slice example | Add to vertical-slice example. |
| 4 | `coverage_state` block | absent in schema block (only mentioned in Beat 4 / Metrics) | present per-variable | Add formal `coverage_state` map to the canonical Participant Response schema (in BOTH docs). |
| 5 | Per-record `quality` shape | `{variable_coverage, ambiguity_resolved, evidence_linked, requires_recontact}` | `{completion_score, ambiguity_count, evidence_link_count}` | Per-record stays spec.md shape. Vertical-slice fields move to study-level rollup. |
| 6 | `conversation_status` enum | `complete\|partial\|excluded` | (only `complete\|partial\|excluded` implied) | Add `static_form` value so static-baseline records share the schema. |

## Canonical Participant Response (post-WP1)

Both spec.md schema block and vertical-slice example block must be replaced with this exact structure.

```json
{
  "participant_id": "string",
  "study_id": "string",
  "segment": "string",
  "persona_summary": "string",
  "conversation_status": "complete|partial|excluded|static_form",
  "structured_fields": {
    "primary_loss_reason": "unclear_roi|budget_timing|procurement_friction|security_concern|competitor_pressure|missing_feature|economic_buyer_gap|other|unknown",
    "secondary_loss_reason": "string|null",
    "roi_clarity": "clear|partially_clear|unclear|unknown",
    "budget_timing": "in_cycle|out_of_cycle|unknown",
    "procurement_friction": "none|low|medium|high|unknown",
    "security_concern": "none|low|medium|high|unknown",
    "competitor_pressure": "none|named_competitor|unknown",
    "aha_moment_reached": "yes|no|unknown"
  },
  "field_confidence": {
    "<variable_name>": 0.0
  },
  "coverage_state": {
    "<variable_name>": "missing|ambiguous|covered_low_confidence|covered_high_confidence"
  },
  "quality": {
    "variable_coverage": 0.0,
    "ambiguity_resolved": true,
    "evidence_linked": true,
    "requires_recontact": false
  },
  "evidence": [
    {
      "field": "string",
      "quote": "string",
      "transcript_turn_id": "string",
      "context_used": ["string"]
    }
  ],
  "unresolved_ambiguities": ["string"]
}
```

## Coverage state definitions

| State | Definition |
| --- | --- |
| `missing` | No usable evidence captured for this variable. |
| `ambiguous` | Evidence exists but cannot be mapped confidently to one enum value. |
| `covered_low_confidence` | Mapped with weak or single-source evidence (e.g. one quote, no MCP context confirmation). |
| `covered_high_confidence` | Mapped with quote AND context evidence and sufficient specificity. |

These states drive Beat 4 (stop condition) and Beat 5 (re-plan trigger).

## Guardrail event types and shape

Required event types (covering spec.md Guardrails section):

- `participant_misunderstanding` — participant misunderstands the question.
- `participant_contradiction` — participant gives information that contradicts an earlier turn.
- `participant_frustration` — participant signals disengagement or annoyance.
- `participant_vague_answer` — participant gives a one-word or non-decision-relevant answer that probing cannot resolve.

Canonical event shape:

```json
{
  "event_id": "string",
  "study_id": "string",
  "participant_id": "string",
  "event_type": "participant_misunderstanding|participant_contradiction|participant_frustration|participant_vague_answer",
  "trigger": {
    "transcript_turn_id": "string",
    "trigger_text": "string"
  },
  "action_taken": "rephrase_once|clarifying_followup|mark_ambiguous|graceful_end",
  "measurement_intent_preserved": true,
  "variable_affected": "string|null",
  "timestamp": "string"
}
```

Distinct from `Tool Event` in spec.md, which logs MCP tool calls only. Both event streams co-exist in the developer overlay.

## Quality scoring rubric

### Per-record (Participant Response `quality` block)

- `quality.variable_coverage` = (count of required variables with `coverage_state ∈ {covered_low_confidence, covered_high_confidence}`) / (count of required variables for the study).
- `quality.ambiguity_resolved` = `true` iff no required variable has `coverage_state == ambiguous`.
- `quality.evidence_linked` = `true` iff at least one variable has `coverage_state == covered_high_confidence` AND every such variable has at least one entry in `evidence[]` mapping to it. (`covered_low_confidence` variables may be supported by context-only or inferred-from-absence reasoning and do not require a quote. The "at least one" clause makes the field meaningfully `false` for static-form records with no resolved variables.)
- `quality.requires_recontact` = `true` iff any required variable has `coverage_state == missing`.

### Study-level rollup (Data Quality Agent `quality_summary`)

Already defined in spec.md, retained:

- `variable_coverage_rate` — mean of per-record `variable_coverage` across non-excluded records.
- `ambiguity_resolution_rate` — fraction of records with `ambiguity_resolved == true`.
- `evidence_coverage_rate` — fraction of records with `evidence_linked == true`.
- `mean_field_confidence` — mean across all populated `field_confidence` values.

WP1 additions to study rollup:

- `vague_answer_rate` — static-survey only; fraction of static records with at least one variable in `coverage_state == ambiguous` rooted in a vague-text answer.
- `missing_variable_rate` — fraction of (record, required-variable) pairs with `coverage_state == missing`.
- `replan_event_count` — count of autonomous re-plans triggered for the study (expected: 1).

## Static-form baseline schema

Static-form participants produce a Participant Response with `conversation_status: "static_form"`. Static questions map to canonical variables; unmapped questions are recorded only in raw form and surfaced as `requires_recontact == true`.

| Static question | Canonical variable mapped | Typical captured state |
| --- | --- | --- |
| 1. What was the main reason you did not move forward? | `primary_loss_reason` | Vague free-text → `coverage_state: ambiguous` |
| 2. How would you rate the product value? | (no canonical map) | Discarded; record `quality.requires_recontact = true` |
| 3. Was pricing a concern? | `budget_timing` (weak proxy) | yes/no → `coverage_state: covered_low_confidence` value `unknown` |
| 4. What could we improve? | `secondary_loss_reason` (weak) | Free text; usually discarded |

The static path is a thin UI/path using the same fixture personas (per spec.md "Prototype commitment"). It populates the schema with the same shape so the rubric scores both paths uniformly.

## BigQuery table schema

Table: `methodic_demo.win_loss_responses` (matches spec.md export-target reference).

Shape decision: **flat columns** for `structured_fields`, `coverage_state`, and `field_confidence` (SQL-friendly, easy joins, easy aggregation). **JSON STRING** for the nested `evidence` array and `unresolved_ambiguities` (variable-length, demo doesn't query into them).

DDL:

```sql
CREATE TABLE IF NOT EXISTS `methodic_demo.win_loss_responses` (
  participant_id STRING NOT NULL,
  study_id STRING NOT NULL,
  segment STRING,
  persona_summary STRING,
  conversation_status STRING NOT NULL,

  -- structured_fields (flat)
  primary_loss_reason STRING,
  secondary_loss_reason STRING,
  roi_clarity STRING,
  budget_timing STRING,
  procurement_friction STRING,
  security_concern STRING,
  competitor_pressure STRING,
  aha_moment_reached STRING,

  -- field_confidence (flat, FLOAT64, prefix conf_)
  conf_primary_loss_reason FLOAT64,
  conf_roi_clarity FLOAT64,
  conf_budget_timing FLOAT64,
  conf_procurement_friction FLOAT64,
  conf_security_concern FLOAT64,
  conf_competitor_pressure FLOAT64,
  conf_aha_moment_reached FLOAT64,

  -- coverage_state (flat, STRING, prefix cov_)
  cov_primary_loss_reason STRING,
  cov_roi_clarity STRING,
  cov_budget_timing STRING,
  cov_procurement_friction STRING,
  cov_security_concern STRING,
  cov_competitor_pressure STRING,
  cov_aha_moment_reached STRING,

  -- per-record quality
  quality_variable_coverage FLOAT64,
  quality_ambiguity_resolved BOOL,
  quality_evidence_linked BOOL,
  quality_requires_recontact BOOL,

  -- nested as JSON STRING
  evidence_json STRING,
  unresolved_ambiguities_json STRING,

  exported_at TIMESTAMP NOT NULL
);
```

Rationale for flat over RECORD: judges look at SELECT statements in the developer overlay; flat columns are more readable. RECORD type would preserve nesting symmetry with the JSON shape but obscure the demo "structured table" claim.

## Worked examples

### Example A — static-form baseline (P-001 via static path)

```json
{
  "participant_id": "P-001",
  "study_id": "WL-2026-Q2-MM",
  "segment": "lost_deal_economic_buyer",
  "persona_summary": "VP Finance at lost mid-market deal",
  "conversation_status": "static_form",
  "structured_fields": {
    "primary_loss_reason": "unknown",
    "secondary_loss_reason": null,
    "roi_clarity": "unknown",
    "budget_timing": "unknown",
    "procurement_friction": "unknown",
    "security_concern": "unknown",
    "competitor_pressure": "unknown",
    "aha_moment_reached": "unknown"
  },
  "field_confidence": {
    "primary_loss_reason": 0.2
  },
  "coverage_state": {
    "primary_loss_reason": "ambiguous",
    "secondary_loss_reason": "missing",
    "roi_clarity": "missing",
    "budget_timing": "covered_low_confidence",
    "procurement_friction": "missing",
    "security_concern": "missing",
    "competitor_pressure": "missing",
    "aha_moment_reached": "missing"
  },
  "quality": {
    "variable_coverage": 0.125,
    "ambiguity_resolved": false,
    "evidence_linked": false,
    "requires_recontact": true
  },
  "evidence": [
    {
      "field": "primary_loss_reason",
      "quote": "Price was too high.",
      "transcript_turn_id": "STATIC-P-001-Q1",
      "context_used": []
    }
  ],
  "unresolved_ambiguities": ["primary_loss_reason"]
}
```

### Example B — Methodic output (P-001 via Methodic path)

```json
{
  "participant_id": "P-001",
  "study_id": "WL-2026-Q2-MM",
  "segment": "lost_deal_economic_buyer",
  "persona_summary": "VP Finance at lost mid-market deal",
  "conversation_status": "complete",
  "structured_fields": {
    "primary_loss_reason": "unclear_roi",
    "secondary_loss_reason": "budget_timing",
    "roi_clarity": "unclear",
    "budget_timing": "out_of_cycle",
    "procurement_friction": "unknown",
    "security_concern": "none",
    "competitor_pressure": "none",
    "aha_moment_reached": "no"
  },
  "field_confidence": {
    "primary_loss_reason": 0.86,
    "secondary_loss_reason": 0.55,
    "roi_clarity": 0.82,
    "budget_timing": 0.78,
    "procurement_friction": 0.55,
    "security_concern": 0.8,
    "competitor_pressure": 0.8,
    "aha_moment_reached": 0.9
  },
  "coverage_state": {
    "primary_loss_reason": "covered_high_confidence",
    "secondary_loss_reason": "covered_low_confidence",
    "roi_clarity": "covered_high_confidence",
    "budget_timing": "covered_high_confidence",
    "procurement_friction": "covered_low_confidence",
    "security_concern": "covered_high_confidence",
    "competitor_pressure": "covered_high_confidence",
    "aha_moment_reached": "covered_high_confidence"
  },
  "quality": {
    "variable_coverage": 1.0,
    "ambiguity_resolved": true,
    "evidence_linked": true,
    "requires_recontact": false
  },
  "evidence": [
    {
      "field": "primary_loss_reason",
      "quote": "Finance never saw proof. We never got to the report output.",
      "transcript_turn_id": "T-001-07",
      "context_used": ["lookup_deal_context.trial_usage.report_builder_reached"]
    },
    {
      "field": "roi_clarity",
      "quote": "Finance never saw proof. We never got to the report output.",
      "transcript_turn_id": "T-001-07",
      "context_used": ["lookup_deal_context.trial_usage.report_builder_reached"]
    },
    {
      "field": "budget_timing",
      "quote": "The quarter had closed by the time we were ready to commit.",
      "transcript_turn_id": "T-001-09",
      "context_used": []
    },
    {
      "field": "aha_moment_reached",
      "quote": "We never got to the report output.",
      "transcript_turn_id": "T-001-07",
      "context_used": ["lookup_deal_context.trial_usage.report_builder_reached"]
    },
    {
      "field": "security_concern",
      "quote": "No security or competitor issues.",
      "transcript_turn_id": "T-001-11",
      "context_used": []
    },
    {
      "field": "competitor_pressure",
      "quote": "No security or competitor issues.",
      "transcript_turn_id": "T-001-11",
      "context_used": []
    },
    {
      "field": "procurement_friction",
      "quote": "No procurement involvement — the deal closed before we got there.",
      "transcript_turn_id": "T-001-11",
      "context_used": []
    }
  ],
  "unresolved_ambiguities": []
}
```

Note on procurement_friction evidence: the entry has `context_used: []` (no MCP corroboration) by design — keeping the state at `covered_low_confidence` per WP2 sign-off resolution #3. Adding an MCP context reference here would promote it to `covered_high_confidence` and break the re-plan trigger.

### Example C — guardrail event (P-002 vague answer)

```json
{
  "event_id": "GE-2026-Q2-MM-001",
  "study_id": "WL-2026-Q2-MM",
  "participant_id": "P-002",
  "event_type": "participant_vague_answer",
  "trigger": {
    "transcript_turn_id": "T-002-07",
    "trigger_text": "Maybe. I'd be guessing — I wasn't in those conversations."
  },
  "action_taken": "mark_ambiguous",
  "measurement_intent_preserved": true,
  "variable_affected": "procurement_friction",
  "timestamp": "2026-05-18T14:22:09Z"
}
```

### Example D — BigQuery row (P-001 Methodic, flattened from Example B)

```json
{
  "participant_id": "P-001",
  "study_id": "WL-2026-Q2-MM",
  "segment": "lost_deal_economic_buyer",
  "persona_summary": "VP Finance at lost mid-market deal",
  "conversation_status": "complete",
  "primary_loss_reason": "unclear_roi",
  "secondary_loss_reason": "budget_timing",
  "roi_clarity": "unclear",
  "budget_timing": "out_of_cycle",
  "procurement_friction": "unknown",
  "security_concern": "none",
  "competitor_pressure": "none",
  "aha_moment_reached": "no",
  "conf_primary_loss_reason": 0.86,
  "conf_roi_clarity": 0.82,
  "conf_budget_timing": 0.78,
  "conf_procurement_friction": 0.55,
  "conf_security_concern": 0.8,
  "conf_competitor_pressure": 0.8,
  "conf_aha_moment_reached": 0.9,
  "cov_primary_loss_reason": "covered_high_confidence",
  "cov_roi_clarity": "covered_high_confidence",
  "cov_budget_timing": "covered_high_confidence",
  "cov_procurement_friction": "covered_low_confidence",
  "cov_security_concern": "covered_high_confidence",
  "cov_competitor_pressure": "covered_high_confidence",
  "cov_aha_moment_reached": "covered_high_confidence",
  "quality_variable_coverage": 1.0,
  "quality_ambiguity_resolved": true,
  "quality_evidence_linked": true,
  "quality_requires_recontact": false,
  "evidence_json": "[{\"field\":\"primary_loss_reason\",\"quote\":\"Finance never saw proof. We never got to the report output.\",\"transcript_turn_id\":\"T-001-07\",\"context_used\":[\"lookup_deal_context.trial_usage.report_builder_reached\"]},{\"field\":\"roi_clarity\",\"quote\":\"Finance never saw proof. We never got to the report output.\",\"transcript_turn_id\":\"T-001-07\",\"context_used\":[\"lookup_deal_context.trial_usage.report_builder_reached\"]},{\"field\":\"budget_timing\",\"quote\":\"The quarter had closed by the time we were ready to commit.\",\"transcript_turn_id\":\"T-001-09\",\"context_used\":[]},{\"field\":\"aha_moment_reached\",\"quote\":\"We never got to the report output.\",\"transcript_turn_id\":\"T-001-07\",\"context_used\":[\"lookup_deal_context.trial_usage.report_builder_reached\"]},{\"field\":\"security_concern\",\"quote\":\"No security or competitor issues.\",\"transcript_turn_id\":\"T-001-11\",\"context_used\":[]},{\"field\":\"competitor_pressure\",\"quote\":\"No security or competitor issues.\",\"transcript_turn_id\":\"T-001-11\",\"context_used\":[]},{\"field\":\"procurement_friction\",\"quote\":\"No procurement involvement — the deal closed before we got there.\",\"transcript_turn_id\":\"T-001-11\",\"context_used\":[]}]",
  "unresolved_ambiguities_json": "[]",
  "exported_at": "2026-05-30T18:00:00Z"
}
```

Note: P-001 contributes `procurement_friction == unknown` because the deal closed before the procurement stage. Coverage is `covered_low_confidence` (single-source — inferred from absence of procurement involvement, no MCP corroboration). This combines under WP2's aggregate rule with P-002/P-003's `ambiguous` contributions to give a study-level `procurement_friction == ambiguous`, firing the re-plan trigger. WP2 fixture matrix expands on this.

## Validation tooling (executable artifact)

WP1 must create `scripts/validate_schemas.py` that:

1. Loads `docs/schema/participant-response.schema.json` and `docs/schema/guardrail-event.schema.json` (JSON Schema draft-07).
2. Validates examples A and B against the Participant Response schema; example C against the Guardrail Event schema.
3. Validates example D against the BigQuery DDL column set: every column in DDL is present in the example, every example field maps to a DDL column, types are JSON-compatible (STRING→string, FLOAT64→number, BOOL→bool, TIMESTAMP→ISO-8601 string).
4. Exits 0 on success, non-zero on any failure with a line indicating which example and which field broke.

Suggested implementation: Python `jsonschema` for steps 1–2; lightweight DDL parser (regex over `CREATE TABLE` block) for step 3.

Run command: `python scripts/validate_schemas.py docs/schema/`

WP1 acceptance gate: `python scripts/validate_schemas.py docs/schema/` exits 0 against all four examples.

## Files WP1 must create

- `docs/schema/participant-response.schema.json` (JSON Schema draft-07 for Participant Response)
- `docs/schema/guardrail-event.schema.json` (JSON Schema draft-07 for Guardrail Event)
- `docs/schema/bigquery-table.sql` (DDL block above, verbatim)
- `docs/schema/examples/static-baseline.json` (Example A)
- `docs/schema/examples/methodic-output.json` (Example B)
- `docs/schema/examples/guardrail-event.json` (Example C)
- `docs/schema/examples/bigquery-row.json` (Example D)
- `scripts/validate_schemas.py` (validator)

## Files WP1 must edit

- `docs/spec.md` — Participant Response schema block: add `coverage_state` map, extend `conversation_status` enum to include `static_form`. No change to `structured_fields` enums or `quality` block.
- `docs/methodic-vertical-slice.md` — replace the `Minimum output record` example block with Example B above. Remove `evidence_quote`/`context_refs`/divergent `quality` keys. Add a one-line note pointing to spec.md as canonical.

## Out of scope for WP1

- Live validation of agent outputs against the schema (WP5/WP7).
- Persistence layer (file/Firestore decision is in WP7/WP9).
- Re-plan trigger logic (WP8); WP1 only defines the coverage-state taxonomy that WP8 reads.
