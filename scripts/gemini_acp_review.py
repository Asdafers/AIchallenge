#!/usr/bin/env python3
"""ACP-driven gemini worker for mission-control tasks.

Picks the highest-priority eligible mission task (filtered by role + parent
completion + status), claims it atomically from Python, then spawns
`gemini --acp` and drives a single ACP session to do the work and complete the
task. On any error (or Ctrl-C) the claim is broken cleanly so the task is not
stranded.

Usage:
    python scripts/gemini_acp_review.py [--role gemini] [--list | --dry-run | --loop]
    python scripts/gemini_acp_review.py TASK_ID                  # specific task

Without TASK_ID, it auto-picks the next eligible open task. With --loop, it
keeps picking and processing tasks until the queue is empty.

Requires:
    - gemini CLI (>=0.40) on PATH, authenticated (~/.gemini/oauth_creds.json)
    - mission-mcp container reachable: docker exec into
      email-calendar-agent-mission-control-1
    - Python 3.10+, stdlib only

Run from the repository root.

This client uses asyncio.create_subprocess_exec (safe argv form, NOT a shell
string). It forbids fs/write_text_file + terminal/* callbacks by default. Tool
calls go through an explicit allowlist; mission_complete_task and
mission_refuse_task are constrained to the task_id we picked.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import signal
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ACP_PROTOCOL_VERSION = 1
MCP_PROTOCOL_VERSION = "2024-11-05"

PROJECT = "aichallenge"

MISSION_MCP_CMD: tuple[str, ...] = (
    "docker",
    "exec",
    "-i",
    "email-calendar-agent-mission-control-1",
    "python",
    "brain/mission_server.py",
    "stdio",
)

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}

# ---------------------------------------------------------------------------
# Permission policy (closure-bound to the picked task_id at runtime)
# ---------------------------------------------------------------------------

# Tool-name substrings auto-approved (read-only and listing).
ALLOWED_TOOL_FRAGMENTS: tuple[str, ...] = (
    "mission_get_task",
    "mission_list_tasks",
    "mission_get_strategy",
    "read_file",
    "read_many_files",
    "list_directory",
    "glob",
    "search_file_content",
    "google_web_search",
    "web_fetch",
)

# Tool-name substrings that need task-id matching (closure_bound below).
SCOPED_WRITE_TOOLS: tuple[str, ...] = (
    "mission_complete_task",
    "mission_refuse_task",
)

# Shell command prefixes allowed when the agent runs an `execute` tool.
ALLOWED_SHELL_PREFIXES: tuple[str, ...] = (
    "python scripts/validate_schemas.py",
    "python scripts/validate_fixtures.py",
    "python -m json.tool",
    "git status",
    "git log",
    "git diff",
    "ls ",
    "cat ",
    "head ",
    "tail ",
    "wc ",
    "grep ",
    "find ",
    "rg ",
)


# ---------------------------------------------------------------------------
# Pretty output
# ---------------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def c(code: str, text: str) -> str:
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def stamp() -> str:
    return time.strftime("%H:%M:%S")


def log(prefix: str, body: str, color: str = "0") -> None:
    print(f"{c('2', stamp())} {c(color, prefix)} {body}", flush=True)


def hr() -> None:
    print(c("2", "-" * 78), flush=True)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class RPCError(Exception):
    def __init__(self, err: dict[str, Any]) -> None:
        super().__init__(err.get("message", "RPC error"))
        self.code = err.get("code")
        self.data = err.get("data")


class NoEligibleTask(Exception):
    pass


# ---------------------------------------------------------------------------
# Mission-MCP stdio client
# ---------------------------------------------------------------------------


class MissionMcpClient:
    """Minimal MCP stdio client for the mission-control server."""

    def __init__(self, cmd: tuple[str, ...] = MISSION_MCP_CMD) -> None:
        self.cmd = cmd
        self.proc: asyncio.subprocess.Process | None = None
        self.next_id = 1
        self.pending: dict[int, asyncio.Future[Any]] = {}
        self._reader: asyncio.Task[None] | None = None
        self._stderr: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self.proc = await asyncio.create_subprocess_exec(
            *self.cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._reader = asyncio.create_task(self._read_loop(), name="mcp-stdout")
        self._stderr = asyncio.create_task(self._stderr_drain(), name="mcp-stderr")

    async def stop(self) -> None:
        if self.proc and self.proc.returncode is None:
            try:
                self.proc.terminate()
                await asyncio.wait_for(self.proc.wait(), timeout=2)
            except asyncio.TimeoutError:
                self.proc.kill()
                await self.proc.wait()

    async def _read_loop(self) -> None:
        assert self.proc and self.proc.stdout
        while True:
            line = await self.proc.stdout.readline()
            if not line:
                break
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            req_id = msg.get("id")
            if req_id is None:
                continue  # notification from server (we don't track these)
            fut = self.pending.pop(req_id, None)
            if fut and not fut.done():
                if "error" in msg:
                    fut.set_exception(RPCError(msg["error"]))
                else:
                    fut.set_result(msg.get("result"))

    async def _stderr_drain(self) -> None:
        assert self.proc and self.proc.stderr
        while True:
            line = await self.proc.stderr.readline()
            if not line:
                break
            txt = line.decode(errors="replace").rstrip()
            if txt:
                log("[mcp-stderr]", txt, "33")

    def _send(self, msg: dict[str, Any]) -> None:
        assert self.proc and self.proc.stdin
        self.proc.stdin.write((json.dumps(msg, separators=(",", ":")) + "\n").encode())

    async def _request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        req_id = self.next_id
        self.next_id += 1
        msg: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            msg["params"] = params
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        self.pending[req_id] = fut
        self._send(msg)
        return await fut

    def _notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    async def initialize(self) -> dict[str, Any]:
        result = await self._request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "gemini-acp-worker", "version": "0.1.0"},
            },
        )
        # MCP spec: client must send initialized notification after handshake.
        self._notify("notifications/initialized")
        return result

    async def call_tool(self, name: str, args: dict[str, Any] | None = None) -> Any:
        result = await self._request(
            "tools/call",
            {"name": name, "arguments": args or {}},
        )
        if result.get("isError"):
            raise RPCError({"code": -32603, "message": f"tool error: {result}"})
        for item in result.get("content", []) or []:
            if item.get("type") == "text":
                txt = item.get("text", "")
                try:
                    return json.loads(txt)
                except json.JSONDecodeError:
                    return {"_raw_text": txt}
        return {}


# ---------------------------------------------------------------------------
# Task picking
# ---------------------------------------------------------------------------


def _is_eligible(task: dict[str, Any], role: str) -> bool:
    if task.get("status") != "open":
        return False
    if task.get("claimed_by"):
        return False
    assignee = task.get("requested_assignee")
    return assignee in (role, "any", None, "")


def _priority_score(task: dict[str, Any]) -> int:
    return PRIORITY_RANK.get(task.get("priority", "medium"), 2)


async def _parent_done(mcp: MissionMcpClient, parent_id: str) -> bool:
    parent = await mcp.call_tool("mission_get_task", {"task_id": parent_id})
    return bool(parent.get("task", {}).get("is_done"))


async def find_eligible_tasks(
    mcp: MissionMcpClient, role: str
) -> list[dict[str, Any]]:
    """Return eligible open tasks for role, sorted highest priority first."""
    tasks_result = await mcp.call_tool(
        "mission_list_tasks", {"project": PROJECT, "status": "open"}
    )
    tasks = tasks_result.get("tasks", [])
    eligible = [t for t in tasks if _is_eligible(t, role)]
    ready: list[dict[str, Any]] = []
    for t in eligible:
        parent_id = t.get("parent_id")
        if parent_id and not await _parent_done(mcp, parent_id):
            continue
        ready.append(t)
    ready.sort(
        key=lambda t: (-_priority_score(t), t.get("created_at", "")),
    )
    return ready


def make_actor_id(role: str) -> str:
    suffix = secrets.token_hex(2)
    ts = time.strftime("%Y-%m-%dT%H%M", time.gmtime())
    return f"{role}-{ts}-{suffix}"


# ---------------------------------------------------------------------------
# ACP client
# ---------------------------------------------------------------------------


class ACPClient:
    def __init__(
        self,
        gemini_argv: list[str],
        cwd: str,
        picked_task_id: str,
    ) -> None:
        self.gemini_argv = gemini_argv
        self.cwd = cwd
        self.picked_task_id = picked_task_id
        self.proc: asyncio.subprocess.Process | None = None
        self.next_id = 1
        self.pending: dict[int, asyncio.Future[Any]] = {}
        self.session_id: str | None = None
        self.cancelled = False
        self._reader: asyncio.Task[None] | None = None
        self._stderr: asyncio.Task[None] | None = None

    async def start(self) -> None:
        log("[spawn]", " ".join(self.gemini_argv), "36")
        self.proc = await asyncio.create_subprocess_exec(
            *self.gemini_argv,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd,
        )
        self._reader = asyncio.create_task(self._read_loop(), name="acp-stdout")
        self._stderr = asyncio.create_task(self._stderr_loop(), name="acp-stderr")

    async def stop(self) -> None:
        if self.proc and self.proc.returncode is None:
            try:
                self.proc.terminate()
                await asyncio.wait_for(self.proc.wait(), timeout=3)
            except asyncio.TimeoutError:
                self.proc.kill()
                await self.proc.wait()

    async def _read_loop(self) -> None:
        assert self.proc and self.proc.stdout
        while True:
            line = await self.proc.stdout.readline()
            if not line:
                break
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                log("[wire-non-json]", line.decode(errors="replace").rstrip(), "33")
                continue
            try:
                await self._dispatch(msg)
            except Exception as exc:  # noqa: BLE001
                log("[dispatch-error]", repr(exc), "31")

    async def _stderr_loop(self) -> None:
        assert self.proc and self.proc.stderr
        while True:
            line = await self.proc.stderr.readline()
            if not line:
                break
            log("[gemini-stderr]", line.decode(errors="replace").rstrip(), "33")

    def _send(self, msg: dict[str, Any]) -> None:
        assert self.proc and self.proc.stdin
        self.proc.stdin.write((json.dumps(msg, separators=(",", ":")) + "\n").encode())

    async def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        req_id = self.next_id
        self.next_id += 1
        msg: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            msg["params"] = params
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        self.pending[req_id] = fut
        self._send(msg)
        return await fut

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    async def _dispatch(self, msg: dict[str, Any]) -> None:
        if "method" not in msg:
            req_id = msg.get("id")
            fut = self.pending.pop(req_id, None) if req_id is not None else None
            if fut is None or fut.done():
                return
            if "error" in msg:
                fut.set_exception(RPCError(msg["error"]))
            else:
                fut.set_result(msg.get("result"))
            return
        method = msg["method"]
        params = msg.get("params") or {}
        msg_id = msg.get("id")
        try:
            result = await self._handle_callback(method, params)
            if msg_id is not None:
                self._send({"jsonrpc": "2.0", "id": msg_id, "result": result or {}})
        except RPCError as e:
            if msg_id is not None:
                self._send(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": e.code or -32603,
                            "message": str(e),
                            "data": e.data,
                        },
                    }
                )
        except Exception as exc:  # noqa: BLE001
            if msg_id is not None:
                self._send(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32603, "message": f"client error: {exc!r}"},
                    }
                )

    async def _handle_callback(self, method: str, params: dict[str, Any]) -> Any:
        if method == "session/update":
            self._render_update(params)
            return None
        if method == "session/request_permission":
            return self._handle_permission(params)
        if method == "fs/read_text_file":
            return self._handle_fs_read(params)
        if method == "fs/write_text_file":
            raise RPCError({"code": -32601, "message": "fs/write disabled by client policy"})
        if method.startswith("terminal/"):
            raise RPCError({"code": -32601, "message": f"terminal disabled: {method}"})
        log("[unhandled-callback]", method, "33")
        return {}

    def _handle_fs_read(self, params: dict[str, Any]) -> dict[str, Any]:
        path = params.get("path") or ""
        try:
            target = Path(path).resolve()
            base = Path(self.cwd).resolve()
            target.relative_to(base)
        except (ValueError, OSError):
            raise RPCError({"code": -32603, "message": f"fs/read outside cwd refused: {path}"})
        try:
            return {"content": target.read_text(encoding="utf-8")}
        except OSError as exc:
            raise RPCError({"code": -32603, "message": f"fs/read failed: {exc}"})

    # -- permission policy (closure-bound to picked_task_id) ----------------

    def _handle_permission(self, params: dict[str, Any]) -> dict[str, Any]:
        tool_call = params.get("toolCall") or {}
        title = tool_call.get("title") or ""
        kind = tool_call.get("kind") or ""
        raw = tool_call.get("rawInput") or {}
        target = self._tool_name_guess(title, raw)
        approved, reason = self._policy_decision(kind, target, raw)
        verdict = "allow_once" if approved else "reject_once"
        log(
            "[perm]",
            f"{verdict.upper():12s}  kind={kind or '?':8s}  target={target}  ({reason})",
            "32" if approved else "31",
        )
        option_id = None
        for opt in params.get("options", []):
            if opt.get("kind") == verdict:
                option_id = opt.get("optionId")
                break
        if option_id is None:
            wanted_prefix = "allow" if approved else "reject"
            for opt in params.get("options", []):
                if str(opt.get("kind", "")).startswith(wanted_prefix):
                    option_id = opt.get("optionId")
                    break
        if option_id is None:
            return {"outcome": {"outcome": "cancelled"}}
        return {"outcome": {"outcome": "selected", "optionId": option_id}}

    @staticmethod
    def _tool_name_guess(title: str, raw: dict[str, Any]) -> str:
        for key in ("name", "tool_name", "toolName"):
            v = raw.get(key) if isinstance(raw, dict) else None
            if isinstance(v, str):
                return v
        return (title or "").strip()

    def _policy_decision(
        self, kind: str, target: str, raw: dict[str, Any]
    ) -> tuple[bool, str]:
        target_lc = (target or "").lower()
        # ACP built-in kinds
        if kind == "read":
            return True, "read kind"
        if kind == "search":
            return True, "search kind"
        if kind == "fetch":
            return True, "fetch kind"
        if kind == "think":
            return True, "think kind"
        if kind == "execute":
            cmd = ""
            if isinstance(raw, dict):
                cmd = str(raw.get("command", "")).strip()
            if any(cmd.startswith(p) for p in ALLOWED_SHELL_PREFIXES):
                return True, f"shell allowlist hit: {cmd[:40]}"
            return False, f"shell not in allowlist: {cmd[:80]}"
        if kind in ("edit", "delete", "move"):
            return False, f"write kind blocked: {kind}"
        # MCP tools — task-id scoped writes vs read-only allows
        for write_frag in SCOPED_WRITE_TOOLS:
            if write_frag in target_lc:
                arg_id = self._extract_task_id(raw)
                if arg_id == self.picked_task_id:
                    return True, f"scoped write OK ({write_frag} on picked task)"
                return False, f"scoped write blocked: {write_frag} on {arg_id} != picked {self.picked_task_id}"
        # mission_claim_task — already done by Python; deny
        if "mission_claim_task" in target_lc:
            return False, "claim already performed by coordinator"
        # mission_break_claim — never from inside a session
        if "mission_break_claim" in target_lc:
            return False, "break_claim only from coordinator"
        # generic read-only allowlist
        if any(frag in target_lc for frag in ALLOWED_TOOL_FRAGMENTS):
            return True, f"tool allowlist hit: {target}"
        return False, f"no policy match: kind={kind} target={target}"

    @staticmethod
    def _extract_task_id(raw: Any) -> str | None:
        if not isinstance(raw, dict):
            return None
        # MCP tool calls usually carry arguments as raw["arguments"]["task_id"]
        # but ACP rawInput format varies; cover a few shapes.
        for path_keys in (("arguments", "task_id"), ("task_id",), ("input", "task_id")):
            cur: Any = raw
            ok = True
            for k in path_keys:
                if isinstance(cur, dict) and k in cur:
                    cur = cur[k]
                else:
                    ok = False
                    break
            if ok and isinstance(cur, str):
                return cur
        return None

    def _render_update(self, params: dict[str, Any]) -> None:
        update = params.get("update") or {}
        kind = update.get("sessionUpdate", "")
        if kind == "agent_message_chunk":
            text = (update.get("content") or {}).get("text", "")
            sys.stdout.write(text)
            sys.stdout.flush()
        elif kind == "agent_thought_chunk":
            text = (update.get("content") or {}).get("text", "")
            if text.strip():
                log("[thought]", text.strip().splitlines()[0][:200], "2")
        elif kind == "tool_call":
            title = update.get("title", "tool")
            tool_kind = update.get("kind", "")
            log("[tool->]", f"{tool_kind or '?':8s}  {title}", "36")
        elif kind == "tool_call_update":
            status = update.get("status", "")
            title = update.get("title")
            if status == "completed":
                log("[tool ok]", f"{(title or '').strip() or 'completed'}", "32")
            elif status == "failed":
                log("[tool x]", f"{(title or '').strip() or 'failed'}", "31")
        elif kind == "plan":
            entries = update.get("entries") or []
            log("[plan]", f"{len(entries)} step(s)", "35")
            for e in entries:
                p = e.get("priority", "?")
                t = e.get("content") or e.get("title") or ""
                print(f"           [{p}] {t}", flush=True)
        elif kind == "available_commands_update":
            cmds = update.get("availableCommands") or []
            log("[commands]", f"{len(cmds)} available", "2")
        else:
            log("[update]", kind or "(no kind)", "2")


# ---------------------------------------------------------------------------
# Generic worker prompt
# ---------------------------------------------------------------------------


def worker_prompt(task: dict[str, Any], actor_id: str) -> str:
    task_id = task["id"]
    blind = task.get("blind", False)
    blind_clause = ""
    if blind:
        blind_clause = """
This task is BLIND (blind=true). Do NOT read prior critique or review files
(docs/critique-*.md, any third-party review of the same work package) before
writing your verdict. You may cross-check after your verdict is locked.
"""

    return f"""You are an agent operating under ACP from a Python coordinator that has spawned
you in the AIchallenge repository. Read AGENTS.md and AGENTS-PROTOCOL.md to confirm
the multi-agent claim/complete protocol.

YOUR ACTOR ID for this session: {actor_id}
YOUR TASK ID: {task_id}

The Python coordinator has ALREADY claimed this task on your behalf with the
actor id above. You do NOT need to call mission_claim_task — the policy will
deny it. Proceed directly to reading the task body and acting on it.
{blind_clause}
Steps:

1. mission_get_task on {task_id} — read the full task_body, the work scope, and
   the required outcome shape (what the task body says you must include in the
   completion outcome).

2. If the task has a parent_id, mission_get_task on the parent. Read the
   parent's outcome (the implementer's report on what they built and how to
   verify it). Use it as the starting point for the artifacts you should
   inspect.

3. mission_get_strategy — pull mission_strategy['{PROJECT}']. You must cite at
   least one of: thesis, demo_must_show, non_goals, stack_alignment in your
   completion outcome. Anti-drift requirement (AGENTS-PROTOCOL.md §5).

4. Do the work the task body asks for. For review tasks, read the cited
   artifacts and form an independent verdict. For implementation tasks, follow
   the acceptance criteria. For investigation tasks, explore and report.

5. If you cite a verification command (validator, smoke test), run it and
   confirm exit 0. Failed verification is at minimum a Major finding (review)
   or a blocker (implementation).

6. mission_complete_task with task_id={task_id}, completer_id={actor_id}, and
   outcome containing the exact shape the task body requested. Include
   strategy linkage from step 3.

CONSTRAINTS:
- Stay in scope. Do not modify files unrelated to this task.
- Do not call mission_claim_task (already done) or mission_break_claim.
- Do not claim or complete any other mission task.
- If a tool call is denied by the coordinator, do not retry the same call —
  note it in your outcome and move on.
- If you hit an unrecoverable blocker (mission-mcp unavailable, files missing),
  use mission_refuse_task with a clear reason rather than fabricating output.

Begin now.
"""


# ---------------------------------------------------------------------------
# Worker logic
# ---------------------------------------------------------------------------


async def break_claim_safely(
    mcp: MissionMcpClient, task_id: str, actor_id: str
) -> None:
    try:
        await mcp.call_tool(
            "mission_break_claim",
            {"task_id": task_id, "claimer_id": actor_id},
        )
        log("[cleanup]", f"break_claim ok for {task_id}", "33")
    except Exception as exc:  # noqa: BLE001
        log("[cleanup]", f"break_claim failed (may be already complete): {exc}", "33")


async def process_task(
    mcp: MissionMcpClient,
    task: dict[str, Any],
    role: str,
    cwd: str,
    gemini_bin: str,
) -> int:
    actor_id = make_actor_id(role)
    task_id = task["id"]
    log(
        "[picked]",
        f"{task_id}  priority={task.get('priority')}  "
        f"assignee={task.get('requested_assignee')}  blind={task.get('blind')}",
        "35",
    )
    log("[task-text]", task.get("task_text", ""), "2")

    log("[claim]", f"as {actor_id}", "36")
    claim = await mcp.call_tool(
        "mission_claim_task",
        {"task_id": task_id, "claimer_id": actor_id},
    )
    if not claim.get("claimed"):
        reason = claim.get("reason", "unknown")
        log("[claim-failed]", reason, "31")
        return 5
    log("[claim ok]", f"task {task_id} owned by {actor_id}", "32")

    # Spawn ACP and drive
    client = ACPClient([gemini_bin, "--acp"], cwd, picked_task_id=task_id)
    rc = 0
    try:
        await client.start()

        loop = asyncio.get_event_loop()

        def _on_sigint() -> None:
            client.cancelled = True
            if client.session_id:
                client.notify("session/cancel", {"sessionId": client.session_id})
                log("[signal]", "SIGINT -> session/cancel sent", "33")

        try:
            loop.add_signal_handler(signal.SIGINT, _on_sigint)
        except NotImplementedError:
            pass

        log("[step]", "initialize", "36")
        init_result = await client.request(
            "initialize",
            {
                "protocolVersion": ACP_PROTOCOL_VERSION,
                "clientCapabilities": {
                    "auth": {"terminal": False},
                    "fs": {"readTextFile": True, "writeTextFile": False},
                    "terminal": False,
                },
                "clientInfo": {"name": "claude-acp-bridge", "version": "0.1.0"},
            },
        )
        log("[init ok]", json.dumps(init_result)[:160], "32")

        log("[step]", "session/new", "36")
        new_result = await client.request(
            "session/new",
            {"cwd": cwd, "mcpServers": []},
        )
        client.session_id = new_result.get("sessionId")
        log("[session ok]", f"sessionId={client.session_id}", "32")

        prompt_text = worker_prompt(task, actor_id)
        hr()
        log("[step]", "session/prompt — execution begins", "36")
        hr()
        prompt_result = await client.request(
            "session/prompt",
            {
                "sessionId": client.session_id,
                "prompt": [{"type": "text", "text": prompt_text}],
            },
        )
        hr()
        stop = prompt_result.get("stopReason", "unknown")
        usage = prompt_result.get("usage")
        log("[prompt ok]", f"stopReason={stop}  usage={usage}", "32")
        rc = 0 if stop == "end_turn" else 2

    except RPCError as e:
        log("[rpc-error]", f"{e.code}: {e}", "31")
        rc = 3
    except asyncio.CancelledError:
        log("[cancel]", "worker cancelled", "33")
        rc = 130
        raise
    except Exception as exc:  # noqa: BLE001
        log("[fatal]", repr(exc), "31")
        rc = 4
    finally:
        await client.stop()
        # Verify claim was released by completion. If not, break it.
        latest = await mcp.call_tool("mission_get_task", {"task_id": task_id})
        if not latest.get("task", {}).get("is_done") and latest.get("task", {}).get(
            "claimed_by"
        ) == actor_id:
            log("[cleanup]", "task still claimed by us — releasing", "33")
            await break_claim_safely(mcp, task_id, actor_id)

    return rc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def cmd_list(role: str) -> int:
    mcp = MissionMcpClient()
    await mcp.start()
    try:
        await mcp.initialize()
        tasks = await find_eligible_tasks(mcp, role)
        if not tasks:
            log("[list]", f"no eligible tasks for role={role}", "33")
            return 0
        log("[list]", f"{len(tasks)} eligible task(s) for role={role}", "32")
        for t in tasks:
            print(
                f"  {t['id']}  prio={t.get('priority'):<6} "
                f"assignee={t.get('requested_assignee') or '(any)':<8} "
                f"blind={'Y' if t.get('blind') else ' '}  {t.get('task_text', '')}",
                flush=True,
            )
        return 0
    finally:
        await mcp.stop()


async def cmd_run(args: argparse.Namespace) -> int:
    mcp = MissionMcpClient()
    await mcp.start()
    try:
        await mcp.initialize()
        while True:
            if args.task_id:
                # Specific task requested
                detail = await mcp.call_tool(
                    "mission_get_task", {"task_id": args.task_id}
                )
                t = detail.get("task")
                if not t:
                    log("[error]", f"task {args.task_id} not found", "31")
                    return 1
                if not _is_eligible(t, args.role):
                    log(
                        "[error]",
                        f"task {args.task_id} not eligible for role={args.role} "
                        f"(status={t.get('status')}, "
                        f"assignee={t.get('requested_assignee')}, "
                        f"claimed_by={t.get('claimed_by')})",
                        "31",
                    )
                    return 1
                tasks = [t]
            else:
                tasks = await find_eligible_tasks(mcp, args.role)
            if not tasks:
                log("[idle]", f"no eligible tasks for role={args.role}", "33")
                return 0
            picked = tasks[0]

            if args.dry_run:
                log("[dry-run]", f"would pick {picked['id']}", "35")
                log("[dry-run]", picked.get("task_text", ""), "2")
                return 0

            rc = await process_task(
                mcp,
                picked,
                role=args.role,
                cwd=args.cwd,
                gemini_bin=args.gemini,
            )
            if rc != 0:
                log("[exit]", f"task processing returned rc={rc}", "31")
                return rc

            if not args.loop:
                return 0
            log("[loop]", "task done; checking for more eligible work", "36")
            args.task_id = None  # force re-pick on next iteration
    finally:
        await mcp.stop()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    p.add_argument(
        "task_id",
        nargs="?",
        default=None,
        help="Specific mission task UUID. If omitted, picks the next eligible task.",
    )
    p.add_argument(
        "--role",
        default="gemini",
        help=(
            "Filter for tasks whose requested_assignee is this role, plus "
            "tasks marked 'any' or unassigned. The spawned agent is always "
            "gemini --acp (default role: gemini)."
        ),
    )
    p.add_argument(
        "--gemini",
        default="gemini",
        help="gemini binary (default: gemini on PATH).",
    )
    p.add_argument(
        "--cwd",
        default=os.getcwd(),
        help="Working directory for the gemini session (default: cwd).",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="Just list eligible tasks; do not claim or spawn.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Pick the next task and print it; do not claim or spawn.",
    )
    p.add_argument(
        "--loop",
        action="store_true",
        help="After completing a task, re-pick and continue until queue empties.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.list:
        return asyncio.run(cmd_list(args.role))
    return asyncio.run(cmd_run(args))


if __name__ == "__main__":
    sys.exit(main())
