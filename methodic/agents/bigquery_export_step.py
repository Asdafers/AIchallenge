"""BigQuery export step - writes all participant responses to BigQuery."""

from __future__ import annotations
import asyncio
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from methodic.schemas import ParticipantResponse
from methodic.tools.bigquery_export import export_to_bigquery


class BigQueryExportStep(BaseAgent):

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        responses_by_id = state.get("participant_response_by_id", {})
        responses = [
            ParticipantResponse.model_validate(r) for r in responses_by_id.values()
        ]
        result = await asyncio.to_thread(export_to_bigquery, responses)
        state["export_result"] = result
        yield Event(
            author=self.name,
            content=None,
            actions=EventActions(state_delta={"export_status": result}),
        )
