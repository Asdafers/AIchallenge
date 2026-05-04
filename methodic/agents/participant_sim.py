"""Simulated participant agent - responds in character for testing/demo."""

from pathlib import Path
from google.adk.agents.llm_agent import Agent
from methodic import MODEL_FAST

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "sim_participant_system.md").read_text()

participant_sim_agent = Agent(
    name="participant_sim",
    model=MODEL_FAST,
    output_key="latest_participant_turn",
    instruction=_PROMPT + "\n\nPersona details are in the conversation context.",
)
