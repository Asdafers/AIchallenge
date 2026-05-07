# Codex ADK Deployment Review: Agent Runtime vs Cloud Run

Date: 2026-05-06
Task: bd07383d-38ad-4dc6-9827-1c399615d420
Reviewer: codex-2026-05-06T1606-bd07
Verdict: REVISE_REQUIRED

## Correction

This supersedes the first pass of this review. The first pass overweighted the current exploratory implementation and treated the existing Cloud Run/FastAPI demo as something to preserve. That is the wrong frame.

The work so far should be treated as concept exploration and risk discovery. The build should now align with the challenge guidance and judging goals first. Existing code is useful only where it accelerates that target architecture.

## Sources Checked

- `docs/ai-agents-challenge-resource-guide.md`
- `docs/live-demo-deployment-design.md`
- `docs/deployment-architecture-decision.md`
- `methodic/server.py`
- `methodic/demo_runner.py`
- `methodic/agent.py`
- `Dockerfile`
- ADK docs: [Deployment options](https://adk.dev/deploy/), [Cloud Run deployment](https://adk.dev/deploy/cloud-run/), [Agent Runtime deployment](https://adk.dev/deploy/agent-runtime/), [Agent Runtime standard deployment](https://adk.dev/deploy/agent-runtime/deploy/), [Agents CLI deployment](https://adk.dev/deploy/agent-runtime/agents-cli/), [Agent Runtime testing](https://adk.dev/deploy/agent-runtime/test/), [Sessions and memory](https://adk.dev/sessions/), [Evaluation](https://adk.dev/evaluate/), [Observability](https://adk.dev/observability/)

## Strategy Linkage

This review links to `mission_strategy['aichallenge'].stack_alignment`, `demo_must_show`, and the product thesis: no reliable insights without good data capture. The deployment architecture should maximize Google-agent-stack credibility while showing a business user that Methodic turns a decision brief into governed, evidence-linked, analysis-ready data.

## Challenge-Aligned Target

The challenge resource guide points Track 1 builders toward ADK, MCP, Agents CLI, Agent Platform documentation, and a clear before/after demo. It also points reliability/deployment work toward Agent Runtime, observability, evaluation, sessions, and memory.

Therefore the default build target should be:

1. ADK-native agent package with `root_agent` as the source of truth.
2. Agent Runtime as the primary deployed agent environment unless a same-day spike proves a hard blocker.
3. Agents CLI used in a scratch branch or clean scaffold to inspect the recommended project shape, CI/CD, IAM, and Terraform patterns.
4. MCP used through the ADK/MCP tool path, not merely as a local subprocess detail hidden in a custom server.
5. Sessions/state handled through Agent Platform-compatible services where practical, not in-memory state as the planned deployment model.
6. Observability and trajectory evidence captured as part of the demo proof.
7. A simple frontend only where it improves the judge story; it should consume the deployed agent, not define the architecture.

Cloud Run remains valid in two roles:

- As a thin frontend/demo shell that calls the Agent Runtime agent.
- As a fallback deployment target only if Agent Runtime cannot run the required MCP/ADK graph within the available time.

## Findings

### Finding 1 - BLOCKER - The current deployment decision is anchored to exploratory code, not the challenge target

`docs/deployment-architecture-decision.md` currently decides Cloud Run first and then adopts selected Agent Runtime practices. That reverses the right priority. The challenge advice explicitly elevates Agent Runtime, Agents CLI, sessions/memory, observability, and evaluation. If the final software skips those mainly because the current FastAPI demo is convenient, we risk building around yesterday's exploration rather than the competition's strongest path.

Mitigation:

- Replace "Cloud Run with Vertex AI routing" as the decided architecture with a two-track decision gate:
  - Track A, preferred: Agent Runtime core agent plus optional thin frontend.
  - Track B, fallback: Cloud Run-only deployment if Agent Runtime spike fails on a documented blocker.
- Run the Agent Runtime spike before further UI or Cloud Run hardening.
- Treat current FastAPI routes as disposable adapters unless they align with the Agent Runtime target.

### Finding 2 - BLOCKER - Agent Runtime feasibility must be proven or falsified immediately

The question is not whether Cloud Run can host the current app. It probably can. The question is whether Methodic can be submitted as a more Google-native ADK agent with Agent Runtime, managed sessions, observability, and a cleaner story.

Mitigation: run a capped same-day spike:

1. Create a clean scratch branch or temp directory.
2. Use the existing `methodic/agent.py` package as the candidate ADK app.
3. Run `adk deploy agent_engine` or the current Agent Runtime command path against the dedicated project.
4. Exercise create-session and stream-query through the Agent Runtime API.
5. Verify whether MCP tool wiring and custom `BaseAgent` steps survive deployment.
6. Record exact errors if deployment fails.

If this fails on MCP serialization, subprocess packaging, auth, or unsupported custom agent behavior, then Cloud Run fallback is justified. Without this proof, choosing Cloud Run is premature.

### Finding 3 - MAJOR - Agents CLI should inform the repo shape before implementation proceeds

Agents CLI should not be run destructively over the current repo, but it should be used now in a scratch area. The guide calls it out as a bootstrap path for production-ready templates, CI/CD, and infrastructure. That is exactly the kind of signal judges may expect from a serious Google-agent-stack submission.

Mitigation:

- Run Agents CLI in a scratch folder.
- Compare its expected structure against `methodic/`.
- Pull back only the useful conventions:
  - project layout
  - deployment config
  - IAM/service account shape
  - evaluation/observability hooks
  - README/deployment proof format
- Do not import scaffold churn unless it directly supports the final architecture.

### Finding 4 - MAJOR - The custom frontend should be demoted from architecture driver to demo layer

The before/after demo matters, but it should not dictate runtime architecture. The guide says the demo video should clearly highlight before and after; it does not require the core agent to be a custom FastAPI app.

Mitigation:

- Keep the visual before/after UI as a judge-story layer.
- Make it call the deployed Agent Runtime agent if feasible.
- If Agent Runtime does not provide a public browser-friendly API suitable for the demo, use Cloud Run only as a thin frontend/proxy that calls Agent Runtime.
- If even that is too slow, document the blocker and use Cloud Run as fallback.

### Finding 5 - MAJOR - In-memory state should not be the planned hosted architecture

`_demo_sessions` and `InMemorySessionService` were acceptable for exploration. They should not be the planned deployment state if Agent Platform sessions are available and compatible. The challenge advice specifically points toward sessions/runtime/memory for reliability work.

Mitigation:

- Prefer Agent Runtime session APIs for the deployed agent path.
- Use memory only if it supports the research workflow; do not add Memory Bank for decoration.
- If Cloud Run fallback is used, keep `--max-instances=1` and label it as a fallback demo constraint, not the intended architecture.

### Finding 6 - MAJOR - Observability and evaluation should be first-class proof, not optional polish

For this concept, "agentic" has to be visible: methodology pushback, MCP lookup, participant probing, extraction, coverage scoring, re-plan, export. ADK evaluation and observability map directly to this proof. Treating them as later extras weakens the technical story.

Mitigation:

- Capture at least one trajectory/evaluation artifact showing expected vs actual tool/agent steps.
- Capture trace/log proof from the deployed environment.
- Include these artifacts in the demo package and video script.

### Finding 7 - MINOR - Model routing should follow the chosen Google runtime

If Agent Runtime works, use the runtime's recommended model configuration and IAM path. If Cloud Run fallback is used, route Gemini through Vertex AI using `GOOGLE_GENAI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_CLOUD_LOCATION` if smoke tests pass.

Mitigation:

- Avoid centering the final plan on AI Studio API-key routing.
- Use Secret Manager only where an API key remains necessary.

## Direct Answers

1. **Should we use Agent Runtime instead of raw Cloud Run?** Yes, Agent Runtime should be the preferred target until a fast spike proves it cannot run Methodic's ADK/MCP graph. Cloud Run should be fallback or frontend/proxy, not the default core runtime.
2. **Should we use Agents CLI?** Yes, but in a scratch area first. Use it to learn the recommended scaffold and deployment/IAM/evaluation patterns, then selectively port conventions.
3. **Are we missing Agent Platform features?** Yes. Sessions, observability, and at least lightweight evaluation should be treated as core proof. Memory Bank is optional and should be added only if it supports a real cross-session research use case.
4. **Does `get_fast_api_app()` plus custom routes align?** It is acceptable for Cloud Run and useful for exploration, but it should not be the target architecture if Agent Runtime works.
5. **Model routing concerns?** Use the model path recommended by the chosen Google runtime. Prefer Vertex AI/IAM over consumer API-key routing for the final submission story.

## Falsifiable Assumptions

1. Agent Runtime can deploy the existing ADK `root_agent` or a modestly adapted version without rewriting the whole system.
2. Methodic's MCP tool path can work in Agent Runtime, or can be adapted to an Agent Platform-compatible MCP/OpenAPI tool path in time.
3. A thin frontend can call Agent Runtime directly or through a small proxy without consuming more time than a Cloud Run-only fallback saves.
4. Agent Platform sessions/observability/evaluation create stronger judge evidence than preserving the current in-memory FastAPI demo flow.
5. The challenge judges reward alignment with ADK/Agent Platform guidance enough to justify a same-day architecture spike.

## Verdict

**REVISE_REQUIRED.**

Do not proceed with Cloud Run-only deployment as the default. The next step should be an Agent Runtime and Agents CLI feasibility spike, capped tightly and judged by concrete deployment evidence.

Recommended approach:

1. Run Agent Runtime spike using the existing `methodic/agent.py` as the core.
2. Run Agents CLI in a scratch folder and harvest useful conventions.
3. Decide architecture from evidence:
   - If Agent Runtime works: use it as the core deployed agent; add simple frontend/proxy only as needed for the before/after demo.
   - If Agent Runtime fails on a documented blocker: use Cloud Run fallback with Vertex AI routing, observability, `--max-instances=1`, and honest labeling.
4. Make sessions, observability, evaluation, MCP, and before/after demo evidence part of the required proof checklist.
