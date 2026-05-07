"""Custom FastAPI server - ADK web + demo API + A2A-compatible card.

A2A scope: prototype. Serves A2A 1.0-shaped Agent Card at
/.well-known/agent-card.json. Does NOT use to_a2a() (unproven
with get_fast_api_app composition). Upgrade path documented.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent / "static"

AGENT_CARD = {
    "name": "methodic",
    "description": (
        "Autonomous B2B win-loss research agent. Accepts study requests, "
        "conducts governed participant interviews, returns evidence-linked structured data."
    ),
    "version": "1.0.0",
    "url": "https://methodic.run.app",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "authentication": {"schemes": ["none"]},
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain", "application/json"],
    "skills": [{
        "id": "win_loss_study",
        "name": "Win-Loss Study",
        "description": "Conduct a B2B win-loss research study with methodology review, adaptive interviews, and BigQuery export",
        "tags": ["research", "b2b", "win-loss"],
    }],
}

_demo_sessions: dict[str, dict] = {}


def create_app() -> FastAPI:
    try:
        from google.adk.cli.fast_api import get_fast_api_app
        import os
        app = get_fast_api_app(
            agents_dir=str(Path(__file__).resolve().parent.parent),
            allow_origins=["*"],
            web=True,
            trace_to_cloud=os.environ.get("TRACE_TO_CLOUD", "").lower() in ("1", "true"),
        )
    except Exception:
        app = FastAPI(title="Methodic ADK Agent")

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/.well-known/agent-card.json")
    async def agent_card():
        return JSONResponse(content=AGENT_CARD)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/api/demo/run")
    async def run_demo():
        study_id = f"STUDY-{uuid.uuid4().hex[:8]}"
        _demo_sessions[study_id] = {
            "status": "running", "coverage": {}, "events": [],
        }
        from methodic.demo_runner import run_demo_pipeline
        asyncio.create_task(run_demo_pipeline(_demo_sessions, study_id))
        return {"study_id": study_id, "status": "running"}

    @app.get("/api/demo/{study_id}/coverage")
    async def get_coverage(study_id: str):
        session = _demo_sessions.get(study_id)
        if not session:
            return JSONResponse(status_code=404, content={"error": "Study not found"})
        return session.get("coverage", {})

    @app.get("/api/demo/{study_id}/events")
    async def get_events(study_id: str):
        session = _demo_sessions.get(study_id)
        if not session:
            return JSONResponse(status_code=404, content={"error": "Study not found"})
        return session.get("events", [])

    @app.get("/api/demo/{study_id}/status")
    async def get_status(study_id: str):
        session = _demo_sessions.get(study_id)
        if not session:
            return JSONResponse(status_code=404, content={"error": "Study not found"})
        return {"study_id": study_id, "status": session.get("status", "unknown")}

    @app.post("/api/stream")
    async def stream_study(request: Request):
        body = await request.json()
        brief_text = body.get("study_brief", body.get("message", ""))
        if isinstance(brief_text, dict):
            brief_text = json.dumps(brief_text)
        if not brief_text:
            return JSONResponse(status_code=400, content={"error": "study_brief or message required"})

        async def event_generator():
            from methodic.agent import root_agent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types

            session_service = InMemorySessionService()
            runner = Runner(
                agent=root_agent,
                app_name="methodic_demo",
                session_service=session_service,
            )
            adk_session = await session_service.create_session(
                app_name="methodic_demo",
                user_id="demo_stream",
            )
            user_message = types.Content(
                role="user",
                parts=[types.Part(text=brief_text)],
            )

            try:
                async for event in runner.run_async(
                    session_id=adk_session.id,
                    user_id="demo_stream",
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
                    yield f"data: {json.dumps(payload)}\n\n"

                yield f"data: {json.dumps({'author': 'system', 'text': 'Stream complete.', 'state_delta': {}})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'author': 'error', 'text': str(e), 'state_delta': {}})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return app


app = create_app()
