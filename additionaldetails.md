# Additional Challenge Details

## Example Problem Areas

The challenge favors complex, multi-step workflows where agents take meaningful action rather than only answering questions.

Example directions from the challenge material:

- Automated talent sourcing: screen resumes against roles, use internal hiring rubrics, and generate tailored interview questions.
- IT incident resolution: triage alerts, retrieve historical tickets, run diagnostics, and propose fixes.
- Dynamic supply-chain prediction: monitor external events, combine them with inventory data, and proactively alert affected clients.

## Reference Example: Smart Facility Energy Agent

The challenge material uses a smart facility energy agent to explain how a single concept can fit each track.

### Track 1 Build

Use ADK to create the core orchestration engine. Use MCP to connect to HVAC sensors, weather APIs, and calendar data. The agent does not only report current state; it autonomously changes heating in unoccupied rooms based on building context.

### Track 2 Optimize

Stress test the agent against rare events, such as an extreme weather event happening during a peak-demand pricing surge. Use simulation, observability, and optimizer tooling to debug reasoning failures and refine behavior.

### Track 3 Refactor

Move the working MVP onto Google Cloud infrastructure, ensure Gemini-powered reasoning, add Agent Identity, and use Agent-to-Agent (A2A) protocol so the energy agent can coordinate with other enterprise agents.

## Track 3 Mandates

Track 3 projects must meet these architectural requirements:

- B2B focus: solve a clear business-to-business problem.
- Cloud-native runtime: deploy on Google Cloud infrastructure, such as Cloud Run or GKE.
- Google Cloud-powered intelligence: use Gemini, or a third-party LLM deployed exclusively through Agent Platform.
- A2A interoperability: use Agent-to-Agent protocol so the agent can be discovered by and coordinate with enterprise agents.

## General Participant Guidance

- Focus on the design and orchestration of interactions between multiple agents.
- Deploy the multi-agent system on Agent Engine where appropriate.
- Clearly articulate the business use case.
- Use grounding and retrieval to improve reliability.
- Show why collaboration between specialized agents is more capable than a single agent.

## Mandatory Technologies

- Intelligence: Gemini API, or a third-party LLM deployed through Agent Platform.
- Orchestration: ADK, or a supported open-source framework managed on Google's platform.
- Infrastructure: Google Cloud deployment, such as Cloud Run or GKE.

## Resources To Find

The pasted source notes referenced these resources but did not include links:

- ADK documentation.
- Complete Resource Guide.
- Official Rules.
