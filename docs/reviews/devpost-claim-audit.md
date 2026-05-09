# Devpost Copy Claim Audit

Audited: 2026-05-09 | Source: `docs/devpost-copy.md`

## Claim Table

| # | Claim | Line | Current Truth | Source | Status | Action |
|---|-------|------|---------------|--------|--------|--------|
| 1 | "52 automated tests" | 58 | 133 tests collected: 69 unit/integration + 60 E2E (Playwright) + 4 interactive-E2E | `pytest --collect-only` | STALE | Update to 133 (or break down: 69 unit + 64 E2E) |
| 2 | "43 unit tests…plus 9 Playwright E2E tests" | 58 | 69 non-E2E tests; 60 Playwright E2E tests (10 in `test_demo_ui.py`, 21 in `test_interactive_scenarios.py`, rest in `test_interactive_e2e.py`) | `pytest --collect-only` | STALE | Update counts to match reality |
| 3 | "1 live integration test against Cloud Run (passes in ~275s)" | 58 | `test_live_demo_completes` is marked `@pytest.mark.live` and hits Cloud Run; timestamp unverified | `tests/e2e/test_demo_ui.py:78` | NEEDS_REFRESH | Re-run timed run and update elapsed time |
| 4 | "BigQuery export writes structured data" | 29, 45 | Dry-run only by default (`BIGQUERY_DRY_RUN=true`); live insert only when env var is overridden | `bigquery_export.py:75-84` | OVERCLAIM | Add "in live mode" qualifier, or reframe as "exports rows (dry-run by default in demo)" |
| 5 | "Not a prototype or fixture replay" | 57 | `participant_sim` is an LlmAgent using `gemini-2.5-flash-lite` (not a human); it's real LLM inference, not fixture replay — but participants are simulated, not real users | `participant_sim.py:9-14`, `methodic/__init__.py:4` | MISLEADING | Reframe: "real LLM-powered pipeline; participants are Gemini-simulated personas, not human respondents" |
| 6 | "~30% to ~87.5% coverage" | 30, 59 | Fixture benchmark: static baseline aggregates ~8% (0 high-confidence, low-confidence only on 2/8 vars), Methodic achieves 87.5% per `wp5_coverage_summary.json`. "~30%" overstates the static baseline (actual fixture data shows ~12.5% average across 3 participants) | `fixtures/wp5_coverage_summary.json:baseline_comparison` | OVERCLAIM | Fix "~30%" to "~12.5%" or label both values as fixture benchmark averages |
| 7 | "streams 30+ events in real time" | 57 | Live SSE fixture (`sse_live_v6_run.txt`) shows 36 data events; golden fixture shows 22 — actual run-time count varies | `tests/e2e/fixtures/sse_live_v6_run.txt` | PLAUSIBLE | Acceptable if live run consistently exceeds 30; verify with a fresh run |
| 8 | "across 12 agent types" | 57 | Demo graph has 14 named nodes: 7 LlmAgent (`organizer`, `methodology`, `question_design`, `interviewer`, `participant_sim`, `quality_reviewer`, `completion_responder`) + 7 custom BaseAgent/orchestrator steps (`session_init`, `extractor_step`, `turn_checker`, `coverage_step`, `replanner`, `bigquery_export`) + 4 SequentialAgent + 2 LoopAgent. Distinct role types ≈ 14. | `methodic/agent.py` (docstring + code) | INACCURATE | Clarify "12 agent types" is not supported by code count; update to "14 named agents" or justify the 12 figure |
| 9 | "7 LlmAgent nodes…4 custom BaseAgent steps" | 40 | `agent.py` docstring lists 7 LlmAgents and 5 custom BaseAgent steps (`session_init`, `extractor_step`, `turn_checker_step`, `coverage_step`, `replanner` as BaseAgent + `bigquery_export`). Replanner is also a custom BaseAgent, giving 6 total custom steps. | `methodic/agent.py:1-27` | MISMATCH | Recount: 7 LlmAgents, 6 custom BaseAgent steps |
| 10 | "`streaming: false` in agent card" | server.py:55 | Confirmed in deployed agent card at `/.well-known/agent-card.json`; server streams SSE over `/api/demo/{id}/stream` but the A2A capability flag says `false` | `methodic/server.py:55`, live curl | MISMATCH | Fix agent card `capabilities.streaming` to `true`, or add a note that A2A streaming is not yet enabled (SSE is a demo-UI transport, not A2A) |
| 11 | "Cloud Run (us-central1)" | 43 | Live and responding: `curl /health` returns `{"status":"ok"}` | `https://methodic-2030382823.us-central1.run.app/health` | TRUE | Keep |
| 12 | "Gemini 2.5 Pro powers all LLM agents" | 42 | Not all: `participant_sim` uses `gemini-2.5-flash-lite` (`MODEL_FAST`); the other 6 LlmAgents use `gemini-2.5-pro` | `methodic/__init__.py:3-4`, `participant_sim.py:5` | OVERCLAIM | Update to "Gemini 2.5 Pro powers all reasoning agents; participant simulation uses Gemini 2.5 Flash" |
| 13 | "Gemini performed blind adversarial reviews at 10 gates" | 60 | `docs/reviews/` contains 14 files, 5 of which are `gemini-*.md` (gemini-interactive-mode-review, gemini-quality-layer-review, gemini-refinement-plan-review, gemini-research-design-review, gemini-ui-review); Codex also reviewed at 9 gates | `docs/reviews/*.md` (14 files, 5 Gemini) | INACCURATE | Update to "Gemini performed 5 adversarial reviews; Codex performed 9 reviews — 14 total blind reviews across both models" |
| 14 | "21-task implementation plan" | 47, 60 | Referenced in mission strategy context; not independently verifiable from codebase alone | `docs/devpost-copy.md:47` | VERIFY | Cross-check against Mission-MCP task log |
| 15 | "A2A-compatible agent card at `/.well-known/agent-card.json`" | 43 | Agent card is present and live; however `url` field is `https://methodic.run.app` (not the actual Cloud Run URL `https://methodic-2030382823.us-central1.run.app`) | `server.py:54`, live curl | MISMATCH | Fix `url` in agent card to match actual deployment URL |
| 16 | "MCP integration: secure access to deal context and telemetry data" | 44-45 | MCP server provides two tools per `test_mcp_server_lists_both_tools`; field filtering is implemented | `tests/test_integration.py`, `methodic/tools/` | TRUE | Keep, but optionally name the tools |
| 17 | "Persistent study state across sessions (currently single-shot)" listed as future work | 70-73 | Accurate — each run is ephemeral; `_demo_sessions` is in-memory | `methodic/server.py:67` | TRUE | Keep |

## Summary of Critical Issues

1. **Test count** (claim #1, #2): 52 → 133 actual. Sub-breakdown is also wrong (43+9 ≠ 69+60).
2. **Gemini model scope** (claim #12): `participant_sim` uses Flash-Lite, not Pro.
3. **Static baseline coverage** (claim #6): "~30%" is not supported by fixture data (~12.5% actual average).
4. **Gemini review gate count** (claim #13): 5 Gemini reviews, not 10.
5. **Agent count** (claim #8): "12 agent types" is inconsistent with 14 named nodes in `agent.py`.
6. **Agent card streaming flag** (claim #10, #15): `streaming: false` and wrong `url` both deployed live.
7. **BigQuery export** (claim #4): dry-run by default; the word "writes" overstates demo behavior.
