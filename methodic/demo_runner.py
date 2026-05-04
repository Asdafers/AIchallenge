"""Demo runner - async orchestrator that invokes root_agent and streams state.

Bridges the gap between /api/demo/run and the ADK agent graph.
Updates the demo session dict with events and coverage snapshots.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

log = logging.getLogger(__name__)


async def run_demo_pipeline(
    demo_sessions: dict[str, dict],
    study_id: str,
) -> None:
    """Run the full Methodic pipeline as a background task.

    Updates demo_sessions[study_id] with events and coverage as the
    pipeline progresses. Sets status to 'complete' or 'failed'.
    """
    session = demo_sessions.get(study_id)
    if not session:
        return

    try:
        session["events"].append({"step": "request", "status": "done"})

        from methodic.agent import root_agent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService

        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="methodic_demo",
            session_service=session_service,
        )

        adk_session = await session_service.create_session(
            app_name="methodic_demo",
            user_id="demo_user",
        )

        from google.genai import types

        user_message = types.Content(
            role="user",
            parts=[types.Part(text=(
                "Run a win-loss study on recent Q1 2026 lost deals. "
                "Focus on understanding why deals were lost, especially "
                "around ROI clarity and procurement friction. "
                "Available participants: P-001, P-002, P-003. "
                "Reserve: P-005."
            ))],
        )

        session["events"].append({"step": "pipeline_started", "status": "running"})

        async for event in runner.run_async(
            session_id=adk_session.id,
            user_id="demo_user",
            new_message=user_message,
        ):
            if hasattr(event, "actions") and event.actions:
                step_name = getattr(event, "agent_name", "unknown")
                session["events"].append({"step": step_name, "status": "done"})

            state = getattr(event, "state", None)
            if state and "coverage_state" in state:
                session["coverage"] = state["coverage_state"]

        session["status"] = "complete"
        session["events"].append({"step": "complete", "status": "done"})

    except Exception as e:
        log.exception("Demo pipeline failed: %s", e)
        session["status"] = "failed"
        session["events"].append({
            "step": "error", "status": "failed", "detail": str(e),
        })
