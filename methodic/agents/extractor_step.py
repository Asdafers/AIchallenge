"""Extractor step - calls Gemini structured extraction after each turn pair.

Reads transcript from state, calls extractor, writes result back.
Also assembles the running transcript from individual turn outputs.
"""

from __future__ import annotations
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from methodic.tools.extractor import extract_structured_fields


class ExtractorStep(BaseAgent):

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        participant_id = state.get("active_participant_id", "P-001")
        study_id = state.get("study_id", "unknown")

        transcripts = state.get("transcripts_by_participant", {})
        transcript = transcripts.get(participant_id, [])

        interviewer_turn = state.get("latest_interviewer_turn", "")
        participant_turn = state.get("latest_participant_turn", "")

        if interviewer_turn:
            transcript.append({"role": "interviewer", "content": interviewer_turn})
        if participant_turn:
            transcript.append({"role": "participant", "content": participant_turn})

        transcripts[participant_id] = transcript
        state["transcripts_by_participant"] = transcripts

        if not transcript:
            yield Event(author=self.name, content=None)
            return

        result = await extract_structured_fields(
            transcript=transcript,
            participant_id=participant_id,
            study_id=study_id,
            segment=state.get("segment", "unknown"),
            persona_summary=state.get("persona_summary", ""),
        )

        responses = state.get("participant_response_by_id", {})
        responses[participant_id] = result.model_dump()
        state["participant_response_by_id"] = responses
        state["participant_coverage"] = result.coverage_state

        yield Event(author=self.name, content=None)
