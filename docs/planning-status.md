# Methodic Planning Status

Status as of 2026-05-01 15:20 UTC. This is a planning-only snapshot for the operator, Gemini, Claude, and Codex. It does not authorize implementation work.

## Current State

- The canonical wedge is locked: B2B SaaS win-loss research for mid-market enterprise deals.
- The product thesis is locked: no useful insights without good data; Methodic is the governed data-capture layer, not an AI survey tool.
- `docs/methodic-vertical-slice.md` now defines the concrete demo path.
- `docs/delivery-plan.md` now expands the vertical slice into proof beats, delivery gates, and future work packages.
- Gemini completed a planning review with `ship-with-changes`; its findings have been reconciled into the docs.
- Gemini completed a judge-story pass; its 5-scene sequence and narrative risks have been reconciled into the vertical slice.
- Claude is blocked by credits and should review the combined vertical slice plus delivery plan when available.

## Locked Decisions

- **Track**: Track 1 Build - net-new agent system.
- **Codename**: Methodic.
- **Buyer**: Head of Research Operations at a 200-2000 employee B2B SaaS company.
- **Scenario**: Sales Insights agent requests a win-loss study after mid-market enterprise deals slip.
- **Primary proof**: Methodic clarifies ambiguous static-survey answers into evidence-linked decision variables.
- **Google stack**: Gemini API, ADK, MCP, Cloud Run, and real BigQuery structured export.
- **Scope cut**: no voice, no mobile app, no real recruitment, no broad analytics platform, no full A2A compliance unless straightforward.

## Planning Artifacts

- `docs/spec.md`: canonical product and submission spec.
- `docs/methodic-vertical-slice.md`: concrete demo path and daily build milestones.
- `docs/delivery-plan.md`: planning-only task graph, proof beats, gates, and future work packages.
- `docs/judge-storyboard.md`: compressed 3-4 minute demo narrative and story-risk mitigations.
- `docs/claude-review-packet.md`: exact Claude handoff packet for the combined adversarial review.
- `docs/build-go-checklist.md`: operator checklist for opening implementation tasks after Claude.
- `docs/implementation-task-skeletons.md`: draft future Mission task bodies; do not claim until build-go.

## Mission Task Status

- Done: Gemini vertical-slice draft, Codex technical review, Gemini delivery-plan review, Gemini judge-story pass.
- Done in this planning pass: Codex planning hygiene and draft implementation skeletons.
- Done in this planning pass: Codex reconciliation of Gemini judge-story pass.
- Open for Claude: `388eed0b-91af-406b-8557-d73bc581a2b1` - combined adversarial review of vertical slice and delivery plan.
- Duplicate older Claude task: `2584fe9c-5749-49f0-a9da-efae4f045a8d` reviews only the vertical slice. The combined task supersedes it; operator can close or ignore the older task.

## Open Risks

- **Planning review risk**: Claude may find a blocker in sequencing, feasibility, or story clarity.
- **Demo density risk**: B1-B9 may be too much for 3-4 minutes; the current mitigation is the 5-scene sequence in `docs/judge-storyboard.md`, with question generation and guardrails compressed.
- **Readability risk**: the static-vs-Methodic split-screen can become text-heavy; highlight/zoom the Methodic follow-up and MCP trace.
- **Re-plan clarity risk**: re-plan looks random unless `procurement_friction: ambiguous` is visibly marked before the trigger.
- **ADK/MCP deployment risk**: Cloud Run deployment must use deployment-safe ADK structure, MCP tool filtering, explicit timeouts, and traceable fallback.
- **Quality scoring risk**: Coverage states must be deterministic enough for the demo without pretending to prove statistical representativeness.
- **BigQuery export risk**: The spec guarantees a real BigQuery structured export; this must remain a first-class deployment acceptance item.

## Build-Go Criteria

Do not open build tasks until all of these are true:

1. `docs/spec.md`, `docs/methodic-vertical-slice.md`, and `docs/delivery-plan.md` stay aligned on the win-loss wedge.
2. Gemini's planning findings remain reconciled: schema precedes fixtures, guardrail recovery is included, reserve re-plan participant is required, and external request is an HTTP payload or honestly labeled endpoint stub.
3. Gemini's judge-story pass is complete and reconciled, or explicitly waived by the operator.
4. Claude's combined adversarial review is complete or explicitly waived by the operator due to credits/timing.
5. Any Blocker findings are resolved in docs.
6. `docs/build-go-checklist.md` is satisfied.
7. Future implementation tasks are opened from `docs/implementation-task-skeletons.md`, not improvised from memory.

## Strategy Linkage

This planning state directly supports `mission_strategy['aichallenge'].thesis` by keeping data quality as the central demo proof. It preserves `non_goals` by blocking broad platform work and a marketing landing page. It maps future work to `demo_must_show` through the proof beats and keeps `stack_alignment` visible through Gemini, ADK, MCP, Cloud Run, and BigQuery deployment gates.
