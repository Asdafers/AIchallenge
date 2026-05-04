"""Methodology agent - reviews study brief, pushes back on weaknesses."""

from pathlib import Path
from google.adk.agents.llm_agent import Agent
from methodic import MODEL

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "methodology_system.md").read_text()

methodology_agent = Agent(
    name="methodology",
    model=MODEL,
    output_key="methodology_review",
    instruction=_PROMPT + "\n\nReview the study brief from the conversation history.",
)
