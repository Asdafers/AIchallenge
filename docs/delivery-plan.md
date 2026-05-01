# Methodic Delivery Plan

This is a planning-only delivery plan for the Methodic challenge prototype. It expands `docs/methodic-vertical-slice.md` into a task graph with dependencies, acceptance gates, and review checkpoints. It does not authorize build work yet.

## Planning Rules

- Keep all implementation tasks blocked until the planning review tasks are complete.
- Preserve the locked demo wedge: B2B SaaS win-loss research for mid-market enterprise deals.
- Every future build task must cite at least one demo proof beat and one verification gate.
- Prefer a complete vertical slice over platform breadth.
- Treat statistical claims conservatively: operational and qualitative quality gains are acceptable; representativeness claims require caveats.

## Demo Proof Beats

| Beat | Proof | Demo Evidence |
| --- | --- | --- |
| B1 | External agent request | Sales Insights agent sends `request_study`; Methodic asks a clarifying question before accepting. |
| B2 | Organizer planning and methodology pushback | Organizer review package includes brief, sample plan, variables, questions, and a visible sample-bias correction. |
| B3 | Interactive participant capture | Participant agent clarifies vague "price" answer into decision-relevant variables. |
| B4 | MCP triangulation | Participant agent calls `lookup_deal_context` through MCP and uses approved CRM/telemetry context. |
| B5 | Stop condition and coverage loop | Required variables show coverage states and probing stops when thresholds are met. |
| B6 | Autonomous re-plan | Unresolved `procurement_friction` triggers one targeted extra participant session. |
| B7 | Measurable quality delta | Static-survey baseline and Methodic output are scored with the same rubric. |
| B8 | Google-aligned deployability | Gemini, ADK, MCP, and Cloud Run are present in the working architecture and verification trace. |
| B9 | Guardrail recovery | Participant misunderstanding, contradiction, or frustration is handled without changing measurement intent, and the event is logged in the developer overlay. |

## Delivery Gates

| Gate | Required Before | Acceptance |
| --- | --- | --- |
| G1 Planning approval | Any build task starts | `docs/methodic-vertical-slice.md` and this plan pass Gemini review, then Claude adversarial review when available. |
| G2 Schema lock | Fixture and agent-flow implementation | Required variables, coverage states, quality rubric, fixture participant requirements, and export shape are documented. |
| G3 Fixture contract | Organizer work expands | Fixture data follows the locked schema and includes Sales Insights request, baseline survey answers, CRM/telemetry context, three primary participants, and one reserve re-plan participant. |
| G4 Organizer proof | Participant work expands | External request, clarification, methodology pushback, and review package can run from fixtures. |
| G5 MCP proof | Quality dashboard work expands | Participant Agent calls `lookup_deal_context` through MCP with timeout, tool filter, trace, and fallback. |
| G6 Quality proof | Cloud deployment | Static baseline and Methodic sessions produce comparable coverage and ambiguity scores. |
| G7 Re-plan proof | Demo recording | One unresolved variable triggers one targeted extra participant and a written rationale. |
| G8 Cloud proof | Submission | Cloud Run URL can create a session, run the ADK agent, call MCP, persist data, export results, and write the structured table to BigQuery. |

## Future Build Work Packages

These are implementation packages to create only after G1 passes. They are listed here so reviewers can inspect sequencing and scope before tasks are opened.

### WP1: Study Schema And Quality Rubric

- **Purpose**: Lock the data contract before fixtures or agents are built.
- **Depends on**: G1.
- **Proof beats**: B5, B7, B9.
- **Outputs**: required variables, coverage states, guardrail event types, quality scoring rubric, export schema.
- **Acceptance**: every question, fixture, guardrail event, and dashboard metric maps to a documented field.
- **Verification**: schema examples can validate static baseline, Methodic output, and guardrail event examples.

### WP2: Project Scaffold And Fixture Contract

- **Purpose**: Create the minimal deployable app shape and deterministic fixture data from the locked schema.
- **Depends on**: WP1.
- **Proof beats**: B1, B2, B6, B7, B8.
- **Outputs**: app scaffold, HTTP `request_study` payload fixture, three primary participant fixtures, one reserve re-plan participant fixture, CRM/telemetry fixture, static survey baseline fixture.
- **Acceptance**: fixture data can drive the whole demo without live customer data and without inventing fields outside the schema.
- **Verification**: local fixture validation command or documented manual check.

### WP3: External Request And Organizer Flow

- **Purpose**: Show Methodic planning from an external agent request, not a blank form.
- **Depends on**: WP1, WP2.
- **Proof beats**: B1, B2.
- **Outputs**: HTTP `request_study` endpoint or honestly labeled endpoint stub, external request event, clarification response, organizer brief, approval state.
- **Acceptance**: HTTP payload -> clarification -> brief can run from a clean local state.
- **Verification**: local smoke path records each event in order.

### WP4: Methodology And Question Design Review Package

- **Purpose**: Demonstrate research-operations judgment and traceability.
- **Depends on**: WP2, WP3.
- **Proof beats**: B2, B5.
- **Outputs**: methodology pushback, sample revision, question pool, question-to-variable map, visual review package.
- **Acceptance**: biased champion-only sample triggers concrete correction tied to the business decision.
- **Verification**: deterministic fixture test or manual demo script proves the rule fires.

### WP5: Participant Agent Conversation Loop

- **Purpose**: Replace static survey capture with constrained adaptive conversation.
- **Depends on**: WP2, WP4.
- **Proof beats**: B3, B5, B9.
- **Outputs**: participant chat flow, probing policy, stop condition, transcript capture, guardrail recovery for misunderstanding/contradiction/frustration.
- **Acceptance**: three fixture participants produce different paths while preserving measurement intent, and one guardrail event is logged without forcing a category.
- **Verification**: local run captures transcript, guardrail event, and structured extraction for each participant.

### WP6: MCP Context Lookup

- **Purpose**: Prove tool use is bound to measurement intent.
- **Depends on**: WP5.
- **Proof beats**: B4, B8.
- **Outputs**: MCP server, `lookup_deal_context` tool, ADK MCP toolset integration, tool trace, fallback.
- **Acceptance**: participant agent uses MCP context to ask a better ROI follow-up.
- **Verification**: trace shows MCP call, filtered tool access, timeout config, and context reference in output.

### WP7: Data Quality Layer

- **Purpose**: Make data quality measurable in the demo.
- **Depends on**: WP2, WP5, WP6.
- **Proof beats**: B5, B7.
- **Outputs**: coverage scoring, ambiguity detection, evidence linking, quality metadata, JSON/CSV export, BigQuery-ready table schema.
- **Acceptance**: static baseline and Methodic outputs are scored by the same rubric.
- **Verification**: comparison fixture shows lower ambiguity and higher evidence-link coverage for Methodic.

### WP8: Autonomous Re-Plan

- **Purpose**: Prove Methodic can inspect coverage and change the data-capture plan.
- **Depends on**: WP7.
- **Proof beats**: B6.
- **Outputs**: unresolved-variable detector, one targeted extra participant, rationale card.
- **Acceptance**: `procurement_friction` ambiguity triggers exactly one extra targeted session.
- **Verification**: local E2E run records re-plan decision and final variable state.

### WP9: Cloud Run Deployment And Demo Trace

- **Purpose**: Prove the Google-aligned architecture works live.
- **Depends on**: WP3, WP6, WP7, WP8.
- **Proof beats**: B8.
- **Outputs**: Docker/container config, Cloud Run service, BigQuery export wiring, env/secrets docs, live smoke trace.
- **Acceptance**: deployed service can create session, run agent, call MCP, persist data, export results, and write the structured table to BigQuery.
- **Verification**: Cloud Run smoke checklist passes against the live URL and confirms at least one exported row in BigQuery.

### WP10: Submission Package

- **Purpose**: Package the build into a judge-ready story.
- **Depends on**: WP9.
- **Proof beats**: B1-B9.
- **Outputs**: demo script, video, README, architecture diagram, limitations, submission copy.
- **Acceptance**: 3-4 minute demo shows every proof beat without over-claiming statistical rigor.
- **Verification**: rehearsal checklist confirms all proof beats are visible.

## Planning-Only Mission Task Graph

The following tasks are safe to open before build work because they ask only for critique and planning refinement.

| Task | Assignee | Depends on | Purpose |
| --- | --- | --- | --- |
| Review delivery plan and task graph | Gemini | this document | Check judge impact, sequencing, story clarity, and whether the future work packages preserve the Methodic thesis. |
| Reconcile delivery review findings | Codex or any | Gemini review | Update this plan and vertical slice if the review finds gaps. |
| Judge-story pass for demo narrative | Gemini | reconciled delivery plan | Compress the 3-4 minute video story and identify visible vs narrated proof beats. |
| Reconcile judge-story pass | Codex or any | Gemini judge-story pass | Fold accepted narrative sequencing and story risks back into planning docs. |
| Adversarial review of vertical slice and delivery plan | Claude | revised docs; when credits available | Find unstated assumptions, feasibility gaps, demo weaknesses, and planning drift before implementation tasks open. |
| Operator build-go gate | human | Claude review or explicit override | Decide whether to open implementation tasks from WP1-WP10. |

## Review Instructions For Planning Tasks

Planning reviewers should not implement code. They should produce:

1. Severity-rated issues: `Blocker`, `Major`, or `Minor`.
2. Falsifiable assumptions whose failure would invalidate the plan.
3. Explicit verdict: `ship-as-is`, `ship-with-changes`, or `rewrite`.
4. Specific changes needed before implementation tasks are opened.

## Build-Go Criteria

Do not open build tasks until these are true:

- The win-loss scenario remains consistent across `docs/spec.md`, `docs/methodic-vertical-slice.md`, and this plan.
- The Gemini planning review is complete.
- Gemini's `ship-with-changes` findings are reconciled: schema precedes fixtures, guardrail recovery is included, reserve re-plan participant is required, and the external request path is clarified as an HTTP payload or honestly labeled endpoint stub.
- Gemini's judge-story pass is complete and reconciled: the final video uses the 5-scene compressed sequence, split-screen text is zoomed/highlighted, re-plan ambiguity is visually obvious before trigger, and stack details stay in developer overlay/export close.
- The Claude adversarial review is complete or explicitly waived by the operator because credits are unavailable.
- Any Blocker findings are resolved in docs.
- Future implementation tasks are created from WP1-WP10 with acceptance criteria copied into Mission Control.
