# Strategy Memo: Winning the Google for Startups AI Agent Challenge — Track 1

**Author:** Claude (Opus 4.7, 1M-context)
**Date:** 1 May 2026 (35 days to submission deadline)
**Audience:** Founding team, Track 1 submission
**Status:** Companion to `docs/gemini-research.md`. This memo deliberately disagrees with parts of the Gemini draft where a sharper read earns more rubric points.

---

## TL;DR — three decisions that determine whether you win

1. **Reposition *above* the AI-interview category.** "AI moderates the interview" is now a saturated subcategory (Outset $17M, Strella, Listen Labs, Conveo, Glaut, Feedbk, User Intuition, plus the synthetic-respondent flank: Yabble inside YouGov, Fairgen, Simile with $100M from Index in Feb 2026). If judges file you under "another Outset competitor," you lose Innovation and Business Case. Frame as **the autonomous research-operations agent in the enterprise A2A graph** — callable by humans *and* by other agents.
2. **Make "clearly agentic" undeniable** with three specific demo beats that single-vendor SaaS competitors structurally cannot copy: **(a) MCP-mediated mid-interview triangulation**, **(b) A2A inbound from an external enterprise agent**, **(c) Looker BI Agent / BigQuery sink as the closed loop**. Each is a 15–30 second moment in the video.
3. **Build to the rubric, not to the idea.** Every artifact in the demo and every component in the architecture must map to one of the four rubric criteria. If it doesn't, cut it. The 30/30/20/20 split rewards Technical Implementation and Business Case equally — most teams will overinvest in the demo and underinvest in business-case quantification. Don't.

---

## 1. Winning positioning

### 1.1 The sharpest version of the idea

Not "an AI survey tool." Not "an AI interviewer." Frame and pitch as:

> **"The autonomous research-operations agent for the agentic enterprise. You give it a decision; it returns methodologically-grounded, governed, analysis-ready data — and any other agent in your stack can ask it for a study."**

This framing wins on three vectors:

- **Decision-anchored** (not survey-anchored). Every artifact starts from a decision the data must support, not a question list. This is what the existing `product-brief.md` already gestures at. Make it the load-bearing wall.
- **Operations** (not "research tool"). "ResearchOps" is a known enterprise category with budget owners. "Survey tool" lives in marketing-ops procurement; "Research Operations" lives in CIO / Chief Customer Officer / VP Research budgets — 5–10× higher contract values.
- **Agentic** (not chat). The system is *itself* a discoverable agent in an A2A graph. That is the technical claim that distinguishes you from Outset and from any LLM-augmented Qualtrics feature flag.

### 1.2 Naming

The Gemini memo proposed **"Methodic."** It's defensible — connotes rigor, distances from "chatbot." Two alternatives worth A/B-testing internally:

| Name | Why | Risk |
|---|---|---|
| **Methodic** (Gemini) | Methodology-forward, rigor signal | Sounds like a consultancy brand, not an agent |
| **Probe** | Verb-feeling, action-first; "probing follow-up" is the technical core | Trademark / connotation risk; "probe" can feel invasive |
| **Datum** | Singular of data; precision; clean, agent-feeling word | Generic-sounding |
| **Ground Truth** | Direct allusion to ML training-data quality + your "no insights without good data" thesis | "Ground truth" is overloaded in ML — could feel co-opted |

I recommend **"Probe"** for its action-orientation and demo legibility ("Probe found that 47% of lost deals trace to ROI ambiguity"). Lock positioning first; ratify the name after a 24-hour trademark check. Rest of memo uses "Probe."

### 1.3 The strongest business case

Forget "save time on surveys." Anchor on three numbers, all defensible from public data (Sources at end):

| Metric | Traditional research | Probe target | Source basis |
|---|---|---|---|
| Cost per study (n≈50 IDI + n=300 quant) | $25K–$65K | < $1.5K | Drive Research, Main Brain Research 2025 benchmarks |
| Time to clean data | 4–8 weeks | < 48 hours | Standard IDI cycle + analysis |
| Cost per IDI-equivalent conversation | $500–$1,500 | < $5 | Recruitment + moderator + transcription baseline |
| Completion rate | 10–30% (static) | 70–90% (conversational benchmark) | InMoment 2024 (n=3,000), Qualtrics, OpenResearch |
| Open-end depth | Baseline | 2.4× more actionable, 70% more words | InMoment 2024 |

The unbeatable claim is operational, not just cost-based: **"Probe lets you ask a question your dashboard cannot answer and have a defensible thematic answer before tomorrow's standup."** This is a *product manager's daily pain*, which judges (mostly PMs and engineers) will recognize immediately.

### 1.4 What to avoid sounding like

| Avoid | Why | Substitute with |
|---|---|---|
| "SurveyMonkey with AI" | Feature framing, not agent | "Research-operations agent" |
| "AI-moderated interview platform" | Outset/Strella/Listen Labs category | "Decision-anchored research agent" |
| "Conversational forms" | SurveySparrow / Specific consumer category | "Adaptive measurement instrument" |
| "Synthetic respondents" | Wrong category (Yabble/Fairgen/Simile bet) | "Validated, real-respondent data" |
| "ChatGPT for surveys" | Sounds like a wrapper | "Multi-agent system on Google ADK" |
| "BI dashboard with chat" | Post-Looker BI Agent (Next '26), this is everywhere | "Upstream of BI: the data-capture layer" |

---

## 2. Differentiation

### 2.1 The competitive map (May 2026)

**Tier 1 — direct competitors (AI-moderated qualitative + quantitative)**

| Vendor | Funding/scale | Strength | Visible weakness Probe must exploit |
|---|---|---|---|
| **Outset.ai** | $17M Series A | Enterprise sales, video-prompt format, end-to-end workflow | No automatic theme generation — manual review; weak methodology rigor on the front-end; no agent-to-agent interop story |
| **Strella.ai** | Earlier-stage | Hybrid human+AI moderation, real-time highlights | Single-product feel, no multi-agent system, no enterprise governance story |
| **Listen Labs** | Earlier-stage | Voice surveys at scale, 10–30 min sessions | Voice-only, narrower scope, "survey" not "research" |
| **Conveo / Glaut / Feedbk / User Intuition** | Earlier-stage | $20-per-interview pricing (User Intuition) | Commodity AI moderation; no enterprise governance |

**Tier 2 — adjacent / disintermediation risk (synthetic respondents)**

| Vendor | Funding | Position relative to Probe |
|---|---|---|
| **Simile** | $100M, Index Ventures, Feb 2026 | Replaces real respondents; bigger AUM bet |
| **Fairgen** | Earlier; validated against 7,000+ Pew tests | Augments small samples with synthetic data |
| **Yabble** (YouGov) | £4.5M acquisition, Aug 2024 | Synthetic audiences inside YouGov |

Probe is **not** competing here. The synthetic flank is a strategic risk to acknowledge, not engage. Frame as complementary: Probe captures *real* validated data; synthetic respondents extrapolate. (Long-term, the integration is interesting — your data trains better synthetics — but ignore it for the challenge.)

**Tier 3 — analytical / coding tools (post-collection)**

Dovetail, Cauliflower, Marvin, Sprig (in-product) — these analyze data after collection. Probe is upstream of them. Position as a complement, not a replacement.

**Tier 4 — incumbents that could ship a feature**

Qualtrics XM (Edge AI), Microsoft Forms Pro, Google Forms + Gemini, Typeform AI / VideoAsk, SurveyMonkey AI. These will all ship "AI conversational survey" features in 2026. Probe wins by being multi-agent, A2A-native, and methodology-grounded — none of which fits a feature-add inside an incumbent suite.

### 2.2 What makes judges say "this is *clearly agentic*, not a form generator"

Three demo moments. None requires more than 30 seconds of footage. Each is structurally impossible for a single-vendor SaaS competitor to imitate within their architecture.

1. **The Methodology Agent says "no" to the human Organizer.** The Organizer asks for a 5-question survey to lost-deal contacts. The Methodology Agent interrupts: *"Your sampling oversamples champions; without the economic buyer you cannot inform a pricing decision. Recommend 60/40 split with stratified quotas — here is the rationale."* This is **declarative-intent agentic behavior** — agent pursues the *goal* (inform a decision), not the *task* (run a survey).
2. **MCP-mediated triangulation mid-interview.** Participant says *"your product is too slow."* The Survey Agent fires an MCP call to a product-telemetry server, gets `p95 = 1.8s on the trial cohort`, and adapts: *"I can see your last three sessions averaged 1.8 seconds — was it a specific page like the report builder, or felt slow throughout?"* This is **autonomous tool use bound to measurement intent** — exactly what the Track 1 brief calls out.
3. **A2A inbound from an external agent.** A simulated Sales Insights agent issues an A2A request: `requestStudy({decision: "should we adjust mid-market packaging?", deadline: "48h"})` against Probe's signed Agent Card. Probe accepts as an A2A Task, runs the study, and returns structured findings as a Task completion. Other agents in the buyer's stack consume Probe like an API. **No competitor in Tier 1 has shipped this.**

### 2.3 The defensibility argument

A competitor can copy any of these moves in isolation. They cannot copy them as a system without restructuring around ADK + A2A + MCP, which is a 6–18 month re-platform. By the time the deadline arrives, you will have shipped what they cannot ship in a quarter.

---

## 3. Research and methodology — credible without over-claiming

This section is where most challenge entries lose points. Either they say nothing about methodology (Innovation suffers), or they over-claim (Technical credibility suffers when judges ask follow-ups). The line is clear:

### 3.1 Cite, don't synthesize

Use 4–5 academically established frameworks as the methodological backbone. Each gives the Methodology Agent and QA Agent something concrete to do.

| Framework | What Probe does with it | Source |
|---|---|---|
| **Tourangeau–Rasinski–Rips 4-stage cognitive model** (comprehension → retrieval → judgment → response) | Question Design Agent maps every prompt to the cognitive stage it stresses; flags items that overload retrieval | *The Psychology of Survey Response*, Cambridge UP, 2000 |
| **Krosnick's satisficing theory** (1991) | QA Agent detects shallow / patterned responses (e.g., flat-line ratings, ultra-short open-ends) and triggers an adaptive probe | Krosnick, *Applied Cognitive Psychology* 1991 |
| **Glaser–Strauss theoretical saturation** (1967) | Survey Agent Pool stops fielding when N consecutive sessions yield no new themes; report a saturation curve | *The Discovery of Grounded Theory*, 1967 |
| **Cognitive interviewing** (Beatty & Willis) | Question Design Agent runs a synthetic cognitive-interview pass before fielding, simulating comprehension failures | Willis, *Cognitive Interviewing*, 2005 |
| **Krippendorff's α for thematic coding** | Two independent coding passes (Gemini + heuristic), reported with α (preferred over Cohen's κ for >2 coders / multi-level data) | Krippendorff, *Content Analysis*, 4th ed. |

### 3.2 Bias and validity controls (these are what the Methodology Agent *does*)

- **Leading-question detection** (lexical + LLM grading; flags "How great did you find…")
- **Double-barreled detection** ("How satisfied are you with the speed *and* reliability?")
- **Framing / order-effect rotation** (counter-balance ordered scales across participants)
- **Social-desirability mitigation** (indirect questioning patterns where appropriate)
- **Acquiescence-bias guardrails** (avoid all-positive phrasing in agree/disagree blocks)
- **Sample-validity flags** (when self-recruitment biases the sample, surface it visibly in the brief — don't quietly pretend it's representative)

### 3.3 What to *not* claim

| Don't claim | Why |
|---|---|
| "Statistically representative findings" | Your samples will not be probability samples. Don't pretend. |
| "Causal" insights | Unless you ran a true experiment. |
| "Better than human moderators" overall | Demo a *specific* dimension where Probe outperforms (probing depth, response speed, scale). |
| "Eliminates bias" | Bias mitigation, not elimination. |
| "Replaces qualitative researchers" | Augments. Saying "replaces" loses HR/Research-buyer trust instantly. |

### 3.4 Demo-visible quality metrics

Show all of these on screen during the QA-Agent moment:

- **Variable Coverage Rate** — % of decision-critical variables captured per session
- **Ambiguity Reduction Rate** — share of vague answers clarified by adaptive probes
- **Saturation Curve** — new themes per N sessions, flatlining at stop point
- **Krippendorff's α** for thematic coding (target ≥ 0.70)
- **Triangulation Rate** — % of self-reported claims cross-checked against MCP-fetched ground truth
- **Per-variable Confidence Score** — output by the QA Agent, attached to each captured field

Showing α > 0.70 is the single fastest credibility signal you can put on screen. Most competitors don't do it.

---

## 4. Agent architecture — concrete and Google-stack-justified

### 4.1 Topology

```
                    Organizer (human, web UI)
                              │
                              ▼
                     ╔════════════════╗
                     ║  Organizer     ║   (ADK SequentialAgent root)
                     ║  Agent         ║
                     ╚════════╤═══════╝
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
     Methodology       Question Design     Sampling Plan
        Agent              Agent              Agent
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ▼
                     Visualization Agent
                  (visual review package)
                              │
                       ── Approval ──
                              │
                              ▼
                     ╔════════════════╗
                     ║  ADK Parallel  ║    (ADK ParallelAgent over the pool)
                     ║  Survey Pool   ║
                     ╚════════╤═══════╝
                              │
                              ▼
                       Data Quality Agent      ← uses LoopAgent for saturation-stop
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
            BigQuery     Looker BI     A2A Outbound
              sink       Agent UI      (Task object)
                                            │
                                            ▼
                                     External agent caller
                                  (e.g., Sales Insights agent)
```

### 4.2 Agent roster, with tool boundaries

Five named agents minimum, six maximum. More is not better — judges pattern-match on coherence, not headcount.

| Agent | Tools (MCP / native) | State | Memory |
|---|---|---|---|
| **Organizer Agent** | `brief_writer`, `handoff_router`; reads Memory Bank for organizer profile | Session: research brief draft | Memory Bank: organizer profile (voice, prior studies) |
| **Methodology Agent** | `bias_detector`, `methodology_lookup` (Vertex AI Search grounded over a curated corpus of Tourangeau, Krosnick, AAPOR, ESOMAR docs) | Session: methodology critiques | None |
| **Question Design Agent** | `cognitive_stage_mapper`, `wording_optimizer`, `schema_validator` | Session: question pool, schema | None |
| **Sampling Plan Agent** | `sample_size_calculator`, `quota_designer` | Session: sample plan | None |
| **Visualization Agent** | `package_renderer` (writes to a React review-page state) | Session: review-package state | None |
| **Survey Agent (pool)** | `probing_engine`, **MCP: CRM (Salesforce)**, **MCP: telemetry (Mixpanel/PostHog)**, `consent_check` | Session per participant: transcript, structured fields, confidence map | None per-participant; aggregate stats roll up |
| **Data Quality Agent** | `thematic_coder`, `saturation_detector`, `bigquery_writer`, `a2a_responder` | Session: corpus state, α scores | None |

### 4.3 Specific Google-stack choices, with reasoning

- **Orchestration: ADK.** Use `SequentialAgent` for the planning chain (Organizer → Methodology → Question Design → Sampling → Visualization). Use `ParallelAgent` for the survey pool. Use `LoopAgent` for the saturation-stop pattern in the QA Agent. *Do not* invent bespoke orchestration — judges will recognize standard ADK patterns and reward them.
- **Intelligence: Gemini 2.5 Pro / Flash mix.** Use Pro for the Methodology and QA agents (long-context, methodology grounding); use Flash for the Survey Agent pool (latency-sensitive, conversational). Justify the split in the architecture document — judges love seeing cost-aware model selection.
- **Sessions: Agent Engine Sessions (GA).** Keep per-participant state managed. Avoids reinventing.
- **Memory: Agent Engine Memory Bank (GA).** Cross-session organizer memory ("this PM dislikes 5-point Likerts"). Demonstrate it: have the second study auto-skip a question style the organizer rejected before. **This single beat is high-signal for Innovation.**
- **Grounding: Vertex AI Search** over a small curated corpus of methodology PDFs (AAPOR best practices, ESOMAR, Tourangeau excerpts). Methodology Agent's claims become source-linked. Judges scoring Technical Implementation reward visible grounding.
- **MCP wiring:**
  - `mcp-salesforce` (community server) — CRM context (segments, deal history)
  - `mcp-mixpanel` or `mcp-posthog` (custom or community) — product-telemetry triangulation
  - `mcp-slack` (community) — optional notify-on-completion path
  - In the demo, name them out loud and show the tool-call signature in a developer console overlay.
- **A2A v1.0:** Publish a **Signed Agent Card** for Probe. Demonstrate inbound A2A from a mocked Sales Insights agent calling `requestStudy()`. Use JSON-RPC over HTTPS per the spec. v1.0 is now Linux-Foundation owned with 150+ orgs — name-drop this in the technical narrative.
- **Deployment: Cloud Run.** Not GKE. GKE adds 1–2 weeks of infra overhead and earns zero rubric points beyond what Cloud Run earns. The Track 1 brief explicitly says "Cloud Run *or* GKE." Pick the lighter one.
- **Sink: BigQuery.** Show the structured output landing in a BigQuery table with a clear schema. This is the "real product" signal.
- **Optional but high-leverage: Looker BI Agent integration.** Wire the BigQuery output to a Looker dashboard whose **Dashboard Agent** (announced at Next '26) can answer follow-ups against the new dataset. This closes the loop visibly: business question → research → governed data → BI agent answers downstream questions. **This is a 10-second demo beat that lands huge.**

### 4.4 What *not* to build

- **No voice in v1.** Voice is a tax on the demo and adds latency / cost. Cut.
- **No live participant recruitment.** Use simulated participant personas (3–5) with realistic prompts. Judges expect this for a 6-week prototype.
- **No mobile app.** Web only.
- **No own dashboard.** Use Looker. Don't compete with Looker; integrate with it.
- **No analytics layer.** Output is the dataset, not the analysis. Frame this as a deliberate scoping choice on the Innovation slide ("we own the data-capture layer; downstream BI is your existing stack").

---

## 5. Demo strategy — 4-minute B2B win-loss scenario

### 5.1 Why this scenario beats "trial-conversion"

The current `build-plan.md` favors a SaaS trial-conversion demo. It's safe but generic. **Switch to mid-market enterprise win-loss analysis.** Reasons:

- **Higher $-stakes per study** ($2M+ in slipping ARR per quarter is plausible) → stronger Business Case.
- **Naturally A2A-shaped:** a Sales-Insights agent detecting a deal-loss anomaly is a believable trigger.
- **Allows triangulation moment:** lost-deal contact says "ROI was unclear"; Probe pulls trial telemetry and finds the user never reached the report builder. This is a memorable, story-shaped beat.
- **Stronger judge resonance:** every B2B SaaS judge has lived through a board meeting asking "why are we losing mid-market?". The pain is universal among the audience.
- **B2B focus** aligns with Track 3 mandates and signals enterprise-readiness even on Track 1.

### 5.2 The 4-minute demo flow

| t | Beat | Rubric criterion served |
|---|---|---|
| 0:00–0:15 | Problem stat. *"Mid-market deal slippage costs the average B2B SaaS $X/quarter. Win-loss analysis takes 4 weeks. Probe takes 48 hours, governed."* Cut to Probe interface. | Business Case |
| 0:15–0:45 | **A2A inbound.** Mocked "Sales Insights" agent fires an A2A `requestStudy()` against Probe's Signed Agent Card. Show the JSON-RPC payload briefly on screen. Probe accepts the Task. | Technical Implementation, Innovation |
| 0:45–1:30 | **Planning.** Organizer Agent confirms decision intent. Methodology Agent **pushes back** on sampling: *"60/40 champions vs economic buyers."* Question Design Agent maps each item to a Tourangeau cognitive stage. Sampling Plan Agent computes quotas. Visualization Agent renders the review package. *Approve.* | Innovation, Technical Implementation |
| 1:30–2:30 | **Split-screen interview.** Left: static survey. Lost-deal contact types "Price." Submit. End. Right: Probe Survey Agent. *"When you say price, what shifted — competitor offer, internal budget, or unclear ROI?"* Champion: *"ROI was murky."* Probe fires **MCP triangulation** to product telemetry → discovers user logged in 3 times in trial. Probe: *"I see your team logged in three times — was the 'aha' moment unclear, or never reached?"* Champion: *"Never reached the report builder."* | Demo, Innovation |
| 2:30–3:15 | **Saturation + QA.** Saturation curve flatlines at 47 sessions (3 themes saturated). Krippendorff's α = 0.74. Per-variable confidence scores. Click any theme → see verbatim quote → see participant ID + telemetry context. | Technical Implementation, Demo |
| 3:15–3:45 | **A2A outbound + closed loop.** Probe returns A2A Task completion to the Sales Insights agent. Looker dashboard updates via BigQuery. Dashboard Agent (Next '26) answers a follow-up: *"What's the dollar value of slippage attributable to ROI ambiguity?"* Answer: *"$2.1M of slipping ARR."* | Business Case, Demo |
| 3:45–4:00 | One-liner close. *"Probe is the research-operations agent in the agentic enterprise. Decision in, governed data out, callable by every other agent in your stack."* | Innovation |

### 5.3 Visual artifacts judges will remember

- **The agent council overlay.** A developer-mode toggle that shows the agents talking to each other in real time. ADK-pattern legibility = Technical Implementation points.
- **The methodology pushback moment.** Slow down for this. It's your "clearly agentic" beat. Keep the agent's explanation visible on screen for 6+ seconds.
- **The MCP triangulation panel.** A clear three-pane view: participant utterance, MCP call signature, telemetry result, then the adapted probe. This is the moment that beats Outset.
- **The saturation curve.** A live chart that flatlines and triggers stop. Judges have not seen this in any competitor demo.
- **The A2A signed Agent Card.** Show the JSON briefly. Name-drop "v1.0, Linux Foundation, signed."
- **The Looker dashboard.** End on this. It signals "this isn't a toy" better than any architecture diagram.

### 5.4 What to cut from the demo

- Don't show the architecture diagram in the video — link to it in the README. Architecture diagrams kill demo pacing.
- Don't show > 1 organizer-side flow. One study. End-to-end.
- Don't include voice. Don't include a "consumer" use case. Keep B2B throughout.

---

## 6. Judging rubric strategy — beat-by-beat mapping

The rubric is 30/30/20/20. Every demo beat above is tagged. Below is the inverse view: for each criterion, the specific evidence Probe presents.

### 6.1 Technical Implementation (30%)

**What this criterion rewards:** real multi-agent system, real ADK patterns, real MCP wiring, real Google Cloud deployment, observable, debuggable, production-shaped.

**Probe's evidence:**

- ADK SequentialAgent + ParallelAgent + LoopAgent named patterns (visible in the code/architecture)
- 5–6 specialized agents with clear tool boundaries
- 3 MCP servers wired (Salesforce, Mixpanel/PostHog, Slack)
- A2A v1.0 Signed Agent Card published, inbound `requestStudy` demonstrated
- Agent Engine Sessions + Memory Bank in use (GA features)
- Vertex AI Search grounding for the Methodology Agent
- Cloud Run deployment with `gcloud run deploy` reproducible
- BigQuery sink with explicit schema
- Optional: Looker BI Agent integration
- Observable: a developer-overlay view showing agent-to-agent traffic

### 6.2 Business Case (30%)

**What this criterion rewards:** quantified value, defensible numbers, identified buyer, clear willingness-to-pay, real GTM logic.

**Probe's evidence:**

- Cost-per-study comparison table ($25K–$65K → < $1.5K) with public-source citations
- Time-to-insight (4–8 weeks → 48 hours)
- Buyer profile: VP Research / Head of ResearchOps / CCO at $50M–$1B B2B SaaS — named ICP, with deal-size estimate ($60K–$150K ARR for the studio + per-study consumption)
- A2A interop pitched as land-and-expand: once Probe is wired in, *every other agent in the stack* becomes a downstream customer — this is the durable expansion story
- EU AI Act tailwind: high-risk AI obligations enforce in August 2026; Probe's instrument-as-code + DPIA/FRIA-friendly governance is explicitly positioned for it
- Comparison with Outset's public "8×/81%/10×" claims, with Probe matching or exceeding on the dimensions that matter

### 6.3 Innovation and Creativity (20%)

**What this criterion rewards:** non-obvious idea, novel agentic behavior, fresh use of the Google stack.

**Probe's evidence:**

- Reframing of "AI survey" → "research-operations agent in the A2A graph"
- Methodology Agent that *pushes back* on the human (rare in shipped products)
- Mid-interview MCP triangulation (not seen in Tier 1 competitors)
- Inbound A2A from external agents (not seen anywhere in this category)
- Saturation-stop via LoopAgent (rare even in research methodology software)
- Memory Bank that personalizes the *organizer*, not the participant (inverted, fresh)

### 6.4 Demo and Presentation (20%)

**What this criterion rewards:** clarity, pacing, visual polish, narrative.

**Probe's evidence:**

- 4-minute structured flow above
- Single B2B scenario, no scope sprawl
- Three memorable visual beats (methodology pushback, MCP triangulation, saturation curve)
- Closes on Looker dashboard (production signal)
- Plain-language voice-over; no tech-stack jargon in the spoken track (jargon is in screen overlays only)

---

## 7. Risks and pitfalls — what could make this lose

### 7.1 Existential category risks (acknowledge, don't hide)

- **AI-moderated interviews is a crowded category in mid-2026.** Mitigation: lead with the A2A / multi-agent / methodology-rigor framing in the first 30 seconds of the video. Do not let judges file you as "another Outset."
- **Synthetic-respondent vendors could disintermediate this.** Mitigation: position as complementary; long-term, Probe's data trains better synthetics. Out of scope for the challenge.
- **Outset's "8×/81%/10×" public claims are already in the market.** Mitigation: don't compete on those exact axes. Differentiate on agent-graph integration, methodology rigor, and governance — not on speed-and-cost alone.
- **Judges may dismiss as "just a survey tool."** Mitigation: the A2A inbound moment in the first minute of the demo defuses this.

### 7.2 Technical / scope pitfalls

- **Going wide.** One vertical (B2B SaaS), one buyer (Head of ResearchOps), one scenario (win-loss). Resist the urge to add HR or operations or healthcare. Vertical-specific MCP wiring is what makes the demo feel real.
- **Choosing GKE for "production credibility."** Costs 1–2 weeks of infra; rubric-neutral relative to Cloud Run.
- **Inflating agent count.** 5–6 agents with crisp roles > 12 agents with overlapping responsibilities. Judges score coherence, not headcount.
- **Unbounded LoopAgent costs.** Set hard maxima on saturation-stop loops (max 100 sessions per study).
- **Hallucinated probes.** Schema-grounded, instrument-bound prompting is mandatory. The Survey Agent must be unable to introduce a question that wasn't approved.
- **Voice.** Cut.
- **Real participant recruitment.** Cut. Use 3–5 simulated personas with rich back-stories.
- **A frontend that screams "marketing landing page."** AGENTS.md already calls this out. Build the working flow first; brand-pretty later.

### 7.3 Business-case pitfalls

- **Over-claiming statistical rigor.** Say "decision-grade qualitative + light quantitative" — not "statistically representative." Anyone with survey-stats training will catch over-claims and dock Innovation credibility.
- **Vague ROI.** Anchor every number to a public source. The benchmarks table in §1.3 has them.
- **Skipping the buyer.** Name the buyer (Head of ResearchOps at a $50M–$1B B2B SaaS). Without a named buyer, Business Case is automatically weaker.

### 7.4 What must be true for this to feel production-grade

A checklist the team should not ship without:

- [ ] One end-to-end study runs in < 10 minutes from organizer brief to BigQuery row.
- [ ] At least one MCP server actually returns real data (mocked is OK if the tool boundary is real).
- [ ] A2A inbound `requestStudy()` works against a Signed Agent Card.
- [ ] Methodology Agent has at least 3 substantive pushback patterns (sampling, leading questions, cognitive overload).
- [ ] Saturation curve renders live during the survey-pool run.
- [ ] Krippendorff's α computed and shown.
- [ ] Looker dashboard or BigQuery query shown at the end.
- [ ] Cloud Run deployment is one `gcloud run deploy` command (judges will check the README).
- [ ] Agent council / developer overlay view exists and works.
- [ ] Demo video is < 4 minutes, scripted, recorded with stable audio.

---

## 8. Final recommendations — top 10, ordered by leverage

1. **Lock the framing today: "research-operations agent in the A2A graph."** This is the single decision that shapes every subsequent choice. Do not move past this without team alignment.
2. **Build the A2A inbound `requestStudy()` flow first.** It's the most defensible "clearly agentic" beat, the hardest to fake retroactively, and the rarest in the competitive set. If only one feature works on demo day, this is the one.
3. **Build MCP triangulation second.** This is the visual moment that beats Outset. Even with one MCP server (mocked telemetry is acceptable) and one triangulation moment, you have a memorable beat.
4. **Build the Methodology-Agent pushback behavior third.** Hard-code a small set of methodology critiques (sampling, leading questions, cognitive load, double-barreled) and trigger them on patterns the Question Design Agent emits. Don't try to make this fully open-domain.
5. **Switch the demo scenario to B2B win-loss.** Higher $-stakes, naturally A2A-shaped, MCP-friendly, judge-resonant. Update `build-plan.md` accordingly.
6. **Pick Cloud Run, ship a one-command deploy.** Skip GKE. Document `gcloud run deploy` in the README. Judges check this.
7. **Wire BigQuery + Looker in the closing 30 seconds.** This is your "production-grade" signal. The Looker BI Agent integration is a 1-day build relative to its rubric impact.
8. **Use Agent Engine Sessions + Memory Bank — and demo the cross-session memory beat.** Have the organizer run a second study and watch Probe auto-skip a question style they previously rejected. 10-second beat, big Innovation credit.
9. **Show Krippendorff's α and a saturation curve on screen.** Two statistics that signal real methodology depth. Most competitors show neither.
10. **Pre-record everything; don't live-demo.** Live demos fail. Record a polished 4-minute video and ship the deploy as a separate artifact for the judges to inspect at their leisure.

### What I would *cut* from the existing plan

- Voice / multi-modal in v1.
- Any "platform" framing — keep it scoped to one buyer and one workflow.
- An in-house dashboard. Use Looker.
- Real participant recruitment for demo. Use simulated personas.
- The trial-conversion demo scenario — replace with B2B win-loss.

### What I would *add*

- A2A Signed Agent Card and inbound `requestStudy()` flow.
- One MCP triangulation moment with a real (or realistically mocked) tool call.
- Looker BI Agent / BigQuery closed-loop demonstration in the final 30 seconds.
- Methodology-grounding corpus (AAPOR + ESOMAR + Tourangeau excerpts) indexed in Vertex AI Search.
- A developer-overlay view of agent-to-agent traffic.

### Net Promoter — would I bet on this submission?

Yes, conditionally. The product thesis is strong; the competitive gap is real (front-end methodology rigor + A2A interop is unclaimed); the Google stack alignment is excellent. The risk is execution, not idea. With the framing locked above and the top-3 build priorities executed cleanly, this submission has a credible path to **Best of Theme** and an outside path to **Grand Prize**. The most likely failure mode is *not* losing to a better idea — it's spending the first two weeks debating positioning and losing to a worse idea executed in 6 weeks instead of 4.

**Stop debating. Ship.**

---

## Appendix A — Source basis (May 2026)

Public sources used to ground claims:

- **Challenge & Google stack:**
  - [Google for Startups AI Agents Challenge](https://cloud.google.com/blog/topics/startups/startups-are-building-the-agentic-future-with-google-cloud)
  - [ADK documentation](https://google.github.io/adk-docs/)
  - [Agent Engine Sessions / Memory Bank GA](https://cloud.google.com/agent-builder/agent-engine/sessions/manage-sessions-adk)
  - [Agent Garden](https://developers.googleblog.com/agent-garden-samples-for-learning-discovering-and-building/)
  - [Looker BI Agents at Next '26](https://cloud.google.com/blog/products/business-intelligence/looker-updates-for-agentic-bi-at-next26)
  - [BigQuery Agent Analytics](https://cloud.google.com/blog/products/data-analytics/introducing-bigquery-agent-analytics)
  - [Vertex AI Search grounding for ADK](https://google.github.io/adk-docs/grounding/vertex_ai_search_grounding/)
- **A2A v1.0:**
  - [A2A Protocol spec](https://a2a-protocol.org/latest/specification/)
  - [a2aproject/A2A on GitHub](https://github.com/a2aproject/A2A)
  - [Google Developer Blog announcement](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- **MCP ecosystem:**
  - [2026 MCP roadmap](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/)
  - [MCP overview, The New Stack](https://thenewstack.io/model-context-protocol-roadmap-2026/)
- **Competitive (AI-moderated interview):**
  - [Outset.ai pricing & platform](https://outset.ai/), [VentureBeat $17M raise](https://venturebeat.com/ai/outset-raises-17m-to-replace-human-interviewers-with-ai-agents-for-enterprise-research)
  - [Strella vs Outset](https://www.strella.io/compare/strella-vs-outset)
  - [Top 5 AI interview tools 2026 (Feedbk)](https://feedbk.ai/en/blog/top-ai-interview-survey-tools-2026/)
  - [Best AI moderated platforms 2026 (UserIntuition)](https://www.userintuition.ai/posts/best-ai-interview-platforms-2026-comparison/)
- **Synthetic respondents:**
  - [Fairgen platform](https://www.fairgen.ai/)
  - [Fairgen TechCrunch coverage](https://techcrunch.com/2024/05/09/fairgen-boosts-survey-results-using-synthetic-data-and-ai-generated-responses/)
  - [Synthetic research market map (Ditto)](https://askditto.io/news/synthetic-research-platforms-the-2026-market-map)
- **Survey methodology:**
  - [Tourangeau, Rips, Rasinski, *The Psychology of Survey Response* (Cambridge UP)](https://www.cambridge.org/core/books/psychology-of-survey-response/46DE3D6F7C1399BCDC78D9441C630372)
  - [Krosnick 1991 satisficing paper](https://web.stanford.edu/dept/communication/faculty/krosnick/docs/1991/1991%20Satisficing.pdf)
  - [Saturation review (Cogent)](https://www.tandfonline.com/doi/full/10.1080/23311886.2020.1838706)
  - [Intercoder reliability (O'Connor & Joffe, 2020)](https://journals.sagepub.com/doi/10.1177/1609406919899220)
- **Cost / completion benchmarks:**
  - [Drive Research market-research cost](https://www.driveresearch.com/market-research-company-blog/how-much-does-market-research-cost/)
  - [Main Brain Research 2025](https://mainbrainresearch.com/how-much-does-market-research-cost-2025/)
  - [Conversational survey completion benchmarks (SurveySparrow)](https://surveysparrow.com/blog/why-survey-bots-outperform-static-forms/)
  - [InMoment 2024 conversational quality study referenced via Feedbk](https://feedbk.ai/en/blog/conversational-survey-chat-survey/)
- **Regulatory:**
  - [EU AI Act timeline](https://artificialintelligenceact.eu/)
  - [AI Act / GDPR overlap (IAPP)](https://iapp.org/resources/article/mapping-interplays-gdpr-eu-ai-act)

---

*End of memo.*
