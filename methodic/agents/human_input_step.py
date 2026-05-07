"""Human input step - blocks on asyncio.Queue for real participant input.

Replaces participant_sim_agent in the interview loop for interactive mode.
Writes the human's response to latest_participant_turn in state, same key
that participant_sim uses, so extractor and turn_checker work unchanged.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types


class HumanInputStep(BaseAgent):
    session_registry: dict
    timeout_seconds: float = 300.0

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        session_id = ctx.session.id
        isess = self.session_registry[session_id]

        isess.input_requested = True

        yield Event(
            author=self.name,
            content=types.Content(
                role="model", parts=[types.Part(text="awaiting_input")]
            ),
            actions=EventActions(state_delta={"input_requested": True}),
        )

        try:
            human_text = await asyncio.wait_for(
                isess.input_queue.get(), timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            human_text = "No response provided."

        isess.input_requested = False

        yield Event(
            author=self.name,
            content=types.Content(
                role="model", parts=[types.Part(text=human_text)]
            ),
            actions=EventActions(
                state_delta={
                    "latest_participant_turn": human_text,
                    "input_requested": False,
                },
            ),
        )
