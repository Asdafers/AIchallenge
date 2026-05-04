"""Extractor step - calls Gemini structured extraction after each turn pair.

Reads transcript from state, calls extractor, writes result back.
"""

from __future__ import annotations
from typing import Any

from google.adk.agents import BaseAgent
from google.genai import types

from methodic.tools.extractor import extract_structured_fields


class ExtractorStep(BaseAgent):

    async def _run_async_impl(self, ctx) -> types.Content | None:
        state = ctx.session.state
        participant_id = state.get("active_participant_id", "unknown")
        study_id = state.get("study_id", "unknown")
        transcripts = state.get("transcripts_by_participant", {})
        transcript = transcripts.get(participant_id, [])

        if not transcript:
            return None

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

        return None
