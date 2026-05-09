# Methodic — VC Pitch Document

## One-Liner

Methodic is the autonomous research-ops agent that replaces static B2B surveys with governed, evidence-linked data capture — turning business questions into decision-ready datasets.

## The Problem

**$4.5B+ spent annually on B2B research, but the data-capture layer is broken.**

Enterprise teams invest heavily in analytics, BI dashboards, and AI decision systems — then feed them shallow survey data. The result:

- **"Price"** appears in 73% of lost-deal reports, but dashboards can't distinguish packaging friction from ROI justification failure
- **40-60% of survey responses** are too vague to act on (Krosnick satisficing theory)
- **Manual win-loss interviews** cost $500-2,000 per session and take 6-12 weeks to analyze
- **Static surveys** have fixed branching — they can't probe, can't adapt, can't triangulate against CRM data

The upstream data problem means downstream analytics produces the wrong answers at scale.

## The Solution

Methodic is a multi-agent system built on Google's Agent Development Kit that conducts autonomous, methodology-governed research interviews:

1. **Plans the study** — organizer + methodology agents structure objectives and push back on sampling bias
2. **Conducts adaptive interviews** — probes vague answers into specific decision variables in real time
3. **Triangulates against business context** — MCP tools pull CRM/telemetry data mid-interview for sharper follow-ups
4. **Tracks coverage autonomously** — identifies gaps across 8 canonical research variables, re-plans when needed
5. **Exports structured data** — evidence-linked rows with confidence scores directly to BigQuery

**Not a chatbot survey.** An autonomous research operations agent that applies qualitative research methodology at scale.

## Market

### Target Segments

| Segment | Pain Point | Willingness to Pay |
|---------|-----------|-------------------|
| B2B SaaS (Series B+) | Win-loss analysis for board/investors | $2-5K/mo |
| Management Consulting | Client research at scale | $5-15K/mo |
| Market Research Firms | Analyst productivity 10x | $10-50K/mo |
| Product Teams | Churn/NPS deep-dives | $1-3K/mo |

### TAM/SAM/SOM

- **TAM**: $12B — global market research industry (qualitative segment)
- **SAM**: $2.4B — B2B enterprise research (win-loss, churn, competitive intel)
- **SOM**: $48M — initial wedge: mid-market SaaS win-loss analysis (Year 3)

## Competitive Landscape

| Player | Approach | Weakness |
|--------|----------|----------|
| **Clozd / DoubleCheck** | Human-conducted win-loss interviews | $500-2K per interview, 6-12 week turnaround, doesn't scale |
| **Outset.ai** | AI-moderated interviews | No methodology governance, no variable-level coverage tracking, no MCP integration |
| **Strella / Yabble** | AI survey analysis | Analyzes existing survey data, doesn't improve capture quality |
| **SurveyMonkey / Typeform** | Static forms with branching | Fixed paths, no probing, no ambiguity resolution, no evidence linking |
| **Custom LLM chatbots** | One-shot prompts | No multi-agent coordination, no coverage tracking, no re-plan, no audit trail |

### Methodic's Moat

1. **Methodology governance** — methodology agent enforces sampling, variable coverage, and research ethics constraints that competitors skip
2. **Multi-agent coordination** — 7 LLM agents + 6 custom steps, not a single-prompt chatbot
3. **MCP-native data access** — secure, field-filtered access to CRM/telemetry for contextual probing
4. **Measurable quality delta** — +0.692 composite improvement over static surveys on same rubric
5. **Enterprise-grade audit trail** — every data point traces to a conversation turn with confidence scores

## Traction (Prototype Stage)

- **Live on Cloud Run** with Vertex AI — [https://methodic-2030382823.us-central1.run.app](https://methodic-2030382823.us-central1.run.app)
- **133 automated tests** (69 unit + 64 E2E)
- **34 SSE events** streamed per pipeline run, ~5 min end-to-end
- **BigQuery export** with structured schema (17 fields per response)
- **14 blind adversarial reviews** by Gemini and Codex — all passed
- Google AI Agent Challenge submission (Track 1: Net-New Agents)

## Business Model

### Phase 1: Platform (Year 1-2)
- **Self-serve SaaS**: $99-499/mo per team, usage-based on interview sessions
- **API access**: per-study pricing for integration into existing research workflows

### Phase 2: Marketplace (Year 2-3)
- **Custom methodology templates**: industry-specific research frameworks (win-loss, churn analysis, competitive intel)
- **Participant panel integration**: connect to B2B respondent panels (UserTesting, Respondent.io)

### Phase 3: Enterprise (Year 3+)
- **White-label research ops**: embedded in CRM (Salesforce, HubSpot) as automated post-deal research
- **A2A integration**: other enterprise agents can request studies programmatically

## Go-to-Market

### Initial Wedge: B2B SaaS Win-Loss

1. **Why this vertical**: Every SaaS company above $5M ARR does win-loss analysis. Most do it badly (manual, inconsistent, slow). The pain is acute and budget-approved.
2. **Distribution**: Direct outreach to RevOps/Sales Ops leaders. Content marketing around "why your win-loss data is lying to you."
3. **Land**: Free pilot — run one win-loss study, show the quality delta vs. their current approach
4. **Expand**: After proving quality on win-loss → churn analysis → competitive intel → product feedback

### Pricing Comparison

| Approach | Cost per Interview | Time to Insights | Data Quality |
|----------|-------------------|-----------------|-------------|
| Human consultant | $500-2,000 | 6-12 weeks | High (but expensive) |
| Static survey | $0.50-5 | Instant (low quality) | Low |
| **Methodic** | **$15-50** | **5 minutes** | **High (governed, evidence-linked)** |

## Team

[To be filled]

## The Ask

**Raising $X at $Y valuation** to:
1. Build participant panel integration and multi-study support
2. Hire 2 research methodology advisors (domain credibility)
3. Launch beta with 20 B2B SaaS companies for win-loss
4. Achieve $500K ARR within 18 months

## Why Now

1. **LLM costs dropped 90%** in 18 months — autonomous interviews are now economically viable at scale
2. **Enterprise AI adoption** means companies need better input data, not just better models
3. **MCP and A2A standards** enable secure, governed agent-to-agent workflows for the first time
4. **Static surveys peaked** — response rates declining, quality expectations rising
5. **Google ADK maturity** — production-ready multi-agent orchestration didn't exist 12 months ago
