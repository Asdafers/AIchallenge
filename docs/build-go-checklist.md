# Build-Go Checklist

This checklist is for the operator after Claude's combined adversarial review. It prevents accidental implementation drift.

## Before Opening Build Tasks

- [ ] Claude completed `388eed0b-91af-406b-8557-d73bc581a2b1`, or the operator explicitly waived Claude review.
- [ ] The older duplicate Claude task `2584fe9c-5749-49f0-a9da-efae4f045a8d` is closed, ignored, or clearly superseded.
- [ ] Any Claude `Blocker` findings are resolved in docs.
- [ ] Any accepted `Major` findings are either resolved or assigned to a concrete future task.
- [ ] `docs/spec.md`, `docs/methodic-vertical-slice.md`, `docs/delivery-plan.md`, and `docs/judge-storyboard.md` agree on the B2B SaaS win-loss wedge.
- [ ] The final demo still includes all proof beats B1-B9 or intentionally documents what is narrated instead of shown.
- [ ] BigQuery remains a real structured export requirement.
- [ ] A2A is described honestly as either real endpoint support or an A2A-pattern HTTP request, not production A2A compliance unless actually implemented.
- [ ] Statistical claims are limited to operational and qualitative data-quality improvement unless stronger evidence is added.
- [ ] The repo has a clean committed planning baseline.

## Opening Implementation Tasks

Use `docs/implementation-task-skeletons.md` as the source of truth. Do not improvise tasks from memory.

Recommended opening order:

1. WP1: Study Schema And Quality Rubric.
2. WP2: Project Scaffold And Fixture Contract.
3. WP3: External Request And Organizer Flow.
4. WP4: Methodology And Question Design Review Package.
5. WP5: Participant Agent Conversation Loop.
6. WP6: MCP Context Lookup.
7. WP7: Data Quality Layer.
8. WP8: Autonomous Re-Plan.
9. WP9: Cloud Run Deployment And Demo Trace.
10. WP10: Submission Package.

Do not open all WP tasks at once unless the operator explicitly wants a broad parallel build. Prefer opening WP1-WP2 first, then using their outputs to refine downstream tasks.

## First Build Task Acceptance Floor

The first build task should not start until it has:

- [ ] A cited proof beat from `docs/delivery-plan.md`.
- [ ] A cited gate from `docs/delivery-plan.md`.
- [ ] A concrete artifact path.
- [ ] A verification command or manual check.
- [ ] A Mission outcome requirement that references `mission_strategy['aichallenge']`.

## Stop Conditions

Pause implementation and return to planning if:

- A task tries to broaden beyond win-loss research.
- A task starts a marketing landing page before the working experience.
- A task depends on real customer data or real participant recruitment.
- A task claims statistical representativeness.
- MCP, ADK, Cloud Run, or BigQuery integration assumptions fail in a way that changes the demo architecture.
