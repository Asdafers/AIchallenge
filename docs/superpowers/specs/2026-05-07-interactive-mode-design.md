# Interactive Mode — Human-in-the-Loop Interview

## Problem

The current Methodic demo is a spectator experience: the user clicks "Start Demo" and watches a pre-configured autonomous pipeline run. The simulated participant (`participant_sim_agent`) generates fake answers, so the conversation is scripted and the extracted insights are predetermined. A judge or evaluator cannot experience the adaptive interview firsthand — they can only watch.

## Goal

Add an interactive mode where a real human replaces the simulated participant and has a live conversation with the Gemini-powered interviewer agent. The human types real answers, the system probes vague responses in real-time, and the extraction pipeline pulls structured insights from the human's actual words. The planning phase runs autonomously; only the interview is interactive.

## Target Users

- Competition judges evaluating the system live
- The builder (Wiktor) demonstrating the system in person
- Anyone who wants to experience what an AI-powered adaptive research interview feels like

NOT a general-purpose product for B2B research customers (that would require custom study configuration, participant recruitment, access control, etc.).

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Target user | Builder + judges | Keeps scope manageable; presets eliminate configuration complexity |
| Study configuration | Presets + advanced toggle | Instant start for demos, customizable for testing |
| Conversation feel | Split experience | Pure chat (no in-chat UI chrome) + live extraction sidebar |
| Post-interview | Results card + download | Proves the system produces real structured data; no BigQuery/quality wait |
| Technical approach | HumanInputStep with asyncio.Event | Minimal change to agent graph; SSE model unchanged |

## Architecture

Two modes sharing 95% of the same agent code:

- **Demo mode** (`/api/stream`) — current behavior, `participant_sim_agent` in the loop, fully autonomous
- **Interactive mode** (`/api/interactive/start` + `/api/interactive/{session_id}/respond`) — `HumanInputStep` replaces `participant_sim_agent`, blocks on human input each turn

### Agent Graph (Interactive)

```
root_agent (SequentialAgent)
  ├── study_planner (SequentialAgent)        ← autonomous
  │     ├── organizer (LlmAgent)
  │     ├── methodology (LlmAgent)
  │     └── question_design (LlmAgent)
  │
  ├── fieldwork_loop (LoopAgent, max_iterations=1)   ← single participant
  │     ├── session_runner (SequentialAgent)
  │     │     ├── session_init (BaseAgent)
  │     │     └── interview_loop (LoopAgent, max_iterations=6)
  │     │           ├── interviewer (LlmAgent + MCP tools)
  │     │           ├── HumanInputStep (BaseAgent)    ← NEW, replaces participant_sim
  │     │           ├── extractor_step (BaseAgent)
  │     │           └── turn_checker (BaseAgent)
  │     ├── coverage_step (BaseAgent)
  │     └── replanner (BaseAgent)               ← will STOP (single participant)
  │
  └── finalize (SequentialAgent)
        └── completion_responder (LlmAgent)     ← trimmed: no quality/BigQuery
```

### Factory Function

`methodic/agent.py` gets a factory function:

```python
def build_agent_graph(interactive: bool = False, session_registry: dict | None = None):
    if interactive:
        participant_agent = HumanInputStep(name="participant", session_registry=session_registry)
        fieldwork_max = 1  # single human participant
    else:
        participant_agent = participant_sim_agent
        fieldwork_max = 3

    interview_loop = LoopAgent(
        name="interview_loop",
        max_iterations=6,
        sub_agents=[interviewer_agent, participant_agent, ExtractorStep(...), TurnCheckerStep(...)],
    )
    # ... rest of graph with fieldwork_max
```

The existing `root_agent` module-level variable remains for demo mode and ADK Dev UI compatibility.

## Backend

### HumanInputStep (BaseAgent)

The core mechanism. Replaces `participant_sim_agent` in the interview loop.

```python
class HumanInputStep(BaseAgent):
    def __init__(self, name: str, session_registry: dict):
        super().__init__(name=name)
        self.session_registry = session_registry

    async def _run_async_impl(self, ctx):
        session_id = ctx.session.id
        reg = self.session_registry[session_id]

        # Signal frontend: enable text input
        yield Event(
            author=self.name,
            content=Content(parts=[Part(text="awaiting_input")]),
            actions=EventActions(state_delta={"input_requested": True}),
        )

        # Block until human responds or timeout
        try:
            await asyncio.wait_for(reg["event"].wait(), timeout=300)
        except asyncio.TimeoutError:
            reg["message"] = "No response provided."

        human_text = reg["message"]
        reg["event"].clear()

        # Write to state — same key participant_sim used
        yield Event(
            author="participant",
            content=Content(parts=[Part(text=human_text)]),
            actions=EventActions(
                state_delta={
                    "latest_participant_turn": human_text,
                    "input_requested": False,
                },
            ),
        )
```

### New Endpoints

**`POST /api/interactive/start`**

Accepts: `{ "preset": "lost_deals" }` or `{ "topic": "...", "persona": "..." }`

1. Creates session registry entry with `asyncio.Event` + message slot
2. Builds interactive agent graph via `build_agent_graph(interactive=True, session_registry=...)`
3. Starts `runner.run_async()` as a background task, feeding SSE events to a queue
4. Returns `{ "session_id": "...", "stream_url": "/api/interactive/{session_id}/stream" }`

**`GET /api/interactive/{session_id}/stream`**

SSE stream. Same event format as `/api/stream`:
```json
{"author": "interviewer", "text": "...", "state_delta": {...}}
{"author": "participant", "text": "awaiting_input", "state_delta": {"input_requested": true}}
```

**`POST /api/interactive/{session_id}/respond`**

Accepts: `{ "message": "the user's text" }`

1. Looks up session registry
2. Sets `reg["message"]` and triggers `reg["event"].set()`
3. Returns `{ "status": "ok" }`

**`GET /api/interactive/{session_id}/status`**

Returns: `{ "session_id": "...", "status": "planning|interviewing|complete|expired", "input_requested": true|false }`

Used for SSE reconnection — frontend checks if input is still requested after a dropped connection.

**`GET /api/interactive/{session_id}/results`**

Returns the `ParticipantResponse` JSON for the completed session. Used by the "Download JSON" button.

### Study Presets

```python
PRESETS = {
    "lost_deals": {
        "title": "Q1 2026 Lost Deal Analysis",
        "brief": "Run a win-loss study on recent Q1 2026 lost deals. "
                 "Focus on understanding why deals were lost, especially "
                 "around ROI clarity and procurement friction. "
                 "Participant: P-INTERACTIVE.",
        "persona_hint": "You are a VP of Engineering who evaluated our B2B analytics "
                        "platform but chose a competitor. You liked the product but "
                        "struggled to justify the per-seat cost internally.",
    },
    "churn": {
        "title": "Enterprise Churn Analysis",
        "brief": "Investigate why enterprise customers are not renewing. "
                 "Focus on security concerns, competitor pressure, and ROI. "
                 "Participant: P-INTERACTIVE.",
        "persona_hint": "You are a CTO who decided not to renew after 2 years. "
                        "The product worked but your team found a cheaper alternative "
                        "that covered 80% of the use cases.",
    },
    "competitive": {
        "title": "Competitive Displacement Study",
        "brief": "Understand why customers are switching to competitors. "
                 "Focus on feature gaps, pricing models, and support quality. "
                 "Participant: P-INTERACTIVE.",
        "persona_hint": "You are a Head of IT who switched from our product to a rival "
                        "after a procurement review flagged integration concerns.",
    },
}
```

The `persona_hint` is shown to the human on the configuration screen so they know what role to play. It is NOT passed to the interviewer agent — the interviewer should not know the "right" answers.

### Session Registry

```python
@dataclass
class InteractiveSession:
    session_id: str              # external ID used in URLs
    adk_session_id: str          # ADK session ID (used by HumanInputStep via ctx.session.id)
    event: asyncio.Event
    message: str = ""
    status: str = "planning"    # planning → interviewing → complete → expired
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

# Keyed by adk_session_id (what HumanInputStep sees via ctx.session.id)
_interactive_sessions: dict[str, InteractiveSession] = {}
# Reverse lookup: external session_id → adk_session_id
_session_lookup: dict[str, str] = {}
```

In-memory only. Sessions older than 30 minutes are cleaned up by a periodic background task. Endpoints use `_session_lookup` to translate the URL session ID to the ADK session ID for registry access.

## Frontend

### File

`methodic/static/interactive.html` — a separate page from `demo.html`.

### Three States

**State 1: Configuration**
- 3 preset scenario cards — click to select (highlight border)
- Collapsible "Advanced Configuration" with custom topic + persona text inputs
- Persona hint text shown below the selected preset so the user knows what role to play
- "Start Interview" button → POST `/api/interactive/start` → opens SSE stream → transitions to State 2

**State 2: Live Interview**
- Same layout as demo.html: chat panel (left) + insights sidebar (right) + coverage footer (bottom)
- Chat panel shows agent bubbles (left, blue) and human bubbles (right, purple)
- Text input + Send button at bottom of chat panel
- Input is **disabled** by default; **enabled** when SSE delivers `input_requested: true`
- Send button POSTs to `/api/interactive/{session_id}/respond`, then disables input
- PROBE badges, insight cards, phase progress — same rendering logic as demo.html
- Typing indicator shows while interviewer is generating next question
- Turn counter in header updates via SSE state_delta

**State 3: Results Card**
- Centered overlay card replacing the chat area
- Coverage stats grid: fields covered, high confidence count, low confidence count, turns taken
- Each extracted field shown as a card with: field name, confidence badge, extracted value, evidence quote from the human's actual words
- "Download JSON" button — fetches `/api/interactive/{session_id}/results` and triggers file download
- "Start New Interview" button — resets to State 1

### Shared Code

The insights sidebar, phase progress, coverage footer, and chat bubble rendering logic are identical to `demo.html`. These can be extracted to shared functions or simply duplicated (the file is self-contained, no build step). Given the single-file constraint, duplication is acceptable — the interactive page is a distinct product surface, not a mode toggle on the demo.

### SSE Consumption

Same `consumeSSE` pattern as demo.html with one addition: when an event contains `state_delta.input_requested === true`, enable the text input and focus it. When `input_requested === false`, disable the input.

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Human doesn't respond within 5 minutes | `HumanInputStep` writes timeout message, turn proceeds, interview may end early |
| Gemini API error during interviewer turn | SSE emits error event, frontend shows error banner, session marked failed |
| SSE connection drops | Frontend reconnects, checks `/status` endpoint, re-enables input if still requested |
| User closes browser | Session times out after 30 minutes, cleaned up by background sweep |
| Invalid/empty message sent | Server returns 400, frontend shows validation hint |

## What This Does NOT Include

- No persistent session storage (in-memory only)
- No multi-participant interactive mode (human is always participant 1 of 1)
- No saving/resuming interrupted interviews
- No authentication or user accounts
- No WebSocket — SSE + POST is sufficient
- No changes to the demo mode (`/api/stream` and `demo.html` remain unchanged)
- No quality review or BigQuery export in interactive mode
- MCP tools remain on the interviewer agent (reused from demo mode) but preset briefs don't reference specific deal context, so MCP calls are unlikely to fire

## Files to Create or Modify

| File | Action | Purpose |
|------|--------|---------|
| `methodic/agents/human_input_step.py` | Create | `HumanInputStep(BaseAgent)` |
| `methodic/agent.py` | Modify | Add `build_agent_graph(interactive=False)` factory |
| `methodic/server.py` | Modify | Add 4 interactive endpoints + session registry |
| `methodic/static/interactive.html` | Create | Interactive mode UI |
| `methodic/presets.py` | Create | Study preset configurations |
| `tests/test_human_input_step.py` | Create | Unit tests for HumanInputStep |
| `tests/test_interactive_api.py` | Create | Integration tests for interactive endpoints |

## Success Criteria

A judge opens the interactive page, clicks "Lost Deal Analysis", waits 15 seconds for planning, then has a 5-turn conversation with the Gemini interviewer. During the conversation:

1. The interviewer asks relevant, adaptive follow-up questions
2. When the judge gives a vague answer, the interviewer probes with a PROBE-badged question
3. The sidebar shows fields turning from grey to green as insights are extracted from the judge's words
4. After the final turn, a results card shows the structured data with evidence quotes from the judge's own responses
5. The judge can download the JSON and see their freeform conversation transformed into structured research data
