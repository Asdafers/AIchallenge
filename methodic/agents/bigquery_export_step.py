"""BigQuery export step - writes all participant responses to BigQuery."""

from __future__ import annotations

from google.adk.agents import BaseAgent
from google.genai import types

from methodic.schemas import ParticipantResponse
from methodic.tools.bigquery_export import export_to_bigquery


class BigQueryExportStep(BaseAgent):

    async def _run_async_impl(self, ctx) -> types.Content | None:
        state = ctx.session.state
        responses_by_id = state.get("participant_response_by_id", {})
        responses = [
            ParticipantResponse.model_validate(r) for r in responses_by_id.values()
        ]
        result = export_to_bigquery(responses)
        state["export_result"] = result
        return None
