# Claude Review: Methodic Winning Strategy

**Date:** 2026-05-05  
**Task:** 228ce6d5-4210-4912-ad8f-14deb2850170  
**Reviewer:** claude-2026-05-05T1018-STRT  
**Verdict:** APPROVE with 3 minor recommendations

---

## Context

Reviewed `docs/winning-strategy.md` (258 lines) with focus on the `May 5 Execution Focus` section. Cross-referenced against `docs/codex-plan-review.md` (9 findings, 2 BLOCKERs) and `docs/codex-design-review.md` (10 findings, 1 BLOCKER). The implementation has already addressed all design/plan BLOCKERs on branch `feat/methodic-adk-agent` (20 commits, 43 tests passing).

---

## Finding 1 — NOTE — Strategy positioning is strong and correctly scoped

The "autonomous research operations agent" frame avoids every losing position (survey tool, chatbot, form builder). The B2B win-loss vertical is narrow enough to be credible and broad enough to suggest TAM. The three demo moments (methodology pushback, MCP triangulation, A2A invocation) directly map to rubric categories.

No action needed.

## Finding 2 — NOTE — The 72-hour execution plan corrections have already been implemented

The `Immediate Plan Correction` section lists 7 revisions (FunctionTool-as-sub-agent, state contract, loop exit, genai SDK, model IDs, A2A label, BigQuery setup). All 7 are now implemented and review-verified:

- Custom BaseAgent steps: `turn_checker_step.py`, `extractor_step.py`, `coverage_step.py`, `bigquery_export_step.py`, `session_init_step.py`
- State contract: 13 keys, SessionInitStep manages participant rotation
- Loop exit: async generator yields Event, `ctx.actions.escalate = True` on both inner and outer loops
- SDK: `google-genai` with `response_schema` (not `response_json_schema`)
- Model: `MODEL_STABLE_FALLBACK = "gemini-2.5-flash"` defined
- A2A: labeled "A2A-shaped prototype" with correct card path and authentication field
- BigQuery: `_ensure_bigquery_table()`, `fail_on_error`, `asyncio.to_thread`

The strategy doc should be updated to note these are complete, not pending.

## Finding 3 — MINOR — Missing "proof of live" in the Winning Bar section

The Winning Bar (lines 238-246) claims "at least one participant conversation is live, not fixture replay." The current implementation uses a simulated participant (`participant_sim_agent`) with Gemini generating both sides. This is technically live (real LLM conversations, not fixture replay), but judges might expect a human-in-the-loop option.

**Mitigation:** Add one sentence to the Winning Bar clarifying: "Live means Gemini-powered adaptive conversation, not pre-recorded fixture replay. Human participant mode is architecturally supported via the A2A endpoint but not demonstrated in the 5-minute demo." This sets expectations honestly.

## Finding 4 — MINOR — Business case section lacks a single quantified claim

The rubric allocates 30% to Business Case. The strategy says "Quantify the cost of bad input data" but never provides the number. Judges scanning for ROI will find methodology rigor and demo metrics, but no dollar figure or time-saved estimate.

**Mitigation:** Add one concrete anchor: "Enterprise B2B win-loss studies cost $15K-$50K per engagement with 4-8 week timelines. Methodic reduces the capture phase from weeks to hours while producing higher-quality, schema-valid data." This doesn't need to be proven — it's a product positioning claim, not a statistical assertion.

## Finding 5 — MINOR — Demo narrative step 6 (Review and Visualization Agent) is not implemented

The strategy's 10-step demo narrative includes "Review and Visualization Agent shows a polished study map for approval" (step 6). This agent doesn't exist in the implementation. The current flow is: organizer → methodology → question_design → fieldwork → quality → export.

**Mitigation:** Either cut step 6 from the demo narrative and rely on the demo UI overlay as the visualization surface, or rename it to "the Demo UI displays the study plan and coverage state for visual verification." Don't promise an agent that doesn't exist.

## Finding 6 — NOTE — Scope cuts are correct and should be enforced

The scope cuts section (voice, multiple study types, real customer data, statistical claims, marketplace work) are exactly right. The risk is scope creep in the remaining 30 days. The strategy should be treated as a scope ceiling, not a wishlist.

---

## Sequencing Assessment

The 72-hour focus (patch design → skeleton → schemas → extraction → MCP → one validated session) was correct and has been executed. The remaining work is:

1. **Merge feature branch to main** — unblocks deployment
2. **Cloud Run deployment** — proves the "deployed, not localhost" claim
3. **Live smoke test with real Gemini** — proves the "live, not fixture" claim
4. **Demo recording** — the 3-5 minute video with the data-quality comparison
5. **Submission packaging** — README, architecture diagram, business case one-pager

This sequencing is correct. The strategy doesn't need to change — it needs to be executed.

---

## Agreement with Codex Reviews

The Codex plan review (9 findings) and design review (10 findings) identified real implementation risks. All BLOCKERs and MAJORs have been addressed in code. The strategy document's `Immediate Plan Correction` section correctly predicted every issue. This is a sign the strategy is well-calibrated.

---

## Final Verdict

**APPROVE.** The strategy is correctly positioned, the execution focus is well-sequenced, and the winning bar is achievable with the current codebase. The three minor recommendations (proof-of-live language, one quantified business claim, cut the unimplemented visualization agent from the narrative) are polish, not blockers.

Strategy linkage: `mission_strategy['aichallenge'].vertical_slice` (Methodic end-to-end), `demo_must_show` (live conversation + data quality delta), `stack_alignment` (Gemini/ADK/MCP/Cloud Run/BigQuery).
