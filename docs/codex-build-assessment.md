# Codex Build Assessment: Real Methodic Agent Path

Date: 2026-05-04
Task: b2d300f9-279d-465f-a679-635bdda6e709
Status: Independent build recommendation for the 32-day submission window

## Executive Verdict

Claude's assessment is directionally correct: the repository is a strong fixture-driven proof package, not yet a real agent system. The current code proves the intended demo beats with deterministic artifacts, one real MCP boundary, a local HTTP demo server, and dry-run BigQuery setup. It does not yet prove live multi-agent orchestration, live participant conversation, model-based extraction, production A2A interoperability, Cloud Run deployment, or real BigQuery writes.

My recommendation is to build a narrow real vertical slice on ADK plus Gemini, reuse the existing fixtures as regression cases, keep the existing scripts as deterministic fallback and demo evidence generators, and rewrite only the runtime path that judges will inspect as "the agent." The real build should prioritize one live organizer/methodology pass, one live participant interview with MCP context lookup, deterministic quality scoring, Cloud Run, and BigQuery export. Full production A2A compliance is not necessary for Track 1 unless it lands cheaply through ADK's A2A support.

Strategy linkage: this plan serves `mission_strategy['aichallenge'].stack_alignment` by using Gemini, ADK, MCP, and Cloud Run/BigQuery; it serves `vertical_slice` by focusing on Organizer AI, Participant AI, and Data Quality Layer; and it serves `demo_must_show` by making methodology pushback, interactive participant conversations, and measurable data quality improvement real rather than fixture-only.

## Current Codebase Assessment

### What Exists And Should Be Valued

The repo has a coherent demo spine:

- `docs/spec.md` defines the judging story, Track 1 positioning, five proof beats, schemas, metrics, and explicit scope cuts.
- `scripts/validate_schemas.py` and `scripts/validate_fixtures.py` enforce the canonical participant response, guardrail event, fixture, and BigQuery row contracts.
- `scripts/wp3_organizer_flow.py` demonstrates an A2A-pattern request, clarification, organizer brief, and approval flow from fixtures.
- `scripts/wp4_methodology_review.py` has the only live-model path, via Gemini CLI ACP, with deterministic fallback.
- `scripts/wp5_conversation_engine.py` demonstrates the participant pipeline, but explicitly uses deterministic fixture replay and fixture ground-truth extraction.
- `scripts/wp6_mcp_server.py` and `scripts/wp6_mcp_boundary.py` implement a real MCP stdio boundary for `lookup_deal_context`.
- `scripts/wp7_data_quality.py` scores Methodic versus static baseline with an honest note that scores are fixture-derived.
- `scripts/wp8_replan_trigger.py` implements the visible autonomous re-plan beat from fixture coverage state.
- `scripts/wp9_demo_server.py`, `scripts/wp9_deployment_smoke.py`, `Dockerfile`, and `scripts/wp9a_bigquery_export.py` provide a local demo service and dry-run or credential-dependent deployment/export path.

This is useful because it already encodes the product logic, schema, demo storyline, and quality rubric. It is not throwaway work.

### What Is Still Missing For A Real Build

The missing pieces are the exact pieces judges are likely to probe:

- No ADK runtime or `google-adk` dependency exists in `requirements.txt`.
- No real ADK `SequentialAgent`, `ParallelAgent`, or `LoopAgent` orchestrates the workflow.
- No participant conversation engine calls Gemini for interviewer turns.
- No Gemini structured-output extraction replaces persona `expected_response` fixture ground truth.
- No real tool call is made by an LLM-driven participant agent during the conversation path; WP5 simulates it and WP6 verifies the boundary separately.
- No deployable A2A server endpoint exists; WP3 is an honestly labeled fixture stub.
- No Cloud Run deployment artifact proves a public URL.
- No mandatory real BigQuery write has been verified; WP9a can attempt one, but the trace remains dry-run unless credentials and env vars are configured.
- No frontend currently presents the working experience.

## Agreement And Disagreement With Claude

I agree with Claude on the core diagnosis: the current system is fixture replay with one real MCP boundary, and the conversation engine is the critical path.

I agree that ADK + Gemini should be started immediately, but I would make one important scope adjustment: do not try to make the entire WP3-WP9 pipeline "real" at once. Build a new runtime path that uses ADK/Gemini for the judge-visible agent behaviors, then feed its outputs into the existing validators, quality scorer, demo server, and export path.

I partially disagree with the implied need for a fully real A2A implementation in Week 2. For Track 1, the challenge material allows ADK or supported frameworks plus MCP, Gemini, and Google Cloud deployment; the repo itself says full A2A compliance should be cut unless straightforward. Current ADK docs list A2A support as experimental for Python/Go/Java, so the honest plan is an A2A-pattern endpoint with an Agent Card-shaped metadata route unless the ADK quickstart path is easy within 1-2 days.

I also disagree that BigQuery is "plumbing" in the judging context. It is easy engineering, but it is high demo value because Methodic's thesis is governed data capture. A live BigQuery row write is one of the clearest proofs that the agent produces analysis-ready data rather than a chat transcript.

## Current Google Stack Findings

Sources checked on 2026-05-04:

- ADK docs define `LlmAgent` for reasoning, workflow agents for deterministic orchestration, and built-in `SequentialAgent`, `ParallelAgent`, and `LoopAgent` patterns: https://adk.dev/get-started/about/ and https://adk.dev/agents/multi-agents/
- ADK installation is still `pip install google-adk`: https://adk.dev/get-started/installation/
- ADK docs show `SequentialAgent` with `output_key` state handoff and examples using `gemini-2.5-flash`: https://adk.dev/agents/workflow-agents/sequential-agents/
- ADK has a documented MCP bridge through `McpToolset`, including stdio MCP servers and deployment caveats for Cloud Run/GKE: https://adk.dev/tools-custom/mcp-tools/
- Gemini model docs currently list `gemini-2.5-flash` as best price-performance for low-latency reasoning and `gemini-2.5-pro` as the advanced complex reasoning model; `gemini-2.0-flash` is deprecated, and `Gemini 3 Pro Preview` was shut down March 9, 2026: https://ai.google.dev/gemini-api/docs/models
- Gemini structured outputs support JSON Schema for data extraction and classification; docs still require application validation because schema-compliant values can be semantically wrong: https://ai.google.dev/gemini-api/docs/structured-output
- ADK documents A2A support but labels it experimental for Python/Go/Java: https://adk.dev/a2a/
- A2A latest specification is 1.0.0 and defines discovery, task management, HTTP/JSON-RPC/REST bindings, Agent Cards, and streaming, with `.well-known/agent-card.json` as the well-known discovery URI: https://a2a-protocol.org/latest/specification/

## Recommended Tech Stack

Use ADK, not LangChain, as the primary orchestration layer.

Reason:

- The challenge explicitly rewards Google-aligned architecture.
- ADK directly maps to the spec's planned `SequentialAgent`, `ParallelAgent`, and `LoopAgent` proof.
- ADK has official MCP integration through `McpToolset`, which lets the existing WP6 MCP server become a real tool for the participant agent.
- ADK's A2A support gives an upgrade path if full A2A is feasible.

Use the Gemini API through the current Google GenAI/ADK path, not Gemini CLI ACP, for the production runtime. Keep ACP only as a reviewer/automation convenience.

Recommended model split:

- `gemini-2.5-flash` for participant interviewer turns, guardrail handling, and routine extraction. It is stable, low-latency, and supports structured outputs.
- `gemini-2.5-pro` for methodology critique, question-pool revision, final caveat generation, and any contradiction/theme review. Use it sparingly.
- Avoid `gemini-2.0-flash` because the model page marks it deprecated.
- Avoid building the core demo on preview-only 3.x models. They can be optional experiments, not the submission dependency.

Use FastAPI or the ADK runtime server for the external HTTP surface. If ADK's A2A exposing quickstart works quickly, expose a compliant minimal A2A endpoint. Otherwise expose:

- `GET /.well-known/agent-card.json`
- `POST /a2a/message`
- `POST /demo/run`
- `GET /demo/{study_id}`

Label this as "A2A-pattern prototype" in the UI and README unless it passes a real A2A client smoke test.

Use BigQuery through `google-cloud-bigquery` with a real service account and dataset-scoped IAM. Do not leave this as dry-run for submission.

## Recommended Runtime Architecture

### Runtime Modules To Add

Create a new runtime package instead of mutating every WP script:

- `methodic/agents/organizer.py`
- `methodic/agents/methodology.py`
- `methodic/agents/question_design.py`
- `methodic/agents/participant.py`
- `methodic/agents/quality.py`
- `methodic/agents/orchestrator.py`
- `methodic/tools/context_mcp.py`
- `methodic/export/bigquery.py`
- `methodic/server.py`
- `methodic/schemas.py`

Keep `scripts/` as fixtures, validation, and legacy demo harness until the real runtime is stable.

### ADK Shape

Use a deterministic outer workflow with LLM agents inside:

1. `SequentialAgent`: Organizer -> Methodology -> Question Design -> Approval Package.
2. `ParallelAgent`: run participant sessions for P-001/P-002/P-003. For the first live demo, only one needs to be truly live while the others can be marked as recorded live traces generated by the same engine.
3. `LoopAgent` or bounded custom agent: check coverage after primary sessions, trigger exactly one reserve participant when `procurement_friction` remains ambiguous, then stop.
4. Data Quality Agent: mostly deterministic scorer using the current WP7 rules, with optional Gemini review for contradictions and theme labels.
5. Export Agent: writes JSON/CSV plus BigQuery rows and returns a structured completion response.

### Conversation Engine

The participant conversation engine should be the first real rewrite.

Minimum viable behavior:

- Input: approved study brief, question pool, participant persona metadata, allowed MCP fields, required variables, stop thresholds.
- At each turn, Gemini chooses the next interviewer question or a tool call intent.
- If a context lookup is justified, the agent calls `lookup_deal_context` through ADK `McpToolset`, not by directly reading fixture files.
- Gemini produces a participant-facing follow-up that references only approved context summaries.
- After each answer, Gemini emits structured extraction with `structured_fields`, `field_confidence`, `coverage_state`, `evidence`, `unresolved_ambiguities`, and `guardrail_events`.
- Application code validates the structured output against `docs/schema/participant-response.schema.json` or a matching Pydantic model.
- Deterministic policy decides whether to ask another question, stop that variable, or stop the participant session.

For demo reliability, participant responses can still be simulated from persona fixtures. The key is that the interviewer, extraction, tool-use decision, and coverage update are live. That honestly proves the agent while controlling participant variance.

### Data Quality Layer

Keep WP7's scoring weights initially:

- Coverage: 0.30
- Confidence: 0.25
- Ambiguity resolution: 0.25
- Evidence link: 0.20

Change the claim language:

- Good: "This live Methodic run produced higher coverage and evidence linkage than the static reference path on the same personas."
- Bad: "Methodic statistically improves survey quality."

Add one test that feeds a live participant output into the existing WP7 scorer and fails if any required field is missing from the export row.

## Minimum Viable Submission Scope

The minimum viable submission should prove one complete vertical slice:

1. External Sales Insights agent request arrives through an HTTP/A2A-pattern endpoint.
2. Methodic asks one clarifying question.
3. Organizer and Methodology agents create and critique the plan with live Gemini.
4. Participant Agent runs at least one live Gemini interview turn sequence with real MCP context lookup.
5. Structured extraction uses Gemini structured output and local validation.
6. Coverage loop triggers the reserve participant based on deterministic quality state.
7. Data quality view compares static baseline versus Methodic.
8. BigQuery receives at least one real quality/export row.
9. Cloud Run hosts the demo endpoint and UI.
10. Demo UI shows the event timeline, tool call, coverage states, re-plan decision, and export proof.

This scope addresses all judging criteria:

- Technical Implementation 30%: ADK orchestration, Gemini structured output, MCP tool call, Cloud Run, BigQuery, A2A-pattern endpoint.
- Business Case 30%: B2B SaaS win-loss wedge, direct revenue decision, Head of Research Ops buyer, analysis-ready dataset.
- Innovation 20%: methodology pushback, coverage-driven stop/re-plan, governed data capture instead of static survey collection.
- Demo 20%: split-screen static versus Methodic, visible agent events, measurable quality delta, live export.

## What To Keep

Keep:

- `docs/spec.md` as the source of product truth.
- All schemas under `docs/schema/`.
- Fixture personas, CRM, telemetry, static baseline, and expected outputs.
- WP validators and quality scorer.
- WP6 MCP server, but wrap it for ADK use.
- WP8 re-plan logic as deterministic policy.
- WP9 demo server ideas and trace shape, though the UI/server should be modernized.
- `docs/build-real-agent-assessment.md` as Claude's prior review.

## What To Rewrite

Rewrite:

- WP5 conversation engine as a live Gemini participant runtime.
- WP4 live model path from Gemini CLI ACP to Gemini API/ADK.
- WP3 A2A stub into a real HTTP server surface.
- WP9 demo server into a UI-backed app that calls the new runtime rather than only subprocessing fixture scripts.
- WP9a so BigQuery write is a normal export path, not a separate dry-run proof script.

Do not rewrite:

- Validation logic.
- Quality metric definitions.
- Fixture contracts.
- Product positioning.

## 32-Day Build Schedule

### Week 1: Real Agent Core

Goal: Replace the highest-risk fixture behavior with live Gemini/ADK.

Milestones:

- Add `google-adk`, `google-genai`, `pydantic`, `fastapi`, `uvicorn`, and `google-cloud-bigquery` dependencies.
- Build `methodic/schemas.py` from the existing JSON schema fields.
- Implement Organizer, Methodology, and Question Design agents.
- Implement participant conversation loop with Gemini structured output.
- Connect participant agent to WP6 MCP server through ADK `McpToolset`.
- Create tests comparing live/simulated output shape to existing fixture expectations.

Exit gate:

- One participant session runs end to end without reading `expected_response` as the answer oracle.
- One real MCP call occurs inside the participant path.
- Structured output validates locally.

### Week 2: Orchestration, Export, And Deployment

Goal: Make the vertical slice deployable and auditable.

Milestones:

- Implement ADK `SequentialAgent` plan flow.
- Implement bounded coverage loop and reserve participant trigger.
- Integrate WP7 quality scoring against live outputs.
- Implement real BigQuery dataset/table write.
- Deploy to Cloud Run with env vars and service account.
- Add Cloud Run smoke test for `/health`, `/demo/run`, and BigQuery export.

Exit gate:

- Cloud Run URL runs a complete demo trace.
- BigQuery contains at least one row from the live run.
- README documents exact setup and evidence paths.

### Week 3: Demo UI And Reliability

Goal: Convert the runtime into a judge-friendly working experience.

Milestones:

- Build a compact UI: external request, plan review, split-screen static versus Methodic, coverage dashboard, event timeline, export proof.
- Add deterministic demo mode with cached live traces for video reliability.
- Add guardrail examples: vague answer, contradiction, or frustrated participant.
- Add model failure fallback: retry once, then mark unresolved instead of fabricating.
- Add trace export artifact for every demo run.

Exit gate:

- A fresh user can run the demo from the Cloud Run URL and understand the agentic proof beats in under four minutes.
- UI clearly labels live, cached-live, deterministic fallback, and dry-run states.

### Week 4: Submission Hardening

Goal: Make the submission defensible.

Milestones:

- Record 3-4 minute video from the deployed demo.
- Write Devpost copy mapped to the four judging criteria.
- Add architecture diagram.
- Add source-grounded methodology caveats and competitor comparison.
- Run final smoke tests from a clean checkout.
- Freeze scope by 2026-06-02 and reserve the final days for video, README, and deployment fixes.

Exit gate:

- Public/demo URL works.
- Video matches live behavior.
- README contains commands, env vars, architecture, and honest limitations.
- No claim depends on unverified statistical rigor.

## Hard Truths

What can be built in 32 days:

- A compelling, narrow, real vertical slice.
- Live Gemini methodology critique.
- Live participant interviewing for controlled personas.
- Real MCP context lookup.
- Real structured extraction and validation.
- Real BigQuery export.
- Cloud Run deployment.
- A polished demo that shows why Methodic is not a static survey.

What probably cannot be built well in 32 days:

- Production participant recruitment.
- Full multi-tenant research operations platform.
- Statistically meaningful research quality validation.
- Full A2A 1.0 compliance plus enterprise auth unless ADK quickstart makes it trivial.
- Broad industry support.
- Fully autonomous fieldwork with uncontrolled real participants.

## Immediate Next Actions

1. Create `methodic/` runtime package and dependency update.
2. Replace WP5 fixture-oracle extraction first.
3. Wrap WP6 MCP server through ADK `McpToolset`.
4. Add a real BigQuery smoke path early, not in the final week.
5. Build UI only after the live participant loop works.

The most important sequencing rule: do not spend the next week polishing the fixture demo. The fixture demo already tells the story. The submission now needs one real agent path that makes the story true.
