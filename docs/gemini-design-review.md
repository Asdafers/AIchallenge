# Gemini Design Review: Methodic ADK Agent

**Date:** May 4, 2026
**Reviewer:** Gemini

This is a review of the Methodic ADK Agent design specification (`docs/superpowers/specs/2026-05-04-methodic-adk-agent-design.md`) based on the requested claims to verify.

## 1. ADK Agent Graph Nesting
**Finding:** The nesting depth (Sequential → Loop → Parallel → Loop) is theoretically possible in most agent frameworks, but introduces significant complexity in state management and error handling.
*   **Issues to Investigate:**
    *   **State propagation across boundaries:** Ensuring `InvocationContext` flows correctly up and down the deeply nested graph (e.g., from the inner `interview_loop` back up to the `fieldwork_loop` and `replanner`).
    *   **Escalation bubbling:** If an inner `turn_checker` triggers an escalation, you must ensure it halts the specific `interview_loop` without accidentally terminating the parent `ParallelAgent` or the entire `fieldwork_loop` prematurely. The exact behavior of `tool_context.actions.escalate = True` within a parallel loop needs testing.

## 2. Model Choice (`gemini-3.1-pro-preview`)
**Finding:** Relying exclusively on a `-preview` model for a hard deadline (June 5) presents a stability risk.
*   **Issues to Investigate:**
    *   Preview models are subject to unannounced updates, rate limits, or transient downtime. 
    *   **Recommendation:** Define a stable fallback model (e.g., `gemini-3.0-pro` or the current stable equivalent) in the configuration, not just another preview (`flash-lite-preview`) for latency.

## 3. MCP via McpToolset (Stdio in Cloud Run)
**Finding:** Running an MCP server via stdio (subprocess) inside a Cloud Run container will work functionally.
*   **Details:** Cloud Run provides a standard Linux container environment. Spawning a subprocess and communicating over its stdin/stdout is fully supported; there is no restriction preventing this.
*   **Issues to Investigate:**
    *   **Resource Limits:** Each MCP server instance spawns a new Python process. Since `interview_loop` instances run in parallel, multiple stdio subprocesses could be spawned simultaneously. Ensure the Cloud Run container is provisioned with sufficient CPU and memory (e.g., 2+ vCPUs, 1+ GB RAM) to handle `N` concurrent Python subprocesses without thrashing.

## 4. A2A + FastAPI Composition
**Finding:** Mounting an ASGI app (`to_a2a()`) onto a FastAPI app using `app.mount()` is supported in the ASGI specification and by FastAPI.
*   **Details:** `app.mount("/a2a", a2a_app)` correctly isolates the mounted app.
*   **Issues to Investigate:**
    *   **Root pathing:** The A2A app expects to serve its Agent Card at `/.well-known/agent.json`. If mounted under `/a2a`, the card becomes `/a2a/.well-known/agent.json`. As astutely noted in the spec, a manual proxy route on the main FastAPI app (`/.well-known/agent.json` -> `/a2a/.well-known/agent.json`) will be necessary to resolve the root well-known path for discovery.
    *   The proposed fallback (separate ports behind a proxy) is a solid Plan B if ASGI lifecycle events clash.

## 5. Interview Loop Latency
**Finding:** The latency for the `interview_loop` is a major concern for a live synchronous demo.
*   **Details:** The loop has up to 12 iterations. Each iteration involves up to 3 LLM calls: `interviewer` (LlmAgent), `participant_sim` (LlmAgent), and `extractor` (FunctionTool internally calling Gemini).
    *   Total LLM calls per participant = up to 36.
    *   Even at an optimistic 2 seconds per call, a full 12-turn loop will take over a minute to complete.
*   **Issues to Investigate:**
    *   While `ParallelAgent` handles multiple participants simultaneously, a single participant's loop is strictly sequential.
    *   **Recommendation:** Lower `max_iterations` for the demo (e.g., 5-6) or aggressively use `gemini-3.1-flash` for the `participant_sim` and `extractor` to keep turn latency manageable for human observers.

## 6. Structured Output via `response_schema`
**Finding:** `gemini-3.1-pro-preview` fully supports structured outputs (JSON schema) via `response_schema` natively.
*   **Details:** Passing a JSON schema (derived from Pydantic) to the model's generation config is the correct, supported, and most reliable approach for extraction.
*   **Issues to Investigate:**
    *   Ensure the schema strictly defines required fields and uses `enum` lists as specified in the canonical JSON schemas. Structured output performs best when the schema is tightly constrained.