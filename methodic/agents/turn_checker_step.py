"""Turn checker step - deterministic agent that exits the interview loop.

Checks turn count and per-participant coverage. Sets ctx.actions.escalate = True
when stop conditions are met. This is a custom BaseAgent, not a FunctionTool,
because ADK workflow sub_agents must be agent instances.
"""

from __future__ import annotations
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from methodic.schemas import CANONICAL_FIELDS


class TurnCheckerStep(BaseAgent):
    max_turns: int = 6

    def should_escalate(self, state: dict, max_turns: int | None = None) -> bool:
        mt = max_turns or self.max_turns
        turn_count = state.get("turn_count", 0)
        if turn_count >= mt:
            return True
        coverage = state.get("participant_coverage", {})
        if coverage and all(
            coverage.get(f) == "covered_high_confidence"
            for f in CANONICAL_FIELDS
        ):
            return True
        return False

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        state["turn_count"] = state.get("turn_count", 0) + 1
        if self.should_escalate(state):
            ctx.actions.escalate = True
        yield Event(author=self.name, content=None)
