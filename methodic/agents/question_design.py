"""Question design agent - maps questions to canonical variables."""

from google.adk.agents.llm_agent import Agent
from methodic import MODEL

question_design_agent = Agent(
    name="question_design",
    model=MODEL,
    output_key="question_pool",
    instruction="""You are the question design agent for Methodic.

Design a pool of interview questions mapping to 8 canonical variables.

Rules:
- Each variable must have at least one question
- Questions must be open-ended and non-leading
- Include follow-up probes
- Maximum 12 questions

Output JSON array:
[{"question_id": "Q1", "text": "...", "target_variables": [...], "follow_up_probes": [...]}]""",
)
