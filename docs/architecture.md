# Architecture Sketch

## System Roles

### Organizer Agent

Owns the front-door conversation with the company user. It turns vague business goals into a concrete data-capture plan.

Responsibilities:

- Interview the organizer.
- Identify decisions the data must support.
- Detect missing scope, ambiguous goals, and risky assumptions.
- Create or update the research brief.
- Route work to specialist agents.
- Present the final plan for approval.

### Methodology Agent

Grounds the plan in research and measurement practice.

Responsibilities:

- Recommend suitable data-capture methods.
- Identify sampling and segmentation requirements.
- Flag bias, leading-question risks, and measurement validity issues.
- Suggest confidence, sample-size, and coverage considerations.
- Explain tradeoffs in plain language.

### Sampling Plan Agent

Creates practical sampling and quota guidance for the study.

Responsibilities:

- Identify which participant segments are required to support the business decision.
- Flag sample plans that over-represent convenient or biased respondents.
- Recommend quota targets for the demo scenario.
- Explain when the prototype should avoid representativeness claims.

### Question Design Agent

Turns the approved research brief into a usable question pool.

Responsibilities:

- Draft questions.
- Create branching logic.
- Map every question to a goal, variable, or hypothesis.
- Produce participant-friendly wording.
- Maintain reusable question variants.

### Review and Visualization Agent

Builds the organizer-facing review package.

Responsibilities:

- Summarize the research plan.
- Show question coverage against goals.
- Visualize participant journeys.
- Highlight risks and unresolved assumptions.
- Provide approval controls for launch.

### Survey Agent Pool

Conducts participant conversations from the approved structure.

Responsibilities:

- Personalize the conversation while preserving measurement intent.
- Ask follow-up questions when responses are vague.
- Capture structured responses.
- Preserve useful verbatim quotes.
- Respect stop conditions and consent boundaries.

### Data Quality Agent

Reviews collected data before analysis.

Responsibilities:

- Detect incomplete, contradictory, or low-confidence responses.
- Normalize outputs to the target schema.
- Attach quality scores and provenance.
- Recommend re-contact or exclusion where appropriate.

### External Requesting Agent

Represents the agentic-enterprise framing. In the demo, this can be a mocked Sales Insights agent that asks Methodic to run a win-loss study.

Responsibilities:

- Submit a structured study request.
- Receive Methodic's task status and final evidence-linked dataset summary.
- Show that Methodic can be called by humans or by other agents.

## Suggested Google Stack

- Gemini for reasoning and conversational intelligence.
- ADK for agent orchestration.
- MCP for connecting to external tools and data stores.
- Cloud Run for the first deployable prototype.
- Firestore or Cloud SQL for study configuration and response storage.
- BigQuery for structured output and analytics demo.
- Vertex AI Search or Google Search grounding for methodology and market/context research.

## Data Flow

1. Organizer states the business problem.
2. Optionally, an external agent submits the request as a structured task.
3. Organizer Agent builds a research brief through dialogue.
4. Methodology Agent validates measurement approach and flags risks.
5. Sampling Plan Agent proposes segments and quotas.
6. Question Design Agent creates the question pool and schema.
7. Review and Visualization Agent prepares the approval package.
8. Organizer approves or edits.
9. Survey Agent Pool interviews participants.
10. Survey Agent uses MCP to triangulate one approved business-context claim.
11. Data Quality Agent validates and normalizes responses.
12. System exports clean data, metadata, and traceable evidence.
13. System returns a structured completion to the requesting agent or organizer.

## Demo Boundary

For a challenge prototype, the strongest demo is a complete vertical slice:

- One organizer workflow.
- One study type.
- A simulated participant pool.
- Conversational survey sessions.
- One external-agent request.
- One MCP triangulation moment.
- Clean structured dataset output.
- Visual review page.
- Final quality report comparing static-form data against agent-captured data.
