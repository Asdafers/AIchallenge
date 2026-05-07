"""Tests for agent graph factory function."""

from methodic.agent import build_agent_graph, root_agent
from methodic.agents.human_input_step import HumanInputStep


def test_root_agent_still_exists():
    """Module-level root_agent must remain for ADK Dev UI compatibility."""
    assert root_agent is not None
    assert root_agent.name == "methodic"


def test_module_level_exports_preserved():
    """Existing code imports these names from methodic.agent."""
    from methodic.agent import study_planner, fieldwork_loop, finalize, interview_loop
    assert study_planner is not None
    assert fieldwork_loop is not None
    assert finalize is not None
    assert interview_loop is not None


def test_build_demo_mode():
    graph = build_agent_graph(interactive=False)
    assert graph.name == "methodic"
    # Find interview_loop and check for participant_sim
    fw = graph.sub_agents[1]  # fieldwork_loop
    sr = fw.sub_agents[0]
    il = sr.sub_agents[1]
    participant = il.sub_agents[1]
    assert participant.name == "participant_sim"


def test_build_interactive_mode():
    registry = {}
    graph = build_agent_graph(interactive=True, session_registry=registry)
    assert graph.name == "methodic_interactive"
    # Find interview_loop and check for HumanInputStep
    fw = graph.sub_agents[1]
    sr = fw.sub_agents[0]
    il = sr.sub_agents[1]
    participant = il.sub_agents[1]
    assert isinstance(participant, HumanInputStep)
    # Fieldwork max_iterations should be 1 for single participant
    assert fw.max_iterations == 1


def test_interactive_mode_skips_quality_and_export():
    registry = {}
    graph = build_agent_graph(interactive=True, session_registry=registry)
    fin = graph.sub_agents[2]
    agent_names = [a.name for a in fin.sub_agents]
    assert "quality_reviewer" not in agent_names
    assert "bigquery_export" not in agent_names
    assert "completion_responder" in agent_names
