# Claude Review: Methodic Live Demo Deployment Design

**Date:** 2026-05-06
**Task:** f412e386-eb3c-4f3e-b659-93fc0a88301d
**Reviewer:** claude-2026-05-06T1300-DPLY
**Verdict:** APPROVE with 3 required pre-deployment fixes

---

## Context

Reviewed `docs/live-demo-deployment-design.md` (347 lines) against the current implementation on `feat/methodic-adk-agent` (20 commits, 43 tests passing). Cross-referenced `methodic/server.py`, `methodic/demo_runner.py`, `methodic/static/demo.html`, `methodic/__init__.py`, `Dockerfile`, and `docs/winning-strategy.md`.

---

## Finding 1 — NOTE — This is the correct next move

The design correctly identifies that remaining risks are live-environment risks, not architecture risks. The local codebase has 43 passing tests, schema/fixture validators pass, and all review findings (Codex design review, Claude strategy review) have been addressed. No amount of additional local planning will answer whether Cloud Run can run the MCP subprocess, whether Gemini model IDs work at runtime, or whether BigQuery IAM is correctly configured. Deployment is the right action.

No action needed.

## Finding 2 — MINOR — Phase 0 should explicitly include merge to main

The deployment design says "push the branch to the private GitHub repo" but does not mention merging `feat/methodic-adk-agent` into `main`. The winning strategy's sequencing assessment lists "Merge feature branch to main" as step 1, before Cloud Run deployment. Deploying from a feature branch creates unnecessary fragility — if the branch is accidentally deleted or rebased, the deployed artifact has no clean base.

**Mitigation:** Add a step to Phase 0: "Merge `feat/methodic-adk-agent` to `main` after tests pass. Deploy from `main`."

## Finding 3 — MAJOR — No `/health` endpoint in `server.py`

The Phase 2 acceptance gate requires `GET /health` to return success, but `methodic/server.py` does not define a `/health` route. The `get_fast_api_app()` from ADK may or may not expose one, and the fallback path (`FastAPI(title="Methodic ADK Agent")`) definitely does not. Cloud Run also uses health checks for readiness probing — without an explicit endpoint, the service may fail readiness checks.

**Mitigation:** Add to `create_app()`:

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

This is a two-line fix but blocks the acceptance gate if omitted.

## Finding 4 — MAJOR — Events polling will duplicate entries in the UI

The demo UI (`demo.html`) polls `GET /api/demo/{id}/events` every 2 seconds and appends all returned events to the conversation log. But the server endpoint returns the full events list on every call. After three polls, a 5-event pipeline will show 15 entries in the UI. This makes the demo look broken to judges.

**Mitigation:** Either:
- (A) Track the last-seen event index on the client and only render new events: `fetch(base + '/events?since=' + lastIdx)` with server-side slicing, or
- (B) Track the displayed count client-side and skip already-shown events: `events.slice(lastSeen).forEach(...)`.

Option B requires no server changes and is the faster fix.

## Finding 5 — MAJOR — Demo events lack conversation content

The `demo_runner.py` appends events as `{"step": event.author, "status": "done"}` — just the agent name, no actual conversation text. The UI tries to display `ev.text || ev.content || ev.message || JSON.stringify(ev)`, which will fall through to `JSON.stringify` for every event, rendering raw JSON like `{"step":"interviewer","status":"done"}` instead of actual interview turns.

This matters because the winning strategy says: "Judges should see the difference between a static survey answer and an agentically clarified answer within seconds." The current implementation cannot show this difference — the live conversation panel will display a list of agent names, not interview dialogue.

**Mitigation:** In `demo_runner.py`, extract actual content from ADK events:

```python
if hasattr(event, "author") and event.author:
    content = ""
    if hasattr(event, "content") and event.content:
        if hasattr(event.content, "parts"):
            content = " ".join(
                p.text for p in event.content.parts if hasattr(p, "text") and p.text
            )
    session["events"].append({
        "step": event.author,
        "status": "done",
        "text": content or f"[{event.author} completed]",
        "role": "agent" if event.author != "participant_sim" else "participant",
    })
```

This is the single highest-impact fix for judge perception.

## Finding 6 — MINOR — Model fallback is defined but not wired

`methodic/__init__.py` defines `MODEL_STABLE_FALLBACK = "gemini-2.5-flash"` but no code uses it. If `gemini-3.1-pro-preview` is unavailable at deployment time (model deprecation, preview expiry, API quota), every LlmAgent will fail with an API error. The design's risk section mentions this but the mitigation ("use gemini-2.5-flash as the default") contradicts the current code which hardcodes preview models.

**Mitigation:** Add model validation at startup. In `create_app()` or as a lifespan hook, attempt a trivial Gemini call with the configured model. If it fails, log a warning and swap all agent model references to `MODEL_STABLE_FALLBACK`. Alternatively, make `MODEL` read from an environment variable with `gemini-2.5-flash` as the default:

```python
MODEL = os.environ.get("METHODIC_MODEL", "gemini-2.5-flash")
```

This makes deployment robust without code changes — just set the env var on Cloud Run.

## Finding 7 — MINOR — Static survey panel is descriptive prose, not comparative data

The winning strategy says judges should see "Clean table of participant records... Comparison against static survey data quality" and "the difference between a static survey answer and an agentically clarified answer within seconds." The current UI shows a paragraph of text about traditional surveys on the left, and (eventually) event logs on the right. This is a description-vs-data comparison, not a data-vs-data comparison.

**Mitigation:** Replace the left panel prose with a simulated static survey result showing the same participant's answers as they would appear in a traditional survey: `"Why did you choose a competitor?" → "Price"`, with a visible data quality gap (no follow-up, no evidence, confidence unknown). Then the right panel shows Methodic's clarified version with structured fields, evidence quotes, and confidence scores. This is the demo's most important visual moment.

## Finding 8 — MINOR — Phase 5 business case should include the quantified anchor

The Claude strategy review (Finding 4) recommended adding a concrete business claim: "Enterprise B2B win-loss studies cost $15K-$50K per engagement with 4-8 week timelines. Methodic reduces the capture phase from weeks to hours while producing higher-quality, schema-valid data." The deployment design's Phase 5 mentions a "short business-case section" but doesn't include this anchor. The rubric allocates 30% to Business Case — a missing dollar figure leaves judges without an ROI frame.

**Mitigation:** Add the quantified claim to Phase 5's business-case bullet list.

## Finding 9 — NOTE — Credit policy is appropriately conservative

The $500 budget guardrails are well-designed. Min instances at zero, one project, one Cloud Run service, one BigQuery dataset, short scripted smoke runs. The exclusions (no GKE, no multi-region, no Vertex AI Search before vertical slice works) are exactly right. No change needed.

## Finding 10 — NOTE — Risk section is realistic and honest

All six identified risks are real deployment risks, and the mitigations are practical. The A2A risk mitigation ("label it A2A-pattern unless a real client passes") is particularly mature — overstating A2A compliance would be a rubric liability, not an asset.

## Finding 11 — MINOR — MCP subprocess may need Cloud Run filesystem awareness

The design identifies "Cloud Run cannot spawn the stdio MCP server cleanly" as a risk, but the mitigation doesn't address Cloud Run's read-only container filesystem (except `/tmp`). If `wp6_mcp_server.py` writes temporary files or logs to the working directory, it will fail silently. The `Dockerfile` copies the script to `/app/scripts/`, but subprocess `cwd` and temporary file behavior need verification.

**Mitigation:** Add a Cloud Run smoke step that specifically tests the MCP subprocess path in isolation before running the full demo pipeline. Ensure the MCP server uses `/tmp` for any transient state.

---

## Sequencing Assessment

The five deployment phases are correctly ordered:

1. **Phase 0 (repo hygiene)** — prerequisite for everything; prevents losing work
2. **Phase 1 (GCP setup)** — prerequisite for phases 2-5
3. **Phase 2 (container + deploy)** — must succeed before smoke test
4. **Phase 3 (live smoke)** — proves the deployment works
5. **Phase 4 (judge pass)** — proves the demo tells the story
6. **Phase 5 (submission)** — packages the proof

The only sequencing gap is the missing merge-to-main step (Finding 2). Otherwise, this is the right order.

The proof checklist (18 items) is comprehensive. Every item maps to a winning-bar claim from the strategy. The checklist is correctly positioned as a gate — nothing ships until all items are checked.

---

## Extension Proposals (ranked by winning-odds impact)

After the required proof checklist passes:

1. **Data-vs-data comparison UI** (highest leverage) — Replace the left panel prose with a simulated static survey result. This is the demo's "aha moment" and directly addresses the 20% Demo and Presentation rubric category.

2. **Second participant path** — Running two participants (not just one) proves the LoopAgent re-plan behavior and makes the coverage progression visible. This takes the demo from "it works once" to "it operates autonomously."

3. **Quantified business calculator** — A simple display: "Traditional: 4-8 weeks, $15K-$50K. Methodic: 15 minutes, schema-valid output, evidence-linked." Addresses the 30% Business Case rubric category.

4. **Cloud Logging trace in developer overlay** — Shows ADK handoffs, MCP calls, and BigQuery writes as a real observability view. Addresses the 30% Technical Implementation rubric category.

5. **Real `to_a2a()` endpoint** — Only if a smoke test passes quickly. Overstating A2A compliance is worse than honestly labeling it A2A-pattern.

---

## Business-Case and Demo-Story Gaps

1. **No dollar figure anywhere in the demo path.** The Phase 5 business-case section is a placeholder. Judges scanning for ROI will find rigor and methodology but no commercial anchor.

2. **The demo doesn't show the "before" clearly enough.** The static survey panel is a paragraph of text, not a visible data quality failure. The story is strongest when judges see the same question answered badly (static) and well (Methodic), side by side, with the quality delta quantified.

3. **The demo doesn't show the re-plan moment.** The winning strategy says "Coverage remains insufficient for one variable, so Methodic adds one targeted participant session." This is one of the three demo moments that make "clearly agentic" undeniable. The current UI shows coverage bars but doesn't highlight the re-plan decision or the before/after coverage state.

---

## Final Verdict

**APPROVE.** The deployment design is correctly motivated, well-sequenced, and appropriately conservative with the $500 credit budget. The proof checklist maps directly to winning-bar claims.

**Three required pre-deployment fixes (MAJORs):**
1. Add `/health` endpoint to `server.py`
2. Fix events polling deduplication in `demo.html`
3. Add conversation content to demo events in `demo_runner.py`

These are implementation fixes, not design changes. The architecture and sequencing are sound.

Strategy linkage: `mission_strategy['aichallenge'].deployment_proof` (Cloud Run + live Gemini + BigQuery), `demo_must_show` (data-quality delta, MCP call, agent handoffs), `vertical_slice` (B2B win-loss end-to-end).
