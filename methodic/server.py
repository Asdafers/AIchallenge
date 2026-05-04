"""Custom FastAPI server - ADK web + demo API + A2A-compatible card.

A2A scope: prototype. Serves A2A 1.0-shaped Agent Card at
/.well-known/agent-card.json. Does NOT use to_a2a() (unproven
with get_fast_api_app composition). Upgrade path documented.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
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
        app = get_fast_api_app(
            agents_dir=str(Path(__file__).resolve().parent),
            allow_origins=["*"],
            web=True,
        )
    except Exception:
        app = FastAPI(title="Methodic ADK Agent")

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/.well-known/agent-card.json")
    async def agent_card():
        return JSONResponse(content=AGENT_CARD)

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

    return app


app = create_app()
