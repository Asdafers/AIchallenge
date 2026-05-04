#!/usr/bin/env python3
"""WP6 MCP Server — lookup_deal_context backed by fixture CRM + telemetry.

Runs as a stdio MCP server subprocess. Loads fixture files from
fixtures/crm/{participant_id}.json and optionally fixtures/telemetry/{participant_id}.json,
merges them, filters to allowed_fields, and returns the filtered context.

Not invoked directly — spawned by wp6_mcp_boundary.py via stdio_client.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


REPO_ROOT = Path(__file__).resolve().parent.parent
CRM_DIR = REPO_ROOT / "fixtures" / "crm"
TELEMETRY_DIR = REPO_ROOT / "fixtures" / "telemetry"

ALLOWED_FIELDS_ENUM = ["deal_stage", "persona", "trial_usage", "crm_notes"]
TELEMETRY_FIELDS = ["login_count", "features_used", "report_builder_reached", "executive_logins"]

server = Server("methodic-context")
_DELAY_SECONDS = 0.0


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_optional(path: Path) -> dict | None:
    if path.exists():
        return _load_json(path)
    return None


def _build_merged_context(participant_id: str) -> dict[str, Any]:
    crm_path = CRM_DIR / f"{participant_id}.json"
    if not crm_path.exists():
        raise FileNotFoundError(f"No CRM fixture for {participant_id}")

    crm = _load_json(crm_path)
    telemetry = _load_json_optional(TELEMETRY_DIR / f"{participant_id}.json")

    context = dict(crm)

    if telemetry and "trial_usage" in context:
        enriched = dict(context["trial_usage"])
        for key in ("executive_logins", "last_active", "feature_touchpoints"):
            if key in telemetry:
                enriched[key] = telemetry[key]
        context["trial_usage"] = enriched

    return context


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="lookup_deal_context",
            description=(
                "Look up business context for a participant from CRM and "
                "telemetry sources. Returns filtered fields only."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "participant_id": {
                        "type": "string",
                        "description": "Participant identifier (e.g., P-001)",
                    },
                    "allowed_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ALLOWED_FIELDS_ENUM,
                        },
                        "description": "Fields to return from context lookup",
                    },
                },
                "required": ["participant_id", "allowed_fields"],
            },
        ),
        Tool(
            name="lookup_trial_telemetry",
            description=(
                "Look up trial usage telemetry for a participant. Returns login count, "
                "features used, report builder access, and executive login data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "participant_id": {
                        "type": "string",
                        "description": "Participant identifier (e.g., P-001)",
                    },
                },
                "required": ["participant_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    participant_id = arguments["participant_id"]

    if name == "lookup_deal_context":
        allowed_fields = arguments.get("allowed_fields", ALLOWED_FIELDS_ENUM)
        merged = _build_merged_context(participant_id)
        filtered = {k: merged[k] for k in allowed_fields if k in merged}
        if _DELAY_SECONDS > 0:
            await asyncio.sleep(_DELAY_SECONDS)
        return [TextContent(type="text", text=json.dumps(filtered, indent=2))]

    elif name == "lookup_trial_telemetry":
        telemetry_path = TELEMETRY_DIR / f"{participant_id}.json"
        if not telemetry_path.exists():
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"No telemetry data found for {participant_id}"}),
            )]
        telemetry = _load_json(telemetry_path)
        filtered = {k: telemetry[k] for k in TELEMETRY_FIELDS if k in telemetry}
        if _DELAY_SECONDS > 0:
            await asyncio.sleep(_DELAY_SECONDS)
        return [TextContent(type="text", text=json.dumps(filtered, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    global _DELAY_SECONDS
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--delay-ms", type=int, default=0,
        help="Artificial delay in ms before responding (for timeout testing)",
    )
    args = parser.parse_args()
    _DELAY_SECONDS = args.delay_ms / 1000.0

    try:
        async with stdio_server() as (read_stream, write_stream):
            init_options = server.create_initialization_options()
            await server.run(read_stream, write_stream, init_options)
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
