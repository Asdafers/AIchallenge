from methodic.agents.discovery import discovery_agent


def test_discovery_agent_exists():
    assert discovery_agent.name == "discovery"


def test_discovery_agent_has_output_key():
    assert discovery_agent.output_key == "discovery_brief"


def test_discovery_agent_instruction_mentions_study_brief():
    assert "study_objective" in discovery_agent.instruction
    assert "required_variables" in discovery_agent.instruction
    assert "hypotheses" in discovery_agent.instruction
