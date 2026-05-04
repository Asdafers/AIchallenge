# Rehearsal Checklist: Proof Beats → Evidence

Use this table to verify that every required proof beat is visible in the demo, traceable to a file, and grounded in a real execution artifact.

## B1-B9 Evidence Map

| Beat | Proof | Script / File | Fixture / Trace Evidence | Demo Moment |
|------|-------|---------------|--------------------------|-------------|
| B1 | External agent request | `scripts/wp3_organizer_flow.py` | `fixtures/request_study.json` (structured payload), `fixtures/clarification_response.json` (clarifying question), `fixtures/wp3_event_log.json` (5-event sequence: request → clarification → response → brief → approval) | Scene 1: Sales Insights agent sends `request_study`; Methodic asks "Packaging or ROI?" before accepting |
| B2 | Organizer planning + methodology pushback | `scripts/wp4_methodology_review.py` | `fixtures/sample_plan_biased.json` (champion-only bias), `fixtures/wp4_methodology_package.json` (4 pushbacks, 8 questions, 7 revised participants, sample-bias correction visible) | Scene 2: Methodology Agent says "Champions alone cannot answer pricing questions. Adding economic buyers." |
| B3 | Interactive participant capture | `scripts/wp5_conversation_engine.py` | `fixtures/wp5_participant_responses.json` (3 participant transcripts with structured extraction), `fixtures/wp5_coverage_summary.json` (variable coverage states) | Scene 3: Participant says "price was too high" → Methodic clarifies into decision-relevant variables |
| B4 | MCP triangulation | `scripts/wp6_mcp_server.py`, `scripts/wp6_mcp_boundary.py` | `fixtures/wp6_mcp_trace.json` (3 real MCP calls via stdio JSON-RPC 2.0, `filtering_verified: true`, `participant_path_integrated: true`) | Scene 3: Developer Overlay shows `lookup_deal_context` MCP call, CRM+telemetry merge, field filtering |
| B5 | Stop condition + coverage loop | `scripts/wp5_conversation_engine.py`, `scripts/wp7_data_quality.py` | `fixtures/wp5_coverage_summary.json` (variable states: missing/ambiguous/covered), `fixtures/wp7_quality_report.json` (per-participant coverage scores) | Scene 4: Quality dashboard shows variable coverage states transitioning |
| B6 | Autonomous re-plan | `scripts/wp8_replan_trigger.py` | `fixtures/wp8_replan_trace.json` (`procurement_friction` unresolved → P-005 Procurement Lead added → resolved) | Scene 4: `procurement_friction: AMBIGUOUS` triggers one extra session; dashboard updates to resolved |
| B7 | Measurable quality delta | `scripts/wp7_data_quality.py` | `fixtures/wp7_quality_report.json` (methodic composite: 0.761 vs static: 0.069, delta: +0.692), `fixtures/wp7_quality_export.csv`, `fixtures/wp7_bigquery_schema.json` | Scene 5: Side-by-side quality comparison, same rubric applied to both |
| B8 | Google-aligned deployability | `scripts/wp9_demo_server.py`, `scripts/wp9_deployment_smoke.py`, `Dockerfile` | `fixtures/wp9_deployment_trace.json` (7/7 steps pass in `local_container` mode, operator_steps for Cloud Run deploy), `fixtures/wp9a_bigquery_export_trace.json` (BigQuery schema + dry-run validation) | Scene 5: Export to BigQuery, Cloud Run deployment instructions in trace, Docker container proof |
| B9 | Guardrail recovery | `scripts/wp5_conversation_engine.py` | `fixtures/wp5_participant_responses.json` (guardrail events: contradiction handling for P-001, frustration handling for P-003, logged without forcing category change) | Scene 3: Quick callout in trace log showing guardrail event handled + logged |

## Verification Commands

Run these before recording to confirm all artifacts are current:

```bash
# Schema and fixture validation
python3 scripts/validate_schemas.py docs/schema
python3 scripts/validate_fixtures.py

# Full pipeline (generates all traces)
python3 scripts/wp3_organizer_flow.py --output /tmp/wp3_check.json
python3 scripts/wp4_methodology_review.py --mode fallback --output /tmp/wp4_check.json
python3 scripts/wp5_conversation_engine.py --output-responses /tmp/wp5r_check.json --output-coverage /tmp/wp5c_check.json
python3 scripts/wp6_mcp_boundary.py --output /tmp/wp6_check.json
python3 scripts/wp7_data_quality.py --output-report /tmp/wp7_check.json --output-csv /tmp/wp7_check.csv --output-bigquery /tmp/wp7bq_check.json
python3 scripts/wp8_replan_trigger.py --output /tmp/wp8_check.json
python3 scripts/wp9a_bigquery_export.py --dry-run --output /tmp/wp9a_check.json

# Container smoke test (requires Docker)
python3 scripts/wp9_deployment_smoke.py --output /tmp/wp9_check.json
```

## Pre-Recording Sanity Checks

- [ ] All 8 verification commands exit 0
- [ ] `fixtures/wp9_deployment_trace.json` shows `all_steps_passed: true` and `steps_total: 7`
- [ ] `fixtures/wp7_quality_report.json` shows delta > 0.5
- [ ] `fixtures/wp6_mcp_trace.json` shows 3 calls, all `filtering_verified: true`
- [ ] `fixtures/wp8_replan_trace.json` shows `procurement_friction` resolved
- [ ] Docker image builds without errors (`docker build -t methodic-demo:smoke .`)
- [ ] No uncommitted changes to scripts/ or fixtures/
