"""A2A task store — in-memory task lifecycle for agent-to-agent delegation."""

from __future__ import annotations

import time
import uuid
from enum import Enum


class TaskState(str, Enum):
    SUBMITTED = "submitted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class A2ATaskStore:

    def __init__(self):
        self._tasks: dict[str, dict] = {}

    def create(self, skill: str, input_data: dict) -> dict:
        task_id = f"a2a-{uuid.uuid4().hex[:12]}"
        task = {
            "id": task_id,
            "skill": skill,
            "input": input_data,
            "status": TaskState.SUBMITTED,
            "result": None,
            "artifacts": [],
            "events": [],
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        self._tasks[task_id] = task
        return task

    def get(self, task_id: str) -> dict | None:
        return self._tasks.get(task_id)

    def update(self, task_id: str, status: str | TaskState, **kwargs) -> dict:
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Task {task_id} not found")
        task["status"] = TaskState(status) if isinstance(status, str) else status
        task["updated_at"] = time.time()
        task.update(kwargs)
        return task

    def complete(self, task_id: str, result: dict, artifacts: list | None = None) -> dict:
        task = self.update(task_id, status=TaskState.COMPLETED)
        task["result"] = result
        if artifacts:
            task["artifacts"] = artifacts
        return task

    def fail(self, task_id: str, error: str) -> dict:
        task = self.update(task_id, status=TaskState.FAILED)
        task["error"] = error
        return task

    def cancel(self, task_id: str) -> dict:
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Task {task_id} not found")
        if task["status"] in (TaskState.COMPLETED, TaskState.FAILED):
            raise ValueError(f"Cannot cancel task in state {task['status']}")
        return self.update(task_id, status=TaskState.CANCELLED)

    def add_event(self, task_id: str, event: dict) -> None:
        task = self._tasks.get(task_id)
        if task:
            task["events"].append(event)

    def list_tasks(self, skill: str | None = None) -> list[dict]:
        tasks = list(self._tasks.values())
        if skill:
            tasks = [t for t in tasks if t["skill"] == skill]
        return tasks
