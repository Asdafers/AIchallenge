# Codex Plan Review: Methodic ADK Agent Design + Implementation Plan

Date: 2026-05-04
Task: 979c336d-94eb-459d-907f-61be92fd446b
Verdict: REVISE_REQUIRED

## Sources Checked

- Design spec: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md`
- Implementation plan: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md`
- Gemini review: `docs/gemini-plan-review.md`
- ADK workflow agents and state/output_key docs: https://adk.dev/agents/workflow-agents/sequential-agents/
- ADK LoopAgent exit example: https://adk.dev/agents/workflow-agents/loop-agents/
- ADK MCP Toolset docs: https://google.github.io/adk-docs/tools-custom/mcp-tools/
- ADK A2A exposing docs: https://adk.dev/a2a/quickstart-exposing/
- ADK Cloud Run/get_fast_api_app docs: https://google.github.io/adk-docs/deploy/cloud-run/
- Gemini 3 model docs: https://ai.google.dev/gemini-api/docs/gemini-3
- Gemini SDK migration docs: https://ai.google.dev/gemini-api/docs/libraries
- Gemini structured output docs: https://ai.google.dev/gemini-api/docs/structured-output
- A2A 1.0 specification: https://a2a-protocol.org/latest/specification/

## Document 1: Design Spec

Path: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md`

### Finding 1 - BLOCKER - The agent graph treats FunctionTools as workflow sub-agents

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:94-108`, `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:188-207`

The graph places `extractor`, `turn_checker`, `coverage_checker`, and `bigquery_export` directly inside `LoopAgent`/`SequentialAgent` as if a `FunctionTool` can be a sub-agent. ADK workflow agents execute `sub_agents`; tools are attached to an `LlmAgent` or invoked by custom agent code. The ADK examples show `SequentialAgent` and `LoopAgent` taking agent instances as sub-agents, while tools are supplied through a child `LlmAgent.tools` list.

Impact: the specified graph will not assemble or run as described. This also invalidates parts of the state flow table because the FunctionTools have no agent wrapper that can read/write session state.

Mitigation: introduce deterministic wrapper agents for each deterministic step. Options:

- Implement custom `BaseAgent`/workflow agents for `extractor_step`, `coverage_step`, `turn_checker_step`, and `bigquery_export_step`.
- Or attach tools to a thin `LlmAgent` only where an LLM should decide to call them, then add a deterministic post-processing callback/custom agent for mandatory steps.

### Finding 2 - MAJOR - `output_key` state flow is under-specified for participant sessions and appends

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:121-135`, `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:137-144`

There is no circular dependency in the high-level order, but there are missing state keys and one unsupported assumption. The table says `interviewer` writes `participant_responses` and appends, but ADK `output_key` stores the agent output under a key; it does not by itself merge participant records, append to a list, or separate parallel participants. The design also omits state keys for active participant id, persona fixture, transcript, latest interviewer turn, latest participant turn, MCP tool events, extraction result, selected reserve participant, and BigQuery export rows.

Impact: parallel or repeated interview loops can overwrite each other or lose the transcript needed by the extractor and UI.

Mitigation: define an explicit state contract:

- `active_participant_id`
- `participants_to_run`
- `transcripts_by_participant`
- `latest_turn_pair`
- `participant_response_by_id`
- `tool_events`
- `coverage_state`
- `replan_decision`
- `export_result`

Use a deterministic custom agent or callback to append/merge state rather than relying on `output_key` alone.

### Finding 3 - MAJOR - LoopAgent exit is conceptually right, but the spec blurs tool-triggered escalation and agent text

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:146-148`

The design's statement that a tool can set `tool_context.actions.escalate = True` matches ADK's LoopAgent example. The risk is that the design calls `turn_checker` and `replanner` agents "responsible for triggering escalation" while also describing them as FunctionTool/LlmAgent components in different places.

Impact: if implemented as LLM text such as "ESCALATE", the loop will not exit unless separate code detects that text and calls a tool that sets escalation.

Mitigation: make the exit path a real tool or deterministic agent:

- `exit_interview_loop(tool_context)` sets `tool_context.actions.escalate = True`.
- `turn_checker_step` calls it when participant-level stop conditions are met.
- `exit_fieldwork_loop(tool_context)` does the same for study-level stop.

Add tests that run a small `LoopAgent` and prove it exits before `max_iterations`.

### Finding 4 - MAJOR - A2A discovery and Agent Card shape are not A2A 1.0 compliant

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:223-252`, `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:313-320`

The spec says the Agent Card is served at `/.well-known/agent.json`. A2A 1.0 registers `/.well-known/agent-card.json`. The sample card also uses snake_case fields (`default_input_modes`, `default_output_modes`) and omits required A2A 1.0 fields such as `supportedInterfaces`; each skill also needs an `id` and `tags`.

Impact: this can pass a custom smoke test but fail an actual A2A client/discovery test.

Mitigation: let ADK `to_a2a(root_agent, agent_card=...)` generate or validate the card, then expose/proxy `/.well-known/agent-card.json`. If hand-authoring, use A2A 1.0 camelCase fields: `supportedInterfaces`, `defaultInputModes`, `defaultOutputModes`, and skill `id`/`tags`.

### Finding 5 - MAJOR - A2A + FastAPI one-port composition is still unproven

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:254-296`, `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:313-320`

The spec correctly identifies that `to_a2a()` returns a Starlette/ASGI app and `get_fast_api_app()` returns FastAPI. ADK documents `to_a2a(root_agent)` as a uvicorn-served app and `get_fast_api_app()` as a FastAPI app that can be customized with additional routes, but it does not document mounting `to_a2a()` under an ADK FastAPI app as a supported production pattern.

Impact: one-port composition may work, but treating it as the primary implementation path creates schedule risk. The discovery path is especially sensitive because a mounted `/a2a` app will not naturally own root `/.well-known/agent-card.json`.

Mitigation: make the implementation plan prove this on day one of server work. Preferred fallback for the challenge demo: use `get_fast_api_app()` plus a manual `/.well-known/agent-card.json` and honestly label A2A as "A2A-compatible/prototype" unless a real A2A SDK client passes `SendMessage` and task retrieval.

### Finding 6 - MAJOR - Error handling is not complete enough for live Gemini extraction

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:196-201`, `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:359-395`

The design says extraction uses strict JSON, but it does not define behavior for invalid JSON, schema-valid but semantically wrong JSON, missing evidence, model timeout, safety refusal, quota/rate limits, or MCP timeout during a turn.

Impact: the live demo can fail or silently produce untrustworthy data, undermining the "no insights without good data" thesis.

Mitigation: define a recovery matrix:

- invalid JSON: retry once with the validation error, then mark extraction `partial`
- schema-valid but evidence-missing: downgrade affected coverage state
- timeout/rate limit: use cached-live trace in demo mode and mark source
- MCP timeout: ask context-free follow-up and log tool failure
- safety/refusal: mark unresolved, do not fabricate

Add tests for invalid JSON and missing evidence.

### Finding 7 - MINOR - BigQuery flattening is directionally sound

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:331-337`, `docs/schema/bigquery-table.sql:1-47`

Flattening `structured_fields`, confidence, coverage, quality booleans, and JSON-string evidence matches the existing SQL schema and is acceptable for a demo. The missing piece is lifecycle: dataset/table creation, idempotency, and insert failure handling are not specified.

Mitigation: add `ensure_dataset_and_table()` or an explicit setup task, include an insert id or dedupe key, and expose insert errors in `export_result`.

## Document 2: Implementation Plan

Path: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md`

### Finding 1 - BLOCKER - Task 15 cannot implement the design graph

References: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2127-2225`

Task 15 assembles `interview_loop` with only `[interviewer_agent, participant_sim_agent]`, omitting extractor, turn checker, and coverage checker. `finalize` includes `[quality_agent, completion_responder]`, omitting BigQuery export. This agrees with Gemini's blocker, but the deeper issue is that the omitted components cannot simply be inserted as raw `FunctionTool` objects because workflow `sub_agents` must be agents.

Mitigation: add Task 14.5 before root assembly:

- create `methodic/agents/extractor_step.py`
- create `methodic/agents/coverage_step.py`
- create `methodic/agents/turn_checker_step.py`
- create `methodic/agents/bigquery_export_step.py`

Then wire those wrapper agents into Task 15 and test that the graph contains them.

### Finding 2 - BLOCKER - `/api/demo/run` does not run the agent

References: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2246-2353`, `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2369-2416`

The server task creates an in-memory session with `status: running`, empty coverage, and empty events, then returns immediately. No ADK Runner, root agent invocation, background task, Gemini call, MCP call, coverage update, event stream, or export happens. The `demo.html` polling approach is technically fine for a small demo, but it will poll empty data forever.

Mitigation: add a real demo runner before UI work:

- `methodic/demo_runner.py` starts a background async task
- it invokes `root_agent` or a deterministic demo orchestrator
- it appends events and coverage snapshots to `_demo_sessions`
- it transitions status to `complete` or `failed`
- `/api/demo/{id}/events` includes error events

Add a server test that POSTs `/api/demo/run`, waits/polls, and observes at least one event and non-empty coverage.

### Finding 3 - MAJOR - The Gemini SDK code and dependencies are inconsistent with current docs

References: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:73-81`, `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:1118-1202`

The plan uses `import google.generativeai as genai` but does not add `google-generativeai` to requirements. More importantly, Google now recommends the GA `google-genai` SDK and marks `google-generativeai` as not actively maintained. Current structured-output examples use `from google import genai`, `client.models.generate_content(...)`, and `response_json_schema`.

Mitigation: add `google-genai` to `requirements.txt` and rewrite extractor code to use:

```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model=MODEL,
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_json_schema": ParticipantResponseExtraction.model_json_schema(),
    },
)
```

Then validate with `ParticipantResponseExtraction.model_validate_json(response.text)`.

### Finding 4 - MAJOR - The implementation plan does not make `replanner` capable of deterministic loop exit

References: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2066-2110`, `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2200-2204`

Task 14 tells the LLM to include "ESCALATE" in text, but no code detects that text and no tool sets `tool_context.actions.escalate = True`. The `replanner_agent` also has no `check_coverage` tool attached, agreeing with Gemini's major finding.

Mitigation: replace text-triggered escalation with a real exit/check tool or wrapper agent. Unit test it by proving `fieldwork_loop` exits before `max_iterations` when all coverage variables are high confidence.

### Finding 5 - MAJOR - State and signatures do not match across Tasks 10-15

References: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:1708-1737`, `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:1777-1795`, `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:1830-1870`, `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:1939-1944`, `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2179-2224`

The planner agents rely on "conversation history" rather than explicit state placeholders such as `{study_brief}` and `{methodology_review}`. The participant agent has no `output_key`, so its questions are not captured in state. The simulator also has no output key. There is no signature or state contract showing how `extract_structured_fields(transcript, participant_id, study_id, ...)` receives the transcript from the loop.

Mitigation: either use explicit state placeholders in instructions or custom orchestration code that passes state into each step. Add tests for required `output_key`s and for state keys produced after each phase.

### Finding 6 - MAJOR - A2A implementation is only an Agent Card stub

References: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2254-2322`, `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2673-2704`

Task 16 serves `/.well-known/agent.json` and no A2A message/task endpoints. It does not use `to_a2a()`, `adk api_server --a2a`, or an A2A SDK request handler. Its Agent Card is not A2A 1.0 shaped.

Mitigation: either:

- implement real `to_a2a(root_agent)` and test with an A2A SDK client, or
- downgrade plan wording to "A2A-pattern" and serve an A2A 1.0-like Agent Card at `/.well-known/agent-card.json` with `supportedInterfaces`.

### Finding 7 - MAJOR - BigQuery export is not production-ready enough for the demo claim

References: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:1311-1453`, `docs/schema/bigquery-table.sql:1-47`

The flattening itself matches the existing table shape, but the export tool does not create or validate the dataset/table, does not include a project-qualified table id, does not make insertion idempotent, and returns `rows_written: 0` on any insert error without surfacing that as a failed demo state. The plan also sets `BIGQUERY_DRY_RUN=false` in Docker, so Cloud Run will fail if IAM/table setup is missing.

Mitigation: add a setup/validation step:

- `ensure_bigquery_table(project, dataset, table)`
- `export_to_bigquery(..., fail_on_error=True)`
- include insert errors in `/api/demo/{id}/events`
- add a dry-run-safe local mode and a required live smoke test for submission

### Finding 8 - MAJOR - MCP tests hand-roll stdio framing and can hang

References: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:492-590`, `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2500-2539`

The plan hand-rolls MCP JSON-RPC framing without read timeouts. If the server emits stderr, changes protocol headers, or does not respond, the tests can block indefinitely. The existing repo already uses the official MCP client in `scripts/wp6_mcp_boundary.py`, which is safer.

Mitigation: reuse `mcp.client.stdio.stdio_client` and `ClientSession`, or add subprocess timeouts and failure diagnostics to every read loop.

### Finding 9 - MINOR - Dockerfile task overwrites an existing deployment file and ignores `$PORT`

References: `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2420-2456`

The repo already has a `Dockerfile`. The task says "Create: Dockerfile" and would replace existing deployment behavior without an explicit migration note. The command pins port 8080 rather than using Cloud Run's `$PORT` variable.

Mitigation: mark this as "Modify: Dockerfile", explain the migration from the current WP9 server, and use:

```dockerfile
CMD ["sh", "-c", "uvicorn methodic.server:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

### Missing Edge Case Tests

Add tests for:

- invalid Gemini JSON and schema-validation retry
- schema-valid extraction with missing evidence causing confidence downgrade
- LoopAgent exits before max iterations
- A2A Agent Card validates required fields and `/.well-known/agent-card.json`
- demo run produces non-empty events/coverage
- BigQuery insert failure marks demo/export failed
- MCP timeout/fallback event
- parallel participant state does not overwrite transcripts or responses
- `adk web`/`get_fast_api_app` discovers the agent from the chosen `agents_dir`

## Agreement And Disagreement With Gemini Review

I agree with Gemini that:

- import paths may vary by ADK version and should be verified against the installed package
- A2A + FastAPI composition is a real integration risk
- `turn_checker` is missing from the implementation plan
- extractor/export/checker tools are orphaned in Task 15
- the replanner lacks tool access
- the schema tests are a good foundation

I disagree or go further in these areas:

- The problem is not just orphaned tools; the plan's graph model is invalid because it treats FunctionTools as workflow sub-agents.
- The A2A issue is not only mount-path composition; the Agent Card path and shape are not A2A 1.0 compliant.
- The server/UI plan is not just incomplete; `/api/demo/run` currently cannot demonstrate anything because it never invokes the agent.
- The Gemini SDK choice is a concrete implementation risk: the plan uses the legacy `google-generativeai` API without declaring it, while current docs recommend `google-genai`.

## Final Verdict

REVISE_REQUIRED.

The product direction is sound and the plan is close enough to repair, but implementation should not start from Task 15 as written. Fix the graph model first: wrap deterministic tools as agents or custom workflow steps, define state keys explicitly, implement real loop exit, and decide whether A2A is truly `to_a2a()`-backed or honestly A2A-pattern. After those revisions, the plan becomes executable.
