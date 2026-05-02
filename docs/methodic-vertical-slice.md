# Methodic: Vertical-Slice Demo Plan

This document defines the concrete build path for **Methodic**, an autonomous research operations agent for B2B teams.

The vertical slice is intentionally narrow: a B2B SaaS win-loss study for mid-market enterprise deals. The demo should prove that Methodic can turn a business decision into a governed data-capture workflow, run interactive participant conversations, use approved business context through MCP, and export cleaner, evidence-linked data than a static survey, including a real BigQuery structured export for the final dataset.

## Constraints And Alignment

- **Track**: Track 1 Build - net-new agent system.
- **Stack**: Gemini API, Agent Development Kit (ADK), Model Context Protocol (MCP), and Google Cloud Run.
- **Use case**: B2B SaaS win-loss research for mid-market enterprise deals.
- **Buyer**: Head of Research Operations at a 200-2000 employee B2B SaaS company, with secondary value for product, sales, success, and GTM analytics.
- **Timeline**: 2026-05-02 to 2026-06-05.
- **Core thesis**: no useful insights without good data.

## Demo Scope

### What The Slice Must Show

1. A mocked Sales Insights agent requests a win-loss study from Methodic.
2. Methodic asks one clarifying question before accepting or finalizing the task.
3. The Organizer AI turns the request into a research brief, data schema, question pool, and review package.
4. The Methodology Agent pushes back when the user's proposed sample cannot answer the business question.
5. Participant agents conduct interactive conversations, not static forms.
6. One participant conversation uses an MCP context lookup against mocked CRM or product telemetry.
7. The Data Quality Layer tracks required variables as `missing`, `ambiguous`, `covered_low_confidence`, or `covered_high_confidence`.
8. Methodic triggers one autonomous re-plan when a key variable remains unresolved.
9. The final output compares static-survey baseline data with Methodic's evidence-linked structured data.
10. A compact guardrail example shows Methodic handling misunderstanding, contradiction, or frustration without changing measurement intent.

### Explicit Non-Goals

These non-goals come from `mission_strategy['aichallenge'].non_goals`:

- **No broad platform scope before a complete vertical slice**: build one win-loss workflow, not a generic research platform.
- **No over-claiming statistical rigor**: claim operational and qualitative data-quality gains; avoid pretending the prototype proves statistical representativeness.
- **No marketing landing page before the working experience**: the first screen should be the product workflow, not a promotional site.

## Technical Architecture For The Slice

### Agents

- **External Requesting Agent**: mocked Sales Insights agent that submits a structured `request_study` event and receives a structured completion.
- **Organizer Agent**: uses Gemini through ADK to clarify the business decision and produce the research brief.
- **Methodology Agent**: uses a live Gemini reasoning call to review sampling, measurement validity, bias, and overclaim risk. Deterministic critique rules may exist only as a fallback or regression test, not as the primary proof of methodology pushback.
- **Question Design Agent**: maps each question and follow-up category to required variables.
- **Participant Agent**: conducts constrained, adaptive conversations from the approved study plan.
- **Data Quality Agent**: normalizes responses, scores coverage, links evidence, and triggers one bounded re-plan.

### MCP Boundary

Use a real MCP server boundary for one approved business-context lookup. The tool can be backed by fixture data, but the agent must call it through MCP rather than reading local constants directly.

Minimum tool contract:

```json
{
  "tool": "lookup_deal_context",
  "input": {
    "participant_id": "P-002",
    "allowed_fields": ["deal_stage", "persona", "trial_usage", "crm_notes"]
  },
  "output": {
    "deal_stage": "slipping_deal",
    "persona": "economic_buyer",
    "trial_usage": {
      "logins": 3,
      "report_builder_reached": false
    },
    "crm_notes": ["ROI proof requested", "finance stakeholder not convinced"]
  }
}
```

ADK integration requirements:

- Use deployment-safe, synchronous agent definitions for Cloud Run.
- Configure MCP tool filtering so the participant agent only sees approved context tools.
- Set explicit MCP timeouts and show a graceful fallback if context lookup fails.
- Verify locally and after deploy: list apps, create session, run agent, call MCP tool, persist response, export result.

### Canonical Data Quality Schema

Define this before building the agents, because the conversation policy and dashboard depend on it. The canonical field contract lives in `docs/spec.md` under `Data Schema -> Participant Response`. Do not invent parallel field names in implementation docs.

Required variables for the win-loss study:

- `primary_loss_reason`: unclear_roi, budget_timing, procurement_friction, security_concern, competitor_pressure, missing_feature, economic_buyer_gap, other, unknown.
- `secondary_loss_reason`: optional supporting category or null.
- `roi_clarity`: clear, partially_clear, unclear, unknown.
- `budget_timing`: in_cycle, out_of_cycle, unknown.
- `procurement_friction`: none, low, medium, high, unknown.
- `security_concern`: none, low, medium, high, unknown.
- `competitor_pressure`: none, named_competitor, unknown.
- `aha_moment_reached`: yes, no, unknown.

Per-variable coverage states:

- `missing`: no usable evidence.
- `ambiguous`: evidence exists but cannot be mapped confidently.
- `covered_low_confidence`: mapped with weak or single-source evidence.
- `covered_high_confidence`: mapped with quote or context evidence and sufficient specificity.

Minimum output record:

```json
{
  "participant_id": "P-001",
  "study_id": "WL-2026-Q2-MM",
  "segment": "lost_deal_economic_buyer",
  "persona_summary": "VP Finance at lost mid-market deal",
  "conversation_status": "complete",
  "structured_fields": {
    "primary_loss_reason": "unclear_roi",
    "secondary_loss_reason": "budget_timing",
    "roi_clarity": "unclear",
    "budget_timing": "out_of_cycle",
    "procurement_friction": "unknown",
    "security_concern": "none",
    "competitor_pressure": "none",
    "aha_moment_reached": "no"
  },
  "field_confidence": {
    "primary_loss_reason": 0.86,
    "secondary_loss_reason": 0.55,
    "roi_clarity": 0.82,
    "budget_timing": 0.78,
    "procurement_friction": 0.55,
    "security_concern": 0.8,
    "competitor_pressure": 0.8,
    "aha_moment_reached": 0.9
  },
  "coverage_state": {
    "primary_loss_reason": "covered_high_confidence",
    "secondary_loss_reason": "covered_low_confidence",
    "roi_clarity": "covered_high_confidence",
    "budget_timing": "covered_high_confidence",
    "procurement_friction": "covered_low_confidence",
    "security_concern": "covered_high_confidence",
    "competitor_pressure": "covered_high_confidence",
    "aha_moment_reached": "covered_high_confidence"
  },
  "quality": {
    "variable_coverage": 1.0,
    "ambiguity_resolved": true,
    "evidence_linked": true,
    "requires_recontact": false
  },
  "evidence": [
    {
      "field": "primary_loss_reason",
      "quote": "Finance never saw proof. We never got to the report output.",
      "transcript_turn_id": "T-001-07",
      "context_used": ["lookup_deal_context.trial_usage.report_builder_reached"]
    },
    {
      "field": "roi_clarity",
      "quote": "Finance never saw proof. We never got to the report output.",
      "transcript_turn_id": "T-001-07",
      "context_used": ["lookup_deal_context.trial_usage.report_builder_reached"]
    },
    {
      "field": "budget_timing",
      "quote": "The quarter had closed by the time we were ready to commit.",
      "transcript_turn_id": "T-001-09",
      "context_used": []
    },
    {
      "field": "aha_moment_reached",
      "quote": "We never got to the report output.",
      "transcript_turn_id": "T-001-07",
      "context_used": ["lookup_deal_context.trial_usage.report_builder_reached"]
    },
    {
      "field": "security_concern",
      "quote": "No security or competitor issues.",
      "transcript_turn_id": "T-001-11",
      "context_used": []
    },
    {
      "field": "competitor_pressure",
      "quote": "No security or competitor issues.",
      "transcript_turn_id": "T-001-11",
      "context_used": []
    },
    {
      "field": "procurement_friction",
      "quote": "No procurement involvement — the deal closed before we got there.",
      "transcript_turn_id": "T-001-11",
      "context_used": []
    }
  ],
  "unresolved_ambiguities": []
}
```

See `docs/spec.md > Data Schema > Participant Response` for the canonical schema; this example is the per-WP1 Methodic-path Example B.

## Daily-Resolution Build Milestones

### Phase 1: Foundation, Schema, And Organizer Flow

- **2026-05-02**: Scaffold the app and ADK agent directories; add Gemini config loading; run model-selection spike for participant latency and methodology/data-quality reasoning quality.
- **2026-05-03**: Define the canonical study schema from `docs/spec.md`, coverage states, guardrail event types, quality scoring rubric, static-survey baseline fields, BigQuery table schema, and export format.
- **2026-05-04**: Create fixture data for Sales Insights request, CRM context, telemetry, three primary participants, one procurement reserve participant, and static-form baseline; implement the mocked Sales Insights request and Methodic clarification response as an HTTP payload flow, or label the endpoint stub honestly if it is not fully networked yet.
- **2026-05-05**: Build Organizer Agent flow for the win-loss decision: objective, segments, constraints, required variables, and approval state.
- **2026-05-06**: Implement Methodology Agent pushback as a live Gemini reasoning call for biased sample plans, overbroad claims, and missing economic-buyer coverage, with deterministic fallback only.
- **2026-05-07**: Build Question Design Agent output: question pool, follow-up categories, and question-to-variable mapping.
- **2026-05-08**: Build the visual review package showing brief, sample plan, variables, question coverage, risks, and approval controls.
- **2026-05-09**: Run local E2E Organizer test: external request -> clarification -> brief -> methodology pushback -> review package.
- **2026-05-10**: Phase 1 freeze/slack gate: approved research plan can be generated from fixtures without manual editing; unresolved model/schema issues are fixed before Phase 2.

### Phase 2: Participant Agent And MCP Context Lookup

- **2026-05-11**: Scaffold Participant Agent with deployment-safe ADK structure and deterministic test personas.
- **2026-05-12**: Implement conversation policy: preserve measurement intent, probe vague answers, stop probing variables at approved threshold, and recover once from misunderstanding, contradiction, or frustration.
- **2026-05-13**: Build participant chat UI for three primary fixture participants plus one procurement reserve participant for the re-plan path.
- **2026-05-14**: Implement MCP server for `lookup_deal_context` with fixture-backed CRM and telemetry records.
- **2026-05-15**: Integrate MCP toolset into Participant Agent with tool filtering, timeout, and fallback behavior.
- **2026-05-16**: Add structured extraction from transcript to required variables with quote provenance.
- **2026-05-17**: Build thin static-form baseline UI/path using the same fixture participants and target variables; if reduced to fixtures later, label it as a reference fixture rather than a measured comparison.
- **2026-05-18**: Run local participant comparison: static survey records shallow answers; Methodic records clarified variables and evidence.
- **2026-05-19**: Add automated smoke tests for MCP call, transcript capture, variable extraction, and fallback behavior.
- **2026-05-20**: Phase 2 freeze/slack gate: one participant session completes with MCP context lookup and structured output; use this day to absorb MCP/conversation latency fixes before Phase 3.

### Phase 3: Data Quality, Re-Plan, And End-To-End Orchestration

- **2026-05-21**: Implement Data Quality Agent scoring: completeness, ambiguity, evidence links, confidence, and coverage by variable.
- **2026-05-22**: Implement JSON/CSV export and BigQuery-ready table schema with transcript snippets, context references, and quality metadata.
- **2026-05-23**: Build dashboard panels for static baseline vs Methodic: coverage states, ambiguity count, evidence-linked fields, and quality score.
- **2026-05-24**: Link Organizer -> approved schema -> Participant sessions -> Data Quality -> export.
- **2026-05-25**: Implement file-backed prototype persistence for study config, sessions, transcripts, quality states, and exports; defer Firestore/Cloud SQL unless a later task proves it is needed.
- **2026-05-26**: Set up BigQuery dataset/table/IAM and write one structured test row from local code before Cloud Run deployment.
- **2026-05-27**: Implement autonomous re-plan trigger: after P-001, P-002, and P-003, if `procurement_friction` remains `ambiguous`, add P-005, the reserve procurement stakeholder.
- **2026-05-28**: Phase 3 freeze/slack gate: full local E2E runs from a clean state and produces a repeatable demo dataset; use remaining time to stabilize BigQuery/export/re-plan before deployment.

### Phase 4: Cloud Run, Verification, And Submission Package

- **2026-05-29**: Dockerize the app; configure env vars and secrets; run production-mode local container smoke test.
- **2026-05-30**: Deploy to Cloud Run; verify service URL, ADK endpoints, session creation, Gemini calls, MCP context lookup, file-backed persistence, export, and BigQuery write path using the pre-created dataset/table.
- **2026-05-31**: Cloud stabilization/slack day; fix deployment/IAM/latency issues before demo scripting.
- **2026-06-01**: Write final 3-4 minute demo script using the deployed app; rehearse once against live Cloud Run.
- **2026-06-02**: Polish the working product UI: organizer review, participant chat, event trace, and quality dashboard.
- **2026-06-03**: Record demo video scenes and prepare GitHub README, architecture diagram, challenge explanation, and known limitations.
- **2026-06-04**: Submit challenge materials: Devpost, video, repo, architecture notes, and demo URL.
- **2026-06-05**: Buffer day and final deadline at 5:00 PM PT.

## Verification Gates

Before implementation expands beyond each phase, these gates must pass:

- **Organizer gate**: external request and clarification are visible; methodology pushback is tied to the research brief and sample plan.
- **MCP gate**: Participant Agent calls `lookup_deal_context` through MCP and logs the tool result in a developer trace.
- **Quality gate**: every required variable has a coverage state; static-form baseline and Methodic outputs can be compared with the same rubric.
- **Re-plan gate**: P-001, P-002, and P-003 leave `procurement_friction` ambiguous; unresolved coverage triggers exactly one targeted P-005 procurement session and explains why.
- **Guardrail gate**: one misunderstanding, contradiction, or frustration event is logged and handled without changing measurement intent or forcing a category.
- **Cloud Run gate**: deployed service can create a session, run the ADK agent, call MCP, persist data, export results, and write the structured table to BigQuery.

## Demo Script

Target length: 3-4 minutes. `docs/judge-storyboard.md` is the compressed narrative reference for the final video.

### 0:00-0:30 - Hook And Problem

Show a revenue dashboard: mid-market enterprise deals are slipping, and the current explanation is shallow: "price" or "not enough value."

Narration:

> Dashboards tell you what happened. Methodic captures the governed human data needed to explain why.

Show a developer event card:

- Sales Insights agent sends `request_study`.
- Methodic asks: "Should the study optimize for packaging decisions, ROI-message decisions, or both?"
- Sales Insights answers: "both."
- Methodic accepts and opens the organizer review.

Must show:

- Methodic can be invoked by another agent, not only by a human.
- The request is not a plain API call; Methodic clarifies before planning.

### 0:30-1:10 - Organizer Planning And Methodology Pushback

The organizer proposes interviewing only friendly product champions.

Methodic pushes back:

> This sample cannot answer the pricing and ROI decision. Champions can explain enthusiasm, but economic buyers and procurement stakeholders decide budget and approval. Add lost and slipping economic buyers, plus recent wins as a comparison group. Treat the output as decision-grade qualitative evidence and directional quantification, not statistically representative proof.

Show the review package:

- research brief
- target segments
- required variables
- question-to-variable map
- risk and overclaim notes

Must show:

- Agentic planning by the organizer-facing AI.
- Methodology pushback when the user's design will not answer the business question.

Compression rule:

- Do not spend video time showing every generated question. Show the pushback, then briefly show the question-to-variable map as evidence.

### 1:10-2:00 - Conversation And MCP Triangulation

Left: static survey.

- Question: "Why did you not buy?"
- Answer: "Price."
- Output: ambiguous reason, no evidence link, low confidence.

Right: Methodic participant agent.

- Participant says price was the reason.
- Methodic asks whether price means budget timing, competitor offer, procurement friction, or unclear ROI.
- Participant says finance could not prove ROI.
- Methodic calls `lookup_deal_context` and sees the trial account logged in three times but never reached report builder.
- Methodic asks whether the ROI concern came before the product proof point was reached.

Must show:

- Interactive participant conversations, not static forms.
- MCP triangulation tied to measurement intent.
- One guardrail recovery where Methodic rephrases or marks ambiguity instead of forcing an answer.

Compression rule:

- Use one critical participant interaction, then fast-forward to aggregate results. Highlight or zoom the exact Methodic follow-up and the MCP trace so the split-screen is readable.

### 2:00-2:50 - Data Quality And Re-Plan

Show the quality dashboard:

- Static baseline has high ambiguity and weak variable coverage.
- Methodic has evidence-linked values and higher coverage.
- `procurement_friction` remains `ambiguous` after three sessions and is visually marked red before the re-plan trigger.

Methodic explains:

> The current sample resolved ROI-message risk but not procurement friction. Add one targeted participant from procurement or an economic-buyer role in a slipping deal.

Show the added session resolving the variable or marking it unresolved with a caveat.

Must show:

- Measurable data quality improvement vs static-survey baseline.
- Stop condition and coverage loop.
- One autonomous re-plan decision.

### 2:50-3:30 - Export And Google Stack Close

Show export:

- structured JSON/CSV
- BigQuery structured table
- evidence quotes
- context references
- quality metadata
- final recommendation summary

Closing claim:

> Methodic is not an AI survey tool. It is the data-capture layer that turns business decisions into cleaner, evidence-linked data for downstream agents and analytics.

Stack rule:

- Keep Gemini, ADK, MCP, Cloud Run, and BigQuery visible in the developer trace/export phase, but do not let stack narration overtake the B2B win-loss story.
