"""Interviewer agent - conducts live B2B win-loss interviews with MCP tools."""

from pathlib import Path
from google.adk.agents.llm_agent import Agent
from methodic import MODEL
from methodic.tools.deal_context import get_deal_context_toolset

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "interviewer_system.md").read_text()

interviewer_agent = Agent(
    name="interviewer",
    model=MODEL,
    output_key="latest_interviewer_turn",
    instruction=_PROMPT,
    tools=[get_deal_context_toolset()],
)
