"""Coverage step - computes study-wide coverage from all participant responses."""

from __future__ import annotations

from google.adk.agents import BaseAgent
from google.genai import types

from methodic.schemas import ParticipantResponse
from methodic.tools.coverage_checker import check_coverage


class CoverageStep(BaseAgent):

    def compute(self, responses_by_id: dict) -> dict:
        responses = [
            ParticipantResponse.model_validate(r) for r in responses_by_id.values()
        ]
        return check_coverage(responses)

    async def _run_async_impl(self, ctx) -> types.Content | None:
        state = ctx.session.state
        responses_by_id = state.get("participant_response_by_id", {})
        result = self.compute(responses_by_id)
        state["coverage_state"] = result
        return None
