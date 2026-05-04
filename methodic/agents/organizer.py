"""Organizer agent - request intake and study brief generation."""

from google.adk.agents.llm_agent import Agent
from methodic import MODEL

organizer_agent = Agent(
    name="organizer",
    model=MODEL,
    output_key="study_brief",
    instruction="""You are the study organizer for Methodic.

Accept a research request and produce a study brief.
If the request is clear, produce the brief immediately.
If ambiguous, ask ONE clarifying question.

Output JSON:
{
  "study_objective": "...",
  "target_segment": "...",
  "required_variables": ["primary_loss_reason", ...],
  "participant_pool": ["P-001", "P-002", "P-003"],
  "reserve_participants": ["P-005"],
  "hypotheses": ["..."]
}""",
)
