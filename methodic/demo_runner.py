"""Demo runner - async orchestrator that invokes root_agent and streams state.

Bridges the gap between /api/demo/run and the ADK agent graph.
Updates the demo session dict with events and coverage snapshots.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def _extract_event_text(event: Any) -> str:
    """Return displayable text from an ADK event if present."""
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None)
    if not parts:
        return ""

    texts: list[str] = []
    for part in parts:
        text = getattr(part, "text", None)
        if text:
            texts.append(text)
    return " ".join(texts).strip()


def _event_role(author: str) -> str:
    if author == "participant_sim":
        return "participant"
    if author in {"request", "pipeline_started", "complete"}:
        return "system"
    return "agent"


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
        session["events"].append({
            "step": "request",
            "status": "done",
            "role": "system",
            "text": "Sales Insights requests a win-loss study for slipping Q1 2026 deals.",
        })

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

        session["events"].append({
            "step": "pipeline_started",
            "status": "running",
            "role": "system",
            "text": "Methodic starts organizer, methodology, fieldwork, quality, and export pipeline.",
        })

        async for event in runner.run_async(
            session_id=adk_session.id,
            user_id="demo_user",
            new_message=user_message,
        ):
            if hasattr(event, "author") and event.author:
                author = event.author
                text = _extract_event_text(event)
                session["events"].append({
                    "step": author,
                    "status": "done",
                    "role": _event_role(author),
                    "text": text or f"{author} completed.",
                })

        final_session = await session_service.get_session(
            app_name="methodic_demo",
            user_id="demo_user",
            session_id=adk_session.id,
        )
        if final_session and hasattr(final_session, "state"):
            coverage = final_session.state.get("coverage_state", {})
            session["coverage"] = coverage

        session["status"] = "complete"
        session["events"].append({
            "step": "complete",
            "status": "done",
            "role": "system",
            "text": "Demo run complete. Coverage and export status are ready for review.",
        })

    except Exception as e:
        log.exception("Demo pipeline failed: %s", e)
        session["status"] = "failed"
        session["events"].append({
            "step": "error", "status": "failed", "role": "error",
            "text": f"Demo pipeline failed: {e}", "detail": str(e),
        })
