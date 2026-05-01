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
| G9 Model proof | Agent-flow implementation | Gemini model choices are documented with fixture latency and quality checks for participant, methodology, and data-quality paths. |

## Future Build Work Packages

These are implementation packages to create only after G1 passes. They are listed here so reviewers can inspect sequencing and scope before tasks are opened.

### WP1: Study Schema And Quality Rubric

- **Purpose**: Lock the data contract before fixtures or agents are built.
- **Depends on**: G1.
- **Proof beats**: B5, B7, B9.
- **Outputs**: canonical `docs/spec.md` participant-response schema, coverage states, guardrail event types, quality scoring rubric, static-form baseline schema, BigQuery table schema, export schema.
- **Acceptance**: every question, fixture, guardrail event, dashboard metric, and export row maps to the canonical schema; no parallel field names remain in planning docs.
- **Verification**: schema examples can validate static baseline, Methodic output, and guardrail event examples.

### WP2: Project Scaffold And Fixture Contract

- **Purpose**: Create the minimal deployable app shape and deterministic fixture data from the locked schema.
- **Depends on**: WP1.
- **Proof beats**: B1, B2, B6, B7, B8.
- **Outputs**: app scaffold, HTTP `request_study` payload fixture, three primary participant fixtures that leave `procurement_friction` ambiguous, P-005 procurement reserve fixture, CRM/telemetry fixture, static-form baseline fixture.
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
- **Outputs**: live Gemini methodology pushback, deterministic fallback, sample revision, question pool, question-to-variable map, visual review package.
- **Acceptance**: biased champion-only sample triggers a Gemini-generated correction tied to the business decision; deterministic fallback is used only when the live call fails.
- **Verification**: deterministic fixture test or manual demo script proves the rule fires.

### WP5: Participant Agent Conversation Loop

- **Purpose**: Replace static survey capture with constrained adaptive conversation.
- **Depends on**: WP2, WP4.
- **Proof beats**: B3, B5, B9.
- **Outputs**: participant chat flow, selected Gemini model and latency budget, probing policy, stop condition, transcript capture, guardrail recovery for misunderstanding/contradiction/frustration.
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
- **Outputs**: coverage scoring, ambiguity detection, evidence linking, quality metadata, thin static-form baseline comparison, JSON/CSV export, BigQuery-ready table schema.
- **Acceptance**: static-form baseline and Methodic outputs are scored by the same rubric; if the static path is fixture-only, docs label it as a reference fixture rather than a measured comparison.
- **Verification**: comparison fixture shows lower ambiguity and higher evidence-link coverage for Methodic.

### WP8: Autonomous Re-Plan

- **Purpose**: Prove Methodic can inspect coverage and change the data-capture plan.
- **Depends on**: WP7.
- **Proof beats**: B6.
- **Outputs**: unresolved-variable detector, P-005 procurement reserve session, rationale card.
- **Acceptance**: `procurement_friction` ambiguity after P-001/P-002/P-003 triggers exactly one P-005 procurement session.
- **Verification**: local E2E run records re-plan decision and final variable state.

### WP9a: BigQuery Export Setup

- **Purpose**: De-risk Cloud Run deployment by proving the BigQuery export path before deployment day.
- **Depends on**: WP1, WP7.
- **Proof beats**: B7, B8.
- **Outputs**: BigQuery dataset/table, IAM/service-account notes, local write path, one fixture row written locally.
- **Acceptance**: local code writes at least one structured row to the canonical BigQuery table before Cloud Run deploy starts.
- **Verification**: command or documented check confirms the row exists in BigQuery.

### WP9: Cloud Run Deployment And Demo Trace

- **Purpose**: Prove the Google-aligned architecture works live.
- **Depends on**: WP3, WP6, WP7, WP8, WP9a.
- **Proof beats**: B8.
- **Outputs**: Docker/container config, Cloud Run service, env/secrets docs, live smoke trace. BigQuery dataset/table/IAM must already be set up before this package starts.
- **Acceptance**: deployed service can create session, run agent, call MCP, persist data, export results, and write the structured table to the pre-created BigQuery table.
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
| Operator build-go gate | human | Claude review or explicit override | Decide whether to open implementation tasks from WP1-WP10 plus WP9a. |

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
- Future implementation tasks are created from WP1-WP10 plus WP9a with acceptance criteria copied into Mission Control.

## Claude Review Reconciliation

Claude review `388eed0b-91af-406b-8557-d73bc581a2b1` returned `ship-with-changes` and `HOLD`. The current planning docs reconcile the two Blockers and key Majors as follows:

- **Blocker 1, schema contradiction**: `docs/spec.md` is canonical for participant-response schema; vertical/delivery docs now reference that schema and use the same field names.
- **Blocker 2, re-plan contradiction**: P-002 now intentionally leaves procurement ambiguous; P-005 is the reserve procurement stakeholder that resolves the re-plan path.
- **Major, BigQuery/Cloud Run compression**: BigQuery setup is split into a pre-deploy setup package/day before Cloud Run deployment.
- **Major, deterministic proof beats**: methodology pushback is committed to a live Gemini reasoning call with deterministic fallback only.
- **Major, static baseline shape**: baseline is committed to a thin static-form UI/path using the same fixture personas.
- **Major, schedule slack**: freeze/slack days are explicit on 2026-05-10, 2026-05-20, 2026-05-28, and 2026-05-31.
- **Major, model evaluation slot**: model-selection/latency spike is explicit on 2026-05-02 and G9.
