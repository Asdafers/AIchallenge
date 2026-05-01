# Draft Implementation Task Skeletons

These are draft Mission task bodies for future build work. They are intentionally not active Mission tasks.

**DO NOT CLAIM UNTIL BUILD-GO.** Build-go requires the operator to approve implementation after the Gemini judge-story pass and Claude combined adversarial review, or an explicit operator waiver.

Each future task must cite `mission_strategy['aichallenge']` in its Mission outcome and stay scoped to the B2B SaaS win-loss vertical slice.

## WP1: Study Schema And Quality Rubric

**Requested assignee**: Codex or Gemini  
**Priority**: high  
**Depends on**: build-go approval  
**Proof beats**: B5, B7, B9  
**Gate served**: G2 Schema lock

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Implement the planning-approved study schema and quality rubric as repo artifacts. Use `docs/spec.md` `Data Schema -> Participant Response` as canonical. Define coverage states, guardrail event types, quality scoring rubric, static-form baseline fields, BigQuery-ready table schema, and export examples for the B2B SaaS win-loss study.
>
> Acceptance: every question, fixture, guardrail event, dashboard metric, and export field maps to a canonical field. Include example records for static baseline, Methodic output, guardrail event, and BigQuery export row. No parallel field names may remain in implementation docs.
>
> Verification: provide a schema validation command or documented manual check that validates all examples.

## WP2: Project Scaffold And Fixture Contract

**Requested assignee**: Codex  
**Priority**: high  
**Depends on**: WP1  
**Proof beats**: B1, B2, B6, B7, B8  
**Gate served**: G3 Fixture contract

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Create the minimal app scaffold and deterministic fixture data from the locked schema. Include HTTP `request_study` payload fixture, P-001/P-002/P-003 primary participant fixtures that leave `procurement_friction` ambiguous after three sessions, P-005 procurement reserve fixture, CRM/telemetry fixture, and static-form baseline fixture.
>
> Acceptance: fixture data can drive the whole demo without live customer data and without inventing fields outside the schema.
>
> Verification: run local fixture validation and document the command/output.

## WP3: External Request And Organizer Flow

**Requested assignee**: Codex or Gemini  
**Priority**: high  
**Depends on**: WP1, WP2  
**Proof beats**: B1, B2  
**Gate served**: G4 Organizer proof

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Build the planning-approved external request and organizer flow. Use an HTTP `request_study` endpoint or honestly labeled endpoint stub. Show Sales Insights request, Methodic clarification, organizer brief, and approval state.
>
> Acceptance: HTTP payload -> clarification -> brief runs from a clean local state and records each event in order.
>
> Verification: provide local smoke command or manual browser/API path with output evidence.

## WP4: Methodology And Question Design Review Package

**Requested assignee**: Gemini or Codex  
**Priority**: high  
**Depends on**: WP2, WP3  
**Proof beats**: B2, B5  
**Gate served**: G4 Organizer proof

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Build methodology pushback and question-design review package for the win-loss study. The champion-only sample must trigger a live Gemini-generated correction tied to the pricing/ROI decision, with deterministic fallback only. Produce sample revision, question pool, question-to-variable map, risk notes, and approval view.
>
> Acceptance: biased sample plan triggers the expected Gemini-generated correction; every question maps to a variable or hypothesis.
>
> Verification: deterministic fixture test or documented manual demo path proves the rule fires.

## WP5: Participant Agent Conversation Loop

**Requested assignee**: Codex  
**Priority**: high  
**Depends on**: WP2, WP4  
**Proof beats**: B3, B5, B9  
**Gate served**: G5 pre-MCP participant proof

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Build the participant conversation loop before MCP integration. Select and document Gemini model/latency budget for participant turns. Preserve measurement intent, probe vague answers, stop probing variables at approved thresholds, capture transcript, and log one guardrail recovery for misunderstanding, contradiction, or frustration.
>
> Acceptance: three fixture participants produce different paths; one guardrail event is logged without forcing a category.
>
> Verification: local run captures transcript, guardrail event, and structured extraction for each participant.

## WP6: MCP Context Lookup

**Requested assignee**: Codex  
**Priority**: high  
**Depends on**: WP5  
**Proof beats**: B4, B8  
**Gate served**: G5 MCP proof

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Implement real MCP boundary for `lookup_deal_context` and integrate it with the Participant Agent through ADK. Use tool filtering, explicit timeout, fallback behavior, and developer trace logging.
>
> Acceptance: participant agent calls MCP context to ask a better ROI follow-up, and output includes a context reference.
>
> Verification: trace shows MCP call, filtered tool access, timeout config, fallback path, and context reference.

## WP7: Data Quality Layer

**Requested assignee**: Codex or Gemini  
**Priority**: high  
**Depends on**: WP2, WP5, WP6  
**Proof beats**: B5, B7  
**Gate served**: G6 Quality proof

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Build the Data Quality Layer: coverage scoring, ambiguity detection, evidence linking, quality metadata, thin static-form baseline comparison, JSON/CSV export, and BigQuery-ready table schema output.
>
> Acceptance: static-form baseline and Methodic sessions are scored by the same rubric and show a measurable quality delta without over-claiming statistical rigor. If the static path is reduced to fixtures, label it as a reference fixture and stop calling the delta measured.
>
> Verification: comparison fixture shows lower ambiguity and higher evidence-link coverage for Methodic.

## WP8: Autonomous Re-Plan

**Requested assignee**: Codex or Gemini  
**Priority**: high  
**Depends on**: WP7  
**Proof beats**: B6  
**Gate served**: G7 Re-plan proof

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Implement the autonomous re-plan trigger. If `procurement_friction` remains `ambiguous` after P-001/P-002/P-003, add exactly one targeted P-005 procurement reserve participant and explain the rationale.
>
> Acceptance: unresolved coverage triggers one P-005 procurement session and records the final variable state.
>
> Verification: local E2E run records re-plan decision, added participant, and resulting coverage state.

## WP9: Cloud Run Deployment And Demo Trace

**Requested assignee**: Codex  
**Priority**: high  
**Depends on**: WP3, WP6, WP7, WP8, WP9a  
**Proof beats**: B8  
**Gate served**: G8 Cloud proof

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Deploy the vertical slice to Cloud Run with Gemini, ADK, MCP, persistence, export, and BigQuery write path. Produce env/secrets notes and live smoke trace.
>
> Acceptance: deployed service can create session, run ADK agent, call MCP, persist data, export results, and write at least one structured row to BigQuery.
>
> Verification: Cloud Run smoke checklist passes against the live URL and confirms the BigQuery row.

## WP9a: BigQuery Export Setup

**Requested assignee**: Codex  
**Priority**: high  
**Depends on**: WP1, WP7  
**Proof beats**: B7, B8  
**Gate served**: G8 Cloud proof

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Set up BigQuery export before Cloud Run deployment. Create dataset/table, document IAM/service-account needs, implement local write path, and write one fixture row using the canonical schema.
>
> Acceptance: local code writes at least one structured row to the canonical BigQuery table before Cloud Run deploy starts.
>
> Verification: command or documented check confirms the row exists in BigQuery.

Open WP9a before WP9; WP9 depends on WP9a even though the numbering keeps Cloud Run as the main deployment package.

## WP10: Submission Package

**Requested assignee**: Gemini or Codex  
**Priority**: high  
**Depends on**: WP9  
**Proof beats**: B1-B9  
**Gate served**: submission readiness

Task body:

> DO NOT CLAIM UNTIL BUILD-GO.
>
> Package the challenge submission using docs/judge-storyboard.md as the narrative source: 3-4 minute demo script, video plan, README, architecture diagram, limitations, and Devpost copy. Keep the story focused on Methodic as governed data capture, not an AI survey tool.
>
> Acceptance: every proof beat is visible or intentionally narrated; the split-screen is readable; the re-plan trigger is visually obvious; statistical limits are stated clearly; Google stack is visible without dominating the product story.
>
> Verification: rehearsal checklist confirms all proof beats and submission artifacts are present.
