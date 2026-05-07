"""Integration smoke tests."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_root_agent_graph():
    from methodic.agent import root_agent, study_planner, fieldwork_loop, finalize, interview_loop
    assert root_agent.name == "methodic"
    assert len(root_agent.sub_agents) == 3
    assert study_planner.name == "study_planner"
    assert len(study_planner.sub_agents) == 3
    assert fieldwork_loop.max_iterations == 3
    assert interview_loop.max_iterations == 6
    assert len(interview_loop.sub_agents) == 4
    assert len(finalize.sub_agents) == 3


@pytest.mark.asyncio
async def test_mcp_server_lists_both_tools():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(REPO_ROOT / "scripts" / "wp6_mcp_server.py")],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            assert "lookup_deal_context" in names
            assert "lookup_trial_telemetry" in names


def test_coverage_checker_with_fixture_data():
    from methodic.tools.coverage_checker import check_coverage
    from methodic.schemas import (
        ParticipantResponse, StructuredFields, QualityMetrics, EvidenceItem,
    )

    p001 = ParticipantResponse(
        participant_id="P-001", study_id="STUDY-DEMO",
        segment="lost_deal_economic_buyer", persona_summary="VP Finance",
        conversation_status="complete",
        structured_fields=StructuredFields(
            primary_loss_reason="unclear_roi", secondary_loss_reason="budget_timing",
            roi_clarity="unclear", budget_timing="out_of_cycle",
            procurement_friction="unknown", security_concern="none",
            competitor_pressure="none", aha_moment_reached="no",
        ),
        field_confidence={"primary_loss_reason": 0.92},
        coverage_state={
            "primary_loss_reason": "covered_high_confidence",
            "procurement_friction": "missing",
        },
        quality=QualityMetrics(variable_coverage=0.75, ambiguity_resolved=True,
                                evidence_linked=True, requires_recontact=False),
        evidence=[], unresolved_ambiguities=[],
    )
    result = check_coverage([p001])
    assert result["per_variable"]["primary_loss_reason"] == "covered_high_confidence"
    assert "procurement_friction" in result["missing_variables"]


def test_bigquery_export_dry_run():
    from methodic.tools.bigquery_export import export_to_bigquery
    from methodic.schemas import (
        ParticipantResponse, StructuredFields, QualityMetrics,
    )
    r = ParticipantResponse(
        participant_id="P-001", study_id="STUDY-DEMO", segment="lost",
        persona_summary="VP", conversation_status="complete",
        structured_fields=StructuredFields(
            primary_loss_reason="unclear_roi", secondary_loss_reason=None,
            roi_clarity="unclear", budget_timing="out_of_cycle",
            procurement_friction="none", security_concern="none",
            competitor_pressure="none", aha_moment_reached="no",
        ),
        field_confidence={"primary_loss_reason": 0.92},
        coverage_state={"primary_loss_reason": "covered_high_confidence"},
        quality=QualityMetrics(variable_coverage=0.75, ambiguity_resolved=True,
                                evidence_linked=True, requires_recontact=False),
        evidence=[], unresolved_ambiguities=[],
    )
    result = export_to_bigquery([r], dry_run=True)
    assert result["dry_run"] is True
    assert result["rows_written"] == 1
    assert result["rows"][0]["primary_loss_reason"] == "unclear_roi"


def test_server_has_a2a_card():
    from methodic.server import app
    paths = [r.path for r in app.routes if hasattr(r, 'path')]
    assert "/health" in paths
    assert "/.well-known/agent-card.json" in paths
    assert "/api/demo/run" in paths
    assert "/api/demo/{study_id}/status" in paths
    assert "/api/stream" in paths


def test_turn_checker_exits_loop():
    from methodic.agents.turn_checker_step import TurnCheckerStep
    from methodic.schemas import CANONICAL_FIELDS
    step = TurnCheckerStep(name="tc", max_turns=6)
    assert step.should_escalate({"turn_count": 6}) is True
    assert step.should_escalate({"turn_count": 2}) is False
    assert step.should_escalate({
        "turn_count": 1,
        "participant_coverage": {f: "covered_high_confidence" for f in CANONICAL_FIELDS},
    }) is True
