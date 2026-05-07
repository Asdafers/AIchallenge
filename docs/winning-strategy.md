# Winning Strategy

## Positioning

Working name: Methodic

Position this as an autonomous research operations agent, not an AI survey tool.

Core framing:

> There are no useful insights without good data. Methodic replaces brittle forms with a multi-agent system that plans research, designs instruments, and conducts interactive participant conversations to capture clean, decision-ready data at scale.

Sharper challenge framing:

> Methodic is the research-operations agent for the agentic enterprise. Give it a business decision; it returns methodologically grounded, governed, analysis-ready data. Humans can call it, and other enterprise agents can call it.

Avoid these framings:

- SurveyMonkey with AI.
- Typeform with chat.
- Chatbot survey.
- Form generator.
- Generic customer interview bot.

The strongest wedge is not "better surveys." It is "clean data capture for companies making decisions with AI and analytics." This matters because organizations are investing heavily in analytics, RAG, and AI decision systems while still feeding them shallow, inconsistent, biased, or incomplete human input data.

Use "Methodic" for now. Alternatives from research were Probe, Datum, and Ground Truth, but Methodic remains the best fit for a methodology-forward challenge submission unless a trademark check fails.

## Differentiation

Legacy survey tools use fixed forms and branching logic. Methodic should use declarative data-capture intent: the organizer defines the business decision and required variables, then agents pursue sufficient evidence for those variables through adaptive participant conversations.

Key differentiators to show:

- Variable saturation: the participant agent keeps probing until a required variable is sufficiently clear, then stops.
- Ambiguity reduction: vague responses are clarified in the moment instead of being left for manual cleanup.
- Measurement preservation: participant agents can adapt wording and follow-ups without changing the approved research intent.
- Thematic traceability: every structured field and theme links back to transcript evidence.
- Context-aware probing: agents can use approved company context, such as product events or customer segment, to ask sharper questions.
- Data quality scoring: the output is not just answers; it includes completeness, confidence, ambiguity, and provenance metadata.
- Agent interoperability: another enterprise agent can request a study, Methodic can run it, and the clean result can be returned as a structured task completion.

The three demo moments that should make "clearly agentic" undeniable:

1. The Methodology Agent pushes back on the organizer when the requested study design would not support the business decision.
2. A Survey Agent performs a mid-interview MCP triangulation call against approved business context or product telemetry.
3. Methodic is invoked by another agent through an A2A-style request and returns a structured result.

## Methodology Claims

Be credible and specific. Do not claim the product magically solves research validity or guarantees statistical truth.

Use three kinds of rigor:

- Statistical rigor: sample-size guidance, segment quotas, confidence caveats, coverage of required variables.
- Qualitative rigor: saturation, coding consistency, verbatim evidence, interviewer-bias controls.
- Operational rigor: completion rate, ambiguity reduction, schema completeness, re-contact flags, audit trail.

Recommended demo metrics:

- Variable completion rate: how many decision-critical fields were captured.
- Ambiguity reduction: how many initially vague answers were clarified.
- Clarification rate: how often the agent asked a useful follow-up.
- Evidence coverage: percent of structured claims linked to transcript snippets.
- Confidence score by variable.
- Static survey comparison: vague answer rate and missing-variable rate.
- Saturation curve: new themes or unresolved variables flattening as sessions accumulate.
- Coding agreement: optional inter-coder reliability signal for thematic coding if it can be implemented honestly.

Useful methodology anchors to verify and cite:

- Tourangeau, Rips, and Rasinski's cognitive model of survey response.
- Krosnick's satisficing theory.
- Cognitive interviewing for question validation.
- Theoretical saturation from grounded theory.
- Lincoln and Guba's trustworthiness criteria, especially audit trails, dependability, and confirmability.
- Krippendorff's alpha for thematic coding agreement, if the prototype actually computes it.

Do not claim statistical representativeness, causal insight, bias elimination, or replacement of human researchers. Claim better capture, clearer provenance, stronger guardrails, and faster research operations.

## Agent Design

Use a collaborative specialist model.

### Organizer Agent

Owns the company-facing research planning conversation. It identifies the decision to support, target audience, hypotheses, constraints, and required outputs.

### Methodology Agent

Acts as the research scientist. It checks the plan for measurement quality, bias risks, sampling gaps, and methodological overreach.

### Question Design Agent

Creates the question pool, follow-up prompts, schema mappings, and allowed participant-facing wording variants.

### Review and Visualization Agent

Produces the visual approval package: study map, variable coverage, participant journey, bias warnings, sample plan, and launch checklist.

### Survey Agent Pool

Runs participant conversations from the approved plan. Each survey agent can personalize, clarify, and probe, but must preserve measurement intent.

### Data Quality Agent

Normalizes responses, scores quality, detects contradictions, links evidence, exports structured data, and triggers one autonomous re-plan when coverage remains insufficient.

Sampling and quota guidance belongs inside the Methodology Agent for the prototype. A separate Sampling Plan Agent makes the architecture look like a chain of named prompts instead of a coherent agent system.

## MCP and Google Stack

Use MCP to make the agentic behavior visible and credible:

- Context lookup MCP: approved product, CRM, or event context for sharper participant conversations.
- Research grounding MCP: methodology references or internal research standards.
- Storage/export MCP: write clean datasets and evidence metadata to the chosen store.

Use Google Cloud alignment as a proof point:

- Gemini for organizer, methodology, participant, and quality reasoning.
- ADK for orchestration and agent handoffs, especially `SequentialAgent`, `ParallelAgent`, and `LoopAgent` patterns where they match the workflow.
- Cloud Run for the first deployable prototype.
- BigQuery for the clean output dataset. Do not mock this if avoidable.
- A real MCP server boundary for at least one context lookup tool, even if it returns canned demo data.
- Vertex AI Search or another approved grounding path for research-methodology context if time allows.

Before implementation, verify current Google product names, recommended Gemini model, A2A status, and ADK details against the latest official docs. Current quick verification confirms ADK workflow agents include `SequentialAgent`, `ParallelAgent`, and `LoopAgent`.

## Demo Narrative

Recommended scenario: a B2B SaaS company wants to understand why mid-market enterprise deals are being lost or slipping.

Three-to-five minute demo:

1. A mocked Sales Insights agent requests a win-loss study from Methodic because mid-market deals are slipping.
2. Methodic asks one clarifying question back before accepting the task.
3. Organizer Agent confirms the business decision, audience, constraints, and required outputs.
4. Methodology Agent pushes back on a weak plan, such as only interviewing product champions when the pricing decision requires economic buyers, and cites the methodology basis.
5. Question Design Agent builds the question pool and maps every question to a decision-critical variable.
6. Review and Visualization Agent shows a polished study map for approval.
7. Participant demo:
   - Static survey captures "price" and stops.
   - Methodic asks whether price means budget timing, perceived ROI, procurement friction, competitor comparison, or missing enterprise controls.
   - The Survey Agent uses MCP to check approved telemetry or CRM context and asks a sharper, grounded follow-up.
8. Coverage remains insufficient for one variable, so Methodic adds one targeted participant session.
9. Data Quality Agent exports structured records showing that vague "price" answers were clarified into actionable categories.
10. Methodic returns the result to the requesting agent and writes clean evidence-linked data to BigQuery.

The final screen should show:

- Clean table of participant records.
- Quality and confidence scores.
- Theme summary.
- Clickable evidence snippets.
- Comparison against static survey data quality.
- Developer view showing ADK handoffs, MCP tool calls, and the inbound/outbound agent request.

## Rubric Strategy

### Technical Implementation: 30%

Show multi-agent orchestration, tool use, handoffs, state, and deployment. A developer view that displays agent traces, MCP calls, and data writes will make the technical implementation legible to judges.

### Business Case: 30%

Quantify the cost of bad input data and the speed improvement from objective to clean dataset. The business case should focus on better decisions, faster research operations, and fewer unusable responses.

### Innovation and Creativity: 20%

Lead with declarative data capture and variable saturation. The innovation is that the system pursues high-quality variables, not just completed forms.

### Demo and Presentation: 20%

Make the demo visual, concrete, and comparative. Judges should see the difference between a static survey answer and an agentically clarified answer within seconds.

## Build Priorities

1. Variable saturation logic for required fields.
2. Methodology-agent pushback patterns for sampling, leading questions, cognitive overload, and double-barreled questions.
3. Autonomous re-plan when coverage remains insufficient.
4. Real MCP server boundary for one triangulation during a participant conversation.
5. Static survey versus agentic conversation comparison.
6. Visual study review package.
7. Evidence-linked structured output.
8. Data quality scoring with ambiguity, confidence, coverage, and provenance.
9. Developer trace view for agent handoffs, MCP calls, and agent request flow.
10. Cloud Run deployment plus real BigQuery export.

## May 5 Execution Focus

As of May 5, 2026, the submission deadline is June 5, 2026. The project has about 31 days left. The highest-leverage move is to stop expanding review scope and make one live vertical slice real.

The current fixture pipeline already tells the story. It should remain as regression evidence and demo fallback, not the core build claim. The next phase must prove that Methodic can run a real agent path:

1. Organizer creates a study brief from a business decision.
2. Methodology agent pushes back on an invalid or weak study design.
3. Participant agent conducts one live Gemini-powered interview.
4. The participant path calls an MCP tool for approved deal or telemetry context.
5. Gemini extracts structured fields with schema validation.
6. A deterministic coverage checker triggers one re-plan when a variable remains ambiguous.
7. BigQuery receives at least one real export row.
8. Cloud Run hosts the demo endpoint and working UI.

The demo should make the data-quality delta visible within seconds:

- Static survey captures "price" and stops.
- Methodic asks what "price" actually means.
- Methodic uses MCP context to ask a sharper follow-up.
- The UI shows extracted fields, confidence, evidence quote, coverage state, and export result.

### Immediate Plan Correction

Before implementation resumes, revise the ADK design and implementation plan so they are executable:

- Replace FunctionTool-as-sub-agent graph nodes with wrapper/custom agents.
- Define the full session state contract instead of relying on `output_key` to append or merge participant data.
- Make LoopAgent exit a real tool/custom step that sets `tool_context.actions.escalate = True`.
- Use the current `google-genai` SDK path for Gemini structured output.
- Verify model IDs before committing to preview model names.
- Treat A2A as a proven implementation only after a real A2A client smoke test; otherwise label it as A2A-pattern.
- Add BigQuery dataset/table setup and insert-error handling.

### Next 72 Hours

1. Patch the ADK design/plan into a v2 that fixes graph semantics, state, loop exit, model IDs, and A2A claims.
2. Create the `methodic/` runtime skeleton.
3. Implement schema models plus deterministic coverage and quality wrappers.
4. Implement one Gemini structured-output extraction call.
5. Wrap the existing MCP server through ADK `McpToolset`.
6. Prove one participant session produces a validated `ParticipantResponse`.

UI work should wait until the live run produces non-empty events and coverage. The UI should then present the working experience, not a landing page.

### Winning Bar

The submission should be able to make these claims honestly:

- Methodic is an autonomous research operations agent, not a form generator.
- The demo uses Gemini, ADK, MCP, Cloud Run, and BigQuery in a visible path.
- At least one participant conversation is live, not fixture replay.
- The system produces schema-valid, evidence-linked data.
- The system measures data quality against a static-survey baseline.
- The system detects insufficient coverage and re-plans once.
- The product case is narrow and commercial: B2B SaaS win-loss research for revenue, product, and research-operations teams.

## Scope Cuts

Do not build a broad analytics dashboard. The product wins by capturing better data, not by becoming another BI surface.

Avoid:

- Voice in the first prototype unless everything else is already strong.
- Too many study types.
- Real customer data dependency.
- Overbroad statistical claims.
- Marketplace or Track 3 architecture work unless the strategy changes.
