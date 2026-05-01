# Agent Instructions

This folder is a planning and build workspace for a Google for Startups AI Agent Challenge submission.

## Product Direction

Default project concept: a Track 1 net-new agent system for better business data capture.

The core idea is that companies cannot get reliable insights without good data, and traditional surveys are often tedious, repetitive, low-engagement, and methodologically weak. The proposed product replaces static surveys with an agentic workflow:

1. An organizer discusses purpose, goals, target audience, constraints, and decisions with an AI research organizer.
2. The system prepares a research brief, data schema, question pool, and methodological rationale.
3. The system presents a visual review package for approval.
4. A pool of survey agents conducts interactive participant conversations.
5. A data quality layer cleans, validates, scores, and exports analysis-ready data.

## Working Assumptions

- Treat this as Track 1 unless the user explicitly changes direction.
- Favor a B2B use case and clear business value.
- Keep the first prototype scoped to a complete vertical slice, not a broad platform.
- Prefer Google-aligned architecture: Gemini, ADK, MCP, and Cloud Run or GKE.
- Make data quality measurable in the demo.
- Avoid over-claiming statistical rigor; distinguish statistical, qualitative, and operational quality claims.

## Workspace Rules

- Keep challenge reference notes separate from product planning docs.
- Use Markdown for planning artifacts unless implementation begins.
- When adding technical plans, include verification and demo implications.
- If building a frontend, start with the working experience, not a marketing landing page.
- Preserve the user thesis: no insights without good data.
