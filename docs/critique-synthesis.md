# Critique Synthesis

This file tracks judge-style critiques and the concrete changes accepted into the plan.

## Gemini Critique

Source: `docs/critique-gemini.md`

### Accepted Changes

- Add a clarifying response from Methodic back to the requesting Sales Insights agent so the external-agent beat does not look like a plain JSON API call.
- Make the Methodology Agent pushback visibly derived from the brief, decision, and sample plan rather than a canned warning.
- Add visual proof of the variable-coverage loop and stop condition.
- Treat Data Quality as mostly deterministic validation plus structured outputs, not necessarily a separate LLM-heavy agent.
- Guarantee visible Google Cloud alignment through Cloud Run and BigQuery.
- Add explicit guardrail handling for misunderstanding, contradiction, frustration, and vague answers.
- Add a participant-engagement caveat: busy economic buyers may not complete long AI chats, so the demo and pitch must not assume universal engagement.

### Rejected Or Deferred

- Full A2A compliance remains deferred until verified. The prototype can use an A2A-style request, but the submission must avoid overclaiming production A2A support unless implemented.
- Vertex AI Search remains preferred, not guaranteed, because Cloud Run plus BigQuery is the minimum Google Cloud proof for the first vertical slice.

### Resulting Spec Changes

Updated `docs/spec.md` with:

- Clarification request JSON example.
- Methodology pushback implementation note.
- Stop-condition and per-variable coverage proof beat.
- Data Quality implementation guidance.
- Required per-variable stop-state metric.
- Google Cloud guarantee section.
- Guardrails and failure-handling section.
- Participant engagement assumption section.
- Updated build checklist items.

## Claude Critique

Source: `docs/critique-claude.md`

### Accepted Changes

- Add an autonomous re-plan beat: if coverage remains insufficient for a decision-critical variable, Methodic adds one targeted participant session.
- Treat the autonomous re-plan as the strongest anti-"AI survey" proof point.
- Fold Sampling Plan Agent into Methodology Agent to avoid an architecture that looks like a chain of renamed prompts.
- Commit to a real MCP server boundary for at least one tool call, even if the data is canned.
- Commit to real BigQuery export instead of a BigQuery-compatible fallback.
- Drop Agent Engine Sessions and Memory Bank from the prototype commitment unless implementation later demands them.
- Narrow the primary buyer to Head of Research Operations at a 200-2000 employee B2B SaaS company.
- Use three primary demo personas and reserve extras for test data.
- Add a methodology citation overlay to the Methodology Agent pushback.
- Add a competitor comparison in submission materials.

### Rejected Or Deferred

- Full production A2A compliance remains a stretch goal. The spec now asks for a real endpoint if practical, otherwise honest labeling as an A2A-pattern request.
- Pricing, TAM, and design-partner evidence are not fully solved in this critique pass. They are now recognized as business-case gaps to address before submission copy is finalized.

### Resulting Spec And Plan Changes

Updated:

- `docs/spec.md`
- `docs/architecture.md`
- `docs/build-plan.md`
- `docs/winning-strategy.md`

Key net effect:

- The demo is no longer just static survey versus chat. It must show Methodic inspecting coverage, deciding the plan is insufficient, and fielding one more targeted participant session.
