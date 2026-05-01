# Local Agent Collaboration Workflow Design

## Overview
This document outlines the workflow for multi-agent collaboration (Gemini, Claude, and Codex) within the AIchallenge project workspace. The goal of this mission is to coordinate development tasks and strategy using a shared local MCP server, functioning as a persistent **Task Ledger / Blackboard**. 

As identified in multi-agent research, ephemeral chat histories lead to context degradation and hallucination loops. This architecture utilizes a centralized, durable workspace to ensure all agents share a canonical record of truth.

## Architecture & Integration (Task-Ledger Pattern)
*   **Central Hub:** A standalone Docker container (`email-calendar-agent-mission-control-1`) running locally acts as the shared brain and task database. This implements a Blackboard pattern where agents communicate indirectly via the shared environment.
*   **MCP Configuration:** All agents (Gemini, Claude, and Codex) must be configured to connect to this MCP server.
    *   The MCP connection uses the `docker exec` command to pipe stdio from the running container.
    *   Example configuration command: `docker exec -i email-calendar-agent-mission-control-1 python brain/mission_server.py stdio`
*   **Shared Tools:** Agents utilize the tools exposed by the Mission MCP, specifically:
    *   `mission_get_data`
    *   `mission_add_task`
    *   `mission_update_task`
    *   `mission_get_strategy`
    *   `mission_update_strategy`

## Task Format (The Protocol)
To ensure agents pick up the appropriate tasks from the `mission-control` database, a strict naming convention is used when creating tasks via `mission_add_task`.

*   **Format:** `[Assignee] Task Description`
*   **Assignees:**
    *   `[Gemini]` - Tasks specifically requiring Gemini's perspective or capabilities.
    *   `[Claude]` - Tasks specifically requiring Claude's perspective or capabilities.
    *   `[Codex]` - Tasks specifically requiring Codex's perspective or capabilities.
    *   `[Any]` - General tasks that any available agent can pick up.
*   **Example:** `[Codex] Refactor the database connection logic`

## The Execution Loop & Risk Mitigation
When an agent is invoked or starts a work session, it must follow this loop while adhering to strict production risk mitigations:

1.  **Sync:** Call `mission_get_data()` to read the current open tasks.
2.  **Filter & Lock (Concurrency Mitigation):** Scan the list for tasks starting with their specific prefix or `[Any]`. 
    *   *Risk:* Race conditions where two agents pull the same `[Any]` task. 
    *   *Mitigation:* As soon as a task is selected, the agent should immediately update the task description or status (if the MCP schema allows) to indicate it has been claimed (e.g., changing `[Any]` to `[Gemini] (In Progress)` via a delete/re-add or update if supported).
3.  **Context Engineering & Drift Mitigation:**
    *   Before executing the task, the agent must briefly consult the current `mission_get_strategy()` output to ensure the immediate action aligns with the broader project goal. This prevents **Mission Drift** over long-horizon sessions.
4.  **Execute:** Perform the requested coding/research in the workspace, keeping working context small to prevent KV Cache bloat.
5.  **Delegate & Anti-Sycophancy Review:**
    *   If an agent requires peer review, they create a new task for another agent (e.g., `mission_add_task("[Claude] Review the newly generated survey API")`).
    *   *Risk:* Agent Sycophancy (agreeable validation).
    *   *Mitigation:* When creating a review task, the delegating agent MUST explicitly assign an adversarial or critical role. Example: `[Claude] Act as a strict Critic. Actively look for logic flaws and race conditions in the new API. Do not simply validate.` This forces a structured, debate-based consensus.
6.  **Complete:** Once the work is verified and complete, call `mission_update_task(task_id, true)` to check it off.
7.  **Loop:** Repeat step 1 to find the next task.
