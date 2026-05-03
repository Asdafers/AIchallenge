#!/usr/bin/env python3
"""
Gemini ACP driver — launches gemini --acp --yolo, sends a prompt, collects response.

Usage:
    python3 scripts/gemini_acp_driver.py --cwd /path/to/project --prompt "do the thing"
    python3 scripts/gemini_acp_driver.py --cwd . --prompt "review this code" --timeout 300

The ACP (Agent Client Protocol) turns Gemini CLI into a stateful JSON-RPC 2.0 daemon
over stdio. This script drives the full lifecycle: initialize → session/new → session/prompt → shutdown.

Protocol reference (from @agentclientprotocol/sdk bundled in gemini-cli):
    https://agentclientprotocol.com/protocol/overview

Requires: gemini CLI v0.40+ installed globally (`npm i -g @google/gemini-cli`)
"""
import subprocess, json, sys, argparse, threading, queue, time


def ndjson_reader(pipe, q):
    for line in pipe:
        line = line.strip()
        if line:
            try:
                q.put(json.loads(line))
            except json.JSONDecodeError:
                q.put({"_raw": line})
    q.put(None)


def send(proc, msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()


def recv(q, timeout=120):
    try:
        return q.get(timeout=timeout)
    except queue.Empty:
        return None


def recv_until_result(q, req_id, timeout=300):
    messages = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        msg = recv(q, timeout=int(max(1, deadline - time.time())))
        if msg is None:
            break
        messages.append(msg)
        if msg.get("id") == req_id:
            return msg, messages
        if msg.get("error"):
            return msg, messages
    return None, messages


def main():
    parser = argparse.ArgumentParser(description="Drive Gemini CLI via ACP over stdio")
    parser.add_argument("--cwd", required=True, help="Working directory for the Gemini session")
    parser.add_argument("--prompt", required=True, help="Prompt text to send")
    parser.add_argument("--timeout", type=int, default=600, help="Max seconds to wait for response")
    args = parser.parse_args()

    proc = subprocess.Popen(
        ["gemini", "--acp", "--yolo"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1
    )

    q = queue.Queue()
    reader = threading.Thread(target=ndjson_reader, args=(proc.stdout, q), daemon=True)
    reader.start()

    # 1. initialize — handshake with protocolVersion: 1
    send(proc, {"jsonrpc": "2.0", "method": "initialize", "params": {
        "protocolVersion": 1,
        "clientInfo": {"name": "claude-task-driver", "version": "1.0.0"},
        "clientCapabilities": {
            "fs": {"readTextFile": False, "writeTextFile": False},
            "terminal": True,
            "auth": {"terminal": False}
        }
    }, "id": 1})
    init_resp, _ = recv_until_result(q, 1, timeout=15)
    if not init_resp or "error" in init_resp:
        print(json.dumps({"ok": False, "stage": "initialize", "error": init_resp}))
        proc.kill()
        return 1

    # 2. session/new — creates a session scoped to cwd
    send(proc, {"jsonrpc": "2.0", "method": "session/new", "params": {
        "cwd": args.cwd, "mcpServers": []
    }, "id": 2})
    session_resp, _ = recv_until_result(q, 2, timeout=15)
    if not session_resp or "error" in session_resp:
        print(json.dumps({"ok": False, "stage": "session/new", "error": session_resp}))
        proc.kill()
        return 1
    session_id = session_resp["result"]["sessionId"]

    # 3. session/prompt — send the prompt as ContentBlock[]
    send(proc, {"jsonrpc": "2.0", "method": "session/prompt", "params": {
        "sessionId": session_id,
        "prompt": [{"type": "text", "text": args.prompt}]
    }, "id": 3})

    collected_text = []
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        msg = recv(q, timeout=int(max(5, deadline - time.time())))
        if msg is None:
            break
        if msg.get("id") == 3:
            print(json.dumps({
                "ok": True,
                "session_id": session_id,
                "response_text": "".join(collected_text),
                "stop_reason": msg.get("result", {}).get("stopReason"),
                "result": msg.get("result")
            }))
            break
        params = msg.get("params", {})
        update = params.get("update", {})
        if update.get("sessionUpdate") == "agent_message_chunk":
            text = update.get("content", {}).get("text", "")
            collected_text.append(text)
            sys.stderr.write(text)
        elif update.get("sessionUpdate") == "agent_thought_chunk":
            pass
    else:
        print(json.dumps({"ok": False, "stage": "prompt", "error": "timeout"}))

    # 4. shutdown
    send(proc, {"jsonrpc": "2.0", "method": "shutdown", "params": {}, "id": 99})
    time.sleep(1)
    proc.kill()
    proc.wait()
    return 0


if __name__ == "__main__":
    sys.exit(main())
