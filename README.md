# AI Challenge Workspace

This workspace captures the Google for Startups AI Agent Challenge notes and the working concept for a Track 1 submission.

## Proposed Submission

Working name: Methodic

The idea is to replace tedious, repetitive, low-engagement survey workflows with an agentic data-capture system. Companies should be able to describe a research objective to an AI organizer, receive a statistically grounded survey structure for review, and then hand that structure to a pool of conversational survey agents that collect cleaner, richer, and more complete data from participants.

Core thesis: there are no useful insights without good data, and the data-capture experience is often the weakest part of the analytics pipeline.

Positioning guardrail: do not frame this as an AI survey tool. Frame it as an autonomous research operations agent that creates decision-ready data.

## Key Files

- [challenge.md](/Volumes/workz/GitHubProjects/AIchallenge/challenge.md): cleaned challenge overview.
- [additionaldetails.md](/Volumes/workz/GitHubProjects/AIchallenge/additionaldetails.md): cleaned challenge examples and technology notes.
- [docs/product-brief.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/product-brief.md): product framing for the proposed Track 1 submission.
- [docs/spec.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/spec.md): critique-ready submission spec and implementation blueprint.
- [docs/architecture.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/architecture.md): proposed multi-agent architecture.
- [docs/build-plan.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/build-plan.md): practical build plan and demo scope.
- [docs/winning-strategy.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/winning-strategy.md): competition strategy synthesized from additional AI research.
- [docs/research-synthesis.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/research-synthesis.md): distilled takeaways from Gemini, Claude, and NotebookLM-style research.
- [docs/open-questions.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/open-questions.md): unresolved choices to settle before implementation.
- [docs/gemini-research.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/gemini-research.md): raw Gemini research memo.
- [docs/claude-research.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/claude-research.md): raw Claude research memo.
- [docs/notebooklm-strategy-critique.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/notebooklm-strategy-critique.md): NotebookLM strategy critique export.
- [docs/notebooklm-positioning.md](/Volumes/workz/GitHubProjects/AIchallenge/docs/notebooklm-positioning.md): NotebookLM positioning export.

## Current Direction

Track 1 is the strongest initial fit because the product is a net-new autonomous agent system. The demo should emphasize:

- A B2B use case with clear economic value.
- Agentic planning by the organizer-facing AI.
- Methodology pushback when the user's desired study design will not answer the business question.
- Research-grounded instrument design.
- MCP-backed context lookup or triangulation during participant conversations.
- Interactive participant conversations instead of static forms.
- Clean, structured data output with evidence of improved quality.
- Variable saturation, ambiguity reduction, and thematic traceability.
- Google stack alignment: Gemini, ADK, MCP, and Cloud Run or GKE.
