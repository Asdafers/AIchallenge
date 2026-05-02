# Controlling Gemini CLI via ACP (Agent Client Protocol)

## Discovery (2026-05-02)

Gemini CLI v0.40+ has an `--acp` flag that turns it into a **stateful JSON-RPC 2.0 daemon over stdio**. Combined with `--yolo` (auto-approve all tool calls), this lets Claude Code launch and steer Gemini programmatically — no Docker, no HTTP server, no sandbox workaround needed.

## Quick start

```bash
# One-shot prompt via driver script
python3 scripts/gemini_acp_driver.py \
  --cwd /Volumes/workz/GitHubProjects/AIchallenge \
  --prompt "Review the WP3 organizer flow for schema drift" \
  --timeout 300
```

Output is JSON on stdout: `{"ok": true, "response_text": "...", "stop_reason": "end_turn"}`.
Streaming text goes to stderr.

## Protocol lifecycle

The ACP spec lives at `agentclientprotocol.com`. Protocol version is `1` (uint16).

```
Client                              Gemini daemon (--acp)
  │                                       │
  │─── initialize (protocolVersion:1) ───>│
  │<── agentInfo, capabilities ───────────│
  │                                       │
  │─── session/new (cwd, mcpServers) ────>│
  │<── sessionId, modes, models ──────────│
  │                                       │
  │─── session/prompt (sessionId, text) ─>│
  │<── session/update (thought chunks) ───│  (notification)
  │<── session/update (message chunks) ───│  (notification)
  │<── result (stopReason: end_turn) ─────│  (response to id:3)
  │                                       │
  │─── shutdown ─────────────────────────>│
```

## Key methods

### Client → Agent (requests)

| Method | Required params | Returns |
|--------|----------------|---------|
| `initialize` | `protocolVersion: 1`, `clientCapabilities` | `agentInfo`, `authMethods`, `agentCapabilities` |
| `session/new` | `cwd: string`, `mcpServers: []` | `sessionId`, `modes`, `models` |
| `session/prompt` | `sessionId`, `prompt: ContentBlock[]` | `stopReason`, token metadata |
| `session/cancel` | `requestId` | (notification, no response) |
| `shutdown` | `{}` | — |

### Agent → Client (callbacks, only without --yolo)

| Method | Purpose |
|--------|---------|
| `session/request_permission` | Agent asks client to approve a tool call |
| `fs/read_text_file` | Agent asks client to read a file |
| `fs/write_text_file` | Agent asks client to write a file |
| `terminal/create` | Agent asks client to run a shell command |
| `terminal/output` | Agent asks client for terminal output |

With `--yolo`, permission callbacks are skipped entirely.

## ContentBlock format

```json
[{"type": "text", "text": "your prompt here"}]
```

Also supports `image` (base64 + mimeType), `audio`, `resource_link`, `resource` (embedded).

## Streaming updates

During `session/prompt`, the agent sends `session/update` notifications:

- `agent_thought_chunk` — thinking/reasoning (can be ignored)
- `agent_message_chunk` — actual response text
- `available_commands_update` — slash commands available in session

The final response to the `session/prompt` request ID carries `stopReason` and token usage.

## Schemas (from source)

All schemas are Zod-validated from `@agentclientprotocol/sdk` bundled at:
```
~/.nvm/versions/node/v24.11.0/lib/node_modules/@google/gemini-cli/bundle/gemini-ZYQZGZWC.js
```
Lines 11139–11810 contain all method constants (`AGENT_METHODS`, `CLIENT_METHODS`) and Zod schemas.

## Sandbox note

Claude Code's sandbox blocks network access needed by Gemini. Either:
- Disable sandbox: `"sandbox": {"enabled": false}` in `.claude/settings.local.json`
- Or use `dangerouslyDisableSandbox: true` per Bash call

## Available models (as of v0.40.1)

- `auto-gemini-3` (default) — routes to gemini-3.1-pro or gemini-3-flash
- `auto-gemini-2.5` — routes to gemini-2.5-pro or gemini-2.5-flash
- `gemini-3.1-pro-preview`, `gemini-3-flash-preview`
- `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`
