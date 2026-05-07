"""Replanner step - decides whether to continue fieldwork or stop.

Calls the LLM for a coverage assessment and decision, then escalates
the outer fieldwork_loop when the decision is STOP.
"""

from __future__ import annotations
import json
import logging
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google import genai

from methodic import MODEL
from methodic.schemas import ParticipantResponse
from methodic.tools.coverage_checker import check_coverage

log = logging.getLogger(__name__)

REPLANNER_PROMPT = """You are the replanner for Methodic's fieldwork loop.

Current coverage state:
{coverage_json}

Decision logic:
1. ALL 8 variables covered_high_confidence -> STOP
2. Variable is "ambiguous" and reserve participant can resolve -> ADD_PARTICIPANT
3. Max iterations reached -> STOP
4. Only "missing" with no available participants -> STOP

Output ONLY valid JSON:
{{"decision": "STOP" | "ADD_PARTICIPANT", "reason": "...", "add_participant_id": null | "P-005", "target_variables": []}}
"""


class ReplannerStep(BaseAgent):

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        responses_by_id = state.get("participant_response_by_id", {})

        responses = [
            ParticipantResponse.model_validate(r)
            for r in responses_by_id.values()
        ]
        coverage = check_coverage(responses)

        try:
            client = genai.Client()
            response = await client.aio.models.generate_content(
                model=MODEL,
                contents=REPLANNER_PROMPT.format(
                    coverage_json=json.dumps(coverage, indent=2)
                ),
                config={"response_mime_type": "application/json"},
            )
            decision = json.loads(response.text) if response.text else {"decision": "STOP", "reason": "empty response"}
        except Exception as e:
            log.warning("Replanner LLM call failed: %s", e)
            decision = {"decision": "STOP", "reason": f"LLM error: {e}"}

        state["replan_decision"] = decision

        if decision.get("decision") == "STOP":
            ctx.actions.escalate = True
        elif decision.get("decision") == "ADD_PARTICIPANT":
            new_pid = decision.get("add_participant_id", "P-005")
            state["active_participant_id"] = new_pid
            state["turn_count"] = 0

        yield Event(author=self.name, content=None)


replanner_agent = ReplannerStep(name="replanner")
