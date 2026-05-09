# Methodic — VC Pitch Document

## One-Liner

Methodic is the autonomous research-ops agent that replaces manual B2B win-loss interviews with governed, evidence-linked data capture — turning business questions into decision-ready datasets at 10x lower cost.

## The Problem

**B2B teams make $100K+ decisions on $500 worth of data.**

Enterprise analytics, BI dashboards, and AI decision systems are sophisticated — but their inputs are shallow. The data-capture layer is broken:

- **Manual win-loss interviews** cost $500-2,000 per session via firms like Clozd, take 6-12 weeks, and don't scale beyond 10-15 interviews per quarter
- **Static surveys** (SurveyMonkey, Typeform) have fixed branching — they accept "price" and move on, producing data too vague to act on
- **Revenue intelligence** (Gong, Chorus) captures what buyers said *to the rep* — not the unvarnished reasons they chose a competitor after the deal closed
- **No tool connects interview data to CRM context** — analysts manually cross-reference deal records with interview notes

The result: downstream analytics produces the wrong answers at scale because upstream data capture doesn't probe, doesn't adapt, and doesn't link evidence to business context.

## The Solution

Methodic is a multi-agent system built on Google's Agent Development Kit that conducts autonomous, methodology-governed research interviews:

1. **Plans the study** — organizer + methodology agents structure objectives and push back on sampling bias (e.g., "Champions alone cannot answer pricing questions — add economic buyers")
2. **Conducts adaptive interviews** — probes vague answers into specific decision variables in real time
3. **Triangulates against CRM context** — MCP tools pull deal and telemetry data mid-interview for sharper follow-ups
4. **Tracks coverage autonomously** — identifies gaps across 8 canonical research variables, re-plans when needed
5. **Exports structured data** — evidence-linked rows with confidence scores directly to BigQuery

**Not a chatbot survey. Not a form with AI.** A governed research operations agent that applies qualitative research methodology at scale.

## Why Not [Existing Tool]?

| Objection | Answer |
|-----------|--------|
| **"Why not Gong?"** | Gong captures what buyers said *during the sales cycle* — polite, filtered, performance-aware. Methodic captures the unvarnished post-decision truth: why they *actually* chose the competitor, what the internal procurement process looked like, and which objections were never raised to the rep. Different data, different buyer state. |
| **"Why not Clozd?"** | Clozd charges $500-2K per human-conducted interview. At that price, teams do 10-15 per quarter. Methodic delivers comparable depth at $50-150 per interview, enabling 50-100+ per quarter. Clozd's strength is methodology credibility — Methodic must earn this through verified benchmarks and research advisor partnerships. |
| **"Why not Outset.ai?"** | Outset does AI-moderated interviews at scale across video, voice, and text. Outset is the closest competitor. Methodic's wedge is narrower and deeper: CRM-native context injection (MCP), variable-level coverage tracking with autonomous re-plan, evidence-linked structured output, and methodology governance that pushes back on study design before interviews begin. Outset is broad; Methodic is purpose-built for B2B decision research. |
| **"Why not Qualtrics?"** | Qualtrics owns enterprise survey infrastructure. When Qualtrics adds adaptive AI chat nodes (and they will), it will be a general-purpose feature across their platform. Methodic's advantage is vertical depth: CRM integration, research methodology enforcement, and structured variable extraction designed specifically for B2B decision analysis. The play is integration (Qualtrics exports → Methodic deep-dives) not displacement. |

## Market

### Beachhead ICP

B2B SaaS companies with:
- 50+ lost opportunities per quarter
- RevOps or Product Marketing ownership of win-loss
- Existing win-loss spend (consultants, Clozd, or ad hoc)
- CRM (Salesforce/HubSpot) with deal-level data

### Market Sizing

**Top-down:** Global market research industry: ~$54B (Statista 2023). Qualitative B2B research segment: ~$2-4B. AI-moderated research tools (Outset $17M Series A, Strella $14M Series A) — emerging category with $100M+ in recent VC investment.

**Bottom-up:**
- ~15,000 B2B SaaS companies with >$5M ARR in US/EU
- ~3,000 have formal or semi-formal win-loss programs
- Initial ACV target: $24K-60K/year
- Year 3 target: 200 customers × $36K avg ACV = **$7.2M ARR**
- Expansion to churn/competitive/product research: 3-5x multiplier on ACV

### Expansion Path

Win-loss → churn analysis → competitive intelligence → pricing/packaging research → product feedback → CRM-native autonomous research triggers

## Competitive Landscape

| Category | Players | Methodic's Position |
|----------|---------|-------------------|
| **Human win-loss** | Clozd, Klue (acquired DoubleCheck) | 10x lower cost, 10x higher volume. Must earn methodology credibility through research advisors and verified benchmarks. |
| **AI-moderated research** | Outset.ai ($17M A), Strella ($14M A) | Narrower and deeper: CRM context, variable tracking, methodology governance. Complement panels/repos, don't compete on breadth. |
| **Revenue intelligence** | Gong, Chorus, Clari | Different data: post-decision truth vs. in-cycle performance. Complementary — Gong shows what happened, Methodic shows why. |
| **XM/Survey platforms** | Qualtrics ($6.75B Forsta acquisition), Medallia, Alchemer | Integration play, not displacement. Methodic deep-dives where surveys surface signals. |
| **Research repos/panels** | Dovetail, UserTesting, User Interviews | Channel/integration partners for participant sourcing and insight storage. |

### Product Differentiators (Not Moats)

These are current advantages, not defensible moats:
- CRM-native context injection via MCP (deal data informs interview probes)
- Variable-level coverage tracking with autonomous re-plan
- Methodology governance agent that pushes back on study design
- Evidence-linked structured output with confidence scores

### Defensibility Thesis (What We Must Build)

1. **Proprietary methodology corpus** — co-developed with research methodology advisors, validated on real customer data
2. **CRM integration depth** — native Salesforce/HubSpot connectors that trigger research automatically on deal events
3. **Verified benchmark dataset** — published quality comparisons on real (not simulated) interviews, independently scored
4. **Workflow system-of-record** — become the place research teams configure, run, and review win-loss programs

## Business Model

### Pricing

| Tier | ACV | Includes |
|------|-----|----------|
| **Pilot** | $5K-15K (one-time) | One study, up to 30 interviews, human QA review, before/after quality report |
| **Team** | $24K-36K/year | Quarterly studies, standard CRM integration, up to 100 interviews/quarter |
| **Enterprise** | $60K-150K/year | Unlimited studies, custom methodology templates, SSO, audit trail, dedicated CSM |

Usage component: per completed qualified interview (excludes participant incentives/recruiting unless bundled).

### Unit Economics Target

- Cost per interview (LLM + compute): $3-8
- Revenue per interview: $50-150
- Gross margin target: 85%+
- Participant incentives: customer-provided or panel integration (pass-through)

## Respondent Acquisition

**The hardest problem: how do you get busy VPs to talk to an AI?**

1. **Customer-sourced**: customers send their own contacts (like Clozd). Methodic provides the interview link and consent flow.
2. **CRM-triggered**: automated outreach via customer's existing email/Outreach/Salesloft on deal-close events.
3. **Panel integration**: User Interviews, Respondent.io for recruited participants.
4. **Incentive automation**: Tremendous/Rybbon integration for auto-bounties ($50-150 per completed interview).
5. **Trust signals**: branded experience, clear consent, recording controls, "this conversation is for [Company]'s internal research" framing.

Response rates on AI-moderated interviews are an open question. Our bet: B2B professionals who already accept survey requests (30-40% baseline) will accept AI interviews at similar rates if the experience is professional and the incentive is appropriate.

## Trust & Compliance

- **Consent flow**: explicit opt-in before interview begins, with clear AI disclosure
- **Data retention**: configurable per-customer retention policies
- **Redaction**: PII/sensitive content detection and auto-redaction before export
- **Human review**: optional human QA layer before data enters customer systems
- **Security roadmap**: SOC2 Type II by Month 18, GDPR/CCPA data handling from launch
- **Admin controls**: interview topic boundaries, escalation to human, kill switch

## Traction

### Product Proof (Current)

- Live on Cloud Run with Vertex AI — full pipeline completes in ~5 minutes
- 133 automated tests (69 unit + 64 E2E)
- 34 SSE events streamed per pipeline run across 13 agent types
- BigQuery export with structured schema (17 fields per response)
- 14 blind adversarial reviews by Gemini and Codex — all passed
- Google AI Agent Challenge submission (Track 1: Net-New Agents)

### Commercial Proof (Needed)

- [ ] 20-30 buyer discovery interviews with RevOps/Product Marketing leaders
- [ ] 3-5 design partner LOIs for real win-loss pilots
- [ ] Quality benchmark on real customer interviews (not simulated)
- [ ] First paid pilot with before/after evidence

## Team

[To be filled — must demonstrate:]
- Research methodology expertise (academic or practitioner)
- Enterprise SaaS GTM experience
- AI/ML systems engineering
- Security/compliance ownership

If founding team lacks research credentials, the pitch must include named research methodology advisors.

## The Ask

**Raising $[X]M pre-seed/seed** to:

1. **Months 1-6**: 30 buyer discovery interviews, 5 design partner pilots on real win-loss data, verified quality benchmark
2. **Months 6-12**: CRM integration (Salesforce), SOC2 prep, 10 paying customers, $200K ARR
3. **Months 12-18**: SOC2 Type II, panel integrations, expansion to churn analysis, $500K+ ARR

**Milestone for next round**: 20+ paying customers, $500K+ ARR, verified quality benchmark on real interviews, SOC2 Type II.

## Why Now

1. **AI interview normalization** — Outset ($17M), Strella ($14M) have validated that buyers accept AI-moderated research. The category exists; the question is who owns the B2B decision-research wedge.
2. **Budget pressure on services** — $500-2K per human interview is under scrutiny. RevOps teams want Clozd-quality insights at software prices.
3. **CRM-native AI expectations** — Salesforce Einstein, HubSpot AI, and Gong's AI features are training buyers to expect AI-powered workflows connected to their deal data.
4. **Data-quality bottleneck** — organizations investing in analytics and AI decision systems are discovering that better models don't help when input data is shallow and inconsistent.
5. **Infrastructure maturity** — Google ADK, MCP, and A2A standards make governed multi-agent research workflows production-ready for the first time.
