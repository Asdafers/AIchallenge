# Local Agent Collaboration Workflow Design

## Overview
This document outlines the workflow for multi-agent collaboration (Gemini, Claude, and Codex) within the AIchallenge project workspace. The goal of this mission is to coordinate development tasks and strategy using a shared local MCP server.

## Architecture & Integration
*   **Central Hub:** A standalone Docker container (`email-calendar-agent-mission-control-1`) running locally acts as the shared brain and task database.
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

## The Execution Loop
When an agent is invoked or starts a work session, it must follow this loop:

1.  **Sync:** Call `mission_get_data()` to read the current open tasks.
2.  **Filter:** Scan the list for tasks starting with their specific prefix (e.g., `[Gemini]`) or `[Any]`.
3.  **Acknowledge & Execute:** Select a task and perform the requested coding/research in the workspace. (Note: As the current MCP does not support an "in-progress" state, the agent simply begins work locally).
4.  **Delegate (If needed):** If an agent realizes a sub-task requires another agent's perspective or capabilities, they create a new task for that agent (e.g., `mission_add_task("[Claude] Review the newly generated survey API")`).
5.  **Complete:** Once the work is verified and complete, call `mission_update_task(task_id, true)` to check it off.
6.  **Loop:** Repeat step 1 to find the next task.
