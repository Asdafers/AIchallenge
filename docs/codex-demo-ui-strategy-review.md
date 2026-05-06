# Codex Review: Demo UI Strategy

Date: 2026-05-06
Task: ec192a05-51e2-4c6b-8dee-8eaf7af70e1e
Reviewer: codex-2026-05-06T1940-ui01
Verdict: APPROVE_WITH_NOTES

## Sources Checked

- `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md`
- `docs/agent-runtime-spike-results.md`
- `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md`
- `methodic/static/demo.html`

Strategy linkage: this review supports `mission_strategy['aichallenge'].demo_must_show` by preserving live agent handoffs, MCP/tool events, measurable coverage, evidence-linked extraction, and a clear before/after data-quality delta. It also stays inside `non_goals` by avoiding a broad survey-builder UI.

## Recommendation

Use a **thin server-side demo adapter over ADK `api_server` `/run_sse`**, then stream normalized demo events to the browser.

Do not put the Cloud Run bearer token in browser JavaScript. Do not keep the old custom `demo_runner.py` as the primary agent executor. The adapter should be small:

1. Browser posts a fixed demo request to `/demo/run`.
2. Server creates or reuses an ADK session through the local `api_server` endpoints.
3. Server calls `/run_sse` with service identity/auth.
4. Server parses ADK SSE events into a judge-focused event stream:
   - `agent_handoff`
   - `conversation_turn`
   - `mcp_lookup`
   - `extraction`
   - `coverage_update`
   - `replan`
   - `bigquery_export`
5. Browser consumes the normalized stream from `/demo/events/{run_id}` or a server-sent event endpoint controlled by the app.

This preserves ADK `api_server` as the source of truth while keeping auth and event-shaping out of the browser.

## Findings

### Finding 1 - MAJOR - Browser-direct `/run_sse` leaks the wrong abstraction and has an auth problem

The spike proved Cloud Run `api_server` works: `/list-apps`, session creation, and `/run_sse` return real Gemini output via Vertex AI (`docs/agent-runtime-spike-results.md:81-89`, `docs/agent-runtime-spike-results.md:160-166`). It also records that public `allUsers` access is blocked and authenticated identity-token access is required (`docs/agent-runtime-spike-results.md:87-89`).

A browser `EventSource` cannot safely hold a bearer token for a public demo page. Even for a private demo, wiring raw ADK SSE directly into the UI exposes implementation details and makes it harder to produce stable judge-facing visuals.

Mitigation: keep Cloud Run authenticated. Use a thin backend adapter or same-service route that calls `api_server` with server-side identity and emits sanitized demo events to the browser.

### Finding 2 - MAJOR - The current Task 18 polling plan is now stale

Task 18 still specifies polling custom `/api/demo/{study_id}/coverage`, `/events`, and `/status` endpoints (`docs/superpowers/plans/2026-05-04-methodic-adk-agent.md:2562-2580`). The current `demo.html` implements exactly that older polling architecture (`methodic/static/demo.html:218-257`, `methodic/static/demo.html:269-280`).

That conflicts with the spike result that ADK `api_server` now provides the core session and run endpoints (`docs/agent-runtime-spike-results.md:97-101`, `docs/agent-runtime-spike-results.md:160-166`). Keeping the old custom executor as primary duplicates ADK session/run behavior and risks divergence from the deployed agent path.

Mitigation: revise Task 18 so the UI consumes normalized events derived from `/run_sse`. Keep custom endpoints only as the thin presentation adapter, not as a parallel agent runner.

### Finding 3 - MAJOR - The demo needs event normalization, not raw ADK event rendering

Raw `/run_sse` contains useful metadata, but judges should not see raw agent protocol. The planned UI correctly wants a split-screen baseline, coverage bars, and timeline (`docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md:343-357`). The missing layer is a deterministic mapper from ADK event structure to product story.

Mitigation: implement a small event reducer:

- Read `author` into timeline stage.
- Read `content.parts[].text` into conversation cards.
- Read `actions.stateDelta.coverage_state` into coverage bars.
- Detect MCP/tool events and label them visibly.
- Detect extracted `ParticipantResponse` fields and show a structured-data panel.
- Persist enough run state for replay in the demo video.

### Finding 4 - MAJOR - The UI needs a structured output panel, not only conversation + bars

The current page has static baseline, live conversation, coverage bars, and a timeline (`methodic/static/demo.html:66-97`). That is directionally right, but it does not yet show the strongest proof: the final analysis-ready row or extracted field table. The static baseline says "Price"; Methodic must answer with structured fields, evidence quotes, confidence, and export status.

Mitigation: change the layout to four proof zones:

1. Static survey baseline.
2. Live Methodic conversation and agent handoffs.
3. Coverage and re-plan state.
4. Extracted record / BigQuery export proof.

This makes "no insights without good data" visible without relying on narration.

### Finding 5 - MINOR - Hybrid demo is the best scoring path

For scoring, a hybrid is stronger than either a pure live demo or pure recording:

- Record the main submission video from a known-good deployed run.
- Keep the live deployed demo available for judges or follow-up.
- Include a cached/replay mode seeded from a real deployed run to avoid rate-limit, auth, or cold-start failure during judging.

This protects Demo & Presentation while preserving Technical Implementation evidence.

Mitigation: add a `replay_run_id` or static JSON replay artifact generated from real `/run_sse` output. Label replay clearly if used.

### Finding 6 - MINOR - The Human Mode toggle should wait

The current UI includes a Human Mode toggle (`methodic/static/demo.html:100-105`, `methodic/static/demo.html:269-273`). That feature is appealing, but it is not required for the submission proof and complicates input/session state.

Mitigation: cut Human Mode until after the deployed scripted demo is stable. The first demo should prove the B2B win-loss vertical slice, not interactive participant recruitment.

## Answers To Review Questions

1. **Direct `/run_sse` from browser or intermediate layer?** Use an intermediate server-side adapter. Browser-direct SSE is wrong because of bearer-token handling and raw ADK event shape.
2. **Best before/after architecture?** Static baseline on the left; server-normalized live Methodic stream on the right; coverage/re-plan in the middle or side rail; extracted record and BigQuery export proof as a final panel.
3. **Auth handling?** Use service-side auth from a thin frontend/adapter. Do not expose identity tokens in browser JavaScript. For video capture, authenticated curl is fine as an operator tool, not as the UI architecture.
4. **Live vs recorded vs hybrid?** Hybrid. Record a polished deployed run for submission, keep the live demo available, and include a clearly labeled replay fallback from a real run.
5. **Visualization?** Split-screen + coverage bars + timeline is right but incomplete. Add extracted structured record and BigQuery export proof. Highlight the re-plan moment as a single obvious decision point.

## Suggested Task 18 Revision

Replace polling custom `/api/demo/*` as the core architecture with:

```text
Browser demo UI
  |
  | GET /demo
  | POST /demo/run
  | GET /demo/events/{run_id}  (SSE or fetch stream)
  v
Thin demo adapter
  |
  | server-side auth/session management
  v
ADK api_server
  |
  | /apps/{app}/users/{user}/sessions
  | /run_sse
  v
Methodic root_agent
```

Required UI states:

- idle
- starting session
- streaming agent events
- coverage updated
- re-plan triggered
- structured record extracted
- BigQuery export complete
- failed with visible error

## Falsifiable Assumptions

1. `/run_sse` emits enough `actions.stateDelta` data to populate coverage and extracted fields without re-running a custom `demo_runner.py`.
2. A thin server-side adapter can call authenticated Cloud Run/ADK endpoints without exposing bearer tokens to the browser.
3. The deployed Methodic agent emits identifiable MCP/tool events, not only final LLM text.
4. A replay artifact generated from a real deployed run is acceptable if live demo execution is unavailable during judging.
5. Removing Human Mode before submission will not weaken the demo story because the judged proof is the autonomous research workflow.

## Verdict

**APPROVE_WITH_NOTES.**

Proceed with ADK `api_server` on Cloud Run as the core serving surface, but revise Task 18 before implementation. The UI should not consume `/run_sse` directly from the browser and should not preserve the old polling-only custom runner as the core path. Build a thin authenticated demo adapter, normalize ADK SSE into product events, add structured-output/export proof, and record a polished deployed run with a replay fallback.
