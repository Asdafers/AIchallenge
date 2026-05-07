# Deployment Architecture Decision: Target Platform First

Date: 2026-05-06
Status: REVISED - Agent Platform target, Cloud Run fallback/proving ground

## Decision

The current repo and Cloud Run demo work are a proving ground for ideas. They helped explore the product concept, agent graph, data-quality story, MCP touchpoints, BigQuery export, and judge-facing before/after demo.

The submission should now target the challenge-recommended tools and platforms first:

- ADK-native agent architecture
- Agent Runtime / Agent Platform as the preferred deployed agent environment
- Agents CLI as a source of scaffold, IAM, CI/CD, and infrastructure conventions
- MCP tool integration through an ADK/Agent Platform-compatible path
- Sessions/state through Agent Platform-compatible services where practical
- Observability/tracing as demo evidence
- Lightweight evaluation/trajectory proof
- BigQuery export as the analysis-ready data destination
- A simple frontend only where needed to show the before/after judge story

Cloud Run is not the default core deployment choice anymore. It remains valid as:

1. a temporary proving-ground runtime,
2. a thin frontend/proxy for a deployed Agent Runtime agent, or
3. a fallback if Agent Runtime fails on a documented hard blocker.

## Why

The Google for Startups AI Agents Challenge guidance points builders toward ADK, MCP, Agents CLI, Agent Platform documentation, Agent Runtime, sessions/memory, observability, evaluation, and a clear before/after demo.

The submission should demonstrate that Methodic belongs on that stack. Preserving exploratory FastAPI routes is less important than aligning with the target tools and platform expectations.

## Target Architecture

```text
Judge / demo viewer
  |
  v
Simple demo UI or Cloud Console view
  |
  v
Agent Runtime / Agent Platform
  |
  +-- Methodic ADK root_agent
  |   +-- organizer / methodology / question design agents
  |   +-- participant fieldwork loop
  |   +-- MCP-backed context/tool calls
  |   +-- structured extraction
  |   +-- coverage and quality scoring
  |   +-- re-plan decision
  |   +-- BigQuery export
  |
  +-- Session/state service where practical
  +-- Observability / trace evidence
  +-- Evaluation / trajectory artifact
  |
  v
BigQuery: analysis-ready output
```

If Agent Runtime cannot support the required MCP or custom ADK graph quickly enough, fallback architecture is:

```text
Judge browser
  |
  v
Cloud Run demo shell
  |
  +-- Methodic ADK runtime
  +-- MCP subprocess or compatible in-process adapter
  +-- Vertex AI Gemini routing
  +-- BigQuery export
  +-- Cloud Logging/trace evidence
```

Fallback must be labeled honestly as a demo deployment constraint, not as the ideal architecture.

## Immediate Gate

Before further Cloud Run hardening, run a capped Agent Platform feasibility spike:

1. Use the existing `methodic/agent.py` and `root_agent` as the candidate core.
2. Run an Agent Runtime deployment attempt in the dedicated GCP project.
3. Exercise session creation and streamed query.
4. Verify whether custom `BaseAgent` steps run.
5. Verify whether MCP tool access can work in the deployed runtime.
6. Record exact blocker evidence if it fails.

In parallel or immediately after, run Agents CLI in a scratch folder:

1. Inspect recommended project layout.
2. Inspect generated IAM/deployment/evaluation/observability conventions.
3. Port only useful conventions back into this repo.

## Build Rule

Any software built from here must answer:

1. Does it move the submission closer to ADK/Agent Platform alignment?
2. Does it make the before/after data-quality improvement visible?
3. Does it produce judge-facing proof: trace, trajectory, MCP call, BigQuery row, or deployed URL?
4. Does it avoid turning the project into a generic survey chatbot?

If the answer is no, it should wait.

## Required Proof Checklist

- [ ] Agent Runtime feasibility spike completed with evidence.
- [ ] Agents CLI scratch comparison completed.
- [ ] Final deployment target chosen from evidence, not current-code inertia.
- [ ] ADK `root_agent` remains the canonical agent entry point.
- [ ] MCP tool path works in the chosen runtime or fallback is documented.
- [ ] Gemini runs through the chosen Google platform path.
- [ ] Session/state approach is explicit and honestly labeled.
- [ ] Observability or trace evidence exists.
- [ ] Trajectory/evaluation artifact exists.
- [ ] BigQuery export writes at least one real row or a clearly labeled dry-run artifact if live write is blocked.
- [ ] Demo shows before/after data-quality improvement.
- [ ] Submission docs explain why the platform choice matches the challenge guidance.

## Superseded Decision

The prior "Cloud Run with Vertex AI routing" decision is superseded. Cloud Run can still be used, but only after the Agent Runtime path is proven infeasible or as a thin support layer around the target platform.
