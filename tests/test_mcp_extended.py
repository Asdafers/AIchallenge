"""Tests for extended MCP server (lookup_trial_telemetry tool).

Uses the official mcp.client.stdio module for correct framing,
matching the pattern in scripts/wp6_mcp_boundary.py.
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = str(REPO_ROOT / "scripts" / "wp6_mcp_server.py")


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def _run_with_server(fn):
    """Start MCP server and run fn(session)."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await fn(session)


@pytest.mark.asyncio
async def test_list_tools_includes_telemetry():
    async def check(session):
        tools = await session.list_tools()
        tool_names = [t.name for t in tools.tools]
        assert "lookup_deal_context" in tool_names
        assert "lookup_trial_telemetry" in tool_names
        return True
    assert await _run_with_server(check)


@pytest.mark.asyncio
async def test_lookup_trial_telemetry_p001():
    async def check(session):
        result = await session.call_tool(
            "lookup_trial_telemetry",
            arguments={"participant_id": "P-001"},
        )
        content = json.loads(result.content[0].text)
        assert "login_count" in content
        assert "features_used" in content
        assert "report_builder_reached" in content
        return True
    assert await _run_with_server(check)


@pytest.mark.asyncio
async def test_lookup_trial_telemetry_missing_participant():
    async def check(session):
        result = await session.call_tool(
            "lookup_trial_telemetry",
            arguments={"participant_id": "P-999"},
        )
        content = result.content[0].text.lower()
        assert "error" in content or "not found" in content
        return True
    assert await _run_with_server(check)
