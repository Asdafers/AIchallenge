# WP2 Fixture State Matrix — Pre-Implementation Reconciliation Draft

Status: **pre-implementation design**. Authorises the WP2 mission task to build deterministic fixture data from the WP1-locked schema. Subagent must treat the matrices and conversation outlines below as binding fixture specifications.

This draft does NOT itself create fixture files; that is part of WP2 execution. WP2 depends on WP1 being complete (or at least the canonical schema being merged into spec.md and vertical-slice).

## Mission strategy linkage

- `aichallenge.thesis` — fixtures must demonstrate that conversational data capture surfaces decision-relevant signal that static forms miss. The matrix below shows which variables Methodic resolves vs. static path, making the thesis falsifiable from fixture data alone.
- `aichallenge.demo_must_show.interactive participant conversations (not static forms)` — three primary participants with three distinct conversational paths, each producing different evidence shapes.
- `aichallenge.demo_must_show.measurable data quality improvement vs. static-survey baseline` — same fixture personas drive both paths; per-variable coverage states are the measurable delta.
- `aichallenge.demo_must_show.methodology pushback when the user's design will not answer the business question` — fixtures support the pushback by giving WP4 a champion-only initial sample (P-002, P-003) that the methodology agent can flag.
- `aichallenge.non_goals.over-claiming statistical rigor` — three primary + one reserve participants are qualitative depth, not a statistical sample. Matrix outputs are descriptive coverage, never significance.
- `aichallenge.stack_alignment` — fixtures are static JSON files in repo; no live MCP/Cloud Run dependency for WP2. Live MCP arrives in WP6.

## Re-plan trigger design decision

**Decision (a) — `procurement_friction` is the SOLE ambiguous variable at trigger time.**

At the moment the re-plan trigger fires (after P-001 / P-002 / P-003 sessions complete), the study-level coverage state is:

- `procurement_friction` → `ambiguous`
- All other required variables → `covered_low_confidence` or `covered_high_confidence`

P-005 then resolves `procurement_friction` to `covered_high_confidence` (value `high`) without disturbing other variables.

Rationale:

- Cleanest demo: the re-plan card names exactly one unresolved variable. No priority/selection logic among multiple ambiguous variables is needed.
- spec.md Beat 5 supports this reading: it names exactly one variable (`procurement_friction`) and one targeted reserve session (P-005).
- Reduces WP8 (re-plan trigger) complexity to a single predicate.

Alternative (b) — multiple variables ambiguous, `procurement_friction` selected by priority — is rejected for fixture design. Re-evaluate in WP8 only if demo timing requires more visible deliberation.

## Aggregate computation rule

Study-level coverage_state per variable is computed for the re-plan trigger and the dashboard. Rule (in order):

1. **Ambiguity trump**: If any participant has `coverage_state == ambiguous` AND no participant has `coverage_state == covered_high_confidence` with a non-`unknown` actionable value for that variable, study-level = `ambiguous`. The variable is unresolved at study level.
2. **Best wins**: Else study-level = best per-participant `coverage_state` observed (rank: `covered_high_confidence` > `covered_low_confidence` > `missing`). At least one resolution is enough to call the study-level question answered for the segment.

Rationale: rule 1 ensures the re-plan trigger fires when explicit unresolved signal exists somewhere in the study; rule 2 ensures we don't trigger re-plans for variables where at least one participant gave a defensible answer.

Note distinction between the value `unknown` and the state `missing`/`ambiguous`:

- A `covered_high_confidence` record with value `unknown` means **we resolved that the variable did not apply to this participant** with strong context evidence (e.g. CRM confirms procurement was never engaged). It contributes to study coverage.
- A `covered_low_confidence` record with value `unknown` means **we inferred non-applicability with weak/single-source evidence**. It contributes weakly.
- An `ambiguous` state means **we have evidence pointing at the variable but cannot map it confidently**. It does not contribute to coverage and triggers rule 1 if no other participant resolves the variable.

## Per-participant per-variable matrix (Methodic path, after primary three sessions)

Cells show `(coverage_state, value)` contributed by that participant's session.

| Variable | P-001 (lost_deal_economic_buyer) | P-002 (lost_deal_champion) | P-003 (slipping_deal_champion) | Aggregate (study) |
| --- | --- | --- | --- | --- |
| primary_loss_reason | covered_high (`unclear_roi`) | covered_low (`competitor_pressure`) | covered_high (`unclear_roi`) | covered_high |
| secondary_loss_reason | covered_low (`budget_timing`) | covered_low (`procurement_friction`) | covered_high (`economic_buyer_gap`) | covered_high |
| roi_clarity | covered_high (`unclear`) | covered_low (`partially_clear`) | covered_high (`unclear`) | covered_high |
| budget_timing | covered_high (`out_of_cycle`) | covered_low (`unknown`) | covered_low (`unknown`) | covered_high |
| **procurement_friction** | **covered_low (`unknown`)** | **ambiguous** | **ambiguous** | **ambiguous** ← TRIGGER |
| security_concern | covered_high (`none`) | covered_high (`low`) | covered_high (`none`) | covered_high |
| competitor_pressure | covered_high (`none`) | covered_low (`named_competitor`) | covered_high (`none`) | covered_high |
| aha_moment_reached | covered_high (`no`) | covered_low (`no`) | covered_high (`no`) | covered_high |

Why `procurement_friction` aggregate is `ambiguous`:

- P-001: economic buyer in a lost deal that closed *before* procurement-stage involvement. Variable is **inferred** as not-applicable from the absence of procurement-stage activity in the deal record. Single-source, no MCP corroboration → coverage `covered_low_confidence` (value `unknown`). Truthful: we are guessing it didn't matter, we did not measure it.
- P-002: champion who lost visibility post-handoff. Says procurement *may* have mattered but cannot confirm. Coverage `ambiguous`.
- P-003: champion in slipping deal, no procurement contact yet. Coverage `ambiguous`.

Under the aggregate rule (1) — "ambiguity trump: any participant ambiguous AND no participant covered_high with actionable value → study-level ambiguous" — the study-level state is `ambiguous`. No rule amendment needed.

After P-005 contributes `covered_high_confidence (high)`, rule 1 no longer applies (we have a covered_high with a non-`unknown` value), so rule 2 promotes the study-level state to `covered_high_confidence` and the variable is resolved.

## After P-005 (re-plan execution)

| Variable | P-005 contribution | New aggregate |
| --- | --- | --- |
| procurement_friction | covered_high (`high`) | covered_high ← RESOLVED |

P-005 is restricted to procurement-relevant probing in WP8's re-plan card; conversation outline below ensures other variables stay at their pre-P-005 study-level states.

## Conversation outlines (deterministic fixtures)

WP2 fixture transcripts must produce the exact coverage states above. These outlines pin the conversational path; WP5 (Participant Agent) follows them deterministically when running against fixture personas.

### P-001: Lost Deal Economic Buyer (VP Finance)

| Turn | Speaker | Text (fixture) | Variable affected | Outcome |
| --- | --- | --- | --- | --- |
| T-001-01 | Methodic | "What changed between initial interest and not moving forward?" | primary_loss_reason | open probe |
| T-001-02 | P-001 | "Price was too high." | — | vague |
| T-001-03 | Methodic | "When you say price, do you mean budget timing, ROI proof, procurement, or competitor offer?" | primary_loss_reason | clarification |
| T-001-04 | P-001 | "ROI. Finance never saw proof." | primary_loss_reason | `unclear_roi` |
| T-001-05 | Methodic | (calls `lookup_deal_context` MCP) → trial_usage `report_builder_reached: false` | — | MCP context |
| T-001-06 | Methodic | "The trial shows your team logged in three times but never reached the report-builder workflow. Was the ROI concern because the value was unclear, or because the report output didn't map to your business case?" | roi_clarity | context-grounded probe |
| T-001-07 | P-001 | "Finance never saw proof. We never got to the report output." | roi_clarity, primary_loss_reason | `unclear` ; aha_moment `no` |
| T-001-08 | Methodic | "Was budget timing a factor independent of the ROI proof?" | budget_timing | probe |
| T-001-09 | P-001 | "The quarter had closed by the time we were ready to commit." | budget_timing | `out_of_cycle` |
| T-001-10 | Methodic | "Anything related to procurement, security review, or a competitor we should know about?" | procurement_friction, security_concern, competitor_pressure | catch-all |
| T-001-11 | P-001 | "No procurement involvement — the deal closed before we got there. No security or competitor issues." | procurement_friction, security_concern, competitor_pressure | `unknown`, `none`, `none` |

P-001 produces no guardrail events; conversation_status `complete`.

### P-002: Lost Deal Champion (RevOps Manager) — guardrail-event source

| Turn | Speaker | Text (fixture) | Variable affected | Outcome |
| --- | --- | --- | --- | --- |
| T-002-01 | Methodic | "What changed between initial interest and not moving forward?" | primary_loss_reason | open probe |
| T-002-02 | P-002 | "Security slowed us down." | primary_loss_reason | initial signal |
| T-002-03 | Methodic | "What part of security — controls you didn't have, audit log, SSO, or something else?" | security_concern | clarification |
| T-002-04 | P-002 | "Honestly the security review was manageable in the end. I think procurement or vendor consolidation mattered more, but I lost visibility after handoff." | security_concern, procurement_friction | sec=`low` ; procurement initial=`ambiguous` |
| T-002-05 | Methodic | (calls `lookup_deal_context` MCP) → CRM notes mention competitor bundle | — | MCP context |
| T-002-06 | Methodic | "The CRM mentions a competitor bundle — was the procurement decision tied to consolidating with another vendor?" | procurement_friction, competitor_pressure | context-grounded probe |
| T-002-07 | P-002 | "Maybe. I'd be guessing — I wasn't in those conversations." | procurement_friction | stays `ambiguous` ← KEY |
| T-002-08 | Methodic | (logs `participant_vague_answer` guardrail event GE-...-001 → variable_affected `procurement_friction`, action_taken `mark_ambiguous`, measurement_intent_preserved `true`) | — | guardrail emitted |
| T-002-09 | Methodic | "Got it — I'll mark procurement as ambiguous rather than guess. Was there a competitor offer you can confirm?" | competitor_pressure | rephrase |
| T-002-10 | P-002 | "Yes, they mentioned a bundled deal from a competitor we already use elsewhere." | competitor_pressure | `named_competitor` (low conf, hearsay) |

P-002 emits exactly one guardrail event of type `participant_vague_answer`. Variable affected: `procurement_friction`. This is the canonical fixture for Beat 9 (guardrail recovery).

### P-003: Slipping Deal Champion (Sales Operations Lead)

| Turn | Speaker | Text (fixture) | Variable affected | Outcome |
| --- | --- | --- | --- | --- |
| T-003-01 | Methodic | "Where does the deal stand right now?" | — | open |
| T-003-02 | P-003 | "Still interested but stalled." | — | — |
| T-003-03 | Methodic | "What would need to change to move it forward?" | primary_loss_reason | probe |
| T-003-04 | P-003 | "Honestly we can't prove ROI to my VP. He hasn't even logged in." | primary_loss_reason, roi_clarity | `unclear_roi` ; `unclear` |
| T-003-05 | Methodic | (calls `lookup_deal_context` MCP) → trial_usage shows operator users active, no executive logins | — | MCP confirms |
| T-003-06 | Methodic | "Trial usage confirms that — operator users are active, no executive logins. Sounds like an executive-buyer engagement gap rather than a product-fit gap?" | secondary_loss_reason | context-grounded |
| T-003-07 | P-003 | "Exactly. My VP is the blocker." | secondary_loss_reason | `economic_buyer_gap` |
| T-003-08 | Methodic | "Was procurement involved at any point?" | procurement_friction | probe |
| T-003-09 | P-003 | "Not yet. We never got that far — the VP hasn't engaged." | procurement_friction | `ambiguous` |

`unknown` vs `ambiguous` rationale: deal is slipping (not lost) — procurement could become a factor; insufficient evidence to declare `none`. Coverage `ambiguous`.

### P-005: Slipping Deal Procurement Stakeholder (Procurement Lead) — re-plan path

| Turn | Speaker | Text (fixture) | Variable affected | Outcome |
| --- | --- | --- | --- | --- |
| T-005-01 | Methodic | "What's the status of the evaluation from your side?" | — | open |
| T-005-02 | P-005 | "Stuck after the business case review." | — | — |
| T-005-03 | Methodic | "What blocked it at that stage?" | procurement_friction | targeted probe (re-plan card has procurement scope) |
| T-005-04 | P-005 | "We're consolidating vendors. To add another vendor we need stronger ROI evidence than the team brought." | procurement_friction, secondary_loss_reason | `high` ; `unclear_roi` |
| T-005-05 | Methodic | (calls `lookup_deal_context` MCP) → CRM notes show vendor-consolidation objection, no procurement-approved exception | — | MCP confirms |
| T-005-06 | Methodic | "The CRM confirms a consolidation policy. Is the policy absolute, or could a strong ROI case override it?" | procurement_friction | refine |
| T-005-07 | P-005 | "An exception exists but the bar is high. The team didn't meet it." | procurement_friction | confirms `high` |

P-005 contribution: procurement_friction `covered_high_confidence` value `high`. No new ambiguity for other variables; the re-plan card scopes the conversation to procurement, so P-005 only updates `procurement_friction` and `secondary_loss_reason` (low-conf supporting).

## Static-form baseline matrix

Same fixture personas, run through the four-question static-form path (see WP1 reconciliation, "Static-form baseline schema").

| Variable | P-001 static | P-002 static | P-003 static | Aggregate |
| --- | --- | --- | --- | --- |
| primary_loss_reason | ambiguous (raw "Price was too high.") | ambiguous (raw "Security slowed us down.") | missing (raw "Still interested but stalled.") | ambiguous |
| secondary_loss_reason | missing | missing | missing | missing |
| roi_clarity | missing | missing | missing | missing |
| budget_timing | covered_low (yes/no proxy) | missing | missing | covered_low |
| procurement_friction | missing | missing | missing | missing |
| security_concern | missing | covered_low (mentioned in primary answer) | missing | covered_low |
| competitor_pressure | missing | missing | missing | missing |
| aha_moment_reached | missing | missing | missing | missing |

This is the measurable Beat 7 delta:

- Methodic resolves 7/8 variables to `covered_high_confidence` study-level after primary three sessions (post-re-plan: 8/8 with `procurement_friction` resolved to `covered_high_confidence`).
- Static form resolves 0/8 to `covered_high_confidence`; 2/8 to `covered_low_confidence` (budget_timing weak yes/no proxy; security_concern from incidental mention); 1/8 to `ambiguous` (primary_loss_reason); 5/8 `missing`.
- Static `ambiguity_resolution_rate` is low (records have unresolved ambiguity); Methodic `ambiguity_resolution_rate` reaches 1.0 after re-plan.

## Acceptance verification (executable artifact)

WP2 must produce `scripts/validate_fixtures.py` that:

1. Loads each persona fixture transcript and the persona metadata files.
2. Computes per-participant `coverage_state` per variable from the structured_fields/evidence outputs.
3. Computes study-level aggregate per variable using the rule in this document.
4. **Asserts (primary three)**: aggregate `procurement_friction == ambiguous`; all other required-variable aggregates ∈ {`covered_low_confidence`, `covered_high_confidence`}.
5. **Asserts (post-replan)**: after applying P-005, aggregate `procurement_friction == covered_high_confidence`; no other aggregate state changes.
6. **Asserts (guardrail)**: P-002 fixture emits exactly one event of type `participant_vague_answer` with `variable_affected == procurement_friction`, `measurement_intent_preserved == true`, `trigger.transcript_turn_id == "T-002-07"`, and `action_taken == "mark_ambiguous"`. Per sign-off resolution #1.
7. **Asserts (P-001 procurement evidence)**: P-001 fixture emits exactly one evidence entry for `procurement_friction` with `context_used == []` (no MCP corroboration). Per sign-off resolution #3 — adding MCP context here would promote the state to `covered_high_confidence` and break the re-plan trigger.
8. **Asserts (static baseline)**: static-baseline matrix matches the table above; static `ambiguity_resolved == false` for at least P-001 and P-002.
9. **Asserts (schema)**: every fixture-emitted Participant Response and Guardrail Event passes the WP1 JSON Schema validators (re-uses `scripts/validate_schemas.py`).

Run command: `python scripts/validate_fixtures.py`.

WP2 acceptance gate: `python scripts/validate_fixtures.py` exits 0.

## Files WP2 must create

- `fixtures/request_study.json` — Sales Insights → Methodic `request_study` payload.
- `fixtures/clarification_response.json` — Methodic clarification + Sales Insights answer.
- `fixtures/personas/P-001.json` through `P-005.json` — persona metadata, canned transcript turns, expected Participant Response output.
- `fixtures/crm/<persona_id>.json` — CRM context records returned by `lookup_deal_context` (one per persona that requires it: P-001/P-002/P-003/P-005).
- `fixtures/telemetry/<persona_id>.json` — telemetry context records (P-001/P-003 use trial_usage; P-002 uses CRM-only).
- `fixtures/static_baseline/<persona_id>.json` — static-form raw answers per persona.
- `scripts/validate_fixtures.py` — validator described above.

## Out of scope for WP2

- Live MCP server (WP6). Fixture CRM/telemetry files are static JSON read directly by tests; the WP2 validator must NOT require MCP transport.
- Participant Agent conversation engine (WP5). Transcripts are deterministic fixture turns, not generated.
- Re-plan trigger logic (WP8). Fixture data supports the trigger, but the trigger predicate is implemented later.
- Methodology agent pushback content (WP4). Fixtures only need to provide the champion-only initial sample shape that WP4 will react to.

If validation needs a stub (e.g., a small `extract_coverage_state(transcript)` helper), WP2 may include it under `fixtures/_lib/` and must label it `# STUB: replaced in WP5`.

## Reviewer sign-off resolutions

Signed off (Codex review, 2026-05-01). Decisions are locked; WP2 implementation must follow them.

1. **Guardrail event timing — confirmed at P-002 T-002-07 (trigger) / T-002-08 (logged).** The event fires *after* the MCP-grounded probe so the participant's explicit "I'd be guessing" answer becomes the trigger. This makes the narrative beat: Methodic asks a context-sharper question, the participant signals genuine uncertainty, Methodic visibly preserves measurement intent by marking `procurement_friction` ambiguous rather than forcing a category. WP2 fixture transcript and `validate_fixtures.py` must assert this exact (turn, action) pairing.
2. **`secondary_loss_reason` aggregate kept at `covered_high_confidence`.** P-003's `economic_buyer_gap` is a clean, context-grounded signal; relaxing the aggregate would reduce fixture crispness without strengthening the re-plan story. **Presentation constraint**: the demo (and any reviewer-facing copy) must NOT present this as "the study-level secondary loss reason". It must be framed as "at least one high-confidence secondary reason was identified across the study," with row-level outputs preserving per-participant variance (P-001 `budget_timing`, P-002 `procurement_friction`, P-003 `economic_buyer_gap`). WP7 dashboard copy and WP10 demo script must respect this framing.
3. **P-001 `procurement_friction == covered_low_confidence (unknown)` confirmed.** Better than `missing`: P-001 *does* answer the question, but only as inferred non-applicability without strong corroboration. Keeps the aggregate rule honest — P-001 contributes weak non-applicability while P-002/P-003 keep the study-level field `ambiguous` until P-005 resolves it. WP2 fixture for P-001 must record one evidence entry justifying the inference (e.g. CRM note that procurement was never engaged), not zero evidence (which would be `missing`), and must NOT record an MCP corroboration (which would push it to `covered_high_confidence`).
