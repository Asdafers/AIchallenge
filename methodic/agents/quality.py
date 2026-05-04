"""Quality reviewer - reviews participant responses for themes and contradictions."""

from google.adk.agents.llm_agent import Agent
from methodic import MODEL

quality_agent = Agent(
    name="quality_reviewer",
    model=MODEL,
    output_key="quality_report",
    instruction="""You are the quality reviewer for Methodic.

Review collected data for:
1. Cross-participant themes
2. Contradictions between participants
3. Evidence gaps
4. Data quality (specific quotes vs vague)

Output JSON:
{
  "themes": [{"theme": "...", "supporting_participants": [...], "confidence": 0.9}],
  "contradictions": [{"variable": "...", "participants": [...], "description": "..."}],
  "gaps": ["variable_name"],
  "overall_quality_score": 0.0-1.0,
  "recommendation": "SUFFICIENT" | "NEEDS_MORE_DATA"
}""",
)
