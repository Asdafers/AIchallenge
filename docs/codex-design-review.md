# Codex Design Review: Methodic ADK Agent Spec

Date: 2026-05-04
Task: 7271a856-c560-47d7-bdfc-53aa8b5cf388
Verdict: REVISE_REQUIRED

Reviewed file: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md`

Strategy linkage: this review protects `mission_strategy['aichallenge'].stack_alignment` (Gemini API, ADK, MCP, Cloud Run/GKE), `vertical_slice` (Organizer AI, Participant AI, Data Quality Layer), and `demo_must_show` (interactive participant conversations and measurable data quality) by checking whether the proposed ADK design can actually be built.

## Sources Checked

- ADK SequentialAgent and `output_key`: https://adk.dev/agents/workflow-agents/sequential-agents/
- ADK LoopAgent and escalation: https://adk.dev/agents/workflow-agents/loop-agents/
- ADK MCP Toolset: https://google.github.io/adk-docs/tools-custom/mcp-tools/
- ADK A2A exposing: https://adk.dev/a2a/quickstart-exposing/
- ADK Cloud Run and `get_fast_api_app`: https://google.github.io/adk-docs/deploy/cloud-run/
- Gemini 3 model docs: https://ai.google.dev/gemini-api/docs/gemini-3
- A2A 1.0 spec: https://a2a-protocol.org/latest/specification/

## Summary

The design is directionally strong for the challenge: ADK orchestration, Gemini conversations, MCP context lookup, Cloud Run, and BigQuery are the right stack for Methodic. The main revision needed is structural. The spec mixes ADK agents and ADK tools in the workflow graph, assumes `output_key` can append/merge participant state, and overstates A2A one-port composition before it has been proven.

## ADK API Accuracy

### Finding 1 - BLOCKER - FunctionTools are modeled as workflow sub-agents

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:94-108`, `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:188-207`

The graph places `extractor`, `turn_checker`, `coverage_checker`, and `bigquery_export` directly inside `LoopAgent` or `SequentialAgent` as if `FunctionTool` objects can be workflow `sub_agents`. ADK workflow agents execute agent instances as `sub_agents`; FunctionTools are attached to an agent or invoked from custom agent code.

Mitigation: define wrapper/custom agents:

- `extractor_step` invokes Gemini structured extraction and writes `participant_response_by_id`
- `turn_checker_step` computes participant stop conditions and escalates when complete
- `coverage_step` computes study coverage and writes `coverage_state`
- `bigquery_export_step` writes/export rows and writes `export_result`

### Finding 2 - MINOR - Import paths should be version-pinned and smoke-tested

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:170-185`, `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:276-284`

The import families are plausible, but ADK examples commonly import from `google.adk.agents` and MCP examples may use `google.adk.tools.mcp_tool.mcp_toolset` / `mcp_session_manager` paths depending on version. The spec should not rely on untested exact paths.

Mitigation: pin `google-adk` after a local import smoke test and record the verified imports in the implementation plan:

```bash
python - <<'PY'
from google.adk.agents import Agent, SequentialAgent, LoopAgent, ParallelAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.cli.fast_api import get_fast_api_app
print("ADK imports OK")
PY
```

## State Flow And `output_key`

### Finding 3 - MAJOR - No circular dependency, but important state is missing

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:121-135`, `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:137-144`

The state flow is ordered correctly: organizer -> methodology -> question design -> interview -> coverage -> replan -> quality -> export. I do not see a circular dependency.

The missing piece is that `output_key` stores an agent response under a session key; it does not automatically append to `participant_responses`, merge parallel participant outputs, or preserve the transcript needed by extractor/UI. The table also omits active participant id, persona fixture, latest turn pair, tool events, extraction result, selected reserve participant, and export rows.

Mitigation: replace the table with an explicit state contract:

- `active_participant_id`
- `participants_to_run`
- `transcripts_by_participant`
- `latest_turn_pair`
- `participant_response_by_id`
- `tool_events`
- `coverage_state`
- `replan_decision`
- `quality_report`
- `export_result`

Use custom agents or callbacks to append and merge state. Keep `output_key` for simple single-output planner agents only.

## LoopAgent Mechanics

### Finding 4 - MAJOR - Escalation is valid, but only if performed by a real tool/custom step

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:139-148`

The spec's claim that `tool_context.actions.escalate = True` exits a `LoopAgent` is accurate. ADK documents this pattern.

The risk is implementation ambiguity. `turn_checker` is described as a FunctionTool in the graph, while `replanner` is an LLM agent. An LLM saying "stop" or "ESCALATE" will not exit a loop unless a tool or deterministic step sets `tool_context.actions.escalate = True`.

Mitigation: define two explicit exit functions/custom steps:

- `exit_interview_loop(tool_context)` for participant-level stop conditions
- `exit_fieldwork_loop(tool_context)` for study-level coverage sufficiency

Add a test that proves each loop exits before `max_iterations`.

## MCP Toolset Integration

### Finding 5 - MAJOR - McpToolset direction is right, but process lifecycle and Cloud Run behavior need detail

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:154-185`

Using `McpToolset` to wrap the existing stdio MCP server is the correct direction and aligns with ADK docs. The design should add operational details:

- whether one MCP subprocess is created per session, per agent, or per request
- timeout behavior and fallback when the MCP server hangs
- whether Cloud Run can spawn `python3 scripts/wp6_mcp_server.py` from the packaged image
- how tool call results become `tool_events` for the demo UI

Mitigation: add an MCP smoke test using ADK `McpToolset`, not only the existing raw MCP client, and log every tool call to `tool_events`.

## A2A And FastAPI Composition

### Finding 6 - MAJOR - A2A Agent Card path and shape are not A2A 1.0 compliant

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:223-252`

The spec says the card is served at `/.well-known/agent.json`; A2A 1.0 uses `/.well-known/agent-card.json`. The sample card also uses snake_case fields such as `default_input_modes` and `default_output_modes`; A2A 1.0 uses camelCase names such as `defaultInputModes` and `defaultOutputModes`, plus required fields such as `supportedInterfaces` and skill `id`/`tags`.

Mitigation: let ADK `to_a2a()` generate/validate the card where possible. If manually serving a card, align it with A2A 1.0 and smoke-test with an actual A2A client.

### Finding 7 - MAJOR - One-port `to_a2a()` + `get_fast_api_app()` composition is unproven

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:254-320`

ADK documents `get_fast_api_app()` as a FastAPI app that can be customized with additional routes. ADK also documents `to_a2a(root_agent)` as returning a Starlette app. I did not find an official pattern proving that mounting the A2A ASGI app under the ADK FastAPI app preserves A2A discovery and task endpoints on one Cloud Run port.

Mitigation: make this a spike before relying on it:

1. Try `to_a2a(root_agent)` standalone and verify with an A2A client.
2. Try `app.mount("/a2a", a2a_app)` plus a manual root card route.
3. If this fails, choose either ADK web/custom API as the demo surface or A2A standalone, and label the other as A2A-pattern rather than full compliance.

## Cloud Run And BigQuery

### Finding 8 - MINOR - `get_fast_api_app()` is a valid FastAPI customization point

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:273-296`

The design is right that `get_fast_api_app()` returns a FastAPI app suitable for adding custom routes. The risk is not adding routes; it is whether those routes can also host A2A without path/discovery conflicts.

Mitigation: keep custom `/api/demo/*` routes on the FastAPI app, but treat A2A as separately verified.

### Finding 9 - MINOR - BigQuery flattening is sound, but setup/error lifecycle is underspecified

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:331-337`, `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:428-430`

Flattening the participant response into `docs/schema/bigquery-table.sql` is reasonable for a demo. The spec should add dataset/table creation, insert idempotency, and export failure behavior.

Mitigation: add `ensure_bigquery_table()`, a deterministic insert id or run id, and require export errors to appear in `export_result` and the developer overlay.

## Model And SDK Risk

### Finding 10 - MAJOR - `gemini-3.1-pro-preview` / `gemini-3.1-flash-lite-preview` are not verified current model IDs

References: `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:16-22`, `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:111-120`

Current Gemini 3 docs show Gemini 3 Pro Preview as `gemini-3-pro-preview`. I did not verify `gemini-3.1-pro-preview` or `gemini-3.1-flash-lite-preview` as current public Gemini API model IDs. Building the whole spec around unverified model names is a preventable failure mode.

Mitigation: set stable defaults to known model IDs and make preview models optional:

- default: `gemini-2.5-flash` for interview turns
- higher reasoning: `gemini-2.5-pro` or verified `gemini-3-pro-preview`
- fail fast at startup by listing/validating configured model IDs

## Required Revisions

1. Replace FunctionTool-as-sub-agent graph nodes with wrapper/custom agents.
2. Define the full session state contract and stop relying on `output_key` for append/merge behavior.
3. Make loop exit a real tool/custom step that sets `tool_context.actions.escalate = True`.
4. Align A2A card path/fields with A2A 1.0 or relabel as A2A-pattern.
5. Prove or simplify one-port A2A + FastAPI composition.
6. Add MCP lifecycle/timeouts and ADK `McpToolset` smoke tests.
7. Verify model IDs and ADK import paths in the target environment.
8. Add BigQuery setup/error behavior.

## Final Verdict

REVISE_REQUIRED. The design is strategically aligned and close to usable, but the ADK graph semantics and A2A claims need correction before implementation starts.
