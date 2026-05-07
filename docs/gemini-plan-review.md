# Gemini Plan Review: Methodic ADK Agent

**Reviewer:** gemini-2026-05-04T2100-REVIEW
**Task ID:** 544f2f31-8772-4a95-b148-f41b3a9bdab1

## Document 1: Design Spec
**Path:** `docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md`

### Findings
*   **[MINOR] ADK Agent Imports & Capabilities:** The imports and use of `SequentialAgent`, `LoopAgent`, and `ParallelAgent` match ADK's composition patterns. However, the exact import paths may vary slightly depending on the specific ADK version (e.g., standard ADK uses `google.adk.agents.SequentialAgent`).
*   **[MAJOR] A2A + FastAPI Composition:** The `to_a2a()` and `get_fast_api_app()` composition strategy is identified correctly as a potential gotcha. Mounting an A2A ASGI app under `/a2a` can break the `/.well-known/agent.json` discovery endpoint, requiring a proxy route as noted. This is a known ADK edge case.
*   **[MAJOR] Missing Definitions:** The spec references `turn_checker` as a `FunctionTool` responsible for breaking out of the `interview_loop` (escalation), but its exact mechanism of observing the conversation state is vaguely defined.
*   **[MINOR] Latency Estimates:** A 6-turn loop with 3 LLM calls per turn (Interviewer, Sim, Extractor) results in ~18 sequential LLM calls per participant. Across 3 participants sequentially, this could take 3-5 minutes, pushing dangerously close to default Cloud Run timeouts (5 mins). Using `MODEL_FAST` for the simulation is a good mitigation, but concurrency should be prioritized.

---

## Document 2: Implementation Plan
**Path:** `docs/superpowers/plans/2026-05-04-methodic-adk-agent.md`

### Findings
*   **[BLOCKER] Missing `turn_checker` Agent/Tool:** The design spec explicitly states that `turn_checker` is a `FunctionTool` in the `interview_loop` responsible for triggering loop exit (`tool_context.actions.escalate = True`). This tool is completely missing from the implementation plan tasks. Without it, the `interview_loop` will always hit its `max_iterations`.
*   **[BLOCKER] Tool Wiring / Orphaned Tools:** Task 6 creates `extract_structured_fields` and Task 7 creates `export_to_bigquery`. However, in Task 15 (`methodic/agent.py`), these tools are **never added** to the agent graph. `interview_loop` only contains `[interviewer_agent, participant_sim_agent]`, and `finalize` only contains `[quality_agent, completion_responder]`.
*   **[MAJOR] Replanner Tool Access:** In Task 14, the `replanner_agent` is defined without any `tools=[...]` argument. The spec explicitly states the Replanner uses `check_coverage` to decide whether to add participants. It cannot do this if the tool is not attached.
*   **[NOTE] Pydantic Schemas:** The Pydantic schemas in Task 2 excellently mirror the canonical JSON schema. Field names, enums, and required properties match perfectly.
*   **[NOTE] Test Assertions:** The tests in the plan are very well structured. Testing agent definition wiring (e.g., `output_key` correctness, instance checking) instead of mocking LLM behavior is the correct approach for this level of unit testing.
*   **[NOTE] MCP Extension:** Task 3 correctly follows the existing `wp6_mcp_server.py` patterns, extending both `list_tools` and `call_tool` while preserving the delay logic.

---

## Verdict
**REVISE_REQUIRED**

The implementation plan has critical gaps. Specifically, the tools created in Tasks 4, 6, and 7 are orphaned and never wired into the `root_agent` in Task 15. Furthermore, the `turn_checker` logic required to safely exit the interview loop is missing. The plan must be revised to include tool attachment and the missing `turn_checker` component before execution.