# Claude Review Packet

This packet is for Claude's next planning-only adversarial review. It summarizes what to read, what changed, and what verdict the operator needs before implementation tasks are opened.

## Active Claude Task

Use this Mission task:

- `388eed0b-91af-406b-8557-d73bc581a2b1` - **Adversarial review of Methodic vertical slice and delivery plan**

Ignore or operator-close this superseded task:

- `2584fe9c-5749-49f0-a9da-efae4f045a8d` - older vertical-slice-only review. The combined task supersedes it because it includes `docs/delivery-plan.md`, Gemini's planning review findings, and the judge-story reconciliation.

## Files To Read

Read these in order:

1. `docs/spec.md` - canonical product and submission spec.
2. `docs/methodic-vertical-slice.md` - concrete demo path and daily milestones.
3. `docs/delivery-plan.md` - proof beats, gates, and future work packages.
4. `docs/judge-storyboard.md` - compressed 3-4 minute video narrative.
5. `docs/planning-status.md` - current decisions, open risks, and build-go criteria.
6. `docs/implementation-task-skeletons.md` - draft future Mission task bodies; do not claim until build-go.

Optional context:

- `AGENTS-PROTOCOL.md` - Mission Control protocol.
- `docs/critique-gemini.md`, `docs/critique-claude.md`, and `docs/critique-synthesis.md` - earlier critique history.

## What Changed Since The First Vertical Slice

- The scenario was realigned to the locked B2B SaaS win-loss wedge.
- The delivery plan now requires schema/rubric before fixtures.
- The proof beats now include guardrail recovery.
- The plan requires a reserve participant fixture for autonomous re-plan.
- The external Sales Insights request is now an HTTP `request_study` payload or honestly labeled endpoint stub.
- BigQuery is now explicit as a real structured export requirement, not only JSON/CSV.
- Gemini's judge-story pass compressed the video into five scenes:
  1. Hook and problem.
  2. Agentic planning and methodology pushback.
  3. Conversation and MCP triangulation.
  4. Data quality and autonomous re-plan.
  5. Export and Google stack close.
- The vertical-slice demo script now includes readability mitigations for split-screen text, re-plan clarity, and stack-distraction risk.

## Review Questions

Claude should answer:

1. Does the plan still prove Methodic is more than an AI survey tool?
2. Is the scope feasible by the 2026-06-05 deadline?
3. Are WP1-WP10 sequenced correctly, especially schema -> fixtures -> organizer -> participant -> MCP -> quality -> re-plan -> Cloud Run?
4. Are the demo proof beats too dense for a 3-4 minute video?
5. Are any claims still overreaching, especially around statistical rigor, A2A compliance, or autonomous behavior?
6. Are the Google stack requirements visible enough without distracting from the B2B value story?
7. Should implementation tasks be opened now, opened after changes, or held?

## Required Claude Outcome

The Mission outcome must include:

1. Numbered issues with severity: `Blocker`, `Major`, or `Minor`.
2. At least 3 falsifiable assumptions whose failure would invalidate the plan.
3. Explicit verdict: `ship-as-is`, `ship-with-changes`, or `rewrite`.
4. Build-go recommendation: open implementation tasks now, open after specific changes, or hold.
5. Strategy linkage to `mission_strategy['aichallenge'].thesis`, `demo_must_show`, `non_goals`, or `stack_alignment`.

## Current Recommendation Before Claude Review

Hold implementation tasks until Claude completes the combined review or the operator explicitly waives it. The planning packet is coherent enough for adversarial review, but not yet approved for build.
