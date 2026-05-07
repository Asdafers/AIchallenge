"""Tests for HumanInputStep - the human-in-the-loop agent."""

import asyncio
import pytest
from dataclasses import dataclass, field
from unittest.mock import MagicMock

from methodic.agents.human_input_step import HumanInputStep


@dataclass
class MockInteractiveSession:
    input_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    input_requested: bool = False


def _make_ctx(session_id: str = "test-session"):
    """Build a minimal mock InvocationContext."""
    ctx = MagicMock()
    ctx.session.id = session_id
    ctx.session.state = {
        "latest_participant_turn": "",
        "input_requested": False,
    }
    return ctx


@pytest.mark.asyncio
async def test_human_input_step_signals_input_requested():
    isess = MockInteractiveSession()
    registry = {"test-session": isess}
    step = HumanInputStep(name="participant", session_registry=registry)
    ctx = _make_ctx()

    # Pre-load the queue so the step doesn't block
    await isess.input_queue.put("My answer")

    events = []
    async for event in step._run_async_impl(ctx):
        events.append(event)

    # First event signals input_requested
    assert events[0].actions.state_delta["input_requested"] is True
    assert events[0].author == "participant"

    # Second event delivers the human's response
    assert events[1].content.parts[0].text == "My answer"
    assert events[1].actions.state_delta["latest_participant_turn"] == "My answer"
    assert events[1].actions.state_delta["input_requested"] is False


@pytest.mark.asyncio
async def test_human_input_step_sets_input_requested_flag():
    isess = MockInteractiveSession()
    registry = {"test-session": isess}
    step = HumanInputStep(name="participant", session_registry=registry)
    ctx = _make_ctx()

    assert isess.input_requested is False

    # Put message after a short delay so we can observe the flag
    async def delayed_put():
        await asyncio.sleep(0.05)
        assert isess.input_requested is True
        await isess.input_queue.put("Delayed answer")

    asyncio.create_task(delayed_put())

    events = []
    async for event in step._run_async_impl(ctx):
        events.append(event)

    assert isess.input_requested is False
    assert events[1].content.parts[0].text == "Delayed answer"


@pytest.mark.asyncio
async def test_human_input_step_timeout():
    isess = MockInteractiveSession()
    registry = {"test-session": isess}
    step = HumanInputStep(
        name="participant", session_registry=registry, timeout_seconds=0.1,
    )
    ctx = _make_ctx()

    events = []
    async for event in step._run_async_impl(ctx):
        events.append(event)

    assert len(events) == 2
    assert "No response" in events[1].content.parts[0].text
    assert isess.input_requested is False
