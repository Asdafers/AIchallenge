# Devpost Submission Copy

Copy-paste text for the Devpost submission form fields.

---

## Project Name

Methodic

## Tagline

Autonomous research operations agent that turns B2B business decisions into governed, evidence-linked data.

## Track

Track 1: Build — Net-New Agents

## What it does

Methodic replaces static B2B surveys with an autonomous multi-agent research workflow. Given a business question ("Why are we losing enterprise deals to Competitor X?"), it:

1. **Plans the study** — an organizer agent structures objectives, hypotheses, and participant pools; a methodology agent pushes back on sampling bias and insufficient sample sizes
2. **Designs interview questions** — a question design agent maps each question to target research variables with follow-up probes
3. **Conducts governed interviews** — an interviewer agent adaptively probes vague answers ("price") into specific decision variables ("procurement friction vs. ROI justification"), while guardrails enforce research ethics
4. **Extracts structured data in real time** — after each turn pair, a Gemini-powered extractor maps responses to 8 canonical research variables with confidence scores
5. **Tracks coverage and autonomously re-plans** — a coverage agent identifies gaps across variables; a replanner calls Gemini to decide whether to add a targeted follow-up participant or stop the study
6. **Reviews quality and exports** — a quality reviewer validates findings, then BigQuery export writes structured, evidence-linked rows (live mode; dry-run by default in demo)

The result: coverage of 8 canonical research variables improves from ~12.5% (static survey baseline) to ~87.5% (agent-conducted), measured by the same rubric applied to both in a fixture benchmark.

## Inspiration

B2B teams spend months running win-loss research, but the data-capture layer — static surveys — produces shallow answers. "Price" appears in every lost-deal report, but dashboards can't distinguish packaging friction from ROI justification failures. We built Methodic to fix the upstream data problem: capture governed, evidence-linked data that actually supports business decisions.

## How we built it

Methodic is built on Google's Agent Development Kit (ADK) with a multi-agent architecture:

- **ADK Agent Graph**: `SequentialAgent` orchestrates three phases (planning → fieldwork → finalization), with `LoopAgent` managing interview iteration (max 6 turns) and participant cycling (max 3 participants). 7 `LlmAgent` nodes handle reasoning; 6 custom `BaseAgent` steps handle deterministic logic (session init, extraction, turn checking, coverage assessment, re-plan decision, BigQuery export).
- **Gemini 2.5 Pro** powers all reasoning agents — methodology review, question design, interviewing, quality review, and study completion. Participant simulation uses Gemini 2.5 Flash for cost efficiency.
- **Real-time SSE streaming**: A FastAPI server wraps the ADK runner, streaming every agent event as Server-Sent Events. The demo UI renders conversations, coverage bars, agentic moment highlights, and pipeline timeline live as the agent works.
- **Cloud Run deployment**: The full pipeline runs on Cloud Run (us-central1) with Vertex AI authentication, Cloud Trace integration, and A2A-compatible agent card at `/.well-known/agent-card.json`.
- **MCP integration**: Model Context Protocol tools (`lookup_deal_context`, `lookup_trial_telemetry`) provide secure access to deal context and telemetry data through a stdio JSON-RPC 2.0 server with server-side field filtering.
- **BigQuery export**: Structured participant responses with 8 canonical variables, confidence scores, and evidence quotes are flattened and exported to BigQuery. Live writes confirmed on Cloud Run (2 rows exported 2026-05-09).

The build process itself was multi-agent: Claude implemented the task plan, Gemini performed 6 blind adversarial reviews via ACP, and Codex contributed 10 independent code reviews — 16 total blind reviews across both models.

## Challenges we ran into

- **ADK EventActions pattern**: The ADK documentation didn't clearly cover how custom `BaseAgent` steps should signal loop exit. We discovered that `InvocationContext` has no `actions` attribute — escalation must go through `Event(actions=EventActions(escalate=True))`, and state propagation through `EventActions(state_delta={...})`. This was the root cause of our first Cloud Run deployment crash.
- **Non-deterministic pipeline behavior**: Gemini sometimes generates a follow-up question instead of structured output, causing the pipeline to exit early. The architecture handles this gracefully — the `LoopAgent` and `SequentialAgent` continue regardless — but it means each run produces different results.
- **Autonomous re-plan scope control**: The replanner must decide when to add a participant vs. stop the study. We bounded this with `max_iterations=3` on the fieldwork loop and a deterministic STOP condition when coverage is sufficient.

## Accomplishments we're proud of

- **Live end-to-end pipeline**: A real Gemini-powered pipeline running on Cloud Run that streams 34 events in real time across 7 LlmAgent nodes and 6 custom BaseAgent steps, completing in ~5 minutes. Demo mode uses a Gemini-powered participant simulator; interactive mode accepts real human input.
- **BigQuery export — live**: Structured participant responses with confidence scores and evidence quotes export directly to BigQuery. 2 rows confirmed written from live pipeline runs on 2026-05-09 (`dry_run: false`).
- **133 automated tests**: 73 unit/integration tests covering schemas, validators, agent logic, and MCP tools, plus 60 Playwright E2E tests for the demo UI and interactive mode.
- **Measurable quality delta**: Fixture benchmark — same rubric, same participants, static vs. Methodic — coverage improvement from ~12.5% to ~87.5% across 8 canonical research variables (+0.692 composite score).
- **Multi-agent build process**: Implementation plan executed via subagent-driven development with two-stage review (spec compliance + code quality). 16 blind adversarial reviews across Gemini and Codex.

## What we learned

The hardest part of building an autonomous agent isn't the AI — it's the governance layer. Knowing when to stop probing, which turn count triggers escalation, when a re-plan is warranted vs. noise — these are measurement design problems, not engineering problems. The methodology review agent turned out to be the most important component: it consistently pushes back on insufficient sample sizes and sampling bias, which prevents the downstream pipeline from producing meaningless results.

We also learned that ADK's `LoopAgent` and `SequentialAgent` are powerful abstractions for multi-phase workflows, but custom `BaseAgent` steps require careful attention to the Event/EventActions contract. The framework is designed around yielding Events, not mutating context — a pattern that becomes clear only when your first deployment crashes.

## What's next for Methodic

- Multi-participant sessions with parallel interview tracks
- Persistent study state across sessions (currently single-shot)
- Frontend dashboard for organizer review and methodology override
- Multi-study support beyond the B2B win-loss vertical
- A2A integration for inter-agent study delegation

## Built with

- Gemini 2.5 Pro (via Vertex AI)
- Google Agent Development Kit (ADK)
- Model Context Protocol (MCP)
- Cloud Run
- BigQuery
- FastAPI
- Playwright (E2E testing)
- Python

## GCP Project

methodic-ai-challenge

## Links

- GitHub: [repository URL]
- Demo video: demo_output/demo.webm
- Live endpoint: https://methodic-2030382823.us-central1.run.app
