# Critique of Methodic Submission Spec — Skeptical Judge Read

**Reviewer:** Claude (acting as skeptical judge)
**Source:** `docs/spec.md`
**Stance:** Direct. No new product scope unless it clearly raises judging odds.

---

## Executive Verdict

If I read this submission cold against 200 others, here is what would happen:

- I would put it in the "AI survey, dressed up" pile within 60 seconds.
- The spec is well-written and methodologically sober — and that is part of the problem. It reads like a pitch deck and a research-ops white paper, not like an *agent system that does something I have not seen before*.
- The most defensible parts of the strategy (Tourangeau-Rasinski grounding, A2A interoperability, MCP-bound questioning) are *named* in the spec but **not load-bearing in the demo**. Judges score what they see, not what is asserted.
- The architecture is currently a sequential pipeline of LLM calls with JSON outputs. Calling each step an "agent" does not make it agentic. The judges will notice.

If only three things change, win odds rise materially:
1. **One unmistakably autonomous decision** the developer did not pre-script (e.g., the system decides to field one more participant because saturation is not reached, and you watch it happen on screen).
2. **Real A2A and real MCP, not mocks.** Mocking the two protocols whose adoption is the entire reason the Challenge exists is the single biggest scoring own-goal in the spec.
3. **Tourangeau-Rasinski and methodological grounding made visible** in the Methodology pushback, with citation. Right now the methodology beat is described as "deterministic critique rules" — that is a linter, not science.

The rest of this document expands.

---

## 1. What would make me dismiss this as "just an AI survey tool"?

Plenty.

- **The core claim is a survey claim.** "Conversational research agents that collect cleaner, richer, evidence-linked data than static forms." That is the Outset.ai / Strella / Yabble / Versive pitch, almost word-for-word, and those products have been shipping for two years. The Challenge is not "build a better survey." If a judge has seen even one of these products, the wedge collapses.
- **The demo's most vivid moment is a chat UI.** Split-screen static-survey-vs-conversational-agent is exactly the demo every AI survey vendor has been running since 2023. You will not be the first time a judge has seen that frame. They will pattern-match and tune out.
- **The "agent contracts" are JSON output schemas.** Organizer, Methodology, Sampling, Question Design, and Data Quality each take input, return JSON. This is a chain of LLM calls. Renaming pipeline stages as agents is a known anti-pattern; the rubric explicitly rewards autonomous, multi-agent behavior, not "we wrapped each prompt as an Agent class."
- **The "Sampling Plan Agent" is the most damning artifact.** Its output is four lines of static quotas and a caveat string. That is a templated prompt; calling it an agent is the kind of thing that causes a judge to mentally downgrade the entire submission.
- **Stop conditions are deterministic.** The spec admits this. Deterministic stop conditions are correct engineering, but they remove the most agent-like part of the loop. The Survey Agent is now a constrained chatbot whose follow-ups come from an approved list and whose stop comes from a rule.

What you would have to remove from the spec for it to *not* read as a survey tool: the split-screen baseline, the "vague-answer rate" framing, and the participant-conversation centerpiece. Which are also the parts most likely to get applause. So the answer is not to remove them — it is to add a beat that no survey tool has ever shown.

**The missing beat: an autonomous re-plan.** A survey tool cannot, mid-fielding, decide that the sample is wrong and recruit differently. Methodic should. (See §6.)

---

## 2. What parts are not convincingly agentic?

Honest scoring against an "agentic" definition that includes goal-pursuit, tool use that affects planning, and decisions the developer did not encode line-by-line:

| Component | Agentic? | Why |
|---|---|---|
| Organizer Agent | **No** | Single LLM prompt → JSON brief. No tool use, no replanning. |
| Methodology Agent | **Weakly** | Spec says "deterministic critique rules." That is a linter. |
| Sampling Plan Agent | **No** | Output is four hard-coded quotas and a caveat. Cut it. |
| Question Design Agent | **No** | Templated mapping of variables → questions. |
| Survey Agent | **Partially** | Real conversational reasoning, but bounded by approved follow-up categories and approved tool list. The agent never decides to look up something the developer did not anticipate. |
| Data Quality Agent | **No** | Spec already concedes this should be deterministic validation scripts. |
| External Agent Request | **No, in current form** | A JSON payload over an unspecified transport with one clarification round-trip. That is two API calls, not A2A. |

The single moment that could be agentic — MCP triangulation during the participant conversation — is **scripted per persona** (P-001 → unclear_roi, P-002 → procurement_friction, etc.). The agent is not deciding which tool to call based on what it heard; the persona script tells the demo what the agent will conclude. A judge who watches twice will notice the second run produces the same triangulation.

**To genuinely earn the "agentic" label, at least one of the following must be visibly true on screen:**

- The agent invokes a tool the developer did not pre-bind to that question.
- The agent revises the study plan after seeing live data.
- The agent escalates to a human or a different agent because of an emerging finding.
- The agent fires additional participant sessions because saturation is not reached.

The spec hints at the fourth (Beat 4: stop condition and coverage loop) but caps it at "stops probing a variable when threshold is reached." That is a stop, not a decision to *act differently*. Expand it: "saturation not reached → request one more economic buyer from the recruitment queue." Now there is a closed agentic loop with planning, fielding, measurement, and replanning — visible.

---

## 3. Technical claims that need proof in the demo

The spec hedges on every Google-stack item. Hedges read as "we may not ship this." Each hedge is a place a judge will dock points unless the demo shows the real thing.

- **A2A.** "Mocked A2A-style request." If the protocol is open, mock it as little as possible. A judge who knows A2A will check the wire format. Either show real A2A or label the panel honestly: "A2A-pattern demonstration; transport is HTTP for prototype." Pretending is worse than admitting.
- **MCP.** The spec lists three "MCP tools" but does not say whether they are exposed via a real MCP server or as in-process functions named `crm_context_lookup`. Judges scoring "MCP adoption" will look at the developer overlay. Stand up a real MCP server, even if it returns canned data, so the wire calls are visible.
- **ADK SequentialAgent / ParallelAgent / LoopAgent.** "Preferred ADK shape." If the team has not yet built a working ADK pipeline, this is risk. The most credible demos will show ADK primitives in code. If you fall back to a hand-rolled orchestrator, the rubric line for "use of Google agent stack" drops.
- **BigQuery.** "BigQuery, or a BigQuery-compatible export with documented table schema if live BigQuery setup becomes a blocker." Setting up BigQuery is one afternoon. Do not mock it. Mocking a Google-stack service in a Google-sponsored Challenge is a self-inflicted scoring loss.
- **Vertex AI Search / Agent Engine Sessions / Memory Bank.** "Strongly preferred if feasible," "if the deployed path supports it," "only if easy and stable." Three soft commitments and a preview-status escape hatch. Pick **one** (Vertex AI Search for methodology grounding), commit, and ship. Drop the other two from the spec entirely so they cannot be asked about.
- **Cloud Run.** Listed as guaranteed. Good. Do not lose this one to a deployment bug at the deadline.
- **Gemini model selection.** "Verify current recommended model names." Fine, but the demo should show *why* the higher-reasoning model is on Methodology and the lower-latency model on the Survey Agent. A latency overlay or a side-by-side cost annotation would prove the team thought about it.

**Items the spec asserts but does not prove:**

- That the methodology pushback is *derived* from the brief and sample plan rather than triggered by a keyword. The spec says the UI must "make clear why the rule fired" — make sure the rationale is generated, not templated.
- That the saturation curve reflects real measurement, not a pre-baked animation.
- That the structured-field confidence scores are produced by the agent, not assigned by the persona script.

A skeptical judge will hit pause and ask "where did the 0.84 confidence come from?" The demo should answer that question without a slide.

---

## 4. Business-case claims that are weak or unsupported

- **"$2.1M pipeline at risk."** Demo number. Fine for a demo. But if anything in the pitch deck rests on it, a judge will ask for the source.
- **Buyer ICP is four roles.** "Head of Research Operations, customer insights, revenue operations, or product research." That is GTM hedging. Pick one. Head of Research Ops at a 200-2000 person B2B SaaS is the cleanest fit and the one whose pain matches the demo.
- **No design partner, no pilot, no LOI.** For a B2B claim, this is the missing limb. Even one cited conversation with one named ResearchOps lead, with a direct quote, would change the credibility profile.
- **Engagement assumption.** The spec is admirably honest that participant engagement is a hypothesis. Judges will read this and ask: "so why will buyers actually answer your AI?" The mitigations listed (short sessions, clear value exchange, asynchronous completion, existing relationships) are reasonable but read as risk-shifting. **Suggested fix:** make the engagement hypothesis testable in the demo — e.g., one persona is shown declining to engage, and Methodic gracefully marks the session as `excluded` and adjusts the saturation budget. That converts a weakness into an agentic moment.
- **Competitive differentiation is asserted, not shown.** The strategy memo (per project memory) positions Methodic against Outset.ai / Strella / Yabble. The spec itself never mentions them. The demo should have one slide or one developer-overlay annotation that says "what these other tools do not do." Tourangeau-Rasinski grounding is your strongest moat; make it visible. None of the mentioned competitors cite a methodological framework.
- **Pricing, market sizing, and revenue model are absent.** A judge scoring "business case" wants at least: who pays, how much, why now, and what TAM. None of these are in the spec. Even one paragraph would help.
- **"B2B" is doing a lot of work.** B2B SaaS win-loss research is a real but small market (low hundreds of millions globally). If the pitch is "the upstream data-capture layer for the agentic enterprise," the win-loss demo undersells the claim. Either narrow the claim ("research ops for B2B revenue teams") or add one line in the close on how the same agent runs employee experience, product feedback, or post-incident review.

---

## 5. What should be cut to improve execution odds?

Cut these to free engineering time for the things that move scoring:

- **Sampling Plan Agent.** Fold its output into Methodology. Saves an LLM call, removes the most embarrassing "agent" in the lineup, and tightens the architecture diagram.
- **Memory Bank.** The spec already hedges. Drop it. One less preview-status dependency.
- **Agent Engine Sessions.** Same logic. Pick one Google service to feature; drop the rest from the diagram.
- **Two of the four buyer roles.** Pitch to Head of Research Ops only.
- **Two of the five personas.** Three personas (one lost economic buyer, one lost champion, one recent win contrast) carry the demo. Five is grind without payoff.
- **The "allowed_claims / disallowed_claims" Methodology output.** Interesting but hard to demo in 30 seconds. Keep it in the schema; do not feature it in the video.
- **The "static survey" baseline as an extended beat.** Keep it as a 10-second cold open contrast, not a 50-second split-screen. Every survey-tool demo has split-screen. Yours should look different by minute one.

What to **not** cut:

- Methodology pushback. This is your most defensible differentiator if it cites Tourangeau-Rasinski.
- MCP triangulation. Make it real MCP.
- Coverage / saturation visualization. Most original visual in the spec.
- Developer overlay. The thing that proves agent-ness to a technical judge.
- BigQuery export. Google-stack scoring.

---

## 6. What is missing from the demo that would increase score under the rubric

In rough order of expected scoring lift:

1. **An autonomous re-plan moment.** Saturation low for `procurement_friction` after the first three participants → Methodic decides to add one more lost-deal champion to the queue, narrates the decision, and re-runs. This single beat moves the submission from "AI survey" to "agentic research operations." It is the highest-leverage addition in this list.
2. **Real A2A wire.** Even a 30-line A2A server stub. Judges from Google will check.
3. **Real MCP server.** Same logic.
4. **Citation overlay on methodology pushback.** "Sample mismatch flagged per Tourangeau & Rasinski (2000), §4.2: economic buyers are required to answer pricing-decision research questions." Now the methodology agent stops looking like a linter and starts looking like grounded reasoning.
5. **Quantified before/after.** "In our 5-participant demo run: Methodic resolved 4/5 vague initial answers to specific structured causes; static survey resolved 0/5." One line. Numbers calibrate trust.
6. **Failure-mode beat.** The spec has guardrails listed but does not make failure-handling a featured moment. Show one participant becoming frustrated, Methodic ending gracefully, and the saturation budget rebalancing. Judges reward gracefully-handled failure more than perfectly-running demos.
7. **Architecture diagram with explicit agent boundaries and tool calls.** Not a generic "ADK + MCP" cartoon. A real graph: nodes = agents (named), edges = handoffs (typed), tool calls = arcs to external boxes. The developer overlay should mirror this graph live.
8. **Comparison slide.** Six rows by four columns: Methodic, Outset.ai, Strella, Yabble; rows = methodology grounding, A2A, MCP, BigQuery export, autonomous replanning, governance. Methodic is the only "yes" in at least three rows.
9. **Reproducibility note.** "Source available; demo runs locally with `make demo`." Open-source signaling lifts originality scores.

---

## 7. Questions I would ask the team during judging

Sharpest ones first:

1. Show me a single decision your agent made that you did not pre-script.
2. What does Methodic do that Outset.ai or Strella does not?
3. Is the A2A request real A2A, or HTTP with A2A-shaped JSON?
4. Walk me through one MCP call live. Show the wire format.
5. The methodology pushback — was the rationale generated or templated? Show me the prompt.
6. If I gave you a different decision (e.g., post-incident retrospective for an SRE team), how much code rework?
7. Why ADK and not LangGraph or a hand-rolled orchestrator? What does ADK uniquely give you?
8. What is your retention or response rate from real B2B economic buyers? Even one data point.
9. The structured-field confidence — how is it computed? If it is the model's self-reported confidence, why should I trust it?
10. What kills this product if it is wrong? What is the bet?

If the team can answer 8 of these crisply with the demo running, they win the technical-implementation rubric line. If they cannot answer (1) or (2), the submission is judged as a survey tool regardless of the rest.

---

## 8. The exact changes that most improve the chance of winning

Ranked, with effort estimate. Items at the top are the highest leverage per hour.

| # | Change | Effort | Why |
|---|---|---|---|
| 1 | Add an autonomous re-plan beat (saturation low → fire one more session) | 1-2 days | Converts the system from "AI survey" to "agentic research ops" in the judge's head. Single highest-impact change. |
| 2 | Stand up real A2A endpoint + real MCP server (even with canned data) | 1-2 days | Removes the two biggest hedges. Earns the Google-stack score. |
| 3 | Cite Tourangeau-Rasinski in the methodology pushback overlay | 2 hours | Cheapest credibility lift in the spec. Moves Methodology from "linter" to "grounded." |
| 4 | Cut Sampling Plan Agent; merge into Methodology | 2 hours | Removes the weakest "agent" from the diagram. |
| 5 | Replace BigQuery hedge with real BigQuery table + screenshot | 1 day | Removes the most embarrassing scope cut. |
| 6 | Add quantified before/after line ("Methodic 4/5 vs static 0/5") | 1 hour | Calibrates trust; gives every reviewer a soundbite. |
| 7 | Cut Memory Bank, Agent Engine Sessions from spec; commit to Vertex AI Search only | 1 hour | Removes three soft commitments judges may probe. |
| 8 | Pick one buyer (Head of Research Ops, B2B SaaS, 200-2000 employees) | 1 hour | Tightens GTM credibility. |
| 9 | Add competitor comparison row in close (Methodic vs Outset/Strella/Yabble) | 2 hours | Shows the team knows the space and has positioned. |
| 10 | Failure-mode beat (frustrated participant, graceful end, budget rebalance) | 1 day | Rewards visibly-handled failure. |
| 11 | Drop two personas; deepen the remaining three | 0 days (subtraction) | Frees fielding time. |
| 12 | Architecture diagram as named-node graph mirrored by developer overlay | 1 day | Visual proof of agent-ness. |

If the team has only **3 days** of build time left after critique: do (1), (2), and (3). Everything else is downstream of those three.

If the team has **5 days**: add (4), (5), (6), and (7).

If the team has **2 weeks**: do all twelve.

---

## Final Note: The Single Most Likely Way This Submission Loses

A judge watches a clean, well-narrated demo of an AI conducting a smart conversation with a participant about why their deal slipped. The agent asks good follow-ups. The data comes out cleaner than the static survey. The judge nods, scores it solidly, and moves on. The submission lands at the median.

It does not lose because the team built the wrong thing. It loses because **what the team built was already legible to the judge as a category they had seen**, and nothing in the demo forced a recategorization.

The fix is to add one moment that breaks the category. The autonomous re-plan beat does this. The Tourangeau-Rasinski citation does this. The real A2A handshake with a *named* second agent does this. Without at least one of those, this is a strong AI survey demo. With two of them, it is a credible agentic research-ops platform. With all three, it is genuinely competitive for a top-three placement.

— End of critique.
