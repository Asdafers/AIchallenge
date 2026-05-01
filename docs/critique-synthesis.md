# Critique Synthesis

This file tracks judge-style critiques and the concrete changes accepted into the plan.

## Gemini Critique

Source: `docs/critique-gemini.md`

### Accepted Changes

- Add a clarifying response from Methodic back to the requesting Sales Insights agent so the external-agent beat does not look like a plain JSON API call.
- Make the Methodology Agent pushback visibly derived from the brief, decision, and sample plan rather than a canned warning.
- Add visual proof of the variable-coverage loop and stop condition.
- Treat Data Quality as mostly deterministic validation plus structured outputs, not necessarily a separate LLM-heavy agent.
- Guarantee visible Google Cloud alignment through Cloud Run and BigQuery or a BigQuery-compatible export schema.
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
