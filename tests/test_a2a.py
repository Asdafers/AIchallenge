import pytest
from methodic.a2a import A2ATaskStore, TaskState


def test_create_task_returns_id_and_submitted_state():
    store = A2ATaskStore()
    task = store.create(skill="win_loss_study", input_data={"question": "Why are we losing deals?"})
    assert task["id"]
    assert task["status"] == "submitted"
    assert task["skill"] == "win_loss_study"


def test_get_task_returns_stored_task():
    store = A2ATaskStore()
    task = store.create(skill="win_loss_study", input_data={"question": "test"})
    retrieved = store.get(task["id"])
    assert retrieved["id"] == task["id"]
    assert retrieved["status"] == "submitted"


def test_get_nonexistent_task_returns_none():
    store = A2ATaskStore()
    assert store.get("nonexistent") is None


def test_update_task_state():
    store = A2ATaskStore()
    task = store.create(skill="win_loss_study", input_data={"question": "test"})
    store.update(task["id"], status="running")
    assert store.get(task["id"])["status"] == "running"


def test_complete_task_with_result():
    store = A2ATaskStore()
    task = store.create(skill="win_loss_study", input_data={"question": "test"})
    store.complete(task["id"], result={"coverage": {"primary_loss_reason": "covered_high_confidence"}})
    t = store.get(task["id"])
    assert t["status"] == "completed"
    assert t["result"]["coverage"]["primary_loss_reason"] == "covered_high_confidence"


def test_cancel_task():
    store = A2ATaskStore()
    task = store.create(skill="win_loss_study", input_data={"question": "test"})
    store.update(task["id"], status="running")
    store.cancel(task["id"])
    assert store.get(task["id"])["status"] == "cancelled"


def test_cancel_completed_task_raises():
    store = A2ATaskStore()
    task = store.create(skill="win_loss_study", input_data={"question": "test"})
    store.complete(task["id"], result={})
    with pytest.raises(ValueError, match="Cannot cancel"):
        store.cancel(task["id"])


def test_list_tasks():
    store = A2ATaskStore()
    store.create(skill="win_loss_study", input_data={"question": "q1"})
    store.create(skill="domain_discovery", input_data={"domain": "CRM"})
    tasks = store.list_tasks()
    assert len(tasks) == 2
