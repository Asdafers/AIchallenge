# Limitations and Honest Labels

Methodic is a vertical-slice prototype for the Google AI Agent Challenge. This document states what it proves and what it does not.

## What the Prototype Proves

1. **End-to-end ADK agent pipeline** — SequentialAgent + LoopAgent graph with 7 LlmAgents and 6 custom BaseAgent steps, running on Cloud Run with live Gemini 3.1 Pro.
2. **Real MCP boundary** — `lookup_deal_context` and `lookup_trial_telemetry` run through a stdio JSON-RPC 2.0 MCP server with server-side field filtering.
3. **Interactive + demo modes** — SSE-streaming web UI for both automated demo and human-in-the-loop interviews.
4. **Measurable quality delta** — Fixture benchmark shows +0.692 composite improvement (static 0.069 → Methodic 0.761) across 4-dimension rubric.
5. **Autonomous re-plan** — Replanner calls Gemini to assess coverage gaps and decides whether to add a targeted follow-up session.
6. **Cloud Run deployment** — Live at the submitted URL with Vertex AI authentication.

## What the Prototype Does Not Prove

### In-Memory Sessions Only
Sessions use ADK `InMemorySessionService`. Study state does not persist across server restarts. A production build would use durable session storage.

### Fixture-Backed MCP Tools
The MCP server reads CRM and telemetry data from local JSON fixtures (`fixtures/crm/`, `fixtures/telemetry/`), not a live CRM or analytics system. The MCP boundary and field filtering are real; the data source is not.

### BigQuery Export Mode
BigQuery export defaults to dry-run (`BIGQUERY_DRY_RUN=true`) unless explicitly configured with GCP credentials. The schema, flattening logic, and table creation path are production-ready; live writes require IAM setup.

### Simulated Participants (Demo Mode)
Demo mode uses `participant_sim`, a Gemini-powered LLM agent that role-plays as a B2B stakeholder. Interactive mode accepts real human input. Neither mode uses actual research participants.

### Fixture Benchmark Quality Delta
The +0.692 quality improvement is computed from fixture participant data using a self-defined 4-dimension rubric (variable coverage, ambiguity resolution, evidence linkage, recontact need). It demonstrates rubric mechanics on n=3+1 participants, not a peer-reviewed finding.

### A2A Pattern Only
The server exposes an A2A 1.0-shaped agent card at `/.well-known/agent-card.json` but does not implement the full A2A protocol. Inbound study requests are handled via REST API, not A2A message exchange.

## Honest Label Policy
Every limitation listed here is a deliberate scope cut for a prototype. Over-claiming would undermine trust in the submission.
