# HISTORICAL — Agents Onboarding (2026-05-01)

> **DO NOT FOLLOW.** This file is the original one-time setup guide for wiring Claude Code, Gemini CLI, and Codex CLI to the Mission Control MCP. As of 2026-05-01 all three runtimes are wired in this repo and the operator's host. Future agents should read `AGENTS-PROTOCOL.md` (runtime quickstart) and the v2 design spec, not this file.
>
> Kept for audit/reproducibility only — if a fresh host needs to be set up from scratch, the connection blocks below are the historical reference.

---

## Original §1 — Connect

The Mission Control MCP runs in a local Docker container `email-calendar-agent-mission-control-1`. All three CLIs reach it via `docker exec -i ... stdio`. The container must already be up — verify with `docker ps --filter name=email-calendar-agent-mission-control-1`.

### Claude Code
Already wired. See `.claude/settings.json` in this repo (committed). No further setup.

### Gemini CLI
Already wired. See `.gemini/settings.json` in this repo (committed). No further setup.

### Codex CLI
Add this block to `~/.codex/config.toml` on the host running Codex:

```toml
[mcp_servers.mission-mcp]
command = "docker"
args = [
    "exec",
    "-i",
    "email-calendar-agent-mission-control-1",
    "python",
    "brain/mission_server.py",
    "stdio",
]
```

(Reference: Codex CLI MCP server config docs. Tool-level approval modes can be added under `[mcp_servers.mission-mcp.tools.<name>]` if you want approval prompts on specific writes.)

### Verify the connection
From any of the three runtimes, call:

```
mission_get_strategy()
```

You should see a dict whose keys include `aichallenge`. If `aichallenge` is missing, the harness is not seeded and you should stop and tell the operator.

---

## Original §6 — Self-check before claiming first task

Run this round-trip from your runtime to confirm everything is wired:

1. `mission_get_strategy()` → returns dict including `aichallenge` key. ✅ MCP reachable, namespace seeded.
2. `mission_list_tasks(project="aichallenge", status="open")` → returns ≥0 rows of dicts. ✅ Tool surface is the new schema.
3. Pick any returned `task["id"]`, then `mission_get_task(task_id=<id>)` → returns `{task, events}` with at least the `created` event. ✅ Audit trail is intact.

If any of these fails, stop and tell the operator. Do not "work around it."

---

## Why this was archived

Agents were running the docker-status check and the three-call self-check on every session even though the wiring was stable. The ceremonies shifted load from the MCP (which already returns structured errors) to ad-hoc shell investigation, defeating the point of the protocol. The slim runtime version replaces both blocks with a single halt rule: *if any `mission_*` call fails, stop and tell the operator.*
