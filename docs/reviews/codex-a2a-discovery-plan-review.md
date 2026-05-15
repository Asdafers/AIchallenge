# Codex Review: A2A Task Lifecycle + Discovery Agent Plan

Strategy linkage: this review supports `mission_strategy['aichallenge'].stack_alignment` and `demo_must_show` by checking whether the proposed A2A/discovery work credibly strengthens Methodic as a Google-aligned, agent-to-agent research service. It also protects the thesis by rejecting A2A-shaped UI polish that would not produce trustworthy, interoperable data-capture delegation.

## Issues

1. **Blocker - The proposed endpoints are not current A2A JSON-RPC, so the plan would overclaim protocol credibility.**

   The plan defines bespoke REST endpoints such as `POST /a2a/tasks/send`, `GET /a2a/tasks/{id}`, and `POST /a2a/tasks/sendSubscribe` (`docs/superpowers/plans/2026-05-15-a2a-discovery-agent.md:37-40`, `docs/superpowers/plans/2026-05-15-a2a-discovery-agent.md:336-417`). The current A2A spec requires JSON-RPC 2.0 requests/responses, with core initiation through `message/send`, streaming through `message/stream`, polling through `tasks/get`, and cancellation through `tasks/cancel`. It also says JSON-RPC requests are POSTed to the agent URL and responses must be JSON-RPC objects, with SSE data also containing JSON-RPC response objects. A judge or interoperability tester using an A2A client would not be able to call this implementation as A2A.

   Fix: change Task 2 around a single A2A JSON-RPC endpoint whose request body includes `jsonrpc`, `id`, `method`, and `params`; implement at least `message/send`, `tasks/get`, and `tasks/cancel`, with optional `message/stream` or `tasks/resubscribe` for SSE. Keep REST convenience endpoints only if they are explicitly labeled non-A2A demo helpers.

2. **Major - The Agent Card shape is still A2A-inspired, not spec-shaped.**

   The proposed card adds custom `a2aEndpoints` and `capabilities.a2a` fields (`docs/superpowers/plans/2026-05-15-a2a-discovery-agent.md:524-574`), but it omits required current fields such as `protocolVersion` and `preferredTransport`, and it does not make the `url` field the JSON-RPC endpoint clients should call. The A2A spec requires the Agent Card to declare protocol version and the relationship between `url` and preferred transport. Without that, discovery remains a custom card that happens to mention A2A.

   Fix: update the plan to use a valid Agent Card schema for the target A2A version and pin that version in the plan. Add a card-schema regression test that asserts `protocolVersion`, `preferredTransport`, JSON-RPC `url`, capabilities, skills, input/output modes, and security fields are present and consistent.

3. **Major - Task state and output shape do not match A2A Task semantics.**

   The task store uses a flat `status` string with `running` and `cancelled` (`docs/superpowers/plans/2026-05-15-a2a-discovery-agent.md:144-151`), while current A2A tasks use a nested `status.state` with states such as `submitted`, `working`, `input-required`, `completed`, `canceled`, `failed`, `rejected`, and `auth-required`. The result is returned as `task["result"]` (`docs/superpowers/plans/2026-05-15-a2a-discovery-agent.md:367-375`), but A2A completed tasks should return output through artifacts and may include history. This would make successful calls look unfamiliar to an A2A client and weakens the “structured results” claim.

   Fix: revise `A2ATaskStore` to store and serialize `Task` objects with `id`, `contextId`, `status`, `artifacts`, and optional `history`. Put Methodic outputs in artifacts with typed parts rather than a custom top-level `result` only.

4. **Major - The discovery agent is too generic to prove Methodic’s data-quality thesis.**

   The discovery prompt asks for at least five canonical variables and generic hypotheses (`docs/superpowers/plans/2026-05-15-a2a-discovery-agent.md:645-690`), but it does not require a decision owner, business decision, sampling risk, coverage threshold, enabled field rationale, static-survey baseline, or “do not overclaim” caveats. That means the agent can generate a plausible brief without proving Methodic is pursuing objective coverage or methodology quality.

   Fix: require the discovery output to include `business_decision`, `decision_owner`, `methodology_risks`, `coverage_thresholds`, `enabled_fields_with_rationale`, `sample_plan`, `static_baseline_failure`, and `assumptions`. Add tests that reject generic briefs with no decision target or methodology-risk section.

5. **Major - The integration tests would either call live Gemini in normal pytest or pass on raw invalid JSON.**

   Task 5 creates a test that polls up to 60 seconds and says it requires Gemini credentials (`docs/superpowers/plans/2026-05-15-a2a-discovery-agent.md:968-1014`), but it still lives under normal `tests/` and is invoked with pytest. It also accepts `raw_output` as equivalent to a structured brief (`docs/superpowers/plans/2026-05-15-a2a-discovery-agent.md:988-992`), which means malformed discovery output can pass the key integration test.

   Fix: mark live tests explicitly, skip unless credentials are present, and add mocked integration tests for CI. Treat `raw_output` as failure for discovery unless the specific test is checking error handling.

6. **Minor - The plan file and current checkout appear partially out of sync.**

   The task is framed as a plan review, but `methodic/a2a.py`, `methodic/agents/discovery.py`, `tests/test_a2a.py`, `tests/test_discovery.py`, and the updated `AGENT_CARD` already exist in the checkout. This does not invalidate the plan review, but it increases implementation risk because reviewers may think they are approving future work while some plan choices are already live.

   Fix: add a short “current implementation status” section to the plan or split the next artifact into “review of plan” and “review of existing implementation.”

## Falsifiable Assumptions

1. The target protocol is current A2A v0.3.x or at least v0.2.6, not an intentionally older `tasks/send`-era draft.
2. The submission will claim A2A interoperability, not merely “A2A-inspired HTTP endpoints.”
3. Judges or reviewers may inspect the agent card and attempt to call the service with an A2A client or JSON-RPC request.
4. The discovery agent is expected to strengthen the Methodic thesis, not simply generate generic study JSON.
5. Normal CI should not require live Gemini calls unless tests are explicitly marked and skipped without credentials.

## Verdict

**rewrite.** The idea is strategically valuable, but the implementation plan must be rewritten around the actual A2A JSON-RPC contract before execution. As written, it risks producing a demo that says “A2A” while exposing custom REST endpoints and custom task objects, which is exactly the kind of overclaim the project strategy warns against.

## Sources

- A2A v0.3.0 specification: JSON-RPC requests/responses, core methods, Agent Card requirements, and Task object semantics.
- A2A v0.2.6 specification cross-check: same JSON-RPC requirement and task/message method split.
