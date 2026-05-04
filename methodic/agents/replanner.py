"""Replanner - decides whether to add more sessions. Has check_coverage tool."""

from google.adk.agents.llm_agent import Agent
from google.adk.tools import FunctionTool
from methodic import MODEL
from methodic.tools.coverage_checker import check_coverage
from methodic.schemas import ParticipantResponse


def _check_coverage_tool(responses_json: str) -> str:
    """Check variable coverage across participant responses.

    Args:
        responses_json: JSON string of participant response dicts
    Returns:
        JSON string with coverage summary
    """
    import json
    data = json.loads(responses_json)
    responses = [ParticipantResponse.model_validate(d) for d in data]
    result = check_coverage(responses)
    return json.dumps(result)


replanner_agent = Agent(
    name="replanner",
    model=MODEL,
    output_key="replan_decision",
    tools=[FunctionTool(func=_check_coverage_tool)],
    instruction="""You are the replanner for Methodic's fieldwork loop.

You have the check_coverage tool. Use it to assess coverage.

Decision logic:
1. ALL 8 variables covered_high_confidence -> STOP
2. Variable is "ambiguous" and reserve participant can resolve -> ADD_PARTICIPANT
3. Max iterations reached -> STOP
4. Only "missing" with no available participants -> STOP

Output JSON:
{
  "decision": "STOP" | "ADD_PARTICIPANT",
  "reason": "...",
  "add_participant_id": null | "P-005",
  "target_variables": ["procurement_friction"]
}""",
)
