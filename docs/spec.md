# Methodic Submission Spec

## Purpose

This document is the critique-ready working spec for the Google for Startups AI Agent Challenge submission.

It should be specific enough for Claude, Gemini, NotebookLM, Perplexity, and Google deep research to critique as if they were skeptical judges. It should also be concrete enough to guide implementation.

## Submission Thesis

Methodic is an autonomous research operations agent for B2B teams.

Core claim:

> There are no useful insights without good data. Methodic turns a business decision into a governed, methodologically grounded data-capture workflow, then deploys conversational research agents that collect cleaner, richer, evidence-linked data than static forms.

Methodic is not an AI survey tool. It is the upstream data-capture layer for the agentic enterprise.

## Challenge Track

Default track: Track 1, Build - Net-New Agents.

Reason:

- This is a net-new autonomous agent system.
- The agent does not merely answer questions or generate forms.
- It plans a study, critiques methodology, designs instruments, runs participant conversations, uses tools, validates data, and exports structured results.

## Demo Wedge

Scenario: B2B SaaS win-loss research for mid-market enterprise deals.

Business problem:

A B2B SaaS company is losing or slipping mid-market enterprise deals. The revenue team has dashboard metrics but does not know why deals are failing. Static surveys produce shallow answers such as "price" or "not enough value."

Methodic turns this into a governed research workflow that clarifies whether "price" means budget timing, unclear ROI, procurement friction, competitor pressure, missing controls, weak onboarding, or another decision-relevant factor.

Why this wedge:

- Strong business value and direct revenue tie.
- Easy for judges to understand.
- Naturally supports a mocked external Sales Insights agent request.
- Supports MCP triangulation against CRM, product telemetry, or deal context.
- Makes static survey versus agentic capture easy to compare.
- Keeps scope narrow enough to build before the deadline.

## Target Buyer

Primary buyer:

- Head of Research Operations at a 200-2000 employee B2B SaaS company.

Secondary users:

- Product managers.
- Sales leadership.
- Customer success.
- Go-to-market analytics teams.

## What The Demo Must Prove

The demo must prove four things:

1. Methodic is agentic, not a form generator.
2. Methodic improves input data quality compared with static surveys.
3. Methodic is technically aligned with the Google agent stack.
4. Methodic has a clear B2B business case.

## The Five Agentic Proof Beats

### Beat 1: External Agent Request

A mocked Sales Insights agent notices deal slippage and sends a structured request to Methodic:

```json
{
  "type": "request_study",
  "requesting_agent": "sales_insights_agent",
  "decision": "Should we adjust mid-market enterprise packaging or ROI messaging?",
  "deadline": "48h",
  "target_segments": ["lost_deals", "slipping_deals", "recent_wins"],
  "business_context": {
    "quarter": "Q2",
    "pipeline_at_risk_usd": 2100000,
    "suspected_reasons": ["price", "security", "unclear_roi"]
  }
}
```

Implementation note:

- This can be a mocked A2A-style request in the prototype.
- Do not overclaim full A2A production compliance until verified and implemented.
- The goal is to show Methodic can be called by other agents, not only by humans.
- To avoid this looking like a plain API call, Methodic should ask one clarifying question back before accepting or finalizing the task.

Clarifying response example:

```json
{
  "type": "clarification_request",
  "from": "methodic",
  "to": "sales_insights_agent",
  "question": "Should the study optimize for packaging decisions, ROI-message decisions, or both? The participant mix differs.",
  "options": ["packaging", "roi_messaging", "both"]
}
```

### Beat 2: Methodology Pushback

The organizer suggests interviewing only friendly product champions.

The Methodology Agent pushes back:

> This sample is convenient but it cannot answer the pricing decision. Champions can explain product enthusiasm, but economic buyers decide budget and procurement. Recommend including economic buyers from lost and slipping deals, plus a smaller control group of recent wins. Do not claim representativeness from this sample; use it for decision-grade qualitative evidence and directional quantification.

This proves the system pursues the research goal, not merely the user's initial instruction.

Implementation note:

- The pushback must be visibly derived from the research brief, target decision, and sample plan.
- Avoid a canned one-line warning. Show the triggering condition, rationale, and concrete revision.
- The demo should use a live Gemini reasoning call for the visible methodology pushback, with deterministic critique rules only as fallback and regression tests. The UI should make clear what triggered the pushback, the rationale, and the concrete revision.

### Beat 3: MCP Triangulation During Participant Conversation

Static survey:

> Why did you not buy?
>
> "Price."

Methodic conversation:

> When you say price, what shifted the decision most: budget timing, competitor offer, procurement friction, or uncertainty about ROI?
>
> "Honestly, we could not prove ROI internally."
>
> I can see from approved trial telemetry that your team logged in three times but never reached the report-builder workflow. Was the ROI concern because the value was unclear before that point, or because the report output did not map to your business case?
>
> "We never got to the report output. The champion liked the idea, but finance never saw proof."

This proves tool use is bound to measurement intent. The agent is not chatting randomly; it is clarifying a decision-critical variable.

### Beat 4: Stop Condition And Coverage Loop

The demo must show how Methodic knows when to stop probing a participant or stop fielding more sessions.

Minimum proof:

- Required variables are visible.
- Each variable has a state: `missing`, `ambiguous`, `covered_low_confidence`, or `covered_high_confidence`.
- The Participant Agent stops probing a variable when it reaches the approved coverage threshold.
- The Data Quality step shows a coverage or saturation curve for the study.

This can be implemented deterministically for the prototype. The important thing is visual proof that Methodic is pursuing measurement coverage, not simply running a chat transcript to completion.

### Beat 5: Autonomous Re-Plan

The demo should include one visible decision where Methodic changes its plan based on collected evidence.

Preferred re-plan:

1. After three participant sessions, Methodic sees `procurement_friction` remains `ambiguous` and the saturation curve has not flattened for that variable.
2. Methodic explains the gap: the current sample has champions but not enough economic buyers or technical evaluators to resolve procurement friction.
3. Methodic adds one more participant session from the relevant segment.
4. The additional session resolves the variable or marks it unresolved with a caveat.

This is the highest-value anti-"AI survey" beat. Static survey tools can collect answers; Methodic can inspect coverage, decide the plan is insufficient, and field one more targeted session.

## Demo Script

Target length: 3-4 minutes.

### 0:00-0:20 - Problem

Show a short setup:

- Mid-market enterprise deals are slipping.
- Revenue dashboard shows the symptom, not the reason.
- Static surveys return vague answers like "price."
- Bad input data leads to bad decisions.

Spoken framing:

> Dashboards tell you what happened. Methodic captures the governed human data needed to explain why.

### 0:20-0:45 - External Agent Request

Show a developer panel or compact event card:

- Sales Insights agent sends `request_study`.
- Methodic asks one clarifying question back.
- Sales Insights agent answers.
- Methodic accepts the task.
- The organizer can review and refine the request.

Rubric served:

- Technical implementation.
- Innovation.

### 0:45-1:30 - Research Planning

Show Organizer Agent conversation:

- Confirms business decision.
- Identifies target audience.
- Defines required variables.
- Captures constraints.

Show Methodology Agent pushback:

- Flags biased sampling.
- Flags overclaim risk.
- Recommends economic buyer segment.

Show Question Design Agent:

- Maps questions to variables.
- Creates approved follow-up categories.

Rubric served:

- Technical implementation.
- Business case.
- Innovation.

### 1:30-2:20 - Split-Screen Data Capture

Left: static survey.

- Participant enters "price."
- Static survey records vague answer and stops.

Right: Methodic survey agent.

- Clarifies what "price" means.
- Uses approved context lookup.
- Captures structured answer plus quote.

Rubric served:

- Demo and presentation.
- Innovation.

### 2:20-3:10 - Data Quality Output

Show results:

- Variable coverage.
- Ambiguity reduction.
- Confidence by variable.
- Evidence-linked structured fields.
- Coverage or saturation curve.
- Autonomous re-plan: one unresolved variable triggers one additional targeted participant session.

Example result:

```json
{
  "participant_id": "P-017",
  "segment": "lost_deal_economic_buyer",
  "primary_loss_reason": "unclear_roi",
  "secondary_loss_reason": "budget_cycle",
  "price_was_vague_initially": true,
  "ambiguity_resolved": true,
  "confidence": 0.84,
  "evidence": {
    "quote": "Finance never saw proof. We never got to the report output.",
    "transcript_turn_ids": ["T-017-08", "T-017-09"],
    "context_used": ["trial_event_summary"]
  }
}
```

Rubric served:

- Technical implementation.
- Business case.
- Demo and presentation.

### 3:10-3:40 - Export and Close

Show:

- BigQuery structured output table.
- Methodic returns structured completion to the requesting Sales Insights agent.
- Developer overlay shows agent handoffs and tool calls.

Closing line:

> Methodic is the research operations agent for the agentic enterprise: decision in, governed data out.

## Agent Contracts

### External Requesting Agent

Input:

- Business decision.
- Deadline.
- Target segments.
- Business context.

Output expected:

- Study status.
- Evidence-linked summary.
- Clean dataset location.
- Methodology caveats.

### Organizer Agent

Input:

- External request or human organizer goal.

Responsibilities:

- Clarify the decision to support.
- Identify stakeholders.
- Identify constraints.
- Draft research brief.
- Route to Methodology Agent and Question Design Agent.

Output:

```json
{
  "study_id": "WL-2026-Q2-MM",
  "decision": "Adjust packaging or ROI messaging for mid-market enterprise deals",
  "audience": ["lost_deals", "slipping_deals", "recent_wins"],
  "required_variables": [
    "primary_loss_reason",
    "roi_clarity",
    "budget_timing",
    "procurement_friction",
    "security_concern",
    "competitor_pressure",
    "aha_moment_reached"
  ],
  "constraints": {
    "deadline": "48h",
    "no_sensitive_customer_data_in_demo": true
  }
}
```

### Methodology Agent

Input:

- Research brief.
- Proposed audience.
- Proposed question pool.

Responsibilities:

- Flag leading questions.
- Flag double-barreled questions.
- Flag cognitive overload.
- Flag sample mismatch.
- Flag overclaim risk.
- Recommend segments and caveats.

Output:

```json
{
  "methodology_review": {
    "status": "requires_revision",
    "pushbacks": [
      {
        "type": "sample_mismatch",
        "severity": "high",
        "message": "Champions alone cannot support a pricing or packaging decision. Include economic buyers from lost and slipping deals."
      }
    ],
    "allowed_claims": [
      "directional qualitative evidence",
      "decision-critical variable coverage",
      "ambiguity reduction"
    ],
    "disallowed_claims": [
      "statistically representative",
      "causal"
    ]
  }
}
```

### Question Design Agent

Input:

- Research brief.
- Methodology review.
- Sampling plan.

Responsibilities:

- Draft approved question pool.
- Map questions to variables.
- Define allowed follow-up categories.
- Define stop conditions for each variable.

Output:

```json
{
  "question_pool": [
    {
      "question_id": "Q-loss-reason-open",
      "prompt": "What changed between initial interest and the decision not to move forward?",
      "maps_to": ["primary_loss_reason"],
      "follow_up_policy": "clarify_vague_reason",
      "risk_flags": []
    },
    {
      "question_id": "Q-roi-clarity",
      "prompt": "What evidence would your team have needed to feel confident in the ROI?",
      "maps_to": ["roi_clarity"],
      "follow_up_policy": "probe_missing_evidence",
      "risk_flags": []
    }
  ]
}
```

### Participant Agent

Input:

- Approved study structure.
- Participant persona or participant metadata.
- Tool access policy.

Responsibilities:

- Conduct participant conversation.
- Preserve measurement intent.
- Clarify vague answers.
- Avoid leading questions.
- Use approved context lookup when needed.
- Capture structured fields and quotes.

Hard constraints:

- Must not invent unapproved claims about participant context.
- Must not ask questions outside the approved study purpose.
- Must not turn the interview into sales outreach.
- Must mark unresolved ambiguity instead of forcing a category.

Output:

```json
{
  "participant_id": "P-017",
  "transcript": [],
  "structured_fields": {},
  "field_confidence": {},
  "evidence_links": [],
  "unresolved_ambiguities": []
}
```

### Data Quality Agent

Input:

- Survey transcripts.
- Structured participant outputs.
- Approved schema.

Responsibilities:

- Normalize categories.
- Score variable coverage.
- Score ambiguity resolution.
- Link evidence.
- Detect contradictions.
- Prepare export.

Implementation note:

- Do not make Data Quality a heavyweight separate LLM step unless needed.
- Prefer structured outputs from the Participant Agent plus deterministic validation scripts for coverage, ambiguity, evidence links, and export readiness.
- Use an LLM only for the parts that genuinely need language judgment, such as contradiction review or theme naming.

Output:

```json
{
  "study_id": "WL-2026-Q2-MM",
  "quality_summary": {
    "variable_coverage_rate": 0.91,
    "ambiguity_resolution_rate": 0.72,
    "evidence_coverage_rate": 0.96,
    "mean_field_confidence": 0.81
  },
  "export_targets": [
    {"type": "bigquery", "table": "methodic_demo.win_loss_responses"},
    {"type": "json", "path": "exports/win_loss_responses.json"}
  ]
}
```

## Data Schema

### Study

```json
{
  "study_id": "string",
  "title": "string",
  "business_decision": "string",
  "deadline": "string",
  "segments": ["string"],
  "required_variables": ["string"],
  "approved_question_pool": [],
  "methodology_caveats": [],
  "status": "draft|approved|fielding|complete"
}
```

### Participant Response

```json
{
  "participant_id": "string",
  "study_id": "string",
  "segment": "string",
  "persona_summary": "string",
  "conversation_status": "complete|partial|excluded|static_form",
  "structured_fields": {
    "primary_loss_reason": "unclear_roi|budget_timing|procurement_friction|security_concern|competitor_pressure|missing_feature|economic_buyer_gap|other|unknown",
    "secondary_loss_reason": "string|null",
    "roi_clarity": "clear|partially_clear|unclear|unknown",
    "budget_timing": "in_cycle|out_of_cycle|unknown",
    "procurement_friction": "none|low|medium|high|unknown",
    "security_concern": "none|low|medium|high|unknown",
    "competitor_pressure": "none|named_competitor|unknown",
    "aha_moment_reached": "yes|no|unknown"
  },
  "field_confidence": {
    "primary_loss_reason": 0.0,
    "roi_clarity": 0.0
  },
  "coverage_state": {
    "<variable_name>": "missing|ambiguous|covered_low_confidence|covered_high_confidence"
  },
  "quality": {
    "variable_coverage": 0.0,
    "ambiguity_resolved": true,
    "evidence_linked": true,
    "requires_recontact": false
  },
  "evidence": [
    {
      "field": "primary_loss_reason",
      "quote": "string",
      "transcript_turn_id": "string",
      "context_used": ["string"]
    }
  ]
}
```

### Tool Event

```json
{
  "event_id": "string",
  "study_id": "string",
  "participant_id": "string|null",
  "agent": "string",
  "tool_name": "string",
  "input_summary": "string",
  "output_summary": "string",
  "timestamp": "string"
}
```

## Participant Personas

Use three primary personas in the live demo. Keep additional personas as test data only.

### P-001: Lost Deal Economic Buyer

- Segment: lost_deal_economic_buyer.
- Role: VP Finance.
- Initial answer: "Price was too high."
- Underlying reason: ROI proof was unclear and budget cycle had closed.
- Context lookup result: trial account had low activation and never reached report-builder workflow.
- Desired Methodic outcome: classify as `unclear_roi` with secondary `budget_timing`.

### P-002: Lost Deal Champion

- Segment: lost_deal_champion.
- Role: RevOps Manager.
- Initial answer: "Security slowed us down."
- Underlying reason: security review was manageable, and the champion suspects procurement or vendor consolidation mattered, but they cannot confirm what happened after handoff.
- Context lookup result: CRM notes mention competitor bundle.
- Desired Methodic outcome: leave `procurement_friction` as `ambiguous` or `covered_low_confidence`, with secondary `competitor_pressure`. This is intentionally unresolved after the primary three sessions so the re-plan trigger can fire.

### P-003: Slipping Deal Champion

- Segment: slipping_deal_champion.
- Role: Sales Operations Lead.
- Initial answer: "We are still interested."
- Underlying reason: champion lacks executive sponsor and cannot prove ROI.
- Context lookup result: trial usage high among operators but no executive login.
- Desired Methodic outcome: classify as `unclear_roi` plus `economic_buyer_gap`.

### P-004: Recent Win Economic Buyer

- Segment: recent_win_economic_buyer.
- Role: COO.
- Initial answer: "The business case was obvious."
- Underlying reason: fast path to report output and clear integration story.
- Context lookup result: trial account reached report-builder and invited finance user.
- Desired Methodic outcome: contrast case for `aha_moment_reached = yes`.

### P-005: Slipping Deal Procurement Stakeholder - reserve re-plan persona

- Segment: slipping_deal_procurement.
- Role: Procurement Lead.
- Initial answer: "The evaluation got stuck after the business case review."
- Underlying reason: procurement required vendor consolidation and could not justify adding another vendor without stronger ROI evidence.
- Context lookup result: CRM notes show vendor-consolidation objection and no procurement-approved exception.
- Desired Methodic outcome: resolve `procurement_friction` to `high` with secondary `unclear_roi`. This persona is held in reserve and is only fielded when `procurement_friction` remains ambiguous after P-001, P-002, and P-003.

### P-006: Lost Deal Technical Evaluator - test-only persona

- Segment: lost_deal_technical_evaluator.
- Role: IT Architect.
- Initial answer: "It was not enterprise-ready."
- Underlying reason: SSO and audit logging concerns.
- Context lookup result: security questionnaire had two unresolved items.
- Desired Methodic outcome: classify as `security_concern`.

## Static Survey Baseline

The baseline should be intentionally plausible, not absurd.

Static questions:

1. What was the main reason you did not move forward?
2. How would you rate the product value?
3. Was pricing a concern?
4. What could we improve?

Expected baseline flaws:

- Accepts vague answers.
- Does not distinguish price from ROI or budget timing.
- Cannot ask follow-up questions.
- Does not link structured categories to evidence.
- Cannot use approved context to ask sharper questions.

Prototype commitment:

- Build a thin static-form UI/path using the same fixture participants as Methodic.
- Store static answers through the same schema and quality rubric, with missing or ambiguous fields marked explicitly.
- Do not compare Methodic against a hand-authored "bad JSON" fixture only. If the static path is reduced to a fixture for time reasons, label it as a reference fixture and stop calling the delta a measured comparison.

## Metrics

### Required Demo Metrics

- Variable coverage rate.
- Ambiguity resolution rate.
- Evidence coverage rate.
- Mean field confidence.
- Static survey vague-answer rate.
- Static survey missing-variable rate.
- Per-variable stop state: `missing`, `ambiguous`, `covered_low_confidence`, or `covered_high_confidence`.

### Optional Metrics

- Saturation or coverage curve.
- Coding agreement.
- Clarification rate.
- Recontact recommendation rate.

### Metrics To Avoid Unless Verified

- Completion-rate improvement.
- Cost-per-study reduction.
- Statistically representative confidence.
- Causal claims.

## Architecture Choices

### Frontend

Build the working product experience first:

- Organizer workspace.
- Visual research plan review.
- Split-screen static survey versus Methodic conversation.
- Results and quality view.
- Developer overlay.

Avoid a marketing landing page.

### Backend

Minimal service responsibilities:

- Study state.
- Agent orchestration calls.
- Simulated participant sessions.
- Tool event log.
- Export generation.

### Agent Orchestration

Preferred ADK shape:

- `SequentialAgent`: Organizer -> Methodology -> Question Design -> Review.
- `ParallelAgent`: participant survey sessions.
- `LoopAgent` or bounded equivalent: variable coverage and saturation checks.

### Model Use

Use Gemini for reasoning and conversation. Verify current recommended model names before implementation.

Likely split:

- Higher-reasoning model for Methodology and Data Quality.
- Lower-latency model for participant conversations.

### MCP Tools

Prototype tools:

- `crm_context_lookup`: returns participant segment, deal stage, notes summary.
- `trial_telemetry_lookup`: returns approved product-usage summary.
- `dataset_export`: writes structured data to JSON/CSV locally and to BigQuery for the deployed demo.

The demo only needs one memorable MCP triangulation moment, but it should use a real MCP server boundary even if the server returns canned data. The developer overlay should show the tool call, input summary, and output summary.

### A2A-Style Request

The ideal prototype has a small real A2A endpoint or the closest practical implementation of the current protocol. If full compliance is not implemented, label it honestly as an A2A-pattern request over prototype HTTP rather than implying production A2A support.

The demo must still show:

- Requesting agent identity.
- Methodic clarification request.
- Task acceptance.
- Task completion response.

### Google Cloud

Guaranteed for the prototype:

- Cloud Run deployment.
- Real BigQuery structured export.

Strongly preferred if feasible:

- Vertex AI Search or equivalent methodology grounding.

Drop Agent Engine Sessions and Memory Bank from the prototype commitment unless they become necessary during implementation. They are not required to win the first vertical slice and add avoidable preview/dependency risk.

The architecture diagram and developer overlay must make the governed data flow visible:

1. Approved study structure.
2. Participant transcript.
3. Structured extraction.
4. Evidence links.
5. Quality scores.
6. BigQuery export.
7. Completion response to requesting agent.

### Guardrails And Failure Handling

The demo should include at least one compact failure-handling example.

Required cases to design for:

- Participant misunderstands a question.
- Participant gives contradictory information.
- Participant becomes frustrated or disengaged.
- Participant provides vague one-word answers.

Expected behavior:

- Rephrase once without changing measurement intent.
- Ask one clarifying follow-up.
- Mark unresolved ambiguity instead of forcing a category.
- Respect participant frustration and end gracefully.
- Log the guardrail event in the developer overlay.

### Participant Engagement Assumption

The business case depends on participants engaging with an AI interviewer. The submission should not assume that busy economic buyers will always complete long chats.

Mitigation in product and pitch:

- Keep participant sessions short and purpose-specific.
- Make the value exchange clear in the invite.
- Support asynchronous completion.
- Use Methodic first where the company already has a relationship with the participant.
- Treat engagement improvement as a hypothesis unless measured.

## Scope Cuts

Cut from first prototype:

- Voice.
- Mobile app.
- Real participant recruitment.
- Broad analytics dashboard.
- Multiple industries.
- Multiple study types.
- Synthetic respondents.
- Full A2A compliance unless it is straightforward.
- Claims of statistical representativeness.

## Build Checklist

### Spec Lock

- [ ] Validate demo wedge.
- [ ] Validate target buyer.
- [ ] Validate required variables.
- [ ] Validate static survey baseline.
- [ ] Validate participant personas.
- [ ] Validate Head of Research Operations as the primary buyer.

### Prototype

- [ ] Organizer workspace.
- [ ] External request card.
- [ ] Research brief generation.
- [ ] Methodology pushback.
- [ ] Question pool and schema view.
- [ ] Visual review package.
- [ ] Static survey baseline.
- [ ] Methodic participant conversation.
- [ ] MCP triangulation event.
- [ ] Per-variable stop-state view.
- [ ] Autonomous re-plan event.
- [ ] Structured response output.
- [ ] Data quality summary.
- [ ] Guardrail example for misunderstanding, contradiction, or frustration.
- [ ] Developer overlay.
- [ ] Real BigQuery export.
- [ ] Real MCP server boundary for at least one tool.
- [ ] Real or honestly labeled A2A-style endpoint.

### Submission

- [ ] Cloud Run deployment.
- [ ] README with setup and demo path.
- [ ] Architecture diagram.
- [ ] 3-4 minute video.
- [ ] Devpost submission copy.
- [ ] Source citations for methodology and business claims.
- [ ] Competitor comparison: Methodic versus Outset, Strella, and Yabble on methodology grounding, MCP, agent interoperability, autonomous replanning, and governed export.

## Critique Prompt

Use this prompt for the next critique round:

```text
Critique this Google AI Agent Challenge submission plan as if you are a skeptical judge.

Focus on:
1. What would make you dismiss this as just an AI survey tool?
2. What parts are not convincingly agentic?
3. What technical claims need proof in the demo?
4. What business-case claims are weak or unsupported?
5. What should be cut to improve execution odds?
6. What is missing from the demo that would increase score under the rubric?
7. What questions would you ask the team during judging?
8. What exact changes would most improve the chance of winning?

Be direct. Do not add new product scope unless it clearly improves judging odds.
```
