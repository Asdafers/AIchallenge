# Build Plan

## Goal

Build a Track 1 prototype that proves the value of agentic data capture: a company user can define a research goal, the system creates a grounded survey plan, participant agents conduct adaptive conversations, and the final output is clean, structured, analysis-ready data.

## Phase 1: Define the Wedge

Pick one narrow B2B demo scenario.

Recommended wedge:

B2B SaaS win-loss research for mid-market enterprise deals.

Why:

- Easy for judges to understand.
- Has clear business value and a direct revenue tie.
- Supports both qualitative and quantitative questions.
- Allows simulated participant personas.
- Makes data-quality improvements easy to demonstrate.
- Naturally supports agent-to-agent invocation from a mocked Sales Insights agent.
- Supports MCP triangulation against CRM, product telemetry, or deal context.

Deliverables:

- Research objective.
- Target participant segments.
- Required output schema.
- Baseline static survey for comparison.
- Success metrics.
- Mocked external-agent request.
- Mocked CRM or telemetry context for one triangulation moment.

## Phase 2: Build the Organizer Flow

Create the organizer-facing agent experience.

Capabilities:

- Goal discovery conversation.
- Research brief generation.
- Question pool generation.
- Schema generation.
- Risk and bias review.
- Methodology pushback when the requested design would not support the decision.
- Visual approval summary.

Demo requirement:

- The organizer should feel like they are collaborating with a research operations expert, not filling out a form.

## Phase 3: Build Survey Agent Sessions

Create participant-facing survey agents.

Capabilities:

- Load approved study structure.
- Conduct natural conversation.
- Ask clarifying follow-ups.
- Triangulate one participant claim against approved business context through an MCP tool.
- Keep measurement coverage intact.
- Store structured answers and verbatim snippets.

Demo requirement:

- Show at least three participant personas producing different conversation paths.

## Phase 4: Build Data Quality Layer

Create a post-collection quality review.

Capabilities:

- Completeness scoring.
- Ambiguity detection.
- Schema normalization.
- Contradiction detection.
- Evidence linking from structured field to participant quote.
- Saturation or coverage curve.
- Optional coding-agreement metric if implemented honestly.

Demo requirement:

- Show how the agentic workflow produces cleaner data than a static survey.

## Phase 5: Package for Challenge Submission

Prepare the final story.

Required artifacts:

- Technical demo.
- Architecture diagram.
- Business case.
- Before-and-after data quality comparison.
- Explanation of Gemini, ADK, MCP, and Google Cloud usage.
- Developer trace showing agent handoffs, MCP calls, and the external agent request.
- Short video script.

## Implementation Notes

Use boring infrastructure for the prototype. The product should feel advanced because the workflow is intelligent, not because the infrastructure is exotic.

Likely first implementation:

- Web app for organizer and participant sessions.
- Backend service for study state and agent orchestration.
- Gemini-backed agents.
- MCP tool boundary for research, storage, and export tools.
- Cloud Run deployment.
- BigQuery or BI-ready export.

Preferred ADK workflow shape:

- `SequentialAgent` for organizer planning: Organizer -> Methodology -> Question Design -> Review.
- `ParallelAgent` for simulated participant sessions.
- `LoopAgent` or equivalent bounded loop for variable coverage and saturation checks.

## Immediate Next Steps

1. Lock the B2B win-loss demo wedge and target buyer.
2. Define the output data schema.
3. Draft the organizer conversation flow.
4. Draft the participant conversation policy.
5. Define the methodology pushback rules.
6. Define the MCP triangulation tool contract.
7. Build a clickable prototype or thin vertical slice.
