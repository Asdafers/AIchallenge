"""Session init step - resets per-participant state at the start of each session."""

from __future__ import annotations
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

PARTICIPANT_QUEUE = ["P-001", "P-002", "P-003"]


class SessionInitStep(BaseAgent):

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        state["turn_count"] = 0

        completed = list(state.get("participant_response_by_id", {}).keys())
        active = state.get("active_participant_id")
        if active and active not in completed:
            pass
        else:
            queue = state.get("participant_queue", PARTICIPANT_QUEUE.copy())
            remaining = [p for p in queue if p not in completed]
            if remaining:
                state["active_participant_id"] = remaining[0]
            else:
                state["active_participant_id"] = active or "P-001"

        yield Event(
            author=self.name,
            content=None,
            actions=EventActions(state_delta={
                "turn_count": 0,
                "current_participant": state["active_participant_id"],
            }),
        )
