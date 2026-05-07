# Codex Review - Interactive Mode Spec and Plan

Reviewer: Codex  
Date: 2026-05-07  
Mission task: `a53242e1-d188-4b1e-a0f1-30e39e5433e0`  
Artifacts reviewed: `docs/superpowers/specs/2026-05-07-interactive-mode-design.md`, `docs/superpowers/plans/2026-05-07-interactive-mode.md`, current `methodic/agent.py`, current `methodic/server.py`

## Strategy Linkage

Interactive mode supports `mission_strategy['aichallenge'].demo_must_show[2]`: interactive participant conversations instead of static forms. It also strengthens the thesis that useful insights require good data, because a judge can personally experience vague-answer probing and see their own words become structured fields. The implementation must still preserve the vertical slice and stack alignment: Gemini/ADK/MCP/Cloud Run, not a standalone chat demo.

## STRENGTHS

- The feature is strategically valuable: replacing `participant_sim_agent` with a real human makes the demo more credible and directly addresses the "spectator experience" weakness.
- `HumanInputStep` using `await asyncio.wait_for(reg["event"].wait(), timeout=...)` is the right broad shape. It yields control to the event loop, so it should not block the process while `runner.run_async()` is paused for user input.
- Keeping demo mode at `/api/stream` and adding separate `/api/interactive/*` endpoints reduces regression risk for the recorded demo path.
- The agent graph factory is the right abstraction in principle. Swapping only the participant step while reusing organizer, methodology, interviewer, extractor, coverage, and turn-checker preserves the ADK architecture.
- The three-state frontend flow is appropriate for a judge-facing live experience: configuration, live interview, results.
- Test-first task decomposition is strong and mostly scoped to small files.

## GAPS

1. **Blocker - The agent factory plan breaks existing exported graph globals.** The plan replaces `methodic/agent.py` with a factory and keeps only `root_agent`. Current tests and likely callers import `study_planner`, `fieldwork_loop`, `finalize`, and `interview_loop` directly from `methodic.agent` (`tests/test_integration.py`, `tests/test_agents.py`). The plan's "existing tests pass" expectation is false unless those module-level exports are preserved or tests are intentionally migrated.

2. **Blocker - `input_requested` status is modeled incorrectly.** The proposed `GET /status` returns `input_requested: isess.event.is_set()`. That is backwards: an `asyncio.Event` being set means a response has been submitted and the blocked step can continue, not that the UI should accept input. The session needs a separate `input_requested: bool` or `pending_turn_id` updated from `state_delta.input_requested`.

3. **Blocker - In-memory session registry is unsafe for deployed Cloud Run unless instance routing is constrained.** `POST /respond`, `GET /stream`, `GET /status`, and `GET /results` all require the same process-local dictionaries. On Cloud Run with more than one instance, a later request can land on a different instance and return 404 or hang. The deployment plan must either set and document `--max-instances=1` for the demo or use an external store/session bus.

4. **Major - Duplicate or early responses can overwrite the active answer.** `interactive_respond` accepts any non-empty message and sets `isess.message` even when no human input is currently requested. Two rapid POSTs can overwrite the first answer before `HumanInputStep` reads it, and an early POST during planning can be consumed as the first participant turn. Add `input_requested`, `awaiting_turn_id`, and reject/409 responses unless the session is awaiting that turn.

5. **Major - SSE error completion can leave the client hanging.** `_start_interactive_pipeline` enqueues an `author=error` event on exception but does not enqueue a terminal system event. The stream generator only exits on timeout or a system complete payload, so the frontend can wait up to 600 seconds after an error. Break on `author == "error"` or enqueue a terminal failed event.

6. **Major - Reconnection design loses already-consumed events.** The queue is a single-consumer stream. If the browser disconnects after consuming planning/interview events, reconnecting to `/stream` only receives future queue entries, not the current transcript or insight state. `/status` is not enough to rebuild the UI. Keep an event history snapshot per session or make `/status` return the state needed to hydrate the frontend.

7. **Major - Session lifecycle and cleanup are specified but not implemented in the plan.** The spec says sessions older than 30 minutes are cleaned by a periodic background task, but the implementation plan never adds that task, cancellation, task handles, or registry cleanup on completion/failure. This creates stale ADK runner tasks and unbounded in-memory dictionaries during repeated judge tests.

8. **Major - The status vocabulary is inconsistent.** The spec says `planning|interviewing|complete|expired`; the plan sets `isess.status = "running"` and never updates to `interviewing` when input is requested. The frontend and tests should use one explicit state machine.

9. **Major - Skipping quality and BigQuery weakens the submission story unless labeled.** The interactive design trims finalization to `completion_responder`, with "no BigQuery/quality wait." That is acceptable for a live interview mode, but the UI and submission copy must label it as a live-experience mode, not the full submission pipeline. The strategy still requires measurable data-quality improvement and Google-aligned architecture proof.

10. **Minor - `RegistryProxy` is clever but unnecessary.** It hides message synchronization inside `__getitem__`, while the real shared state is already `InteractiveSession`. A small adapter object or direct registry entry containing the `InteractiveSession` would be easier to reason about and test.

11. **Minor - Endpoint validation is incomplete.** The plan covers empty messages and unknown sessions, but not expired/complete sessions, duplicate submit, overlong message, malformed JSON, stream-before-start race, or results-before-complete as a distinct 409.

12. **Minor - Frontend results depend on data shape not yet specified.** The results card expects extracted values, confidence, and evidence, but the SSE UI mostly receives coverage enums until `/results` is fetched. Define the exact mapping from `ParticipantResponse` to field cards before implementation.

## IMPROVEMENTS

- Preserve module-level demo exports in `methodic.agent`: build demo components through the factory, but still expose `study_planner`, `interview_loop`, `fieldwork_loop`, `finalize`, and `root_agent` for existing tests and ADK Dev UI compatibility.
- Replace the registry dict with a typed `InteractiveSession` API:
  - `request_input(turn_id)`,
  - `submit_input(turn_id, message)`,
  - `consume_input(turn_id, timeout)`,
  - `mark_complete()`,
  - `snapshot()`.
- Track `input_requested` separately from `event.is_set()`. Include `awaiting_turn_id` so duplicate/late responses can be rejected with `409 Conflict`.
- Add terminal queue events for both success and failure. The stream loop should break on `system complete`, `system failed`, or `error`.
- Store `events: list[dict]` and a compact `state_snapshot` on each `InteractiveSession`. Use it for reconnect hydration, `/status`, and debugging.
- Either add a documented demo-only Cloud Run constraint (`--max-instances=1`) or move session state to Redis/Firestore/Cloud Tasks/PubSub before public live use.
- Add cleanup explicitly: task handle, cancel on expiry, remove both registry keys, close streams, and preserve final results for a short TTL.
- Keep quality/export language honest: interactive mode can show coverage and extracted fields, while the full demo mode remains the BigQuery/quality proof path.
- Use `asyncio.Queue(maxsize=...)` or bounded event history to prevent unbounded memory growth if a stream is never opened.
- Add API tests for duplicate response, response before input requested, complete-session response, stream error termination, and session cleanup.

## Verdict

**hold.** The product direction is right and the `asyncio.Event` blocking pattern is viable, but the current plan has three release-blocking design faults: it breaks existing agent exports, conflates "awaiting input" with "response submitted", and relies on process-local session state without a Cloud Run deployment constraint. Fix those before implementation starts.

## Falsifiable Assumptions

1. ADK `runner.run_async()` continues the same `ctx.session.id` created in `interactive_start`; if ADK creates or aliases a different session id, the registry lookup in `HumanInputStep` fails.
2. FastAPI endpoints and the ADK runner task run on the same asyncio event loop in the target server; if not, sharing `asyncio.Event` objects across loops can fail.
3. Cloud Run is configured as a single-instance demo service or provides sticky routing; if not, in-memory session lookup will intermittently fail.
4. The human submits exactly one response per requested turn; duplicate, stale, or early submissions currently alter behavior.
5. `ParticipantResponse` remains available in ADK session state after the interactive run; if not, `/results` cannot build the promised field cards.
