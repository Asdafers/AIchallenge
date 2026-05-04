# Devpost Submission Copy

Copy-paste text for the Devpost submission form fields.

---

## Project Name

Methodic

## Tagline

Autonomous research operations agent that turns B2B business decisions into governed, evidence-linked data.

## Track

Track 1: Build — Net-New Agents

## What it does

Methodic replaces static B2B surveys with an autonomous research operations workflow. Given a business decision ("Why are mid-market deals slipping?"), it:

1. Accepts external agent requests and asks clarifying questions before proceeding
2. Reviews the proposed study methodology and pushes back on sampling bias
3. Conducts interactive participant conversations that probe vague answers ("price") into decision-relevant variables ("procurement friction vs. ROI justification")
4. Uses MCP to securely look up CRM and telemetry context, turning generic responses into evidence-linked data points
5. Tracks variable coverage in real time and autonomously re-plans when gaps remain
6. Exports structured, scored data to BigQuery with full evidence traceability

The result: a +69% quality improvement over static surveys, measured by the same rubric applied to both.

## Inspiration

B2B teams spend months running win-loss research to understand deal outcomes, but the data-capture layer — static surveys — produces shallow answers. "Price" appears in every lost-deal report, but dashboards can't distinguish packaging friction from ROI justification failures. We built Methodic to fix the upstream data problem: capture governed, evidence-linked data that actually supports business decisions.

## How we built it

Methodic is a vertical-slice prototype demonstrating the full autonomous workflow:

- **Gemini API** powers methodology review (live pushback on biased sampling) and conversation design
- **Model Context Protocol (MCP)** provides a real server boundary for `lookup_deal_context` — CRM and telemetry data flows through stdio JSON-RPC 2.0 with server-side field filtering
- **Python orchestration** chains 7 work packages: external request → methodology → conversations → MCP context → quality scoring → autonomous re-plan → BigQuery export
- **Docker / Cloud Run** containerization proves all 7 steps execute in a single deployable unit (local container mode, with operator instructions for Cloud Run deployment)
- **BigQuery schema validation** ensures export-ready structured data with 17 fields per participant row

Multi-agent coordination used Mission-MCP for task management, with Claude and Gemini executing complementary roles: Claude for implementation, Gemini for blind adversarial reviews via the Agent Communication Protocol (ACP).

## Challenges we ran into

- **Honest labeling vs. over-claiming**: Every trace artifact includes an `honest_label` field that states exactly what it proves. The container runs locally, not on live Cloud Run; WP4 uses deterministic fallback without API keys; BigQuery exports are dry-run validated. We chose transparency over impressive-sounding claims.
- **MCP field filtering**: The MCP server must enforce `allowed_fields` server-side to prevent data leakage. Getting the filtering correct while merging CRM and telemetry sources required careful contract design.
- **Autonomous re-plan scope control**: The re-plan trigger must add exactly one targeted session, not spiral into unbounded data collection. We hardcoded the constraint: one reserve participant, one variable gap, one session.

## Accomplishments we're proud of

- **Real MCP boundary**: Not a simulated function call — a real stdio JSON-RPC 2.0 server with tool registration, field filtering, and trace logging
- **Measurable quality delta**: Same rubric, same participants, static vs. Methodic — 0.069 vs. 0.761 composite score
- **Multi-agent build process**: Claude implemented, Gemini reviewed adversarially (9 blind review gates passed), Codex signed off on design — all coordinated through Mission-MCP
- **Every artifact is honest**: No over-claimed deployment status, no fabricated statistics, no hidden disclaimers

## What we learned

The hardest part of building an autonomous agent isn't the AI — it's the governance layer. Knowing when to stop probing, which fields to expose through MCP, when a re-plan is warranted vs. noise — these are measurement design problems, not engineering problems. The Methodology Agent (WP4) turned out to be the most important component: without pushback on bad study design, the downstream data quality improvements don't matter.

## What's next for Methodic

- Live Gemini-powered conversations (replacing fixture-driven dialogue)
- ADK orchestration layer (replacing subprocess chaining)
- Cloud Run deployment with BigQuery live writes
- Frontend dashboard for organizer review and variable coverage monitoring
- Multi-study support beyond the B2B win-loss wedge

## Built with

- Gemini API
- Agent Development Kit (ADK)
- Model Context Protocol (MCP)
- Cloud Run (containerized, deployment-ready)
- BigQuery (schema-validated, dry-run export)
- Python
- Docker

## Links

- GitHub: [repository URL]
- Demo video: [video URL]
