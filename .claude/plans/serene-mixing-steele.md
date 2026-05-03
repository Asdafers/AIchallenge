# WP5: Participant Conversation Engine + Coverage Loop

## Context

WP3 proved the organizer flow, WP4 proved methodology pushback. WP5 proves spec Beats 3-4: interactive participant conversations with MCP triangulation and stop condition / coverage tracking. This is `demo_must_show[3]` ("interactive participant conversations") and contributes to `demo_must_show[4]` ("measurable data quality improvement").

The prototype is **deterministic** — conversations follow pre-written persona fixture transcripts, not live LLM. Structured field extraction uses fixture ground truth. Honestly labeled throughout.

## Approach: Hybrid Pipeline with Fixture Oracle

The engine processes each persona's transcript through a full pipeline (question → probe → tool call → extract → coverage check → stop condition → guardrail), emitting conversation events that demonstrate the interactive flow. The structured_fields come from the persona's `expected_response` (ground truth oracle). The value is demonstrating the **pipeline and coverage loop**, not NLP extraction accuracy.

## Files

| Action | Path | Purpose |
|--------|------|---------|
| Create | `scripts/wp5_conversation_engine.py` | Main script |
| Create | `fixtures/wp5_participant_responses.json` | 3 participant response records (P-001, P-002, P-003) |
| Create | `fixtures/wp5_coverage_summary.json` | Aggregate coverage, replan signal, baseline comparison, conversation events |

## Data Flow

```
Persona fixtures (P-001/P-002/P-003) ─┐
CRM fixtures ──────────────────────────┤  Per-persona pipeline:
Telemetry fixtures ────────────────────┤    1. Replay transcript turns
WP4 question pool ─────────────────────┘    2. Match turns to approved questions
                                            3. Simulate MCP tool calls
                                            4. Emit field extractions (from fixture oracle)
                                            5. Detect guardrail triggers
                                            6. Track coverage state per variable
                                            7. Evaluate stop conditions
                                            8. Output: response record + conversation events
                                                          │
Static baseline fixtures ──────────────────┐              │
                                           ├── Aggregate coverage + baseline comparison
                                           │   → wp5_coverage_summary.json
                                           │
                                           └── wp5_participant_responses.json
```

## Key Functions

```
_load_json(path)                       — standard fixture loader
_event(index, event_type, persona, payload)  — timestamped event (WP3 pattern)
_simulate_tool_call(persona_id, tool_call, crm, telemetry)  — replay MCP from fixtures
_map_turn_to_question(text, pool)      — substring match to WP4 question pool
_derive_stop_conditions(coverage_state) — annotate which vars hit threshold
_aggregate_state(persona_states)        — reimpl of validate_fixtures.py rule
process_persona(persona_id, data, pool, crm, telemetry) → (response, events, guardrails)
build_coverage_summary(responses, events, guardrails, baselines) → summary dict
main()                                 — argparse, load, process, validate, write
```

## Per-Persona Expected Outcomes

| Persona | Segment | Key Signal | Guardrails | procurement_friction |
|---------|---------|------------|------------|---------------------|
| P-001 | lost_deal_economic_buyer | unclear_roi + budget_timing | 0 | covered_low_confidence |
| P-002 | lost_deal_champion | competitor_pressure, vague procurement | 1 (mark_ambiguous) | **ambiguous** |
| P-003 | slipping_deal_champion | unclear_roi + economic_buyer_gap | 0 | **ambiguous** |

Aggregate after 3 sessions: 7/8 variables `covered_high_confidence`, procurement_friction = `ambiguous` (replan trigger). P-005 NOT processed (WP6).

## Coverage Summary Structure

- `per_variable_aggregate`: 8 variables, each with state + per-persona contributions
- `replan_signal`: `{triggered: true, unresolved: ["procurement_friction"], recommended: "Add P-005"}`
- `quality_summary`: methodic vs static metrics side-by-side
- `baseline_comparison`: per-participant deltas (methodic coverage ~0.875-1.0 vs static ~0-0.125)
- `processing_events`: per-persona event arrays showing the conversation pipeline

## Conversation Events (per persona)

1. `conversation_started` — persona metadata, transcript length
2. `question_asked` — for each methodic turn, with matched question_id from WP4 pool
3. `participant_response` — for each participant turn
4. `tool_call_executed` — for each system/tool_call turn, with fixture context source
5. `field_extracted` — one per evidence entry, with extraction_source: fixture_ground_truth
6. `guardrail_triggered` — P-002 only: vague answer → mark_ambiguous
7. `coverage_check` — after extractions, per-variable state breakdown
8. `stop_condition_met` — for variables at covered_high_confidence
9. `conversation_complete` — final status + metrics

## MCP Simulation

System turns with `tool_call` are matched against loaded CRM/telemetry fixture files. The tool_call_executed event carries the fixture's `output_summary` and labels itself as "Deterministic replay — MCP tool call simulated from fixture data."

## Guardrail Detection

Uses `expected_guardrail_events` from persona fixtures (ground truth). P-002 emits exactly 1 event: `participant_vague_answer` for `procurement_friction` at T-002-07 with action `mark_ambiguous`.

## Static Baseline Comparison

Loads `fixtures/static_baseline/P-001.json`, P-002, P-003. Computes per-participant variable_coverage delta and study-level aggregate comparison. Expected result: Methodic 7/8 high-confidence vs Static 0/8.

## Verification

Regression (must all pass):
```bash
python3 scripts/validate_schemas.py docs/schema
python3 scripts/validate_fixtures.py
python3 scripts/wp3_organizer_flow.py > /dev/null
python3 scripts/wp4_methodology_review.py --mode fallback > /dev/null
```

WP5-specific (inline in script):
- Each response record validates against participant-response.schema.json
- structured_fields match fixture expected_response exactly
- coverage_state match fixture expected_response exactly
- P-002 has exactly 1 guardrail event matching fixture
- Aggregate procurement_friction == "ambiguous"
- P-005 does not appear in any output

## Out of Scope

- P-005 processing (WP6 re-plan)
- Live LLM conversation
- Live MCP transport
- BigQuery export, Cloud Run
- Frontend/UI
