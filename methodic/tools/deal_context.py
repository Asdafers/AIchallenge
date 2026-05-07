"""McpToolset wrapper for the wp6 MCP server."""

from __future__ import annotations
from pathlib import Path

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MCP_SERVER_PATH = REPO_ROOT / "scripts" / "wp6_mcp_server.py"


def get_deal_context_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python3", args=[str(MCP_SERVER_PATH)],
            ),
        ),
        tool_filter=["lookup_deal_context", "lookup_trial_telemetry"],
    )
