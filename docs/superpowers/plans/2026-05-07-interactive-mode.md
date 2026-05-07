# Interactive Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a human-in-the-loop interview mode where a real person replaces the simulated participant and converses live with the Gemini interviewer agent.

**Architecture:** A `HumanInputStep(BaseAgent)` replaces `participant_sim_agent` in the interview loop, blocking on `asyncio.Queue.get()` until the human responds via a POST endpoint. The agent graph is built by a factory function that swaps the participant agent based on mode. Module-level demo exports (`root_agent`, `study_planner`, etc.) are preserved. A new `interactive.html` frontend provides configuration → live chat → results card.

**Tech Stack:** Python 3.11, Google ADK 1.32, FastAPI, SSE (text/event-stream), vanilla JS/CSS/HTML

**Design doc:** `docs/superpowers/specs/2026-05-07-interactive-mode-design.md`

**Review feedback incorporated (Gemini + Codex):**
- Use `asyncio.Queue` for human message delivery instead of single string slot (race condition fix)
- Track `input_requested` as a separate bool on `InteractiveSession`, not via `event.is_set()`
- Pass `InteractiveSession` directly to `HumanInputStep` (remove `RegistryProxy`)
- Preserve module-level exports in `methodic/agent.py` for existing test compatibility
- Add terminal error events to SSE stream so frontend doesn't hang
- Deploy with `--max-instances=1` (in-memory session registry requires single instance)
- Add session cleanup background task
- Use consistent status vocabulary: `planning|interviewing|complete|failed|expired`
- Reject `/respond` when no input is currently requested (409 Conflict)

---

### Task 1: Study Presets

**Files:**
- Create: `methodic/presets.py`
- Test: `tests/test_presets.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_presets.py
from methodic.presets import PRESETS, get_preset

def test_presets_has_three_entries():
    assert len(PRESETS) == 3
    assert "lost_deals" in PRESETS
    assert "churn" in PRESETS
    assert "competitive" in PRESETS

def test_preset_has_required_keys():
    for key, preset in PRESETS.items():
        assert "title" in preset
        assert "brief" in preset
        assert "persona_hint" in preset
        assert len(preset["brief"]) > 20

def test_get_preset_returns_preset():
    p = get_preset("lost_deals")
    assert p["title"] == "Q1 2026 Lost Deal Analysis"

def test_get_preset_returns_none_for_unknown():
    assert get_preset("nonexistent") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/test_presets.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'methodic.presets'`

- [ ] **Step 3: Write the implementation**

```python
# methodic/presets.py
"""Study preset configurations for interactive mode."""

from __future__ import annotations

PRESETS: dict[str, dict[str, str]] = {
    "lost_deals": {
        "title": "Q1 2026 Lost Deal Analysis",
        "brief": (
            "Run a win-loss study on recent Q1 2026 lost deals. "
            "Focus on understanding why deals were lost, especially "
            "around ROI clarity and procurement friction. "
            "Participant: P-INTERACTIVE."
        ),
        "persona_hint": (
            "You are a VP of Engineering who evaluated our B2B analytics "
            "platform but chose a competitor. You liked the product but "
            "struggled to justify the per-seat cost internally."
        ),
    },
    "churn": {
        "title": "Enterprise Churn Analysis",
        "brief": (
            "Investigate why enterprise customers are not renewing. "
            "Focus on security concerns, competitor pressure, and ROI. "
            "Participant: P-INTERACTIVE."
        ),
        "persona_hint": (
            "You are a CTO who decided not to renew after 2 years. "
            "The product worked but your team found a cheaper alternative "
            "that covered 80% of the use cases."
        ),
    },
    "competitive": {
        "title": "Competitive Displacement Study",
        "brief": (
            "Understand why customers are switching to competitors. "
            "Focus on feature gaps, pricing models, and support quality. "
            "Participant: P-INTERACTIVE."
        ),
        "persona_hint": (
            "You are a Head of IT who switched from our product to a rival "
            "after a procurement review flagged integration concerns."
        ),
    },
}


def get_preset(name: str) -> dict[str, str] | None:
    return PRESETS.get(name)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/test_presets.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add methodic/presets.py tests/test_presets.py
git commit -m "feat: add study preset configurations for interactive mode"
```

---

### Task 2: HumanInputStep (BaseAgent)

**Files:**
- Create: `methodic/agents/human_input_step.py`
- Test: `tests/test_human_input_step.py`

- [ ] **Step 1: Write the tests**

```python
# tests/test_human_input_step.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/test_human_input_step.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'methodic.agents.human_input_step'`

- [ ] **Step 3: Write the implementation**

```python
# methodic/agents/human_input_step.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/test_human_input_step.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add methodic/agents/human_input_step.py tests/test_human_input_step.py
git commit -m "feat: add HumanInputStep BaseAgent for interactive interview loop"
```

---

### Task 3: Agent Graph Factory

**Files:**
- Modify: `methodic/agent.py`
- Test: `tests/test_agent_factory.py`

- [ ] **Step 1: Write the tests**

```python
# tests/test_agent_factory.py
"""Tests for agent graph factory function."""

from methodic.agent import build_agent_graph, root_agent
from methodic.agents.human_input_step import HumanInputStep


def test_root_agent_still_exists():
    """Module-level root_agent must remain for ADK Dev UI compatibility."""
    assert root_agent is not None
    assert root_agent.name == "methodic"


def test_module_level_exports_preserved():
    """Existing code imports these names from methodic.agent."""
    from methodic.agent import study_planner, fieldwork_loop, finalize, interview_loop
    assert study_planner is not None
    assert fieldwork_loop is not None
    assert finalize is not None
    assert interview_loop is not None


def test_build_demo_mode():
    graph = build_agent_graph(interactive=False)
    assert graph.name == "methodic"
    # Find interview_loop and check for participant_sim
    fw = graph.sub_agents[1]  # fieldwork_loop
    sr = fw.sub_agents[0]
    il = sr.sub_agents[1]
    participant = il.sub_agents[1]
    assert participant.name == "participant_sim"


def test_build_interactive_mode():
    registry = {}
    graph = build_agent_graph(interactive=True, session_registry=registry)
    assert graph.name == "methodic_interactive"
    # Find interview_loop and check for HumanInputStep
    fw = graph.sub_agents[1]
    sr = fw.sub_agents[0]
    il = sr.sub_agents[1]
    participant = il.sub_agents[1]
    assert isinstance(participant, HumanInputStep)
    # Fieldwork max_iterations should be 1 for single participant
    assert fw.max_iterations == 1


def test_interactive_mode_skips_quality_and_export():
    registry = {}
    graph = build_agent_graph(interactive=True, session_registry=registry)
    fin = graph.sub_agents[2]
    agent_names = [a.name for a in fin.sub_agents]
    assert "quality_reviewer" not in agent_names
    assert "bigquery_export" not in agent_names
    assert "completion_responder" in agent_names
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/test_agent_factory.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_agent_graph' from 'methodic.agent'`

- [ ] **Step 3: Modify methodic/agent.py**

Replace the entire file with:

```python
# methodic/agent.py
"""Root agent definition - ADK entry point.

Agent graph (all sub_agents are agent instances, never raw FunctionTools):

root_agent (SequentialAgent)
  +-- study_planner (SequentialAgent)
  |     +-- organizer (LlmAgent)
  |     +-- methodology (LlmAgent)
  |     +-- question_design (LlmAgent)
  |
  +-- fieldwork_loop (LoopAgent, max_iterations=3)
  |     +-- session_runner (SequentialAgent)
  |     |     +-- session_init (custom BaseAgent, resets turn_count)
  |     |     +-- interview_loop (LoopAgent, max_iterations=6)
  |     |           +-- interviewer (LlmAgent + MCP tools)
  |     |           +-- participant_sim (LlmAgent) OR HumanInputStep (interactive)
  |     |           +-- extractor_step (custom BaseAgent, assembles transcript)
  |     |           +-- turn_checker (custom BaseAgent, escalates inner loop)
  |     +-- coverage_step (custom BaseAgent)
  |     +-- replanner (custom BaseAgent, escalates outer loop on STOP)
  |
  +-- finalize (SequentialAgent)
        +-- quality_reviewer (LlmAgent)       [demo only]
        +-- bigquery_export (custom BaseAgent) [demo only]
        +-- completion_responder (LlmAgent)
"""

from __future__ import annotations

from google.adk.agents import LoopAgent
from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent

from methodic import MODEL
from methodic.agents.organizer import organizer_agent
from methodic.agents.methodology import methodology_agent
from methodic.agents.question_design import question_design_agent
from methodic.agents.participant import interviewer_agent
from methodic.agents.participant_sim import participant_sim_agent
from methodic.agents.quality import quality_agent
from methodic.agents.replanner import replanner_agent
from methodic.agents.extractor_step import ExtractorStep
from methodic.agents.turn_checker_step import TurnCheckerStep
from methodic.agents.coverage_step import CoverageStep
from methodic.agents.bigquery_export_step import BigQueryExportStep
from methodic.agents.session_init_step import SessionInitStep


def build_agent_graph(
    interactive: bool = False,
    session_registry: dict | None = None,
) -> SequentialAgent:
    if interactive:
        from methodic.agents.human_input_step import HumanInputStep
        participant_agent = HumanInputStep(
            name="participant", session_registry=session_registry or {},
        )
        fieldwork_max = 1
    else:
        participant_agent = participant_sim_agent
        fieldwork_max = 3

    study_planner = SequentialAgent(
        name="study_planner",
        sub_agents=[organizer_agent, methodology_agent, question_design_agent],
    )

    interview_loop = LoopAgent(
        name="interview_loop",
        max_iterations=6,
        sub_agents=[
            interviewer_agent,
            participant_agent,
            ExtractorStep(name="extractor_step"),
            TurnCheckerStep(name="turn_checker", max_turns=6),
        ],
    )

    session_runner = SequentialAgent(
        name="session_runner",
        sub_agents=[SessionInitStep(name="session_init"), interview_loop],
    )

    fieldwork_loop = LoopAgent(
        name="fieldwork_loop",
        max_iterations=fieldwork_max,
        sub_agents=[
            session_runner,
            CoverageStep(name="coverage_step"),
            replanner_agent,
        ],
    )

    if interactive:
        completion = Agent(
            name="completion_responder",
            model=MODEL,
            instruction=(
                "Summarize the study results. Include key findings, "
                "coverage achieved, and themes discovered."
            ),
        )
        finalize = SequentialAgent(
            name="finalize",
            sub_agents=[completion],
        )
        root_name = "methodic_interactive"
    else:
        completion = Agent(
            name="completion_responder",
            model=MODEL,
            instruction=(
                "Summarize the study results. Include key findings, "
                "coverage achieved, themes, and BigQuery export status."
            ),
        )
        finalize = SequentialAgent(
            name="finalize",
            sub_agents=[quality_agent, BigQueryExportStep(name="bigquery_export"), completion],
        )
        root_name = "methodic"

    return SequentialAgent(
        name=root_name,
        sub_agents=[study_planner, fieldwork_loop, finalize],
    )


# Module-level exports for ADK Dev UI, demo mode, and existing test compatibility.
root_agent = build_agent_graph(interactive=False)
study_planner = root_agent.sub_agents[0]
fieldwork_loop = root_agent.sub_agents[1]
interview_loop = fieldwork_loop.sub_agents[0].sub_agents[1]
finalize = root_agent.sub_agents[2]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/test_agent_factory.py -v`
Expected: 4 passed

- [ ] **Step 5: Run existing tests to verify no regressions**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/ -v --ignore=tests/e2e -k "not live" 2>&1 | tail -15`
Expected: All existing tests still pass (the module-level `root_agent` is still present).

- [ ] **Step 6: Commit**

```bash
git add methodic/agent.py tests/test_agent_factory.py
git commit -m "feat: add build_agent_graph factory for interactive/demo mode switching"
```

---

### Task 4: Interactive API Endpoints

**Files:**
- Modify: `methodic/server.py`
- Test: `tests/test_interactive_api.py`

- [ ] **Step 1: Write the tests**

```python
# tests/test_interactive_api.py
"""Tests for interactive mode API endpoints."""

import asyncio
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from methodic.server import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_interactive_start_with_preset(client):
    with patch("methodic.server._start_interactive_pipeline", new_callable=AsyncMock):
        response = client.post(
            "/api/interactive/start",
            json={"preset": "lost_deals"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "stream_url" in data
    assert data["stream_url"].startswith("/api/interactive/")


def test_interactive_start_with_custom(client):
    with patch("methodic.server._start_interactive_pipeline", new_callable=AsyncMock):
        response = client.post(
            "/api/interactive/start",
            json={"topic": "Custom study", "persona": "Custom persona"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data


def test_interactive_start_invalid(client):
    response = client.post(
        "/api/interactive/start",
        json={},
    )
    assert response.status_code == 400


def test_interactive_respond_unknown_session(client):
    response = client.post(
        "/api/interactive/unknown-id/respond",
        json={"message": "Hello"},
    )
    assert response.status_code == 404


def test_interactive_respond_empty_message(client):
    response = client.post(
        "/api/interactive/unknown-id/respond",
        json={"message": ""},
    )
    assert response.status_code == 400


def test_interactive_status_unknown_session(client):
    response = client.get("/api/interactive/unknown-id/status")
    assert response.status_code == 404


def test_interactive_results_unknown_session(client):
    response = client.get("/api/interactive/unknown-id/results")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/test_interactive_api.py -v`
Expected: FAIL (endpoints don't exist yet)

- [ ] **Step 3: Modify methodic/server.py**

Add the following imports at the top of the file (after existing imports):

```python
import time
import asyncio
from dataclasses import dataclass, field
```

Add the `InteractiveSession` dataclass and session registries after the `_demo_sessions` line:

```python
@dataclass
class InteractiveSession:
    session_id: str
    adk_session_id: str
    input_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    input_requested: bool = False
    status: str = "planning"
    sse_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    results: dict | None = None

_interactive_sessions: dict[str, InteractiveSession] = {}
_session_lookup: dict[str, str] = {}
```

Add the interactive endpoints inside `create_app()`, after the existing endpoints and before `return app`:

```python
    @app.post("/api/interactive/start")
    async def interactive_start(request: Request):
        body = await request.json()
        preset_name = body.get("preset")
        topic = body.get("topic")

        if not preset_name and not topic:
            return JSONResponse(status_code=400, content={"error": "preset or topic required"})

        from methodic.presets import get_preset, PRESETS

        if preset_name:
            preset = get_preset(preset_name)
            if not preset:
                return JSONResponse(status_code=400, content={"error": f"Unknown preset: {preset_name}"})
            brief_text = preset["brief"]
            title = preset["title"]
            persona_hint = preset["persona_hint"]
        else:
            persona = body.get("persona", "A B2B decision-maker.")
            brief_text = f"{topic} Participant: P-INTERACTIVE."
            title = topic[:60]
            persona_hint = persona

        session_id = f"INT-{uuid.uuid4().hex[:8]}"

        from google.adk.sessions import InMemorySessionService
        session_service = InMemorySessionService()
        adk_session = await session_service.create_session(
            app_name="methodic_interactive",
            user_id="interactive_user",
        )

        adk_sid = adk_session.id
        isess = InteractiveSession(
            session_id=session_id,
            adk_session_id=adk_sid,
        )
        _interactive_sessions[adk_sid] = isess
        _session_lookup[session_id] = adk_sid

        asyncio.create_task(
            _start_interactive_pipeline(
                isess, session_service, brief_text, adk_sid
            )
        )

        return {
            "session_id": session_id,
            "stream_url": f"/api/interactive/{session_id}/stream",
            "title": title,
            "persona_hint": persona_hint,
        }

    @app.get("/api/interactive/{session_id}/stream")
    async def interactive_stream(session_id: str):
        adk_sid = _session_lookup.get(session_id)
        if not adk_sid:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        isess = _interactive_sessions.get(adk_sid)
        if not isess:
            return JSONResponse(status_code=404, content={"error": "Session not found"})

        async def event_generator():
            while True:
                try:
                    payload = await asyncio.wait_for(isess.sse_queue.get(), timeout=600)
                except asyncio.TimeoutError:
                    break
                yield f"data: {json.dumps(payload)}\n\n"
                author = payload.get("author", "")
                if author == "error":
                    break
                if author == "system" and "complete" in payload.get("text", "").lower():
                    break

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.post("/api/interactive/{session_id}/respond")
    async def interactive_respond(session_id: str, request: Request):
        body = await request.json()
        message = body.get("message", "")
        if not message:
            return JSONResponse(status_code=400, content={"error": "message required"})

        adk_sid = _session_lookup.get(session_id)
        if not adk_sid:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        isess = _interactive_sessions.get(adk_sid)
        if not isess:
            return JSONResponse(status_code=404, content={"error": "Session not found"})

        if not isess.input_requested:
            return JSONResponse(status_code=409, content={"error": "Not awaiting input"})

        isess.last_activity = time.time()
        await isess.input_queue.put(message)
        return {"status": "ok"}

    @app.get("/api/interactive/{session_id}/status")
    async def interactive_status(session_id: str):
        adk_sid = _session_lookup.get(session_id)
        if not adk_sid:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        isess = _interactive_sessions.get(adk_sid)
        if not isess:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        return {
            "session_id": session_id,
            "status": isess.status,
            "input_requested": isess.input_requested,
        }

    @app.get("/api/interactive/{session_id}/results")
    async def interactive_results(session_id: str):
        adk_sid = _session_lookup.get(session_id)
        if not adk_sid:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        isess = _interactive_sessions.get(adk_sid)
        if not isess:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        if isess.results is None:
            return JSONResponse(status_code=404, content={"error": "Results not yet available"})
        return isess.results
```

Add the `_start_interactive_pipeline` function outside of `create_app()`, before the `app = create_app()` line:

```python
async def _start_interactive_pipeline(
    isess: InteractiveSession,
    session_service,
    brief_text: str,
    adk_session_id: str,
) -> None:
    try:
        from methodic.agent import build_agent_graph
        from google.adk.runners import Runner
        from google.genai import types

        registry = {adk_session_id: isess}

        agent = build_agent_graph(interactive=True, session_registry=registry)
        runner = Runner(
            agent=agent,
            app_name="methodic_interactive",
            session_service=session_service,
        )
        user_message = types.Content(
            role="user",
            parts=[types.Part(text=brief_text)],
        )

        isess.status = "running"

        async for event in runner.run_async(
            session_id=adk_session_id,
            user_id="interactive_user",
            new_message=user_message,
        ):
            author = getattr(event, "author", None)
            if not author:
                continue

            text_parts = []
            content = getattr(event, "content", None)
            for part in getattr(content, "parts", []) or []:
                t = getattr(part, "text", None)
                if t:
                    text_parts.append(t)

            actions = getattr(event, "actions", None)
            state_delta = {}
            if actions:
                raw_delta = getattr(actions, "state_delta", None) or {}
                if isinstance(raw_delta, dict):
                    state_delta = raw_delta

            payload = {
                "author": author,
                "text": " ".join(text_parts),
                "state_delta": state_delta,
            }
            await isess.sse_queue.put(payload)

            if author == "participant" and state_delta.get("input_requested"):
                isess.status = "interviewing"

        # Collect results from session state
        final_session = await session_service.get_session(
            app_name="methodic_interactive",
            user_id="interactive_user",
            session_id=adk_session_id,
        )
        if final_session and hasattr(final_session, "state"):
            responses = final_session.state.get("participant_response_by_id", {})
            coverage = final_session.state.get("coverage_state", {})
            isess.results = {
                "participant_responses": responses,
                "coverage_state": coverage,
            }

        isess.status = "complete"
        await isess.sse_queue.put({
            "author": "system",
            "text": "Stream complete.",
            "state_delta": {},
        })

    except Exception as e:
        isess.status = "failed"
        await isess.sse_queue.put({
            "author": "error",
            "text": str(e),
            "state_delta": {},
        })
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/test_interactive_api.py -v`
Expected: 7 passed

- [ ] **Step 5: Run existing tests to verify no regressions**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/ -v --ignore=tests/e2e -k "not live" 2>&1 | tail -15`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add methodic/server.py tests/test_interactive_api.py
git commit -m "feat: add interactive mode API endpoints with session management"
```

---

### Task 5: Interactive Frontend — HTML Skeleton + Configuration (State 1)

**Files:**
- Create: `methodic/static/interactive.html`

This task creates the full HTML file with CSS, the configuration state, and stub functions for States 2 and 3.

- [ ] **Step 1: Create the interactive.html file**

Create `methodic/static/interactive.html` with the full HTML skeleton. The file structure mirrors `demo.html`: single-file with `<style>` and `<script>` blocks, no dependencies.

The HTML structure:
- `#config-screen` — configuration state with preset cards and advanced toggle
- `#app` — main app container (hidden until interview starts), same layout as demo.html
  - `header` — title, phase label, turn counter, status badge
  - `main > .content-area` — grid with chat panel (left) and sidebar (right)
    - `#chat-panel` with `role="log"` and `aria-live="polite"`, messages area, text input + send button, typing indicator
    - `#sidebar` with insights panel, agentic moments, phase progress
  - `#coverage-footer` with progress bar, coverage text, turn text
- `#results-overlay` — results card (hidden until interview completes)

CSS: Reuse the same color palette and layout rules as `demo.html`. Key additions:
- Config screen styling (preset cards, advanced toggle)
- Active text input styling (blue border when enabled, grey when disabled)
- Results card styling (stats grid, field cards with confidence badges)

JavaScript: State reducer pattern matching `demo.html`, with additions:
- `sessionId` tracking
- `startInterview()` — POSTs to `/api/interactive/start`, opens SSE stream
- `sendMessage()` — POSTs to `/api/interactive/{sessionId}/respond`
- `handleEvent()` — same routing as demo, plus `input_requested` handling
- `showResults()` — builds results card from final state
- `downloadResults()` — fetches `/api/interactive/{sessionId}/results`, triggers download

The text input is disabled by default. When SSE delivers `state_delta.input_requested === true`, enable the input and focus it. When `input_requested === false`, disable it and show the typing indicator.

Important: Use `textContent` for all user-visible text rendering. Use safe DOM construction (createElement/appendChild) instead of innerHTML for dynamic content.

Due to the size of this file (~1200 lines), the implementer should build it by referencing `demo.html` for the chat/sidebar/coverage rendering code and adapting it. The key differences from `demo.html` are:

1. Config screen replaces intro overlay
2. Text input + Send button at bottom of chat panel
3. `input_requested` state handling (enable/disable input)
4. Results overlay with field-level detail (not just coverage stats)
5. Download JSON button
6. No "Run Demo" button in footer — the flow starts from config
7. `CHAT_AUTHORS` maps `participant` to `participant` (not `participant_sim`)

- [ ] **Step 2: Verify the skeleton renders**

Open `methodic/static/interactive.html` in browser or via the dev server. Expected: Configuration screen with 3 preset cards visible, advanced toggle works, Start Interview button present.

- [ ] **Step 3: Commit**

```bash
git add methodic/static/interactive.html
git commit -m "feat: interactive mode frontend with config, chat, and results states"
```

---

### Task 6: Interactive Frontend — Live Interview (State 2) + Results (State 3)

**Files:**
- Modify: `methodic/static/interactive.html`

This task wires the SSE consumption, message sending, and results rendering.

- [ ] **Step 1: Wire SSE consumption and message sending**

Implement `startInterview()`:
1. Read selected preset or custom fields
2. POST to `/api/interactive/start` with `{preset: name}` or `{topic, persona}`
3. Store `sessionId` and `personaHint` from response
4. Hide config screen, show app
5. Show persona hint as a system message in chat
6. Open SSE stream from `stream_url`
7. Call `consumeSSE()` to process events

Implement `consumeSSE(response)`:
- Same streaming pattern as `demo.html` (fetch with getReader, buffer partial lines, parse `data:` prefixed JSON)
- Call `handleEvent()` for each parsed event
- On stream end: call `showResults()`

Implement `handleEvent(evt)`:
- Same event routing as `demo.html`: chat bubbles, insights, phases, coverage
- Additional: when `state_delta.input_requested === true`, enable text input, focus it, hide typing indicator
- When `state_delta.input_requested === false`, disable text input, show typing indicator

Implement `sendMessage()`:
1. Read text input value, trim
2. If empty, return
3. Disable input and send button
4. Add human's message as a participant bubble immediately
5. POST to `/api/interactive/{sessionId}/respond` with `{message: text}`
6. Clear input, show typing indicator

Handle Enter key: `input.addEventListener('keydown', function(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } })`

- [ ] **Step 2: Wire results rendering**

Implement `showResults()`:
1. Count coverage states from `state.coverage` (high_confidence, low_confidence, ambiguous, missing)
2. Build results card using createElement:
   - Title: "Interview Complete"
   - Stats grid: 4 cards (Fields Covered, High Confidence, Needs Clarification, Turns Taken)
   - Field detail cards: for each of the 8 canonical fields, show field name, coverage state badge, extracted value (from `state.participantResponses` if available)
3. Add "Download JSON" button → calls `downloadResults()`
4. Add "Start New Interview" button → resets to config screen
5. Show results overlay

Implement `downloadResults()`:
1. Fetch `/api/interactive/{sessionId}/results`
2. Create blob URL from JSON response
3. Create invisible `<a>` element with `download` attribute
4. Click and remove

- [ ] **Step 3: Test the full flow manually**

Start the server and navigate to `/static/interactive.html`. Verify:
- Config screen renders with presets
- Clicking a preset and Start Interview transitions to the app
- Planning phase events appear in sidebar
- When interviewer speaks, a chat bubble appears
- When input is requested, text box lights up
- Typing a response and pressing Enter/Send delivers it
- Response appears as a participant bubble
- Insights update as extractor processes
- After final turn, results card appears

- [ ] **Step 4: Commit**

```bash
git add methodic/static/interactive.html
git commit -m "feat: wire interactive SSE consumption, message sending, and results card"
```

---

### Task 7: E2E Integration Test

**Files:**
- Create: `tests/test_interactive_e2e.py`

- [ ] **Step 1: Write a mock integration test**

```python
# tests/test_interactive_e2e.py
"""Integration test for interactive mode - mock Gemini, real endpoints."""

import asyncio
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from methodic.server import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_interactive_start_returns_stream_url(client):
    with patch("methodic.server._start_interactive_pipeline", new_callable=AsyncMock):
        resp = client.post("/api/interactive/start", json={"preset": "lost_deals"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "/stream" in data["stream_url"]
    assert data["title"] == "Q1 2026 Lost Deal Analysis"
    assert "VP of Engineering" in data["persona_hint"]


def test_interactive_respond_queues_message(client):
    """Test that POST /respond puts message on the input queue."""
    from methodic.server import _interactive_sessions, _session_lookup, InteractiveSession

    adk_sid = "fake-adk-session"
    session_id = "INT-test1234"
    isess = InteractiveSession(session_id=session_id, adk_session_id=adk_sid)
    isess.input_requested = True  # Must be awaiting input
    _interactive_sessions[adk_sid] = isess
    _session_lookup[session_id] = adk_sid

    try:
        resp = client.post(
            f"/api/interactive/{session_id}/respond",
            json={"message": "It was about price."},
        )
        assert resp.status_code == 200
        assert not isess.input_queue.empty()
    finally:
        _interactive_sessions.pop(adk_sid, None)
        _session_lookup.pop(session_id, None)


def test_interactive_respond_rejects_when_not_awaiting(client):
    """POST /respond should 409 when no input is requested."""
    from methodic.server import _interactive_sessions, _session_lookup, InteractiveSession

    adk_sid = "fake-adk-session-reject"
    session_id = "INT-reject"
    isess = InteractiveSession(session_id=session_id, adk_session_id=adk_sid)
    isess.input_requested = False
    _interactive_sessions[adk_sid] = isess
    _session_lookup[session_id] = adk_sid

    try:
        resp = client.post(
            f"/api/interactive/{session_id}/respond",
            json={"message": "Too early"},
        )
        assert resp.status_code == 409
    finally:
        _interactive_sessions.pop(adk_sid, None)
        _session_lookup.pop(session_id, None)


def test_interactive_status_returns_state(client):
    from methodic.server import _interactive_sessions, _session_lookup, InteractiveSession

    adk_sid = "fake-adk-session-2"
    session_id = "INT-test5678"
    isess = InteractiveSession(session_id=session_id, adk_session_id=adk_sid, status="interviewing")
    isess.input_requested = True
    _interactive_sessions[adk_sid] = isess
    _session_lookup[session_id] = adk_sid

    try:
        resp = client.get(f"/api/interactive/{session_id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "interviewing"
        assert data["input_requested"] is True
        assert data["session_id"] == session_id
    finally:
        _interactive_sessions.pop(adk_sid, None)
        _session_lookup.pop(session_id, None)
```

- [ ] **Step 2: Run tests**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/test_interactive_e2e.py -v`
Expected: 3 passed

- [ ] **Step 3: Run full test suite**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m pytest tests/ --ignore=tests/e2e -k "not live" --tb=short 2>&1 | tail -15`
Expected: All tests pass (existing + new)

- [ ] **Step 4: Commit**

```bash
git add tests/test_interactive_e2e.py
git commit -m "test: add interactive mode integration tests"
```

---

### Task 8: Deploy and Verify

**Files:**
- No code changes — deployment only

- [ ] **Step 1: Verify local interactive flow**

Run: `cd /Volumes/workz/GitHubProjects/AIchallenge && python3 -m uvicorn methodic.server:app --host 0.0.0.0 --port 8080`

Open `http://localhost:8080/static/interactive.html` in browser. Verify:
- Config screen loads
- Clicking preset highlights it
- Advanced toggle expands form
- Start Interview button is clickable

- [ ] **Step 2: Build and deploy to Cloud Run**

```bash
cd /Volumes/workz/GitHubProjects/AIchallenge
cp Dockerfile.cloudrun Dockerfile
gcloud builds submit --tag us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/methodic:v8 --project=methodic-ai-challenge
gcloud run deploy methodic \
  --image us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/methodic:v8 \
  --region us-central1 \
  --project=methodic-ai-challenge \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 600 \
  --max-instances=1
cp Dockerfile.bak Dockerfile 2>/dev/null; rm -f Dockerfile.bak
```

- [ ] **Step 3: Verify deployed interactive mode**

Open `https://methodic-2030382823.us-central1.run.app/static/interactive.html` in browser. Verify config screen loads and presets are visible.

- [ ] **Step 4: Commit any deployment fixes**

```bash
git add -A
git commit -m "chore: deploy interactive mode to Cloud Run v8"
```
